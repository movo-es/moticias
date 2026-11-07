#!/usr/bin/env python3
"""MOTICIAS · Genera ghost/redirects.yaml: 301 de las URL antiguas en la raíz (/<slug>/) a la sección (/<sección>/<slug>/).

  python3 -I src/ghost_redirects.py

Las piezas se publicaron el 7-11-2026 en la raíz, antes de que existieran las secciones en subdirectorios
(ghost/routes.yaml). Se sube a mano en Ghost: Ajustes → Labs → Redirects → Upload redirects YAML.
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from ghost_publish import load_all_articles, collection_of  # noqa: E402

by = {}
for a in load_all_articles():
    by.setdefault(collection_of(a), []).append(a["id"])
lines = ["## MOTICIAS · redirecciones 301 (generado por src/ghost_redirects.py)", "301:"]
for sec in sorted(by):
    for slug in sorted(by[sec]):
        lines.append("  ^/%s/$: /%s/%s/" % (slug, sec, slug))
open(os.path.join(ROOT, "ghost", "redirects.yaml"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("ghost/redirects.yaml: %d redirecciones" % sum(len(v) for v in by.values()))
