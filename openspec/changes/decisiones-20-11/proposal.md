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

## 21-11-2026 · Titulares recogidos por el servidor

La edición nº 15 (primera con los medios como sensores) gastó 447.597 tokens en lectura web y cerró con tres piezas y sin análisis. Decisión de Rainer: la recogida de titulares pasa al servidor, sin IA, cada hora de 06:00 a 23:00 (Madrid) y nunca entre las 23:01 y las 06:00; sirve además para detectar grandes noticias en el momento.

- `src/sensores_titulares.py` (RSS, archivo por día o portada; `probar`), `verticals → sensores` (13 medios y reglas de «gran noticia»), migración 017 (`sensores_titulares`, `sensores_medios`), cron de Vercel `sensores` (`api/gestor.py`: `sensores_al_dia`).
- Un titular nuevo que casa con una regla va a la cola del editor (rutina «sensores», importancia 4) y encarga un barrido; como mucho tres por pasada; la primera pasada no avisa.
- La edición lee la lista con `execute_sql`; a la antigua solo los medios con error (Aviación Digital responde con una página de espera a las lecturas automáticas).
- Si el tope de 450.000 tokens sigue obligando a cerrar corto, el aviso empieza por «TOPE INSUFICIENTE» y el editor jefe decide si se sube.
- Pendiente: el barrido que encarga un aviso lo atiende la pasada horaria de la redacción solo en laborables de 8 a 21; en fin de semana, las batidas de las 11:00 y las 17:30.
