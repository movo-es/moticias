#!/usr/bin/env python3
"""MOTICIAS · Agenda de eventos (ferias, congresos, jornadas) — cambio OpenSpec `agenda-de-eventos` (16-11-2026).

Colección `data/eventos/<inicio>-<slug>.json`, un evento por fichero, separada de `data/agenda/` (los plazos de la
edición diaria). Temas, colores, formatos, modalidades y estados viven en `verticals/movilidad.json → agenda`; aquí
solo hay reglas. Nada de nombres de personas, correos ni teléfonos en estos ficheros: eso va a la base privada.

  python3 -I src/eventos.py validar [--dir data/eventos] [fichero ...]
  python3 -I src/eventos.py listar [--desde AAAA-MM-DD] [--hasta AAAA-MM-DD] [--estado publicado]
  python3 -I src/eventos.py alta --json evento.json        valida y escribe data/eventos/<id>.json
  python3 -I src/eventos.py pasar-a-pasado [--hoy AAAA-MM-DD]   lo terminado pasa a `pasado` (no se borra)
"""
import argparse, calendar, datetime, glob, json, os, re, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "data", "eventos")
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MES = re.compile(r"^\d{4}-\d{2}$")
ID_OK = re.compile(r"^\d{4}-\d{2}(-\d{2})?-[a-z0-9]+(-[a-z0-9]+)*$")
URL_OK = re.compile(r"^https?://[^\s]+$")
# Nada personal en el repositorio (es público): ni correos ni teléfonos en ningún campo de texto.
CORREO = re.compile(r"[^\s@]+@[^\s@]+\.[a-z]{2,}", re.I)
TELEFONO = re.compile(r"(\+\d{1,3}[\s.-]?)?\b\d{2,3}[\s.-]?\d{3}[\s.-]?\d{2,3}[\s.-]?\d{2,3}\b")
CAMPOS = ("id", "titulo", "titulo_corto", "inicio", "fin", "mes_previsto", "tema", "formato", "modalidad", "publico", "ciudad",
          "sede", "territorio", "geo", "resumen", "organizadores", "url_inscripcion", "url_oficial", "precio", "nota", "estado",
          "origen", "fuentes", "comprobado_at", "revised_at", "revisiones", "destacado", "ghost")


def vertical():
    return json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))


def cfg(v=None):
    return (v or vertical())["agenda"]


def territorios(v=None):
    return {t["id"]: t for t in (v or vertical())["taxonomia"]["territorios"]}


def slug(t, n=60):
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:n].rstrip("-") or "evento"


def hoy():
    return datetime.date.today().isoformat()


def mas_meses(fecha, n):
    d = datetime.date.fromisoformat(fecha)
    m = d.month - 1 + n
    a, m = d.year + m // 12, m % 12 + 1
    return datetime.date(a, m, min(d.day, calendar.monthrange(a, m)[1])).isoformat()


def palabras(t):
    return len(re.findall(r"\S+", str(t or "")))


def fin_de(e):
    return e.get("fin") or e.get("inicio")


def meses_de(e):
    """Meses (AAAA-MM) que toca un evento: una cita que cruza dos meses cuenta en los dos."""
    if not e.get("inicio"):
        return [e["mes_previsto"]] if e.get("mes_previsto") else []
    a, b = e["inicio"][:7], fin_de(e)[:7]
    out, m = [], a
    while m <= b and len(out) < 24:
        out.append(m)
        y, mm = int(m[:4]), int(m[5:])
        m = "%04d-%02d" % (y + (mm == 12), mm % 12 + 1)
    return out


def _texto_personal(e):
    malos = []
    for k, val in e.items():
        if k in ("fuentes", "url_inscripcion", "url_oficial", "geo", "ghost"):
            continue
        for s in (val if isinstance(val, list) else [val]):
            if isinstance(s, str) and (CORREO.search(s) or TELEFONO.search(s)):
                malos.append(k)
    return sorted(set(malos))


def validar(e, v=None, nombre=None):
    """Lista de errores (vacía si vale). `nombre`: nombre del fichero sin .json, que debe ser el id."""
    v = v or vertical()
    c, ter = cfg(v), territorios(v)
    err = []
    temas = {t["id"] for t in c["temas"]}
    if not isinstance(e, dict):
        return ["no es un objeto JSON"]
    for k in e:
        if k not in CAMPOS:
            err.append("campo desconocido: %s" % k)
    i = e.get("id") or ""
    if not ID_OK.match(i):
        err.append("id no válido (AAAA-MM-DD-slug): %r" % i)
    if nombre and nombre != i:
        err.append("el fichero se llama %s y el id es %s" % (nombre, i))
    for k in ("titulo", "titulo_corto", "ciudad", "resumen"):
        if not str(e.get(k) or "").strip():
            err.append("falta %s" % k)
    if e.get("tema") not in temas:
        err.append("tema inexistente: %r" % e.get("tema"))
    if e.get("formato") not in c["formatos"]:
        err.append("formato no previsto: %r" % e.get("formato"))
    if e.get("modalidad") not in c["modalidades"]:
        err.append("modalidad no prevista: %r" % e.get("modalidad"))
    if e.get("publico") not in c["publicos"]:
        err.append("público no previsto: %r" % e.get("publico"))
    if e.get("estado") not in c["estados"]:
        err.append("estado no previsto: %r" % e.get("estado"))
    if e.get("origen") not in c["origenes"]:
        err.append("origen no previsto: %r" % e.get("origen"))
    t = ter.get(e.get("territorio"))
    if not t or t.get("tipo") != "ccaa":
        err.append("territorio no es una comunidad autónoma de la taxonomía: %r" % e.get("territorio"))
    if e.get("estado") == "fecha_por_confirmar" and not e.get("inicio"):
        if not MES.match(str(e.get("mes_previsto") or "")):
            err.append("con fecha por confirmar hace falta mes_previsto (AAAA-MM)")
    else:
        if not FECHA.match(str(e.get("inicio") or "")):
            err.append("falta la fecha de inicio (AAAA-MM-DD)")
        elif e.get("fin") and (not FECHA.match(e["fin"]) or e["fin"] < e["inicio"]):
            err.append("la fecha de fin no es válida o es anterior al inicio")
        elif not i.startswith(e["inicio"]):
            err.append("el id debe empezar por la fecha de inicio")
    g = e.get("geo") or {}
    try:
        if not (27.0 <= float(g["lat"]) <= 44.5 and -18.5 <= float(g["lon"]) <= 4.6):
            err.append("geo fuera de España")
    except Exception:
        err.append("falta geo (lat, lon)")
    if palabras(e.get("resumen")) > 60:
        err.append("el resumen pasa de 60 palabras (%d)" % palabras(e.get("resumen")))
    org = e.get("organizadores")
    if not isinstance(org, list) or not org or not all(isinstance(x, str) and x.strip() for x in org):
        err.append("organizadores: lista de nombres de entidades")
    for k in ("url_inscripcion", "url_oficial"):
        if e.get(k) and not URL_OK.match(e[k]):
            err.append("%s no es un enlace" % k)
    if e.get("estado") in ("publicado", "aplazado", "cancelado", "pasado") and not e.get("url_inscripcion") and not e.get("url_oficial"):
        err.append("un evento publicado necesita enlace de inscripción u oficial")
    f = e.get("fuentes")
    if not isinstance(f, list) or not f:
        err.append("sin fuentes: cada evento lleva al menos una URL con su fecha de comprobación")
    else:
        for x in f:
            if not isinstance(x, dict) or not URL_OK.match(str(x.get("url") or "")) or not FECHA.match(str(x.get("fecha") or "")):
                err.append("fuente sin URL o sin fecha: %r" % (x,))
    if e.get("estado") in ("publicado", "aplazado", "cancelado") and not FECHA.match(str(e.get("comprobado_at") or "")):
        err.append("falta comprobado_at (AAAA-MM-DD)")
    p = _texto_personal(e)
    if p:
        err.append("posible correo o teléfono en %s: los contactos van solo a la base privada" % ", ".join(p))
    return err


def cargar(d=DIR):
    out = []
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        e = json.load(open(f, encoding="utf-8"))
        e["_fichero"] = os.path.basename(f)[:-5]
        out.append(e)
    return out


def limpio(e):
    return {k: e[k] for k in e if not k.startswith("_")}


def guardar(e, d=DIR):
    os.makedirs(d, exist_ok=True)
    ruta = os.path.join(d, e["id"] + ".json")
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(limpio(e), fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    return ruta


def periodo(dia=None, v=None):
    dia = dia or hoy()
    return dia, mas_meses(dia, cfg(v)["periodo_meses"])


def en_periodo(e, dia=None, v=None):
    a, b = periodo(dia, v)
    return bool(e.get("inicio")) and fin_de(e) >= a and e["inicio"] <= b


def visibles(evs, dia=None, v=None):
    """Lo que enseña la página: estados visibles, sin terminar y dentro del periodo; ordenado por fecha."""
    vis = set(cfg(v)["estados_visibles"])
    return sorted([e for e in evs if e.get("estado") in vis and en_periodo(e, dia, v)], key=lambda e: (e["inicio"], e["id"]))


def por_confirmar(evs):
    return sorted([e for e in evs if e.get("estado") == "fecha_por_confirmar"], key=lambda e: (e.get("inicio") or e.get("mes_previsto") or "", e["id"]))


def despues(evs, dia=None, v=None, n=3):
    a, b = periodo(dia, v)
    vis = set(cfg(v)["estados_visibles"])
    return sorted([e for e in evs if e.get("estado") in vis and e.get("inicio") and e["inicio"] > b], key=lambda e: e["inicio"])[:n]


def archivo(evs, dia=None):
    dia = dia or hoy()
    return sorted([e for e in evs if e.get("estado") == "pasado" or (e.get("estado") in ("publicado", "aplazado", "cancelado")
                   and e.get("inicio") and fin_de(e) < dia)], key=lambda e: e["inicio"], reverse=True)


def pasar_a_pasado(evs, dia=None):
    """Devuelve los eventos que cambian a `pasado` (con `revised_at`); no borra nada."""
    dia = dia or hoy()
    out = []
    for e in evs:
        if e.get("estado") in ("publicado", "aplazado", "cancelado") and e.get("inicio") and fin_de(e) < dia:
            n = dict(e, estado="pasado", revised_at=dia)
            n["revisiones"] = list(e.get("revisiones") or []) + [{"fecha": dia, "que": "pasa a pasado (terminó el %s)" % fin_de(e)}]
            out.append(n)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("orden", choices=["validar", "listar", "alta", "pasar-a-pasado"])
    ap.add_argument("ficheros", nargs="*")
    ap.add_argument("--dir", default=DIR)
    ap.add_argument("--desde")
    ap.add_argument("--hasta")
    ap.add_argument("--estado")
    ap.add_argument("--json")
    ap.add_argument("--hoy")
    a = ap.parse_args()
    v = vertical()
    if a.orden == "validar":
        fs = a.ficheros or sorted(glob.glob(os.path.join(a.dir, "*.json")))
        malos = 0
        for f in fs:
            try:
                e = json.load(open(f, encoding="utf-8"))
            except Exception as x:
                print("%s: JSON ilegible (%s)" % (f, x)); malos += 1; continue
            err = validar(e, v, os.path.basename(f)[:-5])
            if err:
                malos += 1
                print("%s:\n  - %s" % (os.path.basename(f), "\n  - ".join(err)))
        print("%d eventos, %d con errores" % (len(fs), malos))
        return 1 if malos else 0
    evs = cargar(a.dir)
    if a.orden == "listar":
        for e in evs:
            if a.estado and e.get("estado") != a.estado:
                continue
            if a.desde and fin_de(e) and fin_de(e) < a.desde:
                continue
            if a.hasta and e.get("inicio") and e["inicio"] > a.hasta:
                continue
            print("%s  %-20s %-14s %-28s %s" % (e.get("inicio") or e.get("mes_previsto"), e.get("estado"), e.get("tema"), e.get("ciudad"), e.get("titulo_corto")))
        return 0
    if a.orden == "alta":
        e = json.load(open(a.json, encoding="utf-8"))
        e.setdefault("id", "%s-%s" % (e.get("inicio") or e.get("mes_previsto"), slug(e.get("titulo_corto") or e.get("titulo"))))
        err = validar(e, v)
        if err:
            print("No se da de alta:\n  - " + "\n  - ".join(err)); return 1
        if os.path.exists(os.path.join(a.dir, e["id"] + ".json")):
            print("Ya existe %s: edítalo en vez de duplicarlo" % e["id"]); return 1
        print(guardar(e, a.dir)); return 0
    if a.orden == "pasar-a-pasado":
        cambian = pasar_a_pasado(evs, a.hoy)
        for e in cambian:
            guardar(e, a.dir)
            print("pasado: %s" % e["id"])
        print("%d eventos pasan al archivo" % len(cambian))
        return 0


if __name__ == "__main__":
    sys.exit(main())
