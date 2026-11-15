#!/usr/bin/env python3
"""MOTICIAS · Tipos de contenido (cambio OpenSpec `tipos-de-contenido`, aprobado por Rainer el 15-11-2026). Solo biblioteca estándar.

Cuatro tipos, siempre distinguibles para el lector, en los datos y en Ghost:

  editorial       análisis y reportajes con firma   «Análisis del director» (solo si firma el director) · «Análisis» · «Reportaje»
  noticia         noticias                            «Noticia»
  nota_de_prensa  comunicado de un emisor externo     «Nota de prensa · Comunicado de <emisor>»
  patrocinado     lo que anuncia un servicio          «Contenido patrocinado · servicio del grupo» · «Contenido patrocinado · <cliente>» · «Publicidad»

Este módulo es el ÚNICO sitio que deduce el tipo, lo valida y lo traduce a marca visible, etiqueta interna de Ghost y
atributo `rel` de los enlaces. Los textos viven en `verticals/<id>.json → tipos_de_contenido`; aquí no hay ninguno.

Uso:
  python3 -I src/tipos.py migrar      # pone `tipo_contenido` donde falte (piezas, notas, anuncios); no toca texto, firma ni fechas
  python3 -I src/tipos.py validar     # sale con error si un documento no lo tiene o no cuadra con sus otros campos
  python3 -I src/tipos.py informe     # recuento por tipo y marca
  python3 -I src/tipos.py pieza data/articles/<id>.json   # tipo, marca y etiquetas de un documento (JSON)
"""
import glob, json, os, sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIPOS = ("editorial", "noticia", "nota_de_prensa", "patrocinado")
TIPOS_ANUNCIO = ("grupo", "patrocinio", "publicidad")
COLECCIONES = {"articles": "pieza", "notas-de-prensa": "nota", "ads": "anuncio"}
_V = {}


def vertical(vid="movilidad"):
    if vid not in _V:
        _V[vid] = json.load(open(os.path.join(ROOT, "verticals", vid + ".json"), encoding="utf-8"))
    return _V[vid]


def cfg(v=None):
    return (v or vertical()).get("tipos_de_contenido") or {}


def firmas_director(v=None):
    e = (v or vertical()).get("editorial") or {}
    return {x for x in [e.get("director")] + list(e.get("director_firma_antigua") or []) if x}


def es_del_director(a, v=None):
    return (a.get("author") or "") in firmas_director(v)


def _cliente(sp):
    if isinstance(sp, dict):
        return sp.get("nombre") or sp.get("name") or sp.get("cliente") or ""
    return str(sp or "")


def _es_grupo(sp, v=None):
    """`sponsored_by` de una empresa del grupo: {grupo: true}, o el id o el nombre de una marca de `grupo.marcas`."""
    if isinstance(sp, dict) and sp.get("grupo"):
        return True
    nombres = set()
    for m in ((v or vertical()).get("grupo") or {}).get("marcas") or []:
        nombres |= {m.get("id"), m.get("nombre")} | set(m.get("productos") or [])
    return _cliente(sp) in {x for x in nombres if x} or (isinstance(sp, dict) and sp.get("producto") in nombres)


# ---------- deducir ----------
def coleccion_de(ruta):
    return os.path.basename(os.path.dirname(os.path.abspath(ruta)))


def deducir(doc, coleccion="articles"):
    """Tipo que corresponde a un documento por sus otros campos. None si no se puede saber."""
    if coleccion == "notas-de-prensa":
        return "nota_de_prensa"
    if coleccion == "ads":
        return "patrocinado"
    if doc.get("sponsored_by"):
        return "patrocinado"
    k = doc.get("kind")
    if k in ("analisis", "reportaje"):
        return "editorial"
    if k == "noticia":
        return "noticia"
    return None


def tipo(doc, coleccion="articles"):
    return doc.get("tipo_contenido") or deducir(doc, coleccion)


# ---------- traducir ----------
def marca(doc, coleccion="articles", v=None):
    """Texto que ve el lector."""
    c, t = cfg(v), tipo(doc, coleccion)
    m = c.get("marcas") or {}
    if coleccion == "ads":
        return marca_anuncio(doc, v)
    if t == "editorial":
        if doc.get("kind") == "reportaje":
            return m["reportaje"]
        return m["analisis_director"] if es_del_director(doc, v) else m["analisis"]
    if t == "noticia":
        return m["noticia"]
    if t == "nota_de_prensa":
        emisor = ((doc.get("organizacion") or {}).get("nombre") if isinstance(doc.get("organizacion"), dict) else doc.get("organizacion")) or "empresa"
        return m["nota_de_prensa"] % {"emisor": emisor}
    if t == "patrocinado":
        sp = doc.get("sponsored_by")
        return m["patrocinado_grupo"] if _es_grupo(sp, v) else m["patrocinado_cliente"] % {"cliente": _cliente(sp) or "cliente"}
    return ""


def dominios_grupo(v=None):
    """Dominios de las empresas del grupo (verticals → grupo.marcas y editor) y del propio medio."""
    v = v or vertical()
    g = v.get("grupo") or {}
    urls = [m.get("url") for m in g.get("marcas") or []] + [(g.get("editor") or {}).get("url"), "https://" + (v.get("domain") or "")]
    out = set()
    for u in urls:
        h = urlparse(u or "").hostname or ""
        if h:
            out.add(h[4:] if h.startswith("www.") else h)
    return out


def anuncio_es_del_grupo(ad, v=None):
    """Una caja anuncia un servicio del grupo si enlaza a un dominio del grupo o su anunciante es una marca del grupo."""
    v = v or vertical()
    h = urlparse(str(ad.get("url") or "")).hostname or ""
    h = h[4:] if h.startswith("www.") else h
    if str(ad.get("url") or "").startswith("mailto:"):
        h = str(ad["url"]).split("@", 1)[-1].split("?", 1)[0].lower()
    if any(h == dom or h.endswith("." + dom) for dom in dominios_grupo(v)):
        return True
    anunciante = (ad.get("advertiser") or "").lower()
    return any(m.get("nombre") and m["nombre"].lower() in anunciante for m in (v.get("grupo") or {}).get("marcas") or [])


def marca_anuncio(ad, v=None):
    """Etiqueta de una caja de `data/ads/` según su `type`: grupo · patrocinio (cliente) · publicidad."""
    m = cfg(v).get("marcas") or {}
    t = ad.get("type") or "publicidad"
    if t == "grupo" or anuncio_es_del_grupo(ad, v):  # lo del grupo es siempre tipo grupo, lo hayan tipado como lo hayan tipado;
        # en las cajas por niveles el lector ve solo «Contenido patrocinado» (decisión de Rainer, 15-11-2026, noche)
        return m.get("patrocinado_grupo_caja") or m["patrocinado_grupo"]
    if t == "patrocinio":
        return m["patrocinado_cliente"] % {"cliente": ad.get("advertiser") or "cliente"}
    return m["publicidad"]


def marca_mencion(v=None):
    """Etiqueta de las cajas «Contenido patrocinado» dentro del texto (siempre servicios del grupo)."""
    return (cfg(v).get("marcas") or {})["patrocinado_grupo"]


def etiquetas_ghost(doc, coleccion="articles", v=None):
    """Etiquetas internas de Ghost (las que empiezan por #) por tipo; el análisis firmado por el director lleva además la suya,
    para que el módulo y el botón «Análisis del director» filtren por firma y no por tema."""
    c = cfg(v)
    t = tipo(doc, coleccion)
    out = [c["etiquetas_ghost"][t]] if t in (c.get("etiquetas_ghost") or {}) else []
    if t == "editorial" and doc.get("kind") == "analisis" and es_del_director(doc, v) and c.get("etiqueta_analisis_director"):
        out.append(c["etiqueta_analisis_director"])
    return out


def rel(doc_o_tipo, coleccion="articles"):
    """`rel` de los enlaces que anuncian: todo lo patrocinado lleva sponsored, sin excepción."""
    t = doc_o_tipo if isinstance(doc_o_tipo, str) else tipo(doc_o_tipo, coleccion)
    return "sponsored noopener" if t == "patrocinado" else "noopener"


def en_portada(doc, coleccion="articles", v=None):
    return tipo(doc, coleccion) in (cfg(v).get("portada") or ["editorial", "noticia"])


def en_boletin(doc, coleccion="articles", v=None):
    return tipo(doc, coleccion) in (cfg(v).get("boletin") or ["editorial", "noticia"])


# ---------- validar ----------
def errores(doc, coleccion="articles", v=None):
    """Lista de motivos por los que el documento no se puede publicar (vacía si está bien)."""
    out = []
    t = doc.get("tipo_contenido")
    if not t:
        return ["falta tipo_contenido"]
    if t not in TIPOS:
        return ["tipo_contenido desconocido: %s" % t]
    d = deducir(doc, coleccion)
    if coleccion == "articles":
        if doc.get("kind") == "analisis" and doc.get("sponsored_by"):
            out.append("un análisis no puede ser contenido patrocinado")
        if doc.get("kind") == "analisis" and any(m.get("estado") == "publicada" for m in doc.get("menciones") or []):
            out.append("un análisis no lleva cajas de contenido patrocinado")
        if t == "editorial" and not doc.get("author"):
            out.append("el contenido editorial va con firma")
        if t == "nota_de_prensa":
            out.append("una nota de prensa no va en data/articles/ (va en data/notas-de-prensa/)")
    if coleccion == "notas-de-prensa" and doc.get("featured"):
        out.append("una nota de prensa no va en la portada")
    if coleccion == "ads" and doc.get("type") != "grupo" and anuncio_es_del_grupo(doc, v):
        out.append("anuncia un servicio del grupo: su tipo es «grupo» («Contenido patrocinado · servicio del grupo»)")
    if coleccion == "ads" and (doc.get("type") or "") not in TIPOS_ANUNCIO:
        out.append("tipo de anuncio desconocido: %s (admitidos: %s)" % (doc.get("type"), ", ".join(TIPOS_ANUNCIO)))
    if d and t != d and not out:
        out.append("tipo_contenido %s no cuadra con sus campos (le corresponde %s)" % (t, d))
    return out


def comprobar(doc, coleccion="articles", v=None):
    """Lanza ValueError si el documento no se puede publicar."""
    e = errores(doc, coleccion, v)
    if e:
        raise ValueError("%s: %s" % (doc.get("id", "?"), "; ".join(e)))


# ---------- ficheros ----------
def _ficheros():
    for col in COLECCIONES:
        for p in sorted(glob.glob(os.path.join(ROOT, "data", col, "*.json"))):
            yield col, p


def _guardar_con_campo(p, doc, valor):
    """Añade el campo al final sin reordenar nada (diff de una línea) y respeta el salto de línea final del fichero."""
    raw = open(p, encoding="utf-8").read()
    doc["tipo_contenido"] = valor
    out = json.dumps(doc, ensure_ascii=False, indent=1)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(out + ("\n" if raw.endswith("\n") else ""))


def migrar():
    hechos, dudas = [], []
    for col, p in _ficheros():
        doc = json.load(open(p, encoding="utf-8"))
        if doc.get("tipo_contenido"):
            continue
        t = deducir(doc, col)
        if not t:
            dudas.append(os.path.relpath(p, ROOT))
            continue
        _guardar_con_campo(p, doc, t)
        hechos.append((os.path.relpath(p, ROOT), t))
    return hechos, dudas


def validar():
    malos = []
    for col, p in _ficheros():
        doc = json.load(open(p, encoding="utf-8"))
        for e in errores(doc, col):
            malos.append("%s: %s" % (os.path.relpath(p, ROOT), e))
    return malos


def informe():
    from collections import Counter
    c = Counter()
    for col, p in _ficheros():
        doc = json.load(open(p, encoding="utf-8"))
        c[(COLECCIONES[col], tipo(doc, col) or "?", marca(doc, col))] += 1
    return c


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("migrar", "validar", "informe", "pieza"):
        sys.exit(__doc__)
    acc = sys.argv[1]
    if acc == "migrar":
        hechos, dudas = migrar()
        print("tipo_contenido añadido a %d documentos%s" % (len(hechos), "".join("\n  %s → %s" % h for h in hechos[:200])))
        if dudas:
            print("Sin poder deducir (revisar a mano):\n  " + "\n  ".join(dudas))
            sys.exit(1)
    elif acc == "validar":
        malos = validar()
        if malos:
            print("\n".join(malos))
            sys.exit("%d errores de tipo de contenido" % len(malos))
        print("tipos de contenido: todo en orden")
    elif acc == "informe":
        for (col, t, m), n in sorted(informe().items()):
            print("%-8s %-15s %4d  %s" % (col, t, n, m))
    else:
        p = sys.argv[2]
        col = coleccion_de(p)
        doc = json.load(open(p, encoding="utf-8"))
        print(json.dumps({"tipo_contenido": tipo(doc, col), "marca": marca(doc, col), "etiquetas_ghost": etiquetas_ghost(doc, col),
                          "rel": rel(doc, col), "errores": errores(dict(doc, tipo_contenido=tipo(doc, col)), col)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
