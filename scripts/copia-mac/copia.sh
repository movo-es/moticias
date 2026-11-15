#!/bin/bash
# MOTICIAS · Copia de seguridad en el Mac (cambio OpenSpec copia-de-seguridad-mac; «sí» de Rainer del 15-11-2026).
#
# Lo lanza macOS (launchd: ~/Library/LaunchAgents/com.moticias.copia.plist) cada día a las 13:30 y al iniciar sesión;
# si ese día ya hay una copia correcta, no hace nada. Copia tres cosas en ~/Copias/MOTICIAS/AAAA-MM-DD/:
#   1. repo.bundle         el repositorio movo-es/moticias con todas sus ramas e historial (es público: sin cifrar)
#   2. privado.sparseimage imagen de disco CIFRADA (AES-256) con la base privada de Supabase (pg_dump) y lo que solo
#                          está en Ghost (miembros, ajustes, boletines, planes, etiquetas, páginas, posts). Se escribe
#                          directamente dentro de la imagen cifrada: los datos personales nunca tocan el disco en claro.
# Después borra copias viejas (7 diarias, 4 semanales, 12 mensuales), hace la prueba de restauración si toca (primer
# lunes del mes, o si la última correcta tiene más de 35 días) y manda al gestor el registro: fecha, tamaños, huellas y
# recuentos, NUNCA datos.
#
# Claves: todas en el llavero de macOS (servicio «moticias-copia»); este fichero no contiene ninguna.
# Producción no depende de esto: si el Mac no copia, lo único que pasa es que el gestor avisa por correo.
set -uo pipefail

BASE="${MOTICIAS_COPIAS:-$HOME/Copias/MOTICIAS}"
PROG="$BASE/.programa"
HOY="$(date +%Y-%m-%d)"
DIA="$BASE/$HOY"
LOG="$BASE/registro.log"
API="https://app.moticias.com/api/gestor?a=copia"
export PATH="/Applications/Postgres.app/Contents/Versions/latest/bin:/opt/homebrew/opt/libpq/bin:/usr/local/opt/libpq/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
mkdir -p "$BASE"
exec >>"$LOG" 2>&1
echo "=== $(date '+%Y-%m-%d %H:%M:%S') copia ==="

clave() { security find-generic-password -s moticias-copia -a "$1" -w 2>/dev/null; }
INICIO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
EQUIPO="$(scutil --get ComputerName 2>/dev/null || hostname)"
MNT=""

anotar() {  # anotar <clase> <ok:true|false> <partes.json o vacío> <error>
  local tok; tok="$(clave token-registro)"
  [ -z "$tok" ] && { echo "sin token de registro en el llavero: no se anota en el gestor"; return 0; }
  TOK="$tok" CLASE="$1" OK="$2" PARTES="${3:-}" ERR="${4:-}" INI="$INICIO" EQ="$EQUIPO" URL="$API" /usr/bin/python3 -I - <<'PY'
import json, os, urllib.request
partes = {}
if os.environ.get("PARTES") and os.path.exists(os.environ["PARTES"]):
    partes = json.load(open(os.environ["PARTES"]))
cuerpo = {"token": os.environ["TOK"], "clase": os.environ["CLASE"], "ok": os.environ["OK"] == "true", "inicio": os.environ["INI"],
          "equipo": os.environ["EQ"][:80], "partes": partes, "error": (os.environ.get("ERR") or None)}
req = urllib.request.Request(os.environ["URL"], data=json.dumps(cuerpo).encode(), method="POST",
                             headers={"Content-Type": "application/json", "User-Agent": "MOTICIAS-copia-mac/1.0"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("registro en el gestor:", r.status)
except Exception as e:  # sin red no pasa nada: la copia está hecha y el gestor avisará si faltan días
    print("no se pudo anotar en el gestor:", e)
PY
}

fallo() {
  echo "FALLO: $1"
  [ -n "$MNT" ] && hdiutil detach "$MNT" -force >/dev/null 2>&1
  anotar copia false "" "$1"
  /usr/bin/osascript -e "display notification \"$1\" with title \"MOTICIAS · la copia de seguridad ha fallado\"" >/dev/null 2>&1
  exit 1
}

# ¿Ya hay copia correcta hoy? (se lanza también al iniciar sesión)
if [ -f "$DIA/.ok" ] && [ "${1:-}" != "--forzar" ]; then
  echo "hoy ya hay copia correcta"
else
  for c in supabase-url ghost-admin-key cifrado; do [ -n "$(clave $c)" ] || fallo "falta la clave «$c» en el llavero (vuelve a ejecutar instalar.sh)"; done
  command -v pg_dump >/dev/null || fallo "no encuentro pg_dump: instala Postgres.app (https://postgresapp.com/)"
  mkdir -p "$DIA"; rm -f "$DIA/.ok"

  # 1. Repositorio (público): espejo local y bundle con todo el historial
  ESP="$BASE/.espejo.git"
  if [ ! -d "$ESP" ]; then git clone --quiet --mirror https://github.com/movo-es/moticias.git "$ESP" || fallo "no se pudo clonar el repositorio"; fi
  git -C "$ESP" remote update --prune >/dev/null 2>&1 || fallo "no se pudo actualizar el repositorio desde GitHub"
  git -C "$ESP" bundle create "$DIA/repo.bundle" --branches --tags >/dev/null 2>&1 || fallo "no se pudo crear el bundle"
  git bundle verify "$DIA/repo.bundle" >/dev/null 2>&1 || fallo "el bundle no se verifica"
  COMMIT="$(git -C "$ESP" rev-parse refs/heads/main)"

  # 2. Imagen cifrada y, dentro, la base privada y Ghost
  IMG="$DIA/privado.sparseimage"
  rm -f "$IMG"
  printf '%s' "$(clave cifrado)" | hdiutil create -quiet -size 2g -type SPARSE -fs APFS -encryption AES-256 -stdinpass -volname MOTICIAS-privado "$IMG" || fallo "no se pudo crear la imagen cifrada"
  MNT="$(mktemp -d /tmp/moticias-copia.XXXXXX)"
  printf '%s' "$(clave cifrado)" | hdiutil attach -quiet -stdinpass -nobrowse -noautoopen -mountpoint "$MNT" "$IMG" || fallo "no se pudo abrir la imagen cifrada"
  URI="$(clave supabase-url)"
  psql "$URI" -At -F $'\t' -c "select table_name from information_schema.tables where table_schema='public' and table_type='BASE TABLE' order by 1" > "$MNT/tablas.txt" || fallo "no se pudieron listar las tablas"
  : > "$MNT/filas.tsv"
  while read -r t; do printf '%s\t%s\n' "$t" "$(psql "$URI" -At -c "select count(*) from public.\"$t\"")" >> "$MNT/filas.tsv"; done < "$MNT/tablas.txt"
  # Recuentos ANTES del volcado: como en la base no se borra nada, el volcado tiene al menos esas filas (la prueba lo comprueba)
  pg_dump "$URI" --schema=public --format=custom --no-owner --no-privileges --file "$MNT/base.dump" || fallo "pg_dump de la base privada falló"
  GHOST_ADMIN_KEY="$(clave ghost-admin-key)" /usr/bin/python3 -I "$PROG/ghost_exportar.py" "$MNT/ghost" || fallo "la exportación de Ghost falló"
  # Manifiesto dentro de la imagen (lo usa la prueba de restauración) y huellas para el registro (fuera, sin datos)
  COMMIT="$COMMIT" MNT="$MNT" DIA="$DIA" /usr/bin/python3 -I - <<'PY' || fallo "no se pudo escribir el manifiesto"
import hashlib, json, os
m, dia = os.environ["MNT"], os.environ["DIA"]
def h(p):
    s = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            s.update(b)
    return s.hexdigest()
filas = dict(l.rstrip("\n").split("\t") for l in open(os.path.join(m, "filas.tsv")) if "\t" in l)
filas = {k: int(v) for k, v in filas.items()}
gh = json.load(open(os.path.join(m, "ghost", "resumen.json")))
ghost_bytes = sum(os.path.getsize(os.path.join(m, "ghost", f)) for f in os.listdir(os.path.join(m, "ghost")))
man = {"commit": os.environ["COMMIT"], "filas": filas, "ghost": gh, "base_sha256": h(os.path.join(m, "base.dump"))}
json.dump(man, open(os.path.join(m, "manifiesto.json"), "w"), indent=1)
partes = {"repo": {"bytes": os.path.getsize(os.path.join(dia, "repo.bundle")), "sha256": h(os.path.join(dia, "repo.bundle")), "commit": os.environ["COMMIT"]},
          "base": {"bytes": os.path.getsize(os.path.join(m, "base.dump")), "sha256": man["base_sha256"], "tablas": len(filas), "filas": filas},
          "ghost": {"bytes": ghost_bytes, "miembros": gh.get("members"), "posts": gh.get("posts"), "paginas": gh.get("pages")}}
json.dump(partes, open(os.path.join(dia, "partes.json"), "w"), indent=1)
PY
  hdiutil detach "$MNT" -quiet || hdiutil detach "$MNT" -force -quiet
  rmdir "$MNT" 2>/dev/null; MNT=""
  hdiutil compact -quiet "$IMG" -stdinpass <<<"$(clave cifrado)" >/dev/null 2>&1 || true
  /usr/bin/python3 -I - "$DIA/partes.json" "$IMG" <<'PY'
import json, os, sys
p = json.load(open(sys.argv[1])); p["imagen_cifrada_bytes"] = os.path.getsize(sys.argv[2]); json.dump(p, open(sys.argv[1], "w"), indent=1)
PY
  touch "$DIA/.ok"
  echo "copia correcta en $DIA"
  anotar copia true "$DIA/partes.json" ""
fi

# 3. Conservación: 7 diarias, 4 semanales y 12 mensuales. Solo se borra dentro de ~/Copias/MOTICIAS, y solo carpetas con
#    nombre de fecha; nunca nada de producción.
BASE="$BASE" /usr/bin/python3 -I - <<'PY'
import datetime, os, re, shutil
base = os.environ["BASE"]
dias = sorted((d for d in os.listdir(base) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) and os.path.exists(os.path.join(base, d, ".ok"))), reverse=True)
guardar = set(dias[:7])
sem, mes = {}, {}
for d in dias:
    f = datetime.date.fromisoformat(d)
    sem.setdefault(f.isocalendar()[:2], d)
    mes.setdefault((f.year, f.month), d)
guardar |= set(list(sem.values())[:4]) | set(list(mes.values())[:12])
for d in os.listdir(base):
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) and d not in guardar:
        if os.path.exists(os.path.join(base, d, ".ok")) or d < (datetime.date.today() - datetime.timedelta(days=3)).isoformat():
            shutil.rmtree(os.path.join(base, d)); print("copia antigua retirada:", d)
PY

# 4. Prueba de restauración si toca (primer lunes del mes o más de 35 días desde la última correcta)
ULT="$BASE/.ultima-prueba"
TOCA=0
if [ "$(date +%u)" = 1 ] && [ "$(date +%d)" -le 7 ] && [ "$(cat "$ULT" 2>/dev/null)" != "$HOY" ]; then TOCA=1; fi
if [ ! -f "$ULT" ] || [ $(( ( $(date +%s) - $(date -j -f %Y-%m-%d "$(cat "$ULT")" +%s 2>/dev/null || echo 0) ) / 86400 )) -gt 35 ]; then TOCA=1; fi
if [ "$TOCA" = 1 ] && [ -f "$DIA/.ok" ]; then /bin/bash "$PROG/restaurar-prueba.sh" "$DIA"; fi

# 5. Recordatorio del tema de Ghost (hasta que esté versionado en el repositorio)
TEMA="$BASE/tema"
mkdir -p "$TEMA"
if [ -z "$(find "$TEMA" -name '*.zip' -mtime -31 2>/dev/null | head -1)" ]; then
  /usr/bin/osascript -e 'display notification "Ghost → Settings → Design → Change theme → Advanced → Download, y guarda el .zip en ~/Copias/MOTICIAS/tema/" with title "MOTICIAS · toca descargar el tema de Ghost"' >/dev/null 2>&1
fi
echo "=== fin $(date '+%H:%M:%S') ==="
