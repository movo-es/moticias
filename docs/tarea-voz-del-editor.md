# Tarea: «La voz del editor» (sábados, 07:51 Europe/Madrid)

Decisión de Rainer del 15-11-2026, cambio `menu-y-voz-del-editor` (`verticals/movilidad.json → voz_del_editor`). Corre en la nube, sin nadie para contestar preguntas. Propone; no publica nunca: texto e imagen necesitan siempre la aprobación del editor jefe en el gestor, y lo aprobado sale el lunes a las 08:00 (programado en Ghost).

## Qué entrega
Dos o tres propuestas de columna para la semana, cada una como pieza en borrador en `data/articles/<id>.json`, con:
- `kind: "opinion"`, `tipo_contenido: "editorial"`, `section: "analisis"`, `status: "pendiente"` (nunca `publicado`), `author: "Rainer Uphoff"`, `author_role: "Editor jefe de MOTICIAS"`, `date` = el lunes siguiente, sin `published_at` (lo pone el gestor al aprobar).
- `voz: {semana: "AAAA-Www", enfoque: "<la tesis en una frase>", por_que_ahora: "<qué se ha debatido esta semana y dónde, con enlaces>", propuesta: 1|2|3}`.
- `title` (afirmativo, con la tesis), `subtitle`, `summary`, `body_md` de 700–1.100 palabras, `sources` (cada hecho con su fuente primaria y su fecha; las opiniones ajenas citadas, con su enlace), `interests_note` (la de las piezas que firma el editor jefe) y las etiquetas comunes (`python3 -I src/taxonomia.py pieza <ruta>`; `importancia` 4 o 5).
- `image`: imagen candidata con licencia libre, del sujeto concreto, sin rostros reconocibles, con `credit`, `license` y `source_url` (Openverse, como en la edición diaria; `docs/tarea-edicion-diaria.md` paso 5). Si no hay ninguna pertinente, `image: null` y dilo.

## Cómo
1. **Qué se ha debatido esta semana.** Barrido de los últimos siete días (WebSearch acotado): prensa general y sectorial, Congreso y Senado, asociaciones (Confebus, Anfac, ALA, Anave, CETM…), sindicatos, reguladores (CNMC, AESA, AIReF), Comisión Europea y LinkedIn público de los decisores. Más la cola del editor (temas de la semana con importancia 4–5, `cola_temas`) y lo publicado en MOTICIAS (`python3 -I src/buscador.py`). Elige dos o tres temas **espinosos**: donde hay intereses enfrentados, una decisión pendiente o una contradicción entre lo que se dice y lo que se hace. No temas del grupo (Movenbus, MUFMI, MOVO, Avionline) ni ataques personales.
2. **Estilo del editor jefe.** Antes de escribir, lee enteras las piezas que ha firmado (`author: "Rainer Uphoff"` en `data/articles/`; hoy: «Después de Urda: quién manda en la vía», «Conectar Europa a precios constantes», «Cultura justa por la vía urgente», «El autobús vive de prórroga», «Despacho ordinario para una agenda que no lo es»). Imita: tesis en el primer párrafo, frases cortas, datos con unidad y fuente, una objeción leal al propio argumento, cierre con lo que debería decidirse y quién. Sin adjetivos vacíos, sin descalificaciones, sin «en definitiva». La opinión se nota; los hechos no se inventan: **ninguna cifra, cita ni fecha sin su fuente primaria abierta en esta sesión**.
3. **Imagen.** Una candidata por propuesta (Openverse, licencia CC0, CC BY o CC BY-SA), guardada en `portal/img/` con su entrada en `portal/img/credits.json`.
4. **Validar.** `python3 -I src/tipos.py validar` y `python3 -I src/taxonomia.py validar`.
5. **Subir.** `git push` si puedes; si no, el buzón del repositorio (`src/buzon.py`, como la edición diaria). Después, `python3 -I src/ghost_publish.py --ids <ids> --status draft` si hay `GHOST_ADMIN_KEY` (quedan como borrador en Ghost; si no, el gestor las sube al aprobarlas).
6. **Aviso.** Un mensaje corto: «La voz del editor: N propuestas para el lunes DD», una línea por propuesta (título · enfoque · palabras · imagen sí/no) y el enlace directo `https://app.moticias.com/gestor/?vista=cola`, donde se aprueban (texto e imagen), se editan o se pide otra versión.

## Lo que hace el editor jefe (no la tarea)
En la pestaña «Cola» del gestor, arriba, «La voz del editor · propuestas»: **Aprobar** (marca texto e imagen; queda programada para el lunes 08:00), **Leer y editar**, o **Pedir otra versión** (crea un retoque que atiende `/retoques` en su pasada horaria: rehace el texto o busca otra imagen y la deja otra vez pendiente). Las propuestas que no apruebe se quedan en borrador; nada se borra.
