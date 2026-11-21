"""Pruebas sin red de la entradilla y de la lista de fotos en Ghost (cambio OpenSpec `extracto-y-fotos`, 22-11-2026).

  python3 -I tests/test_extracto_y_fotos.py
"""
import glob, json, os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "api"))
import ghost_publish as G  # noqa: E402
import gestor as GS  # noqa: E402


class Extracto(unittest.TestCase):
    def test_lo_que_cabe_no_se_toca(self):
        self.assertEqual(G.extracto("Una frase corta."), "Una frase corta.")
        self.assertEqual(G.extracto(None), "")

    def test_corta_al_final_de_una_frase(self):
        a = json.load(open(os.path.join(ROOT, "data", "articles", "el-poligono-no-tiene-plan-v7kd.json"), encoding="utf-8"))
        e = G.extracto(a["summary"])
        self.assertLessEqual(len(e), 300)
        self.assertTrue(e.endswith("con las obligadas."), e)
        self.assertTrue(a["summary"].startswith(e))

    def test_no_corta_en_abreviaturas_ni_en_cifras(self):
        t = ("El art. 26 de la Ley 9/2025 obliga a los centros de más de 200 personas y prevé 1.500 planes, según Avionline S.L. y otras fuentes "
             "del sector consultadas esta semana por la redacción. " + "Segunda frase que ya no cabe porque alarga el resumen mucho más de la cuenta. " * 3)
        e = G.extracto(t)
        self.assertLessEqual(len(e), 300)
        self.assertTrue(e.endswith("más de la cuenta."), e)      # frases enteras: ni «art.» ni «S.L.» ni «1.500» son un final
        self.assertEqual(e.count("Segunda frase"), 1)
        self.assertTrue(G.extracto(t[:140] + " y sigue sin punto " * 12).endswith("…"))

    def test_sin_frase_que_quepa_corta_en_palabra_entera(self):
        e = G.extracto("palabra " * 80)
        self.assertLessEqual(len(e), 300)
        self.assertTrue(e.endswith("palabra…"), e[-20:])

    def test_ninguna_pieza_publica_una_entradilla_a_medias(self):
        for f in glob.glob(os.path.join(ROOT, "data", "articles", "*.json")):
            s = json.load(open(f, encoding="utf-8")).get("summary") or ""
            e = G.extracto(s)
            self.assertLessEqual(len(e), 300, f)
            if len(" ".join(s.split())) > 300:
                self.assertRegex(e, r"[.!?…»]$", f)


class Fotos(unittest.TestCase):
    def setUp(self):
        self.viejo = (G.URLS_FOTOS, G._del_repositorio, G._FOTOS_REPO, dict(G.FOTOS_NUEVAS), GS.leer, GS.escribir)
        G.FOTOS_NUEVAS.clear()

    def tearDown(self):
        G.URLS_FOTOS, G._del_repositorio, G._FOTOS_REPO, nuevas, GS.leer, GS.escribir = self.viejo
        G.FOTOS_NUEVAS.clear(); G.FOTOS_NUEVAS.update(nuevas)

    def test_sin_fichero_en_el_despliegue_se_lee_del_repositorio_una_vez(self):
        G.URLS_FOTOS, G._FOTOS_REPO, pedidos = "/no/existe/ghost-urls.json", None, []
        G._del_repositorio = lambda ruta: (pedidos.append(ruta) or json.dumps({"a.jpg": "https://ghost/a.jpg"}).encode())
        self.assertEqual(G.urls_fotos()["a.jpg"], "https://ghost/a.jpg")
        G.urls_fotos()
        self.assertEqual(pedidos, ["portal/img/ghost-urls.json"])

    def test_una_foto_anotada_no_se_vuelve_a_subir(self):
        G.URLS_FOTOS, G._FOTOS_REPO = "/no/existe/ghost-urls.json", {"a.jpg": "https://ghost/a.jpg"}
        subidas = []
        viejo = G.subir_imagen
        G.subir_imagen = lambda *a, **k: subidas.append(a) or "https://ghost/otra.jpg"
        try:
            self.assertEqual(G.imagen_ghost({"image": {"src": "img/a.jpg"}}, "https://x", "token"), "https://ghost/a.jpg")
        finally:
            G.subir_imagen = viejo
        self.assertFalse(subidas)

    def test_las_fotos_nuevas_se_anotan_en_el_repositorio(self):
        os.environ["GITHUB_TOKEN"] = "prueba"
        G._FOTOS_REPO = {}
        G.FOTOS_NUEVAS["nueva.jpg"] = "https://ghost/nueva.jpg"
        escritos = []
        GS.leer = lambda ruta, repo=None: ({"a.jpg": "https://ghost/a.jpg"}, "sha1")
        GS.escribir = lambda ruta, obj, sha, mensaje, repo=None: (escritos.append((ruta, obj, sha)) or True, "abc1234")
        self.assertTrue(GS._anotar_fotos())
        self.assertEqual(escritos[0][0], "portal/img/ghost-urls.json")
        self.assertEqual(escritos[0][1], {"a.jpg": "https://ghost/a.jpg", "nueva.jpg": "https://ghost/nueva.jpg"})
        self.assertFalse(G.FOTOS_NUEVAS)
        self.assertFalse(GS._anotar_fotos())   # nada nuevo: no escribe otra vez
        self.assertEqual(len(escritos), 1)

    def test_todas_las_fotos_publicadas_tienen_su_url(self):
        urls = json.load(open(os.path.join(ROOT, "portal", "img", "ghost-urls.json"), encoding="utf-8"))
        for pid in ("el-poligono-no-tiene-plan-v7kd", "anetra-pide-a-la-nueva-presidenta-de-renfe-que-desista-k4nt"):
            a = json.load(open(os.path.join(ROOT, "data", "articles", pid + ".json"), encoding="utf-8"))
            self.assertIn(a["image"]["src"][4:], urls, pid)


if __name__ == "__main__":
    unittest.main(verbosity=1)
