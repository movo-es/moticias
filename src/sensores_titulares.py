#!/usr/bin/env python3
"""Titulares de los medios monitorizados, recogidos por el servidor sin IA (decisión de Rainer, 21-11-2026).

La edición del 21-11-2026 gastó casi todo su tope de tokens leyendo con IA las portadas de los medios. Desde entonces el
cron `sensores` de Vercel baja cada hora (de 06:00 a 23:00, hora de Madrid) el RSS, el archivo del día o la portada de cada
medio de `verticals/<vertical>.json → sensores.medios`, saca titular, enlace, fecha y entradilla, y lo guarda en la base
privada (`sensores_titulares`, migración 017). La edición lee esa lista en vez de abrir cada medio. Un titular con pinta de
gran noticia (`sensores.grandes`) va además a la cola del editor y encarga un barrido.

  python3 -I src/sensores_titulares.py probar [--medio ID]     (con red: enseña lo que saca de cada medio; no guarda nada)

Solo biblioteca estándar. Los titulares son información pública de cada medio; aquí no se guarda el texto de los artículos.
"""
import datetime, email.utils, html, json, os, re, sys, unicodedata, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 MoticiasSensores/1.0"


def vertical(nombre="movilidad"):
    return json.load(open(os.path.join(ROOT, "verticals", nombre + ".json"), encoding="utf-8"))


def plano(s):
    return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()


def bajar(url, tope=3_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/html;q=0.9, */*;q=0.5",
                                               "Accept-Language": "es-ES,es;q=0.9"})
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read(tope)
        cs = r.headers.get_content_charset()
    return raw, cs


def texto(raw, cs=None):
    for c in [cs, "utf-8", "latin-1"]:
        if c:
            try:
                return raw.decode(c)
            except (UnicodeDecodeError, LookupError):
                continue
    return raw.decode("utf-8", "replace")


def limpio(s, n=None):
    s = re.sub(r"<[^>]+>", " ", html.unescape(str(s or "")))
    s = re.sub(r"\s+", " ", html.unescape(s)).strip()
    return s[:n].rstrip() if n else s


def _fecha(s):
    """Fecha de publicación del RSS o Atom como ISO en UTC, o None: nunca se deduce."""
    if not s:
        return None
    try:
        d = email.utils.parsedate_to_datetime(s.strip())
    except (TypeError, ValueError, IndexError):
        try:
            d = datetime.datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=datetime.timezone.utc)
    return d.astimezone(datetime.timezone.utc).isoformat(timespec="seconds")


def de_rss(raw):
    """Entradas de un RSS 2.0 o un Atom: [{titulo, url, publicado_at, entradilla}]."""
    raiz = ET.fromstring(raw)
    out = []
    for it in raiz.iter():
        etiqueta = it.tag.rsplit("}", 1)[-1]
        if etiqueta not in ("item", "entry"):
            continue
        campos = {}
        for h in it:
            k = h.tag.rsplit("}", 1)[-1]
            if k == "link" and h.get("href") and h.get("rel", "alternate") == "alternate":
                campos.setdefault("link", h.get("href"))
            elif k not in campos and (h.text or "").strip():
                campos[k] = h.text.strip()
        titulo, url = limpio(campos.get("title"), 300), (campos.get("link") or "").strip()
        if titulo and url.startswith("http"):
            out.append({"titulo": titulo, "url": url, "publicado_at": _fecha(campos.get("pubDate") or campos.get("published") or campos.get("updated") or campos.get("date")),
                        "entradilla": limpio(campos.get("description") or campos.get("summary") or "", 300) or None})
    return out


def de_html(pagina, base, patron=None, excluye=None):
    """Titulares de una portada o de un archivo por día: los enlaces del mismo sitio cuyo texto parece un titular."""
    host = urllib.parse.urlparse(base).netloc.replace("www.", "")
    out, vistos = [], set()
    for m in re.finditer(r"<a\b[^>]*?href=[\"']([^\"'#]+)[\"'][^>]*>(.*?)</a>", pagina, re.S | re.I):
        href = html.unescape(m.group(1)).strip()
        url = urllib.parse.urljoin(base, ("https://" + href) if href.startswith("www.") else href)
        t = limpio(m.group(2))
        if urllib.parse.urlparse(url).netloc.replace("www.", "") != host or url in vistos:
            continue
        if patron and not re.search(patron, url):
            continue
        if excluye and re.search(excluye, url):
            continue
        if not ((28 if patron else 35) <= len(t) <= 240) or len(t.split()) < (4 if patron else 5):
            continue
        vistos.add(url)
        out.append({"titulo": t, "url": url, "publicado_at": None, "entradilla": None})
    return out[:80]


def es_grande(titulo, reglas):
    """¿Tiene pinta de gran noticia? Reglas del vertical (`sensores.grandes`): cada una es una lista de expresiones que deben
    aparecer todas en el titular (sin acentos). Es un aviso para que lo mire la redacción, no un juicio."""
    t = plano(titulo)
    for regla in reglas or []:
        if all(re.search(x, t) for x in regla):
            return True
    return False


def recoger_medio(m, ahora):
    """Titulares de un medio por su mejor vía: RSS, archivo por día (hoy y ayer) o portada. Devuelve (titulares, error)."""
    errores, out = [], []
    vias = []
    if m.get("rss"):
        vias.append(("rss", m["rss"]))
    if m.get("archivo"):
        for d in (ahora, ahora - datetime.timedelta(days=1)):
            vias.append(("archivo", d.strftime(m["archivo"])))
    if m.get("portada"):
        vias.append(("portada", m["portada"]))
    for via, url in vias:
        try:
            raw, cs = bajar(url)
            filas = de_rss(raw) if via == "rss" else de_html(texto(raw, cs), url, m.get("patron"), m.get("excluye"))
            if via == "archivo":
                dia = re.search(r"(\d{4})/(\d{2})/(\d{2})", url)
                for f in filas:  # el archivo del día da la fecha, no la hora
                    f["publicado_at"] = "%s-%s-%sT00:00:00+00:00" % dia.groups() if dia else None
            out += filas
            if via == "rss" and filas:
                break  # con el RSS basta; el archivo y la portada son el plan B
        except (urllib.error.URLError, ET.ParseError, TimeoutError, ValueError, OSError) as e:
            errores.append("%s: %s" % (via, str(getattr(e, "reason", None) or e)[:120]))
    vistos, unicos = set(), []
    for f in out:
        if f["url"] not in vistos:
            vistos.add(f["url"])
            unicos.append(dict(f, medio=m["id"]))
    return unicos, ("; ".join(errores) if errores and not unicos else None)


def recoger(v=None, ahora=None, solo=None):
    v = v or vertical()
    conf = v.get("sensores") or {}
    ahora = ahora or datetime.datetime.now(datetime.timezone.utc)
    titulares, estado = [], {}
    for m in conf.get("medios") or []:
        if solo and m["id"] != solo:
            continue
        filas, error = recoger_medio(m, ahora)
        for f in filas:
            f["grande"] = es_grande(f["titulo"], conf.get("grandes"))
        titulares += filas
        estado[m["id"]] = {"n": len(filas), "error": error}
    return titulares, estado


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "probar":
        solo = sys.argv[sys.argv.index("--medio") + 1] if "--medio" in sys.argv else None
        titulares, estado = recoger(solo=solo)
        for mid, e in estado.items():
            print("%-24s %3d titulares %s" % (mid, e["n"], ("· ERROR " + e["error"]) if e["error"] else ""))
            for f in [t for t in titulares if t["medio"] == mid][:3]:
                print("     %s %s| %s" % ((f["publicado_at"] or "sin fecha")[:16], "[GRANDE] " if f["grande"] else "", f["titulo"][:100]))
        print("grandes:", [t["titulo"][:90] for t in titulares if t["grande"]])
        return
    print(__doc__)


if __name__ == "__main__":
    main()
