"""MOTICIAS · Agenda de eventos en el gestor y en la base privada (cambio OpenSpec `agenda-de-eventos`, 16-11-2026).

Lo usan api/agenda.py (formulario público «Subir mi evento» y calendario .ics) y api/gestor.py (pestaña «Agenda»,
bloque «Agenda» de «Inicio», cron del comprobador). Los eventos públicos viven en data/eventos/ (src/eventos.py); aquí
está lo privado (migración 015): envíos del formulario, organizadores y responsables, contactos con su nivel y su
fuente, comprobaciones de enlaces, avisos y barridos.

Reglas (no se negocian):
- Lo que sube un tercero o encuentra el barrido entra como `propuesto`; publicar, retirar y restaurar solo los hace el
  editor jefe (permiso `piezas`; el servidor responde 403). Editor y oficina proponen.
- Nada se borra: retirar es `estado: retirado`; lo terminado pasa a `pasado`.
- CRM sin duplicados: la cuenta se casa por dominio de la web (y además por nombre en los dominios compartidos por
  muchos organismos); sin web, por nombre exacto. Etiqueta `organizador-eventos`, origen `agenda`.
- Contacto más cercano: cada dato con canal, nivel (directo · prensa · general · centralita), URL de fuente y fecha.
  Nada deducido; sin ninguno, «Falta contacto». «No contactar» es para siempre. Un contacto público no es permiso
  comercial: los permisos del formulario se guardan tal como se marcaron, con fecha y texto.
"""
import datetime, hashlib, html, json, os, random, re, sys, time, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import bd as BD  # noqa: E402
import eventos as EV  # noqa: E402

E = lambda s: html.escape(str(s if s is not None else ""), quote=True)  # noqa: E731
_ORIGEN = {}  # freno en memoria por origen (además del de la base)
DOMINIOS_COMPARTIDOS = ("gobiernodecanarias.org", "juntadeandalucia.es", "aragon.es", "gob.es", "comunidad.madrid", "madrid.org", "gencat.cat",
                        "gva.es", "navarra.es", "euskadi.eus", "xunta.gal", "jcyl.es", "castillalamancha.es", "carm.es", "asturias.es",
                        "cantabria.es", "larioja.org", "caib.es", "juntaex.es", "europa.eu", "mitma.es", "transportes.gob.es")
TIPO_CUENTA = {"Administración pública": "institucion", "Asociación": "institucion", "Universidad o centro de investigación": "institucion",
               "Empresa": "empresa", "Recinto ferial o de congresos": "empresa", "Otra": "otro"}
NIVEL_ORDEN = {"directo": 0, "prensa": 1, "general": 2, "centralita": 3}


def hoy():
    return datetime.date.today().isoformat()


def ahora():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def dominio(web):
    if not web:
        return ""
    w = web if "://" in web else "https://" + web
    d = urllib.parse.urlparse(w).netloc.lower().split(":")[0]
    return d[4:] if d.startswith("www.") else d


def compartido(dom):
    return any(dom == x or dom.endswith("." + x) for x in DOMINIOS_COMPARTIDOS)


# ---------- formulario público «Subir mi evento» ----------
def _texto(d, k, n):
    return " ".join(str(d.get(k) or "").split())[:n]


def recibir(d, ua, ip, correo=None, v=None):
    """Envío del formulario → agenda_envios (estado `recibido`). Nunca publica nada. Devuelve (estado HTTP, cuerpo)."""
    v = v or EV.vertical()
    c = EV.cfg(v)
    if d.get("web2"):  # campo trampa: solo lo rellenan los robots; se responde como si nada
        return 200, {"ok": True, "mensaje": "Gracias. La redacción lo revisará."}
    try:
        seg = int(d.get("t") or 0)
    except (TypeError, ValueError):
        seg = 0
    if seg < c["formulario"]["segundos_minimos"]:
        return 400, {"error": "Revisa los datos y vuelve a enviarlo dentro de unos segundos."}
    if not (d.get("permiso_tratamiento") is True or str(d.get("permiso_tratamiento")) in ("1", "true", "on")):
        return 400, {"error": "Sin el permiso de tratamiento no podemos revisar ni publicar el evento."}
    ev = {k: _texto(d, k, n) for k, n in (("titulo", 200), ("tema", 30), ("formato", 40), ("inicio", 10), ("fin", 10), ("ciudad", 80), ("sede", 160),
                                           ("territorio", 40), ("modalidad", 20), ("resumen", 600), ("url_inscripcion", 300), ("precio", 120), ("cartel", 300))}
    ent = {"nombre": _texto(d, "entidad", 200), "tipo": _texto(d, "entidad_tipo", 60), "web": _texto(d, "entidad_web", 300)}
    per = {"nombre": _texto(d, "nombre", 120), "cargo": _texto(d, "cargo", 160), "correo": _texto(d, "correo", 200).lower(), "telefono": _texto(d, "telefono", 40)}
    faltan = [n for k, n in (("titulo", "nombre del evento"), ("tema", "tema"), ("inicio", "fecha de inicio"), ("ciudad", "ciudad"), ("territorio", "comunidad"),
                             ("resumen", "resumen"), ("url_inscripcion", "enlace de inscripción")) if not ev[k]]
    faltan += [n for k, n in (("nombre", "entidad organizadora"),) if not ent[k]] + [n for k, n in (("nombre", "tu nombre"), ("correo", "tu correo")) if not per[k]]
    if faltan:
        return 400, {"error": "Falta: " + ", ".join(faltan) + "."}
    if ev["tema"] not in {t["id"] for t in c["temas"]} or ev["territorio"] not in EV.territorios(v):
        return 400, {"error": "Elige el tema y la comunidad de las listas."}
    if not EV.FECHA.match(ev["inicio"]) or (ev["fin"] and (not EV.FECHA.match(ev["fin"]) or ev["fin"] < ev["inicio"])) or ev["inicio"] < hoy():
        return 400, {"error": "Revisa las fechas: el inicio no puede haber pasado y el fin no puede ser anterior."}
    if EV.palabras(ev["resumen"]) > 60:
        return 400, {"error": "El resumen pasa de 60 palabras."}
    if not EV.URL_OK.match(ev["url_inscripcion"]) or (ent["web"] and not EV.URL_OK.match(ent["web"] if "://" in ent["web"] else "https://" + ent["web"])):
        return 400, {"error": "Revisa los enlaces (deben empezar por https://)."}
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", per["correo"]):
        return 400, {"error": "El correo no es válido."}
    if per["telefono"] and not (9 <= len(re.sub(r"\D", "", per["telefono"])) <= 15):
        return 400, {"error": "El teléfono no es válido."}
    huella = hashlib.sha256(("%s|%s" % (ip or "?", hoy())).encode()).hexdigest()[:40]
    t = time.time()
    _ORIGEN[huella] = [x for x in _ORIGEN.get(huella, []) if t - x < 86400] + [t]
    tope = c["formulario"]["maximo_por_origen_dia"]
    if len(_ORIGEN[huella]) > tope:
        return 429, {"error": "Has enviado muchos eventos hoy. Escríbenos a redaccion@moticias.com."}
    if not BD.configurada():
        return 503, {"error": "El formulario no está disponible ahora mismo. Escríbenos a redaccion@moticias.com."}
    try:
        if len(BD.leer("agenda_envios", select="id", huella_origen="eq." + huella, limit=str(tope + 1))) >= tope:
            return 429, {"error": "Has enviado muchos eventos hoy. Escríbenos a redaccion@moticias.com."}
        import ghost_agenda as GA
        marca = ahora()
        fila = BD.insertar("agenda_envios", {
            "estado": "recibido", "evento": ev, "entidad": ent, "nombre": per["nombre"], "cargo": per["cargo"] or None, "correo": per["correo"], "telefono": per["telefono"] or None,
            "permiso_tratamiento_at": marca, "permiso_boletin_at": marca if _si(d.get("permiso_boletin")) else None,
            "permiso_comercial_at": marca if _si(d.get("permiso_comercial")) else None,
            "permisos_texto": {k: {"texto": GA.PERMISOS[k], "marcado": k == "tratamiento" or _si(d.get("permiso_" + k))} for k in GA.PERMISOS},
            "huella_origen": huella, "historial": [{"cuando": marca, "quien": "formulario", "que": "recibido"}]})[0]
    except BD.ErrorBD as e:
        return 502, {"error": "No hemos podido guardarlo (%s). Escríbenos a redaccion@moticias.com." % e}
    if correo:
        para = (v.get("prensa") or {}).get("aviso_editor_jefe")
        if para:
            correo([para], "Agenda: evento propuesto por un organizador · %s" % ev["titulo"][:80],
                   "<p><b>%s</b> · %s · %s</p><p>Propuesto por %s (%s).</p><p><a href=\"https://app.moticias.com/gestor/?vista=agenda&agenda_envio=%s\">Revisarlo en la cola de la agenda</a></p>" % (
                       E(ev["titulo"]), E(ev["inicio"]), E(ev["ciudad"]), E(ent["nombre"]), E(dominio(ent["web"]) or "sin web"), fila["id"]))
        correo([per["correo"]], "Hemos recibido tu evento para la agenda de MOTICIAS",
               "<p>Hola:</p><p>Hemos recibido «%s» (%s, %s). La redacción comprueba los datos en la web del organizador y, si encaja, "
               "lo publica en la agenda; te escribiremos con el enlace a su ficha o para pedirte lo que falte.</p>"
               "<p>Responsable del tratamiento: Avionline S.L. (MOTICIAS). Para cualquier cambio, responde a este correo.</p><p>MOTICIAS · Agenda</p>" % (
                   E(ev["titulo"]), E(ev["inicio"]), E(ev["ciudad"])))
    return 200, {"ok": True, "id": fila["id"], "mensaje": "La redacción comprobará los datos en la web del organizador y te escribirá al publicarlo, con el enlace a su ficha."}


def _si(x):
    return x is True or str(x) in ("1", "true", "on")


# ---------- de envío a evento ----------
def evento_de_envio(env, v=None):
    """Borrador de data/eventos/ a partir de un envío: `propuesto`, origen `tercero`, con la web del organizador como
    fuente pendiente de comprobar (fecha de hoy solo cuando la redacción la abra; aquí, la del envío)."""
    v = v or EV.vertical()
    ev, ent = env["evento"], env["entidad"]
    e = {"titulo": ev["titulo"], "titulo_corto": ev["titulo"][:60], "inicio": ev["inicio"], "fin": ev.get("fin") or ev["inicio"], "tema": ev["tema"],
         "formato": ev.get("formato") or "Jornada", "modalidad": ev.get("modalidad") or "presencial", "publico": "profesional", "ciudad": ev["ciudad"],
         "sede": ev.get("sede") or "sede sin publicar", "territorio": ev["territorio"], "resumen": ev["resumen"], "organizadores": [ent["nombre"]],
         "url_inscripcion": ev["url_inscripcion"], "estado": "propuesto", "origen": "tercero",
         "fuentes": [{"url": ev["url_inscripcion"], "fecha": env["creado_at"][:10], "nota": "enlace que dio el organizador; falta comprobarlo"}],
         "nota": "Propuesto por el organizador; pendiente de comprobar."}
    if ev.get("precio"):
        e["precio"] = ev["precio"]
    if ent.get("web"):
        e["url_oficial"] = ent["web"] if "://" in ent["web"] else "https://" + ent["web"]
    e["geo"] = _geo_ciudad(ev["ciudad"], v) or {"lat": 40.42, "lon": -3.7}  # ciudad desconocida: la redacción la sitúa al revisarlo
    e["id"] = "%s-%s" % (e["inicio"], EV.slug(e["titulo_corto"]))
    return e


def duplicados(e, evs):
    """Posibles duplicados: misma fecha de inicio y ciudad, o título muy parecido."""
    t = set(EV.slug(e.get("titulo")).split("-")) - {"de", "del", "la", "el", "y", "en", "2026", "2027", "i", "ii"}
    out = []
    for x in evs:
        if x["id"] == e.get("id"):
            continue
        tx = set(EV.slug(x.get("titulo")).split("-"))
        parecido = len(t & tx) / max(1, len(t)) if t else 0
        if (x.get("inicio") == e.get("inicio") and EV.slug(x.get("ciudad")) == EV.slug(e.get("ciudad"))) or parecido >= 0.6:
            out.append({"id": x["id"], "titulo": x["titulo"], "inicio": x.get("inicio"), "ciudad": x.get("ciudad"), "estado": x.get("estado")})
    return out


# ---------- CRM ----------
def _cuenta(nombre, web, tipo_ent=None, quien="agenda"):
    """Crea o actualiza la cuenta de una entidad organizadora sin duplicar. Devuelve (id, nueva)."""
    dom = dominio(web)
    filas = []
    if dom:
        filas = BD.leer("crm_cuentas", select="id,nombre,tipo,etiquetas,web", dominio="eq." + dom, archivada_at="is.null", limit="20")
        if compartido(dom):
            filas = [f for f in filas if EV.slug(f["nombre"]) == EV.slug(nombre)]
        filas = [f for f in filas if f["tipo"] != "medio"] or filas
    if not filas:
        filas = [f for f in BD.leer("crm_cuentas", select="id,nombre,tipo,etiquetas,web,dominio", nombre="ilike." + nombre.replace("*", ""), archivada_at="is.null", limit="5")
                 if not dom or not f.get("dominio") or f.get("dominio") == dom]
    etq = "organizador-eventos"
    if filas:
        f = filas[0]
        cambios = {}
        if etq not in (f.get("etiquetas") or []):
            cambios["etiquetas"] = list(f.get("etiquetas") or []) + [etq]
        if web and not f.get("web"):
            cambios["web"] = web[:300]
        if cambios:
            BD.actualizar("crm_cuentas", {"id": "eq." + f["id"]}, cambios)
        return f["id"], False
    fila = BD.insertar("crm_cuentas", {"producto": "moticias", "tipo": TIPO_CUENTA.get(tipo_ent or "", "otro"), "nombre": nombre[:200], "web": (web or "")[:300] or None,
                                       "dominio": (dom if not compartido(dom) else None) or None, "origen": "agenda", "etiquetas": [etq], "creada_por": quien})[0]
    BD.insertar("crm_estados", {"cuenta_id": fila["id"], "estado": "sin_contacto", "quien": quien, "motivo": "organiza un evento de la agenda"})
    return fila["id"], True


def _contacto(cuenta_id, canal, valor, nivel, fuente_url, fuente_fecha, persona_id=None, quien="agenda", notas=None):
    if not valor:
        return None
    ya = BD.leer("crm_contactos", select="id", cuenta_id="eq." + cuenta_id, canal="eq." + canal, valor="ilike." + valor.replace("*", ""), archivado_at="is.null", limit="1")
    if ya:
        return ya[0]["id"]
    return BD.insertar("crm_contactos", {"cuenta_id": cuenta_id, "persona_id": persona_id, "canal": canal, "valor": valor[:300], "nivel": nivel,
                                         "fuente_url": fuente_url, "fuente_fecha": fuente_fecha, "notas": notas, "creado_por": quien})[0]["id"]


def _no_contactar(cuenta_id):
    try:
        est = BD.leer("crm_cuentas_hoy", select="estado", id="eq." + cuenta_id, limit="1")
        return bool(est) and est[0].get("estado") == "no_contactar"
    except BD.ErrorBD:
        return False


def crm_al_publicar(e, quien="editor jefe", envio=None, v=None):
    """Publicar un evento: cuenta por organizador (sin duplicar), responsable si lo hay (solo desde el formulario o la
    base; nunca del repositorio), contactos con nivel y fuente, actividad `evento_agenda` y paso a 14 días antes."""
    v = v or EV.vertical()
    c = EV.cfg(v)
    out = []
    for i, nombre in enumerate(e["organizadores"]):
        web = None
        if envio and i == 0:
            web = envio["entidad"].get("web")
        elif i == 0 and e.get("url_oficial"):
            web = e["url_oficial"]
        cid, nueva = _cuenta(nombre, web, (envio or {}).get("entidad", {}).get("tipo"), quien)
        persona_id = None
        if envio and i == 0:
            persona_id = _persona_de_envio(cid, envio, quien)
            _contacto(cid, "correo", envio["correo"], "directo", "https://www.moticias.com/agenda/subir-mi-evento/", envio["creado_at"][:10], persona_id, quien,
                      "dado por la propia persona en el formulario")
            if envio.get("telefono"):
                _contacto(cid, "telefono", envio["telefono"], "directo", "https://www.moticias.com/agenda/subir-mi-evento/", envio["creado_at"][:10], persona_id, quien)
        if web:
            _contacto(cid, "web", web, "general", web if "://" in web else "https://" + web, hoy(), None, quien)
        ya = BD.leer("agenda_organizadores", select="id,persona_id", evento_id="eq." + e["id"], cuenta_id="eq." + cid, limit="1")
        if ya:
            if persona_id and not ya[0].get("persona_id"):
                BD.actualizar("agenda_organizadores", {"id": "eq.%s" % ya[0]["id"]}, {"persona_id": persona_id})
        else:
            BD.insertar("agenda_organizadores", {"evento_id": e["id"], "cuenta_id": cid, "persona_id": persona_id, "creado_por": quien})
            BD.insertar("crm_actividades", {"cuenta_id": cid, "persona_id": persona_id, "tipo": "evento_agenda", "quien": quien,
                                            "notas": ("Evento en la agenda: %s (%s, %s). https://www.moticias.com/agenda/%s/" % (e["titulo"], e.get("inicio"), e["ciudad"], e["id"]))[:2000]})
            if e.get("inicio") and not _no_contactar(cid):
                f = (datetime.date.fromisoformat(e["inicio"]) - datetime.timedelta(days=c["paso_dias_antes"]))
                f = max(f, datetime.date.today()).isoformat()
                BD.insertar("crm_pasos", {"cuenta_id": cid, "persona_id": persona_id, "que": "%s · %s" % (c["paso_texto"], e["titulo_corto"])[:300],
                                          "fecha": f, "responsable": "editor jefe", "creado_por": quien})
        out.append({"cuenta_id": cid, "nueva": nueva, "persona_id": persona_id})
    return out


def _persona_de_envio(cuenta_id, env, quien):
    r = BD.leer("crm_personas", select="id,no_contactar_at,permiso_correo_at", correo="eq." + env["correo"], limit="1")
    permiso = env.get("permiso_comercial_at") or env.get("permiso_boletin_at")
    como = None
    if permiso:
        marc = [k for k, x in (env.get("permisos_texto") or {}).items() if x.get("marcado") and k != "tratamiento"]
        como = ("Formulario «Subir mi evento» (%s): %s" % (env["creado_at"][:10], " | ".join(env["permisos_texto"][k]["texto"] for k in marc)))[:200]
    if r:
        if permiso and not r[0].get("permiso_correo_at") and not r[0].get("no_contactar_at"):
            BD.actualizar("crm_personas", {"id": "eq." + r[0]["id"]}, {"permiso_correo_at": permiso, "permiso_correo_como": como})
        return r[0]["id"]
    fila = {"cuenta_id": cuenta_id, "nombre": env["nombre"], "cargo": env.get("cargo"), "perfil": "organizador", "correo": env["correo"],
            "telefono": env.get("telefono"), "verificado": False, "creada_por": quien}
    if permiso:
        fila.update(permiso_correo_at=permiso, permiso_correo_como=como)
    return BD.insertar("crm_personas", fila)[0]["id"]


# ---------- tabla «Organizadores y responsables» ----------
def estado_contacto(contactos, persona):
    utiles = [x for x in contactos if x["canal"] in ("correo", "telefono")]
    if not utiles:
        return "Falta contacto"
    if any(x["nivel"] == "directo" for x in utiles) and persona:
        return "Contacto directo"
    return "Contacto general" if persona else "Contacto general · falta responsable"


def organizadores(evs=None):
    evs = {e["id"]: e for e in (evs or [EV.limpio(x) for x in EV.cargar()])}
    filas = BD.leer("agenda_organizadores", select="evento_id,cuenta_id,persona_id,crm_cuentas(nombre,web),crm_personas(nombre,cargo)", limit="5000")
    ids = sorted({f["cuenta_id"] for f in filas})
    cont = {}
    for i in range(0, len(ids), 80):
        for x in BD.leer("crm_contactos", select="cuenta_id,canal,valor,nivel,fuente_url,fuente_fecha", cuenta_id="in.(%s)" % ",".join(ids[i:i + 80]), archivado_at="is.null", limit="5000"):
            cont.setdefault(x["cuenta_id"], []).append(x)
    out = []
    for f in filas:
        e = evs.get(f["evento_id"]) or {}
        cs = sorted(cont.get(f["cuenta_id"], []), key=lambda x: NIVEL_ORDEN.get(x["nivel"], 9))
        mejor = lambda canal: next(({"valor": x["valor"], "nivel": x["nivel"], "fuente": x["fuente_url"], "fecha": x["fuente_fecha"]} for x in cs if x["canal"] == canal), None)
        per = f.get("crm_personas") or None
        out.append({"evento_id": f["evento_id"], "evento": e.get("titulo") or f["evento_id"], "inicio": e.get("inicio"), "estado_evento": e.get("estado"),
                    "enlace": e.get("url_inscripcion") or e.get("url_oficial"), "cuenta_id": f["cuenta_id"], "entidad": (f.get("crm_cuentas") or {}).get("nombre"),
                    "web": (f.get("crm_cuentas") or {}).get("web") or (mejor("web") or {}).get("valor"),
                    "responsable": per and per.get("nombre"), "cargo": per and per.get("cargo"),
                    "correo": mejor("correo"), "telefono": mejor("telefono"), "estado": estado_contacto(cs, per and per.get("nombre"))})
    out.sort(key=lambda x: (x["inicio"] or "9999", x["evento"], x["entidad"] or ""))
    ents = {}
    for x in out:
        ents.setdefault(x["cuenta_id"], x)
    ev_con_resp = {x["evento_id"] for x in out if x["responsable"]}
    cont_n = {
        "eventos": len({x["evento_id"] for x in out}), "entidades": len(ents),
        "responsables": len({(x["cuenta_id"], x["responsable"]) for x in out if x["responsable"]}),
        "entidades_con_contacto": sum(1 for x in ents.values() if x["estado"] != "Falta contacto"),
        "eventos_sin_responsable": len({x["evento_id"] for x in out} - ev_con_resp),
        "entidades_sin_contacto": sum(1 for x in ents.values() if x["estado"] == "Falta contacto")}
    return {"filas": out, "contadores": cont_n}


# ---------- comprobador de enlaces de inscripción ----------
def comprobar_enlaces(origen="agente", azar=True, solo=None, tope_s=120, visitar=None):
    """Cada día laborable, cada enlace de inscripción de los eventos visibles una vez, a una hora al azar."""
    import seguimiento as S
    visitar = visitar or S.visitar
    evs = [EV.limpio(e) for e in EV.cargar()]
    objs = [e for e in EV.visibles(evs) if e.get("url_inscripcion") and (not solo or e["id"] == solo)]
    ya = set()
    if azar:
        try:
            ya = {f["evento_id"] for f in BD.leer("agenda_comprobaciones", select="evento_id", at="gte." + hoy() + "T00:00:00+01:00", limit="2000")}
        except BD.ErrorBD:
            pass
    hora = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).hour
    random.shuffle(objs)
    out, t0 = [], time.time()
    for e in objs:
        if azar and (e["id"] in ya or random.random() > (0.9 if hora >= 18 else 0.25)):
            continue
        if time.time() - t0 > tope_s:
            break
        ok, estado, final, ms, err = visitar(e["url_inscripcion"])
        fila = {"evento_id": e["id"], "url": e["url_inscripcion"][:600], "ok": ok, "estado_http": estado, "destino": (final or "")[:600] or None,
                "error": err, "ms": ms, "origen": origen}
        try:
            BD.insertar("agenda_comprobaciones", fila)
            if not ok:
                abierto = BD.leer("agenda_avisos", select="id", evento_id="eq." + e["id"], tipo="eq.enlace_caido", resuelto_at="is.null", limit="1")
                if not abierto:
                    BD.insertar("agenda_avisos", {"evento_id": e["id"], "tipo": "enlace_caido", "origen": "comprobador",
                                                  "detalle": ("El enlace de inscripción no responde: %s" % (err or estado))[:1000], "fuente_url": e["url_inscripcion"]})
        except BD.ErrorBD:
            pass
        out.append(fila)
        if azar:
            time.sleep(random.uniform(0.5, 3))
    return out


def enlaces_caidos():
    try:
        filas = BD.leer("agenda_comprobaciones", select="evento_id,ok,at,error,estado_http", order="at.desc", limit="2000")
    except BD.ErrorBD:
        return []
    ultimo = {}
    for f in filas:
        ultimo.setdefault(f["evento_id"], f)
    return [dict(f) for f in ultimo.values() if not f["ok"]]


# ---------- bloque «Agenda» del panel (pantalla «Inicio» del gestor) ----------
def panel(evs=None):
    evs = evs or [EV.limpio(x) for x in EV.cargar()]
    h = hoy()
    en14 = (datetime.date.today() + datetime.timedelta(days=14)).isoformat()
    vis = EV.visibles(evs)
    prox = [e for e in vis if e["inicio"] <= en14]
    propuestos = [e for e in evs if e.get("estado") == "propuesto"]
    out = {"proximos_14": [{"id": e["id"], "titulo": e["titulo_corto"], "inicio": e["inicio"], "ciudad": e["ciudad"]} for e in prox],
           "propuestos": len(propuestos), "envios": 0, "sin_responsable": None, "sin_contacto": None, "caidos": [], "cambios": [], "ultimo_barrido": None,
           "comprobado": max([e.get("comprobado_at") or "" for e in vis] or [""])}
    if not BD.configurada():
        return out
    try:
        out["envios"] = len(BD.leer("agenda_envios", select="id", estado="in.(recibido,en_revision,datos_pedidos)", limit="500"))
        org = organizadores(evs)
        visibles = {e["id"] for e in vis}
        out["sin_responsable"] = len({x["evento_id"] for x in org["filas"] if x["evento_id"] in visibles} - {x["evento_id"] for x in org["filas"] if x["responsable"]})
        out["sin_contacto"] = org["contadores"]["entidades_sin_contacto"]
        out["caidos"] = [x for x in enlaces_caidos() if x["evento_id"] in visibles]
        out["cambios"] = BD.leer("agenda_avisos", select="id,evento_id,tipo,detalle,creado_at", resuelto_at="is.null", tipo="neq.enlace_caido", order="creado_at.desc", limit="50")
        b = BD.leer("agenda_barridos", select="at,ok,resumen,resultado", order="at.desc", limit="1")
        out["ultimo_barrido"] = b[0] if b else None
    except BD.ErrorBD as e:
        out["error"] = str(e)
    return out


# ---------- acciones del gestor (pestaña «Agenda») ----------
EDITABLES = ("titulo", "titulo_corto", "inicio", "fin", "mes_previsto", "tema", "formato", "modalidad", "publico", "ciudad", "sede", "territorio", "geo",
             "resumen", "organizadores", "url_inscripcion", "url_oficial", "precio", "nota", "fuentes")
VISIBLES = ("publicado", "aplazado", "cancelado")
SOLO_JEFE = ("publicar", "retirar", "restaurar")


def ruta(eid):
    return "data/eventos/%s.json" % eid


def estado_de_cola(evs=None):
    """Lo que ve la pestaña: cola (envíos sin convertir + eventos `propuesto`), publicados, por confirmar y retirados."""
    evs = evs or [EV.limpio(x) for x in EV.cargar()]
    envios = []
    if BD.configurada():
        try:
            envios = BD.leer("agenda_envios", select="id,creado_at,estado,evento,entidad,evento_id,cargo,permiso_boletin_at,permiso_comercial_at",
                             estado="in.(recibido,en_revision,datos_pedidos)", order="creado_at.desc", limit="200")
        except BD.ErrorBD:
            envios = []
    for x in envios:
        x["duplicados"] = duplicados({"titulo": x["evento"].get("titulo"), "inicio": x["evento"].get("inicio"), "ciudad": x["evento"].get("ciudad")}, evs)
    caidos = {x["evento_id"]: x for x in enlaces_caidos()} if BD.configurada() else {}
    prop = [dict(e, duplicados=duplicados(e, evs), errores=EV.validar(e)) for e in evs if e.get("estado") == "propuesto"]
    pub = [dict(e, caido=caidos.get(e["id"])) for e in sorted([e for e in evs if e.get("estado") in VISIBLES], key=lambda e: e.get("inicio") or "")]
    return {"envios": envios, "propuestos": prop, "publicados": pub,
            "por_confirmar": EV.por_confirmar(evs), "retirados": [e for e in evs if e.get("estado") == "retirado"],
            "pasados": len([e for e in evs if e.get("estado") == "pasado"])}


def _revision(e, que, quien, de=None):
    e["revisiones"] = list(e.get("revisiones") or []) + [dict({"fecha": hoy(), "que": que, "quien": quien}, **({"de": de} if de else {}))]
    e["revised_at"] = hoy()


def accion(ses, d, io, v=None):
    """`io`: {"leer": f(ruta) -> (obj, sha), "escribir": f(ruta, obj, sha, mensaje) -> (ok, det), "republicar": f(lista) -> dict,
    "correo": f(para, asunto, html) -> bool}. Devuelve (estado HTTP, cuerpo). Varias a la vez con `ids`."""
    v = v or EV.vertical()
    per, quien = ses["permisos"], ses.get("nombre") or ses.get("perfil") or "gestor"
    jefe = "piezas" in per
    acc = d.get("accion")
    if acc in SOLO_JEFE and not jefe:
        return 403, {"error": "solo el editor jefe publica, retira o restaura eventos; tú puedes proponerlos"}
    if not jefe and "proponer" not in per:
        return 403, {"error": "tu perfil no toca la agenda"}
    if acc == "alta":
        return _alta(d, io, v, quien, jefe)
    if acc in ("convertir", "pedir_datos", "descartar_envio"):
        return _envio(acc, d, io, v, quien)
    if acc == "resolver_aviso":
        BD.actualizar("agenda_avisos", {"id": "eq.%s" % int(d.get("aviso"))}, {"resuelto_at": ahora(), "resuelto_por": quien})
        return 200, {"ok": True}
    if acc == "comprobar_enlace":
        return 200, {"resultados": comprobar_enlaces(origen="manual", azar=False, solo=d.get("id"))}
    ids = d.get("ids") or ([d["id"]] if d.get("id") else [])
    if not ids:
        return 400, {"error": "¿qué evento?"}
    hechos, errores, cambiados = [], [], []
    for eid in ids[:40]:
        if not re.fullmatch(r"[0-9a-z-]{8,120}", str(eid)):
            errores.append({"id": eid, "error": "id no válido"}); continue
        e, sha = io["leer"](ruta(eid))
        if not e:
            errores.append({"id": eid, "error": "no existe"}); continue
        antes = e.get("estado")
        if antes in VISIBLES and not jefe:
            errores.append({"id": eid, "error": "este evento ya está en la web: lo cambia el editor jefe"}); continue
        if acc == "editar":
            for k in EDITABLES:
                if k in (d.get("campos") or {}):
                    e[k] = d["campos"][k]
            _revision(e, "editado en el gestor", quien)
        elif acc == "publicar":
            e["estado"] = "publicado"
            e["comprobado_at"] = hoy()
            _revision(e, "publicado (comprobado por el editor jefe)", quien, antes)
        elif acc == "retirar":
            e["estado"] = "retirado"
            _revision(e, "retirado: %s" % (d.get("motivo") or "sin motivo"), quien, antes)
        elif acc == "restaurar":
            prev = next((r.get("de") for r in reversed(e.get("revisiones") or []) if r.get("de") and r.get("de") != "retirado"), "propuesto")
            e["estado"] = prev
            _revision(e, "restaurado", quien, antes)
        elif acc in ("fecha_por_confirmar", "aplazado", "cancelado"):
            e["estado"] = acc
            if acc == "fecha_por_confirmar" and e.get("inicio"):
                e["mes_previsto"] = e["inicio"][:7]
            _revision(e, "marcado %s" % acc.replace("_", " "), quien, antes)
        else:
            return 400, {"error": "acción desconocida"}
        err = EV.validar(e, v, eid) if e["estado"] != "retirado" else [x for x in EV.validar(e, v, eid) if "estado" in x]
        if err:
            errores.append({"id": eid, "error": "; ".join(err)}); continue
        ok, det = io["escribir"](ruta(eid), e, sha, "Agenda: %s %s" % (acc, eid))
        if not ok:
            errores.append({"id": eid, "error": det}); continue
        cambiados.append(e)
        crm = None
        if acc == "publicar" and BD.configurada():
            try:
                env = BD.leer("agenda_envios", select="*", evento_id="eq." + eid, limit="1")
                crm = crm_al_publicar(e, quien, env[0] if env else None, v)
                if env:
                    BD.actualizar("agenda_envios", {"id": "eq." + env[0]["id"]}, {"estado": "convertido", "actualizado_at": ahora(),
                                  "historial": env[0]["historial"] + [{"cuando": ahora(), "quien": quien, "que": "publicado"}]})
                    if io.get("correo"):
                        io["correo"]([env[0]["correo"]], "Tu evento ya está en la agenda de MOTICIAS",
                                     "<p>Hola:</p><p>«%s» ya está publicado en la agenda de MOTICIAS: <a href=\"https://www.moticias.com/agenda/%s/\">ver la ficha</a>.</p>"
                                     "<p>Si cambia algo (fecha, sede, enlace), responde a este correo.</p><p>MOTICIAS · Agenda</p>" % (E(e["titulo"]), E(eid)))
            except BD.ErrorBD as x:
                crm = {"error": str(x)}
        hechos.append({"id": eid, "estado": e["estado"], "commit": det, "crm": crm})
        BD.registrar(quien, "agenda_" + acc, eid)
    web = io["republicar"](cambiados) if cambiados and io.get("republicar") else None
    return (200 if hechos else 400), {"ok": not errores, "hechos": hechos, "errores": errores, "web": web}


def _alta(d, io, v, quien, jefe):
    e = {k: d["campos"][k] for k in EDITABLES if k in (d.get("campos") or {})}
    e.setdefault("modalidad", "presencial")
    e.setdefault("publico", "profesional")
    e["origen"] = "redaccion"
    e["estado"] = "publicado" if (jefe and d.get("publicar")) else "propuesto"
    if e["estado"] == "publicado":
        e["comprobado_at"] = hoy()
    if isinstance(e.get("organizadores"), str):
        e["organizadores"] = [x.strip() for x in re.split(r"\s*;\s*|\s+y\s+", e["organizadores"]) if x.strip()]
    e["id"] = "%s-%s" % (e.get("inicio") or e.get("mes_previsto") or "", EV.slug(e.get("titulo_corto") or e.get("titulo")))
    _revision(e, "alta en el gestor", quien)
    err = EV.validar(e, v)
    if err:
        return 400, {"error": "No se da de alta: " + "; ".join(err)}
    ya, _ = io["leer"](ruta(e["id"]))
    if ya:
        return 409, {"error": "ya existe %s: edítalo en vez de duplicarlo" % e["id"]}
    evs = [EV.limpio(x) for x in EV.cargar()]
    ok, det = io["escribir"](ruta(e["id"]), e, None, "Agenda: alta %s" % e["id"])
    if not ok:
        return 502, {"error": det}
    crm = crm_al_publicar(e, quien, None, v) if e["estado"] == "publicado" and BD.configurada() else None
    web = io["republicar"]([e]) if e["estado"] == "publicado" and io.get("republicar") else None
    return 200, {"ok": True, "id": e["id"], "estado": e["estado"], "commit": det, "duplicados": duplicados(e, evs), "crm": crm, "web": web}


def _envio(acc, d, io, v, quien):
    if not BD.configurada():
        return 503, {"error": "la base privada no está conectada"}
    r = BD.leer("agenda_envios", select="*", id="eq.%s" % str(d.get("envio") or "")[:40], limit="1")
    if not r:
        return 404, {"error": "envío no encontrado"}
    env = r[0]
    hist = env["historial"]
    if acc == "descartar_envio":
        BD.actualizar("agenda_envios", {"id": "eq." + env["id"]}, {"estado": "descartado", "actualizado_at": ahora(),
                      "historial": hist + [{"cuando": ahora(), "quien": quien, "que": "descartado: %s" % (d.get("motivo") or "")[:200]}]})
        return 200, {"ok": True}
    if acc == "pedir_datos":
        msg = str(d.get("mensaje") or "").strip()[:2000]
        if len(msg) < 10:
            return 400, {"error": "escribe qué datos faltan"}
        ok = io.get("correo") and io["correo"]([env["correo"]], "Tu evento en la agenda de MOTICIAS: nos falta un dato",
                                               "<p>Hola:</p><p>Sobre «%s»:</p><p>%s</p><p>Responde a este correo y lo completamos.</p><p>MOTICIAS · Agenda</p>" % (
                                                   E(env["evento"].get("titulo")), E(msg).replace("\n", "<br>")))
        BD.actualizar("agenda_envios", {"id": "eq." + env["id"]}, {"estado": "datos_pedidos", "actualizado_at": ahora(),
                      "historial": hist + [{"cuando": ahora(), "quien": quien, "que": "datos pedidos"}]})
        return 200, {"ok": True, "correo": bool(ok)}
    e = evento_de_envio(env, v)
    for k in EDITABLES:  # la redacción puede corregir al convertir (geo de la ciudad, sede, fuentes…)
        if k in (d.get("campos") or {}):
            e[k] = d["campos"][k]
    e["id"] = "%s-%s" % (e["inicio"], EV.slug(e["titulo_corto"]))
    geo = _geo_ciudad(e["ciudad"], v)
    if geo and "geo" not in (d.get("campos") or {}):
        e["geo"] = geo
    err = EV.validar(e, v)
    if err:
        return 400, {"error": "; ".join(err), "borrador": e}
    ya, _ = io["leer"](ruta(e["id"]))
    if ya:
        return 409, {"error": "ya existe %s" % e["id"], "duplicado": e["id"]}
    ok, det = io["escribir"](ruta(e["id"]), e, None, "Agenda: propuesto por un organizador (%s)" % e["id"])
    if not ok:
        return 502, {"error": det}
    BD.actualizar("agenda_envios", {"id": "eq." + env["id"]}, {"estado": "en_revision", "evento_id": e["id"], "actualizado_at": ahora(),
                  "historial": hist + [{"cuando": ahora(), "quien": quien, "que": "pasado a la cola como %s" % e["id"]}]})
    return 200, {"ok": True, "id": e["id"], "commit": det}


def _geo_ciudad(ciudad, v):
    c = EV.cfg(v).get("ciudades") or {}
    return c.get(EV.slug(ciudad))
