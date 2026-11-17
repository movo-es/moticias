#!/usr/bin/env python3
"""MOTICIAS · «La voz del editor»: la imagen de cada columna (cambio OpenSpec `voz-visual`, 17-11-2026).

Decisión de Rainer (17-11-2026): «La voz del editor tiene que quedar mucho más bonito y visual: nada de banners que
compitan arriba (solo al final) y siempre con una buena imagen bien seleccionada».

La columna se abre con su imagen a toda la anchura y el titular encima (app/public/sitio/m.js, apartado 9), así que la
imagen no es un adorno: sin ella no hay columna, y una foto pequeña o vertical se ve mal. Aquí están las comprobaciones
que se pueden hacer sin mirar la foto (que exista, que sea horizontal, que tenga ancho suficiente, crédito, licencia y
texto alternativo). Que sea buena —nítida, del asunto, con una idea visual clara— lo decide quien la elige mirándola
(docs/tarea-voz-del-editor.md, paso 3) y, al final, el editor jefe al aprobarla.

  python3 -I src/voz.py validar     las columnas pendientes: sale con 1 si a alguna le falta la imagen o no cumple
  python3 -I src/voz.py informe     todas las columnas, también las publicadas, con sus avisos

Las medidas viven en verticals/<id>.json → voz_del_editor.imagen. Solo biblioteca estándar.
"""
import glob, json, os, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POR_DEFECTO = {"ancho_min": 1600, "proporcion_min": 1.3, "candidatas": 3}


def config(vertical=None):
    c = dict(POR_DEFECTO)
    c.update(((vertical or {}).get("voz_del_editor") or {}).get("imagen") or {})
    return c


def medidas(ruta):
    """(ancho, alto) de un JPEG, PNG o WebP leyendo solo la cabecera, o None si no se puede."""
    try:
        with open(ruta, "rb") as fh:
            b = fh.read(32)
            if b[:8] == b"\x89PNG\r\n\x1a\n":
                return struct.unpack(">II", b[16:24])
            if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
                fh.seek(0)
                d = fh.read(64)
                if d[12:16] == b"VP8X":
                    return (int.from_bytes(d[24:27], "little") + 1, int.from_bytes(d[27:30], "little") + 1)
                if d[12:16] == b"VP8 ":
                    return (struct.unpack("<H", d[26:28])[0] & 0x3FFF, struct.unpack("<H", d[28:30])[0] & 0x3FFF)
                return None
            if b[:2] != b"\xff\xd8":
                return None
            fh.seek(2)
            while True:
                m = fh.read(2)
                if len(m) < 2 or m[0] != 0xFF:
                    return None
                while m[1] == 0xFF:  # relleno
                    m = bytes([0xFF]) + fh.read(1)
                if m[1] in (0xD8, 0x01) or 0xD0 <= m[1] <= 0xD7:
                    continue
                largo = struct.unpack(">H", fh.read(2))[0]
                if 0xC0 <= m[1] <= 0xCF and m[1] not in (0xC4, 0xC8, 0xCC):
                    alto, ancho = struct.unpack(">HH", fh.read(5)[1:5])
                    return (ancho, alto)
                fh.seek(largo - 2, 1)
    except (OSError, struct.error, IndexError):
        return None


def ruta_local(a):
    src = ((a.get("image") or {}).get("orig_src") or (a.get("image") or {}).get("src") or "")
    return os.path.join(ROOT, "portal", src) if src.startswith("img/") else None


def problemas_imagen(a, vertical=None):
    """(impiden, avisos) sobre la imagen de una columna. `impiden`: sin esto no se aprueba (falta la imagen, el crédito o
    la licencia). `avisos`: se puede aprobar, pero conviene pedir otra (pequeña, vertical, sin texto alternativo)."""
    c = config(vertical)
    im = a.get("image") or {}
    if not (im.get("src") or "").strip():
        return ["falta la imagen: «La voz del editor» sale siempre con una"], []
    impiden, avisos = [], []
    if not (im.get("credit") or "").strip():
        impiden.append("la imagen no tiene crédito")
    if not (im.get("license") or "").strip():
        impiden.append("la imagen no dice su licencia")
    if not (im.get("alt") or "").strip():
        avisos.append("la imagen no tiene texto alternativo")
    ruta = ruta_local(a)
    m = medidas(ruta) if ruta and os.path.exists(ruta) else None
    if m:
        ancho, alto = m
        if ancho < c["ancho_min"]:
            avisos.append("la imagen mide %d px de ancho y se abre a toda la anchura: por debajo de %d se ve blanda" % (ancho, c["ancho_min"]))
        if alto and ancho / alto < c["proporcion_min"]:
            avisos.append("la imagen es casi cuadrada o vertical (%d × %d): el titular va encima y pide una horizontal" % (ancho, alto))
    return impiden, avisos


def columnas():
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "articles", "*.json"))):
        with open(p, encoding="utf-8") as fh:
            a = json.load(fh)
        if a.get("kind") == "opinion":
            yield a


def main(argv):
    orden = argv[1] if len(argv) > 1 else ""
    if orden not in ("validar", "informe"):
        print(__doc__)
        return 2
    with open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8") as fh:
        v = json.load(fh)
    mal, out = 0, []
    for a in columnas():
        pendiente = a.get("status") in ("pendiente", "borrador")
        if orden == "validar" and not pendiente:
            continue
        impiden, avisos = problemas_imagen(a, v)
        if pendiente and (impiden or avisos):
            mal += 1
        out.append({"id": a["id"], "status": a.get("status"), "impiden": impiden, "avisos": avisos})
    print(json.dumps({"columnas": out, "con_problemas": mal, "medidas": config(v)}, ensure_ascii=False, indent=1))
    return 1 if (orden == "validar" and mal) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
