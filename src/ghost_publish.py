#!/usr/bin/env python3
"""MOTICIAS · Publicador a Ghost (Admin API), solo biblioteca estándar.

  python3 -I src/ghost_publish.py --dry-run --ids <id> [<id> ...]      genera el HTML y el JSON del post sin tocar Ghost
  python3 -I src/ghost_publish.py --all --status published             todas las piezas (rutinarias publicadas, críticas en borrador)
  python3 -I src/ghost_publish.py --date AAAA-MM-DD --status published --edition AAAA-MM-DD
                                                                       edición diaria: piezas del día, apertura destacada y
                                                                       página de la edición (boletines, plazos, documento, mapa)
  python3 -I src/ghost_publish.py --edition AAAA-MM-DD                 solo reescribe la página de la edición
  python3 -I src/ghost_publish.py --pages [--ids <slug> ...]           páginas fijas de data/paginas/ (siempre en borrador)
  python3 -I src/ghost_publish.py --setup                              secciones (etiquetas con su respuesta directa) y menú

Variables de entorno (nunca en el repositorio): GHOST_URL (URL de la Admin API, p. ej. https://moticias.ghost.io)
y GHOST_ADMIN_KEY (clave de una integración personalizada de Ghost, formato id:secret).
Vertical: --vertical movilidad (lee verticals/<id>.json: secciones, firma, menú, URL pública).

Qué hace con cada pieza de data/articles/<id>.json:
- HTML de la ficha dentro de una tarjeta HTML de Ghost (se conserva tal cual; Ghost borraría las clases de un HTML
  normal): respuesta directa, cuerpo, columna con trazabilidad, dato y cifras clave, cronología (futuros marcados),
  firma y declaración de intereses; guía rápida de cinco bloques; fuentes con fecha de publicación y de consulta.
- Etiquetas: la sección como etiqueta principal pública (Tierra, Mar, Aire…), subsector y temas; internas «#reportaje»
  y «#segunda». La URL pública es /<sección>/<slug>/ (análisis y reportajes, /analisis/<slug>/) según ghost/routes.yaml.
- Apertura: la pieza con featured 1 de la última edición sale como destacada en Ghost; la de featured 2, con «#segunda».
- Firma (verticals/<id>.json → editorial.ghost_authors): «G. Jordan» → g-jordan, «Rainer» → rainer; si falta el
  usuario de G. Jordan, sale a nombre de Rainer y se avisa.
- Estado: --status published publica solo las rutinarias; las críticas (risk «critica» o status «pendiente») y los
  borradores van siempre como draft, a la espera del director.
- Foto: sube a Ghost el fichero de portal/img/ (una vez; caché en work/ghost/imagenes-<host>.json) y pone el crédito
  y la licencia como pie.
- Metadatos: extracto = subtítulo; meta descripción = respuesta directa; fecha original (published_at);
  codeinjection_head con JSON-LD NewsArticle y FAQPage (guía rápida).
- Resultado de cada pieza en work/ghost/<id>.json.
"""
import argparse, base64, datetime, glob, hashlib, hmac, html, json, mimetypes, os, re, sys, time, urllib.error, urllib.request, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Moticias/1.0 (+https://moticias.com)"
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MONTHS_S = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
HTML_CARD = "<!--kg-card-begin: html-->\n%s\n<!--kg-card-end: html-->"


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


class Ghost:
    """Cliente mínimo: renueva el token antes de que caduque."""

    def __init__(self, base_url, key):
        self.base, self.key, self.t, self.tok = base_url.rstrip("/"), key, 0, None

    def token(self):
        if time.time() - self.t > 240:
            self.tok, self.t = ghost_token(self.key), time.time()
        return self.tok

    def call(self, method, path, body=None, raw=None, ctype="application/json"):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(self.base + "/ghost/api/admin" + path, data=data, method=method, headers={
            "Authorization": "Ghost " + self.token(), "Content-Type": ctype, "Accept-Version": "v5.0", "User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                t = r.read()
                return r.status, (json.loads(t) if t[:1] in (b"{", b"[") else {})
        except urllib.error.HTTPError as e:
            t = e.read()
            try:
                return e.code, json.loads(t)
            except ValueError:
                return e.code, {"raw": t[:300].decode("utf-8", "replace")}


def api(method, url, token, body=None):
    """Compatibilidad con scripts anteriores."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Ghost " + token, "Content-Type": "application/json", "Accept-Version": "v5.0", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def d_iso(s):
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def fmt_short(s):
    d = d_iso(s)
    return "%d %s %d" % (d.day, MONTHS_S[d.month - 1], d.year) if d else esc(s or "")


def fmt_num(s):
    d = d_iso(s)
    return d.strftime("%d.%m.%Y") if d else "sin fecha"


def fmt_long(s, weekday=True):
    d = d_iso(s)
    if not d:
        return ""
    t = "%d de %s de %d" % (d.day, MONTHS[d.month - 1], d.year)
    return ("%s, %s" % (DAYS[d.weekday()], t)) if weekday else t


def fmt_tl(s):
    m = re.match(r"^(\d{4})-(\d{2})(?:-(\d{2}))?", str(s or ""))
    if not m:
        return esc(s)
    return fmt_short(s) if m.group(3) else "%s %s" % (MONTHS_S[int(m.group(2)) - 1], m.group(1))


def fmt_date(d):
    return fmt_num(d) if d else "sin fecha publicada"


def host(u):
    m = re.match(r"https?://(?:www\.)?([^/]+)", u or "")
    return m.group(1) if m else ""


# ---------- Markdown mínimo → HTML ----------
def inline(s):
    s = html.escape(str(s or ""), quote=False)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    return s


def answer_of(text, lo=40, hi=60):
    """Respuesta directa: frases completas del resumen hasta 60 palabras (mínimo la primera frase)."""
    sents = [x for x in re.split(r"(?<=[.;])\s+(?=[A-ZÁÉÍÓÚÑ«¿0-9])", (text or "").strip()) if x]
    out, n = [], 0
    for x in sents:
        w = len(x.split())
        if out and n + w > hi:
            break
        out.append(x); n += w
        if n >= lo:
            break
    return " ".join(out)


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
            out.append("</%s>" % lst)
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
            flush(); close_list(); out.append('<p class="pull">%s</p>' % inline(line[3:].strip())); continue
        if line.startswith("> "):
            flush(); close_list(); out.append("<blockquote>%s</blockquote>" % inline(line[2:].strip())); continue
        m = re.match(r"^(- |\d+\. )(.*)", line)
        if m:
            flush()
            kind = "ul" if m.group(1) == "- " else "ol"
            if lst != kind:
                close_list(); out.append("<%s>" % kind); lst = kind
            out.append("<li>%s</li>" % inline(m.group(2).strip())); continue
        close_list(); para.append(line.strip())
    flush(); close_list()
    return "\n".join(out)


# ---------- vertical ----------
def load_vertical(vid):
    return json.load(open(os.path.join(ROOT, "verticals", vid + ".json"), encoding="utf-8"))


def collection_of(a):
    return "analisis" if a.get("kind") in ("analisis", "reportaje") else (a.get("section") or "noticias")


def rel_url(a):
    return "/%s/%s/" % (collection_of(a), a["id"])


def load_all_articles():
    arts = []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "articles", "*.json"))):
        arts.append(json.load(open(p, encoding="utf-8")))
    return arts


def latest_edition_date():
    eds = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, "data", "editions", "*.json")))
    return eds[-1] if eds else None


# ---------- firma y estado ----------
def is_critical(art):
    return art.get("risk") == "critica" or art.get("status") in ("pendiente", "borrador")


def target_status(art, requested):
    """Las críticas y los borradores nunca se publican desde aquí: esperan al director."""
    return "draft" if is_critical(art) else requested


def resolve_authors(vertical, g):
    """Devuelve ({firma: slug de Ghost}, avisos). Busca cada usuario por slug y, si no, por nombre."""
    ed = vertical.get("editorial", {})
    wanted = ed.get("ghost_authors", {})
    director = ed.get("director", "Rainer")
    st, res = g.call("GET", "/users/?limit=all&fields=id,name,slug")
    users = res.get("users", []) if st == 200 else []
    by_slug = {u["slug"]: u["slug"] for u in users}
    by_name = {u["name"].strip().lower(): u["slug"] for u in users}
    first = {u["name"].strip().split()[0].lower(): u["slug"] for u in users}
    out, warn = {}, []
    for sig, slug in wanted.items():
        found = by_slug.get(slug) or by_name.get(sig.strip().lower()) or first.get(sig.strip().lower())
        if found and found != slug:
            warn.append("El usuario «%s» existe en Ghost con slug «%s», no «%s»: se usa «%s»." % (sig, found, slug, found))
        out[sig] = found
    dslug = out.get(director)
    for sig in wanted:
        if not out[sig]:
            warn.append("El usuario «%s» (%s) no existe en Ghost: sus piezas salen a nombre de %s." % (sig, wanted[sig], director))
            out[sig] = dslug
    return out, warn


def author_slug(art, authors, vertical):
    ed = vertical.get("editorial", {})
    sig = art.get("author")
    if sig not in authors:
        sig = ed.get("director") if is_critical(art) else ed.get("default_author")
    return authors.get(sig)


# ---------- ficha de la pieza ----------
def build_html(a, vertical, today=None):
    today = today or datetime.date.today().isoformat()
    ed = vertical.get("editorial", {})
    parts = ['<div class="m-art" data-section="%s">' % esc(a.get("section"))]
    if a.get("summary"):
        parts.append('<p class="m-answer">%s</p>' % inline(a.get("answer") or answer_of(a["summary"])))
    parts.append('<div class="m-body">%s</div>' % md_to_html(a.get("body_md", "")))

    # Columna lateral
    side = []
    ofs = sorted([s for s in a.get("sources", []) if s.get("kind") == "oficial" and s.get("published")], key=lambda s: s["published"])
    accessed = sorted([s.get("accessed") for s in a.get("sources", []) if s.get("accessed")])
    tr = []
    if a.get("event_date"):
        tr.append(("Fecha de los hechos", fmt_short(a["event_date"])))
    if ofs:
        tr.append(("Documento oficial más reciente", "%s, publicado el %s" % (esc(ofs[-1].get("outlet") or host(ofs[-1].get("url"))), fmt_short(ofs[-1]["published"]))))
    if accessed:
        tr.append(("Fuentes consultadas", fmt_short(accessed[-1])))
    pa = a.get("published_at") or a.get("date")
    m = re.match(r"^(\d{4}-\d{2}-\d{2})(?:T(\d{2}:\d{2}))?", str(pa or ""))
    if m:
        tr.append(("Redactado", fmt_short(m.group(1)) + (", %s CET" % m.group(2) if m.group(2) else "")))
    if a.get("revised_at"):
        tr.append(("Ampliado o corregido", fmt_short(a["revised_at"])))
    side.append('<div class="m-box m-trace"><h4>Trazabilidad</h4><dl>%s</dl></div>' % "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (k, v) for k, v in tr))
    if a.get("key_fact"):
        side.append('<div class="m-box m-key"><h4>Dato clave</h4><p>%s</p></div>' % inline(a["key_fact"]))
    kd = [k for k in a.get("key_data") or [] if k and k.get("value")]
    if kd:
        side.append('<div class="m-box"><h4>Cifras clave</h4><dl class="m-kd">%s</dl></div>' % "".join(
            "<div><dt>%s</dt><dd>%s%s</dd></div>" % (inline(k.get("label")), inline(k.get("value")), "<small>%s</small>" % inline(k["source"]) if k.get("source") else "")
            for k in kd))
    tl = sorted([t for t in a.get("timeline") or [] if t and t.get("text")], key=lambda t: str(t.get("date") or ""))
    if tl:
        side.append('<div class="m-box"><h4>Cronología</h4><ol class="m-tl">%s</ol><p class="m-tl-legend"><i></i>Fechas por venir</p></div>' % "".join(
            '<li data-date="%s"%s><span class="d">%s</span><span>%s</span></li>' % (
                esc(t.get("date")), ' class="next"' if str(t.get("date") or "") > today else "", fmt_tl(t.get("date")), inline(t["text"]))
            for t in tl))
    role = a.get("author_role") or (ed.get("director_role") if a.get("author") == ed.get("director") else ed.get("default_author_role"))
    side.append('<div class="m-box m-author"><h4>Firma</h4><p><b>%s</b>%s</p>%s</div>' % (
        esc(a.get("author") or ed.get("default_author")), "<br><span>%s</span>" % esc(role) if role else "",
        '<p class="m-interests">%s</p>' % inline(a["author_note"]) if a.get("author_note") else ""))
    parts.append('<aside class="m-aside">%s</aside>' % "".join(side))

    # Guía rápida
    guide = [("De qué trata", a.get("summary")), ("Quiénes son los protagonistas", a.get("actors")),
             ("Para quién es relevante", a.get("relevance_for")), ("Por qué es importante", a.get("why")), ("Qué puede pasar ahora", a.get("next"))]
    if any(v for _, v in guide):
        parts.append('<section class="m-quick"><h2>Guía rápida</h2><div class="m-quick-grid">%s</div></section>' % "".join(
            '<div class="m-blk"><h3>%s</h3><p>%s</p></div>' % (k, inline(v)) for k, v in guide if v))

    # Fuentes
    def src_li(s):
        return ('<li><span class="m-badge">%s</span><div><a href="%s" rel="noopener">%s</a><div class="m-meta"><span>%s</span>'
                '<span>Publicado %s</span><span>Consultado %s</span></div></div></li>') % (
            "Oficial" if s.get("kind") == "oficial" else "Medios", esc(s.get("url")), inline(s.get("title") or s.get("outlet") or s.get("url")),
            esc(s.get("outlet") or host(s.get("url"))), fmt_date(s.get("published")), fmt_date(s.get("accessed")))
    of = [s for s in a.get("sources") or [] if s.get("kind") == "oficial"]
    me = [s for s in a.get("sources") or [] if s.get("kind") != "oficial"]
    if of or me:
        parts.append('<section class="m-sources"><h2>Para saber más</h2>%s%s</section>' % (
            "<h3>Documentos y fuentes oficiales</h3><ul>%s</ul>" % "".join(src_li(s) for s in of) if of else "",
            "<h3>Medios</h3><ul>%s</ul>" % "".join(src_li(s) for s in me) if me else ""))
    parts.append('<p class="m-fin">%s · %s · FIN</p>' % (esc(vertical.get("name", "")), fmt_short(a.get("date"))))
    parts.append("</div>")
    return HTML_CARD % "\n".join(parts)


def jsonld(a, vertical, url):
    gh = vertical.get("ghost", {})
    site = gh.get("site_url", "https://%s" % vertical.get("domain", ""))
    d = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": a.get("title"), "description": a.get("summary"),
         "datePublished": a.get("published_at"), "dateModified": a.get("revised_at") or a.get("published_at"), "inLanguage": "es-ES",
         "author": {"@type": "Person", "name": a.get("author") or "Redacción", "jobTitle": a.get("author_role")},
         "publisher": {"@type": "NewsMediaOrganization", "name": vertical.get("name"), "url": site + "/",
                       "logo": {"@type": "ImageObject", "url": site + "/assets/marca/icon-512.png"}},
         "mainEntityOfPage": url, "articleSection": (gh.get("sections", {}).get(a.get("section"), {}) or {}).get("name", a.get("section")),
         "keywords": ", ".join(a.get("tags") or [])}
    if a.get("sources"):
        d["citation"] = [s.get("url") for s in a["sources"] if s.get("url")]
    out = ['<script type="application/ld+json">%s</script>' % json.dumps(d, ensure_ascii=False)]
    guide = [("¿De qué trata?", a.get("summary")), ("¿Quiénes son los protagonistas?", a.get("actors")),
             ("¿Para quién es relevante?", a.get("relevance_for")), ("¿Por qué es importante?", a.get("why")), ("¿Qué puede pasar ahora?", a.get("next"))]
    qa = [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"\*\*|\[|\]\([^)]*\)", "", v)}} for q, v in guide if v]
    if len(qa) >= 2:
        out.append('<script type="application/ld+json">%s</script>' % json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": qa}, ensure_ascii=False))
    return "\n".join(out).replace("</", "<\\/").replace("<\\/script>", "</script>")


def edition_picks(arts, date):
    """(apertura, segunda) publicables de una edición: la apertura prevista si es rutinaria; si espera al director,
    la segunda sube a apertura y la siguiente rutinaria del día pasa a segunda."""
    if not date:
        return None, None
    day = [a for a in arts if a.get("date") == date and a.get("kind") == "noticia" and not is_critical(a)]
    day.sort(key=lambda a: ({1: 0, 2: 1}.get(a.get("featured"), 2), a.get("relevance") != "ALTA", a.get("published_at") or ""))
    ids = [a["id"] for a in day]
    return (ids[0] if ids else None), (ids[1] if len(ids) > 1 else None)


PICKS = {}


def build_tags(a, vertical, latest):
    gh = vertical.get("ghost", {})
    secs = gh.get("sections", {})
    it = gh.get("internal_tags", {})
    sec = "analisis" if a.get("kind") == "analisis" else a.get("section")
    tags = [{"name": secs.get(sec, {}).get("name", sec), "slug": sec}]
    if a.get("kind") == "reportaje":
        tags.append({"name": it.get("reportaje", "#reportaje")})
    if latest and PICKS.get(latest, (None, None))[1] == a["id"]:
        tags.append({"name": it.get("segunda", "#segunda")})
    seen = {t.get("slug") or t["name"].lower() for t in tags}
    for t in [a.get("subsector")] + list(a.get("tags") or []):
        if t and t.lower() not in seen:
            seen.add(t.lower()); tags.append({"name": t})
    return tags


def build_post(a, vertical, base_url, latest=None, today=None):
    slug = a["id"]
    site = vertical.get("ghost", {}).get("site_url", base_url)
    url = site.rstrip("/") + rel_url(a)
    post = {"title": a.get("title"), "slug": slug, "html": build_html(a, vertical, today), "custom_excerpt": (a.get("subtitle") or a.get("summary") or "")[:300],
            "tags": build_tags(a, vertical, latest), "published_at": a.get("published_at"), "meta_title": a.get("title")[:300],
            "meta_description": (a.get("summary") or a.get("subtitle") or "")[:500], "codeinjection_head": jsonld(a, vertical, url),
            "featured": bool(latest and PICKS.get(latest, (None, None))[0] == a["id"])}
    im = a.get("image") or {}
    if im.get("credit") or im.get("license"):
        cap = " · ".join(x for x in [im.get("credit"), im.get("license")] if x)
        post["feature_image_caption"] = ('Foto: <a href="%s" rel="noopener">%s</a>' % (esc(im["source"]), esc(cap))) if im.get("source") else "Foto: " + esc(cap)
        post["feature_image_alt"] = (im.get("alt") or "")[:190]
    if im.get("src", "").startswith("http"):
        post["feature_image"] = im["src"]
    return post


# ---------- imágenes ----------
def local_image(a):
    im = a.get("image") or {}
    for cand in [im.get("src"), im.get("orig_src")] + (["img/b-%s.jpg" % im["assetId"]] if im.get("assetId") else []):
        if cand and not cand.startswith("http"):
            p = os.path.join(ROOT, "portal", cand.lstrip("/").replace("_blob/", "img/b-"))
            for q in (p, p + ".jpg"):
                if os.path.isfile(q):
                    return q
    return None


def upload_image(g, path, cache):
    name = os.path.basename(path)
    if name in cache:
        return cache[name]
    bnd = uuid.uuid4().hex
    ctype = mimetypes.guess_type(path)[0] or "image/jpeg"
    body = (("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\nContent-Type: %s\r\n\r\n" % (bnd, name, ctype)).encode()
            + open(path, "rb").read() + ("\r\n--%s\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nimage\r\n--%s--\r\n" % (bnd, bnd)).encode())
    st, res = g.call("POST", "/images/upload/", raw=body, ctype="multipart/form-data; boundary=" + bnd)
    if st in (200, 201) and res.get("images"):
        cache[name] = res["images"][0]["url"]
        return cache[name]
    return None


# ---------- publicación ----------
def upsert(post, status, g, kind="posts"):
    post = dict(post, status=status)
    st, found = g.call("GET", "/%s/slug/%s/?fields=id,updated_at" % (kind, post["slug"]))
    if st == 200 and found.get(kind):
        pid = found[kind][0]["id"]
        post["updated_at"] = found[kind][0]["updated_at"]
        st, res = g.call("PUT", "/%s/%s/?source=html" % (kind, pid), {kind: [post]})
    else:
        st, res = g.call("POST", "/%s/?source=html" % kind, {kind: [post]})
    if st not in (200, 201):
        return None, res
    p = res[kind][0]
    out = {"ghost_id": p["id"], "url": p.get("url"), "status": p.get("status"), "featured": p.get("featured"), "updated_at": p.get("updated_at")}
    if p.get("status") != "published" and p.get("uuid"):
        out["preview_url"] = p.get("url")
    return out, None


def publish_pages(a, vertical, g, outdir):
    """Páginas fijas (aviso legal, privacidad, cookies, cómo trabajamos): data/paginas/<slug>.json, siempre en borrador."""
    outdir = os.path.join(outdir, "paginas")
    os.makedirs(outdir, exist_ok=True)
    authors, warn = ({}, []) if not g else resolve_authors(vertical, g)
    director = vertical.get("editorial", {}).get("director", "Rainer")
    ok, bad = [], []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "paginas", "*.json"))):
        pg = json.load(open(p, encoding="utf-8"))
        if a.ids and pg["slug"] not in a.ids:
            continue
        page = {"title": pg["title"], "slug": pg["slug"], "html": HTML_CARD % ('<div class="m-page">%s</div>' % md_to_html(pg["body_md"])),
                "custom_excerpt": pg.get("summary", "")[:300], "meta_description": pg.get("summary", "")[:500]}
        if authors.get(director):
            page["authors"] = [{"slug": authors[director]}]
        if not g:
            open(os.path.join(outdir, pg["slug"] + ".html"), "w", encoding="utf-8").write(page["html"])
            ok.append({"slug": pg["slug"]})
            continue
        status = "published" if pg.get("status") == "publicado" else "draft"
        res, err = upsert(page, status, g, kind="pages")
        if err:
            bad.append((pg["slug"], err))
        else:
            res["slug"] = pg["slug"]
            ok.append(res)
            json.dump(res, open(os.path.join(outdir, pg["slug"] + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"paginas": ok, "errores": bad, "avisos": warn}


# ---------- página de la edición ----------
def build_edition(date, vertical, arts):
    """HTML de la página oculta «edicion-hoy»: teletipo, documento del día, mapa, boletines, plazos y nota metodológica."""
    ep = os.path.join(ROOT, "data", "editions", date + ".json")
    if not os.path.isfile(ep):
        sys.exit("No existe data/editions/%s.json" % date)
    ed = json.load(open(ep, encoding="utf-8"))
    pub = [a for a in arts if not is_critical(a)]
    by_id = {a["id"]: a for a in arts}
    secs = vertical.get("ghost", {}).get("sections", {})
    bol = [json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(ROOT, "data", "boletines", "*.json"))]
    agenda = [json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(ROOT, "data", "agenda", "*.json"))]
    out = ['<div class="m-ed" data-date="%s">' % esc(date)]

    tk = ed.get("ticker") or []
    if tk:
        out.append('<div class="m-ticker"><span class="m-ticker-label">%s %s</span><ul>%s</ul></div>' % (
            esc(ed.get("ticker_label") or "Boletines"), fmt_short(date),
            "".join('<li><b>%s</b> <a href="%s" rel="noopener">%s</a></li>' % (esc(t.get("ref")), esc(t.get("url")), esc(t.get("text"))) for t in tk)))

    doc = ed.get("document") or {}
    if doc.get("title"):
        lines = [l.strip() for l in re.split(r"(?<=\.)\s+(?=[A-ZÁÉÍÓÚÑ])", doc.get("summary") or "") if l.strip()]
        out.append('<section class="m-doc"><div class="m-sh regulacion"><h2>El documento del día<small>fuente primaria</small></h2></div>'
                   '<div class="m-doc-card"><div class="m-kicker regulacion">%s</div><h3><a href="%s" rel="noopener">%s</a></h3>'
                   '<ul class="m-doc-guide">%s</ul><div class="m-meta"><span class="m-badge">%s</span><span>%s</span>%s</div></div></section>' % (
                       esc(doc.get("kicker") or "Documento"), esc(doc.get("url")), esc(doc.get("title")),
                       "".join("<li>%s</li>" % esc(l) for l in lines), esc(doc.get("source") or "Fuente oficial"), fmt_short(doc.get("date")),
                       "<span>%s</span>" % esc(doc["ref"]) if doc.get("ref") else ""))

    # Mapa: piezas publicadas con lugar, de la edición y de los seis días anteriores
    d0 = d_iso(date)
    geo = [a for a in pub if (a.get("geo") or {}).get("lat") is not None and d_iso(a.get("date")) and 0 <= (d0 - d_iso(a["date"])).days <= 6]
    geo.sort(key=lambda a: (a.get("date") != date, a.get("date")), reverse=False)
    if geo:
        out.append('<section class="m-mapa"><div class="m-sh"><h2>El mapa de la semana<small>%d piezas con lugar en los últimos siete días</small></h2></div>'
                   '<div class="m-map-grid"><div class="m-map" data-map aria-hidden="true"></div><ul class="m-map-list">%s</ul></div></section>' % (
                       len(geo), "".join('<li data-lat="%s" data-lon="%s" data-sec="%s"><span class="m-place">%s</span><span class="m-kicker %s">%s</span><a href="%s">%s</a></li>' % (
                           a["geo"]["lat"], a["geo"]["lon"], esc(a.get("section")), esc(a["geo"].get("place")), esc(a.get("section")),
                           esc(secs.get(a.get("section"), {}).get("name", a.get("section"))), rel_url(a), esc(a["title"])) for a in geo)))

    rows = sorted([b for b in bol if (b.get("edicion") or b.get("fecha")) == date], key=lambda b: b.get("referencia", ""))
    if rows:
        out.append('<section class="m-boletines"><div class="m-sh"><h2>Boletines oficiales<small>%d referencias seleccionadas · BOE %s</small></h2></div>'
                   '<div class="m-table-wrap"><table class="m-data"><thead><tr><th>Fecha</th><th>Referencia</th><th>Órgano</th><th>Qué es</th><th>Modo</th></tr></thead><tbody>%s</tbody></table></div></section>' % (
                       len(rows), fmt_short(date), "".join(
                           '<tr><td class="date">%s</td><td class="ref"><a href="%s" rel="noopener">%s</a></td><td class="org">%s</td><td class="t"><a href="%s" rel="noopener">%s</a>%s</td><td>%s</td></tr>' % (
                               fmt_num(b.get("fecha")), esc(b.get("url")), esc(b.get("referencia")), esc(b.get("organo")), esc(b.get("url")),
                               esc(b.get("titulo_corto") or b.get("titulo")), '<div class="nota">%s</div>' % esc(b["nota"]) if b.get("nota") else "",
                               " ".join('<span class="m-tag %s">%s</span>' % (esc(m), esc(secs.get(m, {}).get("name", m))) for m in b.get("modos") or []))
                           for b in rows)))

    soon = sorted([x for x in agenda if x.get("date") and x["date"] >= date], key=lambda x: x["date"])[:8]
    if soon:
        kinds = {"plazo": "Plazo", "consulta": "Consulta", "vigor": "Entrada en vigor", "evento": "Evento"}
        out.append('<section class="m-plazos"><div class="m-sh licitaciones"><h2>Próximos plazos<small>ofertas, consultas y entradas en vigor</small></h2></div><div class="m-deadlines">%s</div></section>' % "".join(
            '<div class="m-deadline %s" data-date="%s"><div class="when"><span>%s · %s</span><b class="m-countdown"></b></div><div class="what">%s</div><div class="who">%s</div></div>' % (
                esc(x.get("kind")), esc(x["date"]), fmt_num(x["date"]), kinds.get(x.get("kind"), "Fecha"),
                '<a href="%s" rel="noopener">%s</a>' % (esc(x["url"]), esc(x.get("title"))) if x.get("url") else esc(x.get("title")),
                esc(" · ".join(v for v in [x.get("authority"), x.get("amount")] if v))) for x in soon))

    if ed.get("note_metodologica"):
        out.append('<section class="m-nota"><div class="m-sh"><h2>Nota metodológica</h2></div><p>%s</p></section>' % esc(ed["note_metodologica"]))
    out.append('<p class="m-fin-ed">FIN DE EDICIÓN · %s%s</p>' % (fmt_long(date, False), ", %s CET" % esc(ed["closed_at"]) if ed.get("closed_at") else ""))
    out.append("</div>")

    lead = by_id.get(edition_picks(arts, date)[0]) or {}
    an = by_id.get(ed.get("analysis_id")) or {}
    n_day = len([a for a in pub if a.get("date") == date])
    answer = "Edición nº %s de MOTICIAS, %s: %d piezas publicadas, %d referencias del BOE y %d plazos a la vista.%s%s" % (
        ed.get("number", ""), fmt_long(date), n_day, len(rows), len(soon),
        " Apertura: «%s»." % lead["title"] if lead and not is_critical(lead) else "",
        " Análisis: «%s»." % an["title"] if an and not is_critical(an) else "")
    return {"title": "Edición nº %s · %s" % (ed.get("number", ""), fmt_long(date)), "slug": vertical.get("ghost", {}).get("page_edition_slug", "edicion-hoy"),
            "custom_excerpt": ("Cierre %s CET" % ed["closed_at"]) if ed.get("closed_at") else "",
            "meta_description": answer[:500], "html": HTML_CARD % "\n".join(out),
            "tags": [{"name": vertical.get("ghost", {}).get("internal_tags", {}).get("edicion", "#edicion")}],
            "canonical_url": vertical.get("ghost", {}).get("site_url", "") + "/"}


# ---------- configuración del sitio ----------
def setup(vertical, g):
    gh = vertical.get("ghost", {})
    res = {"etiquetas": [], "errores": []}
    for slug, s in gh.get("sections", {}).items():
        body = {"name": s["name"], "slug": slug, "description": s["description"][:500], "meta_title": "%s · %s" % (s["name"], vertical.get("name")),
                "meta_description": s["description"][:500]}
        st, found = g.call("GET", "/tags/slug/%s/" % slug)
        if st == 200 and found.get("tags"):
            st, r = g.call("PUT", "/tags/%s/" % found["tags"][0]["id"], {"tags": [body]})
        else:
            st, r = g.call("POST", "/tags/", {"tags": [body]})
        (res["etiquetas"] if st in (200, 201) else res["errores"]).append(slug if st in (200, 201) else (slug, r))
    nav = [{"label": l, "url": u} for l, u in gh.get("menu", [])]
    nav2 = [{"label": l, "url": u} for l, u in gh.get("secondary_menu", [])]
    st, r = g.call("PUT", "/settings/", {"settings": [{"key": "navigation", "value": json.dumps(nav, ensure_ascii=False)},
                                                      {"key": "secondary_navigation", "value": json.dumps(nav2, ensure_ascii=False)},
                                                      {"key": "timezone", "value": vertical.get("timezone", "Europe/Madrid")},
                                                      {"key": "locale", "value": "es"}]})
    res["menu"] = "ok" if st == 200 else ("no permitido a la integración (%s): hazlo a mano en Ajustes → Navegación" % st)
    return res


def unfeature_others(g, keep_featured, keep_segunda, arts_by_id, vertical, latest, today):
    """Quita la marca de apertura y «#segunda» a las piezas de ediciones anteriores."""
    fixed = []
    st, r = g.call("GET", "/posts/?limit=all&fields=id,slug&filter=featured:true")
    st2, r2 = g.call("GET", "/posts/?limit=all&fields=id,slug&filter=tag:hash-segunda")
    stale = {p["slug"] for p in (r.get("posts") or []) if p["slug"] != keep_featured} | {p["slug"] for p in (r2.get("posts") or []) if p["slug"] != keep_segunda}
    for slug in stale:
        a = arts_by_id.get(slug)
        if not a:
            continue
        st, cur = g.call("GET", "/posts/slug/%s/?fields=id,updated_at,status" % slug)
        if st != 200:
            continue
        p = cur["posts"][0]
        body = {"featured": False, "tags": build_tags(a, vertical, latest), "updated_at": p["updated_at"]}
        st, _ = g.call("PUT", "/posts/%s/" % p["id"], {"posts": [body]})
        if st == 200:
            fixed.append(slug)
    return fixed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vertical", default="movilidad")
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--date")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--status", default="draft", choices=["draft", "published"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pages", action="store_true")
    ap.add_argument("--edition", help="AAAA-MM-DD: reescribe la página de la edición")
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--today", help="fecha de referencia para marcar futuros (por defecto, hoy)")
    a = ap.parse_args()
    vertical = load_vertical(a.vertical)
    base_url = os.environ.get("GHOST_URL", vertical.get("ghost", {}).get("site_url", "https://%s" % vertical.get("domain", ""))).rstrip("/")
    outdir = os.path.join(ROOT, "work", "ghost")
    os.makedirs(outdir, exist_ok=True)
    g = None
    if not a.dry_run:
        key = os.environ.get("GHOST_ADMIN_KEY")
        if not key or ":" not in key:
            sys.exit("Falta GHOST_ADMIN_KEY (id:secret) en el entorno; usa --dry-run para probar sin Ghost")
        g = Ghost(base_url, key)
    today = a.today or datetime.date.today().isoformat()
    report = {"modo": "prueba" if a.dry_run else a.status}

    if a.setup and g:
        report["setup"] = setup(vertical, g)
    if a.pages:
        report.update(publish_pages(a, vertical, g, outdir))
        if not (a.ids or a.date or a.all or a.edition):
            print(json.dumps(report, ensure_ascii=False, indent=1)); return

    all_arts = load_all_articles()
    by_id = {x["id"]: x for x in all_arts}
    latest = latest_edition_date()
    PICKS[latest] = edition_picks(all_arts, latest)
    if a.edition:
        PICKS[a.edition] = edition_picks(all_arts, a.edition)
    arts = [x for x in all_arts if (a.all or (a.ids and x["id"] in a.ids) or (a.date and x.get("date") == a.date))]
    if a.ids and a.pages:
        arts = [x for x in arts if x["id"] in by_id]

    authors, warn = (resolve_authors(vertical, g) if g else (dict(vertical.get("editorial", {}).get("ghost_authors", {})), []))
    img_cache_p = os.path.join(outdir, "imagenes-%s.json" % host(base_url))
    img_cache = json.load(open(img_cache_p)) if os.path.isfile(img_cache_p) else {}
    ok, bad, counts, imgs = 0, [], {}, 0
    for art in arts:
        post = build_post(art, vertical, base_url, latest, today)
        slug = author_slug(art, authors, vertical)
        if slug:
            post["authors"] = [{"slug": slug}]
        status = target_status(art, a.status)
        counts[status] = counts.get(status, 0) + 1
        if a.dry_run:
            with open(os.path.join(outdir, art["id"] + ".html"), "w", encoding="utf-8") as fh:
                fh.write(post["html"])
            with open(os.path.join(outdir, art["id"] + ".post.json"), "w", encoding="utf-8") as fh:
                json.dump({k: v for k, v in post.items() if k != "html"}, fh, ensure_ascii=False, indent=1)
            ok += 1
            continue
        if not a.no_images and "feature_image" not in post:
            lp = local_image(art)
            if lp:
                u = upload_image(g, lp, img_cache)
                if u:
                    post["feature_image"] = u; imgs += 1
                    json.dump(img_cache, open(img_cache_p, "w"), indent=1)
        res, err = upsert(post, status, g)
        if err:
            bad.append((art["id"], err))
        else:
            ok += 1
            with open(os.path.join(outdir, art["id"] + ".json"), "w", encoding="utf-8") as fh:
                json.dump(res, fh, ensure_ascii=False, indent=1)
        time.sleep(0.3)
    if arts:
        report.update({"piezas": len(arts), "por_estado": counts, "ok": ok, "imagenes": imgs, "errores": bad})
    report["avisos"] = warn + report.get("avisos", [])

    if a.edition:
        page = build_edition(a.edition, vertical, all_arts)
        if a.dry_run:
            open(os.path.join(outdir, "edicion-%s.html" % a.edition), "w", encoding="utf-8").write(page["html"])
            report["edicion"] = "work/ghost/edicion-%s.html" % a.edition
        else:
            res, err = upsert(page, "published", g, kind="pages")
            report["edicion"] = res or err
            lead, seg = PICKS[a.edition]
            report["apertura"], report["segunda"] = lead, seg
            report["destacadas_retiradas"] = unfeature_others(g, lead, seg, by_id, vertical, latest, today)
    if not (arts or a.edition or a.setup or a.pages):
        sys.exit("Nada que hacer (usa --ids, --date, --all, --edition, --pages o --setup)")
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
