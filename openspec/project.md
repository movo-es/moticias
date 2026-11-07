# MOTICIAS · Contexto del proyecto (OpenSpec)

## Propósito
Portal profesional de noticias, análisis y referencia regulatoria del transporte de personas (tierra, mar, aire) en España, para decisores. Edición diaria automática en laborables, redactada por Claude bajo las reglas de `docs/`, publicada hoy en artefactos de Claude (portal y hemeroteca) y mañana en Ghost(Pro) (moticias.com).

## Pila
- Contenido: JSON por documento en `data/`; fotos CC en `portal/img/`.
- Portal: artefacto de Claude (HTML/CSS/JS sin dependencias, base de datos del artefacto). Código en `portal/`.
- Hemeroteca: artefacto de Claude. Código en `hemeroteca/`; compilador `src/hemeroteca_build.py`.
- Rutina: Claude Code, comando `/edicion-diaria`, tarea programada a las 06:38 Europe/Madrid.
- Scripts: Python 3 estándar (`src/`), sin dependencias externas.
- Publicación futura: Ghost(Pro) por Admin API (`src/ghost_publish.py`, pendiente).
- Suscriptores: Brevo o miembros de Ghost (por decidir).

## Convenciones
- Español de España en código, docs, commits y specs.
- Un cambio OpenSpec = carpeta `openspec/changes/<nombre-kebab>/` con `proposal.md`, `tasks.md` y `specs/<capacidad>/spec.md` (deltas: ADDED / MODIFIED / REMOVED Requirements con escenarios).
- Las specs en `openspec/specs/<capacidad>/spec.md` describen lo que el sistema hace HOY; se actualizan al archivar un cambio.
- `docs/` es la explicación larga para personas; las specs son la verdad corta y comprobable. Si discrepan, gana la spec y se corrige la doc en el mismo cambio.
- Nunca se borra contenido publicado.

## Flujo
explore (leer specs y docs; entender) → propose (crear el cambio, con escenarios) → apply (specs, docs, código, comando) → verify (probar; para la rutina, una edición en seco) → archive (mover a `changes/archive/AAAA-MM-DD-<nombre>` y fundir deltas en `specs/`).
