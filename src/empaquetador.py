#!/usr/bin/env python3
"""MOTICIAS · Módulo 2 · Empaquetador de ediciones a medida (página, correo y PDF). Solo biblioteca estándar;
para el PDF usa Google Chrome sin cabeza o wkhtmltopdf si están instalados (si no, deja página y correo y lo dice).

  python3 -I src/empaquetador.py --perfil data/perfiles/edicion-autobus-y-carretera.json [--hasta AAAA-MM-DD] [--out work/ediciones]
  python3 -I src/empaquetador.py --perfil ... --seleccion work/sel.json   (reutiliza una selección ya hecha o revisada)

Salida en <out>/<perfil>/<fecha>/: seleccion.json (lo que ha elegido el selector; editable antes de emitir),
revision.md (texto para el documento de revisión colaborativo), pagina.html (edición privada), correo.html
(HTML sencillo con estilos en línea para Brevo), edicion.pdf (si hay conversor) y resumen.json.

Reglas: el contenido del cliente (perfil.client_content_dir, un JSON por pieza: {title, date, body_md, url})
se maqueta igual pero con la marca «Contenido de <cliente>»; nunca se mezcla sin marca. Cada pieza de
MOTICIAS enlaza a su original y muestra cuántas fuentes y cuántas oficiales la sostienen. La marca
«Powered by MOTICIAS» y la declaración de intereses del vertical van siempre al pie.
"""
import argparse, datetime, glob, html, json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from selector import seleccionar  # noqa: E402
from ghost_publish import md_to_html, inline  # noqa: E402

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
SECCION = {"tierra": "Tierra", "mar": "Mar", "aire": "Aire", "regulacion": "Regulación", "licitaciones": "Licitaciones",
           "analisis": "Análisis", "logistica": "Logística", "tecnologia": "Tecnología", "datos": "Datos"}


def fecha_larga(iso):
    try:
        d = datetime.date.fromisoformat(iso[:10])
        return "%d de %s de %d" % (d.day, MESES[d.month - 1], d.year)
    except Exception:
        return iso or ""


def fecha_corta(iso):
    try:
        d = datetime.date.fromisoformat(iso[:10])
        return "%d %s" % (d.day, MESES[d.month - 1][:3])
    except Exception:
        return iso or ""


def e(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def contenido_cliente(perfil, hasta):
    d = perfil.get("client_content_dir")
    if not d:
        return []
    d = d if os.path.isabs(d) else os.path.join(ROOT, d)
    out = []
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        try:
            o = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if hasta and (o.get("date") or "") > hasta:
            continue
        o.setdefault("id", os.path.basename(f)[:-5])
        out.append(o)
    out.sort(key=lambda o: o.get("date") or "", reverse=True)
    return out[: int((perfil.get("limits") or {}).get("client_content", 5))]


CSS = """
:root{--ink:#0f1f33;--ink-2:#27354a;--muted:#5f6877;--paper:#f3f2ee;--paper-2:#fff;--line:#d8d5cc;--accent:%(accent)s;--gold:#e9b532}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 "IBM Plex Sans","Helvetica Neue",Arial,sans-serif}
.wrap{max-width:880px;margin:0 auto;background:var(--paper-2);box-shadow:0 1px 2px rgba(15,31,51,.06),0 12px 32px rgba(15,31,51,.08)}
header.top{background:var(--ink);color:#f3f2ee;padding:28px 40px;display:flex;align-items:center;gap:20px;border-bottom:6px solid var(--accent)}
.logo{width:56px;height:56px;border-radius:12px;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;font:700 22px "Newsreader",Georgia,serif;flex:none}
header.top h1{margin:0;font:600 28px/1.1 "Newsreader",Georgia,serif}header.top p{margin:4px 0 0;color:#b8c0cc;font-size:14px}
.meta{padding:12px 40px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
.intro{padding:24px 40px 8px;font-size:17px;line-height:1.55;color:var(--ink-2)}.intro p{margin:0 0 10px}
h2.sec{margin:28px 40px 8px;padding-bottom:6px;border-bottom:2px solid var(--accent);font:600 13px "IBM Plex Sans",Arial,sans-serif;text-transform:uppercase;letter-spacing:.12em;color:var(--accent)}
article.p{padding:16px 40px;border-bottom:1px solid var(--line);display:grid;grid-template-columns:1fr 200px;gap:20px}
article.p.nofoto{grid-template-columns:1fr}
.k{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--accent)}.k span{color:var(--muted);font-weight:400;text-transform:none;letter-spacing:0;margin-left:8px}
article.p h3{margin:4px 0 2px;font:600 22px/1.2 "Newsreader",Georgia,serif}article.p h3 a{color:var(--ink);text-decoration:none}
.sub{margin:0 0 8px;color:var(--ink-2);font-size:15px;font-style:italic}.sum{margin:0 0 8px;color:var(--ink-2)}
.kf{display:inline-block;background:#fbf3d9;border-left:3px solid var(--gold);padding:4px 10px;font-size:13px;margin:4px 0 6px}
.tr{font-size:12px;color:var(--muted)}.tr a{color:var(--muted)}
article.p img{width:200px;height:134px;object-fit:cover;border-radius:6px;display:block}.cr{font-size:10px;color:var(--muted);margin-top:4px}
.cliente{background:#eef3ea;border-left:4px solid var(--accent)}.cliente .k{color:#355024}
table.b{width:calc(100%% - 80px);margin:8px 40px;border-collapse:collapse;font-size:13px}table.b td{padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
table.b td.d{white-space:nowrap;color:var(--muted);width:84px;font-variant-numeric:tabular-nums}table.b td.t{width:150px;color:var(--muted)}table.b a{color:var(--ink);text-decoration:none;font-weight:500}
.plazo td.d{color:var(--accent);font-weight:600}
.contacto{margin:28px 40px 0;padding:18px 22px;background:var(--paper);border:1px solid var(--line);border-radius:8px}.contacto h4{margin:0 0 6px;font:600 18px "Newsreader",Georgia,serif}.contacto p{margin:0;color:var(--ink-2)}
footer{padding:20px 40px 28px;font-size:12px;color:var(--muted);border-top:1px solid var(--line);margin-top:24px}footer p{margin:4px 0}footer b{color:var(--ink)}
@page{size:A4;margin:14mm 12mm}@media print{body{background:#fff}.wrap{box-shadow:none;max-width:none}header.top{-webkit-print-color-adjust:exact;print-color-adjust:exact}article.p{orphans:3;widows:3}article.p h3{break-after:avoid}h2.sec{break-after:avoid}}
"""


def miniatura(src, out_dir):
    """Copia reducida (400 px) junto a la salida, para que el PDF no pese; si no hay PIL, usa el original."""
    if not out_dir:
        return src
    try:
        from PIL import Image  # opcional
    except Exception:
        return src
    try:
        os.makedirs(os.path.join(out_dir, "img"), exist_ok=True)
        dst = os.path.join(out_dir, "img", os.path.basename(src))
        if not os.path.exists(dst):
            im = Image.open(src).convert("RGB")
            im.thumbnail((400, 400))
            im.save(dst, "JPEG", quality=78)
        return dst
    except Exception:
        return src


def bloque_pieza(a, out_dir=None, cliente=None):
    img = a.get("image")
    src = None
    if img:
        if img.startswith("img/"):
            p = os.path.join(ROOT, "portal", img)
            src = miniatura(p, out_dir) if os.path.exists(p) else None
        elif img.startswith("http"):
            src = img
    cls = "p" + ("" if src else " nofoto") + (" cliente" if cliente else "")
    k = ("Contenido de %s" % e(cliente)) if cliente else e(a.get("kicker") or SECCION.get(a.get("section"), ""))
    h = ["<article class='%s'><div>" % cls, "<div class='k'>%s<span>%s</span></div>" % (k, e(fecha_corta(a.get("date"))))]
    h.append("<h3><a href='%s'>%s</a></h3>" % (e(a.get("url") or "#"), e(a.get("title"))))
    if a.get("subtitle"):
        h.append("<p class='sub'>%s</p>" % e(a["subtitle"]))
    if a.get("summary"):
        h.append("<p class='sum'>%s</p>" % e(a["summary"]))
    if a.get("body_html"):
        h.append(a["body_html"])
    if a.get("key_fact"):
        h.append("<div class='kf'>%s</div>" % e(a["key_fact"]))
    if not cliente:
        h.append("<div class='tr'>%s fuentes, %s oficiales · <a href='%s'>Leer la pieza completa en MOTICIAS</a></div>" % (
            a.get("sources_count", "—"), a.get("sources_oficiales", "—"), e(a.get("url") or "#")))
    h.append("</div>")
    if src:
        h.append("<div><img src='%s' alt=''><div class='cr'>%s</div></div>" % (e(src), e(a.get("image_credit") or "")))
    h.append("</article>")
    return "\n".join(h)


def pagina_html(perfil, sel, vertical, propios, out_dir=None):
    b = perfil.get("brand") or {}
    accent = b.get("accent") or "#0f1f33"
    nombre = b.get("client_name") or perfil.get("name")
    hoy = fecha_larga(sel["hasta"])
    h = ["<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>",
         "<title>%s · %s</title><meta name='robots' content='noindex'><style>%s</style></head><body><div class='wrap'>" % (e(perfil.get("name")), e(hoy), CSS % {"accent": accent}),
         "<header class='top'><div class='logo'>%s</div><div><h1>%s</h1><p>%s</p></div></header>" % (e(b.get("logo_text") or "M"), e(perfil.get("name")), e(b.get("tagline") or "")),
         "<div class='meta'><span>%s · edición %s</span><span>%s piezas · %s boletines · %s plazos</span></div>" % (
             e(nombre), e(hoy), sel["counts"]["articles"], sel["counts"]["boletines"], sel["counts"]["agenda"])]
    if b.get("intro_md"):
        h.append("<div class='intro'>%s</div>" % md_to_html(b["intro_md"]))
    if propios:
        h.append("<h2 class='sec'>%s</h2>" % e(perfil.get("client_content_title") or ("Comunicados de %s" % nombre)))
        for a in propios:
            a = dict(a, body_html=md_to_html(a.get("body_md") or ""))
            h.append(bloque_pieza(a, out_dir, cliente=nombre))
    if sel["articles"]:
        h.append("<h2 class='sec'>Lo esencial</h2>")
        for a in sel["articles"]:
            h.append(bloque_pieza(a, out_dir))
    if sel["boletines"]:
        h.append("<h2 class='sec'>Boletines oficiales</h2><table class='b'>")
        for x in sel["boletines"]:
            h.append("<tr><td class='d'>%s</td><td class='t'>%s · %s</td><td><a href='%s'>%s</a>%s</td></tr>" % (
                e(fecha_corta(x.get("fecha"))), e(x.get("boletin") or ""), e(x.get("tipo") or ""), e(x.get("url") or "#"), e(x.get("titulo_corto") or x.get("referencia")),
                ("<br><span style='color:var(--muted)'>%s</span>" % e(x["nota"])) if x.get("nota") else ""))
        h.append("</table>")
    if sel["agenda"]:
        h.append("<h2 class='sec'>Próximos plazos</h2><table class='b'>")
        for g in sel["agenda"]:
            t = e(g.get("title"))
            if g.get("url"):
                t = "<a href='%s'>%s</a>" % (e(g["url"]), t)
            h.append("<tr class='plazo'><td class='d'>%s</td><td class='t'>%s</td><td>%s%s</td></tr>" % (
                e(fecha_corta(g.get("date"))), e(g.get("kind") or ""), t, (" · " + e(g["authority"])) if g.get("authority") else ""))
        h.append("</table>")
    c = perfil.get("contact") or {}
    if c.get("title"):
        h.append("<div class='contacto'><h4>%s</h4><p>%s%s</p></div>" % (e(c["title"]), e(c.get("text") or ""),
                 (" <a href='%s'>%s</a>" % (e(c["cta_url"]), e(c.get("cta_text") or c["cta_url"]))) if c.get("cta_url") else ""))
    ed = vertical.get("editor") or {}
    h.append("<footer><p><b>Powered by MOTICIAS</b> · Noticias con M de Movilidad y Transportes · <a href='%s'>%s</a></p>" % (e(sel["base_url"]), e(vertical.get("domain", "moticias.com"))))
    h.append("<p>Selección automática según el perfil «%s» (%s) revisada por la redacción. Cada pieza enlaza a su original con todas sus fuentes y fechas.</p>" % (e(perfil.get("id")), e(perfil.get("cadence") or "a demanda")))
    if ed.get("interests_note"):
        h.append("<p>%s</p>" % e(ed["interests_note"]))
    h.append("<p>Generado el %s.</p></footer></div></body></html>" % e(sel["generated_at"][:16].replace("T", " ")))
    return "\n".join(h)


def correo_html(perfil, sel, vertical, propios):
    """HTML sencillo, tablas y estilos en línea: lo que los clientes de correo soportan. Listo para Brevo."""
    b = perfil.get("brand") or {}
    accent = b.get("accent") or "#0f1f33"
    nombre = b.get("client_name") or perfil.get("name")
    f = "font-family:Georgia,'Times New Roman',serif"
    s = "font-family:Arial,Helvetica,sans-serif"
    h = ["<!doctype html><html lang='es'><head><meta charset='utf-8'><title>%s</title></head><body style='margin:0;background:#f3f2ee'>" % e(perfil.get("name")),
         "<table role='presentation' width='100%%' cellpadding='0' cellspacing='0' style='background:#f3f2ee'><tr><td align='center' style='padding:16px'>",
         "<table role='presentation' width='600' cellpadding='0' cellspacing='0' style='max-width:600px;width:100%%;background:#ffffff'>",
         "<tr><td style='background:#0f1f33;color:#f3f2ee;padding:20px 24px;border-bottom:5px solid %s;%s'><div style='font-size:22px;font-weight:bold'>%s</div><div style='font-size:13px;color:#b8c0cc;%s'>%s · %s</div></td></tr>" % (
             accent, f, e(perfil.get("name")), s, e(nombre), e(fecha_larga(sel["hasta"])))]
    if b.get("intro_md"):
        h.append("<tr><td style='padding:18px 24px 4px;%s;font-size:15px;line-height:1.5;color:#27354a'>%s</td></tr>" % (s, md_to_html(b["intro_md"])))

    def seccion(t):
        h.append("<tr><td style='padding:18px 24px 4px;%s;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:%s;border-bottom:2px solid %s'>%s</td></tr>" % (s, accent, accent, e(t)))

    def pieza(a, cliente=None):
        h.append("<tr><td style='padding:14px 24px;border-bottom:1px solid #e3e1da;%s'>" % (("background:#eef3ea;" if cliente else "")))
        h.append("<div style='%s;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:%s;font-weight:bold'>%s <span style='color:#5f6877;font-weight:normal;text-transform:none;letter-spacing:0'>%s</span></div>" % (
            s, accent, ("Contenido de %s" % e(cliente)) if cliente else e(a.get("kicker") or ""), e(fecha_corta(a.get("date")))))
        h.append("<div style='%s;font-size:19px;line-height:1.25;margin:4px 0'><a href='%s' style='color:#0f1f33;text-decoration:none'>%s</a></div>" % (f, e(a.get("url") or "#"), e(a.get("title"))))
        if a.get("subtitle"):
            h.append("<div style='%s;font-size:14px;color:#27354a;font-style:italic;margin-bottom:6px'>%s</div>" % (s, e(a["subtitle"])))
        if a.get("summary"):
            h.append("<div style='%s;font-size:14px;line-height:1.5;color:#27354a'>%s</div>" % (s, e(a["summary"])))
        if a.get("body_html"):
            h.append("<div style='%s;font-size:14px;line-height:1.5;color:#27354a'>%s</div>" % (s, a["body_html"]))
        if a.get("key_fact"):
            h.append("<div style='%s;font-size:13px;background:#fbf3d9;border-left:3px solid #e9b532;padding:4px 10px;margin:8px 0;display:inline-block'>%s</div>" % (s, e(a["key_fact"])))
        if not cliente:
            h.append("<div style='%s;font-size:12px;color:#5f6877'>%s fuentes, %s oficiales · <a href='%s' style='color:#5f6877'>Leer en MOTICIAS</a></div>" % (s, a.get("sources_count", "—"), a.get("sources_oficiales", "—"), e(a.get("url") or "#")))
        h.append("</td></tr>")

    if propios:
        seccion(perfil.get("client_content_title") or ("Comunicados de %s" % nombre))
        for a in propios:
            pieza(dict(a, summary=None, body_html=md_to_html(a.get("body_md") or "")), cliente=nombre)
    if sel["articles"]:
        seccion("Lo esencial")
        for a in sel["articles"]:
            pieza(a)
    if sel["boletines"]:
        seccion("Boletines oficiales")
        for x in sel["boletines"]:
            h.append("<tr><td style='padding:8px 24px;border-bottom:1px solid #e3e1da;%s;font-size:13px'><span style='color:#5f6877'>%s · %s</span><br><a href='%s' style='color:#0f1f33;text-decoration:none;font-weight:bold'>%s</a>%s</td></tr>" % (
                s, e(fecha_corta(x.get("fecha"))), e(x.get("tipo") or ""), e(x.get("url") or "#"), e(x.get("titulo_corto") or x.get("referencia")),
                ("<br><span style='color:#5f6877'>%s</span>" % e(x["nota"])) if x.get("nota") else ""))
    if sel["agenda"]:
        seccion("Próximos plazos")
        for g in sel["agenda"]:
            h.append("<tr><td style='padding:8px 24px;border-bottom:1px solid #e3e1da;%s;font-size:13px'><span style='color:%s;font-weight:bold'>%s</span> · %s%s</td></tr>" % (
                s, accent, e(fecha_corta(g.get("date"))), ("<a href='%s' style='color:#0f1f33;text-decoration:none'>%s</a>" % (e(g["url"]), e(g.get("title")))) if g.get("url") else e(g.get("title")),
                (" · " + e(g["authority"])) if g.get("authority") else ""))
    ed = vertical.get("editor") or {}
    h.append("<tr><td style='padding:18px 24px;%s;font-size:12px;color:#5f6877;border-top:1px solid #e3e1da'><b style='color:#0f1f33'>Powered by MOTICIAS</b> · Noticias con M de Movilidad y Transportes · <a href='%s' style='color:#5f6877'>%s</a><br>%s<br>Recibes este correo porque tu organización está suscrita a esta edición a medida. {{ unsubscribe }}</td></tr>" % (
        s, e(sel["base_url"]), e(vertical.get("domain", "moticias.com")), e(ed.get("interests_note") or "")))
    h.append("</table></td></tr></table></body></html>")
    return "\n".join(h)


def revision_md(perfil, sel, propios):
    l = ["# Revisión · %s · %s" % (perfil.get("name"), fecha_larga(sel["hasta"])), "",
         "Marca con una X lo que se quita; añade debajo lo que falta. Al aprobar, se emite tal cual quede `seleccion.json`.", ""]
    if propios:
        l += ["## Contenido del cliente"] + ["- [ ] %s · %s" % (a.get("date"), a.get("title")) for a in propios] + [""]
    l += ["## Lo esencial (%d de %d candidatas)" % (sel["counts"]["articles"], sel["counts"]["articles_candidatas"])]
    l += ["- [ ] (%s) %s · **%s** — %s" % (a.get("score"), a.get("date"), a.get("title"), a.get("kicker")) for a in sel["articles"]]
    l += ["", "## Boletines (%d)" % sel["counts"]["boletines"]] + ["- [ ] %s · %s · %s" % (x.get("fecha"), x.get("tipo"), x.get("titulo_corto")) for x in sel["boletines"]]
    l += ["", "## Plazos (%d)" % sel["counts"]["agenda"]] + ["- [ ] %s · %s" % (g.get("date"), g.get("title")) for g in sel["agenda"]]
    l += ["", "## Falta algo", "- ", ""]
    return "\n".join(l)


def a_pdf(html_path, pdf_path):
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if chrome:
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer", "--print-to-pdf=" + pdf_path, "file://" + os.path.abspath(html_path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:
            return "chrome"
    wk = shutil.which("wkhtmltopdf")
    if wk:
        subprocess.run([wk, "--quiet", "--enable-local-file-access", html_path, pdf_path], capture_output=True, text=True, timeout=120)
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:
            return "wkhtmltopdf"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--perfil", required=True)
    ap.add_argument("--hasta")
    ap.add_argument("--seleccion", help="JSON de una selección ya hecha (p. ej. tras la revisión)")
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "ediciones"))
    ap.add_argument("--base-url")
    ap.add_argument("--sin-pdf", action="store_true")
    a = ap.parse_args()
    perfil = json.load(open(a.perfil, encoding="utf-8"))
    vid = perfil.get("vertical") or "movilidad"
    vertical = json.load(open(os.path.join(ROOT, "verticals", vid + ".json"), encoding="utf-8"))
    sel = json.load(open(a.seleccion, encoding="utf-8")) if a.seleccion else seleccionar(perfil, a.hasta, a.base_url, os.environ.get("GHOST_URL"), os.environ.get("GHOST_CONTENT_KEY"))
    propios = contenido_cliente(perfil, sel["hasta"])
    out = os.path.join(a.out, perfil["id"], sel["hasta"])
    os.makedirs(out, exist_ok=True)
    json.dump(sel, open(os.path.join(out, "seleccion.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(out, "revision.md"), "w", encoding="utf-8").write(revision_md(perfil, sel, propios))
    pagina = os.path.join(out, "pagina.html")
    open(pagina, "w", encoding="utf-8").write(pagina_html(perfil, sel, vertical, propios, out))
    open(os.path.join(out, "correo.html"), "w", encoding="utf-8").write(correo_html(perfil, sel, vertical, propios))
    pdf = None
    if not a.sin_pdf and (perfil.get("outputs") or {}).get("pdf", True):
        pdf = a_pdf(pagina, os.path.join(out, "edicion.pdf"))
    resumen = {"perfil": perfil["id"], "fecha": sel["hasta"], "out": out, "counts": sel["counts"], "contenido_cliente": len(propios),
               "pdf": pdf or "no generado (sin Chrome ni wkhtmltopdf)", "generated_at": sel["generated_at"]}
    json.dump(resumen, open(os.path.join(out, "resumen.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(resumen, ensure_ascii=False))


if __name__ == "__main__":
    main()
