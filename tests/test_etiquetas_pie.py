"""Etiquetas clicables al pie de cada noticia (decisión de Rainer, 20-11-2026). Sin red: python3 -I tests/test_etiquetas_pie.py"""
import glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import ghost_publish as G  # noqa: E402

V = json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))


def test_slug():
    assert G.slug_etiqueta("Marina Mercante") == "marina-mercante"
    assert G.slug_etiqueta("Ley 9/2025") == "ley-9-2025"
    assert G.slug_etiqueta("contaminación marina") == "contaminacion-marina"
    assert G.slug_etiqueta("Orden TRM/1232/2026") == "orden-trm-1232-2026"


def test_pie_sin_internas_y_libres_primero():
    tags = [{"name": "#regulacion"}, {"name": "Puertos", "slug": "m-puertos"}, {"name": "Marina Mercante"}, {"name": "OSPAR"},
            {"name": "#tipo-noticia"}, {"name": "España (Estado)", "slug": "t-estado"}]
    pie = G.etiquetas_pie(tags, {"ospar": "ospar-2"})
    assert pie == [("Marina Mercante", "marina-mercante"), ("OSPAR", "ospar-2"), ("Puertos", "m-puertos"), ("España (Estado)", "t-estado")], pie
    h = G.etiquetas_pie_html(pie)
    assert 'href="/tag/ospar-2/"' in h and "#tipo" not in h and 'data-fmt="%s"' % G.FORMATO in h and h.startswith("<!--kg-card-begin: html-->")


def test_todas_las_piezas_llevan_el_bloque():
    n = 0
    for f in glob.glob(os.path.join(ROOT, "data", "articles", "*.json")):
        a = json.load(open(f, encoding="utf-8"))
        h = G.build_html(a, V)
        assert 'class="m-etiquetas"' in h and 'data-fmt="%s"' % G.FORMATO in h, a["id"]
        assert h.index('class="m-etiquetas"') > h.index("<h2>Para saber más</h2>") if a.get("sources") else True, a["id"]
        assert h.count('rel="tag"') >= 1, a["id"]
        n += 1
    assert n > 50


def test_alinear_ejes_sin_red():
    """21-11-2026: con el nombre nuevo y el slug ocupado, Ghost creaba una etiqueta por pieza (t-ue-2, t-ue-3…)."""
    tags = {"t-ue": {"id": "1", "name": "Unión Europea", "n": 3}, "t-ue-2": {"id": "2", "name": "Europa", "n": 0}, "t-ue-3": {"id": "3", "name": "Europa", "n": 1},
            "m-puertos": {"id": "5", "name": "Puertos", "n": 9}, "puertos": {"id": "6", "name": "Puertos", "n": 2}, "ley-9-2025": {"id": "8", "name": "Ley 9/2025", "n": 0}}

    def api(method, url, token, body=None):
        if method == "GET" and "/tags/?" in url:
            return 200, {"tags": [{"id": v["id"], "name": v["name"], "slug": k, "count": {"posts": v["n"]}} for k, v in tags.items()], "meta": {"pagination": {"next": None}}}
        sl = url.rstrip("/").split("/")[-1]
        if method == "GET":
            return (200, {"tags": [dict(tags[sl], slug=sl, updated_at="u")]}) if sl in tags else (404, {})
        sl = [k for k, v in tags.items() if v["id"] == sl][0]
        if method == "DELETE":
            del tags[sl]
            return 204, {}
        tags[sl]["name"] = body["tags"][0]["name"]
        return 200, {}

    ejes = [{"name": "Europa", "slug": "t-ue"}, {"name": "Puertos", "slug": "m-puertos"}]
    original = G.api
    G.api, G._SLUGS, G._NOMBRES = api, {}, {}
    try:
        r = G.alinear_ejes(ejes + [{"name": "OSPAR"}], "https://x", "t")
        borradas = G.limpiar_duplicadas(ejes + [{"name": "Ley 9", "slug": "ley-9"}], "https://x", "t")
    finally:
        G.api, G._SLUGS, G._NOMBRES = original, {}, {}
    assert tags["t-ue"]["name"] == "Europa" and r["europa"] == "t-ue" and r["puertos"] == "m-puertos"
    assert borradas == 1 and "t-ue-2" not in tags and "t-ue-3" in tags and "puertos" in tags and "ley-9-2025" in tags


if __name__ == "__main__":
    for nombre, f in sorted(globals().items()):
        if nombre.startswith("test_"):
            f()
            print("ok", nombre)
