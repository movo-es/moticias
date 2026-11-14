# MOTICIAS · Puesta en marcha de las tareas automáticas

Lo que necesita cada tarea programada para trabajar sola, sin parches ni pasos a mano. Se hace una vez. Si una tarea avisa al arrancar de que no puede subir o de que le faltan claves, es que falta algo de esta lista. Las claves no se escriben nunca en el repositorio (es público) ni en el chat: solo en los campos de variables de Claude y de Vercel. Cambio OpenSpec `fin-de-semana-barrido-y-arranque` (tareas 2.1–2.4 y 2 bis).

## 1. Acceso de Claude al repositorio en GitHub

La aplicación de GitHub de Claude tiene que tener acceso de escritura a `movo-es/moticias`. `movo-es` es una cuenta personal de GitHub, no una organización: con la sesión de `movo-es` abierta, https://github.com/settings/installations → Claude → Configure → Repository access → «Only select repositories» → añadir `moticias` → Save. Si Claude no aparece en la lista, se instala desde https://github.com/apps/claude eligiendo la cuenta `movo-es` y el repositorio `moticias`.

## 2. Repositorio adjunto en cada tarea

En claude.ai/code/routines, en cada tarea → Edit → Advanced settings → Repository: `movo-es/moticias`.

| Tarea | Identificador |
|---|---|
| MOTICIAS · edición diaria | `trig_0172GECYAmmfyxR7zajD9tp9` |
| MOTICIAS · batida de fin de semana (mañana) | `trig_012Sc1jheY62WPUukGPstLqk` |
| MOTICIAS · batida de fin de semana (tarde) | `trig_01A5CAWQfbfusMNxU3krTUVU` |
| MOTICIAS · retoques del director | `trig_01MJXeXrgHYTVjAQW4nVYD6T` |
| MOTICIAS · asesor de visibilidad y credibilidad | `trig_01RcFoSJK79QunM8FRk4orgi` |
| MOTICIAS · base de prensa | `trig_018tEfQ3B8Wr5Ua8R4htYKwm` |

Sin este paso, el proxy de la sesión rechaza el `push` («not in this session's authorized repository set») y la tarea deja el trabajo como parche en el proyecto de Claude (`claude/moticias-pendiente/`).

## 3. Variables del entorno en la nube de las tareas

Mismo sitio (Edit → Cloud environment → variables). Si las tareas comparten entorno, basta con ponerlas una vez.

| Variable | Valor | De dónde sale | Para qué |
|---|---|---|---|
| `GHOST_URL` | `https://www.moticias.com` | — | publicar en moticias.com (paso 7 quater) |
| `GHOST_ADMIN_KEY` | la Admin API key | Ghost Admin → Settings → Integrations → Add custom integration («MOTICIAS redacción») → Admin API key | ídem |
| `BREVO_API_KEY` | la clave de la API | Brevo → SMTP & API → API keys → Generate a new API key | correo de menciones y base de prensa |
| `MOTICIAS_CONTACTO` | `redaccion@moticias.com` | — | opcional: contacto de la cabecera de las APIs del BOE y Openverse |

Si la tarea de retoques avisa de que no ve la base del gestor (`/noticias-gestor`), añade también `SUPABASE_URL`, `SUPABASE_ANON_KEY` y `MOTICIAS_BD_CLAVE`, con los mismos valores que tienen en Vercel.

## 4. Aprobación automática en las dos batidas

En las dos batidas → Edit → «Automatically approve», como la edición diaria. Sin ello, una batida puede quedarse esperando una aprobación que nadie va a dar.

## 5. Token del botón «Iniciar barrido de noticias ahora»

En «MOTICIAS · batida de fin de semana (mañana)» → Edit → Trigger → + → API → Generate token. Se copia una sola vez y va a Vercel como `RUTINA_BARRIDO_TOKEN` (paso 6). El identificador de la tarea ya está en `verticals/movilidad.json` → `rutinas.barrido`; `RUTINA_BARRIDO_ID` solo hace falta si se cambia de tarea.

## 6. Vercel (proyecto `moticias-app`, equipo MOVO)

Settings → Environment Variables (entorno Production). Deben existir: `GESTOR_CLAVE_SUPERADMIN`, `GESTOR_CLAVE_OFICINA`, `GITHUB_TOKEN`, `GHOST_URL`, `GHOST_ADMIN_KEY`, `CRON_SECRET`, `BREVO_API_KEY`, `RUTINA_BARRIDO_TOKEN`, `SUPABASE_URL`, `SUPABASE_ANON_KEY` y `MOTICIAS_BD_CLAVE`; opcionales: `PRENSA_REMITENTE`, `PRENSA_RESPONDER_A`, `ANTHROPIC_API_KEY`, `AI_GATEWAY_API_KEY`. Después de añadir o cambiar una, Deployments → el último → Redeploy.

## 7. Comprobación

1. `https://app.moticias.com/api/gestor?a=yo` debe dar `true` en `configurado`, `escritura`, `ghost`, `bd` y `barrido` (no enseña ningún valor, solo si la variable existe).
2. Botón «Iniciar barrido de noticias ahora» en el gestor: la sesión dice en sus primeras líneas que puede subir y que tiene las claves de Ghost; aplica los parches de `claude/moticias-pendiente/` en orden de nombre, los sube a `main` y los borra del proyecto.
3. Vercel redespliega solo al llegar el `push` a `main`; en menos de 15 minutos el cron `ghost_al_dia` publica en moticias.com las ediciones que falten (todos los días, de 7 a 20 h).
4. La cabecera de `https://www.moticias.com/` dice «Edición nº N» con la última edición de `data/editions/`.
