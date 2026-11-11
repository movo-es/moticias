# Cambio: fin de semana, barrido a demanda y arranque sin fallos

Decisiones de Rainer del 9 de noviembre de 2026 (tarde), tras una mañana en que la edición nº 4 se cerró en el portal pero no llegó a GitHub ni a moticias.com. La regla de firma del director (cupo del 10 %) va en el cambio `editor-jefe-y-crm`; aquí solo la identidad de los commits.

## Por qué

- «No debe haber ningún fallo ningún día.» La rutina dependía de una herramienta (`add_repo`) que unas sesiones tienen y otras no; sin ella, el proxy rechaza el `git push` y el trabajo se pierde al cerrarse la sesión. Tampoco había claves de Ghost en el entorno de la tarea.
- «Los sábados y domingos haz batidas solo para grandes noticias, interrupciones de servicio, catástrofes, etc., que se merezcan una edición extra. El resto se guarda para el lunes.»
- «En el panel del editor jefe, además de las demás herramientas, debo tener un botón para "Iniciar barrido de noticias ahora", por si veo que ha pasado algo gordo que aún no está.»
- Los commits de la redacción salían con el correo del director; firma la redacción: `G. Jordan <redaccion@moticias.com>`.

## Qué cambia

- **Arranque**: la rutina comprueba antes de las 07:12 si puede subir a `main`, si tiene `GHOST_URL` y `GHOST_ADMIN_KEY` y las herramientas del portal; si falta algo, avisa en ese momento. Sube siempre a `main`. Si no puede subir, deja el parche (sin datos regenerables) en el proyecto de Claude, `claude/moticias-pendiente/`, y la siguiente sesión con permiso lo aplica. Antes de la edición de hoy, pone al día la anterior (hemeroteca, moticias.com, menciones).
- **Fin de semana**: dos tareas, sábados y domingos a las 10:55 y 17:26, con `docs/tarea-batida.md`: edición extra solo si algo lo merece; lo demás a `data/reserva/` para el lunes, que lo usa en su selección. En festivo nacional entre semana, la rutina diaria hace la misma batida.
- **Botón**: «Iniciar barrido de noticias ahora» en la vista Piezas del gestor y en el menú ✎ del editor jefe en moticias.com (todas las páginas), para el editor jefe y los editores, con una pista opcional; lanza la batida por el disparador de API de su tarea. El token vive solo en Vercel (`RUTINA_BARRIDO_TOKEN`).
- **Commits** de la redacción como `G. Jordan <redaccion@moticias.com>` (`editorial.commits`).

## Impacto

- Documentos: `CLAUDE.md`, `docs/tarea-edicion-diaria.md` (DÍAS, EL REPOSITORIO, ARRANQUE), `docs/manual-operativo.md`, `docs/tarea-batida.md` (nuevo).
- Comandos: `.claude/commands/batida.md` (nuevo).
- Configuración: `verticals/movilidad.json` (`schedule.weekend_sweeps`, `editorial.commits`, `fin_de_semana`, `rutinas`).
- Código: `api/gestor.py` (acción `barrido`), `app/public/gestor/index.html` (caja y botón; `?barrido=1`), `app/public/sitio/m.js` (menú ✎ en todas las páginas con el barrido), `src/equipo.py` (permiso `barrido`).
- Tareas programadas: texto nuevo de «MOTICIAS · edición diaria»; nuevas «MOTICIAS · batida de fin de semana (mañana)» y «(tarde)».
- Datos nuevos: `data/reserva/AAAA-MM-DD.json` (sin datos personales).
