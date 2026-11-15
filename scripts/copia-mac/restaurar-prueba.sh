#!/bin/bash
# MOTICIAS · Prueba de restauración de una copia del Mac (cambio copia-de-seguridad-mac). Una copia que no se ha probado a
# restaurar no cuenta. Lo llama copia.sh el primer lunes de cada mes (o si la última prueba correcta tiene más de 35 días);
# se puede lanzar a mano:  bash ~/Copias/MOTICIAS/.programa/restaurar-prueba.sh [~/Copias/MOTICIAS/AAAA-MM-DD]
#
# Comprueba, en una carpeta temporal que borra al terminar:
#   1. el bundle se clona y su rama main apunta al commit anotado;
#   2. la imagen cifrada se abre con la frase del llavero; la base se restaura en un PostgreSQL LOCAL (Postgres.app) y cada
#      tabla tiene al menos las filas contadas al hacer la copia;
#   3. los JSON de Ghost se leen y tienen los miembros, posts y páginas anotados.
# El resultado (sin datos) va al gestor como «prueba». La base de prueba local se borra al terminar.
set -uo pipefail
BASE="${MOTICIAS_COPIAS:-$HOME/Copias/MOTICIAS}"
export PATH="/Applications/Postgres.app/Contents/Versions/latest/bin:/opt/homebrew/opt/libpq/bin:/usr/local/opt/libpq/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
DIA="${1:-$(ls -d "$BASE"/20??-??-?? 2>/dev/null | sort | tail -1)}"
echo "=== $(date '+%Y-%m-%d %H:%M:%S') prueba de restauración de $DIA ==="
clave() { security find-generic-password -s moticias-copia -a "$1" -w 2>/dev/null; }
INICIO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
TMP="$(mktemp -d /tmp/moticias-prueba.XXXXXX)"
MNT="$TMP/img"; mkdir -p "$MNT"
BD="moticias_prueba_$(date +%Y%m%d%H%M)"

terminar() {  # terminar <ok:true|false> <error>
  hdiutil detach "$MNT" -force -quiet >/dev/null 2>&1
  dropdb -h localhost --if-exists "$BD" >/dev/null 2>&1
  rm -rf "$TMP"
  local tok; tok="$(clave token-registro)"
  if [ -n "$tok" ]; then
    TOK="$tok" OK="$1" ERR="${2:-}" INI="$INICIO" DIA="$DIA" /usr/bin/python3 -I - <<'PY'
import json, os, urllib.request, subprocess
eq = subprocess.run(["scutil", "--get", "ComputerName"], capture_output=True, text=True).stdout.strip()
partes = {"copia": os.path.basename(os.environ["DIA"])}
c = {"token": os.environ["TOK"], "clase": "prueba", "ok": os.environ["OK"] == "true", "inicio": os.environ["INI"], "equipo": eq[:80],
     "partes": partes, "error": os.environ.get("ERR") or None}
try:
    urllib.request.urlopen(urllib.request.Request("https://app.moticias.com/api/gestor?a=copia", data=json.dumps(c).encode(), method="POST",
                           headers={"Content-Type": "application/json", "User-Agent": "MOTICIAS-copia-mac/1.0"}), timeout=30)
except Exception as e:
    print("no se pudo anotar en el gestor:", e)
PY
  fi
  if [ "$1" = true ]; then
    date +%Y-%m-%d > "$BASE/.ultima-prueba"; echo "PRUEBA CORRECTA"
  else
    echo "PRUEBA FALLIDA: $2"
    /usr/bin/osascript -e "display notification \"$2\" with title \"MOTICIAS · la prueba de restauración ha fallado\"" >/dev/null 2>&1
  fi
  exit 0
}

[ -f "$DIA/.ok" ] || terminar false "no hay copia correcta que probar en $DIA"
COMMIT="$(/usr/bin/python3 -I -c 'import json,sys;print(json.load(open(sys.argv[1]))["repo"]["commit"])' "$DIA/partes.json")"

# 1. Repositorio
git clone --quiet "$DIA/repo.bundle" "$TMP/repo" 2>/dev/null || terminar false "el bundle no se puede clonar"
[ "$(git -C "$TMP/repo" rev-parse refs/remotes/origin/main 2>/dev/null)" = "$COMMIT" ] || terminar false "el bundle no tiene main en el commit anotado"

# 2. Imagen cifrada y base privada
printf '%s' "$(clave cifrado)" | hdiutil attach -quiet -readonly -stdinpass -nobrowse -noautoopen -mountpoint "$MNT" "$DIA/privado.sparseimage" || terminar false "la imagen cifrada no se abre con la frase del llavero"
if ! pg_isready -q -h localhost; then open -a Postgres >/dev/null 2>&1; for i in $(seq 1 30); do pg_isready -q -h localhost && break; sleep 1; done; fi
pg_isready -q -h localhost || terminar false "Postgres.app no está en marcha: ábrelo una vez y marca «Iniciar al arrancar»"
createdb -h localhost "$BD" || terminar false "no se pudo crear la base local de prueba"
# Los roles y funciones propios de Supabase (anon, privado.gestor_ok…) no existen en local: sus políticas y permisos dan
# avisos que no afectan a los datos. Lo que cuenta es que estén todas las tablas con sus filas.
pg_restore -h localhost -d "$BD" --no-owner --no-privileges "$MNT/base.dump" >"$TMP/restore.log" 2>&1
RES="$(MNT="$MNT" BD="$BD" /usr/bin/python3 -I - <<'PY'
import json, os, subprocess
man = json.load(open(os.path.join(os.environ["MNT"], "manifiesto.json")))
mal = []
for t, n in man["filas"].items():
    r = subprocess.run(["psql", "-h", "localhost", "-d", os.environ["BD"], "-At", "-c", 'select count(*) from public."%s"' % t], capture_output=True, text=True)
    if r.returncode != 0 or int(r.stdout.strip() or -1) < n:
        mal.append("%s (%s de %s)" % (t, r.stdout.strip() or "no está", n))
gdir = os.path.join(os.environ["MNT"], "ghost")
for k in ("members", "posts", "pages"):
    try:
        if len(json.load(open(os.path.join(gdir, k + ".json")))[k]) != man["ghost"][k]:
            mal.append("Ghost %s incompleto" % k)
    except Exception:
        mal.append("Ghost %s ilegible" % k)
print("; ".join(mal)[:500])
PY
)"
[ -z "$RES" ] || terminar false "$RES"
terminar true ""
