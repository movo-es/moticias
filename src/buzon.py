#!/usr/bin/env python3
"""MOTICIAS · Buzón del repositorio (migración 008, 14-11-2026), para las tareas programadas que no pueden hacer `push`.

  python3 -I src/buzon.py preparar --origen batida [--lote AAAAMMDD-HHMM-batida] [--desde origin/main]

Toma los commits de `--desde..HEAD` y escribe en work/buzon/ los `insert` de la tabla `repo_buzon`, uno por parte
(350 KB como mucho cada uno). Se ejecutan en orden con `execute_sql` del conector de Supabase (proyecto «moticias»,
`cjrntzaqmvhgscdgiehs`). El cron `aplicar_buzon` del gestor (Vercel, con su GITHUB_TOKEN) sube el lote a `main` en un
solo commit en menos de 10 minutos, y `ghost_al_dia` lo publica en moticias.com en los 15 siguientes.

Solo contenido: data/, docs/ediciones.md, docs/fuentes.md, docs/asesor/ y portal/img/. hemeroteca/data/ y
app/public/buscador/index.json se regeneran y no entran. El código y la configuración no van por el buzón. Nada se borra.
Cada fichero lleva `base`, el blob que había en `--desde`: si `main` lo ha cambiado desde entonces, el lote queda en
`error` y no se pisa nada. Comprobación, con el mismo conector:
  select lote, parte, partes, estado, sha, error from repo_buzon order by creado_at desc limit 10;
"""
import argparse, base64, datetime, json, os, secrets, subprocess, sys, zoneinfo

RUTAS = ("data/", "docs/ediciones.md", "docs/fuentes.md", "docs/asesor/", "portal/img/")
REGENERABLES = ("hemeroteca/data/", "app/public/buscador/index.json")
MAX = 350_000


def git(*args, binario=False):
    r = subprocess.run(["git", *args], capture_output=True)
    if r.returncode:
        sys.exit("git %s: %s" % (" ".join(args), r.stderr.decode("utf-8", "replace").strip()))
    return r.stdout if binario else r.stdout.decode("utf-8")


def literal(s):
    return "'" + str(s).replace("'", "''") + "'"


def preparar(a):
    lineas = [l.split("\t") for l in git("diff", "--name-status", "--no-renames", a.desde, "HEAD").splitlines() if l.strip()]
    if not lineas:
        print("Nada que enviar: HEAD no cambia nada respecto de %s." % a.desde)
        return
    ficheros, prohibidos = [], []
    for estado, ruta in ((l[0], l[-1]) for l in lineas):
        if ruta.startswith(REGENERABLES):
            continue
        if estado.startswith("D"):
            sys.exit("El buzón no borra ficheros (%s): en MOTICIAS nada se borra." % ruta)
        if not ruta.startswith(RUTAS):
            prohibidos.append(ruta)
            continue
        datos = git("show", "HEAD:" + ruta, binario=True)
        base = subprocess.run(["git", "rev-parse", "--verify", "-q", "%s:%s" % (a.desde, ruta)],
                              capture_output=True).stdout.decode().strip() or None
        try:
            ficheros.append({"ruta": ruta, "base": base, "texto": datos.decode("utf-8")})
        except UnicodeDecodeError:
            ficheros.append({"ruta": ruta, "base": base, "base64": base64.b64encode(datos).decode("ascii")})
    if prohibidos:
        sys.exit("Estos ficheros no pueden ir por el buzón (código o configuración: necesitan un push de verdad): "
                 + ", ".join(prohibidos))
    if not ficheros:
        print("Nada que enviar: solo cambian datos regenerables.")
        return
    mensaje = git("log", "--reverse", "--format=%B", "%s..HEAD" % a.desde).strip()
    autor, correo = git("log", "-1", "--format=%an%n%ae").splitlines()[:2]
    lote = a.lote or datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Madrid")).strftime("%Y%m%d-%H%M-") + a.origen
    partes, actual, tam = [], [], 0
    for f in ficheros:
        t = len(json.dumps(f, ensure_ascii=False))
        if actual and tam + t > MAX:
            partes.append(actual)
            actual, tam = [], 0
        actual.append(f)
        tam += t
    if actual:
        partes.append(actual)
    os.makedirs(a.salida, exist_ok=True)
    rutas = []
    for i, p in enumerate(partes, 1):
        js = json.dumps(p, ensure_ascii=False)
        tag = "$b%s$" % secrets.token_hex(4)
        while tag in js or tag in mensaje:
            tag = "$b%s$" % secrets.token_hex(4)
        sql = ("insert into repo_buzon (lote, parte, partes, origen, mensaje, autor, autor_correo, ficheros) values "
               "(%s, %d, %d, %s, %s%s%s, %s, %s, %s%s%s::jsonb) on conflict (lote, parte) do nothing;\n") % (
            literal(lote), i, len(partes), literal(a.origen), tag, mensaje, tag, literal(autor), literal(correo), tag, js, tag)
        ruta = os.path.join(a.salida, "%s-%02d.sql" % (lote, i))
        with open(ruta, "w", encoding="utf-8") as fh:
            fh.write(sql)
        rutas.append((ruta, len(sql.encode("utf-8")), len(p)))
    print("Lote %s: %d ficheros en %d parte(s). Ejecuta cada fichero, en orden, con execute_sql (proyecto cjrntzaqmvhgscdgiehs):"
          % (lote, len(ficheros), len(partes)))
    for ruta, b, n in rutas:
        print("  %s  (%d ficheros, %d bytes)" % (ruta, n, b))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    p = sub.add_parser("preparar")
    p.add_argument("--origen", required=True, help="edicion-diaria, batida, retoques, asesor…")
    p.add_argument("--lote", help="AAAAMMDD-HHMM-origen (por defecto, la hora de Madrid de ahora)")
    p.add_argument("--desde", default="origin/main")
    p.add_argument("--salida", default="work/buzon")
    a = ap.parse_args()
    preparar(a)
