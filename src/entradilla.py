#!/usr/bin/env python3
"""MOTICIAS · Entradilla: el texto corto de cada pieza que se ve en las tarjetas, en los listados y al compartir.

Decisión de Rainer (17-11-2026, cambio OpenSpec `entradilla-y-linkedin`): «abajo se corta el texto de la entradilla
abruptamente; no generes entradillas que no quepan en el resumen». Ghost guarda como mucho 300 caracteres en el
resumen de un post (`custom_excerpt`) y el publicador mandaba los 300 primeros del bloque «De qué trata» (`summary`,
60–110 palabras): todas las tarjetas acababan a media palabra.

Regla: cada pieza lleva su propio campo `entradilla`, escrito para caber —frases completas, como mucho
`editorial.entradilla.max` caracteres (280), sin puntos suspensivos ni saltos de línea—. El `summary` no cambia: sigue
abriendo la pieza. Ningún texto se corta ya a media palabra: si una pieza no trae entradilla válida, se usan las frases
completas del `summary` que quepan y, solo si ni la primera cabe, un corte por palabra con «…».

  python3 -I src/entradilla.py validar              todas las piezas de data/articles (sale con 1 si alguna falla)
  python3 -I src/entradilla.py proponer <fichero>   propone la entradilla de una pieza a partir de su summary
  python3 -I src/entradilla.py migrar               escribe la entradilla en las piezas que no la tienen y cuyo summary
                                                    da frases completas que caben; lista las que hay que escribir a mano

Solo biblioteca estándar. Lo usan src/ghost_publish.py (resumen del post), src/redaccion.py (editor del gestor),
src/export_search_index.py (tarjetas de las secciones), src/compartir.py (LinkedIn) y api/gestor.py.
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMITE_GHOST = 300  # lo que admite `custom_excerpt`; por encima Ghost rechaza el post
MAX = 280           # límite editorial por defecto (verticals/<id>.json → editorial.entradilla.max)
MIN = 60

# Abreviaturas tras las que un punto no cierra la frase.
_ABREV = {"art", "arts", "núm", "num", "n", "sr", "sra", "sres", "d", "dña", "dr", "dra", "ud", "uds", "av", "avda", "c", "ctra",
          "pág", "págs", "apdo", "aprox", "etc", "ej", "p", "ee", "uu", "s", "a", "l", "u", "excmo", "ilmo", "vol", "cap", "ss",
          "km", "h", "min", "máx", "mín", "tel", "dpto", "admón", "cía", "prof", "fdo", "vs", "cf", "op", "cit", "ref"}
_FIN = ".!?"
_CIERRES = "»”\")]’'"


def limpio(texto):
    return " ".join(str(texto or "").split())


def config(vertical=None):
    c = ((vertical or {}).get("editorial") or {}).get("entradilla") or {}
    return {"max": min(int(c.get("max") or MAX), LIMITE_GHOST), "min": int(c.get("min") or MIN)}


def frases(texto):
    """Parte un texto en frases sin romper abreviaturas (art. 25, S.L., n.º 3), iniciales (G. Jordan) ni cifras (1.500)."""
    t = limpio(texto)
    out, ini, i = [], 0, 0
    while i < len(t):
        if t[i] in _FIN or t[i] == "…":
            j = i + 1
            while j < len(t) and (t[j] in _FIN or t[j] in _CIERRES or t[j] == "…"):
                j += 1
            if j >= len(t):
                break
            if t[j] == " " and j + 1 < len(t) and (t[j + 1].isupper() or t[j + 1].isdigit() or t[j + 1] in "«“\"¿¡(—"):
                previa = re.search(r"([\wºª]+)$", t[ini:i])
                palabra = (previa.group(1) if previa else "").lower()
                es_abrev = t[i] == "." and (palabra in _ABREV or (len(palabra) == 1 and palabra.isalpha()) or palabra.endswith(("º", "ª")))
                if not es_abrev:
                    out.append(t[ini:j].strip())
                    ini = j + 1
            i = j
        else:
            i += 1
    resto = t[ini:].strip()
    if resto:
        out.append(resto)
    return out


def acaba_bien(texto):
    """¿Termina en frase completa? Punto, interrogación o exclamación (con comillas o paréntesis de cierre), sin «…»."""
    t = limpio(texto).rstrip(_CIERRES)
    return bool(t) and t[-1] in _FIN and not t.endswith("...")


def proponer(texto, n=MAX):
    """Las frases completas del principio de `texto` que caben en `n` caracteres, o None si ni la primera cabe."""
    out = ""
    for f in frases(texto):
        cand = (out + " " + f).strip()
        if len(cand) > n:
            break
        out = cand
    return out if out and acaba_bien(out) else None


def recortar(texto, n=LIMITE_GHOST):
    """Nunca a media palabra: el texto entero si cabe; si no, sus frases completas que quepan; si ni la primera cabe,
    corte en el último espacio con «…» (se nota que sigue, no parece un error)."""
    t = limpio(texto)
    if len(t) <= n:
        return t
    p = proponer(t, n)
    if p:
        return p
    corte = t[: n - 1].rsplit(" ", 1)[0].rstrip(" ,;:—–-(«“\"")
    return corte + "…"


def problemas(texto, cfg=None):
    """Lista de motivos por los que `texto` no vale como entradilla (vacía = vale)."""
    cfg = cfg or config()
    crudo = str(texto or "")
    t = limpio(crudo)
    if not t:
        return ["falta la entradilla"]
    out = []
    if len(t) > cfg["max"]:
        out.append("tiene %d caracteres y el máximo es %d: no cabría entera en las tarjetas" % (len(t), cfg["max"]))
    if len(t) < cfg["min"]:
        out.append("es demasiado corta (%d caracteres; mínimo %d)" % (len(t), cfg["min"]))
    if "\n" in crudo.strip():
        out.append("lleva saltos de línea: es un solo párrafo")
    if "…" in t or "..." in t:
        out.append("lleva puntos suspensivos: tiene que ser una frase completa")
    elif not acaba_bien(t):
        out.append("no termina en frase completa (punto final)")
    return out


def de(a, n=LIMITE_GHOST):
    """La entradilla que se enseña de la pieza `a`: su campo `entradilla` si cabe; si no, lo que quepa entero del
    `summary` (o del subtítulo). Es lo que va a Ghost, a las tarjetas y a LinkedIn. Nunca corta a media palabra."""
    e = limpio(a.get("entradilla"))
    if e and len(e) <= n:
        return e
    return recortar(e or a.get("summary") or a.get("subtitle") or "", n)


def validar_pieza(a, cfg=None):
    return problemas(a.get("entradilla"), cfg)


def _vertical(nombre="movilidad"):
    with open(os.path.join(ROOT, "verticals", nombre + ".json"), encoding="utf-8") as fh:
        return json.load(fh)


def _piezas():
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "articles", "*.json"))):
        with open(p, encoding="utf-8") as fh:
            yield p, json.load(fh)


def guardar(ruta, a):
    """Escribe la pieza sin mover lo demás: si el fichero tenía las claves ordenadas, sigue ordenado; si no, conserva
    su orden (las claves nuevas quedan al final). Así el historial solo enseña lo que cambió."""
    ordenado = True
    try:
        with open(ruta, encoding="utf-8") as fh:
            crudo = fh.read()
        ordenado = json.dumps(json.loads(crudo), ensure_ascii=False, indent=1, sort_keys=True) == crudo.rstrip("\n")
    except (OSError, ValueError):
        pass
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(a, fh, ensure_ascii=False, indent=1, sort_keys=ordenado)
        fh.write("\n")


def main(argv):
    orden = argv[1] if len(argv) > 1 else ""
    cfg = config(_vertical())
    if orden == "validar":
        mal = [(a["id"], pr) for _, a in _piezas() for pr in [validar_pieza(a, cfg)] if pr]
        for pid, pr in mal:
            print("%s: %s" % (pid, "; ".join(pr)))
        print(json.dumps({"piezas": sum(1 for _ in _piezas()), "con_problemas": len(mal), "max": cfg["max"]}, ensure_ascii=False))
        return 1 if mal else 0
    if orden == "proponer" and len(argv) > 2:
        with open(argv[2], encoding="utf-8") as fh:
            a = json.load(fh)
        p = proponer(a.get("summary"), cfg["max"])
        print(json.dumps({"id": a.get("id"), "entradilla": p, "caracteres": len(p or ""), "max": cfg["max"],
                          "nota": None if p else "la primera frase del summary no cabe: escribe la entradilla a mano, con los mismos hechos"},
                         ensure_ascii=False, indent=1))
        return 0 if p else 1
    if orden == "migrar":
        hechas, a_mano = 0, []
        for ruta, a in _piezas():
            if not validar_pieza(a, cfg):
                continue
            p = proponer(a.get("summary"), cfg["max"])
            if not p or problemas(p, cfg):
                a_mano.append(a["id"])
                continue
            a["entradilla"] = p
            guardar(ruta, a)
            hechas += 1
        print(json.dumps({"escritas": hechas, "a_mano": a_mano}, ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
