"""Pruebas sin red de la entradilla y del botón «Compartir en LinkedIn» (cambio OpenSpec `entradilla-y-linkedin`).

  python3 -I tests/test_entradilla.py
"""
import copy, glob, json, os, sys, unittest, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "api"))
import entradilla as EN  # noqa: E402
import compartir as CP  # noqa: E402
import redaccion as R  # noqa: E402
import ghost_publish as G  # noqa: E402
import gestor as GS  # noqa: E402

V = json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))
PIEZAS = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(ROOT, "data", "articles", "*.json")))]
LARGO = ("El Consejo de Ministros aprobó el 10 de noviembre el real decreto que crea el Defensor o Defensora de Víctimas de Accidentes "
         "de Transporte Colectivo, con rango de subsecretario y adscrito al Ministerio de Transportes. Su ámbito es el transporte "
         "colectivo de viajeros de competencia estatal —ferrocarril, aviación comercial, pasaje marítimo y autobús— y puede extenderse "
         "a servicios autonómicos y locales mediante acuerdos. Tendrá una oficina con rango de dirección general.")


class Frases(unittest.TestCase):
    def test_no_rompe_abreviaturas_iniciales_ni_cifras(self):
        self.assertEqual(EN.frases("El Gobierno aprobó el art. 25 de la Ley 9/2025. Entra en vigor el 1 de enero."),
                         ["El Gobierno aprobó el art. 25 de la Ley 9/2025.", "Entra en vigor el 1 de enero."])
        self.assertEqual(EN.frases("Renfe S.A. Operadora licitó 1.500 trenes. G. Jordan lo firma."),
                         ["Renfe S.A. Operadora licitó 1.500 trenes.", "G. Jordan lo firma."])
        self.assertEqual(EN.frases("La consigna CR-V n.º 32/2026 quedó sin efecto. Renfe lo confirmó."),
                         ["La consigna CR-V n.º 32/2026 quedó sin efecto.", "Renfe lo confirmó."])

    def test_el_caso_de_la_captura_ya_no_se_corta(self):
        """El resumen acababa en «—ferrocarr»: 300 caracteres justos del summary (captura de Rainer, 17-11-2026)."""
        self.assertTrue(LARGO[:300].endswith("ferrocarr"))
        e = EN.recortar(LARGO, 300)
        self.assertTrue(e.endswith("Ministerio de Transportes."))
        self.assertLessEqual(len(e), 300)

    def test_recortar_nunca_deja_media_palabra(self):
        una = "palabra " * 60 + "final"  # una sola frase que no cabe
        r = EN.recortar(una, 100)
        self.assertLessEqual(len(r), 100)
        self.assertTrue(r.endswith("palabra…"))
        self.assertEqual(EN.recortar("Cabe entera.", 300), "Cabe entera.")
        self.assertIsNone(EN.proponer(una, 100))


class Regla(unittest.TestCase):
    def test_problemas(self):
        cfg = EN.config(V)
        self.assertEqual(cfg["max"], 280)
        buena = "El Consejo de Ministros aprobó el 10 de noviembre el real decreto que crea el Defensor de las víctimas."
        self.assertEqual(EN.problemas(buena, cfg), [])
        self.assertTrue(EN.problemas("", cfg))
        self.assertTrue(EN.problemas(LARGO, cfg))                               # no cabe
        self.assertTrue(EN.problemas(buena[:-1] + "…", cfg))                     # puntos suspensivos
        self.assertTrue(EN.problemas(buena[:-1], cfg))                           # sin punto final
        self.assertTrue(EN.problemas(buena + "\nOtra línea más que no debería estar aquí.", cfg))

    def test_todas_las_piezas_tienen_entradilla_que_cabe(self):
        cfg = EN.config(V)
        mal = {a["id"]: EN.validar_pieza(a, cfg) for a in PIEZAS if EN.validar_pieza(a, cfg)}
        self.assertEqual(mal, {})

    def test_la_entradilla_no_anade_cifras_que_no_esten_en_la_pieza(self):
        for a in PIEZAS:
            self.assertFalse(R.cifras(a["entradilla"]) - R.cifras(R.corpus(dict(a, entradilla=""))), a["id"])

    def test_lo_que_va_a_ghost_cabe_y_acaba_en_frase(self):
        for a in PIEZAS:
            post = G.build_post(a, V, "https://www.moticias.com")
            self.assertLessEqual(len(post["custom_excerpt"]), EN.LIMITE_GHOST, a["id"])
            self.assertTrue(EN.acaba_bien(post["custom_excerpt"]), a["id"])
            self.assertEqual(post["custom_excerpt"], a["entradilla"])
            self.assertLessEqual(len(post["meta_description"]), 500)

    def test_pieza_antigua_sin_entradilla_tampoco_se_corta(self):
        a = dict(PIEZAS[0], summary=LARGO)
        a.pop("entradilla")
        self.assertTrue(EN.de(a).endswith("Ministerio de Transportes."))


class Editor(unittest.TestCase):
    def test_el_editor_no_admite_una_entradilla_que_no_cabe(self):
        a = copy.deepcopy(PIEZAS[0])
        with self.assertRaises(ValueError):
            R.aplicar_edicion(a, {"entradilla": LARGO}, "prueba")
        with self.assertRaises(ValueError):
            R.aplicar_edicion(a, {"entradilla": ""}, "prueba")
        nueva = EN.frases(a["summary"])[0] if len(EN.frases(a["summary"])[0]) <= 280 and EN.frases(a["summary"])[0] != a["entradilla"] else "Una frase completa y distinta que cabe de sobra en la tarjeta de la pieza."
        self.assertIn("entradilla", R.aplicar_edicion(a, {"entradilla": nueva}, "prueba"))
        self.assertEqual(a["entradilla"], nueva)
        self.assertIn("entradilla", R.CAMPOS)

    def test_columna_escrita_en_el_gestor_nace_con_entradilla(self):
        texto = ("El polígono no tiene plan y la ley sí tiene fecha. " + "palabra " * 140 + "\n\n## Lo que toca\n\nCierre.")
        a = GS.voz_nueva_pieza({"title": "El polígono no tiene plan", "subtitle": "Sub", "body_md": texto}, "prueba", V)
        self.assertLessEqual(len(a["entradilla"]), 280)
        self.assertFalse(a["entradilla"].endswith("palabr"))


class LinkedIn(unittest.TestCase):
    def setUp(self):
        self.a = next(a for a in PIEZAS if a.get("status") == "publicado")

    def test_texto_con_entradilla_linea_de_suscripcion_enlace_y_firma(self):
        r = CP.linkedin(self.a, V)
        self.assertTrue(r["texto"].startswith(self.a["entradilla"]))
        self.assertIn("Suscríbete gratis para seguir leyendo: https://www.moticias.com/%s/?" % self.a["id"], r["texto"])
        self.assertTrue(r["texto"].endswith("moticias.com - Noticias con M de Movilidad y Transportes"))
        self.assertIn("utm_source=linkedin", r["url"])
        self.assertLessEqual(len(r["texto"]), CP.MAX_LINKEDIN)

    def test_el_enlace_abre_el_redactor_con_ese_texto(self):
        r = CP.linkedin(self.a, V)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(r["abrir"]).query)
        self.assertEqual(urllib.parse.urlparse(r["abrir"]).netloc, "www.linkedin.com")
        self.assertEqual(q["text"][0], r["texto"])
        self.assertEqual(r["plantilla"].replace("{texto}", urllib.parse.quote(r["texto"], safe="")), r["abrir"])

    def test_lo_que_no_esta_publicado_no_se_comparte(self):
        for estado in ("pendiente", "borrador", "retirada"):
            self.assertIsNone(CP.linkedin(dict(self.a, status=estado), V))
        self.assertIsNone(CP.linkedin(self.a, dict(V, redes={"linkedin": {"activo": False}})))


class GhostAlDia(unittest.TestCase):
    """El cron deja en Ghost la entradilla de cada pieza tocando solo el resumen."""
    def setUp(self):
        self.puestos = []
        self.viejo = (os.environ.get("GHOST_URL"), os.environ.get("GHOST_ADMIN_KEY"))
        os.environ["GHOST_URL"], os.environ["GHOST_ADMIN_KEY"] = "https://www.moticias.com", "id:00"
        self.orig = (G.ghost_token, G.resumenes_en_ghost, G.poner_resumen, GS.leer, GS.BD.registrar)
        G.ghost_token = lambda k: "pase"
        GS.BD.registrar = lambda *a, **k: None
        GS.leer = lambda ruta, repo=None: (None, None)
        G.poner_resumen = lambda post, texto, url, token: (self.puestos.append((post["id"], texto)) or True, "ok")

    def tearDown(self):
        G.ghost_token, G.resumenes_en_ghost, G.poner_resumen, GS.leer, GS.BD.registrar = self.orig
        for k, v in zip(("GHOST_URL", "GHOST_ADMIN_KEY"), self.viejo):
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

    def test_cambia_solo_los_que_no_coinciden(self):
        a, b = PIEZAS[0], PIEZAS[1]
        G.resumenes_en_ghost = lambda url, token: {a["id"]: {"id": "g1", "custom_excerpt": a["summary"][:300], "updated_at": "x"},
                                                   b["id"]: {"id": "g2", "custom_excerpt": b["entradilla"], "updated_at": "x"}}
        r = GS.entradillas_al_dia()
        self.assertEqual((r["ok"], r["cambiadas"], r["quedan"]), (True, 1, 0))
        self.assertEqual(self.puestos, [("g1", a["entradilla"])])

    def test_manda_la_pieza_fresca_del_repositorio(self):
        a = PIEZAS[0]
        fresca = dict(a, entradilla="El editor la acaba de cambiar en el gestor y todavía no hay despliegue nuevo.")
        GS.leer = lambda ruta, repo=None: (fresca, "sha")
        G.resumenes_en_ghost = lambda url, token: {a["id"]: {"id": "g1", "custom_excerpt": "otra cosa", "updated_at": "x"}}
        GS.entradillas_al_dia()
        self.assertEqual(self.puestos, [("g1", fresca["entradilla"])])

    def test_sin_tiempo_lo_deja_para_la_siguiente_pasada(self):
        G.resumenes_en_ghost = lambda url, token: {a["id"]: {"id": a["id"], "custom_excerpt": "", "updated_at": "x"} for a in PIEZAS[:5]}
        r = GS.entradillas_al_dia(segundos=-1)
        self.assertEqual((r["cambiadas"], r["quedan"]), (0, 5))
        self.assertFalse(self.puestos)


if __name__ == "__main__":
    unittest.main()
