#!/usr/bin/env python3
"""MOTICIAS · Barrido del BOE por la API de datos abiertos.

  python3 -I src/boe_sweep.py AAAA-MM-DD [AAAA-MM-DD ...]        un día o varios
  python3 -I src/boe_sweep.py --desde AAAA-MM-DD --hasta AAAA-MM-DD
  Opciones: --json FICHERO (vuelca los candidatos), --todo (no filtra por departamento ni palabras clave)

Para cada día pide el sumario (https://www.boe.es/datosabiertos/api/boe/sumario/AAAAMMDD, Accept: application/json),
recorre secciones, departamentos y epígrafes, y devuelve los ítems de transporte de viajeros con:
  fecha, boletin (número), referencia, seccion_codigo, organo, titulo, tipo, modos, url, pdf.
También calcula la serie diaria para el gráfico (`total`, `lic`, `disp`).

Reglas de clasificación (ver docs/manual-operativo.md § 6):
- «línea aérea de contacto» es catenaria → tierra; «Bus Nàutic» es marítimo; «aeródromo», «aeropuerto», «Aena», «AESA», «ENAIRE» → aire.
- Departamentos: Transportes y Movilidad Sostenible siempre; Interior y Hacienda solo si tocan viajeros; Asuntos Exteriores para convenios de transporte.
El texto de un ítem: https://www.boe.es/diario_boe/xml.php?id=BOE-X-2026-NNNNN (el cuerpo es el ÚLTIMO elemento <texto>).
El BOE del día sale entre las 07:00 y las 07:30; si la API devuelve 404, reintentar cada cinco minutos hasta las 07:50. Domingos y festivos no hay BOE.
"""
import argparse, datetime, json, re, sys, urllib.request, urllib.error

API = "https://www.boe.es/datosabiertos/api/boe/sumario/%s"
UA = "Moticias/1.0 (rainerup@gmail.com)"

KEYWORDS = ["transporte", "viajero", "ferroviari", "adif", "renfe", "autobús", "autobus", "autocar", "concesión", "concesion",
            "aeropuerto", "aena", "aéreo", "aereo", "aeronáutic", "aeronautic", "navegación", "navegacion", "puerto", "portuari",
            "marítim", "maritim", "movilidad", "tráfico", "trafico", "dgt", "taxi", "vtc", "conductor", "peaje", "carretera",
            "autovía", "autovia", "estación", "estacion", "línea", "linea", "buque", "practicaje", "cercanías", "cercanias",
            "alta velocidad", "metro", "tranvía", "tranvia", "pasajero", "aerolínea", "aerolinea", "enaire", "aesa", "salvamento marítimo"]
DEPTS_ALWAYS = ["transportes y movilidad sostenible", "transportes, movilidad"]
DEPTS_MAYBE = ["interior", "hacienda", "asuntos exteriores", "presidencia", "jefatura del estado", "cortes generales",
               "comisión nacional de los mercados", "universidades", "trabajo", "industria", "transición ecológica"]
MAR = ["bus nàutic", "bus nautic", "puerto", "portuari", "marítim", "maritim", "navegación", "navegacion", "buque", "practicaje",
       "naval", "marina mercante", "salvamento", "stcw", "ferry", "remolque", "amarre", "estación marítima"]
AIRE = ["aeropuerto", "aena", "aéreo", "aereo", "aeronáutic", "aeronautic", "aerolínea", "aerolinea", "enaire", "aesa", "aeródromo",
        "aerodromo", "aviación", "aviacion", "aeronave", "helipuerto", "navegación aérea", "navegacion aerea", "drone", "aeródromo"]
TIERRA = ["ferroviari", "adif", "renfe", "autobús", "autobus", "autocar", "carretera", "autovía", "autovia", "tráfico", "trafico",
          "dgt", "taxi", "vtc", "conductor", "peaje", "estación", "estacion", "cercanías", "cercanias", "alta velocidad", "metro",
          "tranvía", "tranvia", "línea aérea de contacto", "linea aerea de contacto", "catenaria", "vía férrea", "via ferrea", "túnel", "tunel",
          "paso a nivel", "andén", "anden", "locomotora", "material rodante", "ertms", "tacógrafo", "tacografo", "permiso de conducción"]
EXCLUDE_ORGS = ["confederación hidrográfica", "intendente de", "comandancia", "jefatura de asuntos económicos", "seguridad alimentaria",
                "sanidad de la producción", "consejo superior de investigaciones", "tgss", "tesorería general"]
STRONG = ["adif", "renfe", "aena", "enaire", "autoridad portuaria", "puertos del estado", "transporte", "viajeros", "ferroviari", "aeropuerto",
          "marina mercante", "carreteras del estado", "dirección general de tráfico", "autobús", "autobus", "autocar", "navegación aérea"]
LIC_TYPES = ["anuncio de licitación", "anuncio de formalización", "formalización de contrato", "licitación", "formalización"]


def fetch(url, accept="application/json", retries=1):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": UA})
    for i in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, b""
        except Exception as e:  # noqa
            if i == retries:
                return 0, str(e).encode()
    return 0, b""


def aslist(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def walk(data):
    """Recorre el sumario y produce (seccion, departamento, epigrafe, item) con la estructura real de la API."""
    for diario in aslist(data.get("data", {}).get("sumario", {}).get("diario")):
        for sec in aslist(diario.get("seccion")):
            for dep in aslist(sec.get("departamento")):
                for ep in aslist(dep.get("epigrafe")) or [None]:
                    holder = ep if ep is not None else dep
                    for it in aslist(holder.get("item")):
                        yield sec, dep, ep or {}, it, diario.get("numero")


def norm(s):
    return (s or "").lower()


def classify_modes(text):
    t = norm(text)
    modes = set()
    if "línea aérea de contacto" in t or "linea aerea de contacto" in t:
        modes.add("tierra")
        t = t.replace("línea aérea de contacto", "").replace("linea aerea de contacto", "")
    if any(k in t for k in MAR):
        modes.add("mar")
    if any(k in t for k in AIRE):
        modes.add("aire")
    if any(k in t for k in TIERRA):
        modes.add("tierra")
    if not modes:
        modes.add("transversal")
    return sorted(modes)


def classify_type(title, section):
    t = norm(title)
    if t.startswith("ley orgánica") or t.startswith("ley "):
        return "ley"
    if t.startswith("real decreto-ley"):
        return "real decreto-ley"
    if t.startswith("real decreto legislativo"):
        return "real decreto legislativo"
    if t.startswith("real decreto"):
        return "real decreto"
    if t.startswith("orden"):
        return "orden"
    if "formalización" in t:
        return "formalización"
    if "anuncio de licitación" in t or "licitación" in t:
        return "anuncio de licitación"
    if "concesión" in t and ("concurso" in t or "otorgamiento" in t):
        return "concesión"
    if "información pública" in t:
        return "información pública"
    if "convenio" in t:
        return "convenio"
    if t.startswith("resolución") or t.startswith("acuerdo"):
        return "resolución"
    if section.startswith("5"):
        return "anuncio"
    return "disposición"


def sweep_day(day, todo=False):
    ymd = day.strftime("%Y%m%d")
    status, body = fetch(API % ymd)
    if status == 404:
        return {"date": day.isoformat(), "status": 404, "items": [], "serie": None}
    if status != 200:
        return {"date": day.isoformat(), "status": status, "items": [], "serie": None, "error": body[:200].decode(errors="replace")}
    data = json.loads(body)
    items, total, lic, disp = [], 0, 0, 0
    boletin = None
    for seccion, depto, epig, it, numero in walk(data):
        boletin = boletin or numero
        sec_code = str(seccion.get("codigo") or "")
        sec_name = seccion.get("nombre") or ""
        dep_name = depto.get("nombre") or ""
        title = it.get("titulo") or ""
        ref = it.get("identificador") or ""
        hay = norm(" ".join([dep_name, epig.get("nombre") or "", title]))
        is_transport_dept = any(d in norm(dep_name) for d in DEPTS_ALWAYS)
        kw = any(k in hay for k in KEYWORDS)
        strong = any(k in hay for k in STRONG)
        excluded = any(o in hay for o in EXCLUDE_ORGS) and not strong
        keep = todo or ((is_transport_dept or (any(d in norm(dep_name) for d in DEPTS_MAYBE) and kw) or (sec_code.startswith("5") and kw)) and not excluded)
        if not keep:
            continue
        tipo = classify_type(title, sec_code)
        total += 1
        if tipo in ("anuncio de licitación", "formalización"):
            lic += 1
        elif not sec_code.startswith("5"):
            disp += 1
        items.append({
            "fecha": day.isoformat(), "boletin": "BOE", "numero": boletin, "referencia": ref, "seccion_codigo": sec_code,
            "seccion": sec_name, "organo": dep_name, "epigrafe": epig.get("nombre") or "", "titulo": title, "tipo": tipo,
            "modos": classify_modes(hay), "url": "https://www.boe.es/diario_boe/txt.php?id=%s" % ref,
            "pdf": (it.get("url_pdf") or {}).get("texto") if isinstance(it.get("url_pdf"), dict) else it.get("url_pdf"),
        })
    return {"date": day.isoformat(), "status": 200, "numero": boletin, "items": items,
            "serie": {"total": total, "lic": lic, "disp": disp}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dias", nargs="*")
    ap.add_argument("--desde")
    ap.add_argument("--hasta")
    ap.add_argument("--json")
    ap.add_argument("--todo", action="store_true")
    a = ap.parse_args()
    days = [datetime.date.fromisoformat(d) for d in a.dias]
    if a.desde:
        d0 = datetime.date.fromisoformat(a.desde)
        d1 = datetime.date.fromisoformat(a.hasta) if a.hasta else datetime.date.today()
        while d0 <= d1:
            days.append(d0)
            d0 += datetime.timedelta(days=1)
    if not days:
        ap.error("indica días o --desde/--hasta")
    out = [sweep_day(d, a.todo) for d in days]
    for r in out:
        print("%s · BOE %s · estado %s · %d candidatos · serie %s" % (r["date"], r.get("numero"), r["status"], len(r["items"]), r["serie"]), file=sys.stderr)
        for it in r["items"]:
            print("  %s [%s] %s · %s" % (it["referencia"], ",".join(it["modos"]), it["tipo"], it["titulo"][:110]), file=sys.stderr)
    if a.json:
        json.dump(out, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    else:
        json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
