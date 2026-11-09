#!/usr/bin/env python3
"""MOTICIAS · Retoques del director (`data/retoques/`): encargos de retoque a una pieza publicada, pedidos desde el gestor.

  python3 -I src/retoques.py pendientes                      lista (JSON) los retoques pendientes, con la pieza cargada
  python3 -I src/retoques.py crear --pieza <id> --instruccion "…" [--por editor]
  python3 -I src/retoques.py cerrar --id <id> --estado aplicado|sin_fuentes|cancelado --resumen "…" [--fuente URL ...] [--cambios "titular,párrafo…"]
  python3 -I src/retoques.py revisar --pieza <id> --nota "…"  añade `revised_at` y la nota de revisión al final de `body_md`

Un retoque es una instrucción editorial de Rainer (o de un editor) sobre una pieza ya publicada: un enfoque, un titular, una
referencia que falta («Iberia incluye Granada en su operación especial a Andalucía tras el accidente del AVE»). La atiende la
rutina `/retoques` (tarea programada «MOTICIAS · retoques del director», cada hora en horario laboral) con el método de
siempre: lo que se pide se verifica en fuente primaria antes de escribirlo; si no hay fuente, el retoque queda `sin_fuentes`
con el motivo y no se publica nada. Nunca se borra un retoque: cancelar es `estado: cancelado`.

El repositorio es público: aquí no entra ningún dato personal. `pedido_por` es el perfil (superadmin, editor…), no un nombre.
"""
import argparse, datetime, glob, json, os, re, secrets, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "data", "retoques")
ESTADOS = ("pendiente", "aplicado", "sin_fuentes", "cancelado")


def ahora():
    return datetime.datetime.now().astimezone().isoformat(timespec="minutes")


def guardar(ruta, obj):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")


def cargar_todos():
    out = []
    for p in sorted(glob.glob(os.path.join(DIR, "*.json"))):
        with open(p, encoding="utf-8") as fh:
            out.append(json.load(fh))
    return out


def construir(pieza, instruccion, por="superadmin"):
    """Valida y da forma a un retoque sin escribir nada (el gestor lo guarda por commit en GitHub: en Vercel el disco es de
    solo lectura). Lanza ValueError con un mensaje para la persona si algo no vale."""
    instruccion = " ".join((instruccion or "").split())
    if not instruccion:
        raise ValueError("la instrucción está vacía")
    if len(instruccion) > 1200:
        raise ValueError("la instrucción es demasiado larga (máximo 1.200 caracteres)")
    ruta_pieza = os.path.join(ROOT, "data", "articles", pieza + ".json")
    if not re.fullmatch(r"[a-z0-9-]{3,80}", pieza or "") or not os.path.exists(ruta_pieza):
        raise ValueError("pieza no encontrada")
    rid = "%s-%s-%s" % (datetime.date.today().isoformat(), pieza[:40].rstrip("-"), secrets.token_hex(2))
    return {"id": rid, "pieza": pieza, "instruccion": instruccion, "pedido_por": por, "pedido_en": ahora(), "estado": "pendiente",
            "resultado": None}


def crear(pieza, instruccion, por="superadmin"):
    """Crea el fichero del retoque en data/retoques/ y devuelve el objeto (línea de órdenes y rutinas)."""
    r = construir(pieza, instruccion, por)
    guardar(os.path.join(DIR, r["id"] + ".json"), r)
    return r


def cerrar(rid, estado, resumen, fuentes=None, cambios=None):
    if estado not in ESTADOS[1:]:
        raise ValueError("estado no válido")
    ruta = os.path.join(DIR, rid + ".json")
    r = json.load(open(ruta, encoding="utf-8"))
    r["estado"] = estado
    r["resultado"] = {"en": ahora(), "resumen": resumen, "fuentes": fuentes or [], "cambios": cambios or []}
    guardar(ruta, r)
    return r


def revisar(pieza, nota):
    """Deja constancia de la revisión en la pieza: `revised_at` y una línea «Revisión» al final del cuerpo (regla de la casa)."""
    ruta = os.path.join(ROOT, "data", "articles", pieza + ".json")
    a = json.load(open(ruta, encoding="utf-8"))
    cuando = ahora()
    a["revised_at"] = cuando
    fecha = datetime.datetime.fromisoformat(cuando)
    linea = "*Revisión (%s, %s): %s*" % (fecha.strftime("%d-%m-%Y"), fecha.strftime("%H:%M"), " ".join(nota.split()))
    a["body_md"] = (a.get("body_md") or "").rstrip() + "\n\n" + linea + "\n"
    guardar(ruta, a)
    return a


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pendientes")
    c = sub.add_parser("crear"); c.add_argument("--pieza", required=True); c.add_argument("--instruccion", required=True); c.add_argument("--por", default="superadmin")
    z = sub.add_parser("cerrar"); z.add_argument("--id", required=True); z.add_argument("--estado", required=True, choices=ESTADOS[1:])
    z.add_argument("--resumen", required=True); z.add_argument("--fuente", action="append", default=[]); z.add_argument("--cambios", default="")
    v = sub.add_parser("revisar"); v.add_argument("--pieza", required=True); v.add_argument("--nota", required=True)
    a = ap.parse_args()
    if a.cmd == "pendientes":
        out = []
        for r in cargar_todos():
            if r.get("estado") != "pendiente":
                continue
            p = os.path.join(ROOT, "data", "articles", r["pieza"] + ".json")
            pieza = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
            out.append(dict(r, pieza_datos={k: pieza.get(k) for k in ("title", "subtitle", "date", "status", "author", "kind", "section", "url")} if pieza else None))
        print(json.dumps({"pendientes": len(out), "retoques": out}, ensure_ascii=False, indent=1))
    elif a.cmd == "crear":
        print(json.dumps(crear(a.pieza, a.instruccion, a.por), ensure_ascii=False, indent=1))
    elif a.cmd == "cerrar":
        print(json.dumps(cerrar(a.id, a.estado, a.resumen, a.fuente, [c.strip() for c in a.cambios.split(",") if c.strip()]), ensure_ascii=False, indent=1))
    elif a.cmd == "revisar":
        r = revisar(a.pieza, a.nota)
        print(json.dumps({"pieza": a.pieza, "revised_at": r["revised_at"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
