"""MOTICIAS · Redacción desde el gestor: editar, retirar y «otro enfoque» con IA (decisión de Rainer, 9-11-2026).

«Entrar como editor jefe por defecto una vez acreditado y ver en cada noticia un icono discreto que me permita editar,
borrar o dar otro enfoque con la IA, que vería antes de volver a publicar. Imposible para quien no sea editor jefe.»

- Solo el superadministrador (permiso `redaccion`): lo comprueba api/gestor.py en el servidor.
- Editar cambia una lista cerrada de campos, añade `revised_at` y una línea en `revisiones`; si es una corrección de un
  dato, añade además la nota al final (`correcciones`), como manda la regla de siempre.
- «Borrar» es RETIRAR: la pieza deja de verse (borrador en Ghost, `status: retirada`) y se conserva entera; se puede
  restaurar. Nunca se borra una pieza.
- La IA propone y no publica: devuelve una versión con otro enfoque que el director ve a la vez que la original y
  publica o descarta. No puede añadir cifras ni fechas: lo que traiga y no esté en la pieza ni en sus fuentes se marca,
  y publicar con cifras nuevas exige que el director lo confirme expresamente.
"""
import datetime, json, os, re, urllib.error, urllib.request

CAMPOS = ("title", "subtitle", "kicker", "summary", "body_md", "key_fact", "actors", "relevance_for", "why", "next")
NOMBRES = {"title": "Titular", "subtitle": "Subtítulo", "kicker": "Antetítulo", "summary": "Respuesta directa (40–60 palabras)",
           "body_md": "Texto", "key_fact": "Dato clave", "actors": "Protagonistas", "relevance_for": "Para quién es relevante",
           "why": "Por qué es importante", "next": "Qué puede pasar ahora"}
LIMITES = {"title": 220, "subtitle": 400, "kicker": 120, "summary": 900, "body_md": 30000, "key_fact": 400, "actors": 1500,
           "relevance_for": 1500, "why": 2000, "next": 2000}

ENFOQUES = {
    "administraciones": "Reescribe con el enfoque de una administración (Estado, comunidad autónoma o ayuntamiento) que tiene que decidir: qué competencia toca, qué obligación o plazo nace, qué riesgo corre si no actúa.",
    "operadores": "Reescribe con el enfoque de un operador de transporte (autobús, ferrocarril, marítimo o aéreo): qué cambia en su cuenta de resultados, en sus contratos o en su operación, y qué tiene que hacer ahora.",
    "empresas": "Reescribe con el enfoque de una empresa o gran centro de trabajo (movilidad al trabajo, logística, viajes de empresa): qué le obliga o le conviene y en qué plazo.",
    "territorio": "Reescribe poniendo delante el territorio afectado: qué cambia en esa comunidad o ese municipio, para quién y desde cuándo.",
    "directo": "Reescribe más directo y claro: titular que diga el hecho y su consecuencia, frases más cortas, sin bajar de 1.000 palabras de texto ni perder ningún dato.",
    "titular": "Cambia solo el titular, el subtítulo y la respuesta directa para que digan mejor el hecho y por qué importa; deja lo demás igual.",
}

ESTILO = """Eres la redacción de MOTICIAS («con M de Movilidad»), medio profesional de transporte y movilidad en España para decisores.
Español de España. Rigor de Railway Gazette, Flightglobal y Tagesspiegel Background. Frases cortas; cifras con unidad y origen;
nombres y cargos exactos; vocabulario institucional exacto (obligación de servicio público, mapa concesional, canon, contrato-programa).
Sin adjetivos vacíos, sin preguntas retóricas, sin exclamaciones, sin emoticonos, sin fórmulas de relleno ni de inteligencia artificial.
Reglas que no se rompen: NO añadas ninguna cifra, fecha, cita, nombre ni hecho que no esté en la pieza o en la lista de fuentes que te doy;
puedes reordenar, cambiar el enfoque, el titular y la estructura, y quitar lo accesorio. Conserva todos los enlaces https:// del texto.
El texto (body_md) es Markdown: párrafos, `##` para secciones cortas, **negrita** en el sustantivo de arranque de los párrafos clave.
La «respuesta directa» (summary) abre la pieza: 40–60 palabras que contestan qué ha pasado y por qué importa.
Contesta SOLO con un objeto JSON con estas claves (todas, aunque alguna no cambie): title, subtitle, kicker, summary, body_md, key_fact,
actors, relevance_for, why, next, y además "nota": una o dos frases que expliquen qué has cambiado."""

_NUM = re.compile(r"\d+(?:[.,]\d+)*")


def ahora():
    return datetime.datetime.now().astimezone().isoformat(timespec="minutes")


def _norm(n):
    return n.replace(".", "").replace(",", ".").lstrip("0") or "0"


def cifras(texto):
    return {_norm(m.group(0)) for m in _NUM.finditer(texto or "")}


def corpus(a):
    """Todo lo que la pieza ya afirma: sus campos, cifras clave, cronología, fechas y títulos de las fuentes."""
    partes = [str(a.get(k) or "") for k in CAMPOS + ("date", "event_date", "published_at")]
    partes += [json.dumps(a.get(k) or [], ensure_ascii=False) for k in ("key_data", "timeline", "sources", "geo")]
    return "\n".join(partes)


def cifras_nuevas(original, propuesta):
    """Cifras (y fechas) de la propuesta que no están en la pieza original ni en sus fuentes."""
    base = cifras(corpus(original))
    nuevas = set()
    for k in CAMPOS:
        nuevas |= cifras(propuesta.get(k)) - base
    return sorted(nuevas, key=lambda x: (len(x), x))


def limpiar(cambios):
    out = {}
    for k in CAMPOS:
        if k in (cambios or {}) and isinstance(cambios[k], str):
            v = cambios[k].replace("\r\n", "\n").strip()
            out[k] = v[:LIMITES[k]]
    return out


def aplicar_edicion(a, cambios, quien, origen="manual", correccion=None):
    """Aplica los cambios a la pieza `a` (dict). Devuelve la lista de campos cambiados. No escribe en disco."""
    cambios = limpiar(cambios)
    cambiados = [k for k, v in cambios.items() if v != (a.get(k) or "")]
    if not cambiados and not correccion:
        return []
    if "title" in cambios and not cambios["title"]:
        raise ValueError("el titular no puede quedar vacío")
    if "body_md" in cambios and len(cambios["body_md"].split()) < 150:
        raise ValueError("el texto se queda en menos de 150 palabras: MOTICIAS no publica resúmenes")
    for k in cambiados:
        a[k] = cambios[k]
    t = ahora()
    a["revised_at"] = t
    a.setdefault("revisiones", []).append({"en": t, "por": quien, "campos": cambiados, "origen": origen})
    if correccion:
        a.setdefault("correcciones", []).append({"en": t[:10], "texto": str(correccion).strip()[:600]})
    return cambiados


def retirar(a, quien, motivo):
    if a.get("status") == "retirada":
        raise ValueError("la pieza ya está retirada")
    a["status_antes"] = a.get("status") or "publicado"
    a["status"] = "retirada"
    a.setdefault("revisiones", []).append({"en": ahora(), "por": quien, "accion": "retirar", "motivo": (motivo or "").strip()[:300]})


def restaurar(a, quien):
    if a.get("status") != "retirada":
        raise ValueError("la pieza no está retirada")
    a["status"] = a.pop("status_antes", None) or "publicado"
    a.setdefault("revisiones", []).append({"en": ahora(), "por": quien, "accion": "restaurar"})


# ---------- IA (Vercel AI Gateway) ----------
def _token(cabeceras):
    """Clave para el AI Gateway: AI_GATEWAY_API_KEY si existe; si no, el token OIDC que Vercel pasa a cada función."""
    return os.environ.get("AI_GATEWAY_API_KEY") or (cabeceras or {}).get("x-vercel-oidc-token") or os.environ.get("VERCEL_OIDC_TOKEN")


def _mensaje_usuario(a, enfoque, instruccion):
    fuentes = [{"medio": s.get("outlet"), "titulo": s.get("title"), "url": s.get("url"), "publicado": s.get("published")} for s in a.get("sources") or []]
    pieza = {k: a.get(k) or "" for k in CAMPOS}
    pedido = ENFOQUES.get(enfoque, "")
    if instruccion:
        pedido = (pedido + " " if pedido else "") + "Indicación del director: " + instruccion.strip()[:1500]
    return ("PEDIDO: %s\n\nPIEZA ACTUAL (JSON):\n%s\n\nCIFRAS CLAVE:\n%s\n\nCRONOLOGÍA:\n%s\n\nFUENTES:\n%s" % (
        pedido or "Dale otro enfoque más útil para decisores.", json.dumps(pieza, ensure_ascii=False, indent=1),
        json.dumps(a.get("key_data") or [], ensure_ascii=False), json.dumps(a.get("timeline") or [], ensure_ascii=False),
        json.dumps(fuentes, ensure_ascii=False)))


def _json_de(texto):
    texto = (texto or "").strip()
    if texto.startswith("```"):
        texto = texto.strip("`")
        texto = texto[texto.find("{"):]
    i, j = texto.find("{"), texto.rfind("}")
    if i < 0 or j < 0:
        raise ValueError("la IA no devolvió un JSON")
    return json.loads(texto[i:j + 1])


def otro_enfoque(a, enfoque, instruccion, cabeceras=None, modelo=None, tiempo=240):
    """Devuelve {"propuesta": {campos}, "nota": str, "cifras_nuevas": [...], "modelo": str}. No toca la pieza."""
    tok = _token(cabeceras)
    if not tok:
        raise RuntimeError("la IA del gestor no está activada (falta el acceso al AI Gateway de Vercel)")
    modelo = modelo or os.environ.get("MODELO_IA") or "anthropic/claude-opus-5.5"
    cuerpo = {"model": modelo, "max_tokens": 8000, "temperature": 0.4,
              "messages": [{"role": "system", "content": ESTILO}, {"role": "user", "content": _mensaje_usuario(a, enfoque, instruccion)}]}
    req = urllib.request.Request("https://ai-gateway.vercel.sh/v1/chat/completions", method="POST", data=json.dumps(cuerpo).encode("utf-8"),
                                 headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=tiempo) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            msg = (json.loads(e.read() or b"{}").get("error") or {}).get("message")
        except ValueError:
            msg = None
        raise RuntimeError("la IA respondió %s%s" % (e.code, (": " + msg[:200]) if msg else ""))
    except urllib.error.URLError as e:
        raise RuntimeError("la IA no contesta: %s" % e.reason)
    texto = ((d.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    p = _json_de(texto)
    prop = limpiar(p)
    for k in CAMPOS:  # lo que la IA no devuelve se queda como estaba
        prop.setdefault(k, a.get(k) or "")
    return {"propuesta": prop, "nota": str(p.get("nota") or "")[:600], "cifras_nuevas": cifras_nuevas(a, prop), "modelo": modelo}
