"""MOTICIAS · API de la sala de prensa (función de Vercel, Python, solo biblioteca estándar). Cambio sala-de-prensa-v1.

Sirve app.moticias.com/prensa/ (página en app/public/prensa/index.html):
  POST /api/prensa?a=asesor      análisis automático + recomendación con la audiencia real (sin coste, sin datos personales)
  POST /api/prensa?a=ia          segunda pasada con Claude (pide correo; ANTHROPIC_API_KEY en Vercel)
  POST /api/prensa?a=enviar      el cliente envía su nota y su plan → cola privada (moticias-equipo/prensa/entrantes/)
  GET  /api/prensa?a=confirmar&t=…  el cliente confirma su correo (verificación del emisor si no escribe desde su dominio)
  GET  /api/prensa?a=baja&t=…     baja de un destinatario (total o de un sector), firmada
  GET  /api/prensa?a=informe&t=…  informe de repercusión del cliente, firmado
  GET  /api/prensa?a=oferta       planes y opciones de visibilidad (de verticals/movilidad.json → prensa)

Variables de entorno (en Vercel, nunca en el repositorio): GITHUB_TOKEN (lee y escribe en movo-es/moticias-equipo),
PRENSA_SECRETO (firma de enlaces; el mismo en las tareas), BREVO_API_KEY (correos de confirmación y aviso), ANTHROPIC_API_KEY
(opcional). Datos personales: solo en el repositorio privado EQUIPO_REPO (por defecto movo-es/moticias-equipo).
"""
import base64, html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import contactos as C  # noqa: E402
import prensa_asesor as A  # noqa: E402
import prensa_comun as P  # noqa: E402
from taxonomia import Taxonomia  # noqa: E402

PRIV = os.environ.get("EQUIPO_REPO", "movo-es/moticias-equipo")
V = A.cfg_vertical()
TX = Taxonomia()
_CACHE = {"contactos": (0, None)}
_IA = []  # marcas de tiempo de llamadas a la IA en esta instancia (freno básico; el cortafuegos de Vercel es el de verdad)
MAX_IA_HORA = 40


# ---------- GitHub (repositorio privado) ----------
def gh(method, path, body=None):
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        return 0, {"message": "falta GITHUB_TOKEN"}
    req = urllib.request.Request("https://api.github.com/repos/%s/contents/%s" % (PRIV, urllib.parse.quote(path)), method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json",
                                          "User-Agent": "moticias-prensa", "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
    except urllib.error.URLError as e:
        return 0, {"message": str(e)}


def leer(path, crudo=False):
    st, r = gh("GET", path)
    if st != 200:
        return None, None
    txt = base64.b64decode(r["content"]).decode("utf-8")
    return (txt if crudo else json.loads(txt)), r["sha"]


def escribir(path, obj, sha, mensaje):
    txt = json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    body = {"message": mensaje + "\n\nSala de prensa (app.moticias.com/prensa/)", "content": base64.b64encode(txt.encode()).decode()}
    if sha:
        body["sha"] = sha
    st, r = gh("PUT", path, body)
    return st in (200, 201), r.get("message", "")


def contactos():
    t, base = _CACHE["contactos"]
    if base is None or time.time() - t > 600:
        base, _ = leer("prensa/contactos.json")
        _CACHE["contactos"] = (time.time(), base)
    return base


# ---------- correo ----------
def correo(para, asunto, cuerpo):
    key = os.environ.get("BREVO_API_KEY")
    if not key:
        return False
    r = V["prensa"]["remitente"]
    body = {"sender": {"email": r["email"], "name": r["nombre"]}, "to": [{"email": x} for x in para], "subject": asunto, "htmlContent": cuerpo}
    req = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=json.dumps(body).encode(), method="POST",
                                 headers={"api-key": key, "Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Moticias/1.0"})
    try:
        urllib.request.urlopen(req, timeout=20).read()
        return True
    except urllib.error.URLError:
        return False


# ---------- acciones ----------
def nota_de(d):
    return {"titulo": str(d.get("titulo") or "")[:300], "subtitulo": str(d.get("subtitulo") or "")[:400],
            "cuerpo": str(d.get("cuerpo") or "")[:20000], "organizacion": str(d.get("organizacion") or "")[:160]}


def asesor(d):
    nota = nota_de(d)
    if len(nota["cuerpo"]) < 80:
        return 400, {"error": "Pegue el texto completo de la nota (al menos un párrafo)."}
    objetivo = d.get("objetivo") if d.get("objetivo") in ("noticia", "lanzamiento", "marca", "venta") else "noticia"
    an = A.analizar(nota, V, TX, objetivo)
    ejes = {k: an["ejes"][k] for k in ("submodo", "modo", "territorios", "temas")}
    base = contactos()
    aud = C.recuento(base, ejes, V["prensa"]["filtro_valor"], TX) if base else None
    medios = [m for m in C.medios_para(ejes, TX) if m["tipo"] != "canal-propio"]
    recs = A.recomendar(an, aud, medios, V, objetivo)
    if not V["prensa"].get("tarifas_publicas"):  # hasta que Rainer confirme las tarifas, la página no enseña precios
        for r in recs:
            if r["precio_eur"] != 0:  # lo gratuito se dice siempre
                r["precio_eur"] = None
    nombres = {"submodo": TX.submodos.get(ejes["submodo"], (None, {"nombre": ejes["submodo"]}))[1]["nombre"],
               "territorios": [TX.nombre_territorio(t) for t in ejes["territorios"]], "temas": [TX.temas[t]["nombre"] for t in ejes["temas"] if t in TX.temas]}
    aud_pub = {"individual": aud["individual"], "prensa": aud["prensa"], "resumen_b2c": aud["resumen_b2c"]} if aud else None
    return 200, {"analisis": an, "ejes_nombres": nombres, "audiencia": aud_pub, "medios": [m["nombre"] for m in medios], "recomendacion": recs}


def ia(d):
    if not C.norm_email(d.get("email")):
        return 400, {"error": "Para la revisión con IA necesitamos un correo de contacto."}
    ahora = time.time()
    while _IA and ahora - _IA[0] > 3600:
        _IA.pop(0)
    if len(_IA) >= MAX_IA_HORA:
        return 429, {"error": "Demasiadas revisiones en la última hora. Inténtelo más tarde."}
    _IA.append(ahora)
    nota = nota_de(d)
    an = A.analizar(nota, V, TX)
    return 200, {"ia": A.ia(nota, an)}


def enviar(d):
    nota = nota_de(d)
    cli = d.get("cliente") or {}
    email = C.norm_email(cli.get("email"))
    if not (nota["titulo"] and len(nota["cuerpo"]) >= 80 and nota["organizacion"]):
        return 400, {"error": "Faltan el titular, el texto o la organización."}
    if not (email and cli.get("nombre")):
        return 400, {"error": "Faltan su nombre y su correo profesional."}
    if not d.get("acepta_condiciones"):
        return 400, {"error": "Debe aceptar las condiciones de publicación."}
    plan = d.get("plan") if d.get("plan") in {p["id"] for p in V["prensa"]["planes"]} | {p["id"] for p in V["prensa"]["visibilidad"]} else "publicacion"
    web = str(cli.get("web") or "")[:200]
    dom_web = urllib.parse.urlparse(web if "://" in web else "https://" + web).netloc.replace("www.", "")
    dom_mail = email.split("@")[1]
    corporativo = bool(dom_web) and (dom_mail == dom_web or dom_mail.endswith("." + dom_web))
    an = A.analizar(nota, V, TX, d.get("objetivo") or "noticia")
    nid = P.nuevo_id(nota["titulo"])
    entrante = {"id": nid, "recibida_en": P.ahora(), "origen": "formulario", "nota": nota, "plan": plan, "objetivo": d.get("objetivo") or "noticia",
                "embargo_hasta": d.get("embargo_hasta") or None,
                "cliente": {"nombre": str(cli["nombre"])[:120], "cargo": str(cli.get("cargo") or "")[:120], "email": email,
                            "telefono": str(cli.get("telefono") or "")[:40], "organizacion": nota["organizacion"], "web": web},
                "verificacion": {"dominio_corporativo": corporativo, "correo_confirmado": False},
                "asesor": {"puntuacion": an["puntuacion"], "veredicto": an["veredicto"], "tipo": an["tipo"]},
                "consentimientos": {"condiciones": True, "comunicaciones_moticias": bool(d.get("acepta_comunicaciones")), "fecha": P.ahora()},
                "estado": "recibida"}
    ok, det = escribir("prensa/entrantes/%s.json" % nid, entrante, None, "Sala de prensa: nota recibida %s" % nid)
    if not ok:
        return 502, {"error": "No hemos podido registrar la nota (%s). Escríbanos a prensa@moticias.com." % det}
    if os.environ.get("PRENSA_SECRETO"):
        enlace = "%s/api/prensa?a=confirmar&t=%s" % (P.base_app(), P.firmar("confirmar", nid))
        correo([email], "Confirme el envío de su nota a MOTICIAS",
               "<p>Hemos recibido «%s».</p><p>Para que podamos publicarla, confirme que la envía usted: <a href=\"%s\">confirmar el envío</a>.</p>"
               "<p>Plan elegido: %s. Le escribiremos en cuanto esté publicada.</p><p>MOTICIAS · Sala de prensa</p>" % (html.escape(nota["titulo"]), enlace, html.escape(plan)))
    correo([V["prensa"]["aviso_director"]], "Sala de prensa: nueva nota (%s, %d/100)" % (plan, an["puntuacion"]),
           "<p>%s · %s</p><p>%s</p><p>Emisor %s (%s).</p>" % (html.escape(nota["organizacion"]), html.escape(nota["titulo"]), html.escape(an["veredicto"]),
                                                               "con dominio corporativo" if corporativo else "SIN dominio corporativo: espera confirmación", html.escape(email)))
    return 200, {"ok": True, "id": nid, "verificacion": "dominio" if corporativo else "correo",
                 "mensaje": "Recibida. %s La sala de prensa la revisa y publica en el mismo día laborable si llega antes de las 14:00." %
                            ("Le hemos enviado un correo para confirmar el envío." if not corporativo else "")}


def pagina(titulo, texto):
    return ("<!DOCTYPE html><html lang=es><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><meta name=robots content=noindex>"
            "<title>%s · MOTICIAS</title><body style='font:16px/1.6 system-ui,sans-serif;max-width:560px;margin:15vh auto;padding:0 20px;color:#111827'>"
            "<div style='font:600 12px system-ui;letter-spacing:.06em;text-transform:uppercase;color:#6b7280'>MOTICIAS · Sala de prensa</div><h1 style='font-size:22px'>%s</h1><p>%s</p></body></html>"
            % (html.escape(titulo), html.escape(titulo), texto))


def confirmar(t):
    nid = P.verificar(t, "confirmar")
    if not nid:
        return 400, pagina("Enlace no válido", "El enlace no es válido o está incompleto.")
    ent, sha = leer("prensa/entrantes/%s.json" % nid)
    if not ent:
        return 404, pagina("No encontrada", "No encontramos esa nota.")
    ent["verificacion"]["correo_confirmado"], ent["verificacion"]["confirmado_en"] = True, P.ahora()
    escribir("prensa/entrantes/%s.json" % nid, ent, sha, "Sala de prensa: correo confirmado %s" % nid)
    return 200, pagina("Envío confirmado", "Gracias. La sala de prensa revisará su nota y le escribirá cuando esté publicada.")


def baja(t):
    v = P.verificar(t, "baja")
    if not v:
        return 400, pagina("Enlace no válido", "El enlace de baja no es válido. Escríbanos a prensa@moticias.com y le damos de baja a mano.")
    cid, _, sector = v.partition("|")
    base, sha = leer("prensa/contactos.json")
    for c in (base or {}).get("contactos", []):
        if c["id"] == cid:
            if sector:
                if sector not in c.setdefault("bajas_sector", []):
                    c["bajas_sector"].append(sector)
                txt = "No recibirá más notas de prensa de este sector. Si quiere dejar de recibir todas, escríbanos a prensa@moticias.com."
            else:
                c["estado"], c["baja_en"] = "baja", P.ahora()
                txt = "No recibirá más notas de prensa de MOTICIAS."
            ok, _ = escribir("prensa/contactos.json", base, sha, "Sala de prensa: baja %s" % cid)
            _CACHE["contactos"] = (0, None)
            return (200, pagina("Baja registrada", txt)) if ok else (502, pagina("Inténtelo de nuevo", "No hemos podido guardar la baja. Escríbanos a prensa@moticias.com."))
    return 200, pagina("Baja registrada", "Su dirección no está en nuestra lista de difusión.")


def informe(t):
    v = P.verificar(t, "informe")
    if not v:
        return 400, pagina("Enlace no válido", "El enlace del informe no es válido.")
    nid, _, fecha = v.partition("|")
    txt, _ = leer("prensa/informes/%s-%s.html" % (nid, fecha), crudo=True)
    return (200, txt) if txt else (404, pagina("Informe no disponible", "Este informe todavía no está generado."))


class handler(BaseHTTPRequestHandler):
    def _enviar(self, st, obj):
        es_html = isinstance(obj, str)
        b = (obj if es_html else json.dumps(obj, ensure_ascii=False)).encode("utf-8")
        self.send_response(st)
        self.send_header("Content-Type", ("text/html" if es_html else "application/json") + "; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Robots-Tag", "noindex")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _q(self):
        return {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).items()}

    def do_GET(self):
        q = self._q()
        a = q.get("a")
        if a == "oferta":
            pub = V["prensa"].get("tarifas_publicas")
            quita = lambda ps: [{k: v for k, v in p.items() if pub or k not in ("precio_eur", "desde_eur") or v == 0} for p in ps]
            return self._enviar(200, {"planes": quita(V["prensa"]["planes"]), "visibilidad": quita(V["prensa"]["visibilidad"]), "marca": V["prensa"]["marca"], "tarifas_publicas": bool(pub)})
        try:
            if a == "confirmar":
                return self._enviar(*confirmar(q.get("t", "")))
            if a == "baja":
                return self._enviar(*baja(q.get("t", "")))
            if a == "informe":
                return self._enviar(*informe(q.get("t", "")))
        except SystemExit as e:  # falta PRENSA_SECRETO
            return self._enviar(503, pagina("Servicio no configurado", html.escape(str(e))))
        return self._enviar(404, {"error": "acción desconocida"})

    def do_POST(self):
        a = self._q().get("a")
        if self.headers.get("X-Prensa") != "1":  # solo la página de la sala de prensa envía esta cabecera
            return self._enviar(403, {"error": "petición no válida"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            d = json.loads(self.rfile.read(min(n, 300000)) or b"{}") if n else {}
        except (ValueError, json.JSONDecodeError):
            return self._enviar(400, {"error": "JSON no válido"})
        if a == "asesor":
            return self._enviar(*asesor(d))
        if a == "ia":
            return self._enviar(*ia(d))
        if a == "enviar":
            return self._enviar(*enviar(d))
        return self._enviar(404, {"error": "acción desconocida"})
