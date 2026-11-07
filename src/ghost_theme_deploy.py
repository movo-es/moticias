#!/usr/bin/env python3
"""MOTICIAS · Empaqueta y sube el tema de Ghost (ghost-theme/) y las rutas (ghost/routes.yaml).

  python3 -I src/ghost_theme_deploy.py --zip                 solo crea work/moticias.zip
  python3 -I src/ghost_theme_deploy.py --upload              sube el tema SIN activarlo
  python3 -I src/ghost_theme_deploy.py --upload --activate   sube y activa
  python3 -I src/ghost_theme_deploy.py --routes              sube ghost/routes.yaml
  python3 -I src/ghost_theme_deploy.py --redirects           sube ghost/redirects.yaml

Variables de entorno: GHOST_URL y GHOST_ADMIN_KEY (nunca en el repositorio). Rutas y redirecciones necesitan además
GHOST_STAFF_TOKEN (token de acceso de un usuario administrador): Ghost no deja subirlas a una integración. En GitHub, la Action
.github/workflows/tema-ghost.yml hace lo mismo con los secretos del repositorio.
"""
import argparse, json, os, sys, uuid, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from ghost_publish import Ghost  # noqa: E402


def make_zip():
    out = os.path.join(ROOT, "work", "moticias.zip")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    src = os.path.join(ROOT, "ghost-theme")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for d, _, files in os.walk(src):
            for f in files:
                if f.startswith(".") or f == "node_modules":
                    continue
                p = os.path.join(d, f)
                z.write(p, os.path.join("moticias", os.path.relpath(p, src)))
    return out


def multipart(field, path, ctype, extra=None):
    bnd = uuid.uuid4().hex
    body = b""
    for k, v in (extra or {}).items():
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (bnd, k, v)).encode()
    body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\nContent-Type: %s\r\n\r\n" % (bnd, field, os.path.basename(path), ctype)).encode()
    body += open(path, "rb").read() + ("\r\n--%s--\r\n" % bnd).encode()
    return body, "multipart/form-data; boundary=" + bnd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", action="store_true")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--activate", action="store_true")
    ap.add_argument("--routes", action="store_true")
    ap.add_argument("--redirects", action="store_true")
    a = ap.parse_args()
    z = make_zip()
    rep = {"zip": os.path.relpath(z, ROOT)}
    if a.upload or a.routes or a.redirects or a.activate:
        key = os.environ.get("GHOST_ADMIN_KEY")
        if not key or ":" not in key:
            sys.exit("Falta GHOST_ADMIN_KEY")
        g = Ghost(os.environ["GHOST_URL"], key)
        staff = os.environ.get("GHOST_STAFF_TOKEN")
        gs = Ghost(os.environ["GHOST_URL"], staff) if staff and ":" in staff else g  # rutas y redirecciones
        if a.upload:
            body, ct = multipart("file", z, "application/zip")
            st, r = g.call("POST", "/themes/upload/", raw=body, ctype=ct)
            rep["tema"] = (st, (r.get("themes") or [{}])[0].get("name") if st in (200, 201) else r)
        if a.activate:
            st, r = g.call("PUT", "/themes/moticias/activate/")
            rep["activado"] = (st, "ok" if st == 200 else r)
        if a.routes:
            body, ct = multipart("routes", os.path.join(ROOT, "ghost", "routes.yaml"), "application/x-yaml")
            st, r = gs.call("POST", "/settings/routes/yaml/", raw=body, ctype=ct)
            rep["rutas"] = (st, "ok" if st == 200 else r)
        if a.redirects:
            body, ct = multipart("redirects", os.path.join(ROOT, "ghost", "redirects.yaml"), "application/x-yaml")
            st, r = gs.call("POST", "/redirects/upload/", raw=body, ctype=ct)
            rep["redirecciones"] = (st, "ok" if st == 200 else r)
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
