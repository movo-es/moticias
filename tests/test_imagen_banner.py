"""Pruebas sin red del color de las bandas de la imagen de un banner (cambio OpenSpec `imagenes-de-banner`, 22-11-2026).

  python3 -I tests/test_imagen_banner.py
"""
import json, os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "api"))
import gestor as GS  # noqa: E402

PUB = json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))["publicidad"]


class ColorDeBandas(unittest.TestCase):
    def test_el_campo_se_puede_guardar(self):
        self.assertIn("imagen_fondo", GS.CAMPOS_ANUNCIO)

    def test_llega_al_sitio_solo_si_es_un_color(self):
        a = {"modo": "imagen", "image": "https://x/a.jpg", "formato": "2x4", "alt": "x"}
        self.assertEqual(GS.banner_publico(dict(a, imagen_fondo="#0B2545"), PUB)["imagen_fondo"], "#0B2545")
        for malo in (None, "", "rojo", "#fff", "#12345g", "#0b2545;background:url(x)", "expression(1)"):
            self.assertIsNone(GS.banner_publico(dict(a, imagen_fondo=malo), PUB)["imagen_fondo"], malo)

    def test_el_gestor_rechaza_un_color_que_no_lo_es(self):
        ses = {"permisos": ["publicidad"], "nombre": "Prueba", "perfil": "superadmin"}
        st, r = GS.accion_anuncio(ses, {"accion": "crear", "cambios": {"name": "x", "headline": "y", "imagen_fondo": "url(javascript:1)"}})
        self.assertEqual(st, 400)
        self.assertIn("bandas", r["error"])

    def test_formatos_con_medidas(self):
        r = PUB["rejilla"]
        col = (r["ancho"] - (r["columnas"] - 1) * r["separacion"]) / r["columnas"]
        for f in PUB["formatos"]:
            c, n = map(int, f.split("x"))
            self.assertGreater(round(c * col + (c - 1) * r["separacion"]), 0)
            self.assertGreater(n * r["fila"] + (n - 1) * r["separacion"], 0)


if __name__ == "__main__":
    unittest.main()
