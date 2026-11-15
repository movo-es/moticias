#!/usr/bin/env python3
"""MOTICIAS · Índice del buscador web (estático). Solo biblioteca estándar.

  python3 -I src/export_search_index.py [--salida app/public/buscador/index.json] [--base https://www.moticias.com]

Genera un único JSON que el tema de Ghost (y la maqueta) cargan una vez: taxonomía (nombres y alias de modos, temas y territorios,
vecinos), grupos de sinónimos y una entrada compacta por pieza publicada (sin cuerpo: cabecera, resumen corto, ejes, fecha, foto, URL).
Con 74 piezas pesa ~210 KB sin comprimir (≈ 50 KB con gzip); con 500, ~1,4 MB (≈ 350 KB). Cuando pase de 2 MB se partirá por años.
Cada entrada lleva su tipo de contenido (`tc`) y su marca (`mc`), y `dir: true` si la firma el director (el módulo y el
botón «Análisis del director» filtran por eso, no por el tema). Junto al índice se escribe `tipos.json` (id → [tipo, marca],
unos pocos KB), que `app/public/sitio/m.js` usa para poner la marca junto a cada titular en los listados de moticias.com.
Se regenera en cada edición diaria (paso 7 ter) y se sirve desde Vercel en https://app.moticias.com/buscador/index.json con CORS
para www.moticias.com (vercel.json); el tema de Ghost lo carga una vez por visita y busca en el navegador.
"""
import argparse, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from taxonomia import Taxonomia, plano  # noqa: E402
import tipos as T  # noqa: E402  (tipo de contenido y su marca; openspec tipos-de-contenido)


def recortar(s, n=220):
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


FOTOS_GHOST = {}
try:
    FOTOS_GHOST = json.load(open(os.path.join(ROOT, "portal", "img", "ghost-urls.json"), encoding="utf-8"))
except (OSError, ValueError):
    pass


def entrada(a, base):
    img = a.get("image") or {}
    src = img.get("src") or ""
    gi = src if src.startswith("http") else FOTOS_GHOST.get(src[4:]) if src.startswith("img/") else None
    return {
        "id": a["id"], "t": a.get("title"), "k": a.get("kicker"), "s": a.get("subtitle"), "r": recortar(a.get("summary")),
        "d": a.get("date"), "kind": a.get("kind"), "au": a.get("author"), "f": a.get("featured") or 0,
        "m": a.get("modo"), "sm": a.get("submodo"), "te": a.get("temas") or [], "tr": a.get("territorios") or [], "tg": a.get("tags") or [],
        "img": img.get("src"), "gi": gi, "alt": img.get("alt"), "sec": a.get("section"), "url": "%s/%s/" % (base.rstrip("/"), a["id"]),
        "pat": bool(a.get("menciones")) or bool(a.get("sponsored_by")),
        # tipo de contenido (editorial · noticia · nota_de_prensa · patrocinado) y la marca que ve el lector
        "tc": T.tipo(a, "articles"), "mc": T.marca(a, "articles"), "dir": T.es_del_director(a),
        # texto plano de búsqueda: cabecera + etiquetas + actores + resumen (sin tildes, minúsculas) — lo que el JS compara
        "x": plano(" ".join([str(a.get(k) or "") for k in ("kicker", "title", "subtitle", "summary", "relevance_for")] + list(a.get("tags") or [])
                            + ([a["actors"]] if isinstance(a.get("actors"), str) else list(a.get("actors") or [])))),
    }


def construir(data_dir=None, base="https://www.moticias.com", vertical="movilidad"):
    """El índice completo como diccionario (sin escribirlo). Lo usan main() y el servidor (api/gestor.py → indice_al_dia)."""
    data_dir = data_dir or os.path.join(ROOT, "data")
    tx = Taxonomia(vertical)
    piezas = []
    for p in sorted(glob.glob(os.path.join(data_dir, "articles", "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("status") != "publicado":  # solo lo que el lector puede abrir (sin estado = sin aprobar; 15-11-2026)
            continue
        piezas.append(entrada(d, base))
    piezas.sort(key=lambda e: (e["d"] or "", e["id"]), reverse=True)
    v = json.load(open(os.path.join(ROOT, "verticals", vertical + ".json"), encoding="utf-8"))
    return {
        "generado": __import__("datetime").datetime.now().astimezone().isoformat(timespec="minutes"),
        "taxonomia": {
            "modos": [{"id": m["id"], "nombre": m["nombre"], "submodos": [{"id": s["id"], "nombre": s["nombre"], "alias": s["alias"]} for s in m["submodos"]]} for m in tx.tax["modos"]],
            "temas": [{"id": t["id"], "nombre": t["nombre"], "alias": t["alias"]} for t in tx.tax["temas"]],
            "territorios": [{"id": t["id"], "nombre": t["nombre"], "tipo": t["tipo"], "vecinos": t.get("vecinos", []), "alias": t["alias"]} for t in tx.tax["territorios"]],
        },
        "secciones": {k: r for k, r in (v.get("secciones_web") or {}).items() if isinstance(r, dict)},
        "sinonimos": tx.busqueda.get("sinonimos", []),
        "piezas": piezas,
    }


def textos(out):
    """(index.json, tipos.json) como texto, listos para escribir o subir."""
    ligero = {"generado": out["generado"], "piezas": {p["id"]: [p["tc"], p["mc"]] for p in out["piezas"]}}
    return json.dumps(out, ensure_ascii=False, separators=(",", ":")), json.dumps(ligero, ensure_ascii=False, separators=(",", ":"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "data"))
    ap.add_argument("--salida", default=os.path.join(ROOT, "app", "public", "buscador", "index.json"))
    ap.add_argument("--base", default="https://www.moticias.com")
    ap.add_argument("--vertical", default="movilidad")
    a = ap.parse_args()
    out = construir(a.data, a.base, a.vertical)
    ix, ti = textos(out)
    os.makedirs(os.path.dirname(a.salida), exist_ok=True)
    open(a.salida, "w", encoding="utf-8").write(ix)
    open(os.path.join(os.path.dirname(a.salida), "tipos.json"), "w", encoding="utf-8").write(ti)
    print("índice: %s · %d piezas · %.0f KB" % (os.path.relpath(a.salida, ROOT), len(out["piezas"]), os.path.getsize(a.salida) / 1024))


if __name__ == "__main__":
    main()
