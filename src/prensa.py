"""MOTICIAS · Prensa: base de medios y periodistas, envíos (notas de prensa, noticias, comunicados, invitaciones,
mensajes del editor o de la redacción), coberturas y suscriptores de MOTICIAS entre los periodistas.

Decisión de Rainer (9-11-2026): «Lo importante es tener una base de datos de destinatarios muy buena, que reacciona y
actualizada.» Cambio OpenSpec `prensa-y-medios`; esquema en `supabase/migrations/005_prensa_medios.sql`.

Solo biblioteca estándar. Lo usan el gestor (`api/gestor.py`, pestaña «Prensa») y la tarea de los miércoles
(`/medios-actualizar`, que escribe con el conector de Supabase a partir de `python3 src/prensa.py sql FICHERO.json`).
Nada de lo que maneja este módulo va al repositorio, que es público: los datos viven en la base privada.

Variables de entorno (Vercel): las de `src/bd.py`; BREVO_API_KEY para enviar; PRENSA_REMITENTE («Nombre <correo>»,
por defecto «MOTICIAS · Redacción <redaccion@moticias.com>»); PRENSA_RESPONDER_A (opcional); GHOST_URL y GHOST_ADMIN_KEY
para detectar suscriptores.
"""
import datetime, hashlib, hmac, html, json, os, re, sys, urllib.error, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bd as BD  # noqa: E402

TIPOS_MEDIO = {
    "generalista": "Generalista", "economico": "Económico", "b2b_sector": "B2B del sector", "b2b_otro_sector": "B2B de otro sector",
    "b2g": "B2G (administraciones)", "agencia": "Agencia", "newsletter": "Newsletter", "boletin_asociacion": "Boletín de asociación",
    "radio_tv": "Radio y televisión", "regional": "Regional o local", "turismo": "Turismo", "tecnologia": "Tecnología e innovación",
    "institucional": "Institucional", "otro": "Otro"}
AMBITOS = ["movilidad", "viajeros", "autobus", "ferrocarril", "aereo", "maritimo", "logistica", "turismo", "economia",
           "administracion", "sostenibilidad", "tecnologia", "infraestructuras", "rrhh"]
ROLES = {"director": "Director/a", "redactor_jefe": "Redactor/a jefe", "jefe_seccion": "Jefe/a de sección", "redactor": "Redactor/a",
         "colaborador": "Colaborador/a", "freelance": "Freelance", "corresponsal": "Corresponsal", "editor_newsletter": "Editor/a de newsletter",
         "comunicacion": "Comunicación", "otro": "Otro"}
TIPOS_ENVIO = {"nota_de_prensa": "Nota de prensa (novedades)", "noticia": "Noticia (contenido editorial)", "comunicado": "Comunicado",
               "invitacion_suscripcion": "Invitación a suscribirse", "mensaje_editor": "Mensaje del editor", "mensaje_redaccion": "Mensaje de la redacción"}
COLABORACION = {"colaborador": "Colaborador", "neutral": "En observación", "poco_colaborador": "Poco colaborador"}
REDES = ["x", "linkedin", "bluesky", "instagram", "facebook", "youtube", "tiktok", "threads", "telegram", "mastodon", "whatsapp", "rss"]
GENERICOS = {"gmail.com", "hotmail.com", "outlook.com", "yahoo.es", "yahoo.com", "icloud.com", "live.com", "msn.com", "proton.me",
             "protonmail.com", "hotmail.es", "telefonica.net", "me.com", "gmx.de", "gmx.net", "web.de"}
DIAS_ENTRE_INVITACIONES = 90
SUSCRIBIRSE = "https://www.moticias.com/#/portal/signup"

CAMPOS_MEDIO = {"tipo_medio", "formatos", "alcance", "ambitos", "periodicidad", "grupo", "correo_redaccion", "correo_notas",
                "telefono_corporativo", "direccion", "cp", "ciudad", "region", "pais", "redes", "audiencia", "referencias",
                "comentario_ia", "importancia", "colaboracion", "prob_previa", "prob_publicacion", "acepta_notas", "fuentes",
                "verificado_at", "revisar_at"}
CAMPOS_PERIODISTA = {"rol", "temas", "telefono_corporativo", "otros_medios", "articulo_url", "articulo_titulo", "articulo_fecha",
                     "redes", "comentario_ia", "importancia", "colaboracion", "prob_publicacion", "fuentes", "verificado_at"}
CAMPOS_PERSONA = {"nombre", "cargo", "correo", "telefono", "linkedin"}


def hoy():
    return datetime.date.today().isoformat()


def ahora():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _url_ok(u):
    return isinstance(u, str) and re.match(r"^https?://[^\s<>\"]+$", u) and len(u) <= 400


def limpiar_redes(redes):
    out = []
    for r in redes or []:
        if isinstance(r, dict) and _url_ok(r.get("url")):
            red = str(r.get("red") or "").lower()
            out.append({k: v for k, v in {"red": red if red in REDES else "otra", "url": r["url"], "usuario": (r.get("usuario") or "")[:80] or None,
                                           "seguidores": r.get("seguidores") if isinstance(r.get("seguidores"), int) else None,
                                           "ultimo": (r.get("ultimo") or "")[:280] or None, "at": r.get("at")}.items() if v is not None})
    return out


def seguir_url(red):
    """Enlace para «Seguir»: X tiene intent de seguir; el resto abre el perfil (seguir requiere su propia sesión)."""
    u, usuario = red.get("url", ""), (red.get("usuario") or "").lstrip("@")
    if red.get("red") == "x" and usuario:
        return "https://x.com/intent/follow?screen_name=" + urllib.parse.quote(usuario)
    return u


# ---------- lectura ----------
def medios(q):
    p = {"select": "*", "archivada_at": "is.null", "order": "importancia.desc.nullslast,nombre.asc", "limit": str(min(int(q.get("limit") or 400), 1000))}
    if q.get("tipo") in TIPOS_MEDIO:
        p["tipo_medio"] = "eq." + q["tipo"]
    if q.get("ambito") in AMBITOS:
        p["ambitos"] = "cs.{%s}" % q["ambito"]
    if q.get("colab") in COLABORACION:
        p["colaboracion"] = "eq." + q["colab"]
    elif q.get("colab") == "sin":
        p["colaboracion"] = "is.null"
    if q.get("imp"):
        p["importancia"] = "gte.%d" % int(q["imp"])
    if q.get("suscriptores") == "1":
        p["suscriptores"] = "gt.0"
    if q.get("q"):
        t = re.sub(r"[^\wáéíóúñü .-]", "", q["q"], flags=re.I)[:60]
        p["or"] = "(nombre.ilike.*%s*,dominio.ilike.*%s*,ciudad.ilike.*%s*)" % (t, t, t)
    return BD.leer("medios_hoy", **p)


def resumen():
    filas = BD.leer("medios_hoy", select="tipo_medio,colaboracion,importancia,personas,suscriptores,coberturas", archivada_at="is.null", limit="5000")
    per = BD.leer("periodistas_hoy", select="id,correo,suscriptor_moticias,no_contactar_at", archivada_at="is.null", limit="10000")
    tipos = {}
    for f in filas:
        tipos[f["tipo_medio"]] = tipos.get(f["tipo_medio"], 0) + 1
    return {"medios": len(filas), "periodistas": len(per), "con_correo": sum(1 for x in per if x.get("correo") and not x.get("no_contactar_at")),
            "suscriptores": sum(1 for x in per if x.get("suscriptor_moticias")),
            "colaboradores": sum(1 for f in filas if f.get("colaboracion") == "colaborador"),
            "coberturas": sum(f.get("coberturas") or 0 for f in filas), "tipos": tipos,
            "envios": BD.leer("prensa_envios", select="id,tipo,asunto,estado,creado_at,enviado_at,creado_por", order="id.desc", limit="15"),
            "cfg": {"tipos": TIPOS_MEDIO, "ambitos": AMBITOS, "roles": ROLES, "envios": TIPOS_ENVIO, "colaboracion": COLABORACION}}


def ficha(cid):
    m = BD.leer("medios_hoy", select="*", id="eq." + cid)
    if not m:
        return None
    m = m[0]
    for r in m.get("redes") or []:
        r["seguir"] = seguir_url(r)
    pers = BD.leer("periodistas_hoy", select="*", cuenta_id="eq." + cid, archivada_at="is.null", order="importancia.desc.nullslast,nombre.asc")
    for p in pers:
        for r in p.get("redes") or []:
            r["seguir"] = seguir_url(r)
    return {"medio": m, "periodistas": pers,
            "coberturas": BD.leer("prensa_coberturas", select="*", cuenta_id="eq." + cid, order="fecha.desc.nullslast", limit="50"),
            "recibidos": BD.leer("prensa_destinatarios", select="id,envio_id,correo,estado,at,prensa_envios(tipo,asunto,enviado_at)",
                                 cuenta_id="eq." + cid, order="id.desc", limit="40")}


# ---------- escritura ----------
def _filtra(d, campos):
    out = {k: d[k] for k in campos if k in d}
    for k in ("redes",):
        if k in out:
            out[k] = limpiar_redes(out[k])
    for k in ("importancia",):
        if k in out and out[k] not in (None, ""):
            out[k] = max(1, min(5, int(out[k])))
        elif k in out:
            out[k] = None
    for k in ("prob_previa", "prob_publicacion"):
        if k in out and out[k] not in (None, ""):
            v = float(out[k])
            out[k] = round(max(0.0, min(1.0, v / 100 if v > 1 else v)), 2)
        elif k in out:
            out[k] = None
    for k, v in list(out.items()):
        if v == "":
            out[k] = None
    return out


def guardar_medio(quien, cid, d):
    cambios = _filtra(d, CAMPOS_MEDIO)
    # Lo que una persona fija a mano deja de recalcularse (y vuelve al cálculo si lo deja vacío).
    if "colaboracion" in cambios:
        cambios["colaboracion_manual"] = cambios["colaboracion"] is not None
    if "importancia" in cambios and d.get("manual", True):
        cambios["importancia_manual"] = cambios["importancia"] is not None
    if "prob_publicacion" in cambios:
        cambios["prob_manual"] = cambios["prob_publicacion"] is not None
    cambios["actualizado"] = ahora()
    BD.actualizar("medios", {"cuenta_id": "eq." + cid}, cambios)
    cuenta = {k: d[k] for k in ("nombre", "web", "notas", "sector") if k in d}
    if cuenta:
        BD.actualizar("crm_cuentas", {"id": "eq." + cid}, cuenta)
    BD.registrar(quien, "prensa_medio", cid, {"campos": sorted(cambios)})


def nuevo_medio(quien, d):
    nombre = (d.get("nombre") or "").strip()
    if len(nombre) < 2:
        raise ValueError("falta el nombre del medio")
    web = (d.get("web") or "").strip() or None
    dom = dominio(web)
    if dom and BD.leer("crm_cuentas", select="id", tipo="eq.medio", dominio="eq." + dom, archivada_at="is.null"):
        raise ValueError("ese medio ya está en la base (%s)" % dom)
    c = BD.insertar("crm_cuentas", {"tipo": "medio", "nombre": nombre[:200], "web": web, "dominio": dom, "sector": d.get("sector"),
                                     "origen": "gestor", "creada_por": quien})[0]
    BD.insertar("crm_estados", {"cuenta_id": c["id"], "estado": "sin_contacto", "quien": quien, "motivo": "alta"})
    BD.insertar("medios", dict(_filtra(d, CAMPOS_MEDIO), cuenta_id=c["id"]))
    BD.registrar(quien, "prensa_medio_nuevo", c["id"])
    return c["id"]


def guardar_periodista(quien, d):
    pid, cid = d.get("persona_id"), d.get("cuenta_id")
    pe = {k: (d[k] or None) for k in CAMPOS_PERSONA if k in d}
    if pe.get("correo"):
        pe["correo"] = pe["correo"].strip().lower()
    pp = _filtra(d, CAMPOS_PERIODISTA)
    if "colaboracion" in pp:
        pp["colaboracion_manual"] = pp["colaboracion"] is not None
    if "importancia" in pp:
        pp["importancia_manual"] = pp["importancia"] is not None
    if "prob_publicacion" in pp:
        pp["prob_manual"] = pp["prob_publicacion"] is not None
    if pid:
        if pe:
            BD.actualizar("crm_personas", {"id": "eq." + pid}, pe)
        if d.get("no_contactar"):
            BD.actualizar("crm_personas", {"id": "eq." + pid}, {"no_contactar_at": ahora(), "no_contactar_motivo": (d.get("motivo") or "pedido en el gestor")[:300]})
        pp["actualizado"] = ahora()
        BD.upsert("periodistas", [dict(pp, persona_id=pid)], "persona_id")
    else:
        if not cid or not (pe.get("nombre") or pe.get("correo")):
            raise ValueError("faltan el medio y el nombre o el correo")
        x = BD.insertar("crm_personas", dict(pe, cuenta_id=cid, perfil="periodista", creada_por=quien))[0]
        pid = x["id"]
        BD.insertar("periodistas", dict(pp, persona_id=pid))
    BD.registrar(quien, "prensa_periodista", pid)
    return pid


def cobertura(quien, d):
    if not _url_ok(d.get("url")) or not d.get("cuenta_id"):
        raise ValueError("falta el enlace o el medio")
    fila = {"cuenta_id": d["cuenta_id"], "persona_id": d.get("persona_id") or None, "envio_id": d.get("envio_id") or None,
            "url": d["url"], "titulo": (d.get("titulo") or "")[:300] or None, "fecha": d.get("fecha") or None,
            "alcance": d.get("alcance") if d.get("alcance") in ("integra", "parcial", "mencion", "cita") else None, "detectada": "manual"}
    BD.insertar("prensa_coberturas", fila)
    BD.insertar("crm_actividades", {"cuenta_id": d["cuenta_id"], "persona_id": fila["persona_id"], "tipo": "nota",
                                    "notas": ("Cobertura publicada: %s" % d["url"])[:2000], "quien": quien})
    recalcular()


def respuesta(quien, d):
    """Marca que un destinatario contestó (o una actividad entrante): cuenta como contacto y como respuesta."""
    did = int(d.get("destinatario_id") or 0)
    if did:
        BD.actualizar("prensa_destinatarios", {"id": "eq.%d" % did}, {"estado": "respondido", "at": ahora()})
    if d.get("cuenta_id"):
        BD.insertar("crm_actividades", {"cuenta_id": d["cuenta_id"], "persona_id": d.get("persona_id") or None,
                                        "tipo": "correo_entrante", "notas": (d.get("notas") or "Respuesta a un envío")[:2000], "quien": quien})
    recalcular()


def recalcular():
    try:
        return BD.peticion("POST", "rpc/prensa_recalcular_gestor", cuerpo={})
    except BD.ErrorBD as e:
        return {"error": str(e)}


def dominio(web):
    if not web:
        return None
    h = urllib.parse.urlparse(web if "://" in web else "https://" + web).hostname or ""
    h = h.lower()
    h = h[4:] if h.startswith("www.") else h
    return h if re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", h) else None


# ---------- envíos ----------
def destinatarios(filtro, tipo):
    """Lista de destinatarios según el filtro. Nunca: «No contactar», archivados, sin correo, ni duplicados."""
    q = {k: filtro.get(k) for k in ("tipo", "ambito", "colab", "imp", "q") if filtro.get(k)}
    lista_medios = medios(dict(q, limit=1000))
    tipos = set(filtro.get("tipos") or [])
    if tipos:
        lista_medios = [m for m in lista_medios if m["tipo_medio"] in tipos]
    ambs = set(filtro.get("ambitos") or [])
    if ambs:
        lista_medios = [m for m in lista_medios if ambs & set(m.get("ambitos") or [])]
    if filtro.get("excluir_poco_colaboradores"):
        lista_medios = [m for m in lista_medios if m.get("colaboracion") != "poco_colaborador"]
    ids = {m["id"]: m for m in lista_medios}
    out, vistos = [], set()
    if ids:
        pers = BD.leer("periodistas_hoy", select="id,cuenta_id,nombre,correo,suscriptor_moticias,no_contactar_at,archivada_at,colaboracion,importancia",
                       cuenta_id="in.(%s)" % ",".join(ids), limit="10000")
        recientes = set()
        if tipo == "invitacion_suscripcion":
            desde = (datetime.date.today() - datetime.timedelta(days=DIAS_ENTRE_INVITACIONES)).isoformat()
            for r in BD.leer("prensa_destinatarios", select="correo,prensa_envios!inner(tipo)", at="gte." + desde,
                             **{"prensa_envios.tipo": "eq.invitacion_suscripcion"}, limit="10000"):
                recientes.add(r["correo"].lower())
        for p in pers:
            c = (p.get("correo") or "").lower()
            if not c or p.get("no_contactar_at") or p.get("archivada_at") or c in vistos:
                continue
            if tipo == "invitacion_suscripcion" and (p.get("suscriptor_moticias") or c in recientes):
                continue
            if filtro.get("solo_colaboradores") and p.get("colaboracion") != "colaborador":
                continue
            vistos.add(c)
            out.append({"persona_id": p["id"], "cuenta_id": p["cuenta_id"], "correo": c, "nombre": p.get("nombre"), "medio": ids[p["cuenta_id"]]["nombre"]})
        if filtro.get("incluir_buzones") and tipo in ("nota_de_prensa", "noticia", "comunicado"):
            for m in lista_medios:
                c = (m.get("correo_notas") or m.get("correo_redaccion") or "").lower()
                if c and c not in vistos:
                    vistos.add(c)
                    out.append({"persona_id": None, "cuenta_id": m["id"], "correo": c, "nombre": None, "medio": m["nombre"]})
    return out


def crear_envio(quien, d):
    tipo = d.get("tipo")
    if tipo not in TIPOS_ENVIO:
        raise ValueError("tipo de envío no válido")
    asunto = (d.get("asunto") or "").strip()
    if len(asunto) < 3:
        raise ValueError("falta el asunto")
    filtro = d.get("filtro") or {}
    lista = destinatarios(filtro, tipo)
    if not lista:
        raise ValueError("con ese filtro no hay destinatarios con correo")
    e = BD.insertar("prensa_envios", {"tipo": tipo, "asunto": asunto[:200], "cuerpo": (d.get("cuerpo") or "")[:20000] or None,
                                      "pieza_url": d.get("pieza_url") if _url_ok(d.get("pieza_url")) else None,
                                      "por_cuenta_de": d.get("por_cuenta_de") or None, "filtro": filtro, "creado_por": quien})[0]
    for i in range(0, len(lista), 500):
        BD.insertar("prensa_destinatarios", [{"envio_id": e["id"], "persona_id": x["persona_id"], "cuenta_id": x["cuenta_id"], "correo": x["correo"]}
                                             for x in lista[i:i + 500]])
    BD.registrar(quien, "prensa_envio_borrador", str(e["id"]), {"tipo": tipo, "destinatarios": len(lista)})
    return e["id"], len(lista)


def envio(eid):
    e = BD.leer("prensa_envios", select="*", id="eq.%d" % int(eid))
    if not e:
        return None
    dest = BD.leer("prensa_destinatarios", select="id,correo,estado,at,persona_id,cuenta_id,crm_cuentas(nombre),crm_personas(nombre)",
                   envio_id="eq.%d" % int(eid), order="id.asc", limit="5000")
    est = {}
    for x in dest:
        est[x["estado"]] = est.get(x["estado"], 0) + 1
    return {"envio": e[0], "destinatarios": dest, "estados": est}


def _firma_baja(pid):
    k = (os.environ.get("MOTICIAS_BD_CLAVE") or os.environ.get("GESTOR_CLAVE_SUPERADMIN") or "").encode()
    return hmac.new(k, ("baja:" + pid).encode(), hashlib.sha256).hexdigest()[:32]


def enlace_baja(base, persona_id, correo):
    ref = persona_id or ("c:" + correo)
    return "%s/api/gestor?%s" % (base, urllib.parse.urlencode({"a": "prensa_baja", "p": ref, "f": _firma_baja(ref)}))


def baja(ref, firma):
    if not ref or not hmac.compare_digest(_firma_baja(ref), firma or ""):
        return False
    if ref.startswith("c:"):
        for x in BD.leer("crm_personas", select="id", correo="eq." + ref[2:].lower()):
            _poner_no_contactar(x["id"])
        BD.actualizar("prensa_destinatarios", {"correo": "eq." + ref[2:].lower()}, {"estado": "baja"})
        return True
    _poner_no_contactar(ref)
    BD.actualizar("prensa_destinatarios", {"persona_id": "eq." + ref}, {"estado": "baja"})
    return True


def _poner_no_contactar(pid):
    x = BD.leer("crm_personas", select="no_contactar_at", id="eq." + pid)
    if x and not x[0].get("no_contactar_at"):
        BD.actualizar("crm_personas", {"id": "eq." + pid}, {"no_contactar_at": ahora(), "no_contactar_motivo": "baja desde un envío de prensa"})


def _html(e, nombre, baja_url):
    cuerpo = html.escape(e.get("cuerpo") or "").replace("\n\n", "</p><p>").replace("\n", "<br>")
    cuerpo = re.sub(r"(https://[^\s<]+)", r'<a href="\1">\1</a>', cuerpo)
    saludo = ("Hola, %s:" % html.escape(nombre.split(" ")[0])) if nombre else "Hola:"
    extra = ""
    if e.get("pieza_url"):
        extra += '<p><a href="%s">Leer en MOTICIAS</a></p>' % html.escape(e["pieza_url"])
    if e["tipo"] == "invitacion_suscripcion":
        extra += '<p><a href="%s" style="display:inline-block;background:#111;color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none">Suscribirme gratis a MOTICIAS</a></p>' % SUSCRIBIRSE
    etiqueta = {"nota_de_prensa": "Nota de prensa", "comunicado": "Comunicado", "noticia": "MOTICIAS · Noticia"}.get(e["tipo"], "MOTICIAS")
    return ('<div style="font:16px/1.5 Georgia,serif;color:#141414;max-width:640px">'
            '<p style="font:12px Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#6b6f6c">%s</p>'
            '<p>%s</p><p>%s</p>%s'
            '<hr style="border:0;border-top:1px solid #e3e4e1;margin:24px 0">'
            '<p style="font:12px Arial,sans-serif;color:#6b6f6c">Recibe este correo como profesional de la información por su relación con el '
            'transporte y la movilidad. Responsable: Avionline S.L. (MOTICIAS). Si no quiere recibir más comunicaciones de MOTICIAS, '
            '<a href="%s">dese de baja aquí</a>: no volveremos a escribirle.</p></div>') % (etiqueta, saludo, cuerpo, extra, html.escape(baja_url))


def _brevo(metodo, ruta, cuerpo=None):
    k = os.environ.get("BREVO_API_KEY")
    if not k:
        raise BD.ErrorBD("falta BREVO_API_KEY en Vercel")
    req = urllib.request.Request("https://api.brevo.com/v3" + ruta, method=metodo, data=json.dumps(cuerpo).encode() if cuerpo is not None else None,
                                 headers={"api-key": k, "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise BD.ErrorBD("Brevo respondió %s: %s" % (e.code, (e.read() or b"")[:300].decode("utf-8", "replace")))


def _remitente():
    r = os.environ.get("PRENSA_REMITENTE") or "MOTICIAS · Redacción <redaccion@moticias.com>"
    m = re.match(r"\s*(.*?)\s*<([^>]+)>\s*$", r)
    return {"name": m.group(1), "email": m.group(2)} if m else {"email": r.strip()}


def enviar(quien, eid, base):
    """Aprueba y envía por Brevo (correo transaccional, uno por destinatario, con su enlace de baja). Solo el editor jefe."""
    datos = envio(eid)
    if not datos:
        raise ValueError("envío no encontrado")
    e = datos["envio"]
    if e["estado"] not in ("borrador", "aprobado"):
        raise ValueError("este envío ya está %s" % e["estado"])
    BD.actualizar("prensa_envios", {"id": "eq.%d" % e["id"]}, {"estado": "aprobado", "aprobado_por": quien, "aprobado_at": ahora()})
    nombres = {x["id"]: ((x.get("crm_personas") or {}).get("nombre")) for x in datos["destinatarios"]}
    # «No contactar» puede haberse puesto después del borrador: se vuelve a comprobar.
    bloqueados = {x["id"] for x in BD.leer("crm_personas", select="id", no_contactar_at="not.is.null", limit="10000")}
    pend = [x for x in datos["destinatarios"] if x["estado"] == "pendiente"]
    ok = err = 0
    remitente, tag = _remitente(), "prensa-%d" % e["id"]
    for x in pend:
        if x.get("persona_id") in bloqueados:
            BD.actualizar("prensa_destinatarios", {"id": "eq.%d" % x["id"]}, {"estado": "baja", "detalle": "No contactar"})
            continue
        cuerpo = {"sender": remitente, "to": [{"email": x["correo"]}], "subject": e["asunto"], "tags": [tag, "prensa", e["tipo"]],
                  "htmlContent": _html(e, nombres.get(x["id"]), enlace_baja(base, x.get("persona_id"), x["correo"])),
                  "headers": {"List-Unsubscribe": "<%s>" % enlace_baja(base, x.get("persona_id"), x["correo"])}}
        if os.environ.get("PRENSA_RESPONDER_A"):
            cuerpo["replyTo"] = {"email": os.environ["PRENSA_RESPONDER_A"]}
        try:
            r = _brevo("POST", "/smtp/email", cuerpo)
            BD.actualizar("prensa_destinatarios", {"id": "eq.%d" % x["id"]}, {"estado": "enviado", "at": ahora(), "detalle": (r.get("messageId") or "")[:300] or None})
            ok += 1
        except BD.ErrorBD as ex:
            BD.actualizar("prensa_destinatarios", {"id": "eq.%d" % x["id"]}, {"estado": "error", "detalle": str(ex)[:300]})
            err += 1
    BD.actualizar("prensa_envios", {"id": "eq.%d" % e["id"]}, {"estado": "enviado", "enviado_at": ahora(), "brevo_ref": tag})
    tipo_act = "nota_de_prensa" if e["tipo"] in ("nota_de_prensa", "comunicado", "noticia") else "correo_saliente"
    cuentas = sorted({x["cuenta_id"] for x in pend if x.get("cuenta_id")})
    for i in range(0, len(cuentas), 200):
        BD.insertar("crm_actividades", [{"cuenta_id": c, "tipo": tipo_act, "notas": ("Envío %d · %s · %s" % (e["id"], TIPOS_ENVIO[e["tipo"]], e["asunto"]))[:2000],
                                         "quien": quien} for c in cuentas[i:i + 200]])
    BD.registrar(quien, "prensa_envio_enviado", str(e["id"]), {"ok": ok, "error": err})
    recalcular()
    return {"enviados": ok, "errores": err}


def sincronizar(eid=None):
    """Trae de Brevo aperturas, clics, rebotes y bajas de los envíos de los últimos 30 días."""
    envs = BD.leer("prensa_envios", select="id,brevo_ref,enviado_at", estado="eq.enviado", order="id.desc", limit="30") if not eid else \
        BD.leer("prensa_envios", select="id,brevo_ref,enviado_at", id="eq.%d" % int(eid))
    orden = {"pendiente": 0, "error": 0, "enviado": 1, "abierto": 2, "clic": 3, "respondido": 4, "rebotado": 5, "baja": 6}
    mapa = {"opened": "abierto", "uniqueOpened": "abierto", "clicks": "clic", "hardBounces": "rebotado", "softBounces": "rebotado",
            "blocked": "rebotado", "invalid": "rebotado", "unsubscribed": "baja"}
    n = 0
    for e in envs:
        if not e.get("brevo_ref"):
            continue
        r = _brevo("GET", "/smtp/statistics/events?" + urllib.parse.urlencode({"tags": e["brevo_ref"], "limit": 2500, "days": 30}))
        actual = {x["correo"]: x for x in BD.leer("prensa_destinatarios", select="id,correo,estado,persona_id", envio_id="eq.%d" % e["id"], limit="5000")}
        for ev in r.get("events") or []:
            nuevo, x = mapa.get(ev.get("event")), actual.get((ev.get("email") or "").lower())
            if nuevo and x and orden.get(nuevo, 0) > orden.get(x["estado"], 0):
                BD.actualizar("prensa_destinatarios", {"id": "eq.%d" % x["id"]}, {"estado": nuevo, "at": ahora()})
                x["estado"] = nuevo
                n += 1
                if nuevo == "baja" and x.get("persona_id"):
                    _poner_no_contactar(x["persona_id"])
    recalcular()
    return {"cambios": n}


# ---------- suscriptores de MOTICIAS entre los periodistas ----------
def detectar_suscriptores(ghost_base, ghost_tok, ghost_api):
    """Cruza los miembros de Ghost con la base: por correo exacto y por dominio de un medio (los correos del dominio de
    un medio son de su redacción). Marca `suscriptor_moticias` y crea la ficha del periodista si no existía."""
    miembros, pagina = [], 1
    while True:
        st, r = ghost_api("GET", ghost_base + "/ghost/api/admin/members/?" + urllib.parse.urlencode({"limit": "100", "page": str(pagina), "fields": "id,email,name,status"}), ghost_tok)
        if st != 200:
            raise BD.ErrorBD("Ghost respondió %s" % st)
        miembros += r.get("members") or []
        pag = (r.get("meta") or {}).get("pagination") or {}
        if not pag.get("next") or pagina >= 200:
            break
        pagina += 1
    por_correo = {(m.get("email") or "").lower(): m for m in miembros if m.get("email")}
    personas = BD.leer("periodistas_hoy", select="id,correo,suscriptor_moticias,ghost_member_id", limit="10000")
    dominios = {m["dominio"]: m["id"] for m in BD.leer("medios_hoy", select="id,dominio", archivada_at="is.null", limit="5000") if m.get("dominio")}
    marcados = nuevos = bajas = 0
    conocidos = set()
    for p in personas:
        c = (p.get("correo") or "").lower()
        conocidos.add(c)
        m = por_correo.get(c)
        if m and not p.get("suscriptor_moticias"):
            BD.actualizar("periodistas", {"persona_id": "eq." + p["id"]}, {"suscriptor_moticias": True, "suscriptor_at": ahora(), "actualizado": ahora()})
            if not p.get("ghost_member_id"):
                BD.actualizar("crm_personas", {"id": "eq." + p["id"]}, {"ghost_member_id": m["id"]})
            marcados += 1
        elif not m and p.get("suscriptor_moticias"):
            BD.actualizar("periodistas", {"persona_id": "eq." + p["id"]}, {"suscriptor_moticias": False, "actualizado": ahora()})
            bajas += 1
    for c, m in por_correo.items():
        dom = c.split("@")[-1]
        cid = dominios.get(dom) or next((v for k, v in dominios.items() if dom.endswith("." + k)), None)
        if c in conocidos or dom in GENERICOS or not cid:
            continue
        if BD.leer("crm_personas", select="id", ghost_member_id="eq." + m["id"]):
            continue
        x = BD.insertar("crm_personas", {"cuenta_id": cid, "nombre": (m.get("name") or "").strip() or None, "correo": c, "perfil": "periodista",
                                          "ghost_member_id": m["id"], "notas": "Detectado: suscriptor de MOTICIAS con correo del medio", "creada_por": "detector"})[0]
        BD.insertar("periodistas", {"persona_id": x["id"], "suscriptor_moticias": True, "suscriptor_at": ahora(), "fuentes": ["ghost:miembro"]})
        nuevos += 1
    return {"miembros": len(miembros), "marcados": marcados, "nuevos": nuevos, "ya_no": bajas}


# ---------- carga desde la tarea de los miércoles ----------
def _lit(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, (dict, list)) and not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
        return "'%s'::jsonb" % json.dumps(v, ensure_ascii=False).replace("'", "''")
    if isinstance(v, list):
        return "array[%s]::text[]" % ",".join("'%s'" % x.replace("'", "''") for x in v) if v else "'{}'::text[]"
    return "'%s'" % str(v).replace("'", "''")


def validar(dato):
    """Comprueba un fichero de la tarea: {medios: [{nombre, web, ..., periodistas: [...], coberturas: [...]}]}."""
    errores = []
    for i, m in enumerate(dato.get("medios") or []):
        if not m.get("nombre"):
            errores.append("medio %d sin nombre" % i)
        if m.get("tipo_medio") and m["tipo_medio"] not in TIPOS_MEDIO:
            errores.append("%s: tipo_medio %s" % (m.get("nombre"), m["tipo_medio"]))
        if not dominio(m.get("web")):
            errores.append("%s: sin web válida (la web identifica al medio)" % m.get("nombre"))
        for k in ("correo_redaccion", "correo_notas"):
            if m.get(k) and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", m[k]):
                errores.append("%s: %s no válido" % (m.get("nombre"), k))
        if (m.get("correo_redaccion") or m.get("telefono_corporativo") or m.get("direccion")) and not m.get("fuentes"):
            errores.append("%s: datos de contacto sin fuente" % m.get("nombre"))
        for p in m.get("periodistas") or []:
            if not (p.get("nombre") or p.get("correo")):
                errores.append("%s: periodista sin nombre ni correo" % m.get("nombre"))
            if p.get("correo") and not p.get("fuentes"):
                errores.append("%s / %s: correo sin fuente" % (m.get("nombre"), p.get("nombre")))
            if p.get("rol") and p["rol"] not in ROLES:
                errores.append("%s / %s: rol %s" % (m.get("nombre"), p.get("nombre"), p["rol"]))
    return errores


def sql(dato):
    """SQL idempotente (se puede ejecutar dos veces) para el conector de Supabase: crea o completa cada medio por su
    dominio, sin pisar lo que alguien fijó a mano; añade periodistas por (medio, nombre o correo) y coberturas por URL."""
    out = ["begin;"]
    for m in dato.get("medios") or []:
        dom = dominio(m.get("web"))
        if not dom:
            continue
        web = m.get("web") if "://" in (m.get("web") or "") else "https://" + m["web"]
        out.append(("insert into crm_cuentas (producto, tipo, nombre, web, dominio, sector, origen, creada_por) "
                    "select 'moticias', 'medio', %s, %s, %s, %s, 'agente', 'medios-actualizar' "
                    "where not exists (select 1 from crm_cuentas where tipo = 'medio' and dominio = %s and archivada_at is null);")
                   % (_lit(m["nombre"][:200]), _lit(web), _lit(dom), _lit(m.get("sector")), _lit(dom)))
        cid = "(select id from crm_cuentas where tipo = 'medio' and dominio = %s and archivada_at is null limit 1)" % _lit(dom)
        out.append("insert into crm_estados (cuenta_id, estado, quien, motivo) select %s, 'sin_contacto', 'medios-actualizar', 'alta' "
                   "where not exists (select 1 from crm_estados where cuenta_id = %s);" % (cid, cid))
        f = {k: m[k] for k in CAMPOS_MEDIO if k in m and m[k] not in (None, "", [], {})}
        if "redes" in f:
            f["redes"] = limpiar_redes(f["redes"])
        for k in ("prob_previa",):
            if k in f and f[k] > 1:
                f[k] = round(f[k] / 100, 2)
        f.pop("colaboracion", None)
        f.pop("prob_publicacion", None)
        cols = ["cuenta_id"] + list(f)
        vals = [cid] + [_lit(f[k]) for k in f]
        upd = []
        for k in f:
            if k == "importancia":
                upd.append("importancia = case when medios.importancia_manual then medios.importancia else excluded.importancia end")
            elif k == "fuentes":
                upd.append("fuentes = (select array(select distinct unnest(medios.fuentes || excluded.fuentes)))")
            else:
                upd.append("%s = excluded.%s" % (k, k))
        upd.append("actualizado = now()")
        out.append("insert into medios (%s) values (%s) on conflict (cuenta_id) do update set %s;" % (", ".join(cols), ", ".join(vals), ", ".join(upd)))
        for p in m.get("periodistas") or []:
            correo = (p.get("correo") or "").strip().lower() or None
            nombre = (p.get("nombre") or "").strip() or None
            cond = ("lower(correo) = %s" % _lit(correo)) if correo else ("cuenta_id = %s and lower(nombre) = lower(%s)" % (cid, _lit(nombre)))
            out.append(("insert into crm_personas (cuenta_id, nombre, cargo, perfil, correo, telefono, linkedin, verificado, creada_por) "
                        "select %s, %s, %s, 'periodista', %s, %s, %s, %s, 'medios-actualizar' where not exists (select 1 from crm_personas where %s);")
                       % (cid, _lit(nombre), _lit((p.get("cargo") or "")[:160] or None), _lit(correo), _lit(p.get("telefono")), _lit(p.get("linkedin")),
                          _lit(bool(p.get("fuentes"))), cond))
            pid = "(select id from crm_personas where %s order by creada_at limit 1)" % cond
            # Completar datos que falten en la persona sin pisar los que ya tiene.
            out.append("update crm_personas set cargo = coalesce(cargo, %s), correo = coalesce(correo, %s), telefono = coalesce(telefono, %s), "
                       "linkedin = coalesce(linkedin, %s) where id = %s;" % (_lit(p.get("cargo")), _lit(correo), _lit(p.get("telefono")), _lit(p.get("linkedin")), pid))
            g = {k: p[k] for k in CAMPOS_PERIODISTA if k in p and p[k] not in (None, "", [], {})}
            if "redes" in g:
                g["redes"] = limpiar_redes(g["redes"])
            g.pop("colaboracion", None)
            g.pop("prob_publicacion", None)
            cols = ["persona_id"] + list(g)
            vals = [pid] + [_lit(g[k]) for k in g]
            upd = ["%s = excluded.%s" % (k, k) if k not in ("importancia", "fuentes") else
                   ("importancia = case when periodistas.importancia_manual then periodistas.importancia else excluded.importancia end" if k == "importancia"
                    else "fuentes = (select array(select distinct unnest(periodistas.fuentes || excluded.fuentes)))") for k in g] + ["actualizado = now()"]
            out.append("insert into periodistas (%s) values (%s) on conflict (persona_id) do update set %s;" % (", ".join(cols), ", ".join(vals), ", ".join(upd)))
        for k in m.get("coberturas") or []:
            if _url_ok(k.get("url")):
                out.append("insert into prensa_coberturas (cuenta_id, url, titulo, fecha, alcance, detectada, envio_id) values (%s, %s, %s, %s, %s, 'agente', %s) "
                           "on conflict (url) do nothing;" % (cid, _lit(k["url"]), _lit(k.get("titulo")), _lit(k.get("fecha")), _lit(k.get("alcance")), _lit(k.get("envio_id"))))
    out.append("select prensa_recalcular();")
    out.append("commit;")
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] in ("sql", "validar"):
        dato = json.load(open(sys.argv[2], encoding="utf-8"))
        errores = validar(dato)
        if sys.argv[1] == "validar" or errores:
            print("\n".join(errores) or "ok: %d medios, %d periodistas" % (len(dato.get("medios") or []), sum(len(m.get("periodistas") or []) for m in dato.get("medios") or [])))
            sys.exit(1 if errores else 0)
        print(sql(dato))
    else:
        print("uso: python3 src/prensa.py validar|sql FICHERO.json  (FICHERO en work/, nunca en el repositorio)")
