#!/usr/bin/env python3
"""MOTICIAS · Repercusión de una nota de prensa: detección con evidencia, alcance con fuente e informe al cliente
(cambio sala-de-prensa-v1; método en docs/prensa/metodo-repercusion.md). Solo biblioteca estándar.

Compromiso: CERO falsos positivos. Un impacto solo entra en el informe si está probado (reproducción o adaptación del
texto con el nombre del emisor y fecha válida) o si una persona lo ha revisado (menciones). La exhaustividad no se
promete: el informe dice «detectado por estos métodos». Sin valor publicitario equivalente (AVE).

El agente (/prensa-impacto) busca y lee; este script decide y cuenta:
  python3 -I src/prensa_impacto.py pendientes                      # notas que tocan hoy según el calendario (días 1,2,3,5,7,10,14,21,30)
  python3 -I src/prensa_impacto.py consultas <id>                  # búsquedas exactas que debe lanzar el agente
  python3 -I src/prensa_impacto.py añadir <id> cand1.json [...] --metodo websearch|rss|alerta|manual
        (cada candidato: {"url","titulo","fecha","texto"}; texto = el cuerpo leído de la página)
  python3 -I src/prensa_impacto.py revisar <id> <impacto> --aceptar|--rechazar [--tono positivo|neutro|negativo] --por "Rainer"
  python3 -I src/prensa_impacto.py metrica <id> --nombre "Impresiones LinkedIn (perfil del director)" --valor 1234 --fuente "LinkedIn, 12-11-2026"
  python3 -I src/prensa_impacto.py informe <id> [--publico]         # HTML en <privado>/informes/; --publico: enlace firmado
Carpeta privada: --privado (como en src/contactos.py).
"""
import argparse, datetime, glob, hashlib, html, json, os, re, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from taxonomia import plano  # noqa: E402

V = json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))
CFG = V["prensa"]["impacto"]
RE_CITA = re.compile(r"[«\"“]([^«»\"“”]{25,400})[»\"”]")
RE_CIFRA = re.compile(r"\b\d[\d.,]*\s*(%|€|euros|millones|millón|mil|km|viajeros|pasajeros|usuarios|plazas|vehículos|autobuses|trenes|buques|vuelos|líneas|expediciones|empleos|trabajadores|toneladas|años|meses)\b", re.I)
TIPO_MEDIO = {"medio-digital": "web", "revista": "web", "newsletter": "newsletter", "asociacion": "newsletter", "agencia": "agencia",
              "red-social": "red-social", "canal-propio": "propio"}
ORDEN = {"reproduccion": 0, "adaptacion": 1, "mencion": 2}


def ahora():
    return datetime.datetime.now().astimezone().isoformat(timespec="minutes")


def tokens(s):
    return plano(s).split()


def tejas(s, k=None):
    k = k or CFG["tamano_huella"]
    t = tokens(s)
    return {" ".join(t[i:i + k]) for i in range(max(0, len(t) - k + 1))}


def alias_org(nota):
    n = nota["organizacion"]["nombre"]
    al = {plano(n)}
    sin_forma = re.sub(r"\b(s\.?l\.?u?|s\.?a\.?u?|s\.?coop\.?|slp)\b\.?", "", n, flags=re.I).strip(" ,.")
    al.add(plano(sin_forma))
    dom = urllib.parse.urlparse(nota["organizacion"].get("web") or "").netloc.replace("www.", "")
    if dom:
        al.add(plano(dom.split(".")[0]))
    al |= {plano(a) for a in nota.get("organizacion", {}).get("alias", [])}
    return sorted(a for a in al if len(a) >= 4)


def original(texto, teja):
    """La teja (en plano) devuelta con las palabras originales de la nota, para enseñarla al cliente con sus tildes."""
    pal = re.findall(r"\S+", texto)
    planas = [plano(w) for w in pal]
    obj = teja.split()
    k = len(obj)
    for i in range(len(pal)):
        seq, j = [], i
        while j < len(pal) and len(seq) < k:
            seq += planas[j].split()
            j += 1
        if seq[:k] == obj:
            return " ".join(pal[i:j]).strip(",.;:«»\"“”")
    return teja


def huellas(nota):
    texto = "%s\n%s\n%s" % (nota["titulo"], nota.get("subtitulo", ""), nota["cuerpo_md"])
    citas = [c.strip() for c in RE_CITA.findall(nota["cuerpo_md"])]
    # Frases distintivas para buscar: de cada párrafo, la secuencia de 8 palabras con más palabras largas (nombres, cifras).
    distintivas = []
    for p in [p for p in nota["cuerpo_md"].split("\n\n") if len(p.split()) >= 12][:5]:
        w = p.split()
        mejor = max(range(len(w) - 7), key=lambda i: sum(len(x) > 6 or any(ch.isdigit() for ch in x) for x in w[i:i + 8]))
        distintivas.append(" ".join(w[mejor:mejor + 8]).strip(",.;:«»\"“”"))
    return {"organizacion": alias_org(nota), "citas": citas, "cifras": sorted(set(m.group(0) for m in RE_CIFRA.finditer(texto))),
            "distintivas": distintivas, "tejas": len(tejas(nota["cuerpo_md"]))}


def consultas(nota):
    h = nota.get("huellas") or huellas(nota)
    org = nota["organizacion"]["nombre"]
    q = ['"%s"' % nota["titulo"]]
    q += ['"%s"' % d for d in h["distintivas"][:3]]
    for c in h["citas"][:1]:
        q.append('"%s"' % " ".join(c.split()[:9]))
    q += ['"%s" %s' % (org, c) for c in h["cifras"][:2]]
    q.append('"%s" %s' % (org, nota.get("submodo", "").replace("-", " ")))
    return q


# ---------- medios ----------
def medios():
    return {json.load(open(p, encoding="utf-8"))["id"]: json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(ROOT, "data", "medios", "*.json"))}


def dominio(url):
    return urllib.parse.urlparse(url).netloc.lower().replace("www.", "")


def medio_de(url, cat):
    d = dominio(url)
    for m in cat.values():
        md = dominio(m.get("url", ""))
        if md and (d == md or d.endswith("." + md)):
            return m
    return None


def canonica(url):
    u = urllib.parse.urlparse(url)
    q = [(k, v) for k, v in urllib.parse.parse_qsl(u.query) if not k.startswith(("utm_", "fbclid", "gclid", "mc_"))]
    return urllib.parse.urlunparse((u.scheme or "https", u.netloc.lower().replace("www.", ""), u.path.rstrip("/"), "", urllib.parse.urlencode(q), ""))


# ---------- clasificación ----------
def clasificar(nota, cand, cat):
    """Devuelve el impacto con tipo y estado. Reglas en docs/prensa/metodo-repercusion.md § 2."""
    url, texto = cand.get("url", ""), cand.get("texto", "") or ""
    imp = {"id": "i-" + hashlib.sha256(canonica(url).encode()).hexdigest()[:10], "url": url, "canonica": canonica(url), "dominio": dominio(url),
           "titulo": (cand.get("titulo") or "")[:200], "fecha": (cand.get("fecha") or "")[:10] or None, "detectado_en": ahora(),
           "metodo": cand.get("metodo", "websearch")}
    m = medio_de(url, cat)
    imp["medio_id"], imp["medio"] = (m["id"], m["nombre"]) if m else (None, imp["dominio"])
    pt = " " + plano(imp["titulo"] + " " + texto) + " "
    org_ok = any(" " + a + " " in pt for a in alias_org(nota))
    S = tejas(nota["titulo"] + " " + nota["cuerpo_md"])
    C = tejas(imp["titulo"] + " " + texto)
    comunes = S & C
    cont = len(comunes) / max(len(S), 1)
    h = nota.get("huellas") or huellas(nota)
    cita = any(" ".join(tokens(c)[:8]) in pt for c in h["citas"] if len(tokens(c)) >= 8)
    cifras = [c for c in h["cifras"] if plano(c) in pt]
    imp.update({"contencion": round(cont, 3), "organizacion_nombrada": org_ok, "cita_literal": cita, "cifras_coinciden": cifras[:6]})
    ev = sorted(comunes, key=lambda s: -len(s))[:2]
    imp["evidencia"] = ["«…%s…»" % original(nota["titulo"] + " " + nota["cuerpo_md"], e) for e in ev] + (["cita literal del portavoz"] if cita else []) + \
        (["cifra: " + ", ".join(cifras[:3])] if cifras else [])
    ref = (nota.get("embargo_hasta") or nota.get("publicada_en") or nota.get("recibida_en") or "")[:10]
    propios = {dominio(V["ghost"]["url"]), dominio(nota["organizacion"].get("web") or "") or "—"}
    if imp["dominio"] in propios or any(imp["dominio"].endswith("." + p) for p in propios if p != "—"):
        imp["tipo"], imp["estado"], imp["motivo"] = "descartado", "descartado", "web de MOTICIAS o del propio emisor"
    elif not org_ok:
        imp["tipo"], imp["estado"], imp["motivo"] = "descartado", "descartado", "no nombra a la organización"
    elif imp["fecha"] and ref and imp["fecha"] < ref:
        imp["tipo"], imp["estado"], imp["motivo"] = "descartado", "descartado", "publicado antes que la nota (%s < %s)" % (imp["fecha"], ref)
    elif cont >= CFG["umbral_reproduccion"]:
        imp["tipo"] = "reproduccion"
    elif cont >= CFG["umbral_adaptacion"] or cita:
        imp["tipo"] = "adaptacion"
    elif cifras or cont > 0.03:
        imp["tipo"] = "mencion"
    else:
        imp["tipo"], imp["estado"], imp["motivo"] = "descartado", "descartado", "nombra a la organización pero no a esta nota"
    if "estado" not in imp:
        if imp["tipo"] in ("reproduccion", "adaptacion") and imp["fecha"]:
            imp["estado"], imp["motivo"] = "verificado", "texto de la nota presente (%d %%) con nombre y fecha válida" % round(cont * 100)
        else:
            imp["estado"], imp["motivo"] = "revisar", "mención sin texto de la nota" if imp["tipo"] == "mencion" else "sin fecha de publicación legible"
    return imp


# ---------- registro privado ----------
def ruta(privado, nid):
    return os.path.join(privado, "impacto", nid + ".json")


def registro(privado, nid):
    p = ruta(privado, nid)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"nota_id": nid, "impactos": [], "metricas": [], "consultas": []}


def guardar(privado, reg):
    import prensa_comun as P
    reg["actualizado"] = ahora()
    P.guardar_json(ruta(privado, reg["nota_id"]), reg)


def añadir(reg, imps):
    """Fusiona por URL canónica; y por medio + título (la misma pieza con dos URL). Nunca baja un estado revisado."""
    vistos = {i["canonica"]: i for i in reg["impactos"]}
    claves = {(i.get("medio_id") or i["dominio"], plano(i["titulo"])[:60]): i for i in reg["impactos"] if i.get("titulo")}
    nuevos = 0
    for i in imps:
        k2 = (i.get("medio_id") or i["dominio"], plano(i["titulo"])[:60])
        prev = vistos.get(i["canonica"]) or (claves.get(k2) if i.get("titulo") else None)
        if prev:
            if prev.get("revisado_por"):
                continue
            if ORDEN.get(i["tipo"], 9) < ORDEN.get(prev["tipo"], 9) or (prev["estado"] == "revisar" and i["estado"] == "verificado"):
                prev.update({k: v for k, v in i.items() if k != "id"})
            continue
        reg["impactos"].append(i)
        vistos[i["canonica"]] = i
        nuevos += 1
    # sindicación: el mismo texto en varios medios (contención alta en más de uno)
    rep = [i for i in reg["impactos"] if i["tipo"] == "reproduccion"]
    for i in rep:
        i["sindicado"] = len({x.get("medio_id") or x["dominio"] for x in rep}) > 1
    return nuevos


# ---------- alcance ----------
def alcance(reg, cat):
    """Alcance potencial (suma de audiencias declaradas, un medio una vez) e impactos estimados (horquilla)."""
    ver = [i for i in reg["impactos"] if i["estado"] == "verificado"]
    por_medio, sin_aud, lo, hi = {}, set(), 0.0, 0.0
    for i in ver:
        m = cat.get(i.get("medio_id")) if i.get("medio_id") else None
        au = (m or {}).get("audiencia") or {}
        if not m or not au.get("valor") or au.get("tipo") not in ("declarada", "medida"):
            sin_aud.add(i.get("medio") or i["dominio"])
            continue
        tipo = TIPO_MEDIO.get(m.get("tipo"), "web")
        if tipo == "propio":
            continue  # lo propio va en métricas medidas
        if m["id"] not in por_medio:
            por_medio[m["id"]] = {"medio": m["nombre"], "audiencia": au["valor"], "unidad": au.get("unidad"), "fuente": au.get("fuente"), "fecha": au.get("fecha")}
        co = CFG["coeficientes"][tipo]
        k = co.get("lectura_pieza") or co.get("apertura")
        lo += au["valor"] * k[0]
        hi += au["valor"] * k[1]
    return {"potencial": sum(d["audiencia"] for d in por_medio.values()), "medios_con_audiencia": por_medio,
            "medios_sin_audiencia": sorted(sin_aud), "impactos_estimados": [int(round(lo, -1)), int(round(hi, -1))]}


# ---------- informe ----------
def fnum(n):
    return "{:,}".format(int(n)).replace(",", ".")


def fecha_es(d):
    try:
        return datetime.date.fromisoformat(d[:10]).strftime("%d-%m-%Y")
    except (TypeError, ValueError):
        return "sin fecha"


def informe_html(nota, reg, pedido, cat, hasta=None):
    e = html.escape
    hasta = hasta or datetime.date.today().isoformat()
    ver = sorted([i for i in reg["impactos"] if i["estado"] == "verificado"], key=lambda i: (i.get("fecha") or "", ORDEN.get(i["tipo"], 9)))
    rev = [i for i in reg["impactos"] if i["estado"] == "revisar"]
    desc = [i for i in reg["impactos"] if i["estado"] in ("descartado", "rechazado")]
    al = alcance(reg, cat)
    medios_n = len({i.get("medio_id") or i["dominio"] for i in ver})
    por_tipo = {t: sum(1 for i in ver if i["tipo"] == t) for t in ("reproduccion", "adaptacion", "mencion")}
    met = (pedido or {}).get("metricas") or {}
    env = len((pedido or {}).get("envios") or [])
    pub = nota.get("publicada_en") or nota.get("recibida_en")
    dias = (datetime.date.fromisoformat(hasta) - datetime.date.fromisoformat(pub[:10])).days if pub else 0
    lo, hi = al["impactos_estimados"]
    resumen = ("La nota «%s» de %s, publicada el %s, acumula %d impacto%s verificado%s en %d medio%s en %d días: %d reproducción%s, %d adaptación%s y %d mención%s revisada%s. %s"
               % (nota["titulo"], nota["organizacion"]["nombre"], fecha_es(pub), len(ver), "" if len(ver) == 1 else "s", "" if len(ver) == 1 else "s",
                  medios_n, "" if medios_n == 1 else "s", dias, por_tipo["reproduccion"], "" if por_tipo["reproduccion"] == 1 else "es",
                  por_tipo["adaptacion"], "" if por_tipo["adaptacion"] == 1 else "es", por_tipo["mencion"], "" if por_tipo["mencion"] == 1 else "es",
                  "" if por_tipo["mencion"] == 1 else "s",
                  ("Alcance potencial declarado: %s; impactos estimados entre %s y %s." % (fnum(al["potencial"]), fnum(lo), fnum(hi))) if al["potencial"]
                  else "Ninguno de los medios ha declarado su audiencia: no estimamos impactos sin ese dato."))
    filas = "".join(
        "<tr><td>%s</td><td><a href=\"%s\">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td class=n>%s</td></tr>"
        % (fecha_es(i.get("fecha")), e(i["url"]), e(i.get("medio") or i["dominio"]), e(i.get("titulo") or "—"),
           {"reproduccion": "Reproducción", "adaptacion": "Adaptación", "mencion": "Mención"}[i["tipo"]] + (" · sindicada" if i.get("sindicado") else ""),
           e(" · ".join(i.get("evidencia") or [])[:160]) + (" · revisada por %s" % e(i["revisado_por"]) if i.get("revisado_por") else ""),
           "%d %%" % round(i.get("contencion", 0) * 100)) for i in ver) or "<tr><td colspan=7>Todavía no hay impactos verificados.</td></tr>"
    # evolución diaria
    cuenta = {}
    for i in ver:
        if i.get("fecha"):
            cuenta[i["fecha"]] = cuenta.get(i["fecha"], 0) + 1
    mx = max(cuenta.values() or [1])
    barras = "".join('<div class=bar><span>%s</span><i style="width:%d%%"></i><b>%d</b></div>' % (fecha_es(d), 100 * n / mx, n) for d, n in sorted(cuenta.items()))
    aud = "".join("<tr><td>%s</td><td class=n>%s %s</td><td>%s · %s</td></tr>" % (e(d["medio"]), fnum(d["audiencia"]), e(d.get("unidad") or ""), e(d.get("fuente") or ""), e(d.get("fecha") or ""))
                  for d in al["medios_con_audiencia"].values()) or "<tr><td colspan=3>Ningún medio con audiencia declarada entre los impactos.</td></tr>"
    metr = []
    if env:
        metr.append(("Envíos a profesionales", fnum(env), "Registro de envíos de MOTICIAS"))
    for k, nom in (("entregados", "Entregados"), ("aperturas_unicas", "Aperturas únicas"), ("clics_unicos", "Clics únicos"), ("bajas", "Bajas")):
        if met.get(k) is not None:
            metr.append((nom, fnum(met[k]), "Brevo, etiqueta np-%s" % nota["id"]))
    for m in reg.get("metricas", []):
        metr.append((m["nombre"], fnum(m["valor"]), m["fuente"]))
    metr_html = "".join("<tr><td>%s</td><td class=n>%s</td><td>%s</td></tr>" % (e(a), b, e(c)) for a, b, c in metr) or "<tr><td colspan=3>Sin métricas propias todavía.</td></tr>"
    co = CFG["coeficientes"]
    return """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Informe de repercusión · %(tit)s</title>
<style>
body{font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;color:#111827;max-width:960px;margin:0 auto;padding:24px}
h1{font-size:24px;line-height:1.25;margin:.2em 0}h2{font-size:17px;margin:2em 0 .6em;border-bottom:1px solid #e5e7eb;padding-bottom:.3em}
.k{color:#6b7280;font-size:12px;letter-spacing:.05em;text-transform:uppercase}.res{font-size:16px;background:#f9fafb;border-left:3px solid #0f766e;padding:12px 16px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}.card{border:1px solid #e5e7eb;border-radius:8px;padding:12px}
.card b{display:block;font-size:24px}.card span{font-size:12px;color:#6b7280}table{width:100%%;border-collapse:collapse;font-size:13px}
td,th{border-bottom:1px solid #f0f0f0;padding:6px 8px;text-align:left;vertical-align:top}th{color:#6b7280;font-weight:600}.n{text-align:right;white-space:nowrap}
.bar{display:grid;grid-template-columns:90px 1fr 30px;align-items:center;gap:8px;font-size:12px}.bar i{display:block;height:10px;background:#0f766e;border-radius:3px}
.met{font-size:13px;color:#374151}.met li{margin:.3em 0}footer{margin-top:3em;font-size:12px;color:#6b7280}
@media print{body{padding:0}a{color:inherit}}
</style></head><body>
<div class=k>MOTICIAS · Sala de prensa · Informe de repercusión · hasta el %(hasta)s</div>
<h1>%(tit)s</h1><div class=k>%(org)s · publicada el %(pub)s%(plan)s</div>
<p class=res>%(resumen)s</p>
<div class=cards>
<div class=card><b>%(nver)d</b><span>impactos verificados</span></div>
<div class=card><b>%(nmed)d</b><span>medios distintos</span></div>
<div class=card><b>%(pot)s</b><span>alcance potencial declarado</span></div>
<div class=card><b>%(est)s</b><span>impactos estimados (horquilla)</span></div>
<div class=card><b>%(nrev)d</b><span>menciones pendientes de revisión (no cuentan)</span></div>
</div>
<h2>Impactos verificados</h2>
<table><tr><th>Fecha</th><th>Medio</th><th>Titular</th><th>Tipo</th><th>Evidencia</th><th class=n>Texto de la nota</th></tr>%(filas)s</table>
<h2>Evolución</h2>%(barras)s
<h2>Alcance: medios con audiencia declarada</h2>
<table><tr><th>Medio</th><th class=n>Audiencia</th><th>Fuente y fecha</th></tr>%(aud)s</table>
<p class=met>Sin audiencia declarada (cuentan como impacto, no suman alcance): %(sin)s.</p>
<h2>Métricas medidas de MOTICIAS</h2>
<table><tr><th>Métrica</th><th class=n>Valor</th><th>Fuente</th></tr>%(metr)s</table>
<h2>Método y límites</h2>
<ul class=met>
<li><b>Detección.</b> Búsquedas exactas del titular, frases distintivas, la cita y el nombre con cada cifra; RSS de los medios del catálogo de MOTICIAS; alertas. Lo que no se ha podido leer (muros de pago, papel, radio, televisión, redes cerradas) no está: el informe recoge lo <i>detectado</i>, no todo lo publicado.</li>
<li><b>Verificación.</b> Reproducción: al menos el %(urep)d %% de las frases de seis palabras de la nota aparecen en la pieza. Adaptación: entre el %(uad)d %% y el %(urep)d %%, o la cita literal. En ambos casos con el nombre de la organización y fecha igual o posterior a la publicación. Las menciones solo cuentan si una persona las ha revisado. Descartadas: %(ndesc)d candidatas.</li>
<li><b>Alcance potencial.</b> Suma de la audiencia que cada medio declara (con su fuente y fecha), un medio una vez. No sumamos audiencias que no estén declaradas.</li>
<li><b>Impactos estimados.</b> Horquilla, no medición: web, %(cweb)s; boletines, %(cnl)s; redes, impresiones reales de la plataforma. Son hipótesis de método declaradas, revisables con datos.</li>
<li><b>Sin valor publicitario equivalente (AVE).</b> Los Principios de Barcelona 3.0 de AMEC lo descartan como medida del valor de la comunicación.</li>
</ul>
<footer>Generado el %(gen)s por la sala de prensa de MOTICIAS (Avionline S.L.). Documento para %(org)s; no se publica. Método completo: moticias.com/como-trabajamos/</footer>
</body></html>""" % {
        "tit": e(nota["titulo"]), "org": e(nota["organizacion"]["nombre"]), "pub": fecha_es(pub), "hasta": fecha_es(hasta),
        "plan": (" · plan %s" % e(pedido["plan"])) if pedido and pedido.get("plan") else "", "resumen": e(resumen), "nver": len(ver), "nmed": medios_n,
        "pot": fnum(al["potencial"]) if al["potencial"] else "no declarado", "est": ("%s–%s" % (fnum(lo), fnum(hi))) if al["potencial"] else "—",
        "nrev": len(rev), "filas": filas, "barras": barras or "<p class=met>Sin fechas todavía.</p>", "aud": aud,
        "sin": e(", ".join(al["medios_sin_audiencia"]) or "ninguno"), "metr": metr_html, "ndesc": len(desc),
        "urep": round(CFG["umbral_reproduccion"] * 100), "uad": round(CFG["umbral_adaptacion"] * 100),
        "cweb": e(co["web"]["explicacion"]), "cnl": e(co["newsletter"]["explicacion"]), "gen": ahora()}


def pendientes(notas, hoy=None):
    hoy = hoy or datetime.date.today()
    out = []
    for n in notas:
        if n.get("status") != "publicada" or not n.get("publicada_en"):
            continue
        d = (hoy - datetime.date.fromisoformat(n["publicada_en"][:10])).days
        if d in CFG["calendario_dias"]:
            out.append({"id": n["id"], "dia": d, "titulo": n["titulo"]})
    return out


def main():
    import contactos as C
    import prensa_comun as P
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["pendientes", "consultas", "añadir", "anadir", "revisar", "metrica", "informe"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--privado"); ap.add_argument("--metodo", default="websearch")
    ap.add_argument("--aceptar", action="store_true"); ap.add_argument("--rechazar", action="store_true")
    ap.add_argument("--tono", choices=["positivo", "neutro", "negativo"]); ap.add_argument("--por")
    ap.add_argument("--nombre"); ap.add_argument("--valor", type=float); ap.add_argument("--fuente")
    ap.add_argument("--hasta"); ap.add_argument("--publico", action="store_true")
    a = ap.parse_args()
    priv = C.ruta_privada(a.privado)
    if a.accion == "pendientes":
        print(json.dumps(pendientes(P.todas_las_notas()), ensure_ascii=False, indent=1))
        return
    nid = a.args[0]
    nota = P.leer_nota(nid)
    cat = medios()
    if a.accion == "consultas":
        print("\n".join(consultas(nota)))
        return
    reg = registro(priv, nid)
    if a.accion in ("añadir", "anadir"):
        imps = []
        for f in a.args[1:]:
            c = json.load(open(f, encoding="utf-8"))
            for x in (c if isinstance(c, list) else [c]):
                x.setdefault("metodo", a.metodo)
                imps.append(clasificar(nota, x, cat))
        n = añadir(reg, imps)
        reg["consultas"].append({"fecha": ahora(), "candidatos": len(imps), "nuevos": n})
        guardar(priv, reg)
        for i in imps:
            print("%-11s %-12s %-28s %3d%%  %s" % (i["estado"], i["tipo"], (i.get("medio") or "")[:28], round(i["contencion"] * 100), i.get("motivo", "")))
    elif a.accion == "revisar":
        if not a.por or not (a.aceptar or a.rechazar):
            sys.exit("Indica --aceptar o --rechazar y --por <quién>.")
        for i in reg["impactos"]:
            if i["id"] == a.args[1]:
                i["estado"] = "verificado" if a.aceptar else "rechazado"
                i["revisado_por"], i["revisado_en"] = a.por, ahora()
                if a.tono:
                    i["tono"] = a.tono
                guardar(priv, reg)
                print(i["estado"], i["url"])
                return
        sys.exit("No existe el impacto " + a.args[1])
    elif a.accion == "metrica":
        if not (a.nombre and a.valor is not None and a.fuente):
            sys.exit("Hacen falta --nombre, --valor y --fuente (de dónde sale el dato y de qué fecha).")
        reg["metricas"].append({"nombre": a.nombre, "valor": a.valor, "fuente": a.fuente, "anotada": ahora()})
        guardar(priv, reg)
    elif a.accion == "informe":
        pedido = P.leer_pedido(priv, nid)
        h = informe_html(nota, reg, pedido, cat, a.hasta)
        hoy = (a.hasta or datetime.date.today().isoformat())
        dest = os.path.join(priv, "informes", "%s-%s.html" % (nid, hoy))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "w", encoding="utf-8").write(h)
        print("Informe:", dest)
        if a.publico:
            print("Enlace para el cliente:", "%s/api/prensa?a=informe&t=%s" % (P.base_app(), P.firmar("informe", "%s|%s" % (nid, hoy))))


if __name__ == "__main__":
    main()
