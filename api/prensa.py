"""MOTICIAS · API de la sala de prensa para clientes (función de Vercel, Python, solo biblioteca estándar).
Cambio sala-de-prensa-v1, unido a la base de prensa (prensa-y-medios): los datos viven en la base privada (src/bd.py).

Sirve app.moticias.com/prensa/ (página en app/public/prensa/index.html):
  POST /api/prensa?a=asesor        análisis automático + recomendación con la audiencia real de la base de prensa
  POST /api/prensa?a=ia            segunda pasada con Claude (pide correo; ANTHROPIC_API_KEY en Vercel)
  POST /api/prensa?a=enviar        el cliente envía su nota y su plan → CRM (cuenta y persona) + prensa_notas
  GET  /api/prensa?a=confirmar&t=… el cliente confirma su correo (verificación del emisor si no escribe desde su dominio)
  GET  /api/prensa?a=informe&t=…   informe de repercusión del cliente, siempre al día, firmado
  GET  /api/prensa?a=oferta        planes y opciones de visibilidad (verticals/movilidad.json → prensa)
Las bajas de los destinatarios las atiende el gestor (src/prensa.py, ?a=prensa_baja).

Variables de entorno (en Vercel, nunca en el repositorio): las de src/bd.py (SUPABASE_URL, SUPABASE_ANON_KEY,
MOTICIAS_BD_CLAVE, que también firma los enlaces), BREVO_API_KEY y PRENSA_REMITENTE (correos de confirmación y aviso),
ANTHROPIC_API_KEY (opcional).
"""
import datetime, html, json, os, sys, time, urllib.parse
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import bd as BD  # noqa: E402
import prensa_asesor as A  # noqa: E402
import prensa_valor as PV  # noqa: E402
import prensa_comun as P  # noqa: E402
from taxonomia import Taxonomia  # noqa: E402

V = A.cfg_vertical()
TX = Taxonomia()
_CACHE = {}  # recuentos de audiencia por ejes, 10 minutos
_IA = []  # marcas de tiempo de llamadas a la IA en esta instancia (freno básico; el cortafuegos de Vercel es el de verdad)
MAX_IA_HORA = 40


# ---------- correo ----------
def correo(para, asunto, cuerpo):
    import prensa as PR
    try:
        PR._brevo("POST", "/smtp/email", {"sender": PR._remitente(), "to": [{"email": x} for x in para], "subject": asunto,
                                          "htmlContent": cuerpo, "tags": ["sala-de-prensa"]})
        return True
    except Exception:  # noqa: BLE001 — sin Brevo la nota queda registrada igualmente
        return False


def audiencia(ejes, plan="difusion"):
    k = json.dumps([ejes, plan], sort_keys=True)
    t, v = _CACHE.get(k, (0, None))
    if time.time() - t > 600:
        v = PV.recuento(ejes, plan, TX)
        _CACHE[k] = (time.time(), v)
    return v


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
    aud = audiencia(ejes, "difusion")
    medios = [{"nombre": x} for x in (aud or {}).get("nombres_medios", [])]
    recs = A.recomendar(an, aud, medios, V, objetivo)
    if not V["prensa"].get("tarifas_publicas"):  # hasta que Rainer confirme las tarifas, la página no enseña precios
        for r in recs:
            if r["precio_eur"] != 0:  # lo gratuito se dice siempre
                r["precio_eur"] = None
    nombres = {"submodo": TX.submodos.get(ejes["submodo"], (None, {"nombre": ejes["submodo"]}))[1]["nombre"],
               "territorios": [TX.nombre_territorio(t) for t in ejes["territorios"]], "temas": [TX.temas[t]["nombre"] for t in ejes["temas"] if t in TX.temas]}
    aud_pub = {"individual": aud["individual"], "prensa": aud["prensa"], "periodistas": aud["periodistas"], "redacciones": aud["redacciones"],
               "medios": aud["medios"]} if aud else None
    return 200, {"analisis": an, "ejes_nombres": nombres, "audiencia": aud_pub, "medios": [m["nombre"] for m in medios], "recomendacion": recs}


def ia(d):
    if not P.norm_email(d.get("email")):
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


def _cuenta_cliente(nombre, web, dominio):
    """La organización emisora en el CRM: se busca por dominio y, si no está, se crea como empresa en «contactado»
    con un siguiente paso para hoy (una cuenta en marcha siempre lleva paso con fecha)."""
    if dominio:
        r = BD.leer("crm_cuentas", select="id,tipo", dominio="eq." + dominio, archivada_at="is.null", limit="5")
        r = [x for x in r if x["tipo"] != "medio"] or r
        if r:
            return r[0]["id"], False
    fila = BD.insertar("crm_cuentas", {"producto": "moticias", "tipo": "empresa", "nombre": nombre[:200], "web": web or None,
                                       "dominio": dominio or None, "origen": "sala-de-prensa", "etiquetas": ["sala-de-prensa"],
                                       "creada_por": "sala de prensa"})[0]
    BD.insertar("crm_estados", {"cuenta_id": fila["id"], "estado": "contactado", "quien": "sala de prensa", "motivo": "envió una nota de prensa"})
    return fila["id"], True


def _persona(cuenta_id, cli):
    r = BD.leer("crm_personas", select="id,no_contactar_at", correo="eq." + cli["email"], limit="1")
    if r:
        return r[0]["id"]
    return BD.insertar("crm_personas", {"cuenta_id": cuenta_id, "nombre": cli["nombre"][:120], "cargo": (cli.get("cargo") or "")[:160] or None,
                                        "perfil": "comunicacion", "correo": cli["email"], "telefono": cli.get("telefono") or None,
                                        "creada_por": "sala de prensa"})[0]["id"]


def enviar(d):
    nota = nota_de(d)
    cli = d.get("cliente") or {}
    email = P.norm_email(cli.get("email"))
    if not (nota["titulo"] and len(nota["cuerpo"]) >= 80 and nota["organizacion"]):
        return 400, {"error": "Faltan el titular, el texto o la organización."}
    if not (email and cli.get("nombre")):
        return 400, {"error": "Faltan su nombre y su correo profesional."}
    if not d.get("acepta_condiciones"):
        return 400, {"error": "Debe aceptar las condiciones de publicación."}
    if not BD.configurada():
        return 503, {"error": "La sala de prensa no está disponible ahora mismo. Escríbanos a prensa@moticias.com."}
    planes = {p["id"] for p in V["prensa"]["planes"]} | {p["id"] for p in V["prensa"]["visibilidad"]}
    plan = d.get("plan") if d.get("plan") in planes else "publicacion"
    web = str(cli.get("web") or "")[:200]
    dom_web = urllib.parse.urlparse(web if "://" in web else "https://" + web).netloc.replace("www.", "") if web else ""
    dom_mail = email.split("@")[1]
    corporativo = bool(dom_web) and (dom_mail == dom_web or dom_mail.endswith("." + dom_web))
    an = A.analizar(nota, V, TX, d.get("objetivo") or "noticia")
    nid = P.nuevo_id(nota["titulo"])
    try:
        cuenta_id, nueva = _cuenta_cliente(nota["organizacion"], web, dom_web or (dom_mail if corporativo else ""))
        persona_id = _persona(cuenta_id, {"nombre": str(cli["nombre"]), "cargo": str(cli.get("cargo") or ""), "email": email,
                                          "telefono": str(cli.get("telefono") or "")[:40]})
        if nueva:
            BD.insertar("crm_pasos", {"cuenta_id": cuenta_id, "persona_id": persona_id, "que": "Sala de prensa: revisar y publicar su nota",
                                      "fecha": datetime.date.today().isoformat(), "responsable": "oficina", "creado_por": "sala de prensa"})
        BD.insertar("crm_actividades", {"cuenta_id": cuenta_id, "persona_id": persona_id, "tipo": "correo_entrante",
                                        "notas": ("Nota de prensa recibida (%s, plan %s, asesor %d/100): %s" % (nid, plan, an["puntuacion"], nota["titulo"]))[:2000],
                                        "quien": "sala de prensa"})
        BD.insertar("prensa_notas", {"id": nid, "cuenta_id": cuenta_id, "persona_id": persona_id, "titulo": nota["titulo"],
                                     "nota": {"subtitulo": nota["subtitulo"], "cuerpo": nota["cuerpo"], "organizacion": nota["organizacion"], "web": web},
                                     "plan": plan, "objetivo": d.get("objetivo") or "noticia",
                                     "asesor": {"puntuacion": an["puntuacion"], "veredicto": an["veredicto"], "tipo": an["tipo"], "ejes": an["ejes"], "fecha": P.ahora()},
                                     "verificacion": {"dominio_corporativo": corporativo, "correo_confirmado": False},
                                     "consentimientos": {"condiciones": True, "comunicaciones_moticias": bool(d.get("acepta_comunicaciones")), "fecha": P.ahora()},
                                     "embargo_hasta": d.get("embargo_hasta") or None})
    except BD.ErrorBD as e:
        return 502, {"error": "No hemos podido registrar la nota (%s). Escríbanos a prensa@moticias.com." % e}
    if not corporativo:
        enlace = "%s/api/prensa?a=confirmar&t=%s" % (P.base_app(), P.firmar("confirmar", nid))
        correo([email], "Confirme el envío de su nota a MOTICIAS",
               "<p>Hemos recibido «%s».</p><p>Para que podamos publicarla, confirme que la envía usted: <a href=\"%s\">confirmar el envío</a>.</p>"
               "<p>Plan elegido: %s. Le escribiremos en cuanto esté publicada.</p><p>MOTICIAS · Sala de prensa</p>" % (html.escape(nota["titulo"]), enlace, html.escape(plan)))
    correo([V["prensa"]["aviso_director"]], "Sala de prensa: nueva nota (%s, %d/100)" % (plan, an["puntuacion"]),
           "<p>%s · %s</p><p>%s</p><p>Emisor %s (%s). Ficha en el CRM del gestor.</p>" % (html.escape(nota["organizacion"]), html.escape(nota["titulo"]), html.escape(an["veredicto"]),
                                                               "con dominio corporativo" if corporativo else "SIN dominio corporativo: espera confirmación", html.escape(email)))
    return 200, {"ok": True, "id": nid, "verificacion": "dominio" if corporativo else "correo",
                 "mensaje": "Recibida. %sLa sala de prensa la revisa y publica en el mismo día laborable si llega antes de las 14:00." %
                            ("Le hemos enviado un correo para confirmar el envío. " if not corporativo else "")}


def pagina(titulo, texto):
    return ("<!DOCTYPE html><html lang=es><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><meta name=robots content=noindex>"
            "<title>%s · MOTICIAS</title><body style='font:16px/1.6 system-ui,sans-serif;max-width:560px;margin:15vh auto;padding:0 20px;color:#111827'>"
            "<div style='font:600 12px system-ui;letter-spacing:.06em;text-transform:uppercase;color:#6b7280'>MOTICIAS · Sala de prensa</div><h1 style='font-size:22px'>%s</h1><p>%s</p></body></html>"
            % (html.escape(titulo), html.escape(titulo), texto))


def confirmar(t):
    nid = P.verificar(t, "confirmar")
    if not nid:
        return 400, pagina("Enlace no válido", "El enlace no es válido o está incompleto.")
    ped = P.leer_pedido(nid)
    if not ped:
        return 404, pagina("No encontrada", "No encontramos esa nota.")
    P.guardar_pedido(nid, {"verificacion": dict(ped.get("verificacion") or {}, correo_confirmado=True, confirmado_at=P.ahora())})
    return 200, pagina("Envío confirmado", "Gracias. La sala de prensa revisará su nota y le escribirá cuando esté publicada.")


def informe(t):
    import prensa_impacto as I
    nid = P.verificar(t, "informe")
    if not nid:
        return 400, pagina("Enlace no válido", "El enlace del informe no es válido.")
    try:
        nota = P.leer_nota(nid)
    except FileNotFoundError:
        return 404, pagina("Informe no disponible", "Esta nota todavía no está publicada.")
    reg = I.registro(nid)
    return 200, I.informe_html(nota, reg, I.metricas_envio(reg.get("envio_id")), I.medios())


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
            if a == "informe":
                return self._enviar(*informe(q.get("t", "")))
        except BD.ErrorBD as e:
            return self._enviar(502, pagina("Inténtelo más tarde", html.escape(str(e))))
        except SystemExit as e:  # falta la llave que firma los enlaces
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
