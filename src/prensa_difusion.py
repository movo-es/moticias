#!/usr/bin/env python3
"""MOTICIAS · Difusión de notas de prensa con filtro de valor (cambio sala-de-prensa-v1, unido a prensa-y-medios).

No hay una lista ni un motor de envío propios: el plan se guarda como un envío en borrador de la base de prensa
(`prensa_envios` + `prensa_destinatarios`, tipo `nota_de_prensa`, por cuenta del cliente) y se aprueba y envía en la
pestaña «Prensa» del gestor, con el mismo código de envío (Brevo, uno a uno, baja firmada, «No contactar» para siempre).
Aprueban el editor jefe o la oficina si la nota es de un cliente; las de MOTICIAS, solo el editor jefe.

Lo que añade la sala de prensa: las tres puertas (asesor ≥ umbral del plan, relevancia ≥ 3 en los ejes, tope semanal),
el «Por qué le llega» y el aviso a quien aprueba. El resumen semanal a lectores (B2C) lo manda Ghost con su boletín.

Uso (variables de src/bd.py en el entorno):
  python3 -I src/prensa_difusion.py planificar <id> [--plan difusion|difusion-plus]   # crea el borrador y avisa
  python3 -I src/prensa_difusion.py resumen [--semana AAAA-MM-DD] [--dry-run]         # resumen semanal B2C por Ghost
"""
import argparse, datetime, html, json, os, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import prensa_asesor as A  # noqa: E402
import prensa_comun as P  # noqa: E402
import prensa_valor as PV  # noqa: E402
from taxonomia import Taxonomia  # noqa: E402

V = json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))
CFG = V["prensa"]


def por_que(n, an, tx):
    terr = ", ".join(tx.nombre_territorio(t) for t in n["territorios"])
    sm = tx.submodos.get(n["submodo"], (None, {"nombre": n["submodo"]}))[1]["nombre"]
    que = n.get("subtitulo") or (A.frases(n["cuerpo_md"]) or [n["titulo"]])[0]
    return ["Qué: " + que[:220], "A quién afecta: %s · %s" % (sm, terr), "Dato clave: " + ((an.get("cifras_detectadas") or ["—"])[0])]


def url_nota(n, medio="email"):
    base = (n.get("ghost") or {}).get("url") or "%s/%s/" % (V["ghost"]["url"], n["id"])
    return base + "?" + urllib.parse.urlencode({"utm_source": "moticias", "utm_medium": medio, "utm_campaign": "np-" + n["id"]})


def cuerpo_envio(n, lineas, tx):
    """Texto plano para src/prensa.py (_html lo convierte: párrafos y enlaces)."""
    m = CFG["marca"]
    partes = ["%s · %s%s" % (m["etiqueta"].upper(), m["aviso"], (" · " + m["aviso_grupo"]) if n.get("grupo") else ""),
              "POR QUÉ LE LLEGA\n" + "\n".join(lineas),
              n["titulo"].upper() + ("\n" + n["subtitulo"] if n.get("subtitulo") else ""),
              n["organizacion"]["nombre"] + ((" · Embargo hasta " + n["embargo_hasta"]) if n.get("embargo_hasta") else ""),
              n["cuerpo_md"]]
    for k in ("sobre_md", "contacto_prensa_md"):
        if n.get(k):
            partes.append(n[k])
    partes.append("Nota completa y documentos: " + url_nota(n))
    return "\n\n".join(partes)[:19500]


def planificar(nid, plan=None, aviso=True):
    import bd as BD
    n = P.leer_nota(nid)
    ped = P.leer_pedido(nid)
    if not ped:
        raise SystemExit("La nota %s no tiene pedido en la base (prensa_notas)." % nid)
    plan = plan or ped.get("plan")
    planes = {p["id"]: p for p in CFG["planes"]}
    if plan == "bono":
        plan = "difusion"
    if plan not in ("difusion", "difusion-plus"):
        raise SystemExit("El plan %s no incluye difusión." % plan)
    if n.get("status") != "publicada":
        raise SystemExit("Primero se publica la nota en MOTICIAS (src/prensa_publicar.py publicar %s)." % nid)
    if ped.get("envio_id"):
        raise SystemExit("La nota ya tiene el envío %s." % ped["envio_id"])
    tx = Taxonomia()
    an = A.analizar({"titulo": n["titulo"], "subtitulo": n.get("subtitulo"), "organizacion": n["organizacion"]["nombre"],
                     "cuerpo": "\n\n".join(x for x in (n["cuerpo_md"], n.get("sobre_md"), n.get("contacto_prensa_md")) if x)})
    req = planes[plan]["requiere"]
    medios, per, rec = PV.cargar()
    ejes = PV.ejes_de(n)
    lista, fuera = PV.elegir(ejes, medios, per, rec, tx, plan)
    bloqueo = None
    if an["tipo"] == "promocion":
        bloqueo = "es promoción, no una nota de prensa"
    elif an["puntuacion"] < req["puntuacion_min"]:
        bloqueo = "puntuación %d < %d: se devuelve al cliente con los avisos" % (an["puntuacion"], req["puntuacion_min"])
    elif len(lista) < req["destinatarios_min"]:
        bloqueo = "solo %d destinatarios (mínimo %d): no se cobra la difusión" % (len(lista), req["destinatarios_min"])
    asesor = {"puntuacion": an["puntuacion"], "veredicto": an["veredicto"], "tipo": an["tipo"], "ejes": an["ejes"], "fecha": P.ahora()}
    if bloqueo:
        P.guardar_pedido(nid, {"asesor": asesor, "motivo": "Difusión bloqueada: " + bloqueo})
        print("BLOQUEADO:", bloqueo, "· descartes:", fuera)
        return None
    lineas = ped.get("por_que") or por_que(n, an, tx)
    sm = tx.submodos.get(n["submodo"], (None, {"nombre": n["submodo"]}))[1]["nombre"]
    terr = ", ".join(tx.nombre_territorio(t) for t in n["territorios"])
    e = BD.insertar("prensa_envios", {
        "tipo": "nota_de_prensa", "por_cuenta_de": None if ped.get("grupo") else ped.get("cuenta_id"),
        "asunto": ("%s · %s · %s: %s" % (CFG["marca"]["etiqueta"], sm, terr, n["titulo"]))[:200],
        "cuerpo": cuerpo_envio(n, lineas, tx), "pieza_url": url_nota(n),
        "filtro": {"sala_de_prensa": {"nota": nid, "plan": plan, "puntuacion": an["puntuacion"], "ejes": ejes,
                                      "relevancia_min": CFG["filtro_valor"]["relevancia_min_destinatario"], "descartes": fuera}},
        "creado_por": "sala de prensa"})[0]
    for i in range(0, len(lista), 500):
        BD.insertar("prensa_destinatarios", [{"envio_id": e["id"], "persona_id": x["persona_id"], "cuenta_id": x["cuenta_id"], "correo": x["correo"],
                                              "detalle": ("relevancia %s · %s" % (x["relevancia"], x["motivo"]))[:300]} for x in lista[i:i + 500]])
    P.guardar_pedido(nid, {"envio_id": e["id"], "asesor": asesor, "por_que": lineas, "plan": plan})
    BD.registrar("sala de prensa", "prensa_envio_borrador", str(e["id"]), {"nota": nid, "destinatarios": len(lista)})
    print("Borrador %s: %d destinatarios (%d periodistas, %d redacciones) en %d medios · descartes %s" % (
        e["id"], len(lista), sum(1 for x in lista if x["tipo"] == "periodista"), sum(1 for x in lista if x["tipo"] == "redaccion"),
        len({x["cuenta_id"] for x in lista}), fuera))
    if aviso:
        avisar(n, ped, e["id"], len(lista), an["puntuacion"], lineas)
    return e["id"]


def avisar(n, ped, eid, ndest, punt, lineas):
    """Correo a quien puede aprobar: el director y, si la nota es de un cliente, la oficina. Sin aprobación no sale nada."""
    import bd as BD
    import prensa as PR
    para = {V["prensa"]["aviso_director"]}
    if ped.get("cuenta_id") and not ped.get("grupo"):
        for x in BD.leer("equipo", select="email,datos", limit="200"):
            if (x.get("datos") or {}).get("perfil") in ("oficina", "superadmin") and (x.get("datos") or {}).get("estado") != "suspendida":
                para.add(x["email"])
    enlace = "%s/gestor/?envio=%s" % (P.base_app(), eid)
    cuerpo = ("<p><b>Nota de prensa lista para aprobar</b> · %s · %s</p><p>%s</p><p>Asesor: %d/100 · %d destinatarios.</p><p>%s</p>"
              "<p><a href=\"%s\">Revisar y aprobar en el gestor</a> (pestaña Prensa, envío %s). Sin aprobación no sale nada.</p>") % (
        html.escape(n["organizacion"]["nombre"]), html.escape(ped.get("plan") or ""), html.escape(n["titulo"]), punt, ndest,
        "<br>".join(html.escape(x) for x in lineas), enlace, eid)
    try:
        PR._brevo("POST", "/smtp/email", {"sender": PR._remitente(), "to": [{"email": x} for x in sorted(para)],
                                          "subject": "Aprobar difusión: %s" % n["titulo"][:120], "htmlContent": cuerpo, "tags": ["sala-de-prensa"]})
    except Exception as ex:  # noqa: BLE001 — el borrador ya existe; el aviso se reintenta en la siguiente pasada
        print("Aviso no enviado:", ex)


def resumen(semana=None, dry_run=False):
    """Resumen semanal B2C por el boletín «Notas de prensa» de Ghost: un correo por modo de transporte, solo a los
    lectores con la etiqueta np-<modo> (la eligen al darse de alta). Se publica como página de la lista."""
    import ghost_publish as G
    hoy = datetime.date.fromisoformat(semana) if semana else datetime.date.today()
    desde, hasta = (hoy - datetime.timedelta(days=7)).isoformat(), hoy.isoformat()
    notas = [n for n in P.todas_las_notas() if n.get("status") == "publicada" and desde <= (n.get("publicada_en") or "")[:10] < hasta]
    if not notas:
        print("Sin notas publicadas entre %s y %s: no hay resumen." % (desde, hasta))
        return
    tx = Taxonomia()
    g = CFG["ghost"]
    por_modo = {}
    for n in notas:
        por_modo.setdefault(n["modo"], []).append(n)
    key = os.environ.get("GHOST_ADMIN_KEY")
    for modo, ns in sorted(por_modo.items()):
        nombre = tx.modos.get(modo, {}).get("nombre", modo)
        items = "".join('<li><a href="%s">%s</a><br><small>%s · %s</small></li>' % (html.escape(url_nota(n, "newsletter")), html.escape(n["titulo"]),
                        html.escape(n["organizacion"]["nombre"]), html.escape(", ".join(tx.nombre_territorio(t) for t in n["territorios"]))) for n in ns[:12])
        post = {"title": "Notas de prensa de la semana · %s · %s" % (nombre, hoy.strftime("%d-%m-%Y")), "slug": "notas-de-prensa-%s-%s" % (modo, hasta),
                "html": "<p><small>%s</small></p><ul>%s</ul>" % (html.escape(CFG["marca"]["aviso"]), items),
                "tags": [{"name": "Notas de prensa", "slug": g["tag_publica"]}, {"name": g["tag_interna"]}], "featured": False}
        if dry_run or not key:
            print("Simulación" if dry_run else "Falta GHOST_ADMIN_KEY:", post["title"], "→ label:%s%s" % (g["prefijo_label_b2c"], modo), "·", len(ns), "notas")
            continue
        base = os.environ.get("GHOST_URL") or V["ghost"]["url"]
        adm = G.admin_base(base)
        tok = G.ghost_token(key)
        st, r = G.api("POST", "%s/ghost/api/admin/posts/?source=html" % adm, tok, {"posts": [dict(post, status="draft")]})
        if st >= 300:
            print("Ghost no aceptó el resumen de %s: %s" % (modo, str(r)[:200]))
            continue
        p = r["posts"][0]
        q = urllib.parse.urlencode({"newsletter": g["newsletter"], "email_segment": "label:%s%s" % (g["prefijo_label_b2c"], modo)})
        st, r = G.api("PUT", "%s/ghost/api/admin/posts/%s/?%s" % (adm, p["id"], q), G.ghost_token(key),
                      {"posts": [{"status": "published", "updated_at": p["updated_at"]}]})
        print("Resumen %s:" % modo, "enviado" if st < 300 else "error %s" % str(r)[:200])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["planificar", "resumen"])
    ap.add_argument("id", nargs="?")
    ap.add_argument("--plan", choices=["difusion", "difusion-plus"]); ap.add_argument("--semana"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sin-aviso", action="store_true")
    a = ap.parse_args()
    if a.accion == "planificar":
        planificar(a.id, a.plan, not a.sin_aviso)
    else:
        resumen(a.semana, a.dry_run)


if __name__ == "__main__":
    main()
