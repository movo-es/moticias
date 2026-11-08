#!/usr/bin/env python3
"""MOTICIAS · Buscador sobre lo publicado (data/), solo biblioteca estándar.

  python3 -I src/buscador.py "concesiones de autobús que vencen en Aragón" [--limite 10] [--json] [--data data]

Busca en piezas (data/articles), boletines (data/boletines), plazos (data/agenda) y fichas de soluciones (data/soluciones)
y emite un veredicto para el comando /pieza-bajo-demanda:
  - cubierto        hay una pieza reciente que trata de la consulta (todos los términos fuertes en su cabecera)
  - parcial         hay piezas relacionadas pero ninguna la cubre entera (candidata a pieza nueva que las cite)
  - sin_cobertura   no hay nada publicado: hay que investigar y escribir la pieza
La decisión final de escribir una pieza la toma el agente con el estándar de profundidad; este script solo busca.
"""
import argparse, datetime, glob, json, os, re, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VACIAS = set("""a al algo ante bajo cabe como con contra cual cuales cuando de del desde donde dos e el ella ellas ellos en entre era
es esa esas ese eso esos esta estan este esto estos fue ha hace hasta hay la las le les lo los mas me mi mis muy nos o otra
otras otro otros para pero por que quien se segun ser si sin sobre son su sus tambien te tiene tras tu un una unas uno unos y ya
noticias noticia sobre acerca ultimas ultimo ultima informacion busco buscar quiero saber hay""".split())


def plano(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9/ ]+", " ", s.lower())


def terminos(consulta):
    """Términos fuertes de la consulta: sin vacías, sin palabras de menos de 3 letras; conserva siglas y números."""
    t = [w for w in plano(consulta).split() if w not in VACIAS and (len(w) >= 3 or w.isdigit())]
    return list(dict.fromkeys(t))


def raiz(w):
    """Raíz tosca para plurales y derivados: autobuses→autobus, concesiones→concesion, licitación→licitac."""
    for suf in ("ciones", "siones", "iones", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            w = w[: -len(suf)] + ("ion" if suf in ("ciones", "siones", "iones") else "")
            break
    return w[:7] if len(w) > 7 else w


def hits(texto, terms):
    return [t for t in terms if raiz(t) in texto]


def cargar(data_dir):
    docs = []
    for col, campos_cab, campos_cuerpo in (
        ("articles", ("title", "subtitle", "summary", "kicker"), ("body_md", "actors", "relevance_for", "why", "next", "tags", "subsector")),
        ("boletines", ("titulo_corto", "titulo"), ("nota", "referencia", "organo")),
        ("agenda", ("titulo", "title", "titulo_corto"), ("nota", "texto", "authority", "kind")),
        ("soluciones", ("name", "summary", "provider", "category"), ("body_md", "tags")),
    ):
        for p in glob.glob(os.path.join(data_dir, col, "*.json")):
            try:
                d = json.load(open(p, encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            cab = plano(" ".join(str(d.get(k) or "") for k in campos_cab))
            cuerpo = plano(" ".join(" ".join(v) if isinstance(v := d.get(k), list) else str(v or "") for k in campos_cuerpo))
            fecha = d.get("date") or d.get("edicion") or d.get("fecha") or d.get("verified_at") or ""
            docs.append({"col": col, "id": d.get("id") or os.path.basename(p)[:-5], "titulo": d.get("title") or d.get("titulo_corto") or d.get("titulo") or d.get("name") or "",
                         "fecha": str(fecha)[:10], "cab": cab, "cuerpo": cuerpo, "kind": d.get("kind"), "section": d.get("section"), "url": d.get("url"),
                         "ghost_url": (d.get("ghost") or {}).get("url") if isinstance(d.get("ghost"), dict) else None})
    return docs


def buscar(consulta, docs, hoy=None, limite=10):
    terms = terminos(consulta)
    if not terms:
        return terms, []
    hoy = datetime.date.fromisoformat(hoy) if hoy else datetime.date.today()
    res = []
    for d in docs:
        hc, hb = hits(d["cab"], terms), hits(d["cuerpo"], terms)
        if not hc and not hb:
            continue
        pts = 5 * len(hc) + 2 * len(set(hb) - set(hc))
        if d["col"] == "articles":
            pts += 3
        try:
            edad = (hoy - datetime.date.fromisoformat(d["fecha"])).days
            if edad <= 30:
                pts += 2
        except ValueError:
            edad = None
        cobertura = len(set(hc) | set(hb)) / len(terms)
        res.append({**{k: d[k] for k in ("col", "id", "titulo", "fecha", "kind", "section", "url", "ghost_url")}, "puntos": pts,
                    "cobertura": round(cobertura, 2), "en_cabecera": hc, "en_cuerpo": sorted(set(hb) - set(hc)), "dias": edad})
    res.sort(key=lambda r: (-r["puntos"], r["fecha"]), reverse=False)
    return terms, res[:limite]


def veredicto(terms, res):
    arts = [r for r in res if r["col"] == "articles"]
    if arts and arts[0]["cobertura"] >= 0.99 and len(arts[0]["en_cabecera"]) >= max(1, len(terms) - 1):
        return "cubierto"
    if res and max(r["cobertura"] for r in res) >= 0.5:
        return "parcial"
    return "sin_cobertura"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("consulta")
    ap.add_argument("--data", default=os.path.join(ROOT, "data"))
    ap.add_argument("--limite", type=int, default=10)
    ap.add_argument("--hoy")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    docs = cargar(a.data)
    terms, res = buscar(a.consulta, docs, a.hoy, a.limite)
    v = veredicto(terms, res)
    out = {"consulta": a.consulta, "terminos": terms, "veredicto": v, "documentos": len(docs), "resultados": res}
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return
    print("Consulta: %s · términos: %s · veredicto: %s (%d documentos)" % (a.consulta, ", ".join(terms), v, len(docs)))
    for r in res:
        print("%3d  %-9s %s  %s  [%s] cab=%s cuerpo=%s" % (r["puntos"], r["col"], r["fecha"], r["titulo"][:80], r["id"], ",".join(r["en_cabecera"]), ",".join(r["en_cuerpo"])))


if __name__ == "__main__":
    main()
