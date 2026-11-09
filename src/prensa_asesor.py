#!/usr/bin/env python3
"""MOTICIAS · Asesor de comunicación virtual y recomendador honesto de la sala de prensa (cambio sala-de-prensa-v1).
Solo biblioteca estándar. Lo usan la página app.moticias.com/prensa/ (api/prensa.py), /prensa-buzon y la difusión.

Qué hace:
  analizar()   puntúa una nota de 0 a 100 en cinco dimensiones (noticiabilidad 30, estructura 20, claridad y longitud
               20, tono 15, datos y verificabilidad 15), con cada aviso ligado a la frase concreta y su arreglo.
  recomendar() cruza el análisis con la audiencia REAL disponible (contactos que pasan los filtros y medios del
               catálogo) y dice qué plan conviene, cuál no y por qué. Puede decir «no pague».
  ia()         segunda pasada opcional con la API de Claude (ANTHROPIC_API_KEY): titulares y entradilla alternativos,
               versión recortada y preguntas de periodista. Nunca añade hechos: lo que falte va como [DATO].

Uso:
  python3 -I src/prensa_asesor.py nota.md [--organizacion "X"] [--objetivo noticia|lanzamiento|marca|venta] [--ia] [--privado <ruta>] [--json]
La nota en Markdown: «# Titular», «## Subtítulo» (opcional), cuerpo. También vale un JSON con titulo, subtitulo, cuerpo.
"""
import argparse, datetime, glob, json, os, re, sys, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from taxonomia import Taxonomia, plano  # noqa: E402

MESES = "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre"
RE_FECHA = re.compile(r"\b(\d{1,2} de (%s)( de \d{4})?|\d{1,2}/\d{1,2}/\d{2,4}|(lunes|martes|miércoles|jueves|viernes|sábado|domingo),? \d{1,2}|(%s) de \d{4}|\b20\d\d\b)" % (MESES, MESES), re.I)
RE_CIFRA = re.compile(r"\b\d[\d.,]*\s*(%|€|euros|millones|millón|mil|km|kilómetros|viajeros|pasajeros|usuarios|plazas|vehículos|autobuses|autocares|trenes|buques|vuelos|rutas|líneas|frecuencias|expediciones|empleos|puestos|trabajadores|toneladas|teu|años|meses|días|horas|minutos|municipios|paradas|estaciones|kwh|mwh|co2|unidades)\b", re.I)
RE_CITA = re.compile(r"[«\"“]([^«»\"“”]{25,400})[»\"”]")
RE_ATRIB = re.compile(r"\b(afirm|explic|señal|asegur|declar|destac|subray|indic|apunt|añad|sostien|sostuv|recuerd|record|valor|conclu)\w*\b|\b(según|ha dicho|dijo)\b", re.I)
RE_CARGO = re.compile(r"\b(director|directora|presidente|presidenta|consejero|consejera|ceo|gerente|alcalde|alcaldesa|concejal|concejala|ministro|ministra|secretario|secretaria|responsable|jefe|jefa|fundador|fundadora|socio|socia|delegado|delegada|portavoz)\b", re.I)
RE_EMAIL = re.compile(r"[^@\s<>()]+@[^@\s<>()]+\.[a-z]{2,}", re.I)
RE_TEL = re.compile(r"(\+34\s?)?[6789]\d{2}[\s.]?\d{2,3}[\s.]?\d{2,3}[\s.]?\d{0,3}")
RE_URL = re.compile(r"https?://[^\s)>\]]+")
INSTITUCION = ["ayuntamiento", "consejería", "consejeria", "ministerio", "gobierno", "junta de", "generalitat", "xunta", "diputación", "cabildo",
               "consorcio", "autoridad portuaria", "adif", "renfe", "aena", "comisión europea", "contrato", "adjudica", "adjudicación", "licitación",
               "concesión", "convenio", "boe", "real decreto", "ley ", "orden ministerial", "subvención", "ayuda", "pleno"]
IMPACTO = ["viajeros", "pasajeros", "usuarios", "vecinos", "ciudadanos", "trabajadores", "empleados", "clientes", "servicio", "línea", "linea",
           "frecuencia", "horario", "tarifa", "precio", "billete", "accesib", "emisiones", "sector", "operadores", "municipios", "comarca"]
NOVEDAD = ["pone en marcha", "lanza", "inaugura", "estrena", "presenta", "incorpora", "amplía", "amplia", "abre", "firma", "adjudica",
           "nombra", "nombramiento", "alcanza", "supera", "crea", "nuevo", "nueva", "nuevos", "nuevas", "primer", "primera"]
VENTA = ["descubre", "descubra", "contrata", "contrate", "solicita", "solicite", "ofrecemos", "ofrece a sus clientes", "descuento", "oferta",
         "prueba gratis", "demo", "pide", "llámanos", "llámenos", "visítanos", "no te pierdas", "no se pierda", "consulta nuestras", "precio especial"]
NOSOTROS = re.compile(r"\b(nosotros|nuestro|nuestra|nuestros|nuestras|somos|hemos|queremos|ofrecemos|apostamos)\b", re.I)


def cfg_vertical(vid="movilidad"):
    return json.load(open(os.path.join(ROOT, "verticals", vid + ".json"), encoding="utf-8"))


def palabras(s):
    return re.findall(r"[\wáéíóúüñÁÉÍÓÚÜÑ€%][\wáéíóúüñÁÉÍÓÚÜÑ€%.,'-]*", s or "")


def frases(s):
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ«\"“¿¡])", s or "") if f.strip()]


def leer_nota(ruta):
    raw = open(ruta, encoding="utf-8").read()
    if ruta.endswith(".json"):
        d = json.loads(raw)
        return {"titulo": d.get("titulo") or d.get("title", ""), "subtitulo": d.get("subtitulo") or d.get("subtitle", ""),
                "cuerpo": d.get("cuerpo") or d.get("body_md", ""), "organizacion": d.get("organizacion") or (d.get("org") or {}).get("nombre", "")}
    return partir_md(raw)


def partir_md(raw):
    titulo, sub, cuerpo = "", "", []
    for linea in raw.splitlines():
        if not titulo and linea.startswith("# "):
            titulo = linea[2:].strip()
        elif titulo and not sub and not cuerpo and linea.startswith("## "):
            sub = linea[3:].strip()
        else:
            cuerpo.append(linea)
    return {"titulo": titulo, "subtitulo": sub, "cuerpo": "\n".join(cuerpo).strip(), "organizacion": ""}


def parrafos(cuerpo):
    ps = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", cuerpo or "")]
    return [p for p in ps if p and not p.startswith("#")]


def contiene(texto, lista):
    t = " " + (texto or "").lower() + " "
    return [w for w in lista if re.search(r"(?<![\wáéíóúñ])" + re.escape(w.lower()) + r"(?![\wáéíóúñ])", t)]


def frase_con(texto, termino, maxlen=160):
    for f in frases(texto):
        if termino.lower() in f.lower():
            return f[:maxlen] + ("…" if len(f) > maxlen else "")
    return ""


def separar_cola(ps):
    """Separa del cuerpo el bloque «Sobre X» / «Acerca de» y el de contacto de prensa, que no cuentan como cuerpo."""
    cuerpo, sobre, contacto = [], [], []
    modo = "cuerpo"
    for p in ps:
        pl = plano(p[:40])
        if pl.startswith(("sobre ", "acerca de ")):
            modo = "sobre"
        elif pl.startswith(("contacto", "para mas informacion", "mas informacion", "gabinete de prensa", "prensa ")):
            modo = "contacto"
        (cuerpo if modo == "cuerpo" else sobre if modo == "sobre" else contacto).append(p)
    return cuerpo, sobre, contacto


def temas_recientes(dias=30):
    """Submodos con actividad en MOTICIAS los últimos días: una nota de un tema vivo tiene más opciones."""
    lim = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()
    cuenta = {}
    for p in glob.glob(os.path.join(ROOT, "data", "articles", "*.json")):
        try:
            a = json.load(open(p, encoding="utf-8"))
        except ValueError:
            continue
        if str(a.get("published_at", ""))[:10] >= lim and a.get("submodo"):
            cuenta[a["submodo"]] = cuenta.get(a["submodo"], 0) + 1
    return cuenta


def aviso(dim, gravedad, que, arreglo, frase=""):
    return {"dimension": dim, "gravedad": gravedad, "que": que, "arreglo": arreglo, "frase": frase}


def analizar(nota, vertical=None, tx=None, objetivo="noticia"):
    v = vertical or cfg_vertical()
    c = v["prensa"]["asesor"]
    tx = tx or Taxonomia(v["id"])
    tit, sub, org = (nota.get("titulo") or "").strip(), (nota.get("subtitulo") or "").strip(), (nota.get("organizacion") or "").strip()
    ps_all = parrafos(nota.get("cuerpo"))
    ps, sobre, contacto = separar_cola(ps_all)
    cuerpo = "\n\n".join(ps)
    todo = "\n".join([tit, sub, cuerpo])
    entr = ps[0] if ps else ""
    n_pal = len(palabras(cuerpo))
    avisos, pts = [], {}

    # ---- ejes
    pseudo = {"title": tit, "subtitle": sub, "summary": cuerpo[:2500], "tags": []}
    ejes = tx.clasificar(pseudo)

    # ---- noticiabilidad (30)
    cab = "\n".join([tit, sub] + ps[:2])
    señales = {}
    señales["hecho_fechado"] = bool(RE_FECHA.search(cab))
    cifras = RE_CIFRA.findall(todo)
    señales["cifra"] = bool(RE_CIFRA.search(cab)) or len(cifras) >= 2
    inst = contiene(todo, INSTITUCION)
    señales["institucional"] = bool(inst)
    imp = contiene(todo, IMPACTO)
    señales["impacto"] = len(imp) >= 2
    nov = contiene(cab, NOVEDAD)
    señales["novedad"] = bool(nov)
    recientes = temas_recientes()
    señales["tema_vivo"] = recientes.get(ejes["submodo"], 0) >= 2
    pesos_n = {"hecho_fechado": 5, "cifra": 6, "institucional": 6, "impacto": 5, "novedad": 4, "tema_vivo": 4}
    pts["noticiabilidad"] = sum(pesos_n[k] for k, ok in señales.items() if ok)
    if not señales["hecho_fechado"]:
        avisos.append(aviso("noticiabilidad", "alta", "No hay un hecho con fecha en el titular ni en la entradilla.",
                            "Diga qué ha pasado o pasará y cuándo («El 15 de diciembre empieza a funcionar…»). Sin fecha, un periodista no tiene noticia."))
    if not señales["cifra"]:
        avisos.append(aviso("noticiabilidad", "alta", "No hay una cifra que dé tamaño al hecho.",
                            "Añada el dato que lo mide: importe, viajeros, plazas, kilómetros, flota, empleo o ahorro. [DATO] si aún no lo tiene."))
    if not señales["impacto"]:
        avisos.append(aviso("noticiabilidad", "media", "No queda claro a quién afecta fuera de su organización.",
                            "Una frase con el efecto para usuarios, municipios u otras empresas del sector."))

    # ---- tipo: noticia, mixta o promoción
    humo = contiene(todo, c["palabras_humo"])
    venta = contiene(todo, VENTA)
    nos = NOSOTROS.findall(todo)
    densidad = (len(humo) * 2 + len(venta) * 2 + len(nos) + todo.count("!")) / max(n_pal, 1) * 100
    hecho = señales["hecho_fechado"] + señales["cifra"] + señales["institucional"]
    if hecho == 0 and (venta or densidad > 4):
        tipo = "promocion"
    elif densidad > 3 or (venta and hecho < 2):
        tipo = "mixta"
    else:
        tipo = "noticia"
    if objetivo == "venta":
        tipo = "promocion" if hecho < 2 else "mixta"

    # ---- estructura (20)
    e = 0
    if not tit:
        avisos.append(aviso("estructura", "alta", "Falta el titular.", "Escriba en la primera línea «# Titular»: quién hace qué, dónde, con la cifra."))
    else:
        L = len(tit)
        lo, hi = c["titular_ideal"]
        if L > c["titular_max"]:
            avisos.append(aviso("estructura", "media", "Titular de %d caracteres: se cortará en buscadores y correos." % L,
                                "Déjelo en %d–%d: sujeto, verbo en presente, objeto y cifra." % (lo, hi), tit))
            e += 2
        elif L < 35:
            avisos.append(aviso("estructura", "media", "Titular demasiado corto para decir qué pasa.", "Sujeto + verbo + qué + dónde.", tit))
            e += 3
        else:
            e += 5 if lo <= L <= hi else 4
        if tit.isupper() or tit.endswith("!") or tit.count(":") > 1:
            avisos.append(aviso("tono", "media", "Titular en mayúsculas, con exclamación o con varios dos puntos.", "Frase normal, informativa.", tit))
        if org and plano(org.split()[0]) not in plano(tit + " " + sub + " " + entr):
            avisos.append(aviso("estructura", "baja", "El nombre de la organización no aparece ni en el titular ni en la entradilla.",
                                "Nómbrela en la entradilla: un periodista tiene que saber de quién es la noticia en la primera línea."))
    e += 2 if sub else 0
    if not sub:
        avisos.append(aviso("estructura", "baja", "Sin subtítulo.", "Una línea con el segundo dato más importante (plazo, inversión, ámbito)."))
    w_entr = len(palabras(entr))
    ws = {"qué": bool(nov) or bool(re.search(r"\b(ha|han|va a|van a|será|serán|inicia|comienza|empieza|pone|lanza|firma)\b", entr, re.I)),
          "quién": bool(org and plano(org.split()[0]) in plano(entr)) or bool(re.search(r"\b[A-ZÁÉÍÓÚ][a-záéíóúñ]+ [A-ZÁÉÍÓÚ]", entr)),
          "dónde": bool(tx.territorios_en(entr)) or bool(re.search(r"\ben (el |la |los |las )?[A-ZÁÉÍÓÚ]", entr)),
          "cuándo": bool(RE_FECHA.search(entr))}
    faltan = [k for k, ok in ws.items() if not ok]
    if w_entr > c["entradilla_max_palabras"]:
        avisos.append(aviso("estructura", "media", "La entradilla tiene %d palabras." % w_entr,
                            "Respuesta directa en 40–60 palabras: qué, quién, dónde y cuándo. El resto, después.", entr[:160] + "…"))
    if faltan:
        avisos.append(aviso("estructura", "alta" if len(faltan) > 1 else "media", "La entradilla no responde: " + ", ".join(faltan) + ".",
                            "El primer párrafo es lo único que leerá la mayoría: tiene que contestar las cuatro preguntas.", entr[:160]))
    e += max(0, 6 - 2 * len(faltan) - (1 if w_entr > c["entradilla_max_palabras"] else 0))
    citas = RE_CITA.findall(cuerpo)
    atribuida = any(RE_ATRIB.search(p) and RE_CARGO.search(p) for p in ps if RE_CITA.search(p))
    if citas and atribuida:
        e += 3
    elif citas:
        e += 1
        avisos.append(aviso("estructura", "media", "Hay una cita, pero sin nombre y cargo de quien la dice.", "«…», ha explicado Nombre Apellido, cargo de la organización."))
    else:
        avisos.append(aviso("estructura", "baja", "No hay ninguna cita.", "Una declaración de un responsable con nombre y cargo, que aporte valoración, no repita el dato."))
    if citas:
        cl = max(citas, key=len)
        if contiene(cl, c["palabras_humo"]) or len(palabras(cl)) > 60:
            avisos.append(aviso("tono", "baja", "La cita suena a eslogan o es demasiado larga.", "Una cita corta, con una idea propia y verificable.", cl[:140]))
    e += 2 if sobre else 0
    if not sobre:
        avisos.append(aviso("estructura", "baja", "Falta el bloque «Sobre <organización>».", "Dos o tres líneas al final: qué es, desde cuándo, tamaño, web."))
    tiene_contacto = bool(contacto) or bool(RE_EMAIL.search("\n".join(ps_all[-3:])))
    e += 2 if tiene_contacto else 0
    if not tiene_contacto:
        avisos.append(aviso("estructura", "media", "Falta el contacto de prensa.", "Nombre, cargo, correo y teléfono de quien atiende a los periodistas."))
    pts["estructura"] = min(20, e)

    # ---- claridad y longitud (20)
    cl_pts = 0
    lo, hi = c["cuerpo_ideal_palabras"]
    if lo <= n_pal <= hi:
        cl_pts += 8
    elif n_pal < lo:
        cl_pts += 4
        avisos.append(aviso("claridad", "media", "Cuerpo de %d palabras: poco material para un periodista." % n_pal, "Añada contexto, datos y la cita hasta unas %d–%d palabras." % (lo, hi)))
    elif n_pal <= c["cuerpo_max_palabras"]:
        cl_pts += 5
        avisos.append(aviso("claridad", "baja", "Cuerpo de %d palabras: largo para una nota." % n_pal, "Recorte hasta %d: lo que no sea dato o cita, fuera." % hi))
    else:
        cl_pts += 2
        avisos.append(aviso("claridad", "alta", "Cuerpo de %d palabras: no se leerá." % n_pal, "Máximo %d. El detalle técnico, en un anexo enlazado." % hi))
    largos = [p for p in ps if len(palabras(p)) > c["parrafo_max_palabras"]]
    cl_pts += 4 if not largos else 2 if len(largos) == 1 else 0
    if largos:
        avisos.append(aviso("claridad", "media", "%d párrafo(s) de más de %d palabras." % (len(largos), c["parrafo_max_palabras"]), "Un párrafo, una idea; 3–4 frases.", largos[0][:140] + "…"))
    fs = frases(cuerpo)
    media = sum(len(palabras(f)) for f in fs) / max(len(fs), 1)
    cl_pts += 4 if media <= 25 else 2 if media <= 32 else 0
    if media > 25:
        largas = sorted(fs, key=lambda f: -len(palabras(f)))[0]
        avisos.append(aviso("claridad", "media", "Frases largas (media de %.0f palabras)." % media, "Corte en dos las de más de 30 palabras.", largas[:160] + "…"))
    angl = contiene(todo, c["anglicismos"])
    cl_pts += 4 if not angl else 2 if len(angl) <= 2 else 0
    if angl:
        avisos.append(aviso("claridad", "baja", "Anglicismos: " + ", ".join(sorted(set(angl))) + ".", "Use el término español (socio, partes interesadas, hoja de ruta, objetivo…).", frase_con(todo, angl[0])))
    pts["claridad"] = cl_pts

    # ---- tono (15)
    t = 15 - min(8, len(set(humo)) * 2) - min(4, int(densidad)) - (3 if venta else 0) - min(2, todo.count("!"))
    pts["tono"] = max(0, t)
    if humo:
        avisos.append(aviso("tono", "alta" if len(set(humo)) > 2 else "media", "Adjetivos de autobombo: " + ", ".join(sorted(set(humo))) + ".",
                            "Quítelos o cámbielos por el dato que los prueba. Un periodista los borra y desconfía del resto.", frase_con(todo, humo[0])))
    if venta:
        avisos.append(aviso("tono", "alta", "Lenguaje de venta: " + ", ".join(sorted(set(venta))) + ".",
                            "Una nota de prensa informa; no invita a comprar. Si el objetivo es vender, lo que conviene es contenido patrocinado.", frase_con(todo, venta[0])))
    if len(nos) >= 3:
        avisos.append(aviso("tono", "media", "Escrita en primera persona del plural (%d veces)." % len(nos), "Tercera persona: «La empresa…», «El consorcio…».", frase_con(todo, nos[0])))

    # ---- datos y verificabilidad (15)
    d = 0
    d += 5 if len(cifras) >= 3 else 3 if cifras else 0
    urls = RE_URL.findall(todo)
    d += 3 if urls else 0
    if not urls:
        avisos.append(aviso("datos", "baja", "Sin enlaces.", "Enlace a la fuente del dato (resolución, informe, web del servicio) y a imágenes descargables."))
    rel = contiene(todo, c["fechas_relativas"])
    d += 3 if not rel else 1
    if rel:
        avisos.append(aviso("datos", "media", "Fechas relativas: " + ", ".join(sorted(set(rel))) + ".",
                            "Ponga la fecha («el 15 de diciembre»): la nota se lee días después de enviarse.", frase_con(todo, rel[0])))
    sup = contiene(todo, c["superlativos_a_probar"])
    d += 4 if not sup else 2 if urls else 0
    if sup:
        avisos.append(aviso("datos", "alta" if not urls else "media", "Afirmaciones que hay que probar: " + ", ".join(sorted(set(sup))) + ".",
                            "Cite la fuente que lo demuestra o quítelas. MOTICIAS y cualquier medio serio lo comprobarán.", frase_con(todo, sup[0])))
    pts["datos"] = d

    total = sum(pts.values())
    if tipo == "promocion":
        total = min(total, 45)
    gr = {"alta": 0, "media": 1, "baja": 2}
    avisos.sort(key=lambda a: gr[a["gravedad"]])
    veredicto = ("Lista para difundir" if total >= 75 else "Difundible con arreglos" if total >= 60 else
                 "Publicable, pero no está para difusión" if total >= 40 and tipo != "promocion" else
                 "No es todavía una nota de prensa")
    return {"puntuacion": total, "dimensiones": pts, "maximos": {"noticiabilidad": 30, "estructura": 20, "claridad": 20, "tono": 15, "datos": 15},
            "veredicto": veredicto, "tipo": tipo, "avisos": avisos, "ejes": ejes, "señales": señales,
            "palabras": {"cuerpo": n_pal, "entradilla": w_entr, "titular_caracteres": len(tit)},
            "cifras_detectadas": sorted(set(m.group(0) for m in RE_CIFRA.finditer(todo)))[:12],
            "propuestas": propuestas(tit, sub, entr, org, ejes, tx, faltan)}


def propuestas(tit, sub, entr, org, ejes, tx, faltan):
    """Sin IA: fórmula y esqueleto con huecos; nunca hechos nuevos."""
    terr = ", ".join(tx.nombre_territorio(t) for t in ejes["territorios"] if t not in ("estado", "ue")) or "[DÓNDE]"
    primera = frases(entr)[0] if entr else ""
    titular = re.sub(r"\s+", " ", primera)[:85].rstrip(" ,;:") if 40 <= len(primera) <= 110 else ""
    return {"formula_titular": "[Quién] + [verbo en presente] + [qué] + [dónde] + [cifra]",
            "titular_desde_entradilla": titular,
            "esqueleto_entradilla": "%s %s [QUÉ: el hecho] en %s [CUÁNDO: fecha] [CIFRA: el dato que lo mide], lo que [A QUIÉN AFECTA]." % (org or "[QUIÉN]", "[verbo]", terr),
            "falta_en_entradilla": faltan}


# ---------- recomendador ----------
def recomendar(an, audiencia, medios_ejes, vertical=None, objetivo="noticia"):
    """audiencia: recuento de contactos.recuento() o None si no hay base disponible; medios_ejes: contactos.medios_para()."""
    v = vertical or cfg_vertical()
    planes = {p["id"]: p for p in v["prensa"]["planes"]}
    vis = {p["id"]: p for p in v["prensa"]["visibilidad"]}
    s, tipo = an["puntuacion"], an["tipo"]
    autonomico = all(t not in ("estado", "ue", "internacional") for t in an["ejes"]["territorios"]) and len(an["ejes"]["territorios"]) == 1
    n_dest = audiencia["individual"] if audiencia else None  # los que reciben la nota suelta; B2C va al resumen semanal
    n_medios = len([m for m in medios_ejes if m.get("tipo") != "canal-propio"])
    tx = Taxonomia(v["id"])
    sector = tx.submodos.get(an["ejes"]["submodo"], (None, {"nombre": an["ejes"]["submodo"]}))[1]["nombre"].lower()
    out = []

    def op(pid, recomendado, porque, nombre=None, precio=None):
        p = planes.get(pid) or vis.get(pid) or {}
        out.append({"id": pid, "nombre": nombre or p.get("nombre", pid), "precio_eur": precio if precio is not None else p.get("precio_eur", p.get("desde_eur")),
                    "desde": pid in vis, "recomendado": recomendado, "porque": porque})

    aud_txt = ("%d destinatario(s) profesional(es) que pasan los filtros para %s" % (n_dest, sector) if n_dest is not None
               else "audiencia por confirmar (la base de contactos se está construyendo)")
    if tipo == "promocion" or objetivo == "venta":
        op("patrocinado", True, "Su texto presenta un producto, no un hecho noticiable. Como nota de prensa no lo publicaría ningún medio; como contenido patrocinado señalizado, llega al lector adecuado sin engañarle.")
        op("publicacion", False, "Se puede publicar en la lista solo si añade un hecho con fecha y cifra; ahora no lo hay.")
        op("difusion", False, "No le recomendamos pagar difusión: enviar publicidad a periodistas le cierra puertas para la próxima nota.")
        if objetivo in ("marca", "venta"):
            op("publicidad", False, "Si busca presencia sostenida ante un segmento durante semanas, la publicidad en secciones complementa al patrocinado.")
        return out
    op("publicacion", s < 60 or n_dest is None or n_dest < planes["difusion"]["requiere"]["destinatarios_min"],
       "Gratis. Queda en la lista de notas de prensa de %s, en el buscador y con enlace permanente." % sector)
    if n_dest is None:
        op("difusion", False, "Antes de cobrarle nada le confirmaremos cuántos periodistas y profesionales de su sector la recibirían. Publique gratis y le escribimos con la cifra.")
    elif s < 60:
        op("difusion", False, "Todavía no: con %d/100 la nota no pasa nuestro filtro de valor (60). Arregle primero los avisos de prioridad alta; el asesor le dirá cuándo está lista." % s)
    elif n_dest is not None and n_dest < planes["difusion"]["requiere"]["destinatarios_min"]:
        op("difusion", False, "Hoy solo hay %s: por debajo de %d no le cobramos una difusión que no rendiría. Publique gratis y se lo diremos cuando la audiencia crezca." % (aud_txt, planes["difusion"]["requiere"]["destinatarios_min"]))
    elif autonomico and n_medios < 2:
        op("difusion", False, "Su noticia es de una sola comunidad y solo tenemos %d medio(s) que la cubran: la publicación gratuita basta." % n_medios)
    else:
        op("difusion", True, "La nota está en %d/100 y hay %s y %d medios del catálogo que cubren %s." % (s, aud_txt, n_medios, sector))
    req = planes["difusion-plus"]["requiere"]
    plus_ok = s >= req["puntuacion_min"] and n_dest is not None and n_dest >= req["destinatarios_min"]
    op("difusion-plus", plus_ok,
       ("Nota sólida (%d/100) y audiencia suficiente: la revisión de un editor y el envío a medios generalistas y regionales de %s suman." % (s, ", ".join(an["ejes"]["territorios"]))) if plus_ok
       else "No compensa ahora: %s." % ("la nota necesita %d/100" % req["puntuacion_min"] if s < req["puntuacion_min"] else
                                         "audiencia por confirmar" if n_dest is None else "hacen falta %d destinatarios y hay %d" % (req["destinatarios_min"], n_dest)))
    if objetivo == "marca":
        op("publicidad", True, "Para presencia sostenida de marca ante %s durante semanas: es complemento de la nota, no sustituto." % sector)
    else:
        op("patrocinado", False, "Solo si además quiere explicar a fondo un producto o servicio; para anunciar un hecho, la nota rinde más y cuesta menos.")
    return out


# ---------- segunda pasada con Claude (opcional) ----------
PROMPT = """Eres el asesor de comunicación de la sala de prensa de MOTICIAS, medio profesional del transporte en España.
Revisa la nota de prensa de abajo. REGLAS ESTRICTAS: no añadas ningún hecho, cifra, fecha, nombre ni cita que no esté en la nota;
si algo falta, escribe [DATO: qué falta]. Español de España, tercera persona, sin adjetivos de autobombo.
Devuelve SOLO un JSON con estas claves:
"titulares": 3 titulares de 55 a 80 caracteres (sujeto + verbo en presente + qué + dónde + cifra si existe),
"entradilla": una entradilla de 40 a 60 palabras que responda qué, quién, dónde y cuándo,
"recortada": la nota completa reescrita en 300 a 500 palabras, con los mismos hechos,
"preguntas_periodista": las 3 preguntas que haría un periodista del sector y la nota no responde,
"riesgos": frases que un periodista consideraría no probadas o promocionales (cítalas literalmente).
Avisos del análisis automático: %s

NOTA:
%s"""


def ia(nota, an, modelo=None):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return {"error": "sin ANTHROPIC_API_KEY: solo análisis automático"}
    base = (os.environ.get("ANTHROPIC_API_URL") or "https://api.anthropic.com").rstrip("/")
    texto = "# %s\n## %s\n\n%s" % (nota.get("titulo", ""), nota.get("subtitulo", ""), (nota.get("cuerpo") or "")[:12000])
    av = "; ".join(a["que"] for a in an["avisos"][:10])
    body = {"model": modelo or os.environ.get("PRENSA_MODELO") or "claude-sonnet-5-5", "max_tokens": 2500,
            "messages": [{"role": "user", "content": PROMPT % (av, texto)}]}
    req = urllib.request.Request(base + "/v1/messages", data=json.dumps(body).encode(), method="POST", headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            res = json.loads(r.read())
        txt = "".join(b.get("text", "") for b in res.get("content", []))
        m = re.search(r"\{.*\}", txt, re.S)
        return json.loads(m.group(0)) if m else {"error": "respuesta sin JSON"}
    except (urllib.error.URLError, ValueError) as e:
        return {"error": "IA no disponible: %s" % e}


def texto_humano(an, recs):
    o = ["Puntuación: %d/100 · %s · tipo: %s" % (an["puntuacion"], an["veredicto"], an["tipo"]),
         "  " + " · ".join("%s %d/%d" % (k, v, an["maximos"][k]) for k, v in an["dimensiones"].items()),
         "  ejes: %s / %s / %s" % (an["ejes"]["submodo"], ",".join(an["ejes"]["temas"]), ",".join(an["ejes"]["territorios"])), "", "Avisos:"]
    for a in an["avisos"]:
        o.append("  [%s] %s → %s%s" % (a["gravedad"], a["que"], a["arreglo"], ("\n         «%s»" % a["frase"]) if a["frase"] else ""))
    o += ["", "Recomendación:"]
    for r in recs:
        o.append("  %s %s (%s €%s): %s" % ("✔" if r["recomendado"] else "·", r["nombre"], r["precio_eur"], " desde" if r["desde"] else "", r["porque"]))
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nota")
    ap.add_argument("--organizacion", default="")
    ap.add_argument("--objetivo", default="noticia", choices=["noticia", "lanzamiento", "marca", "venta"])
    ap.add_argument("--ia", action="store_true")
    ap.add_argument("--privado")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    import contactos as C
    v = cfg_vertical()
    tx = Taxonomia()
    nota = leer_nota(a.nota)
    nota["organizacion"] = a.organizacion or nota.get("organizacion", "")
    an = analizar(nota, v, tx, a.objetivo)
    ejes = {"submodo": an["ejes"]["submodo"], "modo": an["ejes"]["modo"], "territorios": an["ejes"]["territorios"], "temas": an["ejes"]["temas"]}
    try:
        aud = C.recuento(C.cargar(C.ruta_privada(a.privado)), ejes, v["prensa"]["filtro_valor"], tx)
    except SystemExit:
        aud = None
    recs = recomendar(an, aud, C.medios_para(ejes, tx), v, a.objetivo)
    out = {"analisis": an, "audiencia": aud, "recomendacion": recs}
    if a.ia:
        out["ia"] = ia(nota, an)
    print(json.dumps(out, ensure_ascii=False, indent=1) if a.json else texto_humano(an, recs) + (("\n\nIA:\n" + json.dumps(out["ia"], ensure_ascii=False, indent=1)) if a.ia else ""))


if __name__ == "__main__":
    main()
