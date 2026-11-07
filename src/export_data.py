#!/usr/bin/env python3
"""MOTICIAS · Vuelca el contenido a data/ (un fichero JSON por documento).

Fuentes, por orden de prioridad:
  1. hemeroteca/data/AAAA-MM.json  (ediciones, piezas con cuerpo, boletines y plazos tal como quedaron al cierre)
  2. portal/data/fallback.json     (blogs, anuncios, soluciones y, como respaldo, piezas de la edición nº 1)

Uso:  python3 -I src/export_data.py
Resultado: data/articles/<id>.json, data/boletines/<id>.json, data/agenda/<id>.json,
           data/editions/<fecha>.json (solo si no existe), data/blogs, data/ads, data/soluciones.
"""
import glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def write(coll, doc):
    d = os.path.join(DATA, coll)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, doc["id"] + ".json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")


def main():
    counts = {}
    for mpath in sorted(glob.glob(os.path.join(ROOT, "hemeroteca", "data", "20??-??.json"))):
        m = json.load(open(mpath, encoding="utf-8"))
        for coll, key in (("articles", "articles"), ("boletines", "boletines"), ("agenda", "agenda")):
            for doc in m.get(key, []):
                write(coll, doc)
                counts[coll] = counts.get(coll, 0) + 1
        for e in m.get("editions", []):
            p = os.path.join(DATA, "editions", e["date"] + ".json")
            if not os.path.exists(p):
                write("editions", dict(e, id=e["date"]))
                counts["editions"] = counts.get("editions", 0) + 1
    fb = json.load(open(os.path.join(ROOT, "portal", "data", "fallback.json"), encoding="utf-8"))
    for coll in ("blogs", "ads", "soluciones"):
        for doc in fb.get(coll, []):
            write(coll, doc)
            counts[coll] = counts.get(coll, 0) + 1
    # Piezas que solo estén en el fallback (no debería ocurrir; se avisa)
    have = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(DATA, "articles", "*.json"))}
    for a in fb.get("articles", []):
        if a["id"] not in have:
            write("articles", a)
            counts["articles (solo fallback)"] = counts.get("articles (solo fallback)", 0) + 1
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
