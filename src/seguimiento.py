"""MOTICIAS · Seguimiento de la publicidad, los patrocinios y el contenido patrocinado, y su comprobador.

Decisiones de Rainer (9-11-2026, tarde): «un panel de seguimiento de cada una de las publicidades y patrocinios: fecha de
publicación y retirada, en qué contextos insertados, en qué posiciones, número de visualizaciones y número de clics», y
«un agente comprobador que en horarios diurnos al azar haga clic en cada uno de los enlaces promocionados […] con
constatación en el panel».

- Visualizaciones y clics los manda el script del sitio (app/public/sitio/m.js) a `POST /api/gestor?a=evento`: una
  visualización cuando la caja se ve al menos a medias en pantalla; un clic cuando el lector pulsa su enlace. Los robots
  (por su identificador) y el comprobador no cuentan: las cifras que verá un anunciante son de lectores.
- Cada caja tiene un identificador: el de su fichero en data/ads/ («grupo-movo-pmst»; hasta el 15-11-2026 llevaban otro prefijo y la migración 009 trasladó su historia) o, para las cajas de contenido
  patrocinado del texto, «caja:<producto>».
- El comprobador visita cada enlace activo con su UTM (`utm_medium=comprobacion`, para que se pueda filtrar en la
  analítica del destino) y apunta el resultado. Lo lanza el cron de Vercel cada hora y decide al azar si toca. Sus visitas no son clics de lectores, no
  cuentan en el panel y no mejoran el SEO de nadie (Google no ve una visita de servidor): sirven para saber que el
  destino funciona. Desde el 16-11-2026 (cambio `comprobador-diario`) corre todos los días, de 9 a 21 h de Madrid, con
  una comprobación por enlace y día a hora al azar, historial descargable para el anunciante y correo si falla dos
  veces seguidas.
"""
import datetime, glob, json, os, random, re, time, urllib.error, urllib.parse, urllib.request

import bd as BD

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ID_OK = re.compile(r"^[a-z0-9:-]{3,90}$")
ROBOT = re.compile(r"bot|crawl|spider|slurp|headless|lighthouse|preview|facebookexternalhit|curl|wget|python|monitor", re.I)
UA = "MOTICIAS-comprobador/1.0 (+https://www.moticias.com/como-trabajamos/)"


def _json(ruta):
    return json.load(open(ruta, encoding="utf-8"))


def anuncios():
    return [_json(f) for f in sorted(glob.glob(os.path.join(ROOT, "data", "ads", "*.json")))]


def productos():
    return [_json(f) for f in sorted(glob.glob(os.path.join(ROOT, "data", "productos", "*.json")))]


def hoy():
    return datetime.date.today().isoformat()


def objetivos():
    """Enlaces promocionados vivos: cajas de publicidad activas hoy y productos del grupo activos (sus cajas del texto)."""
    out, h = [], hoy()
    for a in anuncios():
        if a.get("status") == "activo" and str(a.get("url") or "").startswith("https://") and not (a.get("start") and a["start"] > h) \
                and not (a.get("end") and a["end"] < h):
            out.append({"anuncio": a["id"], "url": a["url"], "nombre": a.get("name") or a["id"]})
    for p in productos():
        if p.get("status") == "activo" and p.get("modo") != "apagado" and str(p.get("url") or "").startswith("https://"):
            out.append({"anuncio": "caja:" + p["id"], "url": p["url"], "nombre": p.get("name") or p["id"]})
    return out


def ids_validos():
    return {a["id"] for a in anuncios()} | {"caja:" + p["id"] for p in productos()}


# ---------- eventos del sitio ----------
def evento(d, ua):
    """Suma una visualización («i») o un clic («c»). Devuelve True si contó."""
    if ROBOT.search(ua or "") or not BD.configurada():
        return False
    aid, hueco, pag, tipo = str(d.get("a") or ""), str(d.get("h") or "")[:40], str(d.get("p") or "/")[:200], d.get("t")
    if tipo not in ("i", "c") or not ID_OK.match(aid) or aid not in ids_validos() or len(hueco) < 2:
        return False
    pag = urllib.parse.urlparse(pag).path or "/"
    try:
        BD.peticion("POST", "rpc/pub_contar", cuerpo={"p_anuncio": aid, "p_hueco": hueco, "p_pagina": pag, "p_tipo": tipo})
        return True
    except BD.ErrorBD:
        return False


TIPOS_AMPLIADOS = {"i": "vista", "c": "clic", "cta": "cta", "fa": "form_abierto", "fe": "form_enviado",
                   "vista": "vista", "clic": "clic", "form_abierto": "form_abierto", "form_enviado": "form_enviado"}
DISPOSITIVOS = ("movil", "tableta", "escritorio")


def evento_ampliado(d, ua):
    """Banner premium (16-11-2026, migración 013): suma el evento con sección, dispositivo y procedencia (dominio de origen o
    utm_source, sin datos personales). Tipos: vista, clic, cta (botón), form_abierto, form_enviado."""
    if ROBOT.search(ua or "") or not BD.configurada():
        return False
    aid, hueco, tipo = str(d.get("a") or ""), str(d.get("h") or "")[:40], TIPOS_AMPLIADOS.get(str(d.get("t") or ""))
    if not tipo or not ID_OK.match(aid) or aid not in ids_validos() or len(hueco) < 2:
        return False
    sec = re.sub(r"[^a-z0-9-]", "", str(d.get("s") or "portada").lower())[:60] or "portada"
    dv = d.get("dv") if d.get("dv") in DISPOSITIVOS else "escritorio"
    pr = re.sub(r"[^a-z0-9.-]", "", str(d.get("pr") or "directo").lower())[:80] or "directo"
    try:
        BD.peticion("POST", "rpc/pub_evento", cuerpo={"p_anuncio": aid, "p_hueco": hueco, "p_seccion": sec, "p_dispositivo": dv, "p_procedencia": pr, "p_tipo": tipo})
        return True
    except BD.ErrorBD:
        return False


def panel_ampliado(dias=30):
    """Por caja: vistas, clics, clics en el botón, formularios abiertos y enviados, y su reparto por procedencia, dispositivo y sección."""
    if not BD.configurada():
        return {}
    desde = (datetime.date.today() - datetime.timedelta(days=dias - 1)).isoformat()
    try:
        filas = BD.leer("pub_eventos", select="anuncio,seccion,dispositivo,procedencia,tipo,n", dia="gte." + desde, limit="50000")
    except BD.ErrorBD:
        return {}
    out = {}
    for f in filas:
        x = out.setdefault(f["anuncio"], {"totales": {}, "procedencia": {}, "dispositivo": {}, "seccion": {}})
        x["totales"][f["tipo"]] = x["totales"].get(f["tipo"], 0) + f["n"]
        for dim in ("procedencia", "dispositivo", "seccion"):
            y = x[dim].setdefault(f[dim], {})
            y[f["tipo"]] = y.get(f["tipo"], 0) + f["n"]
    return out


# ---------- comprobador ----------
def con_utm(url, anuncio):
    p = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qsl(p.query)
    q = [x for x in q if not x[0].startswith("utm_")] + [("utm_source", "moticias"), ("utm_medium", "comprobacion"), ("utm_campaign", anuncio)]
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, urllib.parse.urlencode(q), p.fragment))


def visitar(url, tiempo=15):
    """(ok, estado, url_final, ms, error). Sigue redirecciones; vale todo 2xx y 3xx final."""
    t0 = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*;q=0.8", "Accept-Language": "es-ES,es;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=tiempo) as r:
            r.read(2048)
            return True, r.status, r.geturl(), int((time.time() - t0) * 1000), None
    except urllib.error.HTTPError as e:
        return False, e.code, getattr(e, "url", url), int((time.time() - t0) * 1000), "el destino respondió %s" % e.code
    except Exception as e:  # noqa: BLE001  (DNS, certificado, tiempo agotado…)
        return False, None, None, int((time.time() - t0) * 1000), str(getattr(e, "reason", e))[:300]


def comprobados_hoy():
    try:
        filas = BD.leer("pub_comprobaciones", select="anuncio", at="gte." + hoy() + "T00:00:00+01:00", limit="2000")
    except BD.ErrorBD:
        return set()
    return {f["anuncio"] for f in filas}


def hora_madrid():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Europe/Madrid"))
    except Exception:  # noqa: BLE001 — sin la base de zonas, invierno (UTC+1)
        return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1)))


def _avisar_si_falla_dos_veces(anuncio, nombre):
    """Cambio comprobador-diario (16-11-2026): si un enlace falla dos comprobaciones seguidas, correo al editor jefe
    (una sola vez por racha: solo cuando la anterior a esas dos funcionaba o no existía)."""
    try:
        ult = BD.leer("pub_comprobaciones", select="ok,error,at,url_final", anuncio="eq." + anuncio, order="at.desc", limit="3")
    except BD.ErrorBD:
        return False
    if len(ult) < 2 or ult[0]["ok"] or ult[1]["ok"] or (len(ult) == 3 and not ult[2]["ok"]):
        return False
    try:
        import menciones as M
        v = json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))
        para = (v.get("productos") or {}).get("email") or []
        if not para:
            return False
        ok, _ = M.enviar_correo("MOTICIAS · El enlace de «%s» falla dos veces seguidas" % nombre[:80],
                                "<p>El comprobador ha visitado dos veces seguidas el enlace de <b>%s</b> y no responde: %s.</p>"
                                "<p>Revísalo en el gestor: <a href=\"https://app.moticias.com/gestor/?vista=anuncios\">Publicidad → Seguimiento</a>.</p>" % (
                                    nombre, ult[0].get("error") or "sin respuesta"), para, M.remitentes_avisos(v))
        return ok
    except Exception:  # noqa: BLE001 — el aviso nunca tumba el comprobador
        return False


def comprobar(origen="agente", azar=True, solo=None, tope_s=200):
    """Comprueba los enlaces. Desde el 16-11-2026 (cambio `comprobador-diario`) corre todos los días, de 9 a 21 h de
    Madrid, y cada enlace se comprueba al menos una vez al día a una hora al azar: en cada pasada tiene una probabilidad
    de tocarle (más alta por la tarde si aún no se comprobó hoy, y segura en la última pasada). Sus visitas no son clics
    de lectores ni mejoran el SEO de nadie: sirven para demostrar en el panel que el destino funciona."""
    hora = hora_madrid().hour
    ya = comprobados_hoy() if azar else set()
    objs = [o for o in objetivos() if not solo or o["anuncio"] == solo]
    random.shuffle(objs)
    out, t0 = [], time.time()
    for o in objs:
        if azar:
            if o["anuncio"] in ya:
                continue  # una vez al día basta
            p = 1.0 if hora >= 20 else (0.9 if hora >= 18 else 0.25)
            if random.random() > p:
                continue
        if time.time() - t0 > tope_s:
            break
        url = con_utm(o["url"], o["anuncio"])
        ok, estado, final, ms, err = visitar(url)
        fila = {"anuncio": o["anuncio"], "url": url[:600], "estado": estado, "url_final": (final or "")[:600] or None, "ms": ms, "ok": ok,
                "error": err, "origen": origen}
        try:
            BD.insertar("pub_comprobaciones", fila)
            if not ok:
                _avisar_si_falla_dos_veces(o["anuncio"], o["nombre"])
        except BD.ErrorBD:
            pass
        out.append(dict(fila, nombre=o["nombre"]))
        if azar:
            time.sleep(random.uniform(1, 6))
    return out


def comprobaciones_csv(anuncio, dias=30):
    """Historial auditable de un enlace para el anunciante: fecha y hora (Madrid), resultado, estado HTTP, tiempo y destino."""
    desde = (datetime.date.today() - datetime.timedelta(days=dias - 1)).isoformat()
    filas = BD.leer("pub_comprobaciones", select="at,ok,estado,ms,url_final,error,origen", anuncio="eq." + anuncio, at="gte." + desde, order="at.asc", limit="5000")
    q = lambda x: '"%s"' % str("" if x is None else x).replace('"', '""')
    lineas = ["fecha_hora,resultado,estado_http,ms,destino,error,origen"]
    for f in filas:
        lineas.append(",".join(q(x) for x in (f["at"], "funciona" if f["ok"] else "no funciona", f.get("estado"), f.get("ms"), f.get("url_final"), f.get("error"), f.get("origen"))))
    return "\r\n".join(lineas) + "\r\n"


# ---------- panel ----------
def _hist_anuncio(a):
    h = a.get("historial") or []
    pub = next((x["en"] for x in h if x.get("estado") == "activo"), None) or (a.get("start") if a.get("status") == "activo" else None)
    ret = next((x["en"] for x in reversed(h) if x.get("estado") in ("pausado", "terminado")), None)
    if not ret and a.get("end") and a["end"] < hoy():
        ret = a["end"]
    return pub, ret


def menciones_publicadas():
    """Por producto: cada pieza donde su caja salió en la web, con posición y fechas."""
    out = {}
    for f in glob.glob(os.path.join(ROOT, "data", "articles", "*.json")):
        a = _json(f)
        for m in a.get("menciones") or []:
            if m.get("estado") not in ("publicada", "retirada") or not (m.get("en_web") or m.get("historial")):
                continue
            h = m.get("historial") or []
            pub = m.get("en_web") or next((x["en"] for x in h if x.get("accion") in ("publicar", "anadir")), None) or a.get("published_at")
            ret = next((x["en"] for x in reversed(h) if x.get("accion") == "retirar"), None) if m.get("estado") == "retirada" else None
            out.setdefault("caja:" + (m.get("producto") or ""), []).append({"pieza": a["id"], "titulo": a.get("title"), "seccion": a.get("section"),
                                                                           "posicion": m.get("posicion") or "estandar", "estado": m.get("estado"),
                                                                           "publicada": pub, "retirada": ret})
    for v in out.values():
        v.sort(key=lambda x: x.get("publicada") or "", reverse=True)
    return out


def panel(dias=30):
    desde = (datetime.date.today() - datetime.timedelta(days=dias - 1)).isoformat()
    filas = BD.leer("pub_diario", select="dia,anuncio,hueco,pagina,impresiones,clics", dia="gte." + desde, limit="20000") if BD.configurada() else []
    comps = BD.leer("pub_comprobaciones", select="anuncio,estado,ok,error,ms,url_final,origen,at", order="at.desc", limit="400") if BD.configurada() else []
    por = {}
    for f in filas:
        x = por.setdefault(f["anuncio"], {"impresiones": 0, "clics": 0, "huecos": {}, "paginas": {}, "dias": {}})
        x["impresiones"] += f["impresiones"]
        x["clics"] += f["clics"]
        for k, kk in (("huecos", f["hueco"]), ("paginas", f["pagina"]), ("dias", f["dia"])):
            y = x[k].setdefault(kk, [0, 0])
            y[0] += f["impresiones"]
            y[1] += f["clics"]
    hoy_ = hoy()
    ult = {}
    for c in comps:
        ult.setdefault(c["anuncio"], [])
        if len(ult[c["anuncio"]]) < 6:
            ult[c["anuncio"]].append(c)
    menc = menciones_publicadas()
    cajas = []
    for a in anuncios():
        pub, ret = _hist_anuncio(a)
        cajas.append({"id": a["id"], "nombre": a.get("name"), "anunciante": a.get("advertiser"), "tipo": a.get("type"), "nivel": a.get("nivel"),
                      "estado": a.get("status"), "huecos": a.get("slots") or [], "secciones": a.get("sections") or [], "inicio": a.get("start"),
                      "fin": a.get("end"), "publicada": pub, "retirada": ret, "url": a.get("url"), "cifras": por.get(a["id"]),
                      "comprobaciones": ult.get(a["id"], [])})
    for p in productos():
        k = "caja:" + p["id"]
        lista = menc.get(k, [])
        cajas.append({"id": k, "nombre": "Contenido patrocinado · " + (p.get("name") or p["id"]), "anunciante": p.get("name"), "tipo": "contenido-patrocinado",
                      "nivel": p.get("posicion"), "estado": p.get("status") if p.get("modo") != "apagado" else "apagado",
                      "huecos": sorted({m["posicion"] for m in lista}), "publicada": lista[-1]["publicada"] if lista else None,
                      "retirada": None, "url": p.get("url"), "cifras": por.get(k), "comprobaciones": ult.get(k, []), "piezas": lista})
    amp = panel_ampliado(dias)
    for c in cajas:
        c["ampliado"] = amp.get(c["id"])
        c["comprobado_hoy"] = next((x for x in c["comprobaciones"] if str(x.get("at") or "")[:10] == hoy_), None)
    return {"desde": desde, "dias": dias, "cajas": cajas}
