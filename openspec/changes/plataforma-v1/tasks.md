# Tareas: plataforma-v1

Orden pensado para que cada paso produzca valor por sí solo. Las casillas se marcan al archivar.

## Fase 0 · Cimientos (hecho el 7-11-2026)
- [x] Repositorio como fuente de verdad; docs, specs, datos y scripts migrados.
- [x] `verticals/movilidad.json` y `verticals/turismo.json` (placeholder).
- [x] Comandos de agentes: `/edicion-diaria`, `/consejo-visibilidad`, `/radar-regulatorio`, `/licitaciones-semana`, `/sensores`, `/promo-social`.
- [x] `src/ghost_publish.py` con modo de prueba (`--dry-run`).
- [x] Tarea programada diaria redirigida al repositorio; tarea semanal del asesor creada.

## Fase 1 · Publicar en moticias.com (Ghost)
- [ ] Rainer: elegir plan Ghost(Pro), apuntar el dominio moticias.com, crear integración personalizada y pasar la Admin API key (se guarda como variable de entorno `GHOST_ADMIN_KEY`, nunca en el repo).
- [x] Sociedad titular y responsable del tratamiento: Avionline S.L. (7-11-2026).
- [ ] Textos legales (aviso legal, privacidad, cookies) a nombre de Avionline S.L.
- [ ] Publicar las 74 piezas existentes con `src/ghost_publish.py --all`; comprobar URL en subdirectorios, Schema.org, fuentes al pie, trazabilidad.
- [ ] Añadir `llms.txt`, `robots`, sitemap y alta en Search Console y Publisher Center.
- [ ] Integrar el publicador en `/edicion-diaria` (paso 7 quater).
- [ ] Campaña piloto «Movilidad al trabajo · PMST» (`data/campanas/movilidad-al-trabajo-pmst.json`): verificar en el BOE la fecha del plazo (`hook.date_verified`), publicar la página pilar y el bloque de campaña en Ghost (etiqueta de sección + página), hueco lateral con `casa-movo-pmst`.

## Fase 2 · Sala de redacción mínima (aprobación desde el móvil)
- [ ] Crear proyecto Supabase `moticias` y aplicar la migración 001 (tablas de `design.md`, RLS, roles).
- [ ] `app/`: Next.js con autenticación (Supabase Auth, correo), rol superadmin para Rainer, ruta `/redaccion` con cola de pendientes, vista previa y botones Publicar / Retirar / Reordenar.
- [ ] Desplegar en Vercel (proyecto `moticias`), dominio `redaccion.moticias.com` o `moticias.com/redaccion` (preferible subdirectorio si Ghost lo permite; si no, subdominio solo para la herramienta privada).
- [x] Política de aprobación: rutinarias directas con firma «G. Jordan»; críticas y análisis en `pendiente` con firma «Rainer» (7-11-2026). Pendiente: botón Editar/Retirar en la sala.

## Fase 3 · Suscripciones y CRM
- [ ] Niveles en Ghost: lector (gratis), profesional, corporativa; formulario de alta con los cinco campos; centro de preferencias.
- [ ] Sincronización Ghost → `contacts`/`interests`; eventos de aperturas y clics (Ghost o Brevo) → `events`.
- [ ] Puntuación nocturna → `leads` por solución del grupo; `/crm` con filtros por segmento y exportación.
- [ ] Alertas de licitaciones por comunidad y modo; calendario ICS de plazos.

## Fase 4 · Promoción discreta, campañas y publicidad
- [ ] `/campanas` y `/campanas/<id>` en la sala: plan frente a publicado, métricas, leads, botones Activar / Cerrar / Cambiar monetización; sincronización `data/campanas/` ↔ `campanas_tematicas`.
- [ ] Comando `/campana-tematica` probado de punta a punta (alta, plan, creatividades, informe de cierre en `docs/campanas/`).
- [ ] Etiqueta `campana_id` en eventos y leads; informe de cierre con resultados frente a `kpis`.
- [ ] `relaciones_solucion` y huecos señalizados en Ghost (tema propio o inyección por API) según `docs/gestores-portal.md`.
- [ ] `/anunciantes`: campañas, inventario de huecos, importes, UTM.
- [ ] Ediciones a medida para tres asociaciones piloto (un mes gratis).

## Fase 5 · Sensores y Amarantia
- [ ] Tabla `senales` compartida; `/sensores` escribe en ella; barrido extra de mediodía.
- [ ] Vista por entidad vigilada para Amarantia; sincronización con el hub Inteligencia (Airtable `appBS92rDurXwwDuv`) o migración de ese hub a la misma tabla.

## Fase 6 · Segundo vertical
- [ ] Rellenar `verticals/turismo.json` desde el proyecto «viajar en grupo»; `data-turismo/` o `data/<vertical>/`; marca y dominio; primera edición de prueba.
