#!/usr/bin/env python3
"""MOTICIAS · Buscador sobre lo publicado (data/), solo biblioteca estándar.

  python3 -I src/buscador.py "concesiones de autobús que vencen en Aragón" [--limite 10] [--json] [--data data]

Busca en piezas (data/articles), boletines (data/boletines), plazos (data/agenda) y fichas de soluciones (data/soluciones)
y emite un veredicto para el comando /pieza-bajo-demanda:
  - cubierto        hay una pieza reciente que trata de la consulta (todos los términos fuertes en su cabecera)
  - parcial         hay piezas relacionadas pero ninguna la cubre entera (candidata a pieza nueva que las cite)
  - sin_cobertura   no hay nada publicado: hay que investigar y escribir la pieza
La decisión final de escribir una pieza la toma el agente con el estándar de profundidad; este script solo busca.

Entiende lo que el lector quiere aunque no lo escriba bien (cambio navegacion-y-buscador, 9-11-2026):
  - sinónimos del sector (verticals/<vertical>.json → busqueda.sinonimos): «caducadas» encuentra «vencidas» y «prórroga»;
  - territorio: si la consulta nombra una comunidad, provincia o ciudad, filtra por ese territorio y, si no hay nada,
    propone las comunidades vecinas («nada de Asturias; sí de Cantabria»);
  - erratas: un término sin ningún resultado se corrige con la palabra más parecida del vocabulario publicado («¿quiso decir…?»).
"""
import argparse, datetime, difflib, glob, json, os, re, sys, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from taxonomia import Taxonomia  # noqa: E402

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


def hits(texto, terms, tx=None):
    """Términos de la consulta presentes en el texto —por palabra completa (misma raíz) o por un sinónimo del vertical;
    los sinónimos de varias palabras se buscan como expresión."""
    toks = {raiz(w) for w in texto.split()}
    acolchado = " " + texto + " "
    out = []
    for t in terms:
        if raiz(t) in toks:
            out.append(t)
            continue
        if tx is not None:
            for e in tx.expandir(t):
                if (" " in e and " " + e + " " in acolchado) or (" " not in e and len(e) >= 4 and raiz(e) in toks):
                    out.append(t)
                    break
    return out


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
                         "ghost_url": (d.get("ghost") or {}).get("url") if isinstance(d.get("ghost"), dict) else None,
                         "modo": d.get("modo"), "submodo": d.get("submodo"), "temas": d.get("temas") or [], "territorios": d.get("territorios") or []})
    return docs


def vocabulario(docs):
    """Palabras de cabecera de todo lo publicado (≥ 4 letras), para corregir erratas."""
    v = set()
    for d in docs:
        v.update(w for w in d["cab"].split() if len(w) >= 4 and not w.isdigit())
    return sorted(v)


def corregir(terms, docs, tx):
    """Sustituye los términos que no aparecen en ninguna parte por la palabra más parecida del vocabulario. Devuelve (términos, {malo: bueno})."""
    voc = None
    corr = {}
    out = []
    for t in terms:
        if any(hits(d["cab"] + " " + d["cuerpo"], [t], tx) for d in docs):
            out.append(t)
            continue
        voc = voc if voc is not None else vocabulario(docs)
        c = difflib.get_close_matches(t, voc, n=1, cutoff=0.8)
        if c and c[0] != t:
            corr[t] = c[0]
            out.append(c[0])
        else:
            out.append(t)
    return out, corr


def buscar(consulta, docs, hoy=None, limite=10, tx=None, territorio=None):
    """Devuelve (términos, resultados, contexto). `contexto` trae el territorio detectado, correcciones y vecinos sugeridos."""
    tx = tx or Taxonomia()
    ctx = {"territorio": None, "territorio_nombre": None, "correcciones": {}, "vecinos": [], "aviso": None}
    terms = terminos(consulta)
    # territorio: el que pide el lector (--territorio) o el que nombra en la consulta
    terr = territorio or next(iter(tx.territorios_en(consulta, solo_ccaa=True)), None)
    if terr:
        ctx["territorio"], ctx["territorio_nombre"] = terr, tx.nombre_territorio(terr)
        alias_terr = {plano(a) for a in tx.territorios[terr]["alias"]}
        terms = [t for t in terms if t not in alias_terr]  # el topónimo pasa a ser filtro, no palabra a buscar
    if not terms and not terr:
        return terms, [], ctx
    terms, ctx["correcciones"] = corregir(terms, docs, tx)
    hoy = datetime.date.fromisoformat(hoy) if hoy else datetime.date.today()

    def puntuar(filtro_terr):
        res = []
        for d in docs:
            if filtro_terr and filtro_terr not in d["territorios"]:
                continue
            hc, hb = hits(d["cab"], terms, tx), hits(d["cuerpo"], terms, tx)
            if terms and not hc and not hb:
                continue
            pts = 5 * len(hc) + 2 * len(set(hb) - set(hc))
            if d["col"] == "articles":
                pts += 3
            if filtro_terr:
                pts += 4
            try:
                edad = (hoy - datetime.date.fromisoformat(d["fecha"])).days
                if edad <= 30:
                    pts += 2
            except ValueError:
                edad = None
            cobertura = (len(set(hc) | set(hb)) / len(terms)) if terms else 1.0
            res.append({**{k: d[k] for k in ("col", "id", "titulo", "fecha", "kind", "section", "url", "ghost_url", "modo", "submodo", "temas", "territorios")},
                        "puntos": pts, "cobertura": round(cobertura, 2), "en_cabecera": hc, "en_cuerpo": sorted(set(hb) - set(hc)), "dias": edad})
        res.sort(key=lambda r: (-r["puntos"], r["fecha"]), reverse=False)
        return res

    res = puntuar(terr)
    floja = bool(terr) and (not res or res[0]["cobertura"] < 0.99 or not res[0]["en_cabecera"])
    if floja:
        # nada (o nada que trate de verdad el asunto) en ese territorio: probar las comunidades vecinas y decirlo
        vecinos = []
        for v in tx.vecinos(terr):
            rv = [r for r in puntuar(v) if r["cobertura"] >= 0.99 and r["en_cabecera"]]
            if rv:
                ctx["vecinos"].append({"id": v, "nombre": tx.nombre_territorio(v), "resultados": len(rv)})
                vecinos.extend(rv)
        if vecinos:
            vistos = {r["id"] for r in res}
            res = res + [r for r in vecinos if r["id"] not in vistos]
            res.sort(key=lambda r: (-r["puntos"], r["fecha"]), reverse=False)
            ctx["aviso"] = "%s de %s; sí de %s (vecina%s)." % ("Nada" if not vecinos or not [r for r in res if terr in r["territorios"]] else "Poco",
                                                              ctx["territorio_nombre"], ", ".join(v["nombre"] for v in ctx["vecinos"]), "s" if len(ctx["vecinos"]) > 1 else "")
        elif not res:
            ctx["aviso"] = "No hay piezas de %s ni de sus comunidades vecinas." % ctx["territorio_nombre"]
            res = puntuar(None)  # como último recurso, el asunto sin territorio
    return terms, res[:limite], ctx


def veredicto(terms, res, ctx=None):
    arts = [r for r in res if r["col"] == "articles"]
    if ctx and (ctx.get("vecinos") or (ctx.get("aviso") and ctx.get("territorio"))):
        return "parcial" if res else "sin_cobertura"
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
    ap.add_argument("--territorio", help="id de territorio (cantabria, estado, ue…) para filtrar aunque la consulta no lo nombre")
    ap.add_argument("--vertical", default="movilidad")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    tx = Taxonomia(a.vertical)
    docs = cargar(a.data)
    terms, res, ctx = buscar(a.consulta, docs, a.hoy, a.limite, tx, a.territorio)
    v = veredicto(terms, res, ctx)
    out = {"consulta": a.consulta, "terminos": terms, "veredicto": v, "documentos": len(docs), "contexto": ctx, "resultados": res}
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return
    print("Consulta: %s · términos: %s · veredicto: %s (%d documentos)" % (a.consulta, ", ".join(terms), v, len(docs)))
    if ctx["territorio"]:
        print("Territorio: %s" % ctx["territorio_nombre"])
    if ctx["correcciones"]:
        print("¿Quiso decir? " + ", ".join("%s → %s" % kv for kv in ctx["correcciones"].items()))
    if ctx["aviso"]:
        print("Aviso: " + ctx["aviso"])
    for r in res:
        print("%3d  %-9s %s  %s  [%s] %s/%s %s cab=%s cuerpo=%s" % (r["puntos"], r["col"], r["fecha"], r["titulo"][:70], r["id"][:40], r["modo"] or "-", r["submodo"] or "-",
                                                                  ",".join(r["territorios"]), ",".join(r["en_cabecera"]), ",".join(r["en_cuerpo"])))


if __name__ == "__main__":
    main()
