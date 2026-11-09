#!/usr/bin/env python3
"""MOTICIAS · Sala de prensa: filtro de valor sobre la base de prensa (cambio sala-de-prensa-v1 unido a prensa-y-medios).

Los destinatarios NO tienen una lista propia: son los medios y periodistas de la base privada (Supabase «moticias»,
migración 005_prensa_medios, `src/prensa.py`). Este módulo decide, para una nota con sus tres ejes (modo · tema ·
territorio), quién la recibe y por qué, con tres puertas (design.md § 4):

  1. la nota supera el umbral del asesor para su plan (lo comprueba prensa_difusion.py);
  2. relevancia ≥ 3 entre los ejes de la nota y los ámbitos, alcance y región del medio;
  3. nadie pasa de su tope semanal de notas, y fuera quien está en «No contactar», archivado o es «poco colaborador».

Las funciones puras (relevancia, elegir) trabajan sobre listas ya leídas, para poder probarlas sin la base;
`cargar()` las lee con src/bd.py (variables de Vercel o de la tarea: las de src/bd.py).

Uso:
  python3 -I src/prensa_valor.py segmento --submodo autobus --territorio andalucia [--plan difusion-plus]
  python3 -I src/prensa_valor.py linkedin Connections.csv > work/prensa/linkedin.json   # para `src/prensa.py sql`
"""
import argparse, csv, datetime, io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from taxonomia import Taxonomia, plano  # noqa: E402

V = json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))
CFG = V["prensa"]["filtro_valor"]

# Ejes de MOTICIAS → ámbitos de la base de prensa (src/prensa.py AMBITOS)
SUBMODO_AMBITO = {"autobus": "autobus", "urbano": "movilidad", "carretera": "movilidad", "ferrocarril": "ferrocarril",
                  "aerolineas": "aereo", "aeropuertos": "aereo", "maritimo": "maritimo", "puertos": "maritimo",
                  "logistica-tierra": "logistica", "logistica-mar": "logistica", "logistica-aire": "logistica", "transversal": "movilidad"}
GENERICOS = {"tierra": {"movilidad", "viajeros"}, "mar": {"viajeros", "movilidad"}, "aire": {"viajeros", "turismo"},
             "logistica": {"logistica"}, "transversal": {"movilidad", "viajeros"}}
TEMA_AMBITO = {"infraestructuras": "infraestructuras", "tecnologia": "tecnologia", "regulacion": "administracion",
               "concesiones": "administracion", "empresas": "economia"}
GENERALISTAS = {"generalista", "economico", "regional", "agencia", "radio_tv"}
NOTAS = ("nota_de_prensa", "comunicado")


def ejes_de(n):
    return {"submodo": n["submodo"], "modo": n["modo"], "territorios": list(n["territorios"]), "temas": list(n.get("temas") or [])}


def territorio_medio(m, tx):
    """CCAA del medio a partir de su región o ciudad (texto libre de la base)."""
    return set(tx.territorios_en("%s %s" % (m.get("region") or "", m.get("ciudad") or ""), solo_ccaa=True))


def relevancia(m, ejes, tx, plan="difusion"):
    """Puntos y motivos de un medio para una nota. Un medio regional de otra comunidad queda fuera (−10)."""
    amb = set(m.get("ambitos") or [])
    pts, mot = 0, []
    exacto = SUBMODO_AMBITO.get(ejes["submodo"])
    if exacto and exacto in amb and ejes["submodo"] != "transversal":
        pts += 3; mot.append("cubre " + exacto)
    elif amb & GENERICOS.get(ejes["modo"], set()):
        pts += 2; mot.append("cubre " + ", ".join(sorted(amb & GENERICOS[ejes["modo"]])))
    elif plan == "difusion-plus" and m.get("tipo_medio") in GENERALISTAS:
        pts += 2; mot.append("medio %s (Difusión Plus)" % m.get("tipo_medio"))
    t_amb = {TEMA_AMBITO[t] for t in ejes.get("temas", []) if t in TEMA_AMBITO}
    if amb & t_amb:
        pts += 1; mot.append("tema " + ", ".join(sorted(amb & t_amb)))
    nt = set(ejes["territorios"])
    alc = m.get("alcance")
    if alc in ("autonomico", "provincial", "local"):
        tm = territorio_medio(m, tx)
        if tm & nt:
            pts += 2; mot.append("medio de " + ", ".join(sorted(tm & nt)))
        else:
            pts -= 10; mot.append("medio regional de otra comunidad")
    elif alc == "internacional":
        if nt & {"estado", "ue", "internacional"}:
            pts += 1; mot.append("ámbito internacional")
        else:
            pts -= 2; mot.append("medio internacional para una noticia autonómica")
    else:  # nacional o sin dato
        pts += 1; mot.append("ámbito estatal")
    return pts, mot


def elegir(ejes, medios, periodistas, recientes, tx, plan="difusion"):
    """medios: filas de medios_hoy; periodistas: filas de periodistas_hoy; recientes: {correo: nº de notas en 7 días}.
    Devuelve (destinatarios con motivo, recuento de descartes por motivo)."""
    rmin = CFG["relevancia_min_destinatario"]
    tope_p, tope_b = CFG["max_envios_semana"]["periodista"], CFG["max_envios_semana"]["redaccion"]
    out, fuera, vistos = [], {}, set()

    def no(motivo):
        fuera[motivo] = fuera.get(motivo, 0) + 1

    por_medio = {}
    for p in periodistas:
        por_medio.setdefault(p.get("cuenta_id"), []).append(p)
    for m in medios:
        if m.get("archivada_at"):
            continue
        if m.get("colaboracion") == "poco_colaborador":
            no("medio poco colaborador"); continue
        pts, mot = relevancia(m, ejes, tx, plan)
        if pts < rmin:
            no("relevancia < %d" % rmin); continue
        base = {"cuenta_id": m["id"], "medio": m.get("nombre"), "relevancia": pts, "motivo": "; ".join(mot),
                "importancia": m.get("importancia") or 0, "prob": m.get("prob_publicacion")}
        for p in por_medio.get(m["id"], []):
            c = (p.get("correo") or "").lower()
            if not c or p.get("no_contactar_at") or p.get("archivada_at"):
                no("periodista sin correo o en «No contactar»"); continue
            if p.get("colaboracion") == "poco_colaborador":
                no("periodista poco colaborador"); continue
            if c in vistos:
                continue
            if recientes.get(c, 0) >= tope_p:
                no("tope semanal"); continue
            vistos.add(c)
            out.append(dict(base, persona_id=p["id"], correo=c, nombre=p.get("nombre"), tipo="periodista"))
        buzon = (m.get("correo_notas") or m.get("correo_redaccion") or "").lower()
        if buzon and buzon not in vistos and m.get("acepta_notas") is not False:
            if recientes.get(buzon, 0) >= tope_b:
                no("tope semanal")
            else:
                vistos.add(buzon)
                out.append(dict(base, persona_id=None, correo=buzon, nombre=None, tipo="redaccion"))
    out.sort(key=lambda d: (-d["relevancia"], -(d["importancia"] or 0), d["medio"] or ""))
    return out, fuera


# ---------- lectura de la base ----------
def cargar(ejes=None):
    import bd as BD
    if not BD.configurada():
        raise RuntimeError("base de prensa no configurada (variables de src/bd.py)")
    medios = BD.leer("medios_hoy", select="id,nombre,dominio,web,tipo_medio,alcance,ambitos,region,ciudad,colaboracion,importancia,"
                                           "prob_publicacion,acepta_notas,correo_notas,correo_redaccion,audiencia,archivada_at",
                     archivada_at="is.null", limit="2000")
    per = BD.leer("periodistas_hoy", select="id,cuenta_id,nombre,correo,colaboracion,no_contactar_at,archivada_at", archivada_at="is.null", limit="10000")
    desde = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    rec = {}
    for r in BD.leer("prensa_destinatarios", select="correo,prensa_envios!inner(tipo)", at="gte." + desde,
                     **{"prensa_envios.tipo": "in.(%s)" % ",".join(NOTAS)}, limit="20000"):
        c = (r.get("correo") or "").lower()
        rec[c] = rec.get(c, 0) + 1
    return medios, per, rec


def recuento(ejes, plan="difusion", tx=None):
    """Para el recomendador: cuántos destinatarios pasan los filtros. None si la base no está disponible."""
    tx = tx or Taxonomia()
    try:
        medios, per, rec = cargar(ejes)
    except Exception:  # noqa: BLE001 — sin base, el recomendador lo dice en vez de inventar
        return None
    el, fuera = elegir(ejes, medios, per, rec, tx, plan)
    n_medios = len({d["cuenta_id"] for d in el})
    return {"individual": len(el), "prensa": len(el), "periodistas": sum(1 for d in el if d["tipo"] == "periodista"),
            "redacciones": sum(1 for d in el if d["tipo"] == "redaccion"), "medios": n_medios, "resumen_b2c": None, "fuera": fuera,
            "nombres_medios": sorted({d["medio"] for d in el})[:40]}


# ---------- LinkedIn → fichero para `src/prensa.py sql` ----------
ROLES = [("editor_newsletter", ["newsletter", "boletin"]), ("director", ["director", "directora", "editor jefe", "editora jefa"]),
         ("redactor_jefe", ["redactor jefe", "redactora jefa", "jefe de redaccion", "jefa de redaccion"]),
         ("jefe_seccion", ["jefe de seccion", "jefa de seccion"]), ("corresponsal", ["corresponsal"]),
         ("freelance", ["freelance", "autonomo", "autonoma"]), ("colaborador", ["colaborador", "colaboradora", "columnista"]),
         ("redactor", ["redactor", "redactora", "periodista", "reporter", "journalist", "reportero", "reportera", "editor", "editora"])]


def leer_linkedin(ruta):
    raw = open(ruta, encoding="utf-8-sig", errors="replace").read()
    i = raw.find("First Name")
    for f in csv.DictReader(io.StringIO(raw[i:] if i >= 0 else raw)):
        yield {"nombre": ("%s %s" % (f.get("First Name", ""), f.get("Last Name", ""))).strip(), "linkedin": (f.get("URL") or "").strip(),
               "correo": (f.get("Email Address") or "").strip().lower(), "empresa": (f.get("Company") or "").strip(),
               "cargo": (f.get("Position") or "").strip(), "conectado": (f.get("Connected On") or "").strip()}


def rol_de(cargo):
    c = " " + plano(cargo) + " "
    for rol, claves in ROLES:
        if any(" " + k + " " in c for k in claves):
            return rol
    return None


def linkedin_a_base(filas, medios):
    """Solo periodistas de medios que YA están en la base (por nombre o dominio de correo): la web identifica al medio.
    Los demás contactos no entran en la base de prensa; se devuelven aparte (los de comunicación son clientes potenciales)."""
    idx = {}
    for m in medios:
        for k in {plano(m.get("nombre") or ""), (m.get("dominio") or "").split(".")[0]}:
            if len(k) > 3:
                idx[k] = m
    hoy = datetime.date.today().isoformat()
    por_medio, otros = {}, {"comunicacion": [], "sin_medio": 0, "sin_rol": 0}
    for f in filas:
        dom = f["correo"].split("@")[1] if "@" in f["correo"] else ""
        m = idx.get(plano(f["empresa"])) or next((v for k, v in idx.items() if dom and v.get("dominio") and (dom == v["dominio"] or dom.endswith("." + v["dominio"]))), None)
        rol = rol_de(f["cargo"])
        if any(k in plano(f["cargo"]) for k in ("comunicacion", "prensa", "dircom", "communications")) and not m:
            otros["comunicacion"].append({"nombre": f["nombre"], "empresa": f["empresa"], "cargo": f["cargo"], "linkedin": f["linkedin"]})
            continue
        if not m:
            otros["sin_medio"] += 1; continue
        if not rol:
            otros["sin_rol"] += 1; continue
        p = {"nombre": f["nombre"], "cargo": f["cargo"][:160], "rol": rol, "linkedin": f["linkedin"] or None,
             "fuentes": ["LinkedIn: contacto de primer grado de Rainer Uphoff, exportación oficial del %s" % hoy]}
        if f["correo"]:
            p["correo"] = f["correo"]
        por_medio.setdefault(m["id"], {"nombre": m["nombre"], "web": m.get("web") or ("https://" + m["dominio"]), "periodistas": []})["periodistas"].append(p)
    return {"medios": list(por_medio.values())}, otros


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["segmento", "linkedin"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--submodo", default="transversal"); ap.add_argument("--territorio", nargs="*", default=["estado"])
    ap.add_argument("--tema", nargs="*", default=[]); ap.add_argument("--plan", default="difusion")
    a = ap.parse_args()
    tx = Taxonomia()
    if a.accion == "segmento":
        ejes = {"submodo": a.submodo, "modo": tx.submodos.get(a.submodo, ("transversal",))[0], "territorios": a.territorio, "temas": a.tema}
        print(json.dumps(recuento(ejes, a.plan, tx), ensure_ascii=False, indent=1))
    else:
        medios, _, _ = cargar()
        dato, otros = linkedin_a_base(list(leer_linkedin(a.arg)), medios)
        print(json.dumps(dato, ensure_ascii=False, indent=1))
        print("Periodistas de medios de la base: %d · contactos de comunicación (clientes potenciales, NO entran): %d · sin medio en la base: %d · sin cargo de prensa: %d"
              % (sum(len(m["periodistas"]) for m in dato["medios"]), len(otros["comunicacion"]), otros["sin_medio"], otros["sin_rol"]), file=sys.stderr)


if __name__ == "__main__":
    main()
