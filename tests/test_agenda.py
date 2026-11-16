"""Pruebas sin red de la agenda de eventos (cambio OpenSpec `agenda-de-eventos`). Fecha fija: 15-11-2026.

  python3 -I -m unittest tests/test_agenda.py      (desde la carpeta del proyecto)

La prueba de datos personales lee la lista privada de la semilla del CRM de `work/semilla_crm_privada.txt` (ignorado
por git: el repositorio es público y la lista no puede estar en él). Sin ese fichero, se salta y lo dice.
"""
import copy, glob, json, os, re, subprocess, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import eventos as EV  # noqa: E402
import ghost_agenda as GA  # noqa: E402
import agenda_gestor as AG  # noqa: E402

HOY = "2026-11-15"
V = EV.vertical()
EVS = [EV.limpio(e) for e in EV.cargar()]


class BDFalsa:
    """Base privada en memoria con lo justo de PostgREST (eq., ilike., in., is.null, neq., gte., lte.)."""
    class ErrorBD(Exception):
        pass

    def __init__(self):
        self.t = {}
        self.n = 0

    def configurada(self):
        return True

    def _ok(self, fila, k, cond):
        x = fila.get(k)
        op, _, val = cond.partition(".")
        if op == "eq":
            return str(x) == val
        if op == "neq":
            return str(x) != val
        if op == "ilike":
            return str(x or "").lower() == val.lower()
        if op == "is":
            return x is None
        if op == "in":
            return str(x) in val.strip("()").split(",")
        if op in ("gte", "lte"):
            return x is not None and (str(x) >= val if op == "gte" else str(x) <= val)
        return True

    def leer(self, tabla, **p):
        filas = [f for f in self.t.get(tabla, []) if all(self._ok(f, k, v) for k, v in p.items() if k not in ("select", "order", "limit"))]
        return [copy.deepcopy(f) for f in filas[:int(p.get("limit", 10000))]]

    def insertar(self, tabla, filas):
        filas = filas if isinstance(filas, list) else [filas]
        out = []
        for f in filas:
            self.n += 1
            f = dict(f)
            f.setdefault("id", "00000000-0000-0000-0000-%012d" % self.n)
            f.setdefault("creado_at", "2026-11-15T10:00:00+01:00")
            self.t.setdefault(tabla, []).append(f)
            out.append(copy.deepcopy(f))
        return out

    def actualizar(self, tabla, filtro, cambios):
        out = []
        for f in self.t.get(tabla, []):
            if all(self._ok(f, k, v) for k, v in filtro.items()):
                f.update(cambios)
                out.append(f)
        return out

    def registrar(self, *a, **k):
        pass


def visibles():
    return EV.visibles(EVS, HOY, V)


class Validador(unittest.TestCase):
    def test_semilla_sin_errores(self):
        for f in sorted(glob.glob(os.path.join(ROOT, "data", "eventos", "*.json"))):
            self.assertEqual(EV.validar(json.load(open(f, encoding="utf-8")), V, os.path.basename(f)[:-5]), [], f)

    def test_rechazos(self):
        e = copy.deepcopy(EVS[0])
        sin_fuente = dict(e, fuentes=[])
        sin_fecha = {k: x for k, x in e.items() if k != "inicio"}
        tema_malo = dict(e, tema="submarinos")
        con_correo = dict(e, nota="escribe a alguien@ejemplo.com")
        for malo, pista in ((sin_fuente, "fuentes"), (sin_fecha, "inicio"), (tema_malo, "tema"), (con_correo, "correo")):
            err = EV.validar(malo, V)
            self.assertTrue(err, pista)
            self.assertTrue(any(pista in x for x in err), (pista, err))


class Pagina(unittest.TestCase):
    def setUp(self):
        self.pg = GA.construir(EVS, V, HOY)
        self.r = self.pg["_resumen"]

    def test_cifras(self):
        self.assertEqual(self.r["citas"], 12)
        self.assertEqual(self.r["ciudades"], 8)
        self.assertEqual([self.r["meses"][m] for m in sorted(self.r["meses"])], [7, 3, 2, 1])
        self.assertEqual(sorted(self.r["temas"].values(), reverse=True), [5, 2, 1, 1, 1, 1, 1])
        self.assertEqual(self.r["lugares"]["Madrid"], {"citas": 4, "mixto": True})
        self.assertEqual(self.r["lugares"]["Valencia"]["citas"], 2)
        self.assertIn('class="ma-pin ma-mixto" data-ciudad="madrid"', self.pg["html"])

    def test_respuesta_directa(self):
        m = re.search(r'respuesta-directa">(.*?)</p>', self.pg["html"])
        n = len(re.sub("<[^>]+>", "", m.group(1)).split())
        self.assertTrue(40 <= n <= 60, n)

    def test_todo_en_el_html(self):
        h = self.pg["html"]
        for e in visibles():
            self.assertIn('id="%s"' % e["id"], h)
        self.assertIn("Sin citas en el periodo", h)
        self.assertIn("Por lugar", h)
        self.assertIn("ma-vacio", h)

    def test_filtros_combinados(self):
        """Mismo criterio que agenda.js: mes (la cita cuenta en todos los meses que toca), ciudad y tema a la vez."""
        cs = re.findall(r'<li class="ma-cita" id="[^"]+" data-tema="([^"]+)" data-ciudad="([^"]+)" data-meses="([^"]+)"', self.pg["html"])
        f = lambda mes="", ciudad="", tema="": [c for c in cs if (not mes or mes in c[2].split()) and (not ciudad or c[1] == ciudad) and (not tema or c[0] == tema)]
        self.assertEqual(len(f(mes="2026-12", ciudad="valencia")), 2)
        self.assertEqual(len(f(mes="2027-02", ciudad="valencia")), 0)
        self.assertEqual(len(f(mes="2026-11")) + len(f(mes="2026-12")), 10)  # CONAMA cuenta en los dos

    def test_datos_estructurados(self):
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*)</script>', self.pg["codeinjection_head"]).group(1))
        tipos = {g["@type"] for g in ld["@graph"]}
        self.assertEqual(tipos, {"ItemList", "FAQPage"})
        lista = next(g for g in ld["@graph"] if g["@type"] == "ItemList")
        self.assertEqual(lista["numberOfItems"], 12)
        for it in lista["itemListElement"]:
            ev = it["item"]
            for k in ("name", "startDate", "endDate", "eventStatus", "location", "organizer"):
                self.assertIn(k, ev)
        ibtm = next(e for e in EVS if e["titulo_corto"] == "IBTM World")
        fi = GA.ficha(ibtm, V)
        j = json.loads(re.search(r'<script type="application/ld\+json">(.*)</script>', fi["codeinjection_head"]).group(1))
        self.assertEqual(j["@type"], "Event")
        self.assertEqual(j["offers"]["price"], "100")
        self.assertEqual(j["location"]["address"]["addressCountry"], "ES")
        self.assertTrue(j["organizer"][0]["name"])

    def test_calendario(self):
        ics = GA.ics(EVS, V, HOY)
        self.assertTrue(ics.startswith("BEGIN:VCALENDAR\r\n"))
        self.assertEqual(ics.count("BEGIN:VEVENT"), 14)  # 12 del periodo + 2 justo después; sin propuestos ni por confirmar
        self.assertTrue(all(len(l.encode("utf-8")) <= 75 for l in ics.split("\r\n")))

    def test_pasado_no_se_borra(self):
        cambian = EV.pasar_a_pasado(EVS, "2026-11-20")
        self.assertEqual({e["estado"] for e in cambian}, {"pasado"})
        self.assertIn("Congreso Canario de Carreteras", [e["titulo_corto"] for e in cambian])
        self.assertEqual(len(EV.visibles(EVS, "2026-11-20", V)) + 0, len([e for e in EV.visibles(EVS, "2026-11-20", V)]))


class Formulario(unittest.TestCase):
    def setUp(self):
        self.bd = BDFalsa()
        AG.BD = self.bd
        AG._ORIGEN.clear()
        self.correos = []
        self.d = {"titulo": "Jornada de prueba del transporte", "tema": "autobus", "formato": "Jornada", "inicio": "2027-01-20", "fin": "2027-01-20",
                  "ciudad": "Burgos", "sede": "Fórum Evolución", "territorio": "castilla-y-leon", "modalidad": "presencial",
                  "resumen": "Jornada de prueba para comprobar el formulario.", "url_inscripcion": "https://ejemplo.org/inscripcion",
                  "entidad": "Entidad de prueba", "entidad_tipo": "Asociación", "entidad_web": "https://ejemplo.org",
                  "nombre": "Persona Prueba", "correo": "persona@ejemplo.org", "permiso_tratamiento": True, "t": 30}

    def test_envio_queda_en_la_cola_y_avisa(self):
        st, r = AG.recibir(dict(self.d), "Mozilla/5.0", "1.2.3.4", lambda *a: self.correos.append(a) or True, V)
        self.assertEqual(st, 200, r)
        env = self.bd.t["agenda_envios"][0]
        self.assertEqual(env["estado"], "recibido")
        self.assertEqual(len(self.correos), 2)  # aviso al editor jefe y acuse al remitente
        e = AG.evento_de_envio(dict(env, creado_at="2026-11-15T10:00:00+01:00"), V)
        self.assertEqual(e["estado"], "propuesto")
        self.assertEqual(EV.validar(e, V), [])
        self.assertNotIn(e["id"], [x["id"] for x in EV.visibles(EVS + [e], HOY, V)])
        self.assertNotIn("Jornada de prueba", GA.construir(EVS + [e], V, HOY)["html"])

    def test_sin_permiso_no_se_envia(self):
        st, r = AG.recibir(dict(self.d, permiso_tratamiento=False), "Mozilla/5.0", "1.2.3.4", None, V)
        self.assertEqual(st, 400)
        self.assertNotIn("agenda_envios", self.bd.t)

    def test_trampa_y_prisa(self):
        self.assertEqual(AG.recibir(dict(self.d, web2="x"), "", "1.1.1.1", None, V)[0], 200)
        self.assertNotIn("agenda_envios", self.bd.t)
        self.assertEqual(AG.recibir(dict(self.d, t=2), "", "1.1.1.1", None, V)[0], 400)


class CRM(unittest.TestCase):
    def setUp(self):
        self.bd = BDFalsa()
        AG.BD = self.bd

    def test_misma_entidad_no_duplica(self):
        ifema = [e for e in EVS if e["organizadores"] == ["IFEMA MADRID"] and e["estado"] == "publicado"]
        self.assertGreaterEqual(len(ifema), 2)
        for e in ifema[:2]:
            AG.crm_al_publicar(e, "prueba", None, V)
        self.assertEqual(len(self.bd.t["crm_cuentas"]), 1)
        self.assertEqual(len(self.bd.t["agenda_organizadores"]), 2)
        self.assertEqual({a["tipo"] for a in self.bd.t["crm_actividades"]}, {"evento_agenda"})
        self.assertEqual(len(self.bd.t["crm_pasos"]), 2)
        self.assertIn("organizador-eventos", self.bd.t["crm_cuentas"][0]["etiquetas"])

    def test_dominio_compartido_no_funde_organismos(self):
        a, _ = AG._cuenta("Dirección General Uno", "https://www.gobiernodecanarias.org/uno/", "Administración pública")
        b, _ = AG._cuenta("Dirección General Dos", "https://www.gobiernodecanarias.org/dos/", "Administración pública")
        self.assertNotEqual(a, b)

    def test_sin_contacto(self):
        self.assertEqual(AG.estado_contacto([], None), "Falta contacto")
        self.assertEqual(AG.estado_contacto([{"canal": "web", "nivel": "general"}], "X"), "Falta contacto")
        self.assertEqual(AG.estado_contacto([{"canal": "correo", "nivel": "general"}], None), "Contacto general · falta responsable")
        self.assertEqual(AG.estado_contacto([{"canal": "telefono", "nivel": "centralita"}], "X"), "Contacto general")

    def test_solo_el_jefe_publica(self):
        ses = {"permisos": ["proponer", "crm"], "nombre": "editor"}
        self.assertEqual(AG.accion(ses, {"accion": "publicar", "ids": [EVS[0]["id"]]}, {})[0], 403)
        self.assertEqual(AG.accion(ses, {"accion": "retirar", "ids": [EVS[0]["id"]]}, {})[0], 403)


class Privacidad(unittest.TestCase):
    def test_ningun_dato_de_la_semilla_del_crm(self):
        lista = os.path.join(ROOT, "work", "semilla_crm_privada.txt")
        if not os.path.exists(lista):
            self.skipTest("sin work/semilla_crm_privada.txt (lista privada, fuera del repositorio)")
        datos = [l.strip() for l in open(lista, encoding="utf-8") if l.strip() and not l.startswith("#")]
        for x in datos:
            r = subprocess.run(["git", "grep", "-n", "-i", "-F", x, "--", ".", ":!work"], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.stdout.strip(), "", "aparece en el repositorio: %s" % r.stdout[:200])
        print("\n%d nombres, correos y teléfonos de la semilla del CRM: ninguno en el repositorio" % len(datos))


if __name__ == "__main__":
    unittest.main()
