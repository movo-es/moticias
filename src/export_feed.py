#!/usr/bin/env python3
"""MOTICIAS · Feeds del widget (módulo 3) a partir del selector (módulo 1). Solo biblioteca estándar.

Recorre data/perfiles/*.json con outputs.feed = true, ejecuta el selector y escribe
app/public/feed/<perfil>.json (ligero: lo que el widget necesita) y app/public/feed/index.json.
La rutina diaria lo ejecuta tras cerrar la edición; Vercel sirve app/public/ en app.moticias.com.

  python3 -I src/export_feed.py [--hasta AAAA-MM-DD] [--out app/public/feed] [--base-url https://moticias.com]
"""
import argparse, datetime, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from selector import seleccionar  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hasta")
    ap.add_argument("--out", default=os.path.join(ROOT, "app", "public", "feed"))
    ap.add_argument("--base-url")
    ap.add_argument("--perfiles", default=os.path.join(ROOT, "data", "perfiles"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    index = {"generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "feeds": []}
    for f in sorted(glob.glob(os.path.join(a.perfiles, "*.json"))):
        perfil = json.load(open(f, encoding="utf-8"))
        if not (perfil.get("outputs") or {}).get("feed"):
            continue
        sel = seleccionar(perfil, a.hasta, a.base_url, os.environ.get("GHOST_URL"), os.environ.get("GHOST_CONTENT_KEY"))
        feed = {
            "perfil": perfil["id"], "name": perfil.get("name"), "generated_at": sel["generated_at"], "base_url": sel["base_url"],
            "items": [{k: x.get(k) for k in ("id", "kicker", "title", "subtitle", "section", "subsector", "kind", "date", "url", "image", "image_credit")} for x in sel["articles"]],
            "agenda": [{k: g.get(k) for k in ("date", "kind", "title", "authority", "url")} for g in sel["agenda"]],
        }
        path = os.path.join(a.out, perfil["id"] + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(feed, fh, ensure_ascii=False, separators=(",", ":"))
        index["feeds"].append({"perfil": perfil["id"], "name": perfil.get("name"), "items": len(feed["items"]), "agenda": len(feed["agenda"]), "file": os.path.basename(path)})
    with open(os.path.join(a.out, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=1)
    print(json.dumps(index, ensure_ascii=False))


if __name__ == "__main__":
    main()
