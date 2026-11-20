# decisiones-20-11 — edición todos los días, medios como sensores, fuente secundaria, etiquetas al pie, regiones y preferencias del boletín

Decisiones de Rainer del 20-11-2026 (tarde y noche), a raíz de una noticia que MOTICIAS no dio: «Alsa Rail asume la gestión ferroviaria del puerto de Gijón» (El Mercantil, 13-11-2026).

## Por qué

La noticia no se detectó: el barrido buscaba por temas en un buscador con ventana de 24–48 horas y no leía los medios monitorizados entrada a entrada; salió un viernes por la tarde, el fin de semana solo se buscaban grandes noticias, y las reglas (solo viajeros, solo con fuente primaria, solo 72 horas) la habrían frenado igualmente.

## Qué cambia

1. **Edición todos los días**, también sábados, domingos y festivos (07:05). Las batidas de fin de semana siguen; su reserva la usa la edición de la mañana siguiente.
2. **Medios monitorizados como sensores**: lectura diaria, entrada a entrada, de la prensa especializada. **El Mercantil se repasa entero cada día** (archivo por día) como control, con recuento en la nota metodológica. Mercancías y logística del sector entran; un hecho de hasta siete días no publicado entra con su fecha.
3. **Fuente primaria siempre que exista; secundaria solo si no la hay**: medio reputado, citado con enlace y fecha, redacción totalmente propia, dicho en la nota metodológica. En la cola, «secundaria» basta con un medio profesional reputado.
4. **Etiquetas clicables al pie** de todas las piezas («Más noticias sobre»): `tags` (4–8, protagonistas y temas) más modo, tema y región, enlazadas a `/tag/<slug>/`. `FORMATO = "2"`; el cron `ghost_al_dia` republica las piezas antiguas (`formato_al_dia`, 10 por pasada) sin tocar texto, estado ni destacado.
5. **Regiones**: nueva `pt-iberoamerica` (Portugal e Iberoamérica); `ue` pasa a llamarse «Europa» e `internacional`, «Resto del mundo» (los slugs de Ghost no cambian; `alinear_ejes` renombra las etiquetas). Selección PT‑IbAm limitada a relevancia internacional e inversiones significativas. Todo en español; el enlace, a la fuente en su idioma original.
6. **Preferencias al apuntarse al boletín**: temas y regiones bajo el correo (`m.js`, apartado 9), guardadas como etiquetas del suscriptor en Ghost.

## Dónde

`CLAUDE.md`, `docs/tarea-edicion-diaria.md`, `docs/tarea-batida.md`, `docs/fuentes.md`, `.claude/commands/`, `verticals/movilidad.json`, `src/ghost_publish.py`, `api/gestor.py`, `app/public/sitio/m.js`, `tests/test_etiquetas_pie.py`.

## Hecho el 20-11-2026

- Repaso de El Mercantil del 2 al 20 de noviembre (unos 120 titulares): 14 temas no publicados, a la cola del editor (`rutina: repaso-el-mercantil`); los dos del día 20, además, en `data/reserva/2026-11-20.json`.
- Piezas reclasificadas a `pt-iberoamerica`: TAP–Lufthansa (4-11) y acuerdo aéreo España–Uruguay (18-11).

## Pendiente

- Inventario verificado de fuentes de Portugal e Iberoamérica en `docs/fuentes.md` (hoy el bloque se barre por búsqueda).
- Envíos del boletín segmentados por las etiquetas de preferencia, cuando arranque el boletín.
- Preferencias en la ventana de Ghost (Portal), que no admite etiquetas: hoy «Suscríbete» lleva al formulario del pie.
