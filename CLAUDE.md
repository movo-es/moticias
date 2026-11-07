# MOTICIAS — «con M de Movilidad»

Portal profesional de noticias, análisis y referencia regulatoria del transporte de personas por tierra, mar y aire en España, para decisores. Lo dirige Rainer (director de MOTICIAS; cofundador de Movenbus, operador de transporte de viajeros: MOTICIAS no cubre operaciones propias de Movenbus y lo declara). Idioma: español de España. Referencias de calidad: Railway Gazette, Flightglobal, Lloyd's List, Tagesspiegel Background.

Este repositorio es la única fuente de verdad: reglas, fuentes, contenido y decisiones viven aquí (`docs/arquitectura.md`). Si algo no está aquí, no existe para el sistema.

## Antes de tocar nada

1. Lee `docs/arquitectura.md` (dónde está cada cosa), `docs/estrategia.md` (para qué existe MOTICIAS: credibilidad → leads → promoción discreta; segmentos y soluciones del grupo) y `docs/manual-operativo.md` (modelo de datos, reglas editoriales, rutina).
2. Para escribir o revisar una pieza: `docs/estandar-profundidad.md` es obligatorio.
3. Para la rutina de la mañana: `/edicion-diaria` (`docs/tarea-edicion-diaria.md`).
4. Para cambiar una regla, un formato o el código: método OpenSpec en `openspec/` (explore → propose → apply → verify → archive). Un cambio toca a la vez la spec, la doc, el código y el comando que correspondan; nunca uno solo.

## Reglas de siempre

- Nunca publicar sin fuente primaria enlazada; nunca inventar una cifra, una cita o una fecha; ante la duda sobre una fecha, no se publica.
- Cada pieza es un reportaje de fondo (1.000–1.500 palabras) con cifras clave, cronología y 6–12 fuentes con fecha; los resúmenes no se publican.
- Nunca borrar piezas, boletines ni plazos anteriores; las correcciones añaden `revised_at` y una nota al final.
- Edición diaria solo en laborables españoles; noticia flash de gran importancia, cualquier día.
- Firma y aprobación: las piezas rutinarias (una fuente oficial o dos profesionales de confianza) se publican directas firmadas «G. Jordan, Redactor responsable»; las críticas para la reputación o con implicaciones legales y los análisis se firman «Rainer, Director de MOTICIAS» y esperan su aprobación (`status: pendiente`). Criterios en `verticals/movilidad.json` → `editorial`.
- Titular de MOTICIAS y responsable del tratamiento: Avionline S.L.
- Modelos: barridos y escritura automática en Opus 5.5; el asesor semanal en Fable 5.1.
- Fotos solo con licencia libre y crédito, del sujeto concreto, sin rostros reconocibles; nunca la misma foto dos veces en la misma página.
- Campañas temáticas (`data/campanas/`): orientan la selección (palabras clave, cadencia, peso), nunca el tratamiento ni la firma; monetización señalizada y fuera del texto; la fecha gancho no se publica sin verificar en fuente primaria.
- La investigación de un accidente se cita como investigación en curso.
- No se toca el código del portal, el de la hemeroteca ni el tema de Ghost fuera de un cambio OpenSpec.
- Lectura web sin aprobaciones: WebFetch solo con URL que ya aparecen en la sesión; las APIs del BOE y de Openverse son la única excepción para scripts.

## Cómo trabaja Rainer

- Es experto senior en transporte y movilidad e «ignorante» en lo técnico fuera de su campo: explica sin dar por supuestos conocimientos de programación.
- Todo comando para copiar y pegar lleva delante el `cd` a este proyecto, en un bloque copiable: trabaja con varios repositorios a la vez (`movo-es/movo`, `movo-es/avionline-contabilidad`, este).
- Todo debe funcionar en la nube, sin su ordenador abierto, y poder revisarse y aprobarse desde el móvil.
- Publicación web: subdirectorios, nunca subdominios; estructura answer-first; Schema.org; `llms.txt`; datos propios antes que resúmenes.

## Mapa del repositorio

- `CLAUDE.md` — esta página.
- `docs/` — estrategia, arquitectura, manual operativo, estándar de profundidad, tarea diaria, fuentes, benchmark, plan, gestores del portal, registro de ediciones; `docs/asesor/` informes semanales del asesor; `docs/promo/` borradores de promoción.
- `openspec/` — `project.md`, `specs/` (lo que el sistema hace hoy) y `changes/` (lo que está cambiando; `archive/` lo cerrado). Cambio en curso: `plataforma-v1` (sala de redacción, suscripciones, CRM, promoción, sensores, verticales).
- `verticals/` — configuración de cada vertical (`movilidad.json` = MOTICIAS; `turismo.json` = «viajar en grupo», previsto). Nada específico de un vertical va en el código.
- `supabase/migrations/` — esquema de la plataforma (CRM, leads, campañas, señales, asesor).
- `data/` — contenido publicado, un JSON por documento: `articles/`, `boletines/`, `agenda/`, `editions/`, `settings/`, `blogs/`, `ads/`, `soluciones/`, `campanas/` (campañas temáticas; informes en `docs/campanas/`), `paginas/` (aviso legal, privacidad, cookies, cómo trabajamos).
- `ghost-theme/` — tema de moticias.com (aspecto del portal, marca v1); `ghost/` — `routes.yaml` (secciones en subdirectorios, `/llms.txt`) y `redirects.yaml`; `.github/workflows/tema-ghost.yml` lo despliega (`docs/tema-ghost.md`).
- `verticals/movilidad/marca/` — marca v1 (la Glorieta; `docs/marca.md`).
- `portal/` — código y datos del artefacto MOTICIAS; `portal/img/` las fotos con `credits.json`.
- `hemeroteca/` — código y `data/` de la Hemeroteca MOTICIAS.
- `src/` — `export_data.py`, `hemeroteca_build.py`, `boe_sweep.py`, `ghost_publish.py`, `ghost_theme_deploy.py`, `ghost_redirects.py`.
- `.claude/commands/` — `edicion-diaria`, `consejo-visibilidad`, `radar-regulatorio`, `licitaciones-semana`, `sensores`, `promo-social`, `campana-tematica`.
- `work/` — temporal, ignorado por git.

## Tareas programadas (en la nube, cuenta de Rainer)

- «MOTICIAS · edición diaria» — laborables 06:38 Europe/Madrid — clona este repositorio y ejecuta `/edicion-diaria`.
- «MOTICIAS · asesor de visibilidad y credibilidad» — lunes 09:17 — ejecuta `/consejo-visibilidad`.
- Previstas: radar regulatorio (lunes), licitaciones de la semana (viernes), sensores de mediodía (13:30), promo-social (tras la edición).

## Paso a Claude Code

`docs/paso-a-code.md`: cómo abrir el repositorio en Claude Code, instalar OpenSpec y el orden de las entrevistas (una capacidad por cambio) para construir la plataforma v1.

## Estado (7 de noviembre de 2026)

Tres ediciones publicadas (4, 5 y 6 de noviembre): 74 piezas, 53 referencias del BOE, 51 plazos. Portal y hemeroteca en artefactos de Claude. Ghost(Pro) activo para moticias.com (`src/ghost_publish.py`, regla de firma y estado en `docs/firma-y-publicacion.md`): 62 piezas rutinarias publicadas con firma G. Jordan, 12 críticas, análisis y reportajes en borrador a nombre de Rainer; páginas legales (`data/paginas/`) en borrador hasta su orden. Tema propio con el aspecto del portal (`tema-ghost-v1`) activo en www.moticias.com desde el 7-11-2026 (20:50); funciona en modo «raíz» (menú en el tema, secciones como páginas, piezas en `/<slug>/`) hasta que haya `GHOST_STAFF_TOKEN` para subir `routes.yaml` y los ajustes del sitio (`docs/tema-ghost.md`). Plataforma v1 propuesta en `openspec/changes/plataforma-v1/` con sus fases en `tasks.md`; primera campaña temática «Movilidad al trabajo · PMST» (10-11 → 19-12-2026) en `data/campanas/`. Pendientes principales en `docs/plan-moticias-com.md § 9`.
