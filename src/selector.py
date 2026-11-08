#!/usr/bin/env python3
"""MOTICIAS · Módulo 1 · Selector de contenidos (solo biblioteca estándar).

Dado un PERFIL (JSON en data/perfiles/<id>.json) devuelve piezas, boletines y plazos ordenados por
relevancia y fecha. Lo usan las ediciones a medida, el widget (vía export_feed.py), el empaquetador,
la difusión de comunicados, el radar y el asesor. Fuente por defecto: data/ del repositorio; con
--ghost-url y --ghost-key lee además la Content API de Ghost (posts publicados) y fusiona por slug.

  python3 -I src/selector.py --perfil data/perfiles/edicion-autobus-y-carretera.json
  python3 -I src/selector.py --perfil ... --hasta 2026-11-06 --out work/seleccion.json
  python3 -I src/selector.py --perfil ... --ghost-url https://moticias.com --ghost-key <content api key>

Perfil (todas las claves son opcionales salvo id):
{
 "id": "...", "name": "...", "vertical": "movilidad",
 "filters": {
   "kinds": ["noticia","analisis","reportaje"],  "sections": ["tierra","regulacion"],
   "subsectors": ["autobús","carretera"],         "modos": ["tierra"],
   "tags_include": [], "tags_exclude": [],        "keywords": ["concesión","mapa concesional"],
   "keywords_exclude": [], "campaigns": [],        "relevance_min": "MEDIA", "days": 14
 },
 "limits": {"articles": 12, "boletines": 10, "agenda": 10},
 "include": {"articles": true, "boletines": true, "agenda": true}
}
Reglas: nunca devuelve borradores ni comunicados (kind "comunicado") salvo que el perfil los pida en
"kinds"; un perfil vacío devuelve lo más relevante de los últimos `days` días (14 por defecto).
"""
import argparse, datetime, glob, json, os, re, sys, unicodedata, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODO_POR_SUBSECTOR = {
    "autobús": "tierra", "autobus": "tierra", "carretera": "tierra", "ferrocarril": "tierra", "urbano": "tierra",
    "ferrocarril de mercancías": "tierra", "aéreo": "aire", "aereo": "aire", "aerolíneas": "aire", "aeropuertos": "aire",
    "carga aérea": "aire", "marítimo": "mar", "maritimo": "mar", "puertos": "mar", "naviero": "mar",
    "regulación marítima": "mar", "transversal": "transversal", "multimodal": "transversal",
}
RELEVANCIA = {"ALTA": 2, "MEDIA": 1}


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def load_dir(d):
    out = []
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        try:
            o = json.load(open(f, encoding="utf-8"))
        except Exception as e:  # un fichero roto no detiene la selección
            print("aviso: no se pudo leer", f, e, file=sys.stderr)
            continue
        o.setdefault("id", os.path.basename(f)[:-5])
        out.append(o)
    return out


def modo_de(a):
    sec = a.get("section")
    if sec in ("tierra", "mar", "aire"):
        return sec
    return MODO_POR_SUBSECTOR.get(norm(a.get("subsector")), MODO_POR_SUBSECTOR.get(a.get("subsector"), "transversal"))


def texto_pieza(a, con_cuerpo=True):
    campos = [a.get("kicker"), a.get("title"), a.get("subtitle"), a.get("summary"), a.get("key_fact"),
              " ".join(a.get("tags") or []), a.get("actors"), a.get("relevance_for"), a.get("why")]
    if con_cuerpo:
        campos.append(a.get("body_md"))
    return norm(" ".join(str(c) for c in campos if c))


def pasa_pieza(a, f, hasta, desde):
    if a.get("status") == "borrador":
        return False
    kinds = f.get("kinds") or []
    if kinds:
        if a.get("kind") not in kinds:
            return False
    elif a.get("kind") in ("comunicado", "blog"):
        return False
    d = a.get("date") or ""
    if hasta and d > hasta:
        return False
    if desde and d < desde:
        return False
    if f.get("sections") and a.get("section") not in f["sections"]:
        return False
    if f.get("subsectors") and norm(a.get("subsector")) not in [norm(x) for x in f["subsectors"]]:
        return False
    if f.get("modos") and modo_de(a) not in f["modos"]:
        return False
    tags = [norm(t) for t in (a.get("tags") or [])]
    if f.get("tags_include") and not any(norm(t) in tags for t in f["tags_include"]):
        return False
    if f.get("tags_exclude") and any(norm(t) in tags for t in f["tags_exclude"]):
        return False
    if f.get("campaigns") and a.get("campaign") not in f["campaigns"]:
        return False
    rmin = f.get("relevance_min")
    if rmin and RELEVANCIA.get(a.get("relevance"), 0) < RELEVANCIA.get(rmin, 0):
        return False
    t = texto_pieza(a)
    if f.get("keywords_exclude") and any(norm(k) in t for k in f["keywords_exclude"]):
        return False
    if f.get("keywords") and not any(norm(k) in t for k in f["keywords"]):
        return False
    return True


def puntua_pieza(a, f, hasta):
    """Relevancia editorial + afinidad con el perfil + frescura. Determinista y explicable."""
    s = 0.0
    s += RELEVANCIA.get(a.get("relevance"), 0) * 2
    s += {1: 3, 2: 2}.get(a.get("featured"), 0)
    if a.get("kind") in ("analisis", "reportaje"):
        s += 1
    cab = texto_pieza(a, con_cuerpo=False)
    for k in f.get("keywords") or []:
        if norm(k) in cab:
            s += 2
    tags = [norm(t) for t in (a.get("tags") or [])]
    for t in f.get("tags_include") or []:
        if norm(t) in tags:
            s += 1.5
    try:
        ref = datetime.date.fromisoformat(hasta) if hasta else datetime.date.today()
        edad = (ref - datetime.date.fromisoformat(a.get("date"))).days
        s += max(0.0, 3.0 - edad * 0.25)  # tres puntos el día de publicación, nada a los 12 días
    except Exception:
        pass
    return round(s, 2)


def pasa_boletin(b, f, hasta, desde):
    d = b.get("fecha") or b.get("edicion") or ""
    if hasta and d > hasta:
        return False
    if desde and d < desde:
        return False
    if f.get("modos") and not (set(b.get("modos") or []) & set(f["modos"])):
        return False
    t = norm(" ".join(str(b.get(k) or "") for k in ("titulo", "titulo_corto", "nota", "organo", "tipo")))
    if f.get("keywords_exclude") and any(norm(k) in t for k in f["keywords_exclude"]):
        return False
    kw = (f.get("keywords") or []) + (f.get("subsectors") or [])
    if kw and not any(norm(k) in t for k in kw):
        return False  # con palabras clave o subsectores, el modo solo acota: hace falta coincidencia textual
    return True


def pasa_plazo(g, f, hasta):
    d = g.get("date") or ""
    if hasta and d < hasta:  # los plazos se miran hacia delante
        return False
    if f.get("modos") and g.get("mode") not in f["modos"] + ["transversal"]:
        return False
    t = norm(" ".join(str(g.get(k) or "") for k in ("title", "authority", "kind")))
    if f.get("keywords_exclude") and any(norm(k) in t for k in f["keywords_exclude"]):
        return False
    kw = (f.get("keywords") or []) + (f.get("subsectors") or [])
    if kw and not any(norm(k) in t for k in kw):
        return False
    return True


def resumen_pieza(a, base_url):
    return {
        "id": a["id"], "kind": a.get("kind"), "section": a.get("section"), "subsector": a.get("subsector"),
        "modo": modo_de(a), "kicker": a.get("kicker"), "title": a.get("title"), "subtitle": a.get("subtitle"),
        "summary": a.get("summary"), "key_fact": a.get("key_fact"), "date": a.get("date"),
        "published_at": a.get("published_at"), "relevance": a.get("relevance"), "tags": a.get("tags") or [],
        "author": a.get("author"), "campaign": a.get("campaign"),
        "image": (a.get("image") or {}).get("src") if isinstance(a.get("image"), dict) else None,
        "image_credit": (a.get("image") or {}).get("credit") if isinstance(a.get("image"), dict) else None,
        "url": a.get("ghost_url") or (base_url.rstrip("/") + "/" + a["id"] + "/"),
        "sources_count": len(a.get("sources") or []),
        "sources_oficiales": sum(1 for s in (a.get("sources") or []) if s.get("kind") == "oficial"),
    }


def ghost_posts(ghost_url, ghost_key, limit=200):
    """Lee los posts publicados de la Content API de Ghost y los traduce al esquema de pieza."""
    q = urllib.parse.urlencode({"key": ghost_key, "limit": limit, "include": "tags,authors",
                                "fields": "id,slug,title,custom_excerpt,excerpt,published_at,url,feature_image,feature_image_caption",
                                "order": "published_at desc"})
    req = urllib.request.Request(ghost_url.rstrip("/") + "/ghost/api/content/posts/?" + q,
                                 headers={"Accept-Version": "v5.0", "User-Agent": "Moticias/1.0 (+https://moticias.com)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    out = []
    for p in data.get("posts", []):
        tags = [t["name"] for t in p.get("tags", []) if not t["name"].startswith("#")]
        internos = [t["name"][1:] for t in p.get("tags", []) if t["name"].startswith("#")]
        section = next((t for t in internos if t in ("tierra", "mar", "aire", "regulacion", "licitaciones", "analisis", "logistica", "tecnologia", "datos")), None)
        kind = "comunicado" if "comunicado" in internos else ("analisis" if section == "analisis" else "noticia")
        out.append({"id": p["slug"], "kind": kind, "section": section, "subsector": next((t for t in tags if norm(t) in MODO_POR_SUBSECTOR), None),
                    "title": p["title"], "summary": p.get("custom_excerpt") or p.get("excerpt"), "tags": tags,
                    "date": (p.get("published_at") or "")[:10], "published_at": p.get("published_at"), "ghost_url": p.get("url"),
                    "image": {"src": p.get("feature_image"), "credit": p.get("feature_image_caption")} if p.get("feature_image") else None,
                    "relevance": "MEDIA", "status": "publicado"})
    return out


def seleccionar(perfil, hasta=None, base_url=None, ghost_url=None, ghost_key=None, data_dir=None):
    f = perfil.get("filters") or {}
    lim = {"articles": 12, "boletines": 10, "agenda": 10}
    lim.update(perfil.get("limits") or {})
    inc = {"articles": True, "boletines": True, "agenda": True}
    inc.update(perfil.get("include") or {})
    data_dir = data_dir or os.path.join(ROOT, "data")
    hasta = hasta or datetime.date.today().isoformat()
    dias = int(f.get("days") or 14)
    desde = (datetime.date.fromisoformat(hasta) - datetime.timedelta(days=dias)).isoformat()
    if not base_url:
        vid = perfil.get("vertical") or "movilidad"
        try:
            v = json.load(open(os.path.join(ROOT, "verticals", vid + ".json"), encoding="utf-8"))
            base_url = "https://" + v.get("domain", "moticias.com")
        except Exception:
            base_url = "https://moticias.com"

    piezas = {a["id"]: a for a in load_dir(os.path.join(data_dir, "articles"))}
    if ghost_url and ghost_key:
        try:
            for p in ghost_posts(ghost_url, ghost_key):
                if p["id"] in piezas:
                    piezas[p["id"]]["ghost_url"] = p["ghost_url"]
                else:
                    piezas[p["id"]] = p
        except Exception as e:
            print("aviso: Ghost no disponible:", e, file=sys.stderr)

    arts = [a for a in piezas.values() if pasa_pieza(a, f, hasta, desde)] if inc["articles"] else []
    arts.sort(key=lambda a: (puntua_pieza(a, f, hasta), a.get("date") or "", a.get("published_at") or ""), reverse=True)
    sel_arts = [dict(resumen_pieza(a, base_url), score=puntua_pieza(a, f, hasta)) for a in arts[: lim["articles"]]]

    bols = [b for b in load_dir(os.path.join(data_dir, "boletines")) if pasa_boletin(b, f, hasta, desde)] if inc["boletines"] else []
    bols.sort(key=lambda b: (b.get("fecha") or ""), reverse=True)
    sel_bols = [{k: b.get(k) for k in ("id", "fecha", "boletin", "referencia", "organo", "titulo_corto", "tipo", "modos", "url", "nota")} for b in bols[: lim["boletines"]]]

    ags = [g for g in load_dir(os.path.join(data_dir, "agenda")) if pasa_plazo(g, f, hasta)] if inc["agenda"] else []
    ags.sort(key=lambda g: g.get("date") or "")
    sel_ags = [{k: g.get(k) for k in ("id", "date", "kind", "title", "authority", "amount", "mode", "url")} for g in ags[: lim["agenda"]]]

    return {"perfil": perfil.get("id"), "name": perfil.get("name"), "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "hasta": hasta, "desde": desde, "base_url": base_url,
            "counts": {"articles": len(sel_arts), "articles_candidatas": len(arts), "boletines": len(sel_bols), "agenda": len(sel_ags)},
            "articles": sel_arts, "boletines": sel_bols, "agenda": sel_ags}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--perfil", required=True, help="ruta del perfil JSON")
    ap.add_argument("--hasta", help="fecha de referencia AAAA-MM-DD (por defecto hoy)")
    ap.add_argument("--out", help="fichero de salida JSON (por defecto, stdout)")
    ap.add_argument("--base-url", help="base de los enlaces (por defecto, el dominio del vertical)")
    ap.add_argument("--ghost-url"); ap.add_argument("--ghost-key")
    ap.add_argument("--data", help="carpeta data/ alternativa")
    a = ap.parse_args()
    perfil = json.load(open(a.perfil, encoding="utf-8"))
    res = seleccionar(perfil, a.hasta, a.base_url, a.ghost_url or os.environ.get("GHOST_URL"), a.ghost_key or os.environ.get("GHOST_CONTENT_KEY"), a.data)
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(txt)
        print(json.dumps(res["counts"], ensure_ascii=False))
    else:
        print(txt)


if __name__ == "__main__":
    main()
