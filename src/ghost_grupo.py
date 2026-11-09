"""MOTICIAS · Página «Empresas del grupo» (www.moticias.com/empresas-del-grupo/).

Decisión de Rainer (9-11-2026): que buscadores y modelos de lenguaje asocien cada marca del grupo a su campo —MOVO a los
planes de movilidad sostenible al trabajo y la consultoría de movilidad, Movenbus a las soluciones tecnológicas y
comerciales del autobús por carretera, MUFMI al transporte a la demanda, Avionline a la innovación y el turismo, BUQ al
turismo—. Se hace con transparencia: una página que dice quién edita MOTICIAS, qué hace cada empresa y en qué piezas
aparece su caja «Contenido patrocinado»; respuesta directa al principio, datos estructurados y enlaces internos.
Sale de `verticals/movilidad.json → grupo` y de las menciones publicadas en `data/articles/`.

  python3 -I src/ghost_grupo.py --html            imprime el HTML (para revisarlo)
  python3 -I src/ghost_grupo.py --publicar        crea o actualiza la página en Ghost (GHOST_URL, GHOST_ADMIN_KEY)
"""
import argparse, glob, html, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import ghost_publish as G  # noqa: E402

SLUG = "empresas-del-grupo"
E = lambda s: html.escape(str(s or ""), quote=True)  # noqa: E731


def piezas_por_marca(vertical):
    marcas = {m["id"]: m for m in (vertical.get("grupo") or {}).get("marcas") or []}
    prod_marca = {p: m["id"] for m in marcas.values() for p in m.get("productos") or []}
    out = {k: [] for k in marcas}
    for f in glob.glob(os.path.join(ROOT, "data", "articles", "*.json")):
        a = json.load(open(f, encoding="utf-8"))
        if a.get("status") in ("pendiente", "borrador", "retirada"):
            continue
        for m in a.get("menciones") or []:
            k = prod_marca.get(m.get("producto"))
            if m.get("estado") == "publicada" and k and a["id"] not in [x["id"] for x in out[k]]:
                out[k].append({"id": a["id"], "title": a.get("title"), "date": a.get("date")})
    for v in out.values():
        v.sort(key=lambda x: x["date"] or "", reverse=True)
    return out


def construir(vertical):
    g = vertical.get("grupo") or {}
    ed = g.get("editor") or {}
    base = "https://www.moticias.com/"
    marcas = [m for m in g.get("marcas") or [] if m.get("publica", True)]
    pzs = piezas_por_marca(vertical)
    lista = ", ".join("%s (%s)" % (m["nombre"], m["especialidad"]) for m in marcas)
    partes = ['<p class="respuesta-directa"><strong>MOTICIAS es un medio profesional de movilidad y transportes editado por %s '
              'El grupo editor reúne empresas especializadas: %s. Cuando una noticia trata un problema que una de ellas resuelve, '
              'la pieza lo dice en una caja «Contenido patrocinado», separada del texto y señalizada.</strong></p>' % (E(ed.get("nombre")) + ("" if str(ed.get("nombre") or "").endswith(".") else "."), E(lista))]
    partes.append("<h2>Quién edita MOTICIAS</h2><p><strong>%s</strong> — %s <a href=\"%s\">%s</a></p>" % (
        E(ed.get("nombre")), E(ed.get("descripcion")), E(ed.get("url")), E((ed.get("url") or "").replace("https://", ""))))
    for m in marcas:
        partes.append('<h2 id="%s">%s: %s</h2><p>%s <a href="%s">%s</a></p>' % (E(m["id"]), E(m["nombre"]), E(m["especialidad"]), E(m.get("descripcion")),
                                                                                 E(m["url"]), E(m["url"].replace("https://", ""))))
        if pzs.get(m["id"]):
            partes.append("<p>Piezas de MOTICIAS donde aparece su caja «Contenido patrocinado»:</p><ul>%s</ul>" % "".join(
                '<li><a href="%s%s/">%s</a> (%s)</li>' % (base, E(p["id"]), E(p["title"]), E(p["date"])) for p in pzs[m["id"]][:12]))
    partes.append("<h2>Cómo separamos información y promoción</h2><p>La caja de una empresa del grupo nunca cambia el texto, la firma ni la "
                  "aprobación de la pieza; va señalizada como «Contenido patrocinado», con una línea que declara la relación y enlace marcado como "
                  "patrocinado. Los análisis no llevan cajas, y MOTICIAS no informa de operaciones propias de las empresas del grupo. "
                  'Más en <a href="%scomo-trabajamos/">Cómo trabajamos</a>.</p>' % base)
    org = G.organizacion(vertical)
    ld = {"@context": "https://schema.org", "@type": "AboutPage", "name": "Empresas del grupo editor de MOTICIAS", "url": base + SLUG + "/",
          "about": org, "inLanguage": "es-ES"}
    return {"title": "Empresas del grupo editor de MOTICIAS", "slug": SLUG, "html": "\n".join(partes),
            "custom_excerpt": "Quién edita MOTICIAS y qué hace cada empresa del grupo: %s." % lista[:240],
            "meta_title": "Empresas del grupo editor de MOTICIAS: %s" % ", ".join(m["nombre"] for m in marcas),
            "meta_description": ("MOTICIAS, medio de movilidad y transportes editado por %s. Grupo: %s." % (ed.get("nombre"), lista))[:300],
            "codeinjection_head": '<script type="application/ld+json">%s</script>' % json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")}


def publicar(pagina, base_url, admin_key):
    tok = G.ghost_token(admin_key)
    b = G.admin_base(base_url)
    st, f = G.api("GET", "%s/ghost/api/admin/pages/slug/%s/?fields=id,updated_at" % (b, SLUG), tok)
    p = dict(pagina, status="published")
    if st == 200 and f.get("pages"):
        p["updated_at"] = f["pages"][0]["updated_at"]
        return G.api("PUT", "%s/ghost/api/admin/pages/%s/?source=html" % (b, f["pages"][0]["id"]), tok, {"pages": [p]})
    return G.api("POST", "%s/ghost/api/admin/pages/?source=html" % b, tok, {"pages": [p]})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--publicar", action="store_true")
    a = ap.parse_args()
    v = json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))
    pg = construir(v)
    if a.json:
        print(json.dumps(pg, ensure_ascii=False))
    elif a.html or not a.publicar:
        print(pg["html"])
    if a.publicar:
        url, key = os.environ.get("GHOST_URL"), os.environ.get("GHOST_ADMIN_KEY")
        if not url or not key:
            print("faltan GHOST_URL y GHOST_ADMIN_KEY", file=sys.stderr)
            return 2
        st, r = publicar(pg, url, key)
        print("Ghost %s" % st)
        return 0 if st in (200, 201) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
