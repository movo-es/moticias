#!/usr/bin/env python3
"""MOTICIAS · Base de contactos de difusión de la sala de prensa (cambio sala-de-prensa-v1). Solo biblioteca estándar.

Los contactos son datos personales: NUNCA viven en este repositorio (es público). Viven en el repositorio privado
`movo-es/moticias-equipo`, carpeta `prensa/`, fichero `contactos.json`. Los scripts reciben esa carpeta con
`--privado <ruta>` (por defecto $PRENSA_PRIVADO o `work/privado/prensa`). El catálogo de medios (organizaciones,
datos públicos) sí vive aquí: `data/medios/<id>.json`.

Tipos: redaccion · periodista · newsletter · decisor-b2b · profesional · particular
Estados: activo · pendiente-opt-in · pausado · baja · rebotado   (una baja nunca se borra ni se reactiva sola)
Bases: interes-legitimo-prensa (redacciones, periodistas y editores de boletines) · consentimiento (el resto) · contrato

Uso:
  python3 -I src/contactos.py iniciar                                   # crea la base vacía en la carpeta privada
  python3 -I src/contactos.py importar-linkedin Connections.csv [--aplicar]   # sin --aplicar solo enseña qué haría
  python3 -I src/contactos.py alta --email x@y.es --nombre "…" --tipo periodista --medio carrilbus --origen manual
  python3 -I src/contactos.py baja x@y.es [--sector autobus]           # baja total o de un sector
  python3 -I src/contactos.py informe                                   # recuentos por tipo, estado, base y eje
  python3 -I src/contactos.py segmento --submodo autobus --territorio andalucia   # quién recibiría una nota así
"""
import argparse, csv, datetime, glob, hashlib, io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from taxonomia import Taxonomia, plano  # noqa: E402

TIPOS = ("redaccion", "periodista", "newsletter", "decisor-b2b", "profesional", "particular")
ESTADOS = ("activo", "pendiente-opt-in", "pausado", "baja", "rebotado")
B2B = {"redaccion", "periodista", "newsletter", "decisor-b2b", "profesional"}
PRENSA = {"redaccion", "periodista", "newsletter"}
INDIVIDUAL = PRENSA | {"decisor-b2b"}  # reciben la nota suelta; profesionales y particulares, solo el resumen semanal

# Cargo → tipo. Orden: lo más específico primero. Se compara en plano (sin tildes, minúsculas).
CARGOS = [
    ("newsletter", ["newsletter", "boletin"]),
    ("periodista", ["periodista", "redactor", "redactora", "reportero", "reportera", "corresponsal", "jefe de redaccion",
                    "jefa de redaccion", "director de la revista", "directora de la revista", "editor", "editora", "journalist",
                    "reporter", "columnista", "colaborador de", "colaboradora de", "subdirector", "subdirectora", "redaccion"]),
    ("decisor-b2b", ["director", "directora", "gerente", "ceo", "consejero delegado", "consejera delegada", "presidente", "presidenta",
                     "jefe de", "jefa de", "responsable de", "head of", "manager", "concejal", "concejala", "alcalde", "alcaldesa",
                     "secretario general", "secretaria general", "coordinador", "coordinadora", "socio", "socia", "fundador", "fundadora",
                     "founder", "owner", "propietario", "propietaria", "tecnico de movilidad", "tecnica de movilidad", "ingeniero", "ingeniera"]),
]
COMUNICACION = ["comunicacion", "prensa", "relaciones con medios", "relaciones institucionales", "pr manager", "communications", "dircom"]


def ahora():
    return datetime.datetime.now().astimezone().isoformat(timespec="minutes")


def ruta_privada(arg=None):
    return os.path.abspath(arg or os.environ.get("PRENSA_PRIVADO") or os.path.join(ROOT, "work", "privado", "prensa"))


def fichero(privado):
    return os.path.join(privado, "contactos.json")


def vacio():
    return {"nota": "Datos personales. Repositorio privado movo-es/moticias-equipo. Nunca copiar al repositorio público.",
            "actualizado": ahora(), "contactos": []}


def cargar(privado):
    p = fichero(privado)
    if not os.path.exists(p):
        raise SystemExit("No hay base de contactos en %s. Clona movo-es/moticias-equipo y pasa --privado <ruta>/prensa, "
                         "o crea una vacía con `contactos.py iniciar`." % privado)
    return json.load(open(p, encoding="utf-8"))


def guardar(privado, base):
    os.makedirs(privado, exist_ok=True)
    base["actualizado"] = ahora()
    base["contactos"].sort(key=lambda c: (c.get("tipo", ""), c.get("email") or c.get("linkedin") or c.get("id")))
    tmp = fichero(privado) + ".tmp"
    json.dump(base, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, fichero(privado))


def norm_email(e):
    e = (e or "").strip().lower()
    return e if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e) else ""


def cid(email, linkedin=""):
    """Id estable y no reversible a simple vista (no es seguridad: el fichero ya es privado)."""
    return "c-" + hashlib.sha256((norm_email(email) or (linkedin or "").strip().lower()).encode()).hexdigest()[:12]


# ---------- catálogo de medios (público) ----------
def medios():
    out = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "medios", "*.json"))):
        m = json.load(open(p, encoding="utf-8"))
        out[m["id"]] = m
    return out


def medio_por_nombre(nombre, cat):
    """Empresa de LinkedIn → id de medio del catálogo (por nombre, alias o dominio)."""
    n = plano(nombre)
    if not n:
        return None
    for m in cat.values():
        claves = [plano(m["nombre"])] + [plano(a) for a in m.get("alias", [])]
        dom = re.sub(r"^https?://(www\.)?", "", m.get("url", "")).split("/")[0].split(".")[0]
        if dom:
            claves.append(plano(dom))
        if any(k and (k == n or (len(k) > 5 and k in n)) for k in claves):
            return m["id"]
    return None


def medio_por_dominio(email, cat):
    dom = (norm_email(email).split("@") + [""])[1]
    for m in cat.values():
        md = re.sub(r"^https?://(www\.)?", "", m.get("url", "")).split("/")[0]
        if dom and md and (dom == md or dom.endswith("." + md)):
            return m["id"]
    return None


# ---------- clasificación ----------
def tipo_por_cargo(cargo, empresa_es_medio):
    c = " " + plano(cargo) + " "
    if empresa_es_medio:
        for t, claves in CARGOS[:2]:
            if any(" " + k + " " in c for k in claves):
                return t
        return "periodista" if any(k in c for k in ("director", "directora", "editor", "jefe", "jefa")) else "redaccion"
    for t, claves in CARGOS:
        if t == "newsletter":
            continue
        if any(" " + k + " " in c for k in claves):
            if t == "periodista" and not empresa_es_medio and not any(k in c for k in ("periodista", "redactor", "redactora", "journalist", "reporter", "corresponsal")):
                continue  # «editor» o «subdirector» fuera de un medio no es periodista
            return t
    return "profesional"


def intereses_de(tx, texto, medio=None):
    """Intereses en los tres ejes. Si salen del medio, son declarados por el medio; si salen del cargo/empresa, inferidos."""
    if medio:
        return {"submodos": list(medio.get("submodos", [])), "territorios": list(medio.get("territorios", [])),
                "temas": list(medio.get("temas", [])), "inferidos": False, "origen": "medio:" + medio["id"]}
    subs = tx.submodos_en(texto)[:3]
    terr = tx.territorios_en(texto)[:2]
    return {"submodos": subs, "territorios": terr, "temas": tx.temas_en(texto)[:2], "inferidos": True, "origen": "cargo-empresa"}


# ---------- relevancia y elegibilidad ----------
PESOS = {"submodo": 3, "transversal": 2, "modo": 1, "territorio": 2, "estatal": 1, "tema": 1}


def relevancia(c, ejes, tx):
    """Coincidencias entre los ejes de una nota y los intereses de un contacto. Ámbito estatal o UE suma territorio a
    todos; un contacto sin territorios declarados (medio estatal) también. Intereses inferidos pesan la mitad."""
    it = c.get("intereses") or {}
    subs, terrs, temas = set(it.get("submodos", [])), set(it.get("territorios", [])), set(it.get("temas", []))
    modos_c = {tx.submodos[s][0] for s in subs if s in tx.submodos}
    pts, motivos = 0, []
    if ejes.get("submodo") in subs:
        pts += PESOS["submodo"]; motivos.append("sigue " + ejes["submodo"])
    elif "transversal" in subs:
        pts += PESOS["transversal"]; motivos.append("cubre todo el transporte")
    elif ejes.get("modo") in modos_c:
        pts += PESOS["modo"]; motivos.append("sigue el modo " + ejes.get("modo", ""))
    nt = set(ejes.get("territorios", []))
    if nt & terrs:
        pts += PESOS["territorio"]; motivos.append("cubre " + ", ".join(sorted(nt & terrs)))
    elif not terrs or "estado" in terrs or (nt & {"estado", "ue"} and not terrs <= {"internacional"}):
        pts += PESOS["estatal"]; motivos.append("ámbito estatal")
    elif terrs <= {"internacional", "ue"} and not nt & {"estado", "ue", "internacional"}:
        pts -= 2; motivos.append("medio internacional para una noticia autonómica")
    if set(ejes.get("temas", [])) & temas:
        pts += PESOS["tema"]; motivos.append("tema " + ", ".join(sorted(set(ejes["temas"]) & temas)))
    if it.get("inferidos"):
        pts = pts / 2
    return pts, motivos


def envios_semana(c, hoy=None):
    hoy = hoy or datetime.date.today()
    lunes = hoy - datetime.timedelta(days=hoy.weekday())
    return sum(1 for e in c.get("envios", []) if e.get("fecha", "")[:10] >= lunes.isoformat())


def puede_recibir(c, cfg, hoy=None):
    """(sí/no, motivo). Base legal, estado y frecuencia; no mira la relevancia."""
    if c.get("estado") != "activo":
        return False, "estado " + str(c.get("estado"))
    if c.get("base") == "consentimiento" and not (c.get("consentimiento") or {}).get("fecha"):
        return False, "sin consentimiento registrado"
    if c.get("base") not in ("interes-legitimo-prensa", "consentimiento", "contrato"):
        return False, "sin base legal"
    if c.get("base") == "interes-legitimo-prensa" and c.get("tipo") not in PRENSA:
        return False, "interés legítimo solo vale para prensa"
    if not norm_email(c.get("email")):
        return False, "sin correo"
    tope = cfg["max_envios_semana"].get(c.get("tipo"), 1)
    if envios_semana(c, hoy) >= tope:
        return False, "ya recibió %d esta semana (tope %d)" % (envios_semana(c, hoy), tope)
    return True, ""


def elegibles(base, ejes, cfg, tx, tipos=None, hoy=None, excluir_bajas_sector=True):
    out, fuera = [], {}
    rmin = cfg["relevancia_min_destinatario"]
    for c in base["contactos"]:
        if tipos and c.get("tipo") not in tipos:
            continue
        ok, motivo = puede_recibir(c, cfg, hoy)
        if ok and excluir_bajas_sector and ejes.get("submodo") in (c.get("bajas_sector") or []):
            ok, motivo = False, "baja del sector " + ejes["submodo"]
        if ok:
            pts, mot = relevancia(c, ejes, tx)
            if pts >= rmin:
                out.append({"id": c["id"], "tipo": c["tipo"], "relevancia": pts, "motivo": "; ".join(mot)})
                continue
            motivo = "relevancia %.1f < %s" % (pts, rmin)
        fuera[motivo.split(" (")[0]] = fuera.get(motivo.split(" (")[0], 0) + 1
    out.sort(key=lambda d: (-d["relevancia"], d["tipo"]))
    return out, fuera


def recuento(base, ejes, cfg, tx):
    el, fuera = elegibles(base, ejes, cfg, tx)
    por_tipo = {}
    for d in el:
        por_tipo[d["tipo"]] = por_tipo.get(d["tipo"], 0) + 1
    return {"total": len(el), "individual": sum(v for k, v in por_tipo.items() if k in INDIVIDUAL), "resumen_b2c": sum(v for k, v in por_tipo.items() if k not in INDIVIDUAL), "por_tipo": por_tipo, "b2b": sum(v for k, v in por_tipo.items() if k in B2B),
            "prensa": sum(v for k, v in por_tipo.items() if k in PRENSA), "fuera": fuera}


def medios_para(ejes, tx, cat=None, rmin=3):
    """Medios del catálogo que cubren los ejes de una nota (para el recomendador y el informe)."""
    cat = cat or medios()
    out = []
    for m in cat.values():
        pseudo = {"intereses": {"submodos": m.get("submodos", []), "territorios": m.get("territorios", []), "temas": m.get("temas", [])}}
        pts, mot = relevancia(pseudo, ejes, tx)
        if pts >= rmin:
            out.append({"id": m["id"], "nombre": m["nombre"], "tipo": m.get("tipo"), "relevancia": pts, "audiencia": m.get("audiencia")})
    return sorted(out, key=lambda d: -d["relevancia"])


# ---------- altas, bajas e importación ----------
def nuevo(email, nombre, tipo, base_legal, origen, **kw):
    c = {"id": cid(email, kw.get("linkedin", "")), "email": norm_email(email), "nombre": nombre.strip(), "tipo": tipo,
         "base": base_legal, "origen": origen, "creado": ahora(), "estado": kw.pop("estado", "activo"),
         "intereses": kw.pop("intereses", {"submodos": [], "territorios": [], "temas": [], "inferidos": True}),
         "envios": [], "sin_abrir_seguidos": 0, "bajas_sector": []}
    c.update({k: v for k, v in kw.items() if v not in (None, "")})
    return c


def fusionar(base, c):
    """Añade o actualiza sin pisar lo que decidió el contacto: una baja sigue siendo baja; el consentimiento no se borra."""
    for i, x in enumerate(base["contactos"]):
        if x["id"] == c["id"] or (c.get("email") and x.get("email") == c["email"]):
            for k, v in c.items():
                if k in ("estado", "base", "consentimiento", "envios", "bajas_sector", "creado", "id"):
                    continue
                if v and not x.get(k):
                    x[k] = v
            if x.get("estado") == "pendiente-opt-in" and c.get("estado") == "activo" and c.get("base") == "consentimiento":
                x["estado"], x["base"], x["consentimiento"] = "activo", "consentimiento", c.get("consentimiento")
            return "actualizado"
    base["contactos"].append(c)
    return "nuevo"


def leer_linkedin(ruta):
    """Connections.csv de la exportación oficial de LinkedIn. Trae unas líneas de «Notes:» antes de la cabecera."""
    raw = open(ruta, encoding="utf-8-sig", errors="replace").read()
    i = raw.find("First Name")
    filas = csv.DictReader(io.StringIO(raw[i:] if i >= 0 else raw))
    for f in filas:
        yield {"nombre": ("%s %s" % (f.get("First Name", ""), f.get("Last Name", ""))).strip(), "linkedin": f.get("URL", "").strip(),
               "email": f.get("Email Address", "").strip(), "empresa": f.get("Company", "").strip(), "cargo": f.get("Position", "").strip(),
               "conectado": f.get("Connected On", "").strip()}


def clasificar_linkedin(fila, cat, tx):
    mid = medio_por_nombre(fila["empresa"], cat) or (medio_por_dominio(fila["email"], cat) if fila["email"] else None)
    tipo = tipo_por_cargo(fila["cargo"], bool(mid))
    comunicacion = any(k in plano(fila["cargo"]) for k in COMUNICACION)
    intereses = intereses_de(tx, fila["empresa"] + " " + fila["cargo"], cat.get(mid))
    if tipo in PRENSA and norm_email(fila["email"]):
        estado, base_legal = "activo", "interes-legitimo-prensa"
    else:
        estado, base_legal = "pendiente-opt-in", "consentimiento"
    return nuevo(fila["email"], fila["nombre"], tipo, base_legal, "linkedin-export", estado=estado, intereses=intereses,
                 linkedin=fila["linkedin"], organizacion=fila["empresa"], cargo=fila["cargo"], medio=mid,
                 dircom=comunicacion or None, conectado_linkedin=fila["conectado"], informado_art14=False)


def informe(base, tx):
    from collections import Counter
    cs = base["contactos"]
    print("Contactos: %d (actualizado %s)" % (len(cs), base.get("actualizado")))
    for campo in ("tipo", "estado", "base", "origen"):
        print("  %-8s %s" % (campo, dict(Counter(c.get(campo) for c in cs))))
    subs = Counter(s for c in cs if c.get("estado") == "activo" for s in (c.get("intereses") or {}).get("submodos", []))
    terr = Counter(t for c in cs if c.get("estado") == "activo" for t in (c.get("intereses") or {}).get("territorios", []))
    print("  activos por submodo:", dict(subs.most_common()))
    print("  activos por territorio:", dict(terr.most_common()))
    print("  dircom (cargo de comunicación, clientes potenciales):", sum(1 for c in cs if c.get("dircom")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["iniciar", "importar-linkedin", "alta", "baja", "informe", "segmento"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--privado")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--email"); ap.add_argument("--nombre", default=""); ap.add_argument("--tipo", choices=TIPOS)
    ap.add_argument("--medio"); ap.add_argument("--cargo"); ap.add_argument("--organizacion"); ap.add_argument("--origen", default="manual")
    ap.add_argument("--consentimiento", help="texto o referencia del consentimiento (obligatorio salvo prensa)")
    ap.add_argument("--submodo", nargs="*", default=[]); ap.add_argument("--territorio", nargs="*", default=[]); ap.add_argument("--tema", nargs="*", default=[])
    ap.add_argument("--sector")
    a = ap.parse_args()
    priv = ruta_privada(a.privado)
    tx = Taxonomia()
    cfg = json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))["prensa"]["filtro_valor"]

    if a.accion == "iniciar":
        if os.path.exists(fichero(priv)):
            sys.exit("Ya existe %s: no se toca." % fichero(priv))
        guardar(priv, vacio())
        print("Base vacía creada en", fichero(priv))
        return
    base = cargar(priv)
    cat = medios()
    if a.accion == "importar-linkedin":
        from collections import Counter
        res, tipos, est = Counter(), Counter(), Counter()
        for fila in leer_linkedin(a.arg):
            if not fila["nombre"]:
                continue
            c = clasificar_linkedin(fila, cat, tx)
            tipos[c["tipo"]] += 1; est[c["estado"]] += 1
            res[fusionar(base, c) if a.aplicar else "simulado"] += 1
        print("LinkedIn:", dict(res), "· tipos:", dict(tipos), "· estados:", dict(est))
        print("Los «pendiente-opt-in» NO recibirán notas hasta darse de alta (docs/prensa/legal-contactos.md).")
        if a.aplicar:
            guardar(priv, base)
        else:
            print("Simulación: repite con --aplicar para guardar.")
    elif a.accion == "alta":
        if not norm_email(a.email) or not a.tipo:
            sys.exit("Hacen falta --email válido y --tipo.")
        prensa = a.tipo in PRENSA
        if not prensa and not a.consentimiento:
            sys.exit("Un %s solo entra con consentimiento: indica --consentimiento." % a.tipo)
        m = cat.get(a.medio) if a.medio else None
        it = intereses_de(tx, "", m) if m else {"submodos": a.submodo, "territorios": a.territorio, "temas": a.tema, "inferidos": False, "origen": "declarado"}
        c = nuevo(a.email, a.nombre, a.tipo, "interes-legitimo-prensa" if prensa else "consentimiento", a.origen, intereses=it,
                  medio=a.medio, cargo=a.cargo, organizacion=a.organizacion,
                  consentimiento={"fecha": ahora(), "texto": a.consentimiento} if a.consentimiento else None)
        print(fusionar(base, c), c["id"])
        guardar(priv, base)
    elif a.accion == "baja":
        e = norm_email(a.arg)
        for c in base["contactos"]:
            if c.get("email") == e:
                if a.sector:
                    c.setdefault("bajas_sector", []).append(a.sector)
                else:
                    c["estado"], c["baja_en"] = "baja", ahora()
                guardar(priv, base)
                print("Baja registrada:", e, a.sector or "(total)")
                return
        sys.exit("No está en la base: " + e)
    elif a.accion == "informe":
        informe(base, tx)
    elif a.accion == "segmento":
        sub = (a.submodo or ["transversal"])[0]
        ejes = {"submodo": sub, "modo": tx.submodos.get(sub, ("transversal",))[0], "territorios": a.territorio or ["estado"], "temas": a.tema}
        print(json.dumps(recuento(base, ejes, cfg, tx), ensure_ascii=False, indent=1))
        print("Medios del catálogo:", [m["nombre"] for m in medios_para(ejes, tx, cat)])


if __name__ == "__main__":
    main()
