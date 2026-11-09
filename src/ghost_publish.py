#!/usr/bin/env python3
"""MOTICIAS · Publicador a Ghost (Admin API), solo biblioteca estándar.

  python3 -I src/ghost_publish.py --dry-run --ids <id> [<id> ...]      genera el HTML y el JSON del post sin tocar Ghost
  python3 -I src/ghost_publish.py --dry-run --date AAAA-MM-DD         todas las piezas de una edición
  python3 -I src/ghost_publish.py --all --status draft                 publica (o deja en borrador) todas las piezas de data/articles
  python3 -I src/ghost_publish.py --date AAAA-MM-DD --status published

Variables de entorno (nunca en el repositorio): GHOST_URL (p. ej. https://moticias.ghost.io o https://moticias.com)
y GHOST_ADMIN_KEY (clave de una integración personalizada de Ghost, formato id:secret).
Vertical: --vertical movilidad (lee verticals/<id>.json para secciones y etiquetas).

Qué hace con cada pieza de data/articles/<id>.json:
- Construye el HTML del post: respuesta directa (summary), cuerpo (body_md → HTML sencillo), cifras clave, cronología,
  guía rápida (los cinco bloques), fuentes con fechas, recuadro de trazabilidad y declaración de intereses si procede.
  Si la pieza lleva menciones publicadas, cada una va en una caja «Contenido patrocinado» en medio del cuerpo
  (src/menciones.py: cajas_html + insertar_en_medio; data/productos/; gestor en app.moticias.com/gestor/).
- Metadatos: título, slug (= id), extracto (summary), etiquetas (#<section> interna; modo `m-<submodo>`, temas `tema-<id>` y
  territorios `t-<id>` con slug fijo; etiquetas libres que no repitan un eje), autor por defecto,
  fecha de publicación (published_at), imagen destacada (si hay URL pública; las /_blob/ no se suben todavía),
  codeinjection_head con JSON-LD NewsArticle.
- Crea o actualiza el post por slug (busca antes con GET /posts/slug/<slug>/) y guarda el resultado en
  work/ghost/<id>.json (id de Ghost, url, updated_at) para la sala de redacción.
- Estado en Ghost: una pieza con `status` `pendiente` o `borrador` en data/ (firma del director sin aprobar) va SIEMPRE
  como borrador, aunque se pida --status published; solo las `publicado` se publican.
- Portada: la pieza con `featured: 1` se marca destacada en Ghost (es la apertura que pinta el tema) y la de `featured: 2`
  lleva la etiqueta interna #segunda; al publicar una edición (--date) se quita el destacado a las piezas de días anteriores.
- Fotos: `image.src` relativo (`img/<nombre>.jpg`) se sube a Ghost desde portal/img/ con /images/upload/ una sola vez;
  la URL que devuelve Ghost se guarda en portal/img/ghost-urls.json para reutilizarla (misma foto, misma URL).
Limitaciones conocidas (se resuelven por OpenSpec): el Markdown se convierte con un conversor mínimo (títulos, negrita,
cursiva, enlaces, listas, citas); las fotos /_blob/ requieren subirlas con /images/upload/ (pendiente).
"""
import argparse, base64, datetime, glob, hashlib, hmac, html, json, os, re, sys, time, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from taxonomia import Taxonomia, plano  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from menciones import cajas_html, insertar_en_medio  # noqa: E402  (cajas «Contenido patrocinado»; data/productos/README.md)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Moticias/1.0 (+https://moticias.com)"


# ---------- utilidades ----------
def b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def ghost_token(admin_key):
    """JWT HS256 de 5 minutos para la Admin API, como pide Ghost."""
    kid, secret = admin_key.split(":")
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT", "kid": kid}
    payload = {"iat": now, "exp": now + 300, "aud": "/admin/"}
    signing = b64url(json.dumps(header, separators=(",", ":")).encode()) + "." + b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(bytes.fromhex(secret), signing.encode(), hashlib.sha256).digest()
    return signing + "." + b64url(sig)


def _json(raw, status):
    try:
        return json.loads(raw or b"{}")
    except ValueError:
        return {"errors": [{"message": "respuesta no JSON (HTTP %s): %s" % (status, raw[:160].decode("utf-8", "replace"))}]}


class _SinRedireccion(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_ADMIN = {}


def admin_base(base_url):
    """Dirección de la Admin API. En Ghost(Pro) el dominio público (www.moticias.com) redirige /ghost/ al dominio de
    administración (moticias.ghost.io) y en esa redirección se pierde la autorización: se detecta una vez y se usa el
    destino. GHOST_ADMIN_URL lo fija a mano si hiciera falta. La URL pública de las piezas sigue siendo base_url."""
    if os.environ.get("GHOST_ADMIN_URL"):
        return os.environ["GHOST_ADMIN_URL"].rstrip("/")
    if base_url not in _ADMIN:
        dest = base_url
        try:
            urllib.request.build_opener(_SinRedireccion).open(
                urllib.request.Request(base_url + "/ghost/api/admin/site/", headers={"User-Agent": UA}), timeout=20)
        except urllib.error.HTTPError as e:
            loc = e.headers.get("Location") or ""
            if e.code in (301, 302, 307, 308) and "/ghost/" in loc:
                dest = loc.split("/ghost/")[0].rstrip("/")
        except urllib.error.URLError:
            pass
        _ADMIN[base_url] = dest
    return _ADMIN[base_url]


def api(method, url, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Ghost " + token, "Content-Type": "application/json", "Accept-Version": "v5.0", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, _json(r.read(), r.status)
    except urllib.error.HTTPError as e:
        return e.code, _json(e.read(), e.code)


# ---------- Markdown mínimo → HTML ----------
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" rel="noopener">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    return s


def md_to_html(md):
    out, para, lst = [], [], None

    def flush():
        nonlocal para
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para)))
            para = []

    def close_list():
        nonlocal lst
        if lst:
            out.append("</ul>")
            lst = None

    for raw in (md or "").splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush(); close_list(); continue
        if line.startswith("## "):
            flush(); close_list(); out.append("<h2>%s</h2>" % inline(line[3:].strip())); continue
        if line.startswith("### "):
            flush(); close_list(); out.append("<h3>%s</h3>" % inline(line[4:].strip())); continue
        if line.startswith(">> "):
            flush(); close_list(); out.append('<blockquote class="kg-blockquote-alt">%s</blockquote>' % inline(line[3:].strip())); continue
        if line.startswith("> "):
            flush(); close_list(); out.append("<blockquote>%s</blockquote>" % inline(line[2:].strip())); continue
        if line.startswith("- "):
            flush()
            if not lst:
                out.append("<ul>"); lst = True
            out.append("<li>%s</li>" % inline(line[2:].strip())); continue
        close_list(); para.append(line.strip())
    flush(); close_list()
    return "\n".join(out)


# ---------- construcción del post ----------
def fmt_date(d):
    if not d:
        return "sin fecha publicada"
    try:
        return datetime.date.fromisoformat(d[:10]).strftime("%d-%m-%Y")
    except ValueError:
        return d


def build_html(a, vertical):
    parts = []
    if a.get("summary"):
        parts.append('<p class="respuesta-directa"><strong>%s</strong></p>' % inline(a["summary"]))
    parts.append(insertar_en_medio(md_to_html(a.get("body_md", "")), cajas_html(a, vertical, inline)))
    if a.get("key_data"):
        parts.append("<h2>Cifras clave</h2><ul>" + "".join(
            "<li><strong>%s:</strong> %s <small>(%s)</small></li>" % (inline(k.get("label", "")), inline(k.get("value", "")), inline(k.get("source", "")))
            for k in a["key_data"]) + "</ul>")
    if a.get("timeline"):
        parts.append("<h2>Cronología</h2><ul>" + "".join(
            "<li><strong>%s</strong> · %s</li>" % (inline(t.get("date", "")), inline(t.get("text", ""))) for t in a["timeline"]) + "</ul>")
    guide = [("De qué trata", a.get("summary")), ("Quiénes son los protagonistas", a.get("actors")),
             ("Para quién es relevante", a.get("relevance_for")), ("Por qué es importante", a.get("why")), ("Qué puede pasar ahora", a.get("next"))]
    if any(v for _, v in guide):
        parts.append("<h2>Guía rápida</h2>" + "".join("<p><strong>%s.</strong> %s</p>" % (k, inline(v)) for k, v in guide if v))
    if a.get("sources"):
        parts.append("<h2>Para saber más</h2><ul>" + "".join(
            '<li>[%s] %s — <a href="%s" rel="noopener">%s</a> (publicado %s; consultado %s)</li>' % (
                "Fuente oficial" if s.get("kind") == "oficial" else "Medios", inline(s.get("outlet", "")), html.escape(s.get("url", ""), quote=True),
                inline(s.get("title", "")), fmt_date(s.get("published")), fmt_date(s.get("accessed"))) for s in a["sources"]) + "</ul>")
    for c in a.get("correcciones") or []:  # regla de siempre: la corrección se dice al final, con su fecha
        parts.append('<p class="correccion"><small><strong>Corrección (%s).</strong> %s</small></p>' % (fmt_date(c.get("en")), inline(c.get("texto", ""))))
    traz = ["Hechos: %s" % fmt_date(a.get("event_date")), "Redacción: %s" % (a.get("published_at") or "")]
    if a.get("revised_at"):
        traz.append("Revisión: %s" % a["revised_at"])
    parts.append('<p class="trazabilidad"><small>%s</small></p>' % " · ".join(inline(t) for t in traz))
    if a.get("author_note"):
        nota, edt = a["author_note"], vertical.get("editorial") or {}
        # El nombre del director solo aparece en lo que él firma (cupo de firma, 9-11-2026).
        firmas_director = {edt.get("director")} | set(edt.get("director_firma_antigua") or [])
        if (a.get("author") or "") not in firmas_director and edt.get("director") and edt["director"].split()[0] in nota:
            nota = edt.get("interests_note_redaccion") or nota
        parts.append('<p class="intereses"><small>%s</small></p>' % inline(nota))
    ed = vertical.get("editor", {})
    parts.append('<p class="fin"><small>%s · %s · FIN</small></p>' % (inline(vertical.get("name", "")), inline(a.get("date", ""))))
    return "\n".join(parts)


def organizacion(vertical):
    """La casa en datos estructurados: medio, editor y empresas del grupo (con su especialidad), para buscadores y modelos
    de lenguaje. Las marcas van declaradas como del grupo, nunca como juicio editorial (verticals → grupo)."""
    g = vertical.get("grupo") or {}
    dom = "https://%s/" % vertical.get("domain", "www.moticias.com").replace("moticias.com", "www.moticias.com").replace("www.www.", "www.")
    ed = g.get("editor") or {}
    org = {"@type": "NewsMediaOrganization", "@id": dom + "#organizacion", "name": vertical.get("name", "MOTICIAS"),
           "alternateName": ["MOTICIAS", "Moticias", "moticias.com", "MOTICIAS.com"], "url": dom,
           "slogan": "Noticias con M de Movilidad y Transportes", "inLanguage": "es-ES",
           "logo": {"@type": "ImageObject", "url": dom + "assets/marca/icon-512.png", "width": 512, "height": 512},
           "publishingPrinciples": dom + "como-trabajamos/", "ownershipFundingInfo": dom + "empresas-del-grupo/",
           "knowsAbout": ["movilidad", "transporte de viajeros", "autobús", "ferrocarril", "transporte aéreo", "transporte marítimo", "logística",
                          "regulación del transporte", "planes de movilidad sostenible al trabajo", "transporte a la demanda"]}
    if ed.get("nombre"):
        org["parentOrganization"] = {"@type": "Organization", "name": ed["nombre"], "url": ed.get("url"), "description": ed.get("descripcion")}
    marcas = [m for m in g.get("marcas") or [] if m.get("publica", True)]
    if marcas:
        org["subOrganization"] = [{"@type": "Organization", "name": m["nombre"], "url": m["url"], "description": m.get("descripcion"),
                                   "knowsAbout": m.get("especialidad")} for m in marcas]
    return org


def _marca_de(vertical, producto_id):
    for m in (vertical.get("grupo") or {}).get("marcas") or []:
        if producto_id in (m.get("productos") or []) and m.get("publica", True):
            return m
    return None


def jsonld(a, vertical, url):
    """NewsArticle con autor, medio y editor, fuentes citadas, temas, lugar y respuesta directa (speakable); si la pieza lleva
    caja «Contenido patrocinado», además las empresas del grupo que menciona (`mentions`, declaradas) y la guía rápida como
    preguntas y respuestas: así se «activa» para buscadores y modelos de lenguaje (decisión de Rainer, 9-11-2026)."""
    org = organizacion(vertical)
    edt = vertical.get("editorial") or {}
    autor = a.get("author") or edt.get("default_author") or "Redacción"
    d = {"@context": "https://schema.org", "@type": "NewsArticle", "@id": url + "#pieza", "headline": (a.get("title") or "")[:110],
         "alternativeHeadline": a.get("subtitle"), "description": a.get("summary"), "abstract": a.get("key_fact"),
         "datePublished": a.get("published_at"), "dateModified": a.get("revised_at") or a.get("published_at"), "inLanguage": "es-ES",
         "author": {"@type": "Person", "name": autor, "jobTitle": a.get("author_role") or edt.get("default_author_role"),
                    "worksFor": {"@id": org["@id"]}},
         "publisher": org, "mainEntityOfPage": url, "url": url, "articleSection": a.get("section"), "isAccessibleForFree": True,
         "keywords": ", ".join(a.get("tags") or []), "wordCount": len((a.get("body_md") or "").split()),
         "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".respuesta-directa"]}}
    if a.get("sources"):
        d["citation"] = [{"@type": "CreativeWork", "name": s.get("title"), "url": s.get("url"), "publisher": s.get("outlet"),
                          "datePublished": s.get("published") or None} for s in a["sources"] if s.get("url")]
    temas = [t for t in (a.get("temas") or [])] + [x for x in (a.get("modo"), a.get("submodo")) if x]
    if temas:
        d["about"] = [{"@type": "Thing", "name": t} for t in temas]
    if (a.get("geo") or {}).get("place"):
        g = a["geo"]
        d["contentLocation"] = {"@type": "Place", "name": g["place"], "geo": {"@type": "GeoCoordinates", "latitude": g.get("lat"), "longitude": g.get("lon")}}
    pub = [m for m in a.get("menciones") or [] if m.get("estado") == "publicada"]
    marcas = [x for x in (_marca_de(vertical, m.get("producto")) for m in pub) if x]
    grafo = [d]
    if marcas:
        d["mentions"] = [{"@type": "Organization", "name": m["nombre"], "url": m["url"], "description": "%s. Empresa del grupo editor de MOTICIAS." % (m["especialidad"][:1].upper() + m["especialidad"][1:])} for m in marcas]
        preguntas = [("¿De qué trata?", a.get("summary")), ("¿Quiénes son los protagonistas?", a.get("actors")), ("¿Para quién es relevante?", a.get("relevance_for")),
                     ("¿Por qué es importante?", a.get("why")), ("¿Qué puede pasar ahora?", a.get("next"))]
        qa = [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in preguntas if r]
        if qa:
            grafo.append({"@context": "https://schema.org", "@type": "FAQPage", "@id": url + "#guia", "about": {"@id": url + "#pieza"}, "mainEntity": qa})
    out = grafo[0] if len(grafo) == 1 else {"@context": "https://schema.org", "@graph": [dict(x, **{"@context": None}) for x in grafo]}
    txt = json.dumps(out, ensure_ascii=False).replace('"@context": null, ', "").replace(', "@context": null', "")
    return '<script type="application/ld+json">%s</script>' % txt.replace("</", "<\\/")


_TX = {}


def taxonomia(vertical):
    vid = vertical.get("id", "movilidad")
    if vid not in _TX:
        _TX[vid] = Taxonomia(vid)
    return _TX[vid]


def etiquetas_taxonomia(tx):
    """Las etiquetas públicas de los tres ejes, con slug fijo (el tema de Ghost filtra por slug) y descripción (sale en llms.txt).
    Modo: m-<submodo> · Tema: tema-<id> · Territorio: t-<id>."""
    out = []
    for m in tx.tax["modos"]:
        for sm in m["submodos"]:
            out.append({"name": sm["nombre"] if sm["id"] != "transversal" else "Transversal", "slug": "m-" + sm["id"],
                        "description": "Piezas de MOTICIAS sobre %s (%s): noticias, regulación, contratos y análisis." % (sm["nombre"].lower(), m["nombre"].lower())})
    for t in tx.tax["temas"]:
        out.append({"name": t["nombre"], "slug": "tema-" + t["id"], "description": "Piezas de MOTICIAS del tema «%s» en transporte, movilidad y logística." % t["nombre"]})
    for t in tx.tax["territorios"]:
        out.append({"name": t["nombre"], "slug": "t-" + t["id"],
                    "description": "Noticias de transporte, movilidad y logística que se deciden en %s o afectan a %s." % (t["nombre"], t["nombre"])
                    if t["tipo"] == "ccaa" else "Noticias de transporte, movilidad y logística de ámbito %s." % t["nombre"].lower()})
    return out


def etiquetas_pieza(a, tx):
    """Etiquetas de un post: sección interna (#…), los tres ejes con slug fijo y las etiquetas libres que no repitan un eje."""
    tags = [{"name": "#" + a.get("section", "")}] if a.get("section") else []
    nombres_ejes = set()
    if a.get("submodo") and a["submodo"] in tx.submodos:
        sm = tx.submodos[a["submodo"]][1]
        tags.append({"name": sm["nombre"], "slug": "m-" + sm["id"]}); nombres_ejes.add(plano(sm["nombre"]))
    for t in a.get("temas") or []:
        if t in tx.temas:
            tags.append({"name": tx.temas[t]["nombre"], "slug": "tema-" + t}); nombres_ejes.add(plano(tx.temas[t]["nombre"]))
    for t in a.get("territorios") or []:
        if t in tx.territorios:
            tags.append({"name": tx.territorios[t]["nombre"], "slug": "t-" + t}); nombres_ejes.add(plano(tx.territorios[t]["nombre"]))
    alias_terr = {plano(al) for t in tx.tax["territorios"] for al in t["alias"]} | {plano(t["nombre"]) for t in tx.tax["territorios"]}
    for t in a.get("tags") or []:
        if plano(t) in nombres_ejes or plano(t) in alias_terr or plano(t) == plano(a.get("subsector") or ""):
            continue  # ya está como eje: evita «Cantabria» dos veces
        tags.append({"name": t})
    return tags


def estado_ghost(a, pedido):
    """Estado con el que va la pieza a Ghost. Las piezas del director sin aprobar (`pendiente`) y los borradores nunca se
    publican por mucho que se pida --status published: quedan en borrador hasta que Rainer pulse «Publicar»."""
    return "draft" if a.get("status") in ("pendiente", "borrador", "retirada") else pedido


URLS_FOTOS = os.path.join(ROOT, "portal", "img", "ghost-urls.json")


def urls_fotos():
    try:
        return json.load(open(URLS_FOTOS, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def subir_imagen(ruta, base_url, token):
    """Sube una foto a Ghost (POST /images/upload/, multipart) y devuelve su URL pública, o None."""
    nombre = os.path.basename(ruta)
    limite = "----MoticiasGhost%d" % int(time.time() * 1000)
    cuerpo = b"".join([
        ("--%s\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nimage\r\n" % limite).encode(),
        ("--%s\r\nContent-Disposition: form-data; name=\"ref\"\r\n\r\n%s\r\n" % (limite, nombre)).encode(),
        ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\nContent-Type: image/jpeg\r\n\r\n" % (limite, nombre)).encode(),
        open(ruta, "rb").read(), ("\r\n--%s--\r\n" % limite).encode()])
    req = urllib.request.Request(admin_base(base_url) + "/ghost/api/admin/images/upload/", data=cuerpo, method="POST", headers={
        "Authorization": "Ghost " + token, "Content-Type": "multipart/form-data; boundary=" + limite, "Accept-Version": "v5.0", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            res = _json(r.read(), r.status)
    except urllib.error.HTTPError as e:
        res = _json(e.read(), e.code)
    return ((res.get("images") or [{}])[0]).get("url")


def imagen_ghost(a, base_url, token):
    """URL pública de la foto de la pieza en Ghost: la propia si ya es http; si es `img/<nombre>`, la que ya se subió
    (portal/img/ghost-urls.json) o, con token, la sube ahora desde portal/img/ y la anota. Sin foto: None."""
    im = a.get("image") or {}
    src = im.get("src") or ""
    if src.startswith("http"):
        return src
    if not src.startswith("img/"):
        return None
    nombre = src[4:]
    urls = urls_fotos()
    if urls.get(nombre):
        return urls[nombre]
    ruta = os.path.join(ROOT, "portal", "img", nombre)
    if not token or not os.path.exists(ruta):
        return None
    url = subir_imagen(ruta, base_url, token)
    if url:
        urls[nombre] = url
        with open(URLS_FOTOS, "w", encoding="utf-8") as fh:
            json.dump(urls, fh, ensure_ascii=False, indent=1, sort_keys=True)
            fh.write("\n")
    return url


_AUTORES = {}


def autor_ghost(a, vertical, base_url, token):
    """Id del usuario de Ghost que firma la pieza (`editorial.ghost_autores`: firma → slug). Sin esto Ghost deja la firma
    que tuviera el post o la del dueño de la integración, y el nombre del director acababa en piezas de la redacción."""
    if not token:
        return None
    slug = ((vertical.get("editorial") or {}).get("ghost_autores") or {}).get(a.get("author") or "Redacción")
    if not slug:
        return None
    if slug not in _AUTORES:
        st, r = api("GET", "%s/ghost/api/admin/users/slug/%s/?fields=id" % (admin_base(base_url), slug), token)
        _AUTORES[slug] = (r.get("users") or [{}])[0].get("id") if st == 200 else None
    return _AUTORES[slug]


def build_post(a, vertical, base_url, token=None):
    slug = a["id"]
    url = "%s/%s/" % (base_url.rstrip("/"), slug)  # Ghost sirve /<slug>/ (comprobado el 8-11-2026 en www.moticias.com)
    tags = etiquetas_pieza(a, taxonomia(vertical))
    if a.get("featured") == 2:
        tags.insert(0, {"name": "#segunda"})  # la segunda de la portada, para el tema
    if any(m.get("estado") == "publicada" for m in a.get("menciones") or []):
        tags.append({"name": "#contenido-patrocinado"})  # etiqueta interna: piezas con caja del grupo (página del grupo, colecciones)
    post = {"title": a.get("title"), "slug": slug, "html": build_html(a, vertical), "custom_excerpt": (a.get("summary") or "")[:300],
            "tags": tags, "published_at": a.get("published_at"), "meta_title": a.get("title"), "featured": a.get("featured") == 1,
            "meta_description": (a.get("subtitle") or a.get("summary") or "")[:500], "codeinjection_head": jsonld(a, vertical, url)}
    autor = autor_ghost(a, vertical, base_url, token)
    if autor:
        post["authors"] = [{"id": autor}]
    im = a.get("image") or {}
    foto = imagen_ghost(a, base_url, token)
    if foto:
        post["feature_image"] = foto
        post["feature_image_caption"] = "%s · %s" % (im.get("credit", ""), im.get("license", ""))
        post["feature_image_alt"] = im.get("alt")
    return post


def fijar_portada(slug_lead, base_url, token):
    """Deja destacada en Ghost solo la apertura del día: quita `featured` a cualquier otro post destacado."""
    base = admin_base(base_url)
    st, r = api("GET", base + "/ghost/api/admin/posts/?filter=featured:true&fields=id,slug,updated_at&limit=all", token)
    quitados = []
    for p in (r.get("posts") or []) if st == 200 else []:
        if p["slug"] != slug_lead:
            st2, _ = api("PUT", base + "/ghost/api/admin/posts/%s/" % p["id"], token, {"posts": [{"featured": False, "updated_at": p["updated_at"]}]})
            if st2 == 200:
                quitados.append(p["slug"])
    return quitados


# ---------- etiquetas de los tres ejes en Ghost ----------
def asegurar_etiquetas(tx, base_url, token):
    """Crea en Ghost las etiquetas de modo, tema y territorio con su slug fijo y su descripción; si ya existe una etiqueta
    con ese nombre pero otro slug (p. ej. «Cantabria» creada como etiqueta libre), le cambia el slug para que el tema filtre
    por él. Idempotente: se puede ejecutar cada día."""
    base = admin_base(base_url)
    creadas, cambiadas, errores = 0, 0, []
    for et in etiquetas_taxonomia(tx):
        st, r = api("GET", base + "/ghost/api/admin/tags/slug/%s/" % et["slug"], token)
        if st == 200:
            actual = r["tags"][0]
            if (actual.get("description") or "") != et["description"] or actual.get("name") != et["name"]:
                api("PUT", base + "/ghost/api/admin/tags/%s/" % actual["id"], token,
                    {"tags": [{"name": et["name"], "description": et["description"], "updated_at": actual["updated_at"]}]})
                cambiadas += 1
            continue
        st, r = api("GET", base + "/ghost/api/admin/tags/?filter=%s&limit=1" % urllib.request.quote("name:'%s'" % et["name"].replace("'", "\\'")), token)
        if st == 200 and r.get("tags"):
            actual = r["tags"][0]
            st2, r2 = api("PUT", base + "/ghost/api/admin/tags/%s/" % actual["id"], token,
                          {"tags": [{"slug": et["slug"], "description": et["description"], "updated_at": actual["updated_at"]}]})
            if st2 < 300:
                cambiadas += 1
            else:
                errores.append((et["slug"], r2))
            continue
        st, r = api("POST", base + "/ghost/api/admin/tags/", token, {"tags": [{"name": et["name"], "slug": et["slug"], "description": et["description"]}]})
        if st < 300:
            creadas += 1
        else:
            errores.append((et["slug"], r))
        time.sleep(0.2)
    return {"creadas": creadas, "cambiadas": cambiadas, "errores": errores}


# ---------- publicación ----------
def upsert(post, status, base_url, token):
    base_url = admin_base(base_url)
    post = dict(post, status=status)
    st, found = api("GET", "%s/ghost/api/admin/posts/slug/%s/?fields=id,updated_at" % (base_url, post["slug"]), token)
    if st == 200 and found.get("posts"):
        pid = found["posts"][0]["id"]
        post["updated_at"] = found["posts"][0]["updated_at"]
        st, res = api("PUT", "%s/ghost/api/admin/posts/%s/?source=html" % (base_url, pid), token, {"posts": [post]})
    else:
        st, res = api("POST", "%s/ghost/api/admin/posts/?source=html" % base_url, token, {"posts": [post]})
    if st not in (200, 201):
        return None, res
    p = res["posts"][0]
    return {"ghost_id": p["id"], "url": p.get("url"), "status": p.get("status"), "updated_at": p.get("updated_at")}, None


def marcar_en_web(a, cuando=None):
    """Anota en cada mención publicada cuándo quedó en la web (lo muestra el gestor). Devuelve True si cambió algo."""
    cuando = cuando or datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    cambio = False
    for m in a.get("menciones") or []:
        if m.get("estado") == "publicada" and not m.get("en_web"):
            m["en_web"] = cuando
            cambio = True
        elif m.get("estado") != "publicada" and m.get("en_web"):
            m.pop("en_web")
            cambio = True
    return cambio


def publicar_con_estado(a, vertical, base_url, admin_key, estado):
    """Sube la pieza a Ghost con un estado concreto («published» o «draft»): retirar y restaurar desde el gestor.
    Crea el post si no existía. Devuelve (resultado, error)."""
    token = ghost_token(admin_key)
    return upsert(build_post(a, vertical, base_url, token), estado, base_url, token)


def republicar(a, vertical, base_url, admin_key):
    """Actualiza en Ghost un post que ya existe, manteniendo su estado (publicado o borrador). No crea posts nuevos.
    Lo usa el gestor de patrocinios tras cada cambio. Devuelve (resultado, error)."""
    token = ghost_token(admin_key)
    st, found = api("GET", "%s/ghost/api/admin/posts/slug/%s/?fields=id,status" % (admin_base(base_url), a["id"]), token)
    if st == 404:
        return None, "la pieza aún no está en Ghost (la subirá la rutina)"
    if st != 200 or not found.get("posts"):
        return None, "Ghost respondió %s: %s" % (st, ((found.get("errors") or [{}])[0].get("message") or "")[:200])
    return upsert(build_post(a, vertical, base_url, token), found["posts"][0].get("status") or "draft", base_url, token)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vertical", default="movilidad")
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--date")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--status", default="draft", choices=["draft", "published"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--etiquetas", action="store_true", help="crea o corrige en Ghost las etiquetas de modo, tema y territorio (sin piezas)")
    a = ap.parse_args()
    vertical = json.load(open(os.path.join(ROOT, "verticals", a.vertical + ".json"), encoding="utf-8"))
    if a.etiquetas:
        base_url = os.environ.get("GHOST_URL", "https://%s" % vertical.get("domain", "")).rstrip("/")
        if a.dry_run:
            print(json.dumps(etiquetas_taxonomia(taxonomia(vertical)), ensure_ascii=False, indent=1)); return
        key = os.environ.get("GHOST_ADMIN_KEY")
        if not key or ":" not in key:
            sys.exit("Falta GHOST_ADMIN_KEY (id:secret) en el entorno")
        print(json.dumps(asegurar_etiquetas(taxonomia(vertical), base_url, ghost_token(key)), ensure_ascii=False)); return
    arts = []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "articles", "*.json"))):
        art = json.load(open(p, encoding="utf-8"))
        if a.ids and art["id"] not in a.ids:
            continue
        if a.date and art.get("date") != a.date:
            continue
        if not (a.ids or a.date or a.all):
            continue
        if art.get("status") == "borrador" and a.status == "published":
            continue
        arts.append(art)
    if not arts:
        sys.exit("Ninguna pieza seleccionada (usa --ids, --date o --all)")
    base_url = os.environ.get("GHOST_URL", "https://%s" % vertical.get("domain", "")).rstrip("/")
    outdir = os.path.join(ROOT, "work", "ghost")
    os.makedirs(outdir, exist_ok=True)
    token = None
    if not a.dry_run:
        key = os.environ.get("GHOST_ADMIN_KEY")
        if not key or ":" not in key:
            sys.exit("Falta GHOST_ADMIN_KEY (id:secret) en el entorno; usa --dry-run para probar sin Ghost")
        token = ghost_token(key)
    ok, bad, lead = 0, [], None
    for art in arts:
        post = build_post(art, vertical, base_url, token)
        if a.dry_run:
            with open(os.path.join(outdir, art["id"] + ".html"), "w", encoding="utf-8") as fh:
                fh.write(post["html"])
            with open(os.path.join(outdir, art["id"] + ".post.json"), "w", encoding="utf-8") as fh:
                json.dump({k: v for k, v in post.items() if k != "html"}, fh, ensure_ascii=False, indent=1)
            ok += 1
            continue
        res, err = upsert(post, estado_ghost(art, a.status), base_url, token)
        if err:
            bad.append((art["id"], err))
        else:
            ok += 1
            if art.get("featured") == 1 and estado_ghost(art, a.status) == "published":
                lead = art["id"]
            if marcar_en_web(art):  # las cajas ya están en la web: el gestor lo muestra
                with open(os.path.join(ROOT, "data", "articles", art["id"] + ".json"), "w", encoding="utf-8") as fh:
                    json.dump(art, fh, ensure_ascii=False, indent=1, sort_keys=True)
                    fh.write("\n")
            with open(os.path.join(outdir, art["id"] + ".json"), "w", encoding="utf-8") as fh:
                json.dump(res, fh, ensure_ascii=False, indent=1)
        time.sleep(0.5)
    quitados = fijar_portada(lead, base_url, token) if (lead and a.date and not a.dry_run) else []
    print(json.dumps({"modo": "prueba" if a.dry_run else a.status, "piezas": len(arts), "ok": ok, "errores": bad,
                      "borradores": [x["id"] for x in arts if estado_ghost(x, a.status) == "draft"], "portada": lead, "destacado_quitado_a": quitados}, ensure_ascii=False))


if __name__ == "__main__":
    main()
