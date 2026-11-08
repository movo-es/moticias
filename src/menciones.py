#!/usr/bin/env python3
"""MOTICIAS · Menciones del grupo (cajas «Contenido patrocinado» en el texto), solo biblioteca estándar.

  python3 -I src/menciones.py proponer --fecha AAAA-MM-DD [--ids ID ...] [--aplicar] [--estado publicada|propuesta]
      Puntúa los productos de data/productos/ contra las piezas del día y propone como mucho una mención por pieza.
      Sin --aplicar solo imprime; con --aplicar escribe `menciones` en data/articles/<id>.json.
  python3 -I src/menciones.py informe --fecha AAAA-MM-DD [--out work/menciones]
      Escribe work/menciones/<fecha>.md y .html con cada mención publicada y sus enlaces de edición.
  python3 -I src/menciones.py enviar --fecha AAAA-MM-DD [--dry-run]
      Envía el informe por correo (Brevo, BREVO_API_KEY en el entorno) SOLO si hubo menciones ese día.

Reglas (CLAUDE.md y openspec/changes/patrocinios-en-linea/, decisión de Rainer del 8-11-2026 por la noche): la mención
va en una caja «Contenido patrocinado» en medio del texto de la pieza, separada de los párrafos y con su etiqueta; cada
producto decide en el gestor si entra solo (`modo: automatico`, con su `umbral`), si espera aprobación (`revision`) o si
solo se pone a mano (`manual`), y si es `exclusiva` (ninguna otra caja en esa pieza) o `compartida` (hasta
`max_por_pieza` cajas); los análisis del director y las piezas que ya tratan del grupo no llevan ninguna; el director
recibe el resumen con un enlace al gestor de patrocinios (app.moticias.com/gestor/) para publicar, editar o retirar
cada mención; retirar = `estado: retirada` (nunca se borra).
"""
import argparse, datetime, glob, html, json, os, re, sys, unicodedata, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_EDIT = "https://github.com/movo-es/moticias/edit/main/data/articles/%s.json"
REPO_VIEW = "https://github.com/movo-es/moticias/blob/main/data/articles/%s.json"


# ---------- utilidades ----------
def plano(s):
    """Minúsculas, sin acentos, espacios normalizados."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.lower())


def cargar_vertical(vid):
    return json.load(open(os.path.join(ROOT, "verticals", vid + ".json"), encoding="utf-8"))


def cargar_productos(data_dir):
    out = []
    for p in sorted(glob.glob(os.path.join(data_dir, "productos", "*.json"))):
        try:
            out.append(json.load(open(p, encoding="utf-8")))
        except json.JSONDecodeError as e:
            print("producto ilegible:", p, e, file=sys.stderr)
    return out


def cargar_piezas(data_dir, fecha=None, ids=None):
    arts = []
    for p in sorted(glob.glob(os.path.join(data_dir, "articles", "*.json"))):
        a = json.load(open(p, encoding="utf-8"))
        if ids and a.get("id") not in ids:
            continue
        if fecha and not ids and a.get("date") != fecha:
            continue
        a["_path"] = p
        arts.append(a)
    return arts


def guardar_pieza(a):
    p = a.pop("_path")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(a, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    a["_path"] = p


def url_pieza(a, base_url):
    g = a.get("ghost") or {}
    return g.get("url") or "%s/%s/" % (base_url.rstrip("/"), a["id"])


def url_edicion_ghost(a, base_url):
    g = a.get("ghost") or {}
    if g.get("post_id"):
        return "%s/ghost/#/editor/post/%s" % (base_url.rstrip("/"), g["post_id"])
    return "%s/ghost/#/posts?type=published&search=%s" % (base_url.rstrip("/"), urllib.parse.quote(a.get("title", "")[:60]))


def con_utm(url, producto, pieza_id):
    if not url:
        return url
    sep = "&" if "?" in url else "?"
    q = urllib.parse.urlencode({"utm_source": "moticias", "utm_medium": "contenido-patrocinado",
                                "utm_campaign": producto.get("utm_campaign") or "moticias-nota-de-la-casa", "utm_content": pieza_id})
    return url + sep + q


# ---------- puntuación ----------
def texto_cabecera(a):
    return plano(" ".join(str(a.get(k) or "") for k in ("title", "subtitle", "summary", "kicker")))


def texto_completo(a):
    campos = ("title", "subtitle", "summary", "kicker", "actors", "relevance_for", "why", "next", "body_md", "key_fact")
    t = " ".join(str(a.get(k) or "") for k in campos)
    t += " " + " ".join(a.get("tags") or [])
    return plano(t)


MODOS = ("automatico", "revision", "manual", "apagado")


def modo(prod):
    """automatico | revision | manual | apagado. Sin campo: activo → automatico; otro status → apagado."""
    m = prod.get("modo")
    if m in MODOS:
        return m if prod.get("status") == "activo" else "apagado"
    return "automatico" if prod.get("status") == "activo" else "apagado"


POSICIONES = ("premium", "estandar", "referencia")


def posicion(x):
    """premium (tras el primer párrafo) · estandar (entre el tercio y la mitad del texto) · referencia (al final del texto)."""
    return x.get("posicion") if x.get("posicion") in POSICIONES else "estandar"


def exclusividad(prod):
    return "exclusiva" if prod.get("exclusividad") == "exclusiva" else "compartida"


def puntuar(a, prod):
    """Devuelve (puntuación, motivos) o (None, motivo de exclusión).

    La pieza tiene que TRATAR del problema, no solo rozarlo: cuenta el doble lo que aparece en la cabecera (título,
    subtítulo, resumen, antetítulo) y hace falta, en la cabecera, al menos una frase disparadora o dos palabras clave."""
    if prod.get("status") != "activo" or not prod.get("url"):
        return None, "producto no activo o sin url"
    if a.get("kind") == "analisis":
        return None, "análisis del director: sin menciones"
    cab = texto_cabecera(a)
    for ex in prod.get("excluir") or []:
        if plano(ex) in cab:
            return None, "excluido por «%s»" % ex
    todo = texto_completo(a)
    d = prod.get("disparadores") or {}
    pts, motivos, cab_frases, cab_claves = 0, [], 0, 0
    if plano(a.get("subsector") or "") in [plano(s) for s in d.get("subsectores") or []]:
        pts += 2; motivos.append("subsector " + (a.get("subsector") or ""))
    if plano(a.get("section") or "") in [plano(s) for s in d.get("secciones") or []]:
        pts += 1; motivos.append("sección " + (a.get("section") or ""))
    for f in d.get("frases") or []:
        pf = plano(f)
        if pf in cab:
            pts += 5; cab_frases += 1; motivos.append("«%s» (cabecera)" % f)
        elif pf in todo:
            pts += 3; motivos.append("«%s»" % f)
    frases_ok = [plano(f) for f in d.get("frases") or [] if plano(f) in todo]
    for k in d.get("palabras_clave") or []:
        if any(plano(k) in f for f in frases_ok):
            continue  # ya contada dentro de una frase
        pk = r"\b%s\b" % re.escape(plano(k))
        if re.search(pk, cab):
            pts += 2; cab_claves += 1; motivos.append(k + " (cabecera)")
        elif re.search(pk, todo):
            pts += 1; motivos.append(k)
    if cab_frases == 0 and cab_claves < 2:
        return None, "la cabecera no trata del tema (sin frase disparadora ni dos palabras clave)"
    return pts, motivos


def publicadas_ultimos_dias(data_dir, producto_id, hasta, dias=7):
    n = 0
    lim = (datetime.date.fromisoformat(hasta) - datetime.timedelta(days=dias)).isoformat()
    for p in glob.glob(os.path.join(data_dir, "articles", "*.json")):
        a = json.load(open(p, encoding="utf-8"))
        if not (lim <= (a.get("date") or "") <= hasta):
            continue
        for m in a.get("menciones") or []:
            if m.get("producto") == producto_id and m.get("estado") == "publicada":
                n += 1
    return n


def nueva_mencion(a, prod, pts, motivos, est, origen="automatica"):
    return {"producto": prod["id"], "nombre": prod.get("name"), "texto": (prod.get("textos") or {}).get("corto", ""),
            "cta": (prod.get("textos") or {}).get("cta", ""), "url": con_utm(prod["url"], prod, a["id"]),
            "exclusividad": exclusividad(prod), "posicion": posicion(prod), "estado": est, "motivo": "; ".join(motivos), "puntuacion": pts, "origen": origen,
            "propuesta_en": datetime.datetime.now().astimezone().isoformat(timespec="minutes")}


def candidatos(a, productos):
    """Todos los productos puntuados contra la pieza (también los que no llegan al umbral), de mayor a menor."""
    out = []
    for prod in productos:
        pts, motivos = puntuar(a, prod)
        out.append({"producto": prod.get("id"), "nombre": prod.get("name"), "modo": modo(prod), "exclusividad": exclusividad(prod),
                    "umbral": int(prod.get("umbral") or 10), "puntuacion": pts, "motivo": motivos if pts is None else "; ".join(motivos),
                    "supera": pts is not None and pts >= int(prod.get("umbral") or 10)})
    out.sort(key=lambda c: -(c["puntuacion"] or -1))
    return out


def proponer(a, productos, data_dir, fecha, estado="publicada", max_por_pieza=2):
    """Devuelve la lista de menciones nuevas para la pieza (vacía si ninguna). Respeta modo, umbral, exclusividad y tope semanal."""
    puntuados = []
    for prod in productos:
        if modo(prod) not in ("automatico", "revision"):
            continue
        pts, motivos = puntuar(a, prod)
        if pts is None or pts < int(prod.get("umbral") or 10):
            continue
        puntuados.append((pts, prod, motivos))
    puntuados.sort(key=lambda t: -t[0])
    elegidos = []
    for pts, prod, motivos in puntuados:
        if elegidos and (exclusividad(prod) == "exclusiva" or exclusividad(elegidos[0][1]) == "exclusiva"):
            continue
        if len(elegidos) >= max_por_pieza:
            break
        elegidos.append((pts, prod, motivos))
    out = []
    for pts, prod, motivos in elegidos:
        est = estado if modo(prod) == "automatico" else "propuesta"
        if modo(prod) == "revision":
            motivos = motivos + ["modo revisión: espera aprobación en el gestor"]
        tope = int(prod.get("max_por_semana") or 0)
        if est == "publicada" and tope and publicadas_ultimos_dias(data_dir, prod["id"], fecha) >= tope:
            est = "propuesta"
            motivos = motivos + ["tope semanal alcanzado: queda como propuesta"]
        out.append(nueva_mencion(a, prod, pts, motivos, est))
    return out


# ---------- cajas HTML (las usa ghost_publish) ----------
def cajas_html(a, vertical, inline=html.escape):
    """Lista de (posicion, html): una caja por mención publicada (como mucho max_por_pieza; si la primera es exclusiva,
    solo esa). Siempre lleva enlace (si falta el texto del enlace, se usa el nombre del producto)."""
    cfg = vertical.get("productos") or {}
    pub = [m for m in a.get("menciones") or [] if m.get("estado") == "publicada"]
    if not pub:
        return []
    if pub[0].get("exclusividad") == "exclusiva":
        pub = pub[:1]
    pub = pub[: int(cfg.get("max_por_pieza") or 2)]
    etiqueta = cfg.get("label", "Contenido patrocinado")
    decl = cfg.get("declaracion", "")
    out = []
    for m in pub:
        # Tarjeta HTML de Ghost (los comentarios kg-card la conservan intacta al convertir a Lexical) con estilos en línea,
        # para que la caja se vea igual con cualquier tema: separada del texto, fondo suave, etiqueta pequeña y gris.
        out.append((posicion(m), '<!--kg-card-begin: html--><aside class="contenido-patrocinado" data-producto="%s" '
                   'style="margin:2em 0;padding:1em 1.2em;background:#f4f6f5;border-left:3px solid #c9d2cd;border-radius:4px;font-size:.95em">'
                   '<p class="contenido-patrocinado-etiqueta" style="margin:0 0 .5em;font-size:.72em;letter-spacing:.06em;text-transform:uppercase;color:#7a837e">%s</p>'
                   '<p style="margin:0">%s <a href="%s" rel="sponsored noopener" style="color:inherit;font-weight:600;text-decoration:underline;text-underline-offset:2px">%s</a></p>%s</aside><!--kg-card-end: html-->'
                   % (html.escape(m.get("producto") or "", quote=True), inline(etiqueta), inline(m.get("texto", "")),
                      html.escape(m.get("url", ""), quote=True), inline(m.get("cta") or m.get("nombre") or ""),
                      ('<p class="contenido-patrocinado-declaracion" style="margin:.6em 0 0;font-size:.75em;color:#7a837e">%s</p>'
                       % inline(decl % {"nombre": m.get("nombre") or ""})) if decl else "")))
    return out


def insertar_en_medio(cuerpo_html, cajas):
    """Coloca las cajas en el cuerpo según su posición:
    - premium: tras el primer párrafo del cuerpo (decisión de Rainer, 8-11-2026: no pegada a la entradilla);
    - estandar: entre el tercio y la mitad del texto (una: hacia el 40 %; dos: al tercio y a la mitad), siempre después
      de un párrafo, una lista o una cita;
    - referencia: al final del texto, antes de las cifras clave.
    Acepta también cajas sin posición (texto suelto): cuentan como estándar."""
    cajas = [c if isinstance(c, tuple) else ("estandar", c) for c in cajas or []]
    if not cajas:
        return cuerpo_html
    bloques = [b for b in cuerpo_html.split("\n") if b.strip()]
    premium = [h for p, h in cajas if p == "premium"]
    final = [h for p, h in cajas if p == "referencia"]
    medio = [h for p, h in cajas if p not in ("premium", "referencia")]
    n = len(bloques)
    colocadas = {}
    if medio and n >= 2:
        huecos = [i for i in range(1, n) if bloques[i - 1].startswith(("<p>", "</ul>", "<blockquote"))] or list(range(1, n))
        objetivos = [0.4] if len(medio) == 1 else [1 / 3, 0.5]
        usados = []
        for caja, f in zip(medio, objetivos):
            obj = max(1, round(n * f))
            h = min((h for h in huecos if h not in usados), key=lambda h: abs(h - obj), default=None)
            if h is None:
                final.insert(0, caja)
                continue
            usados.append(h)
            colocadas.setdefault(h, []).append(caja)
    elif medio:
        final = medio + final
    if premium:  # tras el primer párrafo (o la primera lista o cita) del cuerpo
        i1 = next((i + 1 for i, b in enumerate(bloques) if b.startswith(("<p>", "</ul>", "<blockquote"))), min(1, n))
        colocadas[i1] = premium + colocadas.get(i1, [])
    out = []
    for i, b in enumerate(bloques):
        out += colocadas.get(i, [])
        out.append(b)
    out += colocadas.get(n, [])
    out += final
    return "\n".join(out)


def bloque_html(a, vertical, inline=html.escape):
    """Compatibilidad: todas las cajas juntas (sin posición)."""
    return "\n".join(h for _, h in cajas_html(a, vertical, inline))


def url_gestor(vertical, pieza_id=None):
    cfg = vertical.get("productos") or {}
    base = (os.environ.get("GESTOR_URL") or cfg.get("gestor_url") or "https://app.moticias.com/gestor/").rstrip("/") + "/"
    return base + ("?pieza=" + urllib.parse.quote(pieza_id) if pieza_id else "")


# ---------- informe y correo ----------
def informe(piezas, vertical, base_url, fecha):
    gestor = url_gestor(vertical)
    filas = []
    for a in piezas:
        for m in a.get("menciones") or []:
            if m.get("estado") not in ("publicada", "propuesta"):
                continue
            filas.append((a, m))
    if not filas:
        return None, None
    md = ["# Menciones del grupo · %s" % fecha, "",
          "%d mención(es) en la edición. «Gestionar» abre el gestor de patrocinios en el móvil: publicar, retirar o cambiar el texto, y la pieza se republica sola. Gestor: %s" % (len(filas), gestor), ""]
    h = ["<h2>Menciones del grupo · %s</h2><p>%d mención(es). <b>Gestionar</b> abre el gestor de patrocinios: publicar, retirar o cambiar el texto; la pieza se republica sola.</p>"
         '<p><a href="%s" style="display:inline-block;padding:10px 14px;background:#111;color:#fff;text-decoration:none;border-radius:6px">Abrir el gestor de patrocinios</a></p>' % (html.escape(fecha), len(filas), html.escape(gestor, quote=True))]
    for a, m in filas:
        u = url_pieza(a, base_url)
        ge, re_, gp = url_edicion_ghost(a, base_url), REPO_EDIT % a["id"], url_gestor(vertical, a["id"])
        md += ["## %s" % a.get("title", a["id"]), "- Pieza: %s" % u, "- Producto: **%s** · estado: %s · puntuación %s" % (m.get("nombre"), m.get("estado"), m.get("puntuacion")),
               "- Texto: %s — [%s](%s)" % (m.get("texto"), m.get("cta"), m.get("url")), "- Motivo: %s" % m.get("motivo"),
               "- Gestionar: %s · respaldo: [GitHub](%s) · [Ghost](%s)" % (gp, re_, ge), ""]
        h.append('<div style="border:1px solid #ddd;padding:12px;margin:10px 0"><p><b><a href="%s">%s</a></b></p>'
                 '<p>Producto: <b>%s</b> · estado: %s · puntuación %s</p><p style="background:#f6f6f6;padding:8px">%s <a href="%s">%s</a></p>'
                 '<p><small>Motivo: %s</small></p><p><a href="%s" style="display:inline-block;padding:10px 14px;background:#111;color:#fff;text-decoration:none;border-radius:6px">Gestionar</a></p>'
                 '<p><small>Respaldo: <a href="%s">GitHub</a> · <a href="%s">Ghost</a></small></p></div>'
                 % (html.escape(u, quote=True), html.escape(a.get("title", a["id"])), html.escape(m.get("nombre") or ""), html.escape(m.get("estado") or ""), m.get("puntuacion"),
                    html.escape(m.get("texto") or ""), html.escape(m.get("url") or "", quote=True), html.escape(m.get("cta") or ""),
                    html.escape(m.get("motivo") or ""), html.escape(gp, quote=True), html.escape(re_, quote=True), html.escape(ge, quote=True)))
    h.append("<p><small>Generado por src/menciones.py · %s</small></p>" % html.escape(vertical.get("name", "")))
    return "\n".join(md), "\n".join(h)


def enviar_correo(asunto, cuerpo_html, para, de, dry_run=False):
    """Brevo transaccional (api.brevo.com/v3/smtp/email). Devuelve (ok, detalle)."""
    key = os.environ.get("BREVO_API_KEY")
    body = {"sender": {"email": de[0], "name": de[1]}, "to": [{"email": p} for p in para], "subject": asunto, "htmlContent": cuerpo_html}
    if dry_run or not key:
        return False, "sin envío (%s)" % ("dry-run" if dry_run else "falta BREVO_API_KEY en el entorno")
    req = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"api-key": key, "Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Moticias/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, r.read().decode("utf-8", "replace")[:300]
    except urllib.error.HTTPError as e:
        return False, "HTTP %s %s" % (e.code, e.read().decode("utf-8", "replace")[:300])
    except urllib.error.URLError as e:
        return False, "red: %s" % e


# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["proponer", "informe", "enviar"])
    ap.add_argument("--fecha", help="AAAA-MM-DD (por defecto hoy)")
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--estado", default="publicada", choices=["publicada", "propuesta"])
    ap.add_argument("--vertical", default="movilidad")
    ap.add_argument("--data", default=os.path.join(ROOT, "data"))
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "menciones"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    fecha = args.fecha or datetime.date.today().isoformat()
    vertical = cargar_vertical(args.vertical)
    cfg = vertical.get("productos") or {}
    base_url = os.environ.get("GHOST_URL", "https://%s" % vertical.get("domain", "")).rstrip("/")
    piezas = cargar_piezas(args.data, fecha, args.ids)

    if args.accion == "proponer":
        productos = cargar_productos(args.data)
        res = []
        for a in piezas:
            if any(m.get("estado") in ("publicada", "propuesta", "retirada") for m in a.get("menciones") or []):
                res.append({"id": a["id"], "mencion": None, "nota": "ya tenía mención (no se repite)"})
                continue
            ms = proponer(a, productos, args.data, fecha, args.estado, int(cfg.get("max_por_pieza") or 2))
            if ms and args.aplicar:
                a.setdefault("menciones", []).extend(ms)
                guardar_pieza(a)
            res.append({"id": a["id"], "mencion": ms or None})
        con = [r for r in res if r["mencion"]]
        print(json.dumps({"fecha": fecha, "piezas": len(piezas), "con_mencion": len(con), "aplicado": args.aplicar, "detalle": res}, ensure_ascii=False, indent=1))
        return

    md, h = informe(piezas, vertical, base_url, fecha)
    if not md:
        print(json.dumps({"fecha": fecha, "menciones": 0, "enviado": False, "nota": "sin menciones: no se escribe informe ni se envía nada"}, ensure_ascii=False))
        return
    os.makedirs(args.out, exist_ok=True)
    pmd, ph = os.path.join(args.out, fecha + ".md"), os.path.join(args.out, fecha + ".html")
    open(pmd, "w", encoding="utf-8").write(md + "\n")
    open(ph, "w", encoding="utf-8").write(h + "\n")
    if args.accion == "informe":
        print(json.dumps({"fecha": fecha, "menciones": md.count("\n## "), "informe": [pmd, ph]}, ensure_ascii=False))
        return
    para = cfg.get("email") or ["ruphoff@avionline.es"]
    if isinstance(para, str):
        para = [para]
    de = (cfg.get("remitente") or os.environ.get("MENCIONES_FROM") or "redaccion@moticias.com", vertical.get("name", "MOTICIAS"))
    asunto = "%s · menciones del grupo %s (%d)" % (vertical.get("name", "MOTICIAS"), fecha, md.count("\n## "))
    ok, det = enviar_correo(asunto, h, para, de, args.dry_run)
    reg = {"fecha": fecha, "menciones": md.count("\n## "), "para": para, "enviado": ok, "detalle": det, "en": datetime.datetime.now().astimezone().isoformat(timespec="minutes")}
    open(os.path.join(args.out, fecha + ".envio.json"), "w", encoding="utf-8").write(json.dumps(reg, ensure_ascii=False, indent=1))
    print(json.dumps(reg, ensure_ascii=False))


if __name__ == "__main__":
    main()
