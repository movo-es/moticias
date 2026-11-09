#!/usr/bin/env python3
"""MOTICIAS · La página de la edición en moticias.com (Ghost), solo biblioteca estándar.

  python3 -I src/ghost_edicion.py --date AAAA-MM-DD --dry-run     escribe work/ghost/edicion-hoy.html y no toca Ghost
  python3 -I src/ghost_edicion.py --date AAAA-MM-DD               actualiza la página «edicion-hoy» en Ghost

Qué es. La portada de www.moticias.com la pinta el tema a partir de dos cosas: los posts (cada pieza, que sube
src/ghost_publish.py) y la página de Ghost con slug `edicion-hoy`, de la que toma el título («Edición nº N · día»),
el extracto («Cierre HH:MM CET») y el cuerpo con los bloques de la edición: teletipo del BOE, documento del día, mapa de la
semana, tabla de boletines, próximos plazos y nota metodológica. Este script construye ese cuerpo desde `data/`
(editions, boletines, agenda, articles) y lo guarda en la página. Si la página no la actualiza nadie, la web sigue
enseñando la edición anterior aunque las piezas nuevas ya estén publicadas: eso fue lo que pasó el 9-11-2026.

Decisión de Rainer (9-11-2026): el resumen de la edición («Edición nº N de MOTICIAS, …: P piezas, B referencias del BOE y
A plazos. Apertura: …») NO va arriba, distrae; va al final de la edición, en pequeño. Por eso `meta_description` de la
página queda vacía (el tema la pintaba bajo el título) y el resumen se escribe como última línea del cuerpo.

Variables de entorno (nunca en el repositorio): GHOST_URL y GHOST_ADMIN_KEY (id:secret), como en ghost_publish.py.
"""
import argparse, datetime, glob, html, json, os, sys, urllib.error, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ghost_publish import admin_base, api, ghost_token  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLUG = "edicion-hoy"
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MES_CORTO = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
SECCION = {"tierra": "Tierra", "mar": "Mar", "aire": "Aire", "logistica": "Logística", "regulacion": "Regulación",
           "licitaciones": "Licitaciones", "analisis": "Análisis"}
MODO = {"tierra": "Tierra", "mar": "Mar", "aire": "Aire", "logistica": "Logística", "transversal": "transversal"}
TIPO_PLAZO = {"consulta": "Consulta", "evento": "Evento", "plazo": "Plazo", "vigor": "Entrada en vigor"}


def e(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def fecha(iso):
    return datetime.date.fromisoformat(iso[:10])


def larga(iso):  # «viernes, 6 de noviembre de 2026»
    d = fecha(iso)
    return "%s, %d de %s de %d" % (DIAS[d.weekday()], d.day, MESES[d.month - 1], d.year)


def sin_dia(iso):  # «6 de noviembre de 2026»
    d = fecha(iso)
    return "%d de %s de %d" % (d.day, MESES[d.month - 1], d.year)


def corta(iso):  # «6 nov 2026»
    d = fecha(iso)
    return "%d %s %d" % (d.day, MES_CORTO[d.month - 1], d.year)


def puntos(iso):  # «06.11.2026»
    return fecha(iso).strftime("%d.%m.%Y")


def carga(carpeta):
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", carpeta, "*.json"))):
        with open(p, encoding="utf-8") as fh:
            out.append(json.load(fh))
    return out


def publicadas_en_ghost(vertical):
    """Slugs de los posts publicados, leídos de la Content API pública de Ghost (clave pública en verticals/*.json → ghost).
    Sirve para enlazar en el mapa solo piezas que existen en la web (las del director sin aprobar son borradores).
    Si no se puede leer, devuelve None y se usa la regla de `status`."""
    g = vertical.get("ghost") or {}
    if not g.get("content_key"):
        return None
    slugs, page = set(), 1
    try:
        while True:
            q = urllib.parse.urlencode({"key": g["content_key"], "limit": 100, "page": page, "fields": "slug"})
            req = urllib.request.Request((g.get("admin_url") or g.get("url")).rstrip("/") + "/ghost/api/content/posts/?" + q,
                                         headers={"User-Agent": "Moticias/1.0 (+https://moticias.com)", "Accept-Version": "v5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read())
            slugs |= {p["slug"] for p in d.get("posts", [])}
            if not (d.get("meta", {}).get("pagination", {}).get("next")):
                return slugs
            page += 1
    except (urllib.error.URLError, ValueError, KeyError, OSError):
        return None


def construir(dia, vertical):
    base = ((vertical.get("ghost") or {}).get("url") or "https://%s" % vertical.get("domain", "www.moticias.com")).rstrip("/")
    en_ghost = publicadas_en_ghost(vertical)

    def publicada(a):
        if a.get("status") in ("pendiente", "borrador"):
            return False
        return a["id"] in en_ghost if en_ghost is not None else a.get("status") == "publicado"
    ed = json.load(open(os.path.join(ROOT, "data", "editions", dia + ".json"), encoding="utf-8"))
    arts = {a["id"]: a for a in carga("articles")}
    bols = sorted([b for b in carga("boletines") if b.get("edicion") == dia], key=lambda b: (b.get("fecha", ""), b.get("referencia", "")))
    hace7 = (fecha(dia) - datetime.timedelta(days=7)).isoformat()
    plazos = sorted([p for p in carga("agenda") if p.get("date", "") >= dia or p.get("edicion") == dia], key=lambda p: (p.get("date", ""), p.get("title", "")))[:14]
    con_lugar = [a for a in arts.values() if a.get("geo") and (publicada(a) or a.get("date") == dia and a.get("status") == "publicado") and hace7 < a.get("date", "") <= dia]
    con_lugar.sort(key=lambda a: (a.get("date", ""), a.get("published_time", "")), reverse=True)
    publicadas = [a for a in arts.values() if a.get("date") == dia and a.get("status") == "publicado"]  # las del día que van a la web
    lead = arts.get(ed.get("lead_id")) or {}

    # Todo el cuerpo va como una sola tarjeta HTML de Ghost (marcas kg-card-begin/end): sin ellas, Ghost convierte el HTML
    # a su editor y pierde clases, atributos data-* y las secciones, y el tema deja de pintar el mapa y los bloques.
    h = ['<!--kg-card-begin: html-->', '<div class="m-ed" data-date="%s">' % e(dia)]
    # Teletipo del BOE (el tema lo sube bajo la cabecera).
    h.append('<div class="m-ticker"><span class="m-ticker-label">%s %s</span><ul>%s</ul></div>' % (
        e(ed.get("ticker_label") or "Boletines"), e(corta(dia)),
        "".join('<li><b>%s</b> <a href="%s" rel="noopener">%s</a></li>' % (e(t.get("ref")), e(t.get("url")), e(t.get("text"))) for t in ed.get("ticker") or [])))
    # El documento del día.
    doc = ed.get("document") or {}
    if doc.get("title"):
        guia = [l.strip() for l in (doc.get("summary") or "").split("\n") if l.strip()]
        meta = [x for x in (doc.get("source"), corta(doc["date"]) if doc.get("date") else None, doc.get("ref")) if x]
        h.append('<section class="m-doc"><div class="m-sh regulacion"><h2>El documento del día<small>fuente primaria</small></h2></div>'
                 '<div class="m-doc-card"><div class="m-kicker regulacion">%s</div><h3><a href="%s" rel="noopener">%s</a></h3>'
                 '<ul class="m-doc-guide">%s</ul><div class="m-meta"><span class="m-badge">%s</span>%s</div></div></section>' % (
                     e(doc.get("kicker")), e(doc.get("url")), e(doc["title"]), "".join("<li>%s</li>" % e(l) for l in guia),
                     e(meta[0]), "".join("<span>%s</span>" % e(m) for m in meta[1:])))
    # El mapa de la semana.
    if con_lugar:
        h.append('<section class="m-mapa"><div class="m-sh"><h2>El mapa de la semana<small>%d piezas con lugar en los últimos siete días</small></h2></div>'
                 '<div class="m-map-grid"><div class="m-map" data-map="" aria-hidden="true"></div><ul class="m-map-list">%s</ul></div></section>' % (
                     len(con_lugar), "".join(
                         '<li data-lat="%s" data-lon="%s" data-sec="%s"><span class="m-place">%s</span><span class="m-kicker %s">%s</span><a href="%s/%s/">%s</a></li>' % (
                             e(a["geo"].get("lat")), e(a["geo"].get("lon")), e(a.get("section")), e(a["geo"].get("place")), e(a.get("section")),
                             e(SECCION.get(a.get("section"), a.get("section"))), base, e(a["id"]), e(a.get("title"))) for a in con_lugar)))
    # Boletines oficiales.
    if bols:
        dias_boe = sorted({b.get("fecha") for b in bols if b.get("fecha")})
        etiqueta = "BOE " + (corta(dias_boe[-1]) if len(dias_boe) == 1 else "%s y %s" % (corta(dias_boe[0]), corta(dias_boe[-1])))
        filas = []
        for b in bols:
            modo = (b.get("modos") or ["transversal"])[0]
            filas.append('<tr><td class="date">%s</td><td class="ref"><a href="%s" rel="noopener">%s</a></td><td class="org">%s</td>'
                         '<td class="t"><a href="%s" rel="noopener">%s</a>%s</td><td><span class="m-tag %s">%s</span></td></tr>' % (
                             e(puntos(b["fecha"])), e(b.get("url")), e(b.get("referencia")), e(b.get("organo")), e(b.get("url")),
                             e(b.get("titulo_corto") or b.get("titulo")), '<div class="nota">%s</div>' % e(b["nota"]) if b.get("nota") else "",
                             e(modo), e(MODO.get(modo, modo))))
        h.append('<section class="m-boletines"><div class="m-sh"><h2>Boletines oficiales<small>%d referencias seleccionadas · %s</small></h2></div>'
                 '<div class="m-table-wrap"><table class="m-data"><thead><tr><th>Fecha</th><th>Referencia</th><th>Órgano</th><th>Qué es</th><th>Modo</th></tr></thead>'
                 '<tbody>%s</tbody></table></div></section>' % (len(bols), e(etiqueta), "".join(filas)))
    # Próximos plazos.
    if plazos:
        h.append('<section class="m-plazos"><div class="m-sh licitaciones"><h2>Próximos plazos<small>ofertas, consultas y entradas en vigor</small></h2></div><div class="m-deadlines">%s</div></section>' % "".join(
            '<div class="m-deadline %s" data-date="%s"><div class="when"><span>%s · %s</span><b class="m-countdown"></b></div>'
            '<div class="what"><a href="%s" rel="noopener">%s</a></div><div class="who">%s</div></div>' % (
                e(p.get("kind")), e(p.get("date")), e(puntos(p["date"])), e(TIPO_PLAZO.get(p.get("kind"), p.get("kind"))),
                e(p.get("url")), e(p.get("title")), e(p.get("authority"))) for p in plazos))
    # Nota metodológica.
    if ed.get("note_metodologica"):
        h.append('<section class="m-nota"><div class="m-sh"><h2>Nota metodológica</h2></div><p>%s</p></section>' % e(ed["note_metodologica"]))
    # El resumen, al final y en pequeño (decisión del 9-11-2026), y el cierre.
    resumen = "Edición nº %s de MOTICIAS, %s: %d piezas publicadas, %d referencias del BOE y %d plazos a la vista.%s" % (
        ed.get("number"), larga(dia), len(publicadas), len(bols), len([p for p in plazos if p.get("date", "") >= dia]),
        " Apertura: «%s»." % lead["title"] if lead.get("title") else "")
    h.append('<p class="m-resumen-ed" style="font-size:.8em;opacity:.7;margin-top:1.5em">%s</p>' % e(resumen))
    h.append('<p class="m-fin-ed">FIN DE EDICIÓN · %s, %s CET</p>' % (e(sin_dia(dia)), e(ed.get("closed_at") or "")))
    h.append("</div>")
    h.append("<!--kg-card-end: html-->")
    pagina = {"title": "Edición nº %s · %s" % (ed.get("number"), larga(dia)), "custom_excerpt": "Cierre %s CET" % (ed.get("closed_at") or ""),
              # Un espacio de anchura cero: con la descripción vacía, Ghost pinta en su lugar la descripción del sitio, y el tema
              # la mostraba bajo el título. Hasta que el tema versionado quite ese párrafo (y la regla CSS de
              # ghost/inyeccion-cabecera.html lo oculte), así queda en blanco.
              "meta_description": "\u200b", "html": "\n".join(h)}
    return pagina, {"piezas": len(publicadas), "boletines": len(bols), "plazos": len(plazos), "con_lugar": len(con_lugar), "resumen": resumen}


def subir(pagina, base_url, token):
    base = admin_base(base_url)
    st, r = api("GET", base + "/ghost/api/admin/pages/slug/%s/?fields=id,updated_at" % SLUG, token)
    if st == 200 and r.get("pages"):
        p = r["pages"][0]
        st, r = api("PUT", base + "/ghost/api/admin/pages/%s/?source=html" % p["id"], token, {"pages": [dict(pagina, updated_at=p["updated_at"])]})
    else:
        st, r = api("POST", base + "/ghost/api/admin/pages/?source=html", token, {"pages": [dict(pagina, slug=SLUG, status="published")]})
    if st not in (200, 201):
        return None, r
    p = r["pages"][0]
    return {"id": p["id"], "url": p.get("url"), "updated_at": p.get("updated_at")}, None


def subir_inyeccion(base_url, token):
    """Sube ghost/inyeccion-cabecera.html y ghost/inyeccion-pie.html a Settings → Code injection (la clave de integración
    puede editar ajustes, pero no el tema: los temas solo se suben desde el panel con sesión de usuario)."""
    base = admin_base(base_url)
    cab = open(os.path.join(ROOT, "ghost", "inyeccion-cabecera.html"), encoding="utf-8").read().strip()
    pie = open(os.path.join(ROOT, "ghost", "inyeccion-pie.html"), encoding="utf-8").read().strip()
    st, r = api("PUT", base + "/ghost/api/admin/settings/", token,
                {"settings": [{"key": "codeinjection_head", "value": cab}, {"key": "codeinjection_foot", "value": pie}]})
    return st, (None if st == 200 else r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="AAAA-MM-DD de la edición (obligatorio salvo con --inyeccion)")
    ap.add_argument("--vertical", default="movilidad")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--inyeccion", action="store_true", help="sube solo ghost/inyeccion-*.html a Code injection, sin tocar la página")
    a = ap.parse_args()
    vertical = json.load(open(os.path.join(ROOT, "verticals", a.vertical + ".json"), encoding="utf-8"))
    if a.inyeccion:
        key = os.environ.get("GHOST_ADMIN_KEY")
        if not key or ":" not in key:
            sys.exit("Falta GHOST_ADMIN_KEY (id:secret) en el entorno")
        base_url = os.environ.get("GHOST_URL", "https://%s" % vertical.get("domain", "")).rstrip("/")
        st, err = subir_inyeccion(base_url, ghost_token(key))
        print(json.dumps({"inyeccion": "subida" if st == 200 else "error", "detalle": err}, ensure_ascii=False)); return
    if not a.date:
        sys.exit("Falta --date AAAA-MM-DD")
    pagina, cifras = construir(a.date, vertical)
    os.makedirs(os.path.join(ROOT, "work", "ghost"), exist_ok=True)
    with open(os.path.join(ROOT, "work", "ghost", SLUG + ".html"), "w", encoding="utf-8") as fh:
        fh.write(pagina["html"])
    if a.dry_run:
        print(json.dumps(dict(cifras, modo="prueba", title=pagina["title"], fichero="work/ghost/%s.html" % SLUG), ensure_ascii=False)); return
    key = os.environ.get("GHOST_ADMIN_KEY")
    if not key or ":" not in key:
        sys.exit("Falta GHOST_ADMIN_KEY (id:secret) en el entorno; usa --dry-run para probar sin Ghost")
    base_url = os.environ.get("GHOST_URL", "https://%s" % vertical.get("domain", "")).rstrip("/")
    res, err = subir(pagina, base_url, ghost_token(key))
    if err:
        sys.exit("Ghost no aceptó la página: %s" % json.dumps(err, ensure_ascii=False)[:400])
    print(json.dumps(dict(cifras, modo="publicada", title=pagina["title"], **res), ensure_ascii=False))


if __name__ == "__main__":
    main()
