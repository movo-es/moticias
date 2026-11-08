#!/usr/bin/env python3
"""Monta la maqueta publicable en work/maqueta/: index.html + spain.js + search-index.json + fotos reducidas (≤ 720 px, JPEG 72).
  python3 -I openspec/changes/navegacion-y-buscador/maqueta/construir.py
Requiere Pillow para las miniaturas; sin él copia las fotos tal cual."""
import json, os, shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "work", "maqueta")
os.makedirs(os.path.join(OUT, "img"), exist_ok=True)
shutil.copy(os.path.join(AQUI, "index.html"), OUT)
shutil.copy(os.path.join(ROOT, "portal", "spain.js"), OUT)
shutil.copy(os.path.join(ROOT, "app", "public", "buscador", "index.json"), os.path.join(OUT, "search-index.json"))
ix = json.load(open(os.path.join(OUT, "search-index.json"), encoding="utf-8"))
try:
    from PIL import Image
except ImportError:
    Image = None
n = 0
for p in ix["piezas"]:
    if not p.get("img"):
        continue
    src = os.path.join(ROOT, "portal", p["img"])
    dst = os.path.join(OUT, p["img"])
    if not os.path.exists(src) or os.path.exists(dst):
        continue
    if Image:
        im = Image.open(src).convert("RGB")
        im.thumbnail((720, 720))
        im.save(dst, "JPEG", quality=72, optimize=True)
    else:
        shutil.copy(src, dst)
    n += 1
tam = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs) / 1e6
print("maqueta en %s · %d fotos · %.1f MB" % (os.path.relpath(OUT, ROOT), n, tam))
