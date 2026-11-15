#!/bin/bash
# MOTICIAS · Instala la copia de seguridad diaria en el Mac (cambio copia-de-seguridad-mac). Se ejecuta UNA vez, en el Terminal
# del Mac, y se puede repetir sin daño (no pisa las claves que ya estén en el llavero).
#
#   curl -fsSL https://raw.githubusercontent.com/movo-es/moticias/main/scripts/copia-mac/instalar.sh -o /tmp/moticias-instalar.sh && bash /tmp/moticias-instalar.sh
#
# Qué hace: comprueba lo que hace falta (Git, Python y Postgres.app), copia los guiones a ~/Copias/MOTICIAS/.programa/,
# guarda las claves en el llavero de macOS (nunca en ficheros), te deja en el portapapeles las dos líneas que activan el
# acceso de solo lectura en Supabase, programa la copia diaria a las 13:30 con launchd y hace la primera copia y la primera
# prueba de restauración. Ninguna clave sale del Mac salvo la contraseña del usuario de solo lectura, que pegas tú en el
# editor SQL de Supabase.
set -uo pipefail
RAW="https://raw.githubusercontent.com/movo-es/moticias/main/scripts/copia-mac"
BASE="$HOME/Copias/MOTICIAS"; PROG="$BASE/.programa"
REF="cjrntzaqmvhgscdgiehs"
export PATH="/Applications/Postgres.app/Contents/Versions/latest/bin:/opt/homebrew/opt/libpq/bin:/usr/local/opt/libpq/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
paso() { printf '\n\033[1m%s\033[0m\n' "$1"; }
alto() { printf '\n\033[31m%s\033[0m\n' "$1"; exit 1; }
clave() { security find-generic-password -s moticias-copia -a "$1" -w 2>/dev/null; }
guardar() { security add-generic-password -U -s moticias-copia -a "$1" -w "$2" -T /usr/bin/security >/dev/null; }

paso "1/6 · Comprobando lo que hace falta"
[ "$(uname)" = Darwin ] || alto "Esto es para el Mac."
xcode-select -p >/dev/null 2>&1 || { xcode-select --install >/dev/null 2>&1; alto "Falta Git: se ha abierto la instalación de las «herramientas de línea de comandos». Acéptala, espera a que termine y vuelve a pegar el comando."; }
/usr/bin/python3 -c 'import sys; assert sys.version_info >= (3, 8)' 2>/dev/null || alto "Falta Python 3 (viene con las herramientas de línea de comandos de Apple)."
if ! command -v pg_dump >/dev/null || [ "$(pg_dump --version | sed -E 's/[^0-9]*([0-9]+).*/\1/')" -lt 17 ]; then
  open "https://postgresapp.com/downloads.html"
  alto "Falta Postgres.app (versión 17 o posterior). Se ha abierto su página: descárgalo, arrástralo a Aplicaciones, ábrelo una vez, pulsa «Initialize» y marca que se inicie al arrancar. Después vuelve a pegar el comando."
fi
echo "Git, Python y PostgreSQL $(pg_dump --version | sed -E 's/[^0-9]*([0-9.]+).*/\1/'): bien."

paso "2/6 · Guiones en $PROG"
mkdir -p "$PROG" "$BASE/tema"
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in copia.sh restaurar-prueba.sh ghost_exportar.py; do
  if [ -f "$AQUI/$f" ]; then cp "$AQUI/$f" "$PROG/$f"; else curl -fsSL "$RAW/$f" -o "$PROG/$f" || alto "No se pudo descargar $f"; fi
done
chmod 700 "$BASE" "$PROG"; chmod 600 "$PROG"/*
echo "Hecho. La carpeta de copias es $BASE (fuera de tus carpetas de trabajo y de iCloud)."

paso "3/6 · Claves en el llavero de macOS (servicio «moticias-copia»)"
if [ -z "$(clave cifrado)" ]; then
  F="$(openssl rand -base64 30 | tr -d '/+=' | cut -c1-32)"; guardar cifrado "$F"
  printf '\nFrase de cifrado de las copias (guárdala AHORA también en tu gestor de contraseñas o en papel: sin ella, si el Mac\nse pierde, las copias cifradas no se pueden abrir):\n\n    \033[1m%s\033[0m\n\n' "$F"
  read -r -p "Pulsa Intro cuando la hayas guardado. " _
else echo "Frase de cifrado: ya estaba en el llavero."; fi
if [ -z "$(clave ghost-admin-key)" ]; then
  echo "Clave de Ghost: en Ghost → Settings → Integrations → «Add custom integration», llámala «Copia de seguridad Mac» y copia su «Admin API key»."
  open "https://moticias.ghost.io/ghost/#/settings/integrations" >/dev/null 2>&1
  read -r -s -p "Pégala aquí (no se verá) y pulsa Intro: " G; echo
  [[ "$G" == *:* ]] || alto "Eso no parece una Admin API key (tiene la forma xxxxx:yyyyy)."
  guardar ghost-admin-key "$G"
else echo "Clave de Ghost: ya estaba en el llavero."; fi
[ -n "$(clave token-registro)" ] || guardar token-registro "$(openssl rand -hex 32)"

paso "4/6 · Acceso de solo lectura a la base privada (Supabase)"
if [ -z "$(clave supabase-url)" ]; then
  P="$(openssl rand -hex 24)"
  H="$(printf '%s' "$(clave token-registro)" | shasum -a 256 | cut -d' ' -f1)"
  EQUIPO="$(scutil --get ComputerName 2>/dev/null || hostname)"
  printf "alter role copia_lectura with login password '%s';\ninsert into privado.copias_llave (huella, equipo) values ('%s', '%s') on conflict (huella) do nothing;\n" "$P" "$H" "${EQUIPO//\'/}" | pbcopy
  open "https://supabase.com/dashboard/project/$REF/sql/new"
  echo "Se ha abierto el editor SQL de Supabase y tienes DOS líneas en el portapapeles."
  echo "En esa página: pega (Cmd+V), pulsa «Run» y espera a «Success»."
  read -r -p "Pulsa Intro cuando esté. " _
  URI=""
  for host in "aws-1-eu-central-1.pooler.supabase.com" "aws-0-eu-central-1.pooler.supabase.com"; do
    u="postgresql://copia_lectura.$REF:$P@$host:5432/postgres?sslmode=require"
    if psql "$u" -At -c "select 1" >/dev/null 2>&1; then URI="$u"; break; fi
  done
  if [ -z "$URI" ]; then
    u="postgresql://copia_lectura:$P@db.$REF.supabase.co:5432/postgres?sslmode=require"
    psql "$u" -At -c "select 1" >/dev/null 2>&1 && URI="$u"
  fi
  [ -n "$URI" ] || alto "No consigo entrar en la base con el usuario de solo lectura. ¿Salió «Success» en Supabase? Vuelve a pegar el comando: generará una contraseña nueva."
  guardar supabase-url "$URI"; echo "Acceso de solo lectura: funciona."
else echo "Acceso a la base: ya estaba en el llavero."; fi

paso "5/6 · Copia diaria a las 13:30 (y al iniciar sesión, si ese día no se hizo)"
PL="$HOME/Library/LaunchAgents/com.moticias.copia.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PL" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
 <key>Label</key><string>com.moticias.copia</string>
 <key>ProgramArguments</key><array><string>/bin/bash</string><string>$PROG/copia.sh</string></array>
 <key>StartCalendarInterval</key><dict><key>Hour</key><integer>13</integer><key>Minute</key><integer>30</integer></dict>
 <key>RunAtLoad</key><true/>
 <key>ProcessType</key><string>Background</string>
 <key>LowPriorityIO</key><true/>
</dict></plist>
EOF
launchctl bootout "gui/$(id -u)" "$PL" >/dev/null 2>&1
launchctl bootstrap "gui/$(id -u)" "$PL" || alto "macOS no aceptó la tarea programada."
echo "Programada. Si el Mac está dormido a las 13:30, la hace al despertar; si estaba apagado, al iniciar sesión."

paso "6/6 · Primera copia y primera prueba de restauración (unos minutos)"
rm -f "$BASE/.ultima-prueba"
bash "$PROG/copia.sh" --forzar
tail -n 25 "$BASE/registro.log" | grep -E "copia correcta|PRUEBA|FALLO|registro en el gestor" || true
echo
echo "Listo. En el gestor (https://app.moticias.com/gestor/ → Equipo) verás «Última copia» y «Última copia probada»."
echo "El registro detallado está en $BASE/registro.log."
