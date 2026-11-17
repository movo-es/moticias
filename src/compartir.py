#!/usr/bin/env python3
"""MOTICIAS · Compartir una pieza en redes desde el gestor (cambio OpenSpec `entradilla-y-linkedin`, 17-11-2026).

Decisión de Rainer (17-11-2026): «Crea en el gestor del editor un botón compartir en LinkedIn (con la imagen y la
entradilla y un enlace "suscríbete gratis para seguir leyendo: moticias.com - noticias con M de movilidad y
transportes")».

Qué hace: compone el texto de la publicación —la entradilla de la pieza, la línea de suscripción con el enlace a la
pieza y la firma— y la dirección que abre el redactor de LinkedIn con ese texto ya escrito. La imagen no viaja en el
enlace (LinkedIn no lo admite): la pone LinkedIn con la tarjeta del enlace, que toma la foto, el titular y la entradilla
de la propia página. Nada se publica solo: el botón deja la publicación preparada y la persona pulsa «Publicar» en su
LinkedIn (regla de siempre: nada de mensajes automáticos en LinkedIn).

Los textos y los parámetros de medición viven en verticals/<id>.json → redes.linkedin; aquí no hay nada de un vertical.
Solo biblioteca estándar.

  python3 -I src/compartir.py <id de la pieza>     enseña el texto y el enlace que prepararía el botón
"""
import json, os, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import entradilla as EN  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_LINKEDIN = 3000  # caracteres que admite una publicación

_POR_DEFECTO = {"texto": "{entradilla}\n\nSuscríbete gratis para seguir leyendo: {url}\n\n{firma}", "firma": "",
                "utm": {"utm_source": "linkedin", "utm_medium": "social"},
                "abrir": "https://www.linkedin.com/feed/?shareActive=true&text={texto}"}


def config(vertical):
    c = dict(_POR_DEFECTO)
    c.update(((vertical or {}).get("redes") or {}).get("linkedin") or {})
    return c


def url_pieza(a, vertical, utm=None):
    base = ((vertical or {}).get("ghost") or {}).get("url") or "https://www.%s" % (vertical or {}).get("domain", "moticias.com")
    url = "%s/%s/" % (base.rstrip("/"), a["id"])
    return url + ("?" + urllib.parse.urlencode(utm) if utm else "")


def linkedin(a, vertical):
    """Lo que necesita el botón «Compartir en LinkedIn» de una pieza, o None si no se puede compartir (no está publicada
    o la red está apagada). Devuelve {"texto", "url", "abrir", "plantilla", "entradilla", "titulo", "max"}:
    `plantilla` es la dirección con `{texto}` por si la persona retoca el texto antes de compartir."""
    c = config(vertical)
    if not c.get("activo", True) or (a.get("status") or "publicado") != "publicado":
        return None
    ent = EN.de(a, EN.LIMITE_GHOST)
    url = url_pieza(a, vertical, c.get("utm"))
    texto = c["texto"].format(entradilla=ent, url=url, firma=c.get("firma") or "", titulo=a.get("title") or "").strip()
    texto = "\n".join(l.rstrip() for l in texto.split("\n"))[:MAX_LINKEDIN]
    return {"texto": texto, "url": url, "entradilla": ent, "titulo": a.get("title") or "", "plantilla": c["abrir"], "max": MAX_LINKEDIN,
            "abrir": c["abrir"].format(texto=urllib.parse.quote(texto, safe=""), url=urllib.parse.quote(url, safe=""))}


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    with open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8") as fh:
        v = json.load(fh)
    with open(os.path.join(ROOT, "data", "articles", argv[1] + ".json"), encoding="utf-8") as fh:
        a = json.load(fh)
    r = linkedin(a, v)
    print(json.dumps(r, ensure_ascii=False, indent=1) if r else "La pieza no está publicada: no se comparte.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
