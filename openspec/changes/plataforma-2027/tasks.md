# Tareas: plataforma-2027

Este cambio es el mapa; no se aplica entero. Cada fila es un cambio hijo (`openspec/changes/<nombre>/`) que toma su spec de `specs/<módulo>/spec.md` de aquí o de `plataforma-v1`, la afina en la entrevista (si la hay) y se construye y archiva por separado. Las casillas se marcan al archivar el hijo. Orden y fechas: `docs/estrategia-2027.md § 5`.

## Hecho el 8-11-2026 (sesión de estrategia, antes de la primera entrevista)
- [x] Mapa, specs y entrevistas 10–15; reglas nuevas en `CLAUDE.md`.
- [x] Módulo 1 `src/selector.py` + perfiles en `data/perfiles/` (plantilla de asociación migrada del portal, dos widgets).
- [x] Módulo 3 `app/public/widget.js` + `src/export_feed.py` + demo; probado con shadow DOM frente a CSS hostil.
- [x] Módulo 2 `src/empaquetador.py` (selección, revisión, página, correo Brevo, PDF por Chrome); muestra de 8 páginas generada.
- [x] «Quién decide»: `src/quien_decide_semilla.py` y 16 cargos con fuente en `data/cargos/`.
- [x] Comandos `/prensa-buzon`, `/edicion-a-medida`, `/conocimiento-ingesta`, `/auscultar`, `/quien-decide-actualizar` (texto; se afinan en su cambio).
- [x] Borradores legales (`docs/legal/`), `ghost/llms.txt` y `ghost/robots.txt`.
- [x] BDNS como primera fuente de segundo nivel (`src/bdns_sweep.py`, verificado).
- [x] Respuestas de Rainer (8-11, tarde): sector = movilidad + transporte + logística; «conocimiento» tiene código en `movo-es/movo` (se extiende); hay interés de un cliente de Amarantia (auscultador adelantado a enero); canales = Brevo (correo, SMS, WhatsApp), voz después; el repositorio sigue público por decisión suya; la rama se fundió en main (#1).

## Semana 46 (10–16 nov 2026)
- [ ] `publicar-en-ghost-v1` (entrevista 1 hecha el 8-11; `openspec/changes/publicar-en-ghost-v1/tasks.md`): tema versionado, 12 piezas reconciliadas en borrador, legales publicadas, alta con consentimientos, paso 7 quater en la rutina.

## Semana 47
- [ ] `notas-de-prensa-v1` (entrevista corta, nº 10): sección `/notas-de-prensa/`, formulario en `app.moticias.com/prensa/enviar`, buzón `prensa@moticias.com` vaciado por `/prensa-buzon`, ficha de organización, primera nota publicada.

## Semana 48
- [ ] `sala-de-redaccion-v1` (entrevista 3): proyecto Supabase `moticias`, migración 001, `app.moticias.com/redaccion` con cola de aprobación.

## Semana 49
- [ ] `sensores-v1` (sin entrevista): `/sensores` escribe en `senales`; tarea de mediodía 13:30; vista por entidad.

## Semana 50
- [ ] `campanas-tematicas-v1` (entrevista 2): `/campanas` con la campaña PMST.
- [x] `quien-decide-semilla`: hecha el 8-11 (`data/cargos/`, 16 cargos).

## Semanas 51–52
- [ ] `suscripciones-v1` (entrevista 4): niveles en Ghost, alta con perfil, consentimientos separados (boletín · comunicados · ofertas del grupo), centro de preferencias.
- [ ] Tareas programadas: radar regulatorio (lunes 07:30), licitaciones de la semana (viernes 07:30), promo social (laborables 08:15).

## Semanas 1–2 (ene 2027) — adelantado el 8-11 por interés de un cliente
- [ ] `amarantia-auscultador-v1` (entrevista nº 14): `entities`, `baselines`, `alerts`; anillo 2 (Bluesky, Reddit, YouTube, Google News, Telegram público); `/auscultar` cada 2 horas; panel `app.moticias.com/amarantia`; aviso por correo (Brevo) hasta que exista el motor; primera entidad de cliente.

## Semana 3
- [ ] `motor-envios-v1` (entrevista nº 13): adaptador Brevo (correo, SMS, WhatsApp), plantillas, acuses, bajas, registro, secuencias en Vercel Workflow; alertas de licitaciones por comunidad. Voz fuera.
- [ ] `fuentes-segundo-nivel-v1` (sin entrevista): BDNS ya verificada (`src/bdns_sweep.py`); cuatro fuentes más en `sources.json`, tabla `datasets`, primera serie propia descargable con método.

## Semana 4
- [ ] `crm-leads-v1` (entrevista 5): `/crm`, puntuación nocturna `/leads-puntuar`.
- [ ] `notas-de-prensa-v2` (sin entrevista): valoración IA y difusión opcional, pago en MOVO (Stripe), segmento «recibir comunicados».

## Semanas 5–7
- [ ] `conocimiento-v1` (entrevista nº 11): proceso `moticias` en el motor de conocimiento de `movo-es/movo` (migración en ESE repositorio, con sus reglas), canales de MOTICIAS, piezas como fuentes secundarias reputadas, búsqueda semántica (`pgvector` + Voyage) filtrada por `fuente_usable()`, `/conocimiento-ingesta`, consulta con citas en `app.moticias.com/conocimiento` (corporativa) y API para Amarantia.

## Semanas 8–10
- [ ] `ediciones-a-medida-v2` (entrevista nº 12): perfiles, selector, página privada, correo, PDF con documento de revisión, `widget.js`; tres asociaciones piloto.

## Semanas 11–15
- [ ] `amarantia-plus-v1` (entrevista nº 15): `planes`, `audiencias`, `secuencias`, `ejecuciones`, `envios`, `aprobaciones`; primer plan piloto; simulacro con informe; contrato de encargado.

## Semanas 16–17
- [ ] `contactos-quien-decide-v1` (sin entrevista): `/quien-decide` para corporativa, `/quien-decide-actualizar` mensual, exportación bajo contrato.
- [ ] `asesor-v1` (sin entrevista): aceptación de propuestas desde el móvil, métricas de Ghost y Search Console.
- [ ] `/cuadro-de-mando` mensual (día 12).

## Semanas 18–20
- [ ] `publicidad-promocion-v1` (entrevista 6): huecos operativos, `/anunciantes`, primer patrocinio ofrecido.

## Semanas 21–23
- [ ] `vertical-turismo-v1` (entrevista 9): primera edición de prueba de «viajar en grupo».

## Al cerrar cada hijo
- [ ] Deltas fundidos en `openspec/specs/`; `docs/` y `CLAUDE.md` al día; línea en el informe del asesor del lunes siguiente.
