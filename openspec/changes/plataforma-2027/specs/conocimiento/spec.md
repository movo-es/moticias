# Capacidad: conocimiento (delta)

Decisión del 8-11-2026: el conocimiento del grupo es el **motor de conocimiento de MOVO** (`movo-es/movo`: `procesos`, `fuentes`, `fuente_rango`, `fuente_proceso`, `fuente_uso`, `fuente_usable()`, `conocimiento_canales`/`_hallazgos`/`_barridos`, `lib/conocimiento/anclaje.js`, `docs/CONOCIMIENTO-MOVILIDAD.md`). MOTICIAS no construye otro: lo extiende con un proceso propio y una capa de búsqueda semántica. Las migraciones de este cambio se escriben en el repositorio de MOVO, con sus reglas (RLS y permisos explícitos, funciones cerradas, la IA no calcula).

## ADDED Requisito: proceso `moticias` en el motor común
`procesos` gana la fila `moticias` (y, cuando toque, `amarantia`). Las fuentes se comparten por `fuente_proceso` (alcance y veto por proceso); una fuente baneada en un proceso no se cita en él aunque valga en otro.

## ADDED Requisito: canales y hallazgos de MOTICIAS
Los canales de MOTICIAS (BOE por API, boletines autonómicos, reguladores, las propias piezas) se dan de alta en `conocimiento_canales` con `proceso = 'moticias'`, `oficial` marcado por una persona, y filtros. `/conocimiento-ingesta` escribe hallazgos; `ascender_hallazgo()` decide qué entra en `fuentes` según el rango del canal. Los desarrollos normativos encontrados por el agente entran como hallazgos, nunca directamente como fuentes.

#### Escenario: ley con desarrollo autonómico
- CUANDO el agente encuentra un real decreto que desarrolla una ley ya en `fuentes`
- ENTONCES lo escribe como hallazgo del canal que lo publicó; si el canal es oficial, asciende a fuente con `fuente_relacion` «desarrolla»; si no, espera a una persona.

## ADDED Requisito: las piezas son fuentes secundarias reputadas
Cada pieza publicada de MOTICIAS entra en `fuentes` con rango `secundaria_reputada`, identificador `MOTICIAS-<id>`, emisor Avionline S.L., `publicado_at` y `fuente_relacion` «cita» hacia cada una de sus fuentes primarias que ya estén en `fuentes` (las que no, entran como hallazgos).

## ADDED Requisito: búsqueda semántica con citas, filtrada por `fuente_usable()`
`fuente_fragmentos` (fuente, posición, texto, embedding) y una función de consulta que devuelve solo fragmentos de fuentes para las que `fuente_usable(fuente, proceso)` contesta sí, ordenados por similitud y ponderados por rango. La respuesta en pantalla: 40–60 palabras primero, el detalle después, cada afirmación con cita (identificador, artículo o página, vigencia) y «no consta en las fuentes» cuando no hay base. Cifras y fechas se copian del fragmento citado; cada consulta queda registrada con sus citas y su coste.

#### Escenario: pregunta sin base
- CUANDO ninguna fuente usable del proceso tiene un fragmento con similitud suficiente
- ENTONCES la respuesta es «no consta en las fuentes de esta colección», sin texto general del modelo.

## ADDED Requisito: acceso
Consulta en `app.moticias.com/conocimiento` para el nivel corporativa de MOTICIAS (cuota mensual configurable), en la consola de MOVO para la oficina, y por API interna para Amarantia. La información reservada de Amarantia no entra en el motor.
