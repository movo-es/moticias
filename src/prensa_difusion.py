#!/usr/bin/env python3
"""MOTICIAS · Difusión de notas de prensa con filtro de valor y aprobación humana (cambio sala-de-prensa-v1).
Solo biblioteca estándar. Diseño: openspec/changes/sala-de-prensa-v1/design.md § 4.

Tres puertas: (1) la nota supera el umbral del asesor para su plan; (2) cada destinatario tiene relevancia suficiente
en los tres ejes; (3) no se pasa de su frecuencia semanal. Nada sale sin `aprobar`. B2C nunca recibe una nota suelta:
recibe el resumen semanal. Cada correo lleva «Por qué le llega», la marca de comunicado y la baja por sector o total.

Uso (carpeta privada con --privado, como src/contactos.py):
  python3 -I src/prensa_difusion.py planificar <id> [--plan difusion|difusion-plus]
  python3 -I src/prensa_difusion.py aprobar <id> --por "Rainer"
  python3 -I src/prensa_difusion.py enviar <id> [--dry-run] [--fuera-de-horario]
  python3 -I src/prensa_difusion.py eventos <id>                      # aperturas, clics, rebotes y bajas desde Brevo
  python3 -I src/prensa_difusion.py resumen [--semana AAAA-MM-DD] [--dry-run]   # resumen semanal B2C (martes)
"""
import argparse, datetime, html, json, os, sys, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import contactos as C  # noqa: E402
import ghost_publish as G  # noqa: E402
import prensa_asesor as A  # noqa: E402
import prensa_comun as P  # noqa: E402
from taxonomia import Taxonomia  # noqa: E402

V = json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))
CFG = V["prensa"]
INDIVIDUAL = {"redaccion", "periodista", "newsletter", "decisor-b2b"}
RESUMEN = {"profesional", "particular"}
# Festivos nacionales (los autonómicos y locales no frenan un envío estatal). Ampliar cada año.
FESTIVOS = {"2026-12-08", "2026-12-25", "2027-01-01", "2027-01-06", "2027-03-26", "2027-05-01", "2027-08-16", "2027-10-12",
            "2027-11-01", "2027-12-06", "2027-12-08", "2027-12-25"}
BASE_TEXTO = {
    "interes-legitimo-prensa": "Le escribimos porque su dirección es la de contacto profesional de una redacción o de un periodista del sector, y solo le enviamos notas de su especialidad (RGPD, art. 6.1.f). Responsable: Avionline S.L. Puede darse de baja con un clic.",
    "consentimiento": "Recibe este correo porque pidió en MOTICIAS recibir notas de prensa de este sector. Responsable: Avionline S.L.",
    "contrato": "Recibe este correo en el marco de su relación con MOTICIAS. Responsable: Avionline S.L.",
}


def ejes_de(n):
    return {"submodo": n["submodo"], "modo": n["modo"], "territorios": n["territorios"], "temas": n["temas"]}


def por_que(n, an):
    """Las tres líneas «Por qué le llega»: redactadas por la redacción si existen en el pedido; si no, del análisis."""
    tx = Taxonomia()
    terr = ", ".join(tx.nombre_territorio(t) for t in n["territorios"])
    sm = tx.submodos.get(n["submodo"], (None, {"nombre": n["submodo"]}))[1]["nombre"]
    qué = n.get("subtitulo") or A.frases(n["cuerpo_md"])[0]
    cifra = (an.get("cifras_detectadas") or ["—"])[0]
    return ["Qué: " + qué[:220], "A quién afecta: %s · %s" % (sm, terr), "Dato clave: " + cifra]


def planificar(priv, nid, plan=None):
    n = P.leer_nota(nid)
    ped = P.leer_pedido(priv, nid) or {"nota_id": nid, "plan": plan or "difusion", "creado": P.ahora(), "envios": []}
    plan = plan or ped.get("plan") or "difusion"
    planes = {p["id"]: p for p in CFG["planes"]}
    if plan not in ("difusion", "difusion-plus"):
        raise SystemExit("El plan %s no incluye difusión." % plan)
    an = A.analizar({"titulo": n["titulo"], "subtitulo": n.get("subtitulo"), "cuerpo": n["cuerpo_md"] + "\n\n" + (n.get("sobre_md") or "") + "\n\n" + (n.get("contacto_prensa_md") or ""),
                     "organizacion": n["organizacion"]["nombre"]})
    req = planes[plan]["requiere"]
    tx = Taxonomia()
    base = C.cargar(priv)
    ejes = ejes_de(n)
    el, fuera = C.elegibles(base, ejes, CFG["filtro_valor"], tx, tipos=INDIVIDUAL)
    b2c, _ = C.elegibles(base, ejes, CFG["filtro_valor"], tx, tipos=RESUMEN)
    bloqueo = None
    if an["puntuacion"] < req["puntuacion_min"]:
        bloqueo = "puntuación %d < %d: devolver al cliente con los avisos" % (an["puntuacion"], req["puntuacion_min"])
    elif an["tipo"] == "promocion":
        bloqueo = "es promoción, no nota de prensa"
    elif len(el) < req["destinatarios_min"]:
        bloqueo = "solo %d destinatarios (mínimo %d): no cobrar la difusión" % (len(el), req["destinatarios_min"])
    ped.update({"plan": plan, "asesor": {"puntuacion": an["puntuacion"], "veredicto": an["veredicto"], "tipo": an["tipo"], "fecha": P.ahora()},
                "por_que": ped.get("por_que") or por_que(n, an),
                "difusion": {"creado": P.ahora(), "bloqueo": bloqueo, "destinatarios": el, "fuera": fuera, "resumen_b2c": len(b2c),
                             "aprobado_por": None, "aprobado_en": None}})
    P.guardar_pedido(priv, ped)
    from collections import Counter
    print("Plan %s para %s: %d destinatarios %s · %d al resumen B2C · fuera: %s" % (plan, nid, len(el), dict(Counter(d["tipo"] for d in el)), len(b2c), fuera))
    print("BLOQUEADO: " + bloqueo if bloqueo else "Listo para aprobar: python3 -I src/prensa_difusion.py aprobar %s --por <nombre>" % nid)
    return ped


def aprobar(priv, nid, quien):
    ped = P.leer_pedido(priv, nid)
    if not ped or not ped.get("difusion"):
        raise SystemExit("No hay plan de difusión: ejecuta antes `planificar`.")
    if ped["difusion"].get("bloqueo"):
        raise SystemExit("El plan está bloqueado (%s): no se aprueba." % ped["difusion"]["bloqueo"])
    ped["difusion"]["aprobado_por"], ped["difusion"]["aprobado_en"] = quien, P.ahora()
    P.guardar_pedido(priv, ped)
    print("Aprobado por %s: %d destinatarios." % (quien, len(ped["difusion"]["destinatarios"])))


def en_horario(t=None):
    import zoneinfo
    t = (t or datetime.datetime.now(datetime.timezone.utc)).astimezone(zoneinfo.ZoneInfo("Europe/Madrid"))
    return t.weekday() < 5 and t.date().isoformat() not in FESTIVOS and (8, 30) <= (t.hour, t.minute) <= (11, 30)


def url_nota(n, cid=None):
    base = (n.get("ghost") or {}).get("url") or "%s/%s/" % (V["ghost"]["url"], n["id"])
    q = {"utm_source": "moticias", "utm_medium": "email", "utm_campaign": "np-" + n["id"]}
    return base + "?" + urllib.parse.urlencode(q)


def correo(n, ped, c):
    e = html.escape
    m = CFG["marca"]
    tx = Taxonomia()
    sm = tx.submodos.get(n["submodo"], (None, {"nombre": n["submodo"]}))[1]["nombre"]
    terr = ", ".join(tx.nombre_territorio(t) for t in n["territorios"])
    asunto = "%s · %s · %s: %s" % (m["etiqueta"], sm, terr, n["titulo"])[:180]
    baja_s = "%s/api/prensa?a=baja&t=%s" % (P.base_app(), P.firmar("baja", "%s|%s" % (c["id"], n["submodo"])))
    baja_t = "%s/api/prensa?a=baja&t=%s" % (P.base_app(), P.firmar("baja", c["id"]))
    cuerpo = """<div style="font:15px/1.55 system-ui,-apple-system,'Segoe UI',sans-serif;color:#111827;max-width:640px">
<div style="font:600 11px/1.4 system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:#6b7280">MOTICIAS · %(et)s · %(aviso)s%(grupo)s</div>
<div style="background:#f0fdfa;border-left:3px solid #0f766e;padding:10px 14px;margin:12px 0;font-size:14px"><b>Por qué le llega</b><br>%(pq)s</div>
<h1 style="font-size:21px;line-height:1.3;margin:.4em 0">%(tit)s</h1>%(sub)s
<p style="color:#374151;font-size:13px"><b>%(org)s</b>%(emb)s</p>
%(cuerpo)s%(sobre)s%(contacto)s
<p><a href="%(url)s" style="color:#0f766e">Ver la nota en MOTICIAS</a></p>
<hr style="border:0;border-top:1px solid #e5e7eb;margin:24px 0 12px">
<p style="font-size:12px;color:#6b7280">%(base)s<br><a href="%(bs)s">No quiero más notas de %(sm)s</a> · <a href="%(bt)s">No quiero más notas de prensa</a></p>
</div>""" % {
        "et": e(m["etiqueta"]), "aviso": e(m["aviso"]), "grupo": (" · " + e(m["aviso_grupo"])) if n.get("grupo") else "",
        "pq": "<br>".join(e(x) for x in ped.get("por_que", [])), "tit": e(n["titulo"]),
        "sub": ('<p style="font-size:16px;color:#374151;margin:.2em 0 1em">%s</p>' % e(n["subtitulo"])) if n.get("subtitulo") else "",
        "org": e(n["organizacion"]["nombre"]), "emb": (" · Embargo hasta %s" % e(n["embargo_hasta"])) if n.get("embargo_hasta") else "",
        "cuerpo": G.md_to_html(n["cuerpo_md"]), "sobre": G.md_to_html(n.get("sobre_md") or ""), "contacto": G.md_to_html(n.get("contacto_prensa_md") or ""),
        "url": e(url_nota(n)), "base": e(BASE_TEXTO.get(c.get("base"), BASE_TEXTO["consentimiento"])), "bs": e(baja_s), "bt": e(baja_t), "sm": e(sm.lower())}
    return asunto, cuerpo, baja_t


def brevo(asunto, cuerpo, para, nombre, etiqueta, baja, dry_run=False):
    key = os.environ.get("BREVO_API_KEY")
    if dry_run or not key:
        return False, "sin envío (%s)" % ("dry-run" if dry_run else "falta BREVO_API_KEY")
    r = CFG["remitente"]
    body = {"sender": {"email": r["email"], "name": r["nombre"]}, "to": [{"email": para, "name": nombre or para}], "subject": asunto,
            "htmlContent": cuerpo, "tags": [etiqueta], "headers": {"List-Unsubscribe": "<%s>" % baja, "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"},
            "replyTo": {"email": r["email"]}}
    req = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=json.dumps(body).encode(), method="POST",
                                 headers={"api-key": key, "Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Moticias/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return True, json.loads(resp.read() or b"{}").get("messageId", "")
    except urllib.error.HTTPError as ex:
        return False, "HTTP %s %s" % (ex.code, ex.read().decode("utf-8", "replace")[:200])
    except urllib.error.URLError as ex:
        return False, "red: %s" % ex


def enviar(priv, nid, dry_run=False, fuera_de_horario=False):
    n = P.leer_nota(nid)
    ped = P.leer_pedido(priv, nid)
    dif = (ped or {}).get("difusion") or {}
    if not dif.get("aprobado_por"):
        raise SystemExit("Plan sin aprobar: lo aprueba el director o la oficina (`aprobar %s --por <nombre>`). No se envía nada." % nid)
    if n.get("status") != "publicada" and not dry_run:
        raise SystemExit("La nota no está publicada en MOTICIAS: primero `prensa_publicar.py publicar %s`." % nid)
    if not dry_run and not fuera_de_horario and not en_horario():
        raise SystemExit("Fuera de horario (laborables 08:30–11:30, hora de Madrid): se enviará en la próxima ventana.")
    base = C.cargar(priv)
    por_id = {c["id"]: c for c in base["contactos"]}
    ya = {x["contacto"] for x in ped.get("envios", []) if x.get("ok")}
    hechos = fallos = 0
    out_dir = os.path.join(ROOT, "work", "prensa", nid)
    for d in dif["destinatarios"]:
        c = por_id.get(d["id"])
        if not c or d["id"] in ya:
            continue
        ok_c, motivo = C.puede_recibir(c, CFG["filtro_valor"])  # se vuelve a mirar: pudo darse de baja tras el plan
        if not ok_c:
            ped["envios"].append({"contacto": c["id"], "ok": False, "detalle": "omitido: " + motivo, "fecha": P.ahora()})
            continue
        asunto, cuerpo, baja = correo(n, ped, c)
        if dry_run and hechos == 0:
            os.makedirs(out_dir, exist_ok=True)
            open(os.path.join(out_dir, "correo-%s.html" % c["tipo"]), "w", encoding="utf-8").write("<!-- %s -->\n%s" % (html.escape(asunto), cuerpo))
        ok, det = brevo(asunto, cuerpo, c["email"], c.get("nombre"), "np-" + nid, baja, dry_run)
        if dry_run:
            hechos += 1
            continue
        ped["envios"].append({"contacto": c["id"], "tipo": c["tipo"], "ok": ok, "detalle": det, "fecha": P.ahora()})
        if ok:
            c.setdefault("envios", []).append({"nota": nid, "fecha": P.ahora()})
            hechos += 1
        else:
            fallos += 1
    if not dry_run:
        P.guardar_pedido(priv, ped)
        C.guardar(priv, base)
    print("%s: %d enviados, %d fallos%s" % (nid, hechos, fallos, " (simulación: ejemplo en work/prensa/%s/)" % nid if dry_run else ""))


def eventos(priv, nid):
    key = os.environ.get("BREVO_API_KEY")
    if not key:
        raise SystemExit("Falta BREVO_API_KEY.")
    url = "https://api.brevo.com/v3/smtp/statistics/events?" + urllib.parse.urlencode({"tags": "np-" + nid, "limit": 2500, "days": 90})
    req = urllib.request.Request(url, headers={"api-key": key, "Accept": "application/json", "User-Agent": "Moticias/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        evs = json.loads(r.read()).get("events", [])
    por = {}
    for e in evs:
        por.setdefault(e.get("event"), set()).add(e.get("email"))
    met = {"entregados": len(por.get("delivered", set())), "aperturas_unicas": len(por.get("opened", set()) | por.get("uniqueOpened", set())),
           "clics_unicos": len(por.get("clicks", set())), "rebotes": len(por.get("hardBounces", set()) | por.get("softBounces", set())),
           "bajas": len(por.get("unsubscribed", set())), "leido_en": P.ahora(), "fuente": "Brevo, etiqueta np-" + nid}
    ped = P.leer_pedido(priv, nid)
    ped["metricas"] = met
    P.guardar_pedido(priv, ped)
    base = C.cargar(priv)
    abiertos = por.get("opened", set()) | por.get("uniqueOpened", set()) | por.get("clicks", set())
    enviados = {x["contacto"] for x in ped.get("envios", []) if x.get("ok")}
    lim = CFG["filtro_valor"]["pausar_tras_sin_abrir"]
    for c in base["contactos"]:
        if c["id"] not in enviados:
            continue
        if c.get("email") in por.get("hardBounces", set()):
            c["estado"] = "rebotado"
        elif c.get("email") in abiertos:
            c["sin_abrir_seguidos"] = 0
        elif c.get("ultima_nota_contada") != nid:
            c["sin_abrir_seguidos"] = c.get("sin_abrir_seguidos", 0) + 1
            if c["sin_abrir_seguidos"] >= lim and c.get("estado") == "activo":
                c["estado"], c["pausado_motivo"] = "pausado", "%d envíos seguidos sin abrir" % lim
        c["ultima_nota_contada"] = nid
    C.guardar(priv, base)
    print(json.dumps(met, ensure_ascii=False))


def resumen(priv, semana=None, dry_run=False):
    """Resumen semanal B2C: las notas publicadas la semana anterior que encajan con los sectores de cada lector."""
    hoy = datetime.date.fromisoformat(semana) if semana else datetime.date.today()
    desde, hasta = (hoy - datetime.timedelta(days=7)).isoformat(), hoy.isoformat()
    notas = [n for n in P.todas_las_notas() if n.get("status") == "publicada" and desde <= (n.get("publicada_en") or "")[:10] < hasta]
    if not notas:
        print("Sin notas publicadas entre %s y %s: no hay resumen." % (desde, hasta))
        return
    tx = Taxonomia()
    base = C.cargar(priv)
    rmin = CFG["filtro_valor"]["relevancia_min_destinatario"]
    hechos = 0
    for c in base["contactos"]:
        if c.get("tipo") not in RESUMEN or not C.puede_recibir(c, CFG["filtro_valor"])[0]:
            continue
        suyas = [n for n in notas if C.relevancia(c, ejes_de(n), tx)[0] >= rmin and n["submodo"] not in (c.get("bajas_sector") or [])]
        if not suyas:
            continue
        items = "".join('<li><a href="%s">%s</a><br><span style="color:#6b7280;font-size:13px">%s · %s</span></li>'
                        % (html.escape(url_nota(n)), html.escape(n["titulo"]), html.escape(n["organizacion"]["nombre"]), html.escape(n.get("subtitulo") or ""))
                        for n in suyas[:8])
        baja = "%s/api/prensa?a=baja&t=%s" % (P.base_app(), P.firmar("baja", c["id"]))
        cuerpo = ('<div style="font:15px/1.55 system-ui,sans-serif;max-width:640px"><div style="font:600 11px system-ui;text-transform:uppercase;color:#6b7280">MOTICIAS · Notas de prensa de la semana</div>'
                  '<p style="font-size:13px;color:#6b7280">Comunicados de empresas e instituciones de sus sectores, tal como los envían. No son contenido editorial de MOTICIAS.</p><ul>%s</ul>'
                  '<p style="font-size:12px;color:#6b7280">%s <a href="%s">Darme de baja</a></p></div>') % (items, html.escape(BASE_TEXTO["consentimiento"]), html.escape(baja))
        ok, det = brevo("Notas de prensa de la semana · %d de sus sectores" % len(suyas), cuerpo, c["email"], c.get("nombre"), "np-resumen-" + hasta, baja, dry_run)
        if ok:
            c.setdefault("envios", []).append({"nota": "resumen-" + hasta, "fecha": P.ahora()})
        hechos += 1
    if not dry_run:
        C.guardar(priv, base)
    print("Resumen %s: %d lectores%s" % (hasta, hechos, " (simulación)" if dry_run else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["planificar", "aprobar", "enviar", "eventos", "resumen"])
    ap.add_argument("id", nargs="?")
    ap.add_argument("--privado"); ap.add_argument("--plan", choices=["difusion", "difusion-plus"]); ap.add_argument("--por")
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--fuera-de-horario", action="store_true"); ap.add_argument("--semana")
    a = ap.parse_args()
    priv = C.ruta_privada(a.privado)
    if a.accion == "planificar":
        planificar(priv, a.id, a.plan)
    elif a.accion == "aprobar":
        if not a.por:
            raise SystemExit("Indica --por <nombre>.")
        aprobar(priv, a.id, a.por)
    elif a.accion == "enviar":
        enviar(priv, a.id, a.dry_run, a.fuera_de_horario)
    elif a.accion == "eventos":
        eventos(priv, a.id)
    else:
        resumen(priv, a.semana, a.dry_run)


if __name__ == "__main__":
    main()
