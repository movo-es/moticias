#!/usr/bin/env python3
"""MOTICIAS · Índice del buscador web (estático). Solo biblioteca estándar.

  python3 -I src/export_search_index.py [--salida app/public/buscador/index.json] [--base https://www.moticias.com]

Genera un único JSON que el tema de Ghost (y la maqueta) cargan una vez: taxonomía (nombres y alias de modos, temas y territorios,
vecinos), grupos de sinónimos y una entrada compacta por pieza publicada (sin cuerpo: cabecera, resumen corto, ejes, fecha, foto, URL).
Con 74 piezas pesa ~210 KB sin comprimir (≈ 50 KB con gzip); con 500, ~1,4 MB (≈ 350 KB). Cuando pase de 2 MB se partirá por años.
Se regenera en cada edición diaria (paso 7 ter) y se sirve desde Vercel en https://app.moticias.com/buscador/index.json con CORS
para www.moticias.com (vercel.json); el tema de Ghost lo carga una vez por visita y busca en el navegador.
"""
import argparse, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from taxonomia import Taxonomia, plano  # noqa: E402


def recortar(s, n=220):
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def entrada(a, base):
    img = a.get("image") or {}
    return {
        "id": a["id"], "t": a.get("title"), "k": a.get("kicker"), "s": a.get("subtitle"), "r": recortar(a.get("summary")),
        "d": a.get("date"), "kind": a.get("kind"), "au": a.get("author"), "f": a.get("featured") or 0,
        "m": a.get("modo"), "sm": a.get("submodo"), "te": a.get("temas") or [], "tr": a.get("territorios") or [], "tg": a.get("tags") or [],
        "img": img.get("src"), "alt": img.get("alt"), "url": "%s/%s/" % (base.rstrip("/"), a["id"]),
        "pat": bool(a.get("menciones")) or bool(a.get("sponsored_by")),
        # texto plano de búsqueda: cabecera + etiquetas + actores + resumen (sin tildes, minúsculas) — lo que el JS compara
        "x": plano(" ".join([str(a.get(k) or "") for k in ("kicker", "title", "subtitle", "summary", "relevance_for")] + list(a.get("tags") or [])
                            + ([a["actors"]] if isinstance(a.get("actors"), str) else list(a.get("actors") or [])))),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "data"))
    ap.add_argument("--salida", default=os.path.join(ROOT, "app", "public", "buscador", "index.json"))
    ap.add_argument("--base", default="https://www.moticias.com")
    ap.add_argument("--vertical", default="movilidad")
    a = ap.parse_args()
    tx = Taxonomia(a.vertical)
    piezas = []
    for p in sorted(glob.glob(os.path.join(a.data, "articles", "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("status") in ("pendiente", "borrador", "retirada"):
            continue
        piezas.append(entrada(d, a.base))
    piezas.sort(key=lambda e: (e["d"] or "", e["id"]), reverse=True)
    out = {
        "generado": __import__("datetime").datetime.now().astimezone().isoformat(timespec="minutes"),
        "taxonomia": {
            "modos": [{"id": m["id"], "nombre": m["nombre"], "submodos": [{"id": s["id"], "nombre": s["nombre"], "alias": s["alias"]} for s in m["submodos"]]} for m in tx.tax["modos"]],
            "temas": [{"id": t["id"], "nombre": t["nombre"], "alias": t["alias"]} for t in tx.tax["temas"]],
            "territorios": [{"id": t["id"], "nombre": t["nombre"], "tipo": t["tipo"], "vecinos": t.get("vecinos", []), "alias": t["alias"]} for t in tx.tax["territorios"]],
        },
        "sinonimos": tx.busqueda.get("sinonimos", []),
        "piezas": piezas,
    }
    os.makedirs(os.path.dirname(a.salida), exist_ok=True)
    json.dump(out, open(a.salida, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("índice: %s · %d piezas · %.0f KB" % (os.path.relpath(a.salida, ROOT), len(piezas), os.path.getsize(a.salida) / 1024))


if __name__ == "__main__":
    main()
