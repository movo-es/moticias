# Tareas: plataforma-2027

Este cambio es el mapa; no se aplica entero. Cada fila es un cambio hijo (`openspec/changes/<nombre>/`) que toma su spec de `specs/<módulo>/spec.md` de aquí o de `plataforma-v1`, la afina en la entrevista (si la hay) y se construye y archiva por separado. Las casillas se marcan al archivar el hijo. Orden y fechas: `docs/estrategia-2027.md § 5`.

## Semana 46 (10–16 nov 2026)
- [ ] `publicar-en-ghost-v1` (entrevista 1 de `docs/paso-a-code.md`): moticias.com con las 74 piezas, rutina publicando sola, legales a nombre de Avionline, campaña PMST visible. Repositorio puesto en privado.

## Semana 47
- [ ] `notas-de-prensa-v1` (entrevista corta, Anexo A.1): sección `/notas-de-prensa/`, formulario en `app.moticias.com/prensa/enviar`, buzón `prensa@moticias.com` vaciado por `/prensa-buzon`, ficha de organización, primera nota publicada.

## Semana 48
- [ ] `sala-de-redaccion-v1` (entrevista 3): proyecto Supabase `moticias`, migración 001, `app.moticias.com/redaccion` con cola de aprobación.

## Semana 49
- [ ] `sensores-v1` (sin entrevista): `/sensores` escribe en `senales`; tarea de mediodía 13:30; vista por entidad.

## Semana 50
- [ ] `campanas-tematicas-v1` (entrevista 2): `/campanas` con la campaña PMST.
- [ ] `quien-decide-semilla` (sin entrevista): tablas `cargos` y `cargo_fuentes` (migración 002) sembradas con los nombramientos ya publicados en `data/boletines/` y `data/articles/`.

## Semanas 51–52
- [ ] `suscripciones-v1` (entrevista 4): niveles en Ghost, alta con perfil, consentimientos separados (boletín · comunicados · ofertas del grupo), centro de preferencias.
- [ ] Tareas programadas: radar regulatorio (lunes 07:30), licitaciones de la semana (viernes 07:30), promo social (laborables 08:15).

## Semanas 1–2 (ene 2027)
- [ ] `fuentes-segundo-nivel-v1` (sin entrevista): cinco fuentes nuevas en `sources.json`, tabla `datasets`, primera serie propia descargable con método.
- [ ] `crm-leads-v1` (entrevista 5): `/crm`, puntuación nocturna `/leads-puntuar`.

## Semana 3
- [ ] `notas-de-prensa-v2` (sin entrevista): valoración IA y difusión opcional, pago en MOVO (Stripe), segmento «recibir comunicados».

## Semanas 4–6
- [ ] `conocimiento-v1` (entrevista nueva, A.2): esquema `conocimiento` compartido, migración 003 (`pgvector`), `/conocimiento-ingesta`, consulta IA con citas en `app.moticias.com/conocimiento` (corporativa) y API para MOVO.

## Semanas 7–9
- [ ] `ediciones-a-medida-v2` (entrevista nueva, A.3): perfiles, selector, página privada, correo, PDF con documento de revisión, `widget.js`; tres asociaciones piloto.

## Semanas 10–11
- [ ] `motor-envios-v1` (entrevista nueva, A.4): adaptadores Brevo (correo, SMS) y Twilio (WhatsApp, voz), plantillas, acuses, bajas, registro, secuencias en Vercel Workflow; alertas de licitaciones por comunidad.

## Semanas 12–13
- [ ] `amarantia-auscultador-v1` (entrevista nueva, A.5): `entities`, `baselines`, `alerts`; anillo 2 (Bluesky, Reddit, YouTube, Google News, Telegram público); `/auscultar` cada 2 horas; panel `app.moticias.com/amarantia`; primera entidad de cliente.

## Semanas 14–18
- [ ] `amarantia-plus-v1` (entrevista nueva, A.6): `planes`, `audiencias`, `secuencias`, `ejecuciones`, `envios`, `aprobaciones`; primer plan piloto; simulacro con informe; contrato de encargado.

## Semanas 19–20
- [ ] `contactos-quien-decide-v1` (sin entrevista): `/quien-decide` para corporativa, `/quien-decide-actualizar` mensual, exportación bajo contrato.
- [ ] `asesor-v1` (sin entrevista): aceptación de propuestas desde el móvil, métricas de Ghost y Search Console.
- [ ] `/cuadro-de-mando` mensual (día 12).

## Semanas 21–23
- [ ] `publicidad-promocion-v1` (entrevista 6): huecos operativos, `/anunciantes`, primer patrocinio ofrecido.

## Semanas 24–26
- [ ] `vertical-turismo-v1` (entrevista 9): primera edición de prueba de «viajar en grupo».

## Al cerrar cada hijo
- [ ] Deltas fundidos en `openspec/specs/`; `docs/` y `CLAUDE.md` al día; línea en el informe del asesor del lunes siguiente.
