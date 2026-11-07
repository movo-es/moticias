#!/usr/bin/env python3
"""MOTICIAS · Hemeroteca. Compila los datos de la hemeroteca a partir de la base del portal.

La hemeroteca es un artefacto aparte (index.html + app.css + app.js + data/ + img/). Este script
genera la página de entrada, los ficheros de datos y el mapa de ficheros que hay que publicar.

  full   Reconstruye todo desde un volcado completo de la base (y data/fallback.json del portal).
         python3 -I src/hemeroteca_build.py full --db DIR --fallback portal/data/fallback.json --out OUT [--blobs portal/img]
  daily  Añade la edición del día a la hemeroteca publicada.
         python3 -I src/hemeroteca_build.py daily --today AAAA-MM-DD --db DIR --prev hemeroteca --out OUT [--blobs portal/img]

--db      carpeta con articles/, boletines/, agenda/ y editions/ (un JSON por documento; vale `data/` del repositorio).
--prev    carpeta con data/index.json y data/AAAA-MM.json de la hemeroteca publicada (en el repositorio, `hemeroteca/`).
--blobs   carpeta con las fotos /_blob/ del portal guardadas como <assetId>.<ext> o b-<assetId>.<ext> (en el repositorio, `portal/img/`).
--app     carpeta con app.css y app.js: genera además la copia en un solo archivo (moticias-hemeroteca-*.html).

Salida en OUT: index.html (la página), data/*.json, files.json (mapa `files` para publicar),
need_blobs.txt (assetIds que faltan: descárgalos del portal a --blobs y vuelve a ejecutar).
"""
import argparse, datetime, glob, json, os, re, sys, zoneinfo

PORTAL = "https://claude.ai/artifact/6r3hgcemzjFR7LcweAXgEZ"
TZ = zoneinfo.ZoneInfo("Europe/Madrid")
FONTS = ("https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300..800;1,6..72,300..800"
         "&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap")
DEEP = ["image", "body_md", "key_data", "timeline", "sources", "title", "subtitle", "summary", "actors", "relevance_for",
        "why", "next", "key_fact", "deep_rev", "revised_at", "published_at", "published_time"]
A_KEEP = ["id", "kind", "section", "subsector", "kicker", "title", "subtitle", "summary", "actors", "relevance_for", "why",
          "next", "key_fact", "date", "event_date", "published_at", "published_time", "revised_at", "featured", "relevance",
          "geo", "image", "body_md", "key_data", "timeline", "sources", "tags", "reg_kind", "doc_ref", "authority", "amount",
          "deadline", "author", "author_role", "author_note", "scope"]
B_KEEP = ["id", "fecha", "boletin", "referencia", "organo", "titulo", "titulo_corto", "tipo", "modos", "url", "nota", "edicion"]
G_KEEP = ["id", "date", "kind", "title", "authority", "amount", "amount_eur", "mode", "url", "edicion"]
E_KEEP = ["date", "number", "closed_at", "lead_id", "analysis_id", "document", "boe_series", "boe_range", "ticker_label",
          "ticker", "note_metodologica"]
SHELL = """<title>Hemeroteca MOTICIAS</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="Todas las ediciones de MOTICIAS, con búsqueda de texto completo y máquina del tiempo para recorrerlas día a día.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="%s">
<link rel="stylesheet" href="app.css">
<div id="app"><div class="boot"><div class="boot-wm"><span class="m">M</span>OTICIAS</div><div class="boot-sub">Hemeroteca</div><p class="boot-msg">Cargando las ediciones…</p></div></div>
<script src="app.js"></script>
""" % FONTS.replace("&", "&amp;")


def now_iso():
    return datetime.datetime.now(TZ).isoformat(timespec="seconds")


def load_dir(d):
    out = {}
    if not d or not os.path.isdir(d):
        return out
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        o = json.load(open(f, encoding="utf-8"))
        if isinstance(o, dict) and isinstance(o.get("data"), dict) and set(o) <= {"id", "data", "version", "updatedAt", "createdAt"}:
            o = dict(o["data"], id=o.get("id") or o["data"].get("id"))
        o.setdefault("id", os.path.basename(f)[:-5])
        out[o["id"]] = o
    return out


def pick(o, keys):
    return {k: o[k] for k in keys if k in o and o[k] is not None and o[k] != "" and o[k] != []}


def find_blob(blobs, aid):
    if not blobs:
        return None
    for prefix in ("", "b-"):
        for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
            p = os.path.join(blobs, prefix + aid + ext)
            if os.path.exists(p):
                return p
    return None


def map_image(im, blobs):
    """Devuelve (imagen para la hemeroteca, fichero a publicar o None, assetId que falta o None)."""
    if not isinstance(im, dict):
        return None, None, None
    base = pick(im, ["alt", "credit", "license", "source"])
    src = str(im.get("src") or "")
    if src.startswith("img/"):
        base.update(src=src, orig_src=im.get("orig_src") or src)
        local = os.path.join(blobs, os.path.basename(src)) if blobs else None
        if local and os.path.exists(local):
            return base, (src, local), None
        return base, (src, {"artifact": PORTAL, "path": src}), None
    m = re.match(r"^/_blob/([0-9a-f]{32})$", src)
    aid = im.get("assetId") or (m.group(1) if m else None)
    if not aid:
        return None, None, None
    local = find_blob(blobs, aid)
    ext = os.path.splitext(local)[1].lower() if local else ".jpg"
    path = "img/b-%s%s" % (aid, ".jpg" if ext == ".jpeg" else ext)
    base.update(src=path, orig_src=src or "/_blob/" + aid)
    return base, ((path, local) if local else None), (None if local else aid)


def prep_article(a, blobs, files, missing):
    o = pick(a, A_KEEP)
    if a.get("featured") == 0:
        o["featured"] = 0
    im, f, miss = map_image(a.get("image"), blobs)
    if im:
        o["image"] = im
    else:
        o.pop("image", None)
    if f:
        files[f[0]] = f[1]
    if miss:
        missing.add(miss)
    return o


def ed_summary(e, arts, bols, ags, chunk):
    d = e["date"]
    mine = [a for a in arts if a.get("date") == d]
    return {"date": d, "number": e.get("number"), "closed_at": e.get("closed_at"), "lead_id": e.get("lead_id"),
            "analysis_id": e.get("analysis_id"), "chunk": chunk,
            "counts": {"piezas": len(mine), "analisis": sum(1 for a in mine if a.get("kind") == "analisis"),
                       "palabras": sum(len((a.get("body_md") or "").split()) for a in mine),
                       "fuentes": sum(len(a.get("sources") or []) for a in mine),
                       "boletines": sum(1 for b in bols if b.get("edicion") == d),
                       "plazos": sum(1 for g in ags if g.get("edicion") == d)}}


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))


def build(args):
    out = os.path.abspath(args.out)
    os.makedirs(os.path.join(out, "data"), exist_ok=True)
    blobs = os.path.abspath(args.blobs) if args.blobs else None
    db = {k: load_dir(os.path.join(args.db, k)) for k in ("articles", "boletines", "agenda", "editions")}
    files, missing = {}, set()

    if args.mode == "full":
        deep = {}
        if args.fallback and os.path.exists(args.fallback):
            fb = json.load(open(args.fallback, encoding="utf-8"))
            deep = {a["id"]: a for a in fb.get("articles", []) if a.get("deep_rev")}
        eds = sorted((pick(e, E_KEEP) for e in db["editions"].values() if e.get("date")), key=lambda e: e["date"])
        if not eds:
            sys.exit("No hay ediciones en --db/editions")
        first = eds[0]["date"]
        arts = []
        for a in db["articles"].values():
            f = deep.get(a["id"])
            if f and (f.get("deep_rev") or 0) > (a.get("deep_rev") or 0):
                a = dict(a)
                for k in DEEP:
                    if f.get(k) not in (None, "", []):
                        a[k] = f[k]
            if a.get("status") == "borrador" or a.get("kind") == "blog" or not a.get("date"):
                continue
            arts.append(prep_article(a, blobs, files, missing))
        bols, ags = [], []
        for b in db["boletines"].values():
            b = pick(b, B_KEEP)
            if not b.get("edicion"):
                later = [e["date"] for e in eds if e["date"] >= (b.get("fecha") or first)]
                b["edicion"] = later[0] if later else eds[-1]["date"]
            bols.append(b)
        for g in db["agenda"].values():
            g = pick(g, G_KEEP)
            g.setdefault("edicion", first)
            ags.append(g)
        months = {}
        for e in eds:
            months.setdefault(e["date"][:7], {"month": e["date"][:7], "editions": [], "articles": [], "boletines": [], "agenda": []})["editions"].append(e)
        def mon(d):
            return months.setdefault(d[:7], {"month": d[:7], "editions": [], "articles": [], "boletines": [], "agenda": []})
        for a in arts:
            mon(a["date"])["articles"].append(a)
        for b in bols:
            mon(b["edicion"])["boletines"].append(b)
        for g in ags:
            mon(g["edicion"])["agenda"].append(g)
        touched = sorted(months)
        prev_images = set()
        all_eds, all_arts, all_bols, all_ags = eds, arts, bols, ags
    else:
        today = args.today
        prev_idx = json.load(open(os.path.join(args.prev, "data", "index.json"), encoding="utf-8"))
        prev_images = set(prev_idx.get("images", []))
        mkey = today[:7]
        mpath = os.path.join(args.prev, "data", mkey + ".json")
        chunk = json.load(open(mpath, encoding="utf-8")) if os.path.exists(mpath) else {"month": mkey, "editions": [], "articles": [], "boletines": [], "agenda": []}
        e = db["editions"].get(today)
        if not e:
            sys.exit("Falta editions/%s en --db" % today)
        e = pick(e, E_KEEP)
        chunk["editions"] = sorted([x for x in chunk["editions"] if x["date"] != today] + [e], key=lambda x: x["date"])
        new_a = [prep_article(a, blobs, files, missing) for a in db["articles"].values()
                 if a.get("date") == today and a.get("status") != "borrador" and a.get("kind") != "blog"]
        ids = {a["id"] for a in new_a}
        chunk["articles"] = [a for a in chunk["articles"] if a["id"] not in ids] + new_a
        for coll, keep, key in (("boletines", B_KEEP, "boletines"), ("agenda", G_KEEP, "agenda")):
            new = []
            for x in db[coll].values():
                x = pick(x, keep)
                x.setdefault("edicion", today)
                if x["edicion"] == today:
                    new.append(x)
            nids = {x["id"] for x in new}
            chunk[key] = [x for x in chunk[key] if x["id"] not in nids] + new
        months = {mkey: chunk}
        touched = [mkey]
        # Para los resúmenes del índice basta con el mes en curso; el resto se conserva del índice anterior.
        all_eds, all_arts, all_bols, all_ags = chunk["editions"], chunk["articles"], chunk["boletines"], chunk["agenda"]

    for m in touched:
        ch = months[m]
        ch["editions"].sort(key=lambda x: x["date"])
        ch["articles"].sort(key=lambda x: (x.get("date", ""), x.get("published_at", "")))
        write_json(os.path.join(out, "data", m + ".json"), ch)
        files["data/%s.json" % m] = os.path.join(out, "data", m + ".json")

    summaries = {e["date"]: ed_summary(e, all_arts, all_bols, all_ags, "data/%s.json" % e["date"][:7]) for e in all_eds}
    if args.mode == "daily":
        for s in prev_idx.get("editions", []):
            summaries.setdefault(s["date"], s)
    chunks = sorted({s["chunk"] for s in summaries.values()})
    present = {p for p in files if p.startswith("img/")}
    images = sorted(prev_images | present)
    if args.mode == "daily":
        files = {p: v for p, v in files.items() if not (p.startswith("img/") and p in prev_images)}
    eds_list = [summaries[d] for d in sorted(summaries)]
    idx = {"version": 1, "generated_at": now_iso(), "portal": PORTAL, "chunks": chunks, "editions": eds_list,
           "images": images,
           "totals": {k: sum((s.get("counts") or {}).get(k, 0) for s in eds_list) for k in ("piezas", "palabras", "fuentes", "boletines", "plazos")}}
    write_json(os.path.join(out, "data", "index.json"), idx)
    files["data/index.json"] = os.path.join(out, "data", "index.json")
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(SHELL)
    with open(os.path.join(out, "files.json"), "w", encoding="utf-8") as fh:
        json.dump(files, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(out, "need_blobs.txt"), "w") as fh:
        fh.write("\n".join(sorted(missing)))
    if args.app:
        chunk_objs = [json.load(open(os.path.join(out, c) if os.path.exists(os.path.join(out, c)) else os.path.join(args.prev, c), encoding="utf-8")) for c in chunks]
        css = open(os.path.join(args.app, "app.css"), encoding="utf-8").read()
        js = open(os.path.join(args.app, "app.js"), encoding="utf-8").read()
        data = json.dumps({"index": idx, "chunks": chunk_objs}, ensure_ascii=False, separators=(",", ":"))
        data = data.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
        last = eds_list[-1]["date"]
        html = ('<!doctype html>\n<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
                '<title>Hemeroteca MOTICIAS</title><link rel="stylesheet" href="%s"><style>%s</style></head><body><div id="app"></div>'
                '<script>window.__HEMEROTECA__=%s;</script><script>%s</script></body></html>\n') % (
            FONTS.replace("&", "&amp;"), css, data, js.replace("</script", "<\\/script"))
        with open(os.path.join(out, "moticias-hemeroteca-%s.html" % last), "w", encoding="utf-8") as fh:
            fh.write(html)
    print(json.dumps({"mode": args.mode, "editions": len(eds_list), "touched": touched, "files": len(files),
                      "missing_blobs": sorted(missing), "totals": idx["totals"]}, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["full", "daily"])
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fallback")
    ap.add_argument("--prev")
    ap.add_argument("--today")
    ap.add_argument("--blobs")
    ap.add_argument("--app")
    a = ap.parse_args()
    if a.mode == "daily" and not (a.prev and a.today):
        ap.error("daily necesita --prev y --today")
    build(a)
