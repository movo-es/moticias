#!/usr/bin/env python3
"""MOTICIAS · Menciones del grupo («Nota de la casa»), solo biblioteca estándar.

  python3 -I src/menciones.py proponer --fecha AAAA-MM-DD [--ids ID ...] [--aplicar] [--estado publicada|propuesta]
      Puntúa los productos de data/productos/ contra las piezas del día y propone como mucho una mención por pieza.
      Sin --aplicar solo imprime; con --aplicar escribe `menciones` en data/articles/<id>.json.
  python3 -I src/menciones.py informe --fecha AAAA-MM-DD [--out work/menciones]
      Escribe work/menciones/<fecha>.md y .html con cada mención publicada y sus enlaces de edición.
  python3 -I src/menciones.py enviar --fecha AAAA-MM-DD [--dry-run]
      Envía el informe por correo (Brevo, BREVO_API_KEY en el entorno) SOLO si hubo menciones ese día.

Reglas (CLAUDE.md y openspec/changes/plataforma-2027/specs/menciones-del-grupo/spec.md): la mención nunca va dentro
del texto de la pieza; va en un bloque señalizado al pie con su declaración; una pieza lleva una mención como mucho;
los análisis del director y las piezas que ya tratan del grupo no llevan ninguna; el director recibe el resumen con un
enlace para editar o retirar cada mención; retirar = `estado: retirada` (nunca se borra).
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
    q = urllib.parse.urlencode({"utm_source": "moticias", "utm_medium": "nota-de-la-casa",
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


def proponer(a, productos, data_dir, fecha, estado="publicada"):
    mejor = None
    for prod in productos:
        pts, motivos = puntuar(a, prod)
        if pts is None or pts < int(prod.get("umbral") or 6):
            continue
        if mejor is None or pts > mejor[0]:
            mejor = (pts, prod, motivos)
    if not mejor:
        return None
    pts, prod, motivos = mejor
    est = estado
    tope = int(prod.get("max_por_semana") or 0)
    if tope and publicadas_ultimos_dias(data_dir, prod["id"], fecha) >= tope:
        est = "propuesta"
        motivos = motivos + ["tope semanal alcanzado: queda como propuesta"]
    return {"producto": prod["id"], "nombre": prod.get("name"), "texto": (prod.get("textos") or {}).get("corto", ""),
            "cta": (prod.get("textos") or {}).get("cta", ""), "url": con_utm(prod["url"], prod, a["id"]),
            "estado": est, "motivo": "; ".join(motivos), "puntuacion": pts, "origen": "automatica",
            "propuesta_en": datetime.datetime.now().astimezone().isoformat(timespec="minutes")}


# ---------- bloque HTML (lo usa ghost_publish) ----------
def bloque_html(a, vertical, inline=html.escape):
    pub = [m for m in a.get("menciones") or [] if m.get("estado") == "publicada"]
    if not pub:
        return ""
    cfg = vertical.get("productos") or {}
    etiqueta = cfg.get("label", "Nota de la casa")
    decl = cfg.get("declaracion", "%s pertenece al mismo grupo empresarial que este servicio. La mención no es publicidad pagada y no ha intervenido en la selección ni en la redacción de la pieza." % vertical.get("name", "MOTICIAS"))
    m = pub[0]
    return ('<aside class="nota-de-la-casa"><p class="nota-de-la-casa-etiqueta"><small>%s</small></p>'
            '<p>%s <a href="%s" rel="noopener">%s</a></p><p class="nota-de-la-casa-declaracion"><small>%s</small></p></aside>'
            % (inline(etiqueta), inline(m.get("texto", "")), html.escape(m.get("url", ""), quote=True),
               inline(m.get("cta") or m.get("nombre") or ""), inline(decl)))


# ---------- informe y correo ----------
def informe(piezas, vertical, base_url, fecha):
    filas = []
    for a in piezas:
        for m in a.get("menciones") or []:
            if m.get("estado") not in ("publicada", "propuesta"):
                continue
            filas.append((a, m))
    if not filas:
        return None, None
    md = ["# Menciones del grupo · %s" % fecha, "",
          "%d mención(es) en la edición. Para editar el texto o retirar una mención, abre el enlace «GitHub» (cambia `texto` o pon `estado: \"retirada\"`); la rutina republica la pieza. El enlace «Ghost» abre el editor del post publicado." % len(filas), ""]
    h = ["<h2>Menciones del grupo · %s</h2><p>%d mención(es). <b>GitHub</b> edita la fuente de verdad (texto o <code>estado: retirada</code>); <b>Ghost</b> abre el editor del post.</p>" % (html.escape(fecha), len(filas))]
    for a, m in filas:
        u = url_pieza(a, base_url)
        ge, re_ = url_edicion_ghost(a, base_url), REPO_EDIT % a["id"]
        md += ["## %s" % a.get("title", a["id"]), "- Pieza: %s" % u, "- Producto: **%s** · estado: %s · puntuación %s" % (m.get("nombre"), m.get("estado"), m.get("puntuacion")),
               "- Texto: %s — [%s](%s)" % (m.get("texto"), m.get("cta"), m.get("url")), "- Motivo: %s" % m.get("motivo"),
               "- Editar: [GitHub](%s) · [Ghost](%s)" % (re_, ge), ""]
        h.append('<div style="border:1px solid #ddd;padding:12px;margin:10px 0"><p><b><a href="%s">%s</a></b></p>'
                 '<p>Producto: <b>%s</b> · estado: %s · puntuación %s</p><p style="background:#f6f6f6;padding:8px">%s <a href="%s">%s</a></p>'
                 '<p><small>Motivo: %s</small></p><p><a href="%s" style="padding:6px 10px;border:1px solid #333;text-decoration:none">Editar en GitHub</a> &nbsp; '
                 '<a href="%s" style="padding:6px 10px;border:1px solid #333;text-decoration:none">Editar en Ghost</a></p></div>'
                 % (html.escape(u, quote=True), html.escape(a.get("title", a["id"])), html.escape(m.get("nombre") or ""), html.escape(m.get("estado") or ""), m.get("puntuacion"),
                    html.escape(m.get("texto") or ""), html.escape(m.get("url") or "", quote=True), html.escape(m.get("cta") or ""),
                    html.escape(m.get("motivo") or ""), html.escape(re_, quote=True), html.escape(ge, quote=True)))
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
            m = proponer(a, productos, args.data, fecha, args.estado)
            if m and args.aplicar:
                a.setdefault("menciones", []).append(m)
                guardar_pieza(a)
            res.append({"id": a["id"], "mencion": m})
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
