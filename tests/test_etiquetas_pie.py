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


if __name__ == "__main__":
    for nombre, f in sorted(globals().items()):
        if nombre.startswith("test_"):
            f()
            print("ok", nombre)
