# MOTICIAS — «con M de Movilidad»

Portal profesional de noticias, análisis y referencia regulatoria del transporte de personas por tierra, mar y aire en España, para decisores. Lo dirige Rainer (director de MOTICIAS; cofundador de Movenbus, operador de transporte de viajeros: MOTICIAS no cubre operaciones propias de Movenbus y lo declara). Idioma: español de España. Referencias de calidad: Railway Gazette, Flightglobal, Lloyd's List, Tagesspiegel Background.

Este repositorio es la única fuente de verdad: reglas, fuentes, contenido y decisiones viven aquí (`docs/arquitectura.md`). Si algo no está aquí, no existe para el sistema.

## Antes de tocar nada

1. Lee `docs/arquitectura.md` (dónde está cada cosa) y `docs/manual-operativo.md` (modelo de datos, reglas editoriales, rutina).
2. Para escribir o revisar una pieza: `docs/estandar-profundidad.md` es obligatorio.
3. Para la rutina de la mañana: `/edicion-diaria` (`docs/tarea-edicion-diaria.md`).
4. Para cambiar una regla, un formato o el código: método OpenSpec en `openspec/` (explore → propose → apply → verify → archive). Un cambio toca a la vez la spec, la doc, el código y el comando que correspondan; nunca uno solo.

## Reglas de siempre

- Nunca publicar sin fuente primaria enlazada; nunca inventar una cifra, una cita o una fecha; ante la duda sobre una fecha, no se publica.
- Cada pieza es un reportaje de fondo (1.000–1.500 palabras) con cifras clave, cronología y 6–12 fuentes con fecha; los resúmenes no se publican.
- Nunca borrar piezas, boletines ni plazos anteriores; las correcciones añaden `revised_at` y una nota al final.
- Edición diaria solo en laborables españoles; noticia flash de gran importancia, cualquier día.
- Fotos solo con licencia libre y crédito, del sujeto concreto, sin rostros reconocibles; nunca la misma foto dos veces en la misma página.
- La investigación de un accidente se cita como investigación en curso.
- No se toca el código del portal ni el de la hemeroteca fuera de un cambio OpenSpec.
- Lectura web sin aprobaciones: WebFetch solo con URL que ya aparecen en la sesión; las APIs del BOE y de Openverse son la única excepción para scripts.

## Cómo trabaja Rainer

- Es experto senior en transporte y movilidad e «ignorante» en lo técnico fuera de su campo: explica sin dar por supuestos conocimientos de programación.
- Todo comando para copiar y pegar lleva delante el `cd` a este proyecto, en un bloque copiable: trabaja con varios repositorios a la vez (`movo-es/movo`, `movo-es/avionline-contabilidad`, este).
- Todo debe funcionar en la nube, sin su ordenador abierto, y poder revisarse y aprobarse desde el móvil.
- Publicación web: subdirectorios, nunca subdominios; estructura answer-first; Schema.org; `llms.txt`; datos propios antes que resúmenes.

## Mapa del repositorio

- `CLAUDE.md` — esta página.
- `docs/` — manual operativo, estándar de profundidad, tarea diaria, fuentes, benchmark, plan, gestores del portal, registro de ediciones, arquitectura.
- `openspec/` — `project.md`, `specs/` (lo que el sistema hace hoy) y `changes/` (lo que está cambiando; `archive/` lo cerrado).
- `data/` — contenido publicado, un JSON por documento: `articles/`, `boletines/`, `agenda/`, `editions/`, `settings/`, `blogs/`, `ads/`, `soluciones/`.
- `portal/` — código y datos del artefacto MOTICIAS; `portal/img/` las fotos con `credits.json`.
- `hemeroteca/` — código y `data/` de la Hemeroteca MOTICIAS.
- `src/` — `export_data.py`, `hemeroteca_build.py`, `boe_sweep.py`.
- `.claude/commands/` — `edicion-diaria`.
- `work/` — temporal, ignorado por git.

## Estado (7 de noviembre de 2026)

Tres ediciones publicadas (4, 5 y 6 de noviembre): 74 piezas, 53 referencias del BOE, 51 plazos. Portal y hemeroteca en artefactos de Claude. Ghost(Pro) elegido para moticias.com; cuenta creada, dominio y API pendientes. Pendientes principales en `docs/manual-operativo.md § 9` y `docs/plan-moticias-com.md § 9`.
