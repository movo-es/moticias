"""Pruebas sin red de «La voz del editor» desde el gestor (cambio OpenSpec `voz-desde-el-panel`).

  python3 -I tests/test_voz.py
"""
import copy, datetime, json, os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "api"))
import gestor as GS  # noqa: E402
import menciones as M  # noqa: E402

SES = {"nombre": "Editor jefe de prueba", "perfil": "superadmin", "permisos": ["redaccion"]}
TEXTO = ("La tesis va en el primer párrafo, con un [enlace](https://www.boe.es/buscar/act.php?id=BOE-A-2025-24545) a la ley. "
         + "palabra " * 140 + "\n\n## Lo que toca\n\nCierre con lo que debería decidirse y quién.")


class VozDesdeElPanel(unittest.TestCase):
    def setUp(self):
        self.escritos, self.filas, self.subidas = [], [], []
        GS.escribir = lambda ruta, obj, sha, mensaje, repo=None: (self.escritos.append((ruta, copy.deepcopy(obj), sha)) or True, "abc1234")
        GS.BD.registrar = lambda *a, **k: None
        GS.BD.insertar = lambda tabla, fila: (self.filas.append((tabla, fila)) or [dict(fila, id=7)])
        GS._subir = lambda a, v, estado=None: (self.subidas.append((a["id"], estado, a.get("published_at"))) or True, "ok")
        GS.ficha_redaccion = lambda pid: {"id": pid}
        os.environ["GITHUB_TOKEN"] = "prueba"

    def test_escribir_deja_la_columna_pendiente_y_valida(self):
        st, r = GS.accion_voz(SES, {"accion": "crear", "title": "El autobús de empresa no es un lujo", "subtitle": "Sub", "body_md": TEXTO})
        self.assertEqual(st, 200)
        ruta, a, sha = self.escritos[0]
        self.assertTrue(ruta.startswith("data/articles/") and ruta.endswith(".json") and sha is None)
        self.assertRegex(a["id"], r"^[a-z0-9]+(?:-[a-z0-9]+)*-[a-z0-9]{4}$")   # el patrón que exige m.js para el menú ✎
        self.assertEqual((a["kind"], a["tipo_contenido"], a["status"], a["author"]), ("opinion", "editorial", "pendiente", "Rainer Uphoff"))
        self.assertNotIn("published_at", a)                                     # no publica: falta su aprobación
        self.assertEqual(a["sources"][0]["kind"], "oficial")                    # el BOE cuenta como fuente oficial
        self.assertFalse(GS.TX.Taxonomia().faltan(a))                           # con las etiquetas comunes completas
        self.assertFalse(self.subidas)

    def test_escribir_rechaza_lo_que_no_es_una_columna(self):
        self.assertEqual(GS.accion_voz(SES, {"accion": "crear", "title": "Corto", "body_md": TEXTO})[0], 400)
        self.assertEqual(GS.accion_voz(SES, {"accion": "crear", "title": "Un título suficiente", "body_md": "dos líneas"})[0], 400)
        self.assertFalse(self.escritos)

    def test_encargar_va_a_la_redaccion_y_nunca_publica_directo(self):
        st, r = GS.accion_voz(SES, {"accion": "encargar", "tema": "Los PMST y las pymes", "enfoque": "La ley mide por centro y deja fuera a las pymes",
                                    "enlaces": "https://www.boe.es/buscar/act.php?id=BOE-A-2025-24545"})
        self.assertEqual(st, 200)
        tabla, fila = self.filas[0]
        self.assertEqual(tabla, "encargos_gestor")
        self.assertTrue(fila["texto"].startswith(GS.VOZ_MARCA))
        self.assertEqual(fila["publicacion"], "revision")
        self.assertEqual(GS.accion_voz(SES, {"accion": "encargar", "tema": "Los PMST y las pymes", "enfoque": "corto"})[0], 400)

    def _aprobar(self, cuando):
        pieza = GS.voz_nueva_pieza({"title": "El autobús de empresa no es un lujo", "body_md": TEXTO}, "prueba")
        GS.leer = lambda ruta, repo=None: (copy.deepcopy(pieza), "sha1")
        cuerpo = {"id": pieza["id"], "accion": "publicar", "texto_ok": True, "imagen_ok": True}
        if cuando:
            cuerpo["cuando"] = cuando
        st, r = GS.accion_redaccion(SES, cuerpo, {})
        self.assertEqual(st, 200)
        return self.escritos[-1][1]

    def test_aprobar_para_ahora(self):
        a = self._aprobar("ahora")
        cuando = datetime.datetime.fromisoformat(a["published_at"])
        self.assertLess(abs((cuando - datetime.datetime.now().astimezone()).total_seconds()), 120)
        self.assertEqual((a["status"], a["voz"]["salida"]), ("publicado", "ahora"))
        self.assertEqual(self.subidas[-1][1], "published")

    def test_publicar_ahora_manda_la_fecha_con_segundos(self):
        # 16-11-2026: Ghost rechazó «2026-11-16T14:41+00:00» y la columna quedó «publicada» sin estar en la web.
        a = self._aprobar("ahora")
        self.assertRegex(a["published_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d$")

    def _registro(self, filas):
        GS.BD.configurada = lambda: True
        GS.BD.leer = lambda tabla, **k: [dict(f) for f in filas]

    def test_una_subida_que_fallo_se_sabe_y_se_reintenta(self):
        pieza = GS.voz_nueva_pieza({"title": "El autobús de empresa no es un lujo", "body_md": TEXTO}, "prueba")
        pieza["status"] = "publicado"
        self._registro([{"objeto": pieza["id"], "accion": "redaccion_publicar", "detalle": {"ghost": False, "commit": "abc"}, "at": "2026-11-16T14:41:46+00:00"}])
        self.assertEqual(list(GS.subidas_fallidas()), [pieza["id"]])
        GS.leer = lambda ruta, repo=None: (copy.deepcopy(pieza), "sha1")
        apuntes = []
        GS.BD.registrar = lambda quien, accion, objeto=None, detalle=None: apuntes.append((accion, objeto, detalle))
        r = GS.reintentar_subidas()
        self.assertTrue(r["ok"])
        self.assertEqual(self.subidas[-1][:2], (pieza["id"], "published"))
        self.assertEqual(apuntes[-1][0], "web_reintento")
        self.assertTrue(apuntes[-1][2]["ghost"])

    def test_si_despues_se_subio_ya_no_cuenta_como_fallida(self):
        self._registro([{"objeto": "x-abcd", "accion": "redaccion_publicar", "detalle": {"ghost": False}, "at": "2026-11-16T14:41:46+00:00"},
                        {"objeto": "x-abcd", "accion": "republicar", "detalle": {"ghost": True}, "at": "2026-11-16T20:10:00+00:00"},
                        {"objeto": "y-abcd", "accion": "redaccion_publicar", "detalle": {"ghost": True}, "at": "2026-11-16T14:58:08+00:00"}])
        self.assertEqual(GS.subidas_fallidas(), {})

    def test_no_reintenta_sin_fin_ni_lo_retirado(self):
        fallo = {"objeto": "x-abcd", "accion": "web_reintento", "detalle": {"ghost": False, "detalle": "Ghost: 422"}, "at": "2026-11-16T15:00:00+00:00"}
        self._registro([fallo] * GS.REINTENTOS_MAX)
        self.assertEqual(GS.subidas_fallidas()["x-abcd"]["intentos"], GS.REINTENTOS_MAX)
        self.assertEqual(GS.reintentar_subidas()["reintentadas"], [])
        self._registro([fallo])
        GS.leer = lambda ruta, repo=None: ({"id": "x-abcd", "status": "retirada"}, "sha1")
        self.assertEqual(GS.reintentar_subidas()["reintentadas"], [])
        self.assertFalse(self.subidas)

    def test_aprobar_sin_elegir_sale_el_lunes_a_las_ocho(self):
        a = self._aprobar(None)
        cuando = datetime.datetime.fromisoformat(a["published_at"])
        self.assertEqual((cuando.weekday(), cuando.hour, cuando.minute), (0, 8, 0))
        self.assertGreater(cuando, datetime.datetime.now(datetime.timezone.utc))
        self.assertEqual(a["voz"]["salida"], "lunes")

    def test_sin_marcar_el_texto_no_se_aprueba(self):
        pieza = GS.voz_nueva_pieza({"title": "El autobús de empresa no es un lujo", "body_md": TEXTO}, "prueba")
        GS.leer = lambda ruta, repo=None: (copy.deepcopy(pieza), "sha1")
        self.assertEqual(GS.accion_redaccion(SES, {"id": pieza["id"], "accion": "publicar", "cuando": "ahora"}, {})[0], 400)
        self.assertFalse(self.subidas)

    def test_la_columna_no_lleva_cajas_de_contenido_patrocinado(self):
        pieza = GS.voz_nueva_pieza({"title": "Los planes de movilidad sostenible al trabajo y las pymes", "body_md": TEXTO + " plan de movilidad sostenible al trabajo PMST " * 5}, "prueba")
        prods = M.cargar_productos(os.path.join(ROOT, "data"))
        self.assertTrue(all(c["puntuacion"] is None for c in M.candidatos(pieza, prods)))

    def test_la_primera_columna_esta_pendiente_y_declara_intereses(self):
        a = json.load(open(os.path.join(ROOT, "data", "articles", "el-poligono-no-tiene-plan-v7kd.json"), encoding="utf-8"))
        if a["status"] != "pendiente":
            self.skipTest("ya aprobada por el editor jefe")
        self.assertNotIn("published_at", a)
        self.assertIn("MOVO", a["author_note"])
        self.assertTrue(all(s.get("url") for s in a["sources"]))


if __name__ == "__main__":
    unittest.main(verbosity=1)
