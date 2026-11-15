# MOTICIAS · Puesta en marcha de las tareas automáticas

Lo que necesitan las tareas programadas para trabajar solas, sin parches ni pasos a mano. Las claves no se escriben nunca en el repositorio (es público) ni en el chat: solo en los campos de variables de Vercel. Cambio OpenSpec `fin-de-semana-barrido-y-arranque` (2, 2 bis y 2 ter).

## Cómo llega una edición a moticias.com (desde el 14-11-2026)

1. La tarea escribe en el portal y en `data/`, y hace `commit`.
2. Si puede hacer `push`, lo sube a `main`. Si no puede (desde el 12-11-2026 las sesiones programadas arrancan sin el repositorio autorizado y la pantalla de tareas no tiene dónde adjuntarlo), deja el trabajo en el **buzón del repositorio**: `python3 -I src/buzon.py preparar --origen <tarea>` y cada `work/buzon/*.sql` con `execute_sql` del conector de Supabase (proyecto «moticias», `cjrntzaqmvhgscdgiehs`).
3. El cron de Vercel `aplicar_buzon` (cada 10 minutos) sube el lote a `main` con el `GITHUB_TOKEN` del gestor, en un solo commit firmado por la tarea.
4. Vercel se redespliega con el nuevo `main` y el cron `ghost_al_dia` (cada 15 minutos, de 7 a 20 h, todos los días) publica en moticias.com las ediciones que falten, con las claves de Ghost que tiene Vercel.

Por el buzón solo entra contenido: `data/`, `docs/ediciones.md`, `docs/fuentes.md`, `docs/asesor/` y `portal/img/`. Un cambio de código o de configuración necesita un `push` de verdad (una sesión de Claude Code con el repositorio, o un `git push` desde el Mac).

## Una sola vez

1. **Migración 008 en Supabase.** En el editor SQL del proyecto «moticias» (https://supabase.com/dashboard/project/cjrntzaqmvhgscdgiehs/sql/new), pegar el contenido de `supabase/migrations/008_buzon_repositorio.sql` y pulsar Run. Se puede ejecutar dos veces sin daño.
2. **Vercel (proyecto `moticias-app`).** Settings → Environment Variables (Production). Deben existir: `GITHUB_TOKEN` (con permiso de escritura en `movo-es/moticias`), `CRON_SECRET`, `GHOST_URL`, `GHOST_ADMIN_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `MOTICIAS_BD_CLAVE`, `GESTOR_CLAVE_SUPERADMIN`, `GESTOR_CLAVE_OFICINA`, `BREVO_API_KEY` y, para el botón, `RUTINA_BARRIDO_TOKEN`. Tras añadir o cambiar una: Deployments → el último → Redeploy.
3. **Tareas programadas.** En las dos batidas, Permisos → «Automático» (como la edición diaria). No hace falta adjuntar el repositorio ni poner claves en las tareas.
4. **Token del botón «Iniciar barrido de noticias ahora»** (opcional). En la batida de la mañana, el disparador por API → generar token → Vercel `RUTINA_BARRIDO_TOKEN` → Redeploy. El identificador de la tarea ya está en `verticals/movilidad.json` → `rutinas.barrido`.

## Comprobación

1. `https://app.moticias.com/api/gestor?a=yo` da `true` en `configurado`, `escritura`, `ghost`, `bd` y, si se hizo el paso 4, `barrido` (solo dice si la variable existe; no enseña su valor).
2. En Supabase, `select lote, parte, partes, estado, sha, error from repo_buzon order by creado_at desc limit 10;` no tiene lotes en `pendiente` de más de 15 minutos ni en `error`.
3. La cabecera de `https://www.moticias.com/` dice «Edición nº N» con la última edición de `data/editions/`.

## Si un lote queda en `error`

El mensaje dice qué fichero no encajaba: casi siempre, alguien cambió en `main` ese mismo fichero (por ejemplo, `docs/ediciones.md`) desde que la tarea lo leyó. La siguiente sesión con el repositorio al día vuelve a preparar el lote; nada se pisa ni se borra.

## Copia de seguridad en el Mac (cambio `copia-de-seguridad-mac`, 15-11-2026)

Es un respaldo: nada de lo anterior depende de ella. Instalación y comprobación en `docs/copia-de-seguridad.md`. Una sola vez, además: el espejo privado del repositorio (crear `movo-es/moticias-respaldo` vacío y privado, un token con permiso de escritura solo en él y guardarlo como secreto `ESPEJO_TOKEN` de Actions en `movo-es/moticias`). Comprobación: gestor → Equipo → «Copias de seguridad», y en GitHub, Actions → «espejo» en verde.
