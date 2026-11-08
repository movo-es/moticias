# Capacidad: contactos «Quién decide» (delta)

## ADDED Requisito: cargos con fuente y vigencia
`cargos` (id, vertical_id, org_id, persona, cargo, desde, hasta, email_profesional, tel_profesional, verificado_en, vigente) y `cargo_fuentes` (cargo_id, tipo: boe | boletin | borme | web-oficial | comunicado, url, fecha). Nada sin fuente.

## ADDED Requisito: solo datos profesionales
Solo cargos públicos y datos de contacto profesional (art. 19 LOPDGDD). Información del derecho a oponerse en cada uso. Sin exportación masiva en el nivel profesional; exportación en corporativa bajo contrato con finalidad declarada.

## ADDED Requisito: semilla y actualización
Semilla desde los nombramientos ya recogidos en `data/boletines/` y `data/articles/`; `/quien-decide-actualizar` el día 1 de cada mes revisa vigencias con las fuentes de segundo nivel y marca lo caducado.

#### Escenario: cese publicado en un boletín
- CUANDO un boletín publica el cese de un cargo que figura vigente
- ENTONCES el cargo pasa a `vigente: false` con `hasta` y la fuente del cese, y queda la fila histórica.

## ADDED Requisito: consumidores
`app.moticias.com/quien-decide` (corporativa), `/crm` interno (comercial del grupo), listas de la sala de prensa y audiencias de PLUS.
