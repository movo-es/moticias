#!/usr/bin/env python3
"""MOTICIAS · Exporta lo que solo está en Ghost a una carpeta (para la copia de seguridad del Mac). Solo biblioteca estándar
y compatible con el python3 que trae macOS (3.9).

  GHOST_ADMIN_KEY=id:secret python3 -I ghost_exportar.py <carpeta>

Escribe un JSON por colección (members, settings, newsletters, tiers, labels, tags, pages, posts) y `resumen.json` con los
recuentos. La carpeta tiene que estar DENTRO de la imagen cifrada: los miembros son datos personales. El tema y la
exportación completa de la base de Ghost no se pueden sacar con una clave de integración (Ghost responde 403): el tema se
descarga a mano desde el panel hasta que esté versionado en el repositorio (`publicar-en-ghost-v1`).
"""
import base64, hashlib, hmac, json, os, sys, time, urllib.request

URL = os.environ.get("GHOST_URL", "https://moticias.ghost.io").rstrip("/")
COLECCIONES = [  # (nombre, ruta, parámetros)
    ("members", "members/", "limit=all&include=labels,newsletters"),
    ("settings", "settings/", ""),
    ("newsletters", "newsletters/", "limit=all"),
    ("tiers", "tiers/", "limit=all&include=monthly_price,yearly_price,benefits"),
    ("labels", "labels/", "limit=all"),
    ("tags", "tags/", "limit=all"),
    ("pages", "pages/", "limit=all&formats=html,lexical&include=tags,authors"),
    ("posts", "posts/", "limit=all&formats=html,lexical&include=tags,authors&filter=status:[published,draft,scheduled]"),
]


def b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def token(clave):
    kid, sec = clave.split(":")
    ahora = int(time.time())
    ini = b64(json.dumps({"alg": "HS256", "typ": "JWT", "kid": kid}).encode()) + "." + b64(json.dumps({"iat": ahora, "exp": ahora + 300, "aud": "/admin/"}).encode())
    return ini + "." + b64(hmac.new(bytes.fromhex(sec), ini.encode(), hashlib.sha256).digest())


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    clave = os.environ.get("GHOST_ADMIN_KEY") or ""
    if ":" not in clave:
        sys.exit("Falta GHOST_ADMIN_KEY (id:secret)")
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    resumen = {}
    for nombre, ruta, q in COLECCIONES:
        req = urllib.request.Request("%s/ghost/api/admin/%s%s" % (URL, ruta, ("?" + q) if q else ""),
                                     headers={"Authorization": "Ghost " + token(clave), "Accept-Version": "v5.0", "User-Agent": "MOTICIAS-copia-mac/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            datos = json.loads(r.read())
        with open(os.path.join(out, nombre + ".json"), "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False)
        resumen[nombre] = len(datos.get(nombre) or [])
    resumen["exportado"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with open(os.path.join(out, "resumen.json"), "w") as f:
        json.dump(resumen, f, indent=1)
    print(json.dumps({k: v for k, v in resumen.items() if k != "exportado"}))


if __name__ == "__main__":
    main()
