#!/usr/bin/env python3
"""MOTICIAS · Publica una nota de prensa en moticias.com (Ghost) con su marca y los tres ejes (cambio sala-de-prensa-v1).

Una nota es un post de Ghost con: etiqueta pública `notas-de-prensa` (la lista), interna `#comunicado`, autor «Comunicado»,
etiquetas de ejes `m-`, `tema-`, `t-` (filtrado por modo, tema y comunidad igual que las piezas) y la marca visible
«Nota de prensa · Comunicado de empresa · no es contenido editorial de MOTICIAS». Nunca va a la portada editorial ni al
boletín diario: el tema y `src/ghost_edicion.py` excluyen la etiqueta `#comunicado`.

Uso:
  python3 -I src/prensa_publicar.py desde-pedido <id>               # nota recibida por app.moticias.com/prensa/ (prensa_notas) → data/notas-de-prensa/<id>.json
  python3 -I src/prensa_publicar.py nueva nota.md --organizacion "X" --web https://x.es [--grupo]   # nota llegada por el buzón
  python3 -I src/prensa_publicar.py publicar <id> [--dry-run]       # sube a Ghost (GHOST_ADMIN_KEY) y anota url
  python3 -I src/prensa_publicar.py retirar <id>                    # status retirada y borrador en Ghost (nunca se borra)
  python3 -I src/prensa_publicar.py lista                           # crea/actualiza la etiqueta pública con su descripción
"""
import argparse, html, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import ghost_publish as G  # noqa: E402
import prensa_comun as P  # noqa: E402
import prensa_asesor as A  # noqa: E402
import prensa_impacto as I  # noqa: E402
from taxonomia import Taxonomia  # noqa: E402

V = json.load(open(os.path.join(ROOT, "verticals", "movilidad.json"), encoding="utf-8"))
CFG = V["prensa"]


def nueva(ruta_md, organizacion, web="", grupo=False, embargo=None, nid=None, texto=None):
    tx = Taxonomia()
    n = A.partir_md(texto) if texto is not None else A.leer_nota(ruta_md)
    ps = A.parrafos(n["cuerpo"])
    cuerpo, sobre, contacto = A.separar_cola(ps)
    ejes = tx.clasificar({"title": n["titulo"], "subtitle": n["subtitulo"], "summary": "\n".join(cuerpo)[:2500], "tags": []})
    nid = nid or P.nuevo_id(n["titulo"])
    nota = {"id": nid, "titulo": n["titulo"], "subtitulo": n["subtitulo"], "cuerpo_md": "\n\n".join(cuerpo),
            "sobre_md": "\n\n".join(sobre), "contacto_prensa_md": "\n\n".join(contacto),
            "organizacion": {"nombre": organizacion, "web": web}, "grupo": bool(grupo), "embargo_hasta": embargo,
            "recibida_en": P.ahora(), "publicada_en": None, "status": "recibida", "verificado_emisor": False,
            "modo": ejes["modo"], "submodo": ejes["submodo"], "temas": ejes["temas"], "territorios": ejes["territorios"],
            "taxonomia_manual": False, "ghost": None}
    nota["huellas"] = I.huellas(nota)
    P.guardar_nota(nota)
    return nota


def desde_pedido(nid):
    """Crea la nota pública a partir del pedido del formulario. El emisor queda verificado si escribió desde el dominio de
    su organización o confirmó su correo; si no, la nota se crea pero no se publica."""
    ped = P.leer_pedido(nid)
    if not ped:
        raise SystemExit("No hay pedido %s en la base." % nid)
    x = ped.get("nota") or {}
    texto = "# %s\n%s\n\n%s" % (ped["titulo"], ("## " + x["subtitulo"]) if x.get("subtitulo") else "", x.get("cuerpo") or "")
    n = nueva(None, x.get("organizacion") or "", x.get("web") or "", ped.get("grupo"), ped.get("embargo_hasta"), nid=nid, texto=texto)
    ver = ped.get("verificacion") or {}
    n["verificado_emisor"] = bool(ver.get("dominio_corporativo") or ver.get("correo_confirmado"))
    P.guardar_nota(n)
    P.guardar_pedido(nid, {"estado": "registrada"})
    return n


def cuerpo_html(n):
    m = CFG["marca"]
    org = html.escape(n["organizacion"]["nombre"])
    marca = ('<div class="mt-nota-marca" style="font:600 12px/1.5 system-ui,sans-serif;letter-spacing:.04em;text-transform:uppercase;'
             'color:#6b7280;border:1px solid #e5e7eb;border-radius:6px;padding:8px 12px;margin:0 0 1.5em">%s · %s%s</div>'
             % (html.escape(m["etiqueta"]), html.escape(m["aviso"]), (" · " + html.escape(m["aviso_grupo"])) if n.get("grupo") else ""))
    partes = [marca, '<p class="mt-nota-org"><strong>%s</strong>%s</p>' % (org, (' · <a href="%s" rel="noopener">%s</a>' % (html.escape(n["organizacion"]["web"]), html.escape(n["organizacion"]["web"]))) if n["organizacion"].get("web") else ""),
              G.md_to_html(n["cuerpo_md"])]
    if n.get("sobre_md"):
        partes.append('<hr><div class="mt-nota-sobre">%s</div>' % G.md_to_html(n["sobre_md"]))
    if n.get("contacto_prensa_md"):
        partes.append('<div class="mt-nota-contacto">%s</div>' % G.md_to_html(n["contacto_prensa_md"]))
    partes.append('<p class="mt-nota-pie" style="font-size:13px;color:#6b7280">Texto remitido por %s y publicado sin cambios de contenido. '
                  'MOTICIAS no ha verificado sus afirmaciones; si contiene un hecho con interés para el sector, la redacción lo tratará con sus propias fuentes. '
                  '<a href="/como-trabajamos/">Cómo trabajamos</a>.</p>' % org)
    return "\n".join(partes)


def post_de(n, tx):
    pseudo = {"submodo": n["submodo"], "temas": n["temas"], "territorios": n["territorios"], "tags": []}
    tags = [{"name": "Notas de prensa", "slug": CFG["ghost"]["tag_publica"]}, {"name": CFG["ghost"]["tag_interna"]}] + G.etiquetas_pieza(pseudo, tx)
    jl = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": n["titulo"], "description": n.get("subtitulo"),
          "datePublished": n.get("publicada_en"), "inLanguage": "es-ES", "genre": "Press release",
          "author": {"@type": "Organization", "name": n["organizacion"]["nombre"], "url": n["organizacion"].get("web") or None},
          "publisher": {"@type": "Organization", "name": V["name"], "url": "https://%s/" % V["domain"]}}
    return {"title": n["titulo"], "slug": n["id"], "html": cuerpo_html(n), "custom_excerpt": (n.get("subtitulo") or "")[:300], "tags": tags,
            "meta_title": "%s · Nota de prensa de %s" % (n["titulo"][:60], n["organizacion"]["nombre"]),
            "meta_description": (n.get("subtitulo") or n["cuerpo_md"][:300])[:500], "featured": False,
            "published_at": n.get("publicada_en"), "codeinjection_head": '<script type="application/ld+json">%s</script>' % json.dumps(jl, ensure_ascii=False)}


def publicar(nid, dry_run=False):
    n = P.leer_nota(nid)
    if not n.get("verificado_emisor"):
        raise SystemExit("La nota %s no tiene el emisor verificado (dominio corporativo o enlace de confirmación): no se publica." % nid)
    if not (n.get("submodo") and n.get("temas") and n.get("territorios")):
        raise SystemExit("La nota no tiene los tres ejes: no se publica.")
    if n.get("embargo_hasta") and n["embargo_hasta"] > P.ahora():
        raise SystemExit("Embargo hasta %s: se publicará después." % n["embargo_hasta"])
    n["publicada_en"] = n.get("publicada_en") or P.ahora()
    post = post_de(n, Taxonomia())
    if dry_run:
        os.makedirs(os.path.join(ROOT, "work", "prensa", nid), exist_ok=True)
        open(os.path.join(ROOT, "work", "prensa", nid, "post.html"), "w", encoding="utf-8").write(post["html"])
        print("Simulación: work/prensa/%s/post.html · etiquetas: %s" % (nid, ", ".join(t.get("slug") or t["name"] for t in post["tags"])))
        return
    url, key = os.environ.get("GHOST_URL") or V["ghost"]["url"], os.environ.get("GHOST_ADMIN_KEY")
    if not key:
        raise SystemExit("Falta GHOST_ADMIN_KEY: la nota queda lista pero sin publicar.")
    res, err = G.upsert(post, "published", url, G.ghost_token(key))
    if err:
        raise SystemExit("Ghost: %s" % json.dumps(err, ensure_ascii=False)[:400])
    n["status"], n["ghost"] = "publicada", res
    P.guardar_nota(n)
    try:
        if P.leer_pedido(nid):
            P.guardar_pedido(nid, {"estado": "publicada", "ghost_url": res["url"], "publicada_at": n["publicada_en"]})
    except Exception as e:  # noqa: BLE001 — la nota está publicada; el pedido se pone al día en la siguiente pasada
        print("Pedido sin actualizar:", e)
    print("Publicada:", res["url"])


def retirar(nid):
    n = P.leer_nota(nid)
    n["status"], n["retirada_en"] = "retirada", P.ahora()
    key = os.environ.get("GHOST_ADMIN_KEY")
    if key and n.get("ghost"):
        G.upsert(post_de(n, Taxonomia()), "draft", os.environ.get("GHOST_URL") or V["ghost"]["url"], G.ghost_token(key))
    P.guardar_nota(n)
    try:
        if P.leer_pedido(nid):
            P.guardar_pedido(nid, {"estado": "retirada"})
    except Exception:  # noqa: BLE001
        pass
    print("Retirada (no se borra):", nid)


def lista():
    key = os.environ.get("GHOST_ADMIN_KEY")
    if not key:
        raise SystemExit("Falta GHOST_ADMIN_KEY.")
    base = G.admin_base(os.environ.get("GHOST_URL") or V["ghost"]["url"])
    tok = G.ghost_token(key)
    tag = {"name": "Notas de prensa", "slug": CFG["ghost"]["tag_publica"],
           "description": "Comunicados de empresas e instituciones del transporte, la movilidad y la logística, publicados tal como los envían y marcados como tales. No son contenido editorial de MOTICIAS. Se filtran por modo, tema y comunidad."}
    st, f = G.api("GET", "%s/ghost/api/admin/tags/slug/%s/" % (base, tag["slug"]), tok)
    if st == 200 and f.get("tags"):
        G.api("PUT", "%s/ghost/api/admin/tags/%s/" % (base, f["tags"][0]["id"]), tok, {"tags": [dict(tag, updated_at=f["tags"][0].get("updated_at"))]})
    else:
        G.api("POST", "%s/ghost/api/admin/tags/" % base, tok, {"tags": [tag]})
    print("Etiqueta lista:", tag["slug"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["nueva", "desde-pedido", "publicar", "retirar", "lista"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--organizacion"); ap.add_argument("--web", default=""); ap.add_argument("--grupo", action="store_true")
    ap.add_argument("--embargo"); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.accion == "nueva":
        n = nueva(a.arg, a.organizacion or "", a.web, a.grupo, a.embargo)
        print("Creada %s/%s.json · ejes %s / %s / %s" % (os.path.relpath(P.NOTAS, ROOT), n["id"], n["submodo"], ",".join(n["temas"]), ",".join(n["territorios"])))
    elif a.accion == "desde-pedido":
        n = desde_pedido(a.arg)
        print("Creada %s · emisor %s" % (n["id"], "verificado" if n["verificado_emisor"] else "SIN verificar: no se publica todavía"))
    elif a.accion == "publicar":
        publicar(a.arg, a.dry_run)
    elif a.accion == "retirar":
        retirar(a.arg)
    else:
        lista()


if __name__ == "__main__":
    main()
