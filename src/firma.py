"""MOTICIAS · Firma del director: cupo y criterio (decisión de Rainer, 9-11-2026).

«Pon máximo a un 10 % mi nombre, más bien menos, y solo los importantes.»

- El nombre del director firma como mucho el `max_pct` (10 %) de las piezas de los últimos `ventana_dias` (30) días, y la
  rutina apunta al `objetivo_pct` (7 %). Cuentan las publicadas y las que esperan su aprobación (`pendiente`).
- Solo firman con su nombre las piezas importantes: análisis o reportajes con `relevance` ALTA que además cumplan uno de los
  `motivos_importante` del vertical (o que el director marque a mano con `firma_director: true`).
- Lo demás —noticias, reportajes, análisis corrientes y piezas críticas— lo firma la redacción («G. Jordan, Redactor
  responsable»). Firmar y aprobar son cosas distintas: una pieza crítica sigue esperando la aprobación del director
  (`status: pendiente`, `risk: critica`) aunque la firme la redacción.

Uso:
  python3 -I src/firma.py informe [--fecha AAAA-MM-DD]       cupo de los últimos 30 días
  python3 -I src/firma.py decidir --id <pieza> [--aplicar]   firma que corresponde a una pieza (y la escribe con --aplicar)
"""
import argparse, datetime, glob, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def config(vertical):
    ed = vertical.get("editorial") or {}
    c = dict({"max_pct": 10, "objetivo_pct": 7, "ventana_dias": 30, "tipos": ["analisis", "reportaje"]}, **(ed.get("firma_director") or {}))
    c["director"] = ed.get("director", "Rainer")
    c["director_role"] = ed.get("director_role", "Director de MOTICIAS")
    c["redaccion"] = ed.get("default_author", "G. Jordan")
    c["redaccion_role"] = ed.get("default_author_role", "Redactor responsable")
    return c


def cargar(root=ROOT):
    out = {}
    for f in glob.glob(os.path.join(root, "data", "articles", "*.json")):
        a = json.load(open(f, encoding="utf-8"))
        out[a["id"]] = a
    return out


def cuenta(a):
    """Piezas que cuentan para el cupo: publicadas o pendientes de aprobación (no retiradas ni borradores)."""
    return a.get("status") in (None, "publicado", "pendiente")


def es_del_director(a, c):
    return (a.get("author") or "") == c["director"]


def cupo(arts, dia, c, excluir=None):
    """{total, director, pct, max, objetivo, libres_max, libres_objetivo} para la ventana que acaba en `dia`."""
    desde = (datetime.date.fromisoformat(dia) - datetime.timedelta(days=int(c["ventana_dias"]) - 1)).isoformat()
    ventana = [a for a in arts.values() if cuenta(a) and desde <= (a.get("date") or "") <= dia and a.get("id") != excluir]
    tot = len(ventana)
    dire = sum(1 for a in ventana if es_del_director(a, c))
    # Cuántas más podría firmar contando la nueva pieza: (dire + n) / (tot + 1) <= pct.
    libres = lambda pct: max(0, math.floor((tot + 1) * pct / 100.0) - dire)  # noqa: E731
    return {"desde": desde, "hasta": dia, "total": tot, "director": dire, "pct": round(100.0 * dire / tot, 1) if tot else 0.0,
            "max": c["max_pct"], "objetivo": c["objetivo_pct"], "libres_max": libres(c["max_pct"]), "libres_objetivo": libres(c["objetivo_pct"])}


def importante(a, c):
    """(bool, motivo). Solo análisis o reportajes de relevancia ALTA con un motivo de importancia, o la marca manual."""
    if a.get("firma_director") is True:
        return True, "marcada por el director"
    if a.get("firma_director") is False:
        return False, "el director pidió firma de la redacción"
    if a.get("kind") not in c["tipos"]:
        return False, "las %ss las firma la redacción" % (a.get("kind") or "pieza")
    if str(a.get("relevance") or "").upper() != "ALTA":
        return False, "relevancia no ALTA"
    mot = a.get("motivo_importante")
    if mot:
        return True, mot
    return False, "sin motivo de importancia (`motivo_importante`)"


def decidir(a, arts, c, dia=None):
    """Devuelve {author, author_role, firma: director|redaccion, motivo, cupo}. No cambia la aprobación."""
    dia = dia or a.get("date") or datetime.date.today().isoformat()
    q = cupo(arts, dia, c, excluir=a.get("id"))
    imp, mot = importante(a, c)
    if imp and (q["libres_objetivo"] > 0 or (a.get("firma_director") is True and q["libres_max"] > 0)):
        return {"author": c["director"], "author_role": c["director_role"], "firma": "director", "motivo": mot, "cupo": q}
    if imp:
        mot = "importante, pero el cupo está lleno (%s de %s piezas en %s días, tope %s %%)" % (q["director"], q["total"], c["ventana_dias"], c["max_pct"])
    return {"author": c["redaccion"], "author_role": c["redaccion_role"], "firma": "redaccion", "motivo": mot, "cupo": q}


def aplicar(a, d):
    """Escribe la firma decidida. Si pasa a la redacción, quita la nota de intereses personal del director y la sustituye
    por la del medio (la relación con Movenbus se sigue declarando en toda pieza que toque su mercado)."""
    a["author"], a["author_role"] = d["author"], d["author_role"]
    a["firma_motivo"] = d["motivo"]
    if d["firma"] == "redaccion" and a.get("author_note"):
        a["author_note"] = NOTA_REDACCION
    return a


# La relación con Movenbus se declara sin el nombre del director cuando la pieza la firma la redacción.
NOTA_REDACCION = ("El director de MOTICIAS es cofundador de Movenbus, operador de transporte de viajeros. MOTICIAS no cubre "
                  "operaciones propias de Movenbus y declara esta relación en toda pieza que toque su mercado.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("informe")
    i.add_argument("--fecha", default=datetime.date.today().isoformat())
    d = sub.add_parser("decidir")
    d.add_argument("--id", required=True)
    d.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    vertical = json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))
    c, arts = config(vertical), cargar()
    if args.cmd == "informe":
        q = cupo(arts, args.fecha, c)
        print("Firma del director, %s → %s: %s de %s piezas (%s %%). Tope %s %%, objetivo %s %%. Puede firmar %s más (objetivo) o %s (tope)."
              % (q["desde"], q["hasta"], q["director"], q["total"], q["pct"], q["max"], q["objetivo"], q["libres_objetivo"], q["libres_max"]))
        return 0 if q["pct"] <= c["max_pct"] else 1
    a = arts.get(args.id)
    if not a:
        print("no existe la pieza %s" % args.id, file=sys.stderr)
        return 2
    r = decidir(a, arts, c)
    print(json.dumps({k: r[k] for k in ("author", "firma", "motivo")}, ensure_ascii=False))
    if args.aplicar:
        aplicar(a, r)
        p = os.path.join(ROOT, "data", "articles", a["id"] + ".json")
        open(p, "w", encoding="utf-8").write(json.dumps(a, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
