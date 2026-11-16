"""Pruebas sin red del comprobador diario de los enlaces promocionados (cambio OpenSpec `comprobador-diario`).

  python3 -I tests/test_comprobador.py
"""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seguimiento as S  # noqa: E402
from test_agenda import BDFalsa  # noqa: E402


class Comprobador(unittest.TestCase):
    def setUp(self):
        self.bd = BDFalsa()
        S.BD = self.bd
        self.correos = []
        import menciones as M
        M.enviar_correo = lambda asunto, cuerpo, para, de, dry_run=False: (self.correos.append(asunto) or True, "ok")
        S.objetivos = lambda: [{"anuncio": "caja:prueba", "url": "https://ejemplo.org/", "nombre": "Prueba"}]
        S.time.sleep = lambda s: None

    def test_una_vez_al_dia_y_segura_en_la_ultima_pasada(self):
        S.visitar = lambda url, tiempo=15: (True, 200, url, 120, None)
        S.hora_madrid = lambda: S.datetime.datetime(2026, 11, 16, 20, 23)
        S.comprobados_hoy = lambda: set()
        self.assertEqual(len(S.comprobar()), 1)          # última pasada: seguro
        S.comprobados_hoy = lambda: {"caja:prueba"}
        self.assertEqual(len(S.comprobar()), 0)          # ya comprobado hoy: no repite

    def test_correo_si_falla_dos_veces_seguidas_y_solo_una_vez(self):
        S.visitar = lambda url, tiempo=15: (False, 503, url, 90, "el destino respondió 503")
        S.comprobados_hoy = lambda: set()
        S.hora_madrid = lambda: S.datetime.datetime(2026, 11, 16, 20, 23)
        S.comprobar()                                     # 1.º fallo: sin correo
        self.assertEqual(self.correos, [])
        self.bd.t["pub_comprobaciones"][0]["at"] = "2026-11-15T10:00"
        S.comprobar()                                     # 2.º fallo seguido: correo
        self.assertEqual(len(self.correos), 1)
        self.bd.t["pub_comprobaciones"][1]["at"] = "2026-11-16T10:00"
        S.comprobar()                                     # 3.º: la racha ya avisó
        self.assertEqual(len(self.correos), 1)

    def test_csv_auditable(self):
        self.bd.insertar("pub_comprobaciones", {"anuncio": "caja:prueba", "at": "2026-11-16T12:00:00+01:00", "ok": True, "estado": 200, "ms": 100, "url_final": "https://ejemplo.org/", "origen": "agente"})
        csv = S.comprobaciones_csv("caja:prueba", 30)
        self.assertTrue(csv.startswith("fecha_hora,resultado,estado_http"))
        self.assertIn('"funciona"', csv)


if __name__ == "__main__":
    unittest.main()
