# Diseño: plataforma-v1

## Decisiones de arquitectura

**D1. Tres piezas, un solo origen.** El repositorio guarda reglas y contenido (fuente de verdad). Supabase guarda lo que cambia con cada visita o interacción: usuarios, CRM, señales, métricas, estado de aprobación. Ghost sirve la web pública, los boletines y las suscripciones de pago. Ningún dato vive en dos sitios con dos dueños: el contenido se publica del repo a Ghost; los miembros se leen de Ghost al CRM; las señales nacen en los agentes y se escriben en Supabase.

**D2. Misma pila que MOVO.** Next.js App Router + Supabase + Vercel, código en GitHub (`movo-es/moticias`, carpeta `app/`). Razón: Rainer ya opera MOVO así, con auditoría de seguridad semanal y reglas de despliegue conocidas; se reutilizan patrones (RLS, roles, middleware, cabeceras) y se evita mantener dos formas de hacer lo mismo.

**D3. Multi-vertical desde el esquema.** Toda tabla de negocio lleva `vertical_id` (`movilidad`, `turismo`, …). Toda consulta filtra por vertical. La configuración (`verticals/<id>.json`) se carga en Supabase (`verticals`) y la sala de redacción la lee de ahí; el repositorio es su origen.

**D4. Agentes = comandos de Claude Code + tareas programadas.** Cada agente es un comando en `.claude/commands/` (texto versionado) que una tarea programada invoca con el repositorio clonado. Los agentes escriben en el repositorio (contenido) y en Supabase (señales, propuestas, métricas), nunca directamente en Ghost salvo el publicador.

**D6. Campañas temáticas como eje de coordinación.** Una campaña temática (`data/campanas/<id>.json`, estado en `campanas_tematicas`) une en un solo objeto el plan editorial sobre un tema con fecha, el peso que los agentes le dan, la solución que se ofrece a quien tiene ese problema, la monetización (sin publicidad, patrocinada, banner, mixta) y los KPI. Orienta la selección, nunca el tratamiento; la monetización vive en los huecos y en el bloque de campaña, señalizada. Es el mecanismo para «trabajar especialmente» un tema cuando se acerca un plazo (PMST, una gran licitación, una transposición) y medir si ha traído leads.

**D5. Promoción fuera del texto.** La relación pieza ↔ solución se modela como dato (`relaciones_solucion`: pieza, solución, motivo, segmento) y la interfaz la muestra en huecos señalizados. El cuerpo editorial no la contiene.

## Modelo de datos (Supabase, esquema `public`, todas con `vertical_id` y RLS)

- `verticals` (id, name, config jsonb, updated_at).
- `editorial_items` (id = id del JSON en `data/`, vertical_id, kind, status: borrador | pendiente | publicado | retirado, priority, featured, approved_by, approved_at, ghost_post_id, ghost_url, published_at). El contenido sigue en el repo; aquí solo el estado y la prioridad.
- `contacts` (id, vertical_id, email, name, org_id, role, source: ghost | brevo | formulario | manual, consent_newsletter, consent_group_offers, consent_at, tier: lector | profesional | corporativa | anunciante, ghost_member_id, created_at).
- `organizations` (id, vertical_id, name, type: operador | administracion | consorcio | asociacion | consultora | industria | campus | prensa | otro, region, size, licita bool, website).
- `interests` (contact_id, modo, region, topic, weight).
- `events` (id, contact_id, kind: open | click | download | alert | visit | reply | request, item_id, topic, at, meta jsonb).
- `leads` (id, contact_id, segment_id, solution: MUFMI | MOVENBUS | MOVO | PLANES, score, reason, status: nuevo | contactado | reunión | propuesta | ganado | perdido, owner, updated_at).
- `campanas_tematicas` (id = id del JSON en `data/campanas/`, vertical_id, name, topic, hook_date, hook_verified, start, end, status: prevista | activa | cerrada, segment_id, solution, monetization: sin-publicidad | patrocinada | banner | mixta, sponsor_advertiser_id, kpis jsonb, results jsonb, owner). El plan editorial, las palabras clave y las creatividades siguen en el JSON del repo; aquí el estado y los resultados.
- `advertisers` (id, org_id, contact_id, status) · `campaigns` (id, advertiser_id, campana_id → temática opcional, type: patrocinio | banner | contenido | edicion-a-medida, slots[], start, end, amount_eur, status, utm) · `placements` (campaign_id, slot, item_id, impressions, clicks).
- `editorial_items.campana_id`, `events.campana_id`, `leads.campana_id`, `senales.campana_id`: la etiqueta que permite medir cada campaña de punta a punta (pieza → lectura → descarga → lead).
- `custom_editions` (id, name, owner_org_id, filters jsonb, layout, visibility, schedule) — las ediciones a medida y blogs de `docs/gestores-portal.md`.
- `senales` (id, vertical_id, at, source_url, source_name, kind: noticia | norma | licitacion | nombramiento | incidente | riesgo | buena-practica | idea, entities text[], scope, sentiment, relevance 0–1, summary, raw jsonb, used_by text[]: moticias | amarantia | inteligencia) — compartida con Amarantia e Inteligencia.
- `advisor_items` (id, vertical_id, week, category: visibilidad | credibilidad | conocimiento | contactos | canales | ingresos, title, instruction, priority, effort, status: propuesto | aceptado | hecho | descartado, evidence).
- `metrics_daily` (vertical_id, day, subscribers_by_tier jsonb, opens, clicks, leads_new, leads_by_solution jsonb, revenue_subs, revenue_ads).

## Interfaz de la sala de redacción (rutas)

`/redaccion` (cola: pendientes de aprobar, con vista previa y botón Publicar/Retirar/Reordenar, usable con el pulgar) · `/redaccion/pieza/<id>` (editar bloques, foto, estado, relación con soluciones) · `/redaccion/ediciones` (del día y a medida) · `/crm` (contactos, organizaciones, leads por solución, exportar) · `/campanas` (lista y `/campanas/<id>`: plan frente a publicado, lecturas, descargas, altas, leads por solución, organizaciones que han interactuado; botones Activar / Cerrar / Cambiar monetización) · `/anunciantes` (campañas publicitarias, huecos, inventario, importes) · `/asesor` (propuestas de la semana, aceptar/hecho/descartar) · `/senales` (lo que ven los sensores; filtro por entidad para Amarantia) · `/metricas`. Roles: superadmin (Rainer), editor, comercial, lector-anunciante (solo sus campañas).

## Flujos

1. Edición diaria → piezas en `data/` + `editorial_items` en `pendiente` (o `publicado` mientras no se active la aprobación) → publicador a Ghost → métricas.
2. Lector se suscribe en Ghost → webhook/lectura diaria → `contacts` + `interests` → eventos de Brevo/Ghost → `events` → puntuación nocturna → `leads` por solución → aviso al comercial.
3. Sensores (cada edición y un barrido extra a las 13:30) → `senales` → MOTICIAS (piezas, radar), Amarantia (alertas por entidad), Inteligencia (canales).
4. Asesor semanal → `advisor_items` → aviso al superadmin → acciones aceptadas se convierten en tareas de los agentes o en cambios OpenSpec.
5. Campaña temática → `data/campanas/<id>.json` (alta con `/campana-tematica`) → la rutina diaria y los sensores la leen (peso, palabras clave, etiqueta) → piezas con `campaign` → bloque de campaña y huecos en Ghost → eventos y leads con `campana_id` → panel `/campanas/<id>` → informe de cierre.
