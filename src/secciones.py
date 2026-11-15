#!/usr/bin/env python3
"""MOTICIAS · ¿Tienen las secciones de moticias.com lo que cabe esperar? Solo biblioteca estándar.

Decisión de Rainer (15-11-2026): tras cada actualización y cada barrido programado se comprueba que cada página de sección
(Tierra, Mar, Aire, Logística, Regulación, Licitaciones, Análisis) enseña las piezas que le tocan. Las reglas de cada
sección están en `verticals/<id>.json → secciones_web` (las mismas que usa app/public/sitio/m.js para pintarlas).

Qué compara:
  1. lo esperado: las piezas publicadas de `data/articles/` que caen en cada sección (con el mismo índice que genera
     src/export_search_index.py);
  2. lo servido: el índice que la web usa de verdad (https://app.moticias.com/buscador/index.json);
  3. Ghost: que cada pieza esperada esté publicada en moticias.com (Content API, clave pública).
Problemas (avisan): una pieza publicada que falta en el índice servido (la sección no la enseña), una pieza del índice que
no está publicada en Ghost (enlace roto), una sección vacía. Nota (no avisa): una sección sin piezas nuevas en N días.
Con --navegador abre además cada sección en Chromium (Playwright de Node, si está) y cuenta las piezas pintadas.

Uso:
  python3 -I src/secciones.py comprobar [--navegador] [--json]
Sale con código 1 si hay problemas.
"""
import datetime, json, os, shutil, subprocess, sys, tempfile, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
UA = "MOTICIAS-comprobador-secciones/1.0 (+https://www.moticias.com/como-trabajamos/)"
INDICE_WEB = "https://app.moticias.com/buscador/index.json"


def vertical(vid="movilidad"):
    return json.load(open(os.path.join(ROOT, "verticals", vid + ".json"), encoding="utf-8"))


def reglas(v):
    return {k: r for k, r in (v.get("secciones_web") or {}).items() if isinstance(r, dict)}


MERCANCIAS = set()


def pertenece(p, r):
    if r.get("modo") and p.get("m") != r["modo"]:
        return False
    if r.get("medio") and (p.get("md") or p.get("m")) != r["medio"]:
        return False
    if r.get("mercancias") and not (p.get("m") == "logistica" or set(p.get("mo") or []) & MERCANCIAS):
        return False
    if r.get("kind") and p.get("kind") != r["kind"]:
        return False
    if r.get("tema") and r["tema"] not in (p.get("te") or []):
        return False
    if r.get("tipo") and p.get("tc") != r["tipo"]:
        return False
    return True


def reparto(indice, rs):
    MERCANCIAS.update(indice.get("mercancias") or [])
    return {s: [p for p in indice.get("piezas", []) if pertenece(p, r)] for s, r in rs.items()}


def _get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Version": "v5.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def publicadas_en_ghost(v):
    g = v.get("ghost") or {}
    slugs, page = set(), 1
    while True:
        q = urllib.parse.urlencode({"key": g["content_key"], "limit": 100, "page": page, "fields": "slug"})
        d = _get_json((g.get("admin_url") or g.get("url")).rstrip("/") + "/ghost/api/content/posts/?" + q)
        slugs |= {p["slug"] for p in d.get("posts", [])}
        if not d.get("meta", {}).get("pagination", {}).get("next"):
            return slugs
        page += 1


def comprobar(esperado_ix, servido_ix, en_ghost, v, hoy=None):
    """Devuelve {"problemas": [...], "notas": [...], "secciones": {sec: {esperadas, servidas, ultima}}}."""
    rs = reglas(v)
    hoy = hoy or datetime.date.today().isoformat()
    esp, ser = reparto(esperado_ix, rs), reparto(servido_ix or {"piezas": []}, rs)
    problemas, notas, resumen = [], [], {}
    dias = int((v.get("secciones_web") or {}).get("aviso_dias_sin_novedad") or 14)
    for s in rs:
        ids_esp, ids_ser = {p["id"] for p in esp[s]}, {p["id"] for p in ser[s]}
        faltan = sorted(ids_esp - ids_ser)
        ultima = max((p.get("d") or "" for p in esp[s]), default="")
        resumen[s] = {"esperadas": len(ids_esp), "servidas": len(ids_ser), "ultima": ultima}
        if not ids_ser:
            problemas.append("La sección «%s» sale vacía (esperadas: %d)." % (s, len(ids_esp)))
        elif faltan:
            problemas.append("La sección «%s» no enseña %d pieza(s) publicada(s): %s." % (s, len(faltan), ", ".join(faltan[:5]) + ("…" if len(faltan) > 5 else "")))
        if ultima and (datetime.date.fromisoformat(hoy) - datetime.date.fromisoformat(ultima)).days > dias:
            notas.append("La sección «%s» no tiene piezas nuevas desde el %s." % (s, ultima))
    if en_ghost is not None:
        rotas = sorted({p["id"] for p in (servido_ix or {}).get("piezas", [])} - en_ghost)
        if rotas:
            problemas.append("%d pieza(s) del índice no están publicadas en moticias.com (enlace roto en su sección): %s." % (
                len(rotas), ", ".join(rotas[:5]) + ("…" if len(rotas) > 5 else "")))
    return {"problemas": problemas, "notas": notas, "secciones": resumen}


def navegador(rs, base="https://www.moticias.com"):
    """Cuenta las piezas pintadas en cada sección con Chromium (Playwright de Node). None si no hay Node/Playwright."""
    if not shutil.which("node"):
        return None
    js = """const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const o={};
for(const s of %s){const p=await b.newPage();try{await p.goto('%s/'+s+'/',{waitUntil:'load',timeout:45000});
await p.waitForSelector('.mtx-sec li, main p.empty',{timeout:15000}).catch(()=>{});await p.waitForTimeout(1500);
o[s]=await p.evaluate(()=>document.querySelectorAll('.mtx-sec li').length);}catch(e){o[s]=-1}await p.close()}
console.log(JSON.stringify(o));await b.close()})();""" % (json.dumps(list(rs)), base)
    d = tempfile.mkdtemp()
    try:
        f = os.path.join(d, "s.js")
        open(f, "w").write(js)
        r = subprocess.run(["node", f], capture_output=True, text=True, timeout=300, cwd=d)
        return json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 and r.stdout.strip() else None
    except Exception:
        return None
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    if len(sys.argv) < 2 or sys.argv[1] != "comprobar":
        sys.exit(__doc__)
    import export_search_index as X
    v = vertical()
    esperado = X.construir()
    try:
        servido = _get_json(INDICE_WEB)
    except Exception as e:
        servido = None
        print("No se pudo leer el índice servido (%s): se compara solo con Ghost." % e)
    try:
        en_ghost = publicadas_en_ghost(v)
    except Exception as e:
        en_ghost = None
        print("No se pudo leer Ghost (%s)." % e)
    res = comprobar(esperado, servido, en_ghost, v)
    if "--navegador" in sys.argv:
        pint = navegador(reglas(v))
        if pint is not None:
            for s, n in pint.items():
                res["secciones"][s]["pintadas"] = n
                if n >= 0 and n < min(20, res["secciones"][s]["servidas"]):
                    res["problemas"].append("La sección «%s» pinta %d pieza(s) en el navegador; deberían verse %d." % (s, n, min(20, res["secciones"][s]["servidas"])))
    if "--json" in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        for s, x in res["secciones"].items():
            print("%-13s esperadas %3d · en la web %3d%s · última %s" % (s, x["esperadas"], x["servidas"],
                  (" · pintadas %d" % x["pintadas"]) if "pintadas" in x else "", x["ultima"] or "—"))
        for p in res["problemas"]:
            print("PROBLEMA:", p)
        for n in res["notas"]:
            print("Nota:", n)
        if not res["problemas"]:
            print("Secciones: todo en orden.")
    sys.exit(1 if res["problemas"] else 0)


if __name__ == "__main__":
    main()
