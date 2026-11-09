#!/usr/bin/env python3
"""MOTICIAS · Tema de moticias.com en Ghost: descargar, versionar, cambiar un texto y subir. Solo biblioteca estándar.

El tema vive en `ghost/theme/` (fuente de verdad); nunca se edita en el panel de Ghost. Necesita en el entorno
GHOST_ADMIN_KEY (y GHOST_URL, por defecto https://www.moticias.com). La clave nunca se escribe en el repositorio.

Uso:
  python3 -I src/ghost_theme.py estado                       # tema activo y temas instalados
  python3 -I src/ghost_theme.py descargar                    # baja el tema activo a ghost/theme/ (descomprimido)
  python3 -I src/ghost_theme.py buscar "Dirección editorial"  # dónde aparece un texto en ghost/theme/
  python3 -I src/ghost_theme.py reemplazar "ANTES" "DESPUÉS"  # cambia el texto en ghost/theme/ (exige coincidencia exacta)
  python3 -I src/ghost_theme.py subir [--activar]             # comprime ghost/theme/ y lo sube (mismo nombre: sustituye)
"""
import argparse, io, json, os, sys, urllib.error, urllib.request, uuid, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import ghost_publish as G  # noqa: E402

DIR = os.path.join(ROOT, "ghost", "theme")
TEXTO = (".hbs", ".html", ".css", ".js", ".json", ".txt", ".md", ".svg")


def _cred():
    key = os.environ.get("GHOST_ADMIN_KEY")
    if not key:
        sys.exit("Falta GHOST_ADMIN_KEY en el entorno: no se puede leer ni cambiar el tema.")
    base = (os.environ.get("GHOST_URL") or "https://www.moticias.com").rstrip("/")
    return G.admin_base(base), key


def _get(url, key, binario=False):
    req = urllib.request.Request(url, headers={"Authorization": "Ghost " + G.ghost_token(key), "Accept-Version": "v5.0", "User-Agent": G.UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read()
    return raw if binario else json.loads(raw)


def activo(adm, key):
    temas = _get(adm + "/ghost/api/admin/themes/", key).get("themes", [])
    act = next((t for t in temas if t.get("active")), None)
    return act, temas


def descargar(adm, key):
    act, _ = activo(adm, key)
    if not act:
        sys.exit("Ghost no informa de un tema activo.")
    raw = _get(adm + "/ghost/api/admin/themes/%s/download/" % act["name"], key, binario=True)
    z = zipfile.ZipFile(io.BytesIO(raw))
    # El zip de Ghost puede traer una carpeta raíz; se quita para que ghost/theme/ sea el tema.
    nombres = [n for n in z.namelist() if not n.endswith("/")]
    raiz = os.path.commonprefix(nombres)
    raiz = raiz[: raiz.rfind("/") + 1] if "/" in raiz else ""
    os.makedirs(DIR, exist_ok=True)
    for n in nombres:
        rel = n[len(raiz):]
        if not rel or rel.startswith("..") or os.path.isabs(rel):
            continue
        dest = os.path.join(DIR, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(z.read(n))
    json.dump({"name": act["name"], "package": act.get("package", {}), "descargado": True}, open(os.path.join(ROOT, "ghost", "theme.json"), "w"), ensure_ascii=False, indent=1)
    return act["name"], len(nombres)


def ficheros():
    for d, _, fs in os.walk(DIR):
        for f in fs:
            if f.endswith(TEXTO):
                yield os.path.join(d, f)


def buscar(texto):
    out = []
    for p in ficheros():
        for i, linea in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
            if texto in linea:
                out.append((os.path.relpath(p, ROOT), i, linea.strip()[:200]))
    return out


def reemplazar(antes, despues):
    n = 0
    for p in ficheros():
        s = open(p, encoding="utf-8").read()
        if antes in s:
            open(p, "w", encoding="utf-8").write(s.replace(antes, despues))
            n += s.count(antes)
    return n


def subir(adm, key, activar):
    meta = json.load(open(os.path.join(ROOT, "ghost", "theme.json")))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for d, _, fs in os.walk(DIR):
            for f in fs:
                p = os.path.join(d, f)
                z.write(p, os.path.relpath(p, DIR))
    limite = "----moticias" + uuid.uuid4().hex
    cuerpo = (("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s.zip\"\r\nContent-Type: application/zip\r\n\r\n" % (limite, meta["name"])).encode()
              + buf.getvalue() + ("\r\n--%s--\r\n" % limite).encode())
    req = urllib.request.Request(adm + "/ghost/api/admin/themes/upload/", data=cuerpo, method="POST", headers={
        "Authorization": "Ghost " + G.ghost_token(key), "Accept-Version": "v5.0", "User-Agent": G.UA,
        "Content-Type": "multipart/form-data; boundary=" + limite})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            res = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit("Ghost rechazó el tema: HTTP %s %s" % (e.code, e.read().decode("utf-8", "replace")[:400]))
    nombre = res["themes"][0]["name"]
    if activar:
        st, _ = G.api("PUT", adm + "/ghost/api/admin/themes/%s/activate/" % nombre, G.ghost_token(key))
        if st >= 300:
            sys.exit("Subido, pero no se pudo activar (HTTP %s)." % st)
    return nombre


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["estado", "descargar", "buscar", "reemplazar", "subir"])
    ap.add_argument("textos", nargs="*")
    ap.add_argument("--activar", action="store_true")
    a = ap.parse_args()
    if a.accion == "buscar":
        for r in buscar(a.textos[0]):
            print("%s:%d  %s" % r)
        return
    if a.accion == "reemplazar":
        n = reemplazar(a.textos[0], a.textos[1])
        print("%d sustituciones" % n)
        sys.exit(0 if n else 1)
    adm, key = _cred()
    if a.accion == "estado":
        act, temas = activo(adm, key)
        print("Activo:", act and act["name"], "· instalados:", ", ".join(t["name"] for t in temas))
    elif a.accion == "descargar":
        print("Descargado %s (%d ficheros) en ghost/theme/" % descargar(adm, key))
    elif a.accion == "subir":
        print("Subido", subir(adm, key, a.activar))


if __name__ == "__main__":
    main()
