#!/usr/bin/env python3
"""MOTICIAS · Índice del buscador web (estático). Solo biblioteca estándar.

  python3 -I src/export_search_index.py [--salida app/public/buscador/index.json] [--base https://www.moticias.com]

Genera un único JSON que el tema de Ghost (y la maqueta) cargan una vez: taxonomía (nombres y alias de modos, temas y territorios,
vecinos), grupos de sinónimos y una entrada compacta por pieza publicada (sin cuerpo: cabecera, resumen corto, ejes, fecha, foto, URL).
Con 74 piezas pesa ~210 KB sin comprimir (≈ 50 KB con gzip); con 500, ~1,4 MB (≈ 350 KB). Cuando pase de 2 MB se partirá por años.
Cada entrada lleva su tipo de contenido (`tc`) y su marca (`mc`), y `dir: true` si la firma el editor jefe (el módulo y el
dato interno: desde el 15-11-2026 no hay módulo ni botón «Análisis del director»). Junto al índice se escribe `tipos.json` (id → [tipo, marca],
unos pocos KB), que `app/public/sitio/m.js` usa para poner la marca junto a cada titular en los listados de moticias.com.
Se regenera en cada edición diaria (paso 7 ter) y se sirve desde Vercel en https://app.moticias.com/buscador/index.json con CORS
para www.moticias.com (vercel.json); el tema de Ghost lo carga una vez por visita y busca en el navegador.
"""
import argparse, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from taxonomia import Taxonomia, plano  # noqa: E402
import tipos as T  # noqa: E402  (tipo de contenido y su marca; openspec tipos-de-contenido)
import entradilla as EN  # noqa: E402  (la entradilla de las tarjetas: frases completas; openspec entradilla-y-linkedin)


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
        "id": a["id"], "t": a.get("title"), "k": a.get("kicker"), "s": a.get("subtitle"), "r": EN.de(a),
        "d": a.get("date"), "kind": a.get("kind"), "au": a.get("author"), "f": a.get("featured") or 0,
        "m": a.get("modo"), "sm": a.get("submodo"), "te": a.get("temas") or [], "tr": a.get("territorios") or [], "tg": a.get("tags") or [],
        "img": img.get("src"), "gi": gi, "alt": img.get("alt"), "sec": a.get("section"), "url": "%s/%s/" % (base.rstrip("/"), a["id"]),
        "pat": bool(a.get("menciones")) or bool(a.get("sponsored_by")),
        # tipo de contenido (editorial · noticia · nota_de_prensa · patrocinado) y la marca que ve el lector
        "tc": T.tipo(a, "articles"), "mc": T.marca(a, "articles"), "dir": T.es_del_editor_jefe(a),
        # etiquetas comunes (15-11-2026): medio, modos, importancia, fecha del hecho, fecha límite y si caduca (orden del lector)
        "md": a.get("medio"), "mo": a.get("modos") or [], "im": a.get("importancia"), "fh": a.get("event_date"),
        "fl": a.get("fecha_limite"), "nc": Taxonomia.no_caduca(a),
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
        if (d.get("published_at") or "") > __import__("datetime").datetime.now().astimezone().isoformat():
            continue  # programada (p. ej. «La voz del editor» aprobada que sale el lunes): aún no se ve
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
        "mercancias": [k for k, x in tx.modos_t.items() if x["mercancias"]],
        "piezas": piezas,
        "menu": menu(tx, piezas, base),
        "agenda": agenda(base),
    }


def agenda(base="https://www.moticias.com"):
    """Citas visibles de moticias.com/agenda/ (cambio agenda-de-eventos): el buscador las encuentra por título, ciudad y tema."""
    try:
        import eventos as EV
    except ImportError:
        return []
    return [{"id": e["id"], "t": e["titulo"], "c": e["ciudad"], "i": e["inicio"], "f": EV.fin_de(e), "te": e["tema"], "ter": e["territorio"],
             "u": "%s/agenda/#%s" % (base, e["id"])} for e in EV.visibles([EV.limpio(x) for x in EV.cargar()])]


def menu(tx, piezas, base="https://www.moticias.com"):
    """Menú con submenús (cambio menu-y-voz-del-editor, 16-11-2026): medios con sus modos, logística (modos de mercancías de
    todos los medios), temas, regiones y «La voz del editor», con cuántas piezas publicadas hay en cada opción. Las opciones
    sin piezas no se enseñan; un medio apagado (espacio) tampoco."""
    import ghost_publish as G  # noqa: E402
    b = base.rstrip("/")
    cuenta = lambda f: sum(1 for p in piezas if f(p))  # noqa: E731
    modo = lambda mid: {"id": mid, "nombre": tx.modos_t[mid]["nombre"], "url": "%s/tag/%s/" % (b, G.slug_modo(tx, mid)),  # noqa: E731
                        "n": cuenta(lambda p: mid in (p.get("mo") or []))}
    medios = []
    for mid, m in tx.medios.items():
        if not m.get("activo") or mid == "varios":
            continue
        ms = [modo(k) for k, x in tx.modos_t.items() if x["medio"] == mid and not x["mercancias"]]
        medios.append({"id": mid, "nombre": m["nombre"], "url": "%s/%s/" % (b, mid), "n": cuenta(lambda p: p.get("md") == mid),
                       "modos": [x for x in ms if x["n"]]})
    logi = [modo(k) for k, x in tx.modos_t.items() if x["mercancias"]]
    temas = [{"id": t, "nombre": x["nombre"], "url": "%s/tag/tema-%s/" % (b, t), "n": cuenta(lambda p: t in (p.get("te") or []))}
             for t, x in tx.temas.items()]
    regiones = [{"id": t, "nombre": x.get("nombre_corto") or x["nombre"], "tipo": x["tipo"], "url": "%s/tag/t-%s/" % (b, t),
                 "n": cuenta(lambda p: t in (p.get("tr") or []))} for t, x in tx.territorios.items()]
    voz = [{"id": p["id"], "t": p.get("t"), "url": p.get("url"), "d": p.get("d"), "img": p.get("gi")} for p in piezas if p.get("kind") == "opinion"]
    # Portada (16-11-2026): últimos titulares (columna izquierda del banner premium) y «Lo esencial» por columna (el tema la dejaba vacía).
    import secciones as SE  # noqa: E402
    SE.MERCANCIAS.update(k for k, x in tx.modos_t.items() if x["mercancias"])
    v = json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))
    reglas = SE.reglas(v)
    corto = lambda p: {"t": p.get("t"), "url": p.get("url"), "mc": p.get("mc")}  # noqa: E731
    ultimas = [corto(p) for p in piezas if p.get("kind") != "opinion"][:12]
    esencial = {s: [corto(p) for p in piezas if SE.pertenece(p, reglas[s])][:8] for s in ("tierra", "mar", "aire", "regulacion", "licitaciones") if s in reglas}
    return {"ultimas": ultimas, "esencial": esencial, "medios": medios, "logistica": {"nombre": "Logística", "url": "%s/logistica/" % b, "modos": [x for x in logi if x["n"]]},
            "temas": [x for x in temas if x["n"]], "secciones": [{"nombre": "Regulación", "url": "%s/regulacion/" % b}, {"nombre": "Licitaciones", "url": "%s/licitaciones/" % b}],
            "regiones": [x for x in regiones if x["n"]], "analisis": {"nombre": "Análisis", "url": "%s/analisis/" % b},
            "voz": {"nombre": "La voz del editor", "url": "%s/la-voz-del-editor/" % b, "piezas": voz[:12]}}


def textos(out):
    """(index.json, tipos.json) como texto, listos para escribir o subir."""
    ligero = {"generado": out["generado"], "piezas": {p["id"]: [p["tc"], p["mc"]] for p in out["piezas"]}, "menu": out.get("menu")}
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
