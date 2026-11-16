#!/usr/bin/env python3
"""MOTICIAS · Página «Agenda» de moticias.com (cambio OpenSpec `agenda-de-eventos`, 16-11-2026). Patrón de ghost_grupo.py.

Genera desde `data/eventos/` y `verticals/movilidad.json → agenda`:
- la página `moticias.com/agenda/` (todo el contenido en el HTML: respuesta directa, mapa, «Por lugar», leyenda,
  lista, columna lateral, archivo y preguntas; el script del sitio solo añade los filtros), con ItemList y FAQPage;
- la página «Subir mi evento» (slug `agenda-subir-mi-evento`; con las rutas de Ghost, en /agenda/subir-mi-evento/);
- una ficha por evento (entrada de Ghost con etiqueta interna #agenda y datos Event) en /agenda/<evento>/, solo cuando
  Ghost tiene ya las rutas de `ghost/routes.yaml` (sin ellas la cita enlaza a su sitio en la propia página);
- el calendario `app/public/feed/agenda.ics`.

  python3 -I src/ghost_agenda.py --html [--hoy AAAA-MM-DD]     imprime el HTML de la agenda (para revisarlo)
  python3 -I src/ghost_agenda.py --ficha <id> | --subir           imprime una ficha o el formulario
  python3 -I src/ghost_agenda.py --ics app/public/feed/agenda.ics
  python3 -I src/ghost_agenda.py --publicar                     sube páginas y fichas a Ghost (GHOST_URL, GHOST_ADMIN_KEY)
"""
import argparse, datetime, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import eventos as EV  # noqa: E402

E = lambda s: html.escape(str(s if s is not None else ""), quote=True)  # noqa: E731
BASE = "https://www.moticias.com/"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MES_C = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic"]
ESTADO_LD = {"publicado": "EventScheduled", "aplazado": "EventPostponed", "cancelado": "EventCancelled", "pasado": "EventScheduled",
             "fecha_por_confirmar": "EventScheduled"}
MODO_LD = {"presencial": "OfflineEventAttendanceMode", "en línea": "OnlineEventAttendanceMode", "híbrida": "MixedEventAttendanceMode"}


# ---------- utilidades ----------
def fecha_larga(f):
    d = datetime.date.fromisoformat(f)
    return "%d de %s de %d" % (d.day, MESES[d.month - 1], d.year)


def fechas(e):
    """«17–18 nov 2026», «30 nov – 3 dic 2026», «10 dic 2026», «enero de 2027 (por confirmar)»."""
    if not e.get("inicio"):
        y, m = e["mes_previsto"].split("-")
        return "%s de %s (por confirmar)" % (MESES[int(m) - 1], y)
    a, b = datetime.date.fromisoformat(e["inicio"]), datetime.date.fromisoformat(EV.fin_de(e))
    if a == b:
        return "%d %s %d" % (a.day, MES_C[a.month - 1], a.year)
    if (a.year, a.month) == (b.year, b.month):
        return "%d–%d %s %d" % (a.day, b.day, MES_C[a.month - 1], a.year)
    if a.year == b.year:
        return "%d %s – %d %s %d" % (a.day, MES_C[a.month - 1], b.day, MES_C[b.month - 1], a.year)
    return "%d %s %d – %d %s %d" % (a.day, MES_C[a.month - 1], a.year, b.day, MES_C[b.month - 1], b.year)


def nombre_mes(m):
    y, mm = m.split("-")
    return "%s %s" % (MESES[int(mm) - 1], y)


def y_lista(xs):
    xs = [x for x in xs if x]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1] if xs else ""


def ciudad_id(e):
    return EV.slug(e.get("ciudad"))


def temas(v):
    return EV.cfg(v)["temas"]


def tema_de(v, tid):
    return next((t for t in temas(v) if t["id"] == tid), {"id": tid, "nombre": tid, "color": "#ccc"})


def url_ficha(e, rutas_ok):
    return (BASE + "agenda/%s/" % e["id"]) if rutas_ok else (BASE + "agenda/#%s" % e["id"])


def url_subir(rutas_ok, v=None):
    g = EV.cfg(v)["ghost"]
    return BASE + (g["ruta_subir"].strip("/") if rutas_ok else g["slug_subir"]) + "/"


def ld(obj):
    return '<script type="application/ld+json">%s</script>' % json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def precio_num(p):
    if not p or re.search(r"\bgrat", p, re.I) and not re.search(r"\d", p):
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*€", p)
    return m.group(1).replace(",", ".") if m else None


def evento_ld(e, v, rutas_ok):
    t = tema_de(v, e["tema"])
    o = {"@type": "Event", "name": e["titulo"], "description": e["resumen"], "url": url_ficha(e, rutas_ok),
         "eventStatus": "https://schema.org/" + ESTADO_LD.get(e["estado"], "EventScheduled"),
         "eventAttendanceMode": "https://schema.org/" + MODO_LD.get(e.get("modalidad"), "OfflineEventAttendanceMode"),
         "location": {"@type": "Place", "name": e.get("sede") or e["ciudad"],
                      "address": {"@type": "PostalAddress", "addressLocality": e["ciudad"], "addressRegion": EV.territorios(v)[e["territorio"]]["nombre"], "addressCountry": "ES"},
                      "geo": {"@type": "GeoCoordinates", "latitude": e["geo"]["lat"], "longitude": e["geo"]["lon"]}},
         "organizer": [{"@type": "Organization", "name": n} for n in e["organizadores"]], "keywords": t["nombre"], "inLanguage": "es-ES"}
    if e.get("inicio"):
        o["startDate"], o["endDate"] = e["inicio"], EV.fin_de(e)
    if e.get("url_oficial") or e.get("url_inscripcion"):
        o["sameAs"] = e.get("url_oficial") or e.get("url_inscripcion")
    n = precio_num(e.get("precio"))
    if n and e.get("url_inscripcion"):
        o["offers"] = {"@type": "Offer", "url": e["url_inscripcion"], "price": n, "priceCurrency": "EUR", "description": e["precio"]}
    elif e.get("precio") and re.search(r"\bgrat", e["precio"], re.I) and not re.search(r"\d", e["precio"]):
        o["isAccessibleForFree"] = True
    return o


def huella(evs, dia=None):
    """Cambia si cambian los eventos, el día (el periodo se mueve) o este código: entonces el cron rehace la agenda."""
    import hashlib
    h = hashlib.sha256()
    h.update(json.dumps(sorted(evs, key=lambda e: e["id"]), ensure_ascii=False, sort_keys=True).encode("utf-8"))
    h.update((dia or EV.hoy()).encode())
    h.update(open(os.path.abspath(__file__), "rb").read())
    return h.hexdigest()[:16]


# ---------- mapa ----------
def _spain():
    s = open(os.path.join(ROOT, "portal", "spain.js"), encoding="utf-8").read()
    return json.loads(s[s.index("=") + 1:].strip().rstrip(";"))


def proyectar(sp, lon, lat):
    m = sp["meta"]
    x, y = lon, lat
    if lat < 30 and lon < -12:  # Canarias, en su recuadro
        x, y = x + m["dlon"], y + m["dlat"]
    return (x - m["lon0"]) * m["k"] * m["cos0"], -(y - m["lat0"]) * m["k"]


def lugares(evs, v):
    """Una marca por ciudad, con sus citas y temas, en el orden del mapa (de norte a sur)."""
    out = {}
    for e in evs:
        c = out.setdefault(ciudad_id(e), {"id": ciudad_id(e), "ciudad": e["ciudad"], "lat": e["geo"]["lat"], "lon": e["geo"]["lon"], "evs": []})
        c["evs"].append(e)
    for c in out.values():
        c["temas"] = sorted({e["tema"] for e in c["evs"]})
    return sorted(out.values(), key=lambda c: (-len(c["evs"]), c["ciudad"]))


def mapa_svg(evs, v):
    sp = _spain()
    x0, y0, x1, y1 = sp["bbox"]
    pad = 26
    cb = sp["canariasBox"]
    pins = []
    for c in sorted(lugares(evs, v), key=lambda c: c["lat"], reverse=True):
        x, y = proyectar(sp, c["lon"], c["lat"])
        n = len(c["evs"])
        mixto = len(c["temas"]) > 1
        color = "#FFFFFF" if mixto else tema_de(v, c["temas"][0])["color"]
        r = 9 if n == 1 else 12 + min(n, 6)
        izq = c["lon"] > 1.0 or c["lat"] < 30  # Barcelona y Canarias (su recuadro está a la derecha): nombre a la izquierda
        etiqueta = '<text class="ma-pin-nombre" x="%s" y="6" text-anchor="%s">%s</text>' % (
            ("%.1f" % -(r + 5)) if izq else ("%.1f" % (r + 5)), "end" if izq else "start", E(c["ciudad"]))
        pins.append(
            '<g class="ma-pin%s" data-ciudad="%s" data-temas="%s" role="button" tabindex="0" aria-label="%s: %d %s" transform="translate(%.1f %.1f)">'
            '<circle class="ma-pin-toque" r="22"/>%s<circle class="ma-pin-marca" r="%d" fill="%s"/>'
            '<text class="ma-pin-n" y="4.5" text-anchor="middle">%s</text>%s</g>' % (
                " ma-mixto" if mixto else "", E(c["id"]), E(" ".join(c["temas"])), E(c["ciudad"]), n, "cita" if n == 1 else "citas", x, y,
                '<circle class="ma-pin-aro" r="%d"/>' % (r + 4) if mixto else "", r, color, n if n > 1 else "", etiqueta))
    return ('<svg class="ma-svg" viewBox="%.1f %.1f %.1f %.1f" role="img" aria-labelledby="ma-svg-t">'
            '<title id="ma-svg-t">Mapa de España con las ciudades de la agenda</title>'
            '<path class="ma-borde" d="%s"/><path class="ma-ccaa" d="%s"/>'
            '<rect class="ma-canarias" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="4"/>%s</svg>') % (
        x0 - pad, y0 - pad, x1 - x0 + 2 * pad, y1 - y0 + 2 * pad, sp["border"], sp["ccaa"],
        cb[0] - 14, cb[1] - 14, cb[2] - cb[0] + 28, cb[3] - cb[1] + 28, "".join(pins))


# ---------- piezas de la página ----------
def cita_html(e, v, rutas_ok, orden):
    t = tema_de(v, e["tema"])
    est = {"aplazado": "Aplazado", "cancelado": "Cancelado"}.get(e["estado"])
    org = y_lista(e["organizadores"])
    boton = ('<a class="ma-boton" href="%s" target="_blank" rel="noopener">Inscripción<span class="ma-sr"> en %s (se abre en otra pestaña)</span></a>' %
             (E(e["url_inscripcion"]), E(e["titulo_corto"]))) if e.get("url_inscripcion") and e["estado"] != "cancelado" else ""
    titulo = ('<a href="%s">%s</a>' % (E(url_ficha(e, True)), E(e["titulo"]))) if rutas_ok else E(e["titulo"])
    return (
        '<li class="ma-cita" id="%s" data-tema="%s" data-ciudad="%s" data-meses="%s" data-inicio="%s" data-orden-tema="%d" data-corto="%s">'
        '<p class="ma-cita-cab"><time datetime="%s">%s</time> · <span class="ma-tema"><i style="background:%s"></i>%s</span> · %s%s%s</p>'
        '<h3>%s</h3><p class="ma-donde"><strong>%s</strong>%s</p><p>%s</p>'
        '<p class="ma-org">Organiza: %s</p>%s%s</li>') % (
        E(e["id"]), E(e["tema"]), E(ciudad_id(e)), E(" ".join(EV.meses_de(e))), E(e["inicio"]), orden, E(e["titulo_corto"]),
        E(e["inicio"]), E(fechas(e)), E(t["color"]), E(t["nombre"]), E(e["formato"]),
        ' · <span class="ma-publico">Abierta al público</span>' if e.get("publico") == "general" else "",
        ' · <span class="ma-estado">%s</span>' % est if est else "",
        titulo, E(e["ciudad"]), (" · " + E(e["sede"])) if e.get("sede") else "", E(e["resumen"]), E(org),
        ('<p class="ma-precio">Precio: %s</p>' % E(e["precio"])) if e.get("precio") else "",
        '<p class="ma-accion">%s%s</p>' % (boton, (' <span class="ma-nota">%s</span>' % E(e["nota"])) if e.get("nota") else ""))


def respuesta(vis, dia, hasta):
    n = {}
    for e in vis:
        n[e["ciudad"]] = n.get(e["ciudad"], 0) + 1
    top = [c for c, k in sorted(n.items(), key=lambda x: (-x[1], x[0])) if k > 1][:2]
    return ("<strong>La agenda de MOTICIAS reúne %d ferias, congresos y jornadas de transportes, movilidad y turismo en %d ciudades "
            "de España entre el %s y el %s</strong>%s. Cada fecha, sede y enlace está comprobado en la web del organizador.") % (
        len(vis), len(n), fecha_larga(dia), fecha_larga(hasta), (", con más citas en " + y_lista(["%s (%d)" % (c, n[c]) for c in top])) if top else "")


PREGUNTAS = [
    ("¿Qué recoge la agenda de MOTICIAS?", "Ferias, congresos, jornadas y encuentros profesionales de transportes, movilidad y turismo que se celebran en España en los próximos tres meses, más las grandes ferias del sector con días profesionales, marcadas «Abierta al público»."),
    ("¿Cómo se comprueban los datos?", "La redacción comprueba cada fecha, sede y enlace en la web del organizador o en un comunicado suyo, y lo vuelve a comprobar cada semana. Si dos fuentes discrepan, manda el organizador; lo que no se ha podido comprobar se dice."),
    ("¿Cómo publico mi evento?", "Con el formulario «Subir mi evento». La redacción lo revisa en la web del organizador y, si encaja, lo publica gratis. Los datos de la persona responsable no se publican."),
]


def construir(evs, v, dia=None, rutas_ok=False):
    c = EV.cfg(v)
    dia, hasta = EV.periodo(dia, v)
    vis = EV.visibles(evs, dia, v)
    orden_t = {t["id"]: i for i, t in enumerate(temas(v))}
    por_tema = sorted(vis, key=lambda e: (orden_t.get(e["tema"], 99), e["inicio"], e["id"]))
    meses = sorted({m for e in vis for m in EV.meses_de(e) if dia[:7] <= m <= hasta[:7]})
    n_mes = {m: sum(1 for e in vis if m in EV.meses_de(e)) for m in meses}
    n_tema = {t["id"]: sum(1 for e in vis if e["tema"] == t["id"]) for t in temas(v)}
    sin = [t["nombre"] for t in temas(v) if not n_tema[t["id"]]]
    lug = lugares(vis, v)
    comprobado = max([e.get("comprobado_at") or "" for e in vis] or [dia])
    h = ['<!--kg-card-begin: html-->', '<div class="m-agenda" data-desde="%s" data-hasta="%s" data-huella="%s" data-rutas="%d">' % (
        E(dia), E(hasta), huella(evs, dia), int(bool(rutas_ok))), ESTILO]
    h.append('<p class="respuesta-directa">%s</p>' % respuesta(vis, dia, hasta))
    h.append('<div class="ma-rejilla"><div class="ma-principal">')
    # Mapa
    h.append('<section class="ma-mapa" aria-label="Mapa de la agenda">')
    h.append('<div class="ma-meses" role="group" aria-label="Mes"><button type="button" class="ma-mes" data-mes="" aria-pressed="true">Todos los meses <b>%d</b></button>%s</div>' % (
        len(vis), "".join('<button type="button" class="ma-mes" data-mes="%s" aria-pressed="false">%s <b>%d</b></button>' % (m, E(nombre_mes(m).capitalize()), n_mes[m]) for m in meses)))
    h.append('<div class="ma-mapa-cuerpo"><div class="ma-mapa-svg">%s</div>' % mapa_svg(vis, v))
    h.append('<div class="ma-lugares"><h3>Por lugar</h3><ul>%s</ul></div></div>' % "".join(
        '<li data-ciudad="%s"><button type="button" class="ma-lugar" data-ciudad="%s" aria-pressed="false"><span>%s</span> <b>%d</b></button>'
        '<span class="ma-lugar-titulos">%s</span></li>' % (E(l["id"]), E(l["id"]), E(l["ciudad"]), len(l["evs"]),
                                                          E(" · ".join(e["titulo_corto"] for e in l["evs"]))) for l in lug))
    h.append('<div class="ma-leyenda" role="group" aria-label="Tema">%s</div>' % "".join(
        '<button type="button" class="ma-tema-b" data-tema="%s" aria-pressed="false"%s><i style="background:%s"></i>%s <b>%d</b></button>' % (
            E(t["id"]), " disabled" if not n_tema[t["id"]] else "", E(t["color"]), E(t["nombre"]), n_tema[t["id"]]) for t in temas(v)))
    h.append('<p class="ma-filtros"><button type="button" class="ma-quitar">Quitar filtros</button> <span class="ma-cuenta" aria-live="polite"></span></p></section>')
    # Orden y lista
    h.append('<div class="ma-orden" role="group" aria-label="Ordenar la lista">Ordenar la lista: '
             '<button type="button" data-orden="tema" aria-pressed="true">Por tema</button> <button type="button" data-orden="fecha" aria-pressed="false">Por fecha</button></div>')
    h.append('<p class="ma-vacio" hidden>Ninguna cita con esos filtros. <button type="button" class="ma-quitar">Quitar filtros</button></p>')
    h.append('<ol class="ma-lista">%s</ol>' % "".join(cita_html(e, v, rutas_ok, i) for i, e in enumerate(por_tema)))
    if sin:
        h.append('<p class="ma-sin">Sin citas en el periodo: %s.</p>' % E(y_lista(sin)))
    h.append('</div>')
    # Lateral
    pc, des = EV.por_confirmar(evs), EV.despues(evs, dia, v)
    h.append('<aside class="ma-lateral">')
    h.append('<section><h2>%s</h2><p>%s</p><p><a class="ma-boton" href="%s">Subir mi evento</a></p></section>' % (
        E(c["textos"]["organizas"]), E(c["textos"]["organizas_texto"]), E(url_subir(rutas_ok, v))))
    h.append('<section><h2>Lleva la agenda contigo</h2><p>Suscríbete al calendario y las citas aparecerán en el tuyo (Google, Outlook, Apple).</p>'
             '<p><a class="ma-boton ma-boton-2" href="https://app.moticias.com/feed/agenda.ics">Calendario .ics</a></p></section>')
    if pc:
        h.append('<section><h2>Con fecha por confirmar</h2><ul>%s</ul></section>' % "".join(
            '<li><strong>%s</strong> · %s · %s<br><span class="ma-nota">%s</span></li>' % (E(e["titulo_corto"]), E(e["ciudad"]), E(fechas(e)), E(e.get("nota") or "")) for e in pc))
    if des:
        h.append('<section><h2>Después del %s</h2><ul>%s</ul></section>' % (E(fecha_larga(hasta)), "".join(
            '<li><strong>%s</strong> · %s · %s</li>' % (E(e["titulo_corto"]), E(fechas(e)), E(e["ciudad"])) for e in des)))
    h.append('</aside></div>')
    arch = EV.archivo(evs, dia)
    if arch:
        h.append('<details class="ma-archivo"><summary>Archivo: %d citas ya celebradas</summary><ul>%s</ul></details>' % (len(arch), "".join(
            '<li>%s · <strong>%s</strong> · %s</li>' % (E(fechas(e)), E(e["titulo"]), E(e["ciudad"])) for e in arch)))
    h.append('<section class="ma-preguntas"><h2>Preguntas frecuentes</h2>%s</section>' % "".join('<h3>%s</h3><p>%s</p>' % (E(q), E(a)) for q, a in PREGUNTAS))
    h.append('<p class="ma-pie">Última comprobación: %s. %s</p>' % (E(fecha_larga(comprobado)), E(c["textos"]["aviso_pie"])))
    h.append('</div><!--kg-card-end: html-->')
    grafo = {"@context": "https://schema.org", "@graph": [
        {"@type": "ItemList", "name": c["textos"]["titulo"], "url": BASE + "agenda/", "numberOfItems": len(vis),
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": evento_ld(e, v, rutas_ok)} for i, e in enumerate(sorted(vis, key=lambda e: e["inicio"]))]},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in PREGUNTAS]}]}
    titulo = c["textos"]["titulo"]
    desc = "%d ferias, congresos y jornadas de transportes, movilidad y turismo en %d ciudades de España hasta el %s, comprobados en la web de cada organizador." % (
        len(vis), len({e["ciudad"] for e in vis}), fecha_larga(hasta))
    # El tema pone el extracto bajo el título: una línea que complementa la respuesta directa, sin repetir sus cifras.
    return {"title": titulo, "slug": c["ghost"]["slug"], "html": "\n".join(h),
            "custom_excerpt": "Mapa, filtros por mes, ciudad y tema, ficha de cada cita y calendario para tu agenda. Actualizada cada semana.",
            "meta_title": titulo, "meta_description": desc[:300], "codeinjection_head": ld(grafo),
            "_resumen": {"citas": len(vis), "ciudades": len({e["ciudad"] for e in vis}), "meses": n_mes, "temas": {k: n for k, n in n_tema.items() if n},
                         "lugares": {l["ciudad"]: {"citas": len(l["evs"]), "mixto": len(l["temas"]) > 1} for l in lug}, "sin_citas": sin}}


def ficha(e, v, rutas_ok=True):
    t = tema_de(v, e["tema"])
    filas = [("Fechas", fechas(e)), ("Tema", t["nombre"]), ("Formato", e["formato"]), ("Modalidad", e.get("modalidad")),
             ("Público", EV.cfg(v)["publicos"].get(e.get("publico"))), ("Ciudad", e["ciudad"]), ("Sede", e.get("sede")),
             ("Comunidad", EV.territorios(v)[e["territorio"]]["nombre"]), ("Organiza", y_lista(e["organizadores"])), ("Precio", e.get("precio")),
             ("Estado", EV.cfg(v)["estados"].get(e["estado"])), ("Nota", e.get("nota"))]
    h = ['<!--kg-card-begin: html-->', '<div class="m-agenda m-agenda-ficha">', ESTILO,
         '<p class="respuesta-directa"><strong>%s: %s en %s%s.</strong> %s</p>' % (E(e["titulo"]), E(fechas(e)), E(e["ciudad"]), (", " + E(e["sede"])) if e.get("sede") else "", E(e["resumen"])),
         '<dl class="ma-datos">%s</dl>' % "".join('<dt>%s</dt><dd>%s</dd>' % (E(k), E(x)) for k, x in filas if x)]
    if e.get("url_inscripcion") and e["estado"] not in ("cancelado", "pasado"):
        h.append('<p><a class="ma-boton" href="%s" target="_blank" rel="noopener">Inscripción</a>%s</p>' % (
            E(e["url_inscripcion"]), (' <a href="%s" target="_blank" rel="noopener">Web oficial</a>' % E(e["url_oficial"])) if e.get("url_oficial") else ""))
    h.append('<h2>Fuentes</h2><ul class="ma-fuentes">%s</ul>' % "".join(
        '<li><a href="%s" rel="noopener">%s</a> · comprobada el %s%s</li>' % (E(f["url"]), E(re.sub(r"^https?://(www\.)?", "", f["url"]).split("/")[0]), E(fecha_larga(f["fecha"])),
                                                                         (" · " + E(f["nota"])) if f.get("nota") else "") for f in e["fuentes"]))
    h.append('<p class="ma-pie">%s <a href="%sagenda/">Toda la agenda</a></p></div><!--kg-card-end: html-->' % (E(EV.cfg(v)["textos"]["aviso_pie"]), BASE))
    j = dict(evento_ld(e, v, rutas_ok), **{"@context": "https://schema.org"})
    return {"title": e["titulo"], "slug": e["id"], "html": "\n".join(h), "custom_excerpt": e["resumen"][:300],
            "meta_title": "%s · %s, %s" % (e["titulo_corto"], fechas(e), e["ciudad"]), "meta_description": e["resumen"][:300],
            "tags": [{"name": EV.cfg(v)["ghost"]["etiqueta_interna"]}], "codeinjection_head": ld(j)}


def subir(v, rutas_ok=False):
    c = EV.cfg(v)
    ter = [t for t in v["taxonomia"]["territorios"] if t.get("tipo") == "ccaa"]
    op = lambda xs: "".join('<option value="%s">%s</option>' % (E(a), E(b)) for a, b in xs)
    campo = lambda nombre, etiqueta, ctrl, ob=False, ayuda="": '<p class="ma-campo"><label for="f-%s">%s%s</label>%s%s</p>' % (
        nombre, E(etiqueta), ' <span aria-hidden="true">*</span>' if ob else "", ctrl, ('<small>%s</small>' % E(ayuda)) if ayuda else "")
    inp = lambda nombre, tipo="text", ob=False, extra="": '<input id="f-%s" name="%s" type="%s"%s%s>' % (nombre, nombre, tipo, " required" if ob else "", extra)
    h = ['<!--kg-card-begin: html-->', '<div class="m-agenda m-agenda-subir">', ESTILO,
         '<p class="respuesta-directa"><strong>Si organizas una feria, un congreso o una jornada de transportes, movilidad o turismo en España, '
         'cuéntanoslo aquí.</strong> La redacción comprueba los datos en tu web y, si encaja, lo publica gratis en la agenda de MOTICIAS. '
         'Te avisamos por correo al publicarlo, con el enlace a su ficha.</p>',
         '<div class="ma-rejilla"><div class="ma-principal">',
         '<form class="ma-form" method="post" action="%s?a=enviar" data-agenda-form novalidate>' % E(c["formulario"]["api"]),
         '<fieldset><legend>1. El evento</legend>',
         campo("titulo", "Nombre del evento", inp("titulo", ob=True, extra=' maxlength="200"'), True),
         campo("tema", "Tema", '<select id="f-tema" name="tema" required><option value="">Elige…</option>%s</select>' % op([(t["id"], t["nombre"]) for t in c["temas"]]), True),
         campo("formato", "Formato", '<select id="f-formato" name="formato"><option value="">Elige…</option>%s</select>' % op([(f, f) for f in c["formatos"]])),
         campo("inicio", "Fecha de inicio", inp("inicio", "date", True), True),
         campo("fin", "Fecha de fin", inp("fin", "date")),
         campo("ciudad", "Ciudad", inp("ciudad", ob=True, extra=' maxlength="80"'), True),
         campo("sede", "Sede", inp("sede", extra=' maxlength="160"')),
         campo("territorio", "Comunidad autónoma", '<select id="f-territorio" name="territorio" required><option value="">Elige…</option>%s</select>' % op([(t["id"], t["nombre"]) for t in ter]), True),
         campo("modalidad", "Modalidad", '<select id="f-modalidad" name="modalidad">%s</select>' % op([(m, m.capitalize()) for m in c["modalidades"]])),
         campo("resumen", "Resumen", '<textarea id="f-resumen" name="resumen" rows="4" required maxlength="600"></textarea>', True, "Hasta 60 palabras: de qué trata y para quién."),
         campo("url_inscripcion", "Enlace de inscripción", inp("url_inscripcion", "url", True, ' placeholder="https://"'), True),
         campo("precio", "Precio", inp("precio", extra=' maxlength="120" placeholder="Gratis, 25 € + IVA…"')),
         campo("cartel", "Cartel (enlace a la imagen)", inp("cartel", "url", extra=' placeholder="https://"')),
         '</fieldset><fieldset><legend>2. Quién organiza</legend>',
         campo("entidad", "Entidad organizadora", inp("entidad", ob=True, extra=' maxlength="200"'), True),
         campo("entidad_tipo", "Tipo de entidad", '<select id="f-entidad_tipo" name="entidad_tipo">%s</select>' % op([(x, x) for x in ("Empresa", "Asociación", "Administración pública", "Universidad o centro de investigación", "Recinto ferial o de congresos", "Otra")])),
         campo("entidad_web", "Web de la entidad", inp("entidad_web", "url", extra=' placeholder="https://"')),
         '</fieldset><fieldset><legend>3. Persona responsable <span class="ma-nota">(no se publica)</span></legend>',
         campo("nombre", "Nombre y apellidos", inp("nombre", ob=True, extra=' maxlength="120" autocomplete="name"'), True),
         campo("cargo", "Cargo", inp("cargo", extra=' maxlength="160" autocomplete="organization-title"')),
         campo("correo", "Correo", inp("correo", "email", True, ' maxlength="200" autocomplete="email"'), True),
         campo("telefono", "Teléfono", inp("telefono", "tel", extra=' maxlength="40" autocomplete="tel"')),
         '</fieldset><fieldset><legend>4. Permisos</legend>',
         '<p class="ma-check"><input id="f-p1" name="permiso_tratamiento" type="checkbox" value="1" required> <label for="f-p1">%s *</label></p>' % E(PERMISOS["tratamiento"]),
         '<p class="ma-check"><input id="f-p2" name="permiso_boletin" type="checkbox" value="1"> <label for="f-p2">%s</label></p>' % E(PERMISOS["boletin"]),
         '<p class="ma-check"><input id="f-p3" name="permiso_comercial" type="checkbox" value="1"> <label for="f-p3">%s</label></p>' % E(PERMISOS["comercial"]),
         '<p class="ma-nota">Responsable del tratamiento: %s. Puedes ejercer tus derechos escribiendo a privacidad@moticias.com. Más en <a href="%sprivacidad/">Privacidad</a>.</p>' % (E(c["formulario"]["responsable"]), BASE),
         '</fieldset>',
         '<p class="ma-trampa" aria-hidden="true"><label for="f-web2">No rellenes este campo</label><input id="f-web2" name="web2" type="text" tabindex="-1" autocomplete="off"></p>',
         '<input type="hidden" name="t" value="">',
         '<p><button type="submit" class="ma-boton">Enviar mi evento</button></p><p class="ma-resultado" role="status" aria-live="polite"></p>',
         '</form></div><aside class="ma-lateral">',
         '<section><h2>Qué pasa después</h2><ol><li><strong>Revisión.</strong> La redacción comprueba fecha, sede y enlace en la web del organizador, normalmente en dos días laborables.</li>'
         '<li><strong>Publicación.</strong> Si encaja, el editor jefe lo publica en la agenda, con su ficha.</li>'
         '<li><strong>Aviso.</strong> Te escribimos con el enlace a la ficha, o para pedirte lo que falte.</li></ol></section>',
         '<section><h2>Qué publicamos</h2><p>Ferias, congresos, jornadas y encuentros profesionales de transportes, movilidad y turismo en España. '
         'Publicar es gratis. No publicamos los datos de la persona responsable: solo la entidad organizadora.</p></section>',
         '<section><h2>¿Tienes una nota de prensa?</h2><p>Para noticias y comunicados, usa la <a href="https://app.moticias.com/prensa/">sala de prensa</a>.</p></section>',
         '<p><a href="%sagenda/">Volver a la agenda</a></p></aside></div></div><!--kg-card-end: html-->' % BASE]
    return {"title": "Subir mi evento a la agenda", "slug": c["ghost"]["slug_subir"], "html": "\n".join(h),
            "custom_excerpt": "Publica gratis tu feria, congreso o jornada de transportes, movilidad o turismo en la agenda de MOTICIAS.",
            "meta_title": "Subir mi evento a la agenda de MOTICIAS", "meta_description": "Formulario para organizadores: la redacción lo comprueba y lo publica gratis en la agenda de transportes, movilidad y turismo."}


PERMISOS = {
    "tratamiento": "Acepto que Avionline S.L. (MOTICIAS) trate estos datos para revisar y publicar el evento y para escribirme sobre él.",
    "boletin": "Quiero recibir el boletín de MOTICIAS.",
    "comercial": "Acepto que MOTICIAS me contacte para proponerme difusión o patrocinio de este u otros eventos.",
}


# ---------- calendario ----------
def _ics_txt(s):
    return str(s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _plegar(linea):
    b = linea.encode("utf-8")
    if len(b) <= 75:
        return linea
    out, cur = [], ""
    for ch in linea:
        if len((cur + ch).encode("utf-8")) > (75 if not out else 74):
            out.append(cur); cur = ch
        else:
            cur += ch
    out.append(cur)
    return "\r\n ".join(out)


def ics(evs, v, dia=None, rutas_ok=False):
    dia = dia or EV.hoy()
    sello = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ls = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MOTICIAS//Agenda de transportes, movilidad y turismo//ES", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
          "X-WR-CALNAME:MOTICIAS · Agenda", "X-WR-TIMEZONE:Europe/Madrid", "REFRESH-INTERVAL;VALUE=DURATION:P1D"]
    vis = set(EV.cfg(v)["estados_visibles"])
    for e in sorted([e for e in evs if e.get("estado") in vis and e.get("inicio") and EV.fin_de(e) >= dia], key=lambda e: e["inicio"]):
        fin = (datetime.date.fromisoformat(EV.fin_de(e)) + datetime.timedelta(days=1)).strftime("%Y%m%d")
        ls += ["BEGIN:VEVENT", "UID:%s@moticias.com" % e["id"], "DTSTAMP:" + sello, "DTSTART;VALUE=DATE:" + e["inicio"].replace("-", ""), "DTEND;VALUE=DATE:" + fin,
               "SUMMARY:" + _ics_txt(e["titulo"] + (" (CANCELADO)" if e["estado"] == "cancelado" else "")),
               "LOCATION:" + _ics_txt(", ".join(x for x in (e.get("sede"), e["ciudad"]) if x)),
               "DESCRIPTION:" + _ics_txt("%s\nOrganiza: %s\n%s" % (e["resumen"], y_lista(e["organizadores"]), url_ficha(e, rutas_ok))),
               "URL:" + url_ficha(e, rutas_ok), "STATUS:" + ("CANCELLED" if e["estado"] == "cancelado" else "CONFIRMED"), "END:VEVENT"]
    ls.append("END:VCALENDAR")
    return "\r\n".join(_plegar(x) for x in ls) + "\r\n"


# ---------- Ghost ----------
def rutas_activas(base_url, admin_key):
    """¿Tiene Ghost ya las rutas de la agenda? (lectura permitida con la clave de integración; subirlas, no)."""
    import ghost_publish as G
    import urllib.request
    try:
        r = urllib.request.urlopen(urllib.request.Request(G.admin_base(base_url.rstrip("/")) + "/ghost/api/admin/settings/routes/yaml/",
                                                          headers={"Authorization": "Ghost " + G.ghost_token(admin_key), "Accept-Version": "v5.0"}), timeout=30)
        return "/agenda/{slug}/" in r.read().decode("utf-8", "replace")
    except Exception:
        return False


def _upsert(tipo, obj, base_url, admin_key):
    import ghost_publish as G
    tok, b = G.ghost_token(admin_key), G.admin_base(base_url.rstrip("/"))
    st, f = G.api("GET", "%s/ghost/api/admin/%s/slug/%s/?fields=id,updated_at" % (b, tipo, obj["slug"]), tok)
    p = {k: x for k, x in obj.items() if not k.startswith("_")}
    p["status"] = "published"
    if st == 200 and f.get(tipo):
        p["updated_at"] = f[tipo][0]["updated_at"]
        return G.api("PUT", "%s/ghost/api/admin/%s/%s/?source=html" % (b, tipo, f[tipo][0]["id"]), tok, {tipo: [p]})
    return G.api("POST", "%s/ghost/api/admin/%s/?source=html" % (b, tipo), tok, {tipo: [p]})


def _retirar_ficha(slug, base_url, admin_key):
    """Una ficha retirada vuelve a borrador en Ghost (nunca se borra)."""
    import ghost_publish as G
    tok, b = G.ghost_token(admin_key), G.admin_base(base_url.rstrip("/"))
    st, f = G.api("GET", "%s/ghost/api/admin/posts/slug/%s/?fields=id,updated_at,status" % (b, slug), tok)
    if st == 200 and f.get("posts") and f["posts"][0]["status"] == "published":
        return G.api("PUT", "%s/ghost/api/admin/posts/%s/" % (b, f["posts"][0]["id"]), tok, {"posts": [{"status": "draft", "updated_at": f["posts"][0]["updated_at"]}]})
    return st, f


def publicar(evs, v, base_url, admin_key, dia=None):
    rutas_ok = rutas_activas(base_url, admin_key)
    res = {"rutas": rutas_ok, "paginas": {}, "fichas": {}}
    for pg in (construir(evs, v, dia, rutas_ok), subir(v, rutas_ok)):
        st, _ = _upsert("pages", pg, base_url, admin_key)
        res["paginas"][pg["slug"]] = st
    if rutas_ok:
        con_ficha = {"publicado", "aplazado", "cancelado", "pasado"}
        for e in evs:
            if e.get("estado") in con_ficha and e.get("inicio"):
                st, _ = _upsert("posts", ficha(e, v, True), base_url, admin_key)
                res["fichas"][e["id"]] = st
            elif e.get("estado") == "retirado":
                st, _ = _retirar_ficha(e["id"], base_url, admin_key)
                res["fichas"][e["id"]] = "retirada %s" % st
    return res


# Estilos de la agenda, dentro de la tarjeta HTML (Ghost sirve el tema sin versionar; nada fuera de .m-agenda)
ESTILO = """<style>
.m-agenda{--ma-fondo:#0B1F3A;--ma-tinta:#14213d;--ma-suave:#5b6474;--ma-linea:#dfe3ea;--ma-acento:#0B5FFF;font-size:1rem}
.m-agenda .respuesta-directa{font-size:1.05rem;line-height:1.55}
.m-agenda .ma-rejilla{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:32px;align-items:start}
.m-agenda .ma-mapa{background:var(--ma-fondo);color:#fff;border-radius:10px;padding:14px}
.m-agenda .ma-meses,.m-agenda .ma-leyenda{display:flex;flex-wrap:wrap;gap:6px}
.m-agenda button{font:inherit;cursor:pointer}
.m-agenda .ma-mes,.m-agenda .ma-tema-b,.m-agenda .ma-lugar,.m-agenda .ma-quitar,.m-agenda .ma-orden button{min-height:44px;min-width:44px;padding:8px 12px;border-radius:22px;border:1px solid rgba(255,255,255,.35);background:transparent;color:inherit;font-size:.9rem}
.m-agenda .ma-orden button,.m-agenda .ma-vacio .ma-quitar{border-color:var(--ma-linea);color:var(--ma-tinta)}
.m-agenda button[aria-pressed=true]{background:#fff;color:var(--ma-fondo);font-weight:600}
.m-agenda .ma-orden button[aria-pressed=true]{background:var(--ma-tinta);color:#fff}
.m-agenda button:focus-visible,.m-agenda .ma-pin:focus-visible{outline:3px solid #FFE14D;outline-offset:2px}
.m-agenda button[disabled]{opacity:.45;cursor:default}
.m-agenda .ma-tema-b i,.m-agenda .ma-tema i{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:6px;vertical-align:-1px;border:1px solid rgba(0,0,0,.25)}
.m-agenda .ma-mapa-cuerpo{display:grid;grid-template-columns:minmax(0,1fr) 220px;gap:12px;margin:10px 0}
.m-agenda .ma-svg{width:100%;height:auto;display:block}
.m-agenda .ma-ccaa{fill:none;stroke:#3a5f92;stroke-width:.9}
.m-agenda .ma-borde{fill:#17345c;stroke:#7d9cc7;stroke-width:1.3}
.m-agenda .ma-canarias{fill:none;stroke:#6f8db8;stroke-dasharray:4 3}
.m-agenda .ma-pin{cursor:pointer}
.m-agenda .ma-pin-toque{fill:transparent;pointer-events:all}
.m-agenda .ma-borde,.m-agenda .ma-ccaa,.m-agenda .ma-canarias{pointer-events:none}
.m-agenda .ma-pin-marca{stroke:#0B1F3A;stroke-width:2}
.m-agenda .ma-pin-aro{fill:none;stroke:#fff;stroke-width:1.6;stroke-dasharray:3 2.5}
.m-agenda .ma-pin-n{font:700 13px system-ui,sans-serif;fill:#0B1F3A;pointer-events:none}
.m-agenda .ma-pin-nombre{font:600 17px system-ui,sans-serif;fill:#fff;paint-order:stroke;stroke:#0B1F3A;stroke-width:4px}
.m-agenda .ma-pin.ma-activo .ma-pin-marca{stroke:#FFE14D;stroke-width:3}
.m-agenda .ma-pin[hidden]{display:none}
.m-agenda .ma-lugares h3{color:#fff;font-size:.95rem;margin:0 0 6px}
.m-agenda .ma-lugares ul{list-style:none;margin:0;padding:0;max-height:420px;overflow:auto}
.m-agenda .ma-lugares li{margin:0 0 8px}
.m-agenda .ma-lugar{width:100%;text-align:left;display:flex;justify-content:space-between;border-radius:8px}
.m-agenda .ma-lugar-titulos{display:block;font-size:.8rem;opacity:.8;margin:2px 4px 0}
.m-agenda .ma-filtros{margin:10px 0 0}
.m-agenda .ma-orden{margin:18px 0 8px;display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.m-agenda .ma-lista{list-style:none;margin:0;padding:0}
.m-agenda .ma-cita{border-top:1px solid var(--ma-linea);padding:16px 0}
.m-agenda .ma-cita[hidden]{display:none}
.m-agenda .ma-cita h3{margin:4px 0 6px;font-size:1.15rem}
.m-agenda .ma-cita p{margin:4px 0}
.m-agenda .ma-accion{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center}
.m-agenda .ma-cita-cab,.m-agenda .ma-org,.m-agenda .ma-nota,.m-agenda .ma-precio{font-size:.88rem;color:var(--ma-suave)}
.m-agenda .ma-estado{color:#b42318;font-weight:700}
.m-agenda .ma-publico{font-weight:600}
.m-agenda .ma-boton{display:inline-block;min-height:44px;line-height:28px;padding:8px 16px;border-radius:6px;background:var(--ma-acento);color:#fff!important;text-decoration:none;font-weight:600}
.m-agenda .ma-boton-2{background:var(--ma-tinta)}
.m-agenda .ma-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.m-agenda .ma-lateral section{border:1px solid var(--ma-linea);border-radius:10px;padding:14px;margin:0 0 16px}
.m-agenda .ma-lateral h2{font-size:1.05rem;margin:0 0 8px}
.m-agenda .ma-lateral ul,.m-agenda .ma-lateral ol{padding-left:18px;margin:0}
.m-agenda .ma-lateral li{margin:0 0 8px;font-size:.92rem}
.m-agenda .ma-sin,.m-agenda .ma-pie{font-size:.88rem;color:var(--ma-suave)}
.m-agenda .ma-vacio{padding:12px;border:1px dashed var(--ma-linea);border-radius:8px}
.m-agenda .ma-datos{display:grid;grid-template-columns:max-content 1fr;gap:6px 16px}
.m-agenda .ma-datos dt{font-weight:600}
.m-agenda .ma-datos dd{margin:0}
.m-agenda .ma-form fieldset{border:1px solid var(--ma-linea);border-radius:10px;padding:14px;margin:0 0 16px}
.m-agenda .ma-form legend{font-weight:700;padding:0 6px}
.m-agenda .ma-campo label{display:block;font-weight:600;margin:0 0 4px}
.m-agenda .ma-campo input,.m-agenda .ma-campo select,.m-agenda .ma-campo textarea{width:100%;min-height:44px;padding:8px;border:1px solid #b9c0cc;border-radius:6px;font:inherit;box-sizing:border-box}
.m-agenda .ma-campo small{display:block;color:var(--ma-suave)}
.m-agenda .ma-check{display:flex;gap:8px;align-items:flex-start}
.m-agenda .ma-check input{width:22px;height:22px;flex:none;margin-top:2px}
.m-agenda .ma-trampa{position:absolute;left:-9999px}
@media (max-width:860px){.m-agenda .ma-rejilla{grid-template-columns:1fr}.m-agenda .ma-mapa-cuerpo{grid-template-columns:1fr}.m-agenda .ma-lugares ul{max-height:none}}
</style>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ficha")
    ap.add_argument("--subir", action="store_true")
    ap.add_argument("--ics")
    ap.add_argument("--hoy")
    ap.add_argument("--rutas", action="store_true", help="genera como si Ghost ya tuviera las rutas de la agenda")
    ap.add_argument("--publicar", action="store_true")
    a = ap.parse_args()
    v = EV.vertical()
    evs = [EV.limpio(e) for e in EV.cargar()]
    if a.ics:
        os.makedirs(os.path.dirname(os.path.abspath(a.ics)), exist_ok=True)
        open(a.ics, "w", encoding="utf-8", newline="").write(ics(evs, v, a.hoy, a.rutas))
        print("calendario: %s" % a.ics)
    if a.ficha:
        print(ficha(next(e for e in evs if e["id"] == a.ficha), v, True)["html"])
    if a.subir:
        print(subir(v, a.rutas)["html"])
    if a.html or a.json:
        pg = construir(evs, v, a.hoy, a.rutas)
        print(json.dumps(pg["_resumen"], ensure_ascii=False, indent=1) if a.json else pg["html"])
    if a.publicar:
        url, key = os.environ.get("GHOST_URL"), os.environ.get("GHOST_ADMIN_KEY")
        if not url or not key:
            print("faltan GHOST_URL y GHOST_ADMIN_KEY", file=sys.stderr)
            return 2
        r = publicar(evs, v, url, key, a.hoy)
        print(json.dumps(r, ensure_ascii=False))
        return 0 if all(s in (200, 201) for s in r["paginas"].values()) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
