#!/usr/bin/env python3
"""MOTICIAS · Panel SEO y asistentes de IA (cambio `panel-seo-llm`, 16-11-2026). Solo biblioteca estándar.

Tres cosas, todas para la pestaña «SEO» del gestor (solo el editor jefe):
1. Propuestas de mejora ordenadas por impacto esperado, calculadas sobre `data/articles/`: título para buscadores demasiado
   largo, descripción demasiado larga, ninguna pieza relacionada enlazada, y lo que diga el asesor de los lunes
   (`docs/asesor/`). Impacto = importancia de la pieza × peso del problema × frescura (lo que no caduca pesa siempre).
2. «Hazlo con IA»: propone el arreglo (título, descripción) con la pasarela de IA de Vercel, o lo calcula (relacionadas, por
   etiquetas comunes). Los títulos, las descripciones, las relacionadas y el marcado se aplican directo con aviso y se pueden
   deshacer; lo que toque el texto de la pieza va con vista previa. El registro está en `seo_cambios` (migración 014).
3. Batería de asistentes: las preguntas fijas del vertical (`seo.preguntas`) a cada modelo (`seo.modelos`) por la pasarela de
   IA; guarda si citan moticias.com y si nombran las marcas del grupo con lo suyo (`seo.marcas`) en `seo_llm`.

  python3 -I src/seo.py propuestas [N]     # las N propuestas de más impacto (JSON)
  python3 -I src/seo.py relacionadas <id>  # las piezas relacionadas que se enlazarían
  python3 -I src/seo.py analizar "<texto>" # qué marcas nombra un texto y si las asocia con lo suyo
"""
import datetime, glob, json, os, re, sys, unicodedata, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def vertical():
    return json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))


def plano(s):
    s = unicodedata.normalize("NFKD", str(s or "")).lower()
    return "".join(c for c in s if not unicodedata.combining(c))


def articulos(data=None):
    out = {}
    for f in sorted(glob.glob(os.path.join(data or os.path.join(ROOT, "data"), "articles", "*.json"))):
        try:
            a = json.load(open(f, encoding="utf-8"))
        except ValueError:
            continue
        out[a["id"]] = a
    return out


# ---------- propuestas ----------
PESOS = {"seo_title": 3, "seo_description": 2, "relacionadas": 2}


def propuestas(arts=None, n=60):
    v = vertical()
    lim = (v.get("seo") or {}).get("limites") or {}
    arts = arts or articulos()
    hoy = datetime.date.today()
    out = []
    for a in arts.values():
        if a.get("status") != "publicado":
            continue
        imp = a.get("importancia") or 3
        try:
            dias = (hoy - datetime.date.fromisoformat(str(a.get("date"))[:10])).days
        except ValueError:
            dias = 30
        perenne = a.get("tipo_contenido") == "editorial" or a.get("kind") in ("analisis", "reportaje", "opinion")
        frescura = 1.0 if perenne else max(0.3, 1.0 - dias / 60.0)
        titulo_seo = a.get("seo_title") or a.get("title") or ""
        if len(titulo_seo) > lim.get("seo_title", 60):
            out.append({"pieza": a["id"], "tipo": "seo_title", "titulo": a.get("title"), "actual": titulo_seo,
                        "problema": "El título que ve Google tiene %d caracteres; corta a partir de %d." % (len(titulo_seo), lim.get("seo_title", 60)),
                        "directo": True})
        desc = a.get("seo_description") or a.get("subtitle") or a.get("summary") or ""
        if len(desc) > lim.get("seo_description", 155) or not desc:
            out.append({"pieza": a["id"], "tipo": "seo_description", "titulo": a.get("title"), "actual": desc,
                        "problema": "La descripción para buscadores tiene %d caracteres; Google enseña unos %d." % (len(desc), lim.get("seo_description", 155)),
                        "directo": True})
        if not a.get("relacionadas"):
            out.append({"pieza": a["id"], "tipo": "relacionadas", "titulo": a.get("title"), "actual": None,
                        "problema": "No enlaza a ninguna otra pieza de MOTICIAS: los buscadores y los asistentes la encuentran peor y el lector se va.",
                        "directo": True})
        for p in out:
            if p["pieza"] == a["id"] and "impacto" not in p:
                p["impacto"] = round(imp * PESOS[p["tipo"]] * frescura, 2)
                p["importancia"] = imp
    out.sort(key=lambda p: -p["impacto"])
    return out[:n]


def asesor_ultimo():
    fs = sorted(glob.glob(os.path.join(ROOT, "docs", "asesor", "20*.md")))
    if not fs:
        return None
    t = open(fs[-1], encoding="utf-8").read()
    return {"fichero": os.path.relpath(fs[-1], ROOT), "fecha": os.path.basename(fs[-1])[:10], "extracto": t[:1500]}


# ---------- relacionadas (enlaces internos, sin IA: por etiquetas comunes) ----------
def relacionadas(pid, arts=None, n=None):
    v = vertical()
    n = n or ((v.get("seo") or {}).get("limites") or {}).get("relacionadas", 3)
    arts = arts or articulos()
    a = arts.get(pid)
    if not a:
        return []
    def puntos(b):
        p = 3 * len(set(a.get("modos") or []) & set(b.get("modos") or []))
        p += 2 * len(set(a.get("temas") or []) & set(b.get("temas") or []))
        p += 2 * len(set(a.get("territorios") or []) & set(b.get("territorios") or []) - {"estado"})
        p += 1 if a.get("medio") and a.get("medio") == b.get("medio") else 0
        return p
    cands = [b for b in arts.values() if b["id"] != pid and b.get("status") == "publicado" and b.get("kind") != "opinion"]
    cands.sort(key=lambda b: (-puntos(b), -(b.get("importancia") or 3), str(b.get("date") or "")), reverse=False)
    return [{"id": b["id"], "titulo": b.get("title")} for b in cands if puntos(b) >= 3][:n]


# ---------- IA ----------
def _clave(cab=None):
    return os.environ.get("AI_GATEWAY_API_KEY") or (cab or {}).get("x-vercel-oidc-token") or os.environ.get("VERCEL_OIDC_TOKEN")


def ia(mensajes, modelo, clave, max_tokens=900, temperatura=0.3, timeout=90):
    """Una llamada a la pasarela de IA de Vercel (compatible con OpenAI). Devuelve (texto, json completo)."""
    cuerpo = {"model": modelo, "max_tokens": max_tokens, "temperature": temperatura, "messages": mensajes}
    req = urllib.request.Request("https://ai-gateway.vercel.sh/v1/chat/completions", method="POST", data=json.dumps(cuerpo).encode("utf-8"),
                                 headers={"Authorization": "Bearer " + clave, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.loads(r.read())
    return ((j.get("choices") or [{}])[0].get("message") or {}).get("content") or "", j


def proponer_ia(a, tipo, clave, modelo=None):
    """Propuesta de título o descripción para buscadores, sin cifras ni fechas que no estén en la pieza."""
    lim = ((vertical().get("seo") or {}).get("limites") or {})
    n = lim.get(tipo, 60 if tipo == "seo_title" else 155)
    que = "un título para buscadores" if tipo == "seo_title" else "una descripción para buscadores (meta description)"
    sistema = ("Eres editor SEO de MOTICIAS, medio profesional de transporte y movilidad en España. Escribes en español de España, claro y "
               "sin adjetivos vacíos. Regla absoluta: no añadas ninguna cifra, fecha, nombre ni hecho que no esté en el texto que te dan.")
    usuario = ("Escribe %s de como máximo %d caracteres para esta pieza. Pon delante lo que buscaría un profesional (organismo, modo, lugar, "
               "qué cambia). Sin comillas ni punto final en el título. Devuelve solo el texto.\n\nTitular: %s\nSubtítulo: %s\nResumen: %s") % (
        que, n, a.get("title"), a.get("subtitle") or "", a.get("summary") or "")
    texto, _ = ia([{"role": "system", "content": sistema}, {"role": "user", "content": usuario}], modelo or os.environ.get("MODELO_IA") or "anthropic/claude-opus-5.5", clave, 300)
    texto = " ".join(texto.strip().strip('"«»').split())
    if tipo == "seo_title":
        texto = texto.rstrip(".")
    if len(texto) > n:
        texto = texto[:n].rsplit(" ", 1)[0]
    # control: ninguna cifra que no esté en la pieza
    base = " ".join(str(a.get(k) or "") for k in ("title", "subtitle", "summary", "body_md"))
    nuevas = [x for x in re.findall(r"\d[\d.,]*", texto) if x not in base]
    if nuevas:
        raise ValueError("la propuesta traía cifras que no están en la pieza (%s): regénerala" % ", ".join(nuevas))
    return texto


# ---------- batería de asistentes ----------
URL_RE = re.compile(r"https?://[^\s)\]>\"']+")


def analizar(texto, citas=None):
    """{marca: {mencion, asociada}} y si cita moticias.com (en el texto o en las citas)."""
    v = vertical()
    t = plano(texto)
    out = {}
    for m in (v.get("seo") or {}).get("marcas") or []:
        pos = [x.start() for p in m["patrones"] for x in re.finditer(p, t)]
        asoc = any(abs(i - j) <= 250 for i in pos for a in m["asociaciones"] for j in [x.start() for x in re.finditer(re.escape(plano(a)), t)])
        out[m["id"]] = {"mencion": bool(pos), "asociada": bool(pos) and asoc}
    todas = list(citas or []) + URL_RE.findall(texto or "")
    cita = any("moticias.com" in str(c).lower() for c in todas)
    return out, cita, sorted(set(str(c) for c in todas))[:30]


def bateria(clave, ronda=None, modelos=None, preguntas=None, guardar=None):
    """Pregunta a cada asistente cada pregunta fija. `guardar(fila)` la guarda (en el gestor, en seo_llm). Devuelve resumen."""
    v = vertical()
    seo = v.get("seo") or {}
    ronda = ronda or datetime.date.today().isoformat()
    filas = []
    for m in modelos or seo.get("modelos") or []:
        for i, q in enumerate(preguntas or seo.get("preguntas") or [], 1):
            fila = {"ronda": ronda, "modelo": m["id"], "pregunta_n": i, "pregunta": q}
            try:
                texto, j = ia([{"role": "system", "content": "Responde en español de España, de forma concreta, citando las fuentes y webs que recomiendes."},
                               {"role": "user", "content": q}], m["id"], clave, 900, 0.2, 120)
                citas = j.get("citations") or [x.get("url") for x in (j.get("search_results") or []) if isinstance(x, dict)]
                marcas, cita, todas = analizar(texto, citas)
                fila.update(respuesta=texto[:4000], citas=todas, cita_moticias=cita, marcas=marcas)
            except (urllib.error.URLError, urllib.error.HTTPError, ValueError, KeyError, TimeoutError) as e:
                fila.update(error=str(e)[:300])
            filas.append(fila)
            if guardar:
                guardar(fila)
    return resumen(filas)


def resumen(filas):
    """Por modelo y por marca: cuántas respuestas citan moticias.com, nombran cada marca y la asocian con lo suyo."""
    por = {}
    for f in filas:
        x = por.setdefault(f["modelo"], {"preguntas": 0, "errores": 0, "cita_moticias": 0, "marcas": {}})
        x["preguntas"] += 1
        if f.get("error"):
            x["errores"] += 1
            continue
        x["cita_moticias"] += 1 if f.get("cita_moticias") else 0
        for k, m in (f.get("marcas") or {}).items():
            y = x["marcas"].setdefault(k, {"mencion": 0, "asociada": 0})
            y["mencion"] += 1 if m.get("mencion") else 0
            y["asociada"] += 1 if m.get("asociada") else 0
    return por


def main():
    a = sys.argv[1:] or ["-h"]
    if a[0] == "propuestas":
        print(json.dumps(propuestas(n=int(a[1]) if len(a) > 1 else 20), ensure_ascii=False, indent=1))
    elif a[0] == "relacionadas":
        print(json.dumps(relacionadas(a[1]), ensure_ascii=False, indent=1))
    elif a[0] == "analizar":
        print(json.dumps(analizar(" ".join(a[1:]))[:2], ensure_ascii=False))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
