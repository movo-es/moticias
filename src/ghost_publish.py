#!/usr/bin/env python3
"""MOTICIAS · Publicador a Ghost (Admin API), solo biblioteca estándar.

  python3 -I src/ghost_publish.py --dry-run --ids <id> [<id> ...]      genera el HTML y el JSON del post sin tocar Ghost
  python3 -I src/ghost_publish.py --dry-run --date AAAA-MM-DD         todas las piezas de una edición
  python3 -I src/ghost_publish.py --all --status draft                 publica (o deja en borrador) todas las piezas de data/articles
  python3 -I src/ghost_publish.py --date AAAA-MM-DD --status published  (edición diaria: rutinarias publicadas, críticas en borrador)
  python3 -I src/ghost_publish.py --pages [--ids <slug> ...]            páginas fijas de data/paginas/ (siempre en borrador)

Variables de entorno (nunca en el repositorio): GHOST_URL (p. ej. https://moticias.ghost.io o https://moticias.com)
y GHOST_ADMIN_KEY (clave de una integración personalizada de Ghost, formato id:secret).
Vertical: --vertical movilidad (lee verticals/<id>.json para secciones y etiquetas).

Qué hace con cada pieza de data/articles/<id>.json:
- Construye el HTML del post: respuesta directa (summary), cuerpo (body_md → HTML sencillo), cifras clave, cronología,
  guía rápida (los cinco bloques), fuentes con fechas, recuadro de trazabilidad y declaración de intereses si procede.
- Firma (verticals/<id>.json → editorial.ghost_authors): «G. Jordan» → usuario g-jordan, «Rainer» → rainer. Si el
  usuario de G. Jordan no existe en Ghost (ni por slug ni por nombre), la pieza sale a nombre de Rainer y se avisa.
- Estado: --status published publica solo las piezas con risk «rutinaria»; las críticas (risk «critica» o status
  «pendiente») y los borradores se suben o actualizan siempre como draft, a la espera del director.
- Metadatos: título, slug (= id), extracto (summary), etiquetas (#<section>, subsector, tags), autor según la firma,
  fecha de publicación (published_at), imagen destacada (si hay URL pública; las /_blob/ no se suben todavía),
  codeinjection_head con JSON-LD NewsArticle.
- Crea o actualiza el post por slug (busca antes con GET /posts/slug/<slug>/) y guarda el resultado en
  work/ghost/<id>.json (id de Ghost, url, updated_at) para la sala de redacción.
Limitaciones conocidas (se resuelven por OpenSpec): el Markdown se convierte con un conversor mínimo (títulos, negrita,
cursiva, enlaces, listas, citas); las fotos /_blob/ requieren subirlas con /images/upload/ (pendiente).
"""
import argparse, base64, datetime, glob, hashlib, hmac, html, json, os, re, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Moticias/1.0 (+https://moticias.com)"


# ---------- utilidades ----------
def b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def ghost_token(admin_key):
    """JWT HS256 de 5 minutos para la Admin API, como pide Ghost."""
    kid, secret = admin_key.split(":")
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT", "kid": kid}
    payload = {"iat": now, "exp": now + 300, "aud": "/admin/"}
    signing = b64url(json.dumps(header, separators=(",", ":")).encode()) + "." + b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(bytes.fromhex(secret), signing.encode(), hashlib.sha256).digest()
    return signing + "." + b64url(sig)


def api(method, url, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Ghost " + token, "Content-Type": "application/json", "Accept-Version": "v5.0", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


# ---------- Markdown mínimo → HTML ----------
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" rel="noopener">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    return s


def md_to_html(md):
    out, para, lst = [], [], None

    def flush():
        nonlocal para
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para)))
            para = []

    def close_list():
        nonlocal lst
        if lst:
            out.append("</ul>")
            lst = None

    for raw in (md or "").splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush(); close_list(); continue
        if line.startswith("## "):
            flush(); close_list(); out.append("<h2>%s</h2>" % inline(line[3:].strip())); continue
        if line.startswith("### "):
            flush(); close_list(); out.append("<h3>%s</h3>" % inline(line[4:].strip())); continue
        if line.startswith(">> "):
            flush(); close_list(); out.append('<blockquote class="kg-blockquote-alt">%s</blockquote>' % inline(line[3:].strip())); continue
        if line.startswith("> "):
            flush(); close_list(); out.append("<blockquote>%s</blockquote>" % inline(line[2:].strip())); continue
        if line.startswith("- "):
            flush()
            if not lst:
                out.append("<ul>"); lst = True
            out.append("<li>%s</li>" % inline(line[2:].strip())); continue
        close_list(); para.append(line.strip())
    flush(); close_list()
    return "\n".join(out)


# ---------- construcción del post ----------
def fmt_date(d):
    if not d:
        return "sin fecha publicada"
    try:
        return datetime.date.fromisoformat(d[:10]).strftime("%d-%m-%Y")
    except ValueError:
        return d


def build_html(a, vertical):
    parts = []
    if a.get("summary"):
        parts.append('<p class="respuesta-directa"><strong>%s</strong></p>' % inline(a["summary"]))
    parts.append(md_to_html(a.get("body_md", "")))
    if a.get("key_data"):
        parts.append("<h2>Cifras clave</h2><ul>" + "".join(
            "<li><strong>%s:</strong> %s <small>(%s)</small></li>" % (inline(k.get("label", "")), inline(k.get("value", "")), inline(k.get("source", "")))
            for k in a["key_data"]) + "</ul>")
    if a.get("timeline"):
        parts.append("<h2>Cronología</h2><ul>" + "".join(
            "<li><strong>%s</strong> · %s</li>" % (inline(t.get("date", "")), inline(t.get("text", ""))) for t in a["timeline"]) + "</ul>")
    guide = [("De qué trata", a.get("summary")), ("Quiénes son los protagonistas", a.get("actors")),
             ("Para quién es relevante", a.get("relevance_for")), ("Por qué es importante", a.get("why")), ("Qué puede pasar ahora", a.get("next"))]
    if any(v for _, v in guide):
        parts.append("<h2>Guía rápida</h2>" + "".join("<p><strong>%s.</strong> %s</p>" % (k, inline(v)) for k, v in guide if v))
    if a.get("sources"):
        parts.append("<h2>Para saber más</h2><ul>" + "".join(
            '<li>[%s] %s — <a href="%s" rel="noopener">%s</a> (publicado %s; consultado %s)</li>' % (
                "Fuente oficial" if s.get("kind") == "oficial" else "Medios", inline(s.get("outlet", "")), html.escape(s.get("url", ""), quote=True),
                inline(s.get("title", "")), fmt_date(s.get("published")), fmt_date(s.get("accessed"))) for s in a["sources"]) + "</ul>")
    traz = ["Hechos: %s" % fmt_date(a.get("event_date")), "Redacción: %s" % (a.get("published_at") or "")]
    if a.get("revised_at"):
        traz.append("Revisión: %s" % a["revised_at"])
    parts.append('<p class="trazabilidad"><small>%s</small></p>' % " · ".join(inline(t) for t in traz))
    if a.get("author_note"):
        parts.append('<p class="intereses"><small>%s</small></p>' % inline(a["author_note"]))
    ed = vertical.get("editor", {})
    parts.append('<p class="fin"><small>%s · %s · FIN</small></p>' % (inline(vertical.get("name", "")), inline(a.get("date", ""))))
    return "\n".join(parts)


def jsonld(a, vertical, url):
    d = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": a.get("title"), "description": a.get("summary"),
         "datePublished": a.get("published_at"), "dateModified": a.get("revised_at") or a.get("published_at"), "inLanguage": "es-ES",
         "author": {"@type": "Person", "name": a.get("author") or "Redacción"},
         "publisher": {"@type": "Organization", "name": vertical.get("name"), "url": "https://%s/" % vertical.get("domain", "")},
         "mainEntityOfPage": url, "articleSection": a.get("section"), "keywords": ", ".join(a.get("tags") or [])}
    if a.get("sources"):
        d["citation"] = [s.get("url") for s in a["sources"] if s.get("url")]
    return '<script type="application/ld+json">%s</script>' % json.dumps(d, ensure_ascii=False)


def build_post(a, vertical, base_url):
    slug = a["id"]
    url = "%s/%s/%s/" % (base_url.rstrip("/"), a.get("section", "noticias"), slug)
    tags = ["#" + a.get("section", "")] + [t for t in [a.get("subsector")] if t] + list(a.get("tags") or [])
    post = {"title": a.get("title"), "slug": slug, "html": build_html(a, vertical), "custom_excerpt": (a.get("summary") or "")[:300],
            "tags": [{"name": t} for t in tags if t], "published_at": a.get("published_at"), "meta_title": a.get("title"),
            "meta_description": (a.get("subtitle") or a.get("summary") or "")[:500], "codeinjection_head": jsonld(a, vertical, url)}
    im = a.get("image") or {}
    if im.get("src", "").startswith("http"):
        post["feature_image"] = im["src"]
        post["feature_image_caption"] = "%s · %s" % (im.get("credit", ""), im.get("license", ""))
        post["feature_image_alt"] = im.get("alt")
    return post


# ---------- firma y estado ----------
def is_critical(art):
    return art.get("risk") == "critica" or art.get("status") in ("pendiente", "borrador")


def target_status(art, requested):
    """Las críticas y los borradores nunca se publican desde aquí: esperan al director."""
    return "draft" if is_critical(art) else requested


def resolve_authors(vertical, base_url, token):
    """Devuelve ({firma: slug de Ghost}, avisos). Busca cada usuario por slug y, si no, por nombre."""
    ed = vertical.get("editorial", {})
    wanted = ed.get("ghost_authors", {})
    director = ed.get("director", "Rainer")
    st, res = api("GET", "%s/ghost/api/admin/users/?limit=all&fields=id,name,slug" % base_url, token)
    users = res.get("users", []) if st == 200 else []
    by_slug = {u["slug"]: u["slug"] for u in users}
    by_name = {u["name"].strip().lower(): u["slug"] for u in users}
    out, warn = {}, []
    for sig, slug in wanted.items():
        found = by_slug.get(slug) or by_name.get(sig.strip().lower())
        if found and found != slug:
            warn.append("El usuario «%s» existe en Ghost con slug «%s», no «%s»: se usa «%s»." % (sig, found, slug, found))
        out[sig] = found
    dslug = out.get(director)
    for sig in wanted:
        if not out[sig]:
            warn.append("El usuario «%s» (%s) no existe en Ghost: sus piezas salen a nombre de %s." % (sig, wanted[sig], director))
            out[sig] = dslug
    return out, warn


def author_slug(art, authors, vertical):
    ed = vertical.get("editorial", {})
    sig = art.get("author")
    if sig not in authors:
        sig = ed.get("director") if is_critical(art) else ed.get("default_author")
    return authors.get(sig)


# ---------- publicación ----------
def upsert(post, status, base_url, token, kind="posts"):
    post = dict(post, status=status)
    st, found = api("GET", "%s/ghost/api/admin/%s/slug/%s/?fields=id,updated_at" % (base_url, kind, post["slug"]), token)
    if st == 200 and found.get(kind):
        pid = found[kind][0]["id"]
        post["updated_at"] = found[kind][0]["updated_at"]
        st, res = api("PUT", "%s/ghost/api/admin/%s/%s/?source=html" % (base_url, kind, pid), token, {kind: [post]})
    else:
        st, res = api("POST", "%s/ghost/api/admin/%s/?source=html" % (base_url, kind), token, {kind: [post]})
    if st not in (200, 201):
        return None, res
    p = res[kind][0]
    out = {"ghost_id": p["id"], "url": p.get("url"), "status": p.get("status"), "updated_at": p.get("updated_at")}
    if p.get("status") != "published" and p.get("uuid"):
        out["preview_url"] = p.get("url") or "%s/p/%s/" % (base_url, p["uuid"])
    return out, None


def publish_pages(a, vertical, base_url, token):
    """Páginas fijas (aviso legal, privacidad, cookies, cómo trabajamos): data/paginas/<slug>.json, siempre en borrador."""
    outdir = os.path.join(ROOT, "work", "ghost", "paginas")
    os.makedirs(outdir, exist_ok=True)
    authors, warn = ({}, []) if a.dry_run else resolve_authors(vertical, base_url, token)
    director = vertical.get("editorial", {}).get("director", "Rainer")
    ok, bad = [], []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "paginas", "*.json"))):
        pg = json.load(open(p, encoding="utf-8"))
        if a.ids and pg["slug"] not in a.ids:
            continue
        page = {"title": pg["title"], "slug": pg["slug"], "html": md_to_html(pg["body_md"]),
                "custom_excerpt": pg.get("summary", "")[:300], "meta_description": pg.get("summary", "")[:500]}
        if authors.get(director):
            page["authors"] = [{"slug": authors[director]}]
        if a.dry_run:
            open(os.path.join(outdir, pg["slug"] + ".html"), "w", encoding="utf-8").write(page["html"])
            ok.append({"slug": pg["slug"]})
            continue
        res, err = upsert(page, "draft", base_url, token, kind="pages")
        if err:
            bad.append((pg["slug"], err))
        else:
            res["slug"] = pg["slug"]
            ok.append(res)
            json.dump(res, open(os.path.join(outdir, pg["slug"] + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"modo": "prueba" if a.dry_run else "draft", "paginas": ok, "errores": bad, "avisos": warn}, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vertical", default="movilidad")
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--date")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--status", default="draft", choices=["draft", "published"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pages", action="store_true")
    a = ap.parse_args()
    vertical = json.load(open(os.path.join(ROOT, "verticals", a.vertical + ".json"), encoding="utf-8"))
    if a.pages:
        base_url = os.environ.get("GHOST_URL", "https://%s" % vertical.get("domain", "")).rstrip("/")
        token = None
        if not a.dry_run:
            key = os.environ.get("GHOST_ADMIN_KEY")
            if not key or ":" not in key:
                sys.exit("Falta GHOST_ADMIN_KEY (id:secret) en el entorno; usa --dry-run para probar sin Ghost")
            token = ghost_token(key)
        return publish_pages(a, vertical, base_url, token)
    arts = []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "articles", "*.json"))):
        art = json.load(open(p, encoding="utf-8"))
        if a.ids and art["id"] not in a.ids:
            continue
        if a.date and art.get("date") != a.date:
            continue
        if not (a.ids or a.date or a.all):
            continue
        arts.append(art)
    if not arts:
        sys.exit("Ninguna pieza seleccionada (usa --ids, --date o --all)")
    base_url = os.environ.get("GHOST_URL", "https://%s" % vertical.get("domain", "")).rstrip("/")
    outdir = os.path.join(ROOT, "work", "ghost")
    os.makedirs(outdir, exist_ok=True)
    token = None
    if not a.dry_run:
        key = os.environ.get("GHOST_ADMIN_KEY")
        if not key or ":" not in key:
            sys.exit("Falta GHOST_ADMIN_KEY (id:secret) en el entorno; usa --dry-run para probar sin Ghost")
        token = ghost_token(key)
    tok_t = time.time()
    authors, warn = resolve_authors(vertical, base_url, token) if token else (dict(vertical.get("editorial", {}).get("ghost_authors", {})), [])
    ok, bad, counts = 0, [], {}
    for art in arts:
        post = build_post(art, vertical, base_url)
        slug = author_slug(art, authors, vertical)
        if slug:
            post["authors"] = [{"slug": slug}]
        status = target_status(art, a.status)
        counts[status] = counts.get(status, 0) + 1
        if a.dry_run:
            with open(os.path.join(outdir, art["id"] + ".html"), "w", encoding="utf-8") as fh:
                fh.write(post["html"])
            with open(os.path.join(outdir, art["id"] + ".post.json"), "w", encoding="utf-8") as fh:
                json.dump({k: v for k, v in post.items() if k != "html"}, fh, ensure_ascii=False, indent=1)
            ok += 1
            continue
        if time.time() - tok_t > 240:
            token, tok_t = ghost_token(key), time.time()
        res, err = upsert(post, status, base_url, token)
        if err:
            bad.append((art["id"], err))
        else:
            ok += 1
            with open(os.path.join(outdir, art["id"] + ".json"), "w", encoding="utf-8") as fh:
                json.dump(res, fh, ensure_ascii=False, indent=1)
        time.sleep(0.5)
    print(json.dumps({"modo": "prueba" if a.dry_run else a.status, "piezas": len(arts), "por_estado": counts, "ok": ok,
                      "errores": bad, "avisos": warn}, ensure_ascii=False))


if __name__ == "__main__":
    main()
