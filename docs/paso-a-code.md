# MOTICIAS · Paso a Claude Code: cómo seguir construyendo con entrevistas OpenSpec (7 de noviembre de 2026; orden revisado el 8)

Respuesta corta: todo lo que hay que saber ya está en este repositorio; Claude Code lo lee al abrirlo (`CLAUDE.md`). A partir de ahora cada funcionalidad se construye como un cambio OpenSpec: una entrevista corta (`/opsx:explore`) que fija las decisiones, una propuesta con spec, diseño y tareas (`/opsx:propose`), la construcción (`/opsx:apply`) y el archivo (`/opsx:archive`). El cambio grande `plataforma-v1` es el mapa; se ejecuta troceado en cambios pequeños, uno por capacidad, en el orden de abajo. Nada se hace desde el ordenador de Rainer: Claude Code en la nube con el repositorio `movo-es/moticias`.

## 1. Abrir el repositorio en Claude Code (una vez)

1. En claude.ai → **Code** (o la app de escritorio → Code) → nueva sesión → repositorio `movo-es/moticias` (cuenta de GitHub ruphoff@avionline.es, la misma que MOVO). Si no aparece, pulsa «añadir repositorio» y búscalo por nombre; el acceso de GitHub ya está concedido a la organización `movo-es`.
2. La primera sesión lee sola `CLAUDE.md`. Comprueba que lo ha hecho pidiéndole: «Resume en cinco líneas qué es MOTICIAS, qué reglas no se pueden romper y qué cambio está en curso». Si contesta bien, está orientada.
3. Instala OpenSpec dentro del repositorio (pégalo tal cual en la sesión de Code; lo ejecuta ella):

```
cd /home/claude/moticias && npm install -g @fission-ai/openspec@latest && openspec init
```

   `openspec init` detecta la carpeta `openspec/` existente (tiene ya la estructura que la herramienta espera: `specs/<capacidad>/spec.md` y `changes/<cambio>/{proposal,design,tasks}.md` + `specs/`) e instala los comandos `/opsx:*`. Si pregunta qué herramienta de IA, elige Claude Code; si pregunta por el perfil, el básico (`core`: explore, propose, apply, sync, archive). Después, un commit: «OpenSpec instalado».
4. Para comprobarlo: `/opsx:explore` y escribe «¿Qué cambios hay abiertos?». Debe nombrar `plataforma-v1`.

Si `openspec init` no funcionara en la nube (sin Node o sin permisos), no pasa nada: el método sigue siendo el mismo a mano. Los comandos equivalentes son: explorar = «entrevístame sobre <capacidad> siguiendo `docs/paso-a-code.md § 3`»; proponer = «escribe `openspec/changes/<nombre>/` con proposal, design, tasks y specs»; aplicar = «ejecuta `tasks.md` de <nombre> marcando casillas»; archivar = «mueve <nombre> a `openspec/changes/archive/AAAA-MM-DD-<nombre>/` y funde sus deltas en `openspec/specs/`».

## 2. Reglas de trabajo en Code

- Un cambio = una capacidad = una carpeta en `openspec/changes/`. `plataforma-v1` no se aplica entero: cada entrevista crea un cambio hijo (`sala-de-redaccion-v1`, `campanas-tematicas-v1`, …) que toma su spec de `plataforma-v1/specs/<capacidad>/spec.md`, la afina con las respuestas y se construye por separado. Cuando todos los hijos están archivados, se archiva `plataforma-v1`.
- Un cambio toca a la vez spec, documentación (`docs/`), código y comando (`.claude/commands/`) que correspondan; nunca uno solo. `CLAUDE.md` se actualiza solo si cambia una regla de siempre o el mapa.
- Nada específico de MOTICIAS en el código: va a `verticals/<id>.json`. Toda tabla lleva `vertical_id`.
- No se toca `portal/` ni `hemeroteca/` fuera de un cambio OpenSpec; no se borra contenido publicado.
- Claves y secretos solo como variables de entorno (Vercel, tarea programada): `GHOST_ADMIN_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, …; nunca en el repositorio.
- Cada tarea de `tasks.md` termina con una verificación ejecutada (migración aplicada dos veces, test, página abierta) y un commit con mensaje en español. `git push` al cerrar cada sesión.
- Rainer revisa desde el móvil: cada cambio deja al final de `proposal.md` un bloque «Qué verás tú» con la URL o la pantalla que puede comprobar.

## 3. Las entrevistas, en orden

Cada entrevista es una conversación corta (10–15 preguntas como mucho, de una en una, con la opción recomendada marcada) que termina en `/opsx:propose <nombre>`. Las preguntas de abajo son las que faltan por decidir; lo ya decidido está en `docs/estrategia.md`, `openspec/changes/plataforma-v1/design.md` y `verticals/movilidad.json`, y la entrevista no debe volver a preguntarlo. Cómo arrancar cada una, en Code:

```
/opsx:explore
Entrevístame para el cambio <nombre> de MOTICIAS. Lee antes CLAUDE.md, docs/paso-a-code.md § 3 (la entrevista <n>), openspec/changes/plataforma-v1/design.md y la spec correspondiente en openspec/changes/plataforma-v1/specs/. Pregunta de una en una, solo lo que no esté decidido, con tu recomendación. Al terminar, resume las decisiones y pásalas a /opsx:propose <nombre>.
```

### Orden vigente desde el 8-11-2026 (estrategia 2027)

`docs/estrategia-2027.md § 5` manda sobre la numeración de abajo. Un cambio por semana; «sin entrevista» significa que Code propone y aplica a partir de la spec y solo pregunta si encuentra una decisión no cubierta. Las specs de los módulos nuevos están en `openspec/changes/plataforma-2027/specs/`.

| Semana | Cambio | Entrevista |
|---|---|---|
| 46 (10–16 nov) | `publicar-en-ghost-v1` | nº 1, hecha el 8-11 (`openspec/changes/publicar-en-ghost-v1/`): Code aplica `tasks.md` |
| 47 | `notas-de-prensa-v1` | nº 10 (corta) |
| 48 | `sala-de-redaccion-v1` | nº 3 |
| 49 | `sensores-v1` | sin entrevista |
| 50 | `campanas-tematicas-v1` | nº 2 (la semilla de «Quién decide» ya está hecha) |
| 51–52 | `suscripciones-v1` | nº 4 |
| 1–2 (ene 2027) | `amarantia-auscultador-v1` (adelantado: interés de un cliente) | nº 14 |
| 3 | `motor-envios-v1` · `fuentes-segundo-nivel-v1` | nº 13 · sin entrevista |
| 4 | `crm-leads-v1` · `notas-de-prensa-v2` | nº 5 · sin entrevista |
| 5–7 | `conocimiento-v1` (extiende el motor de MOVO; `docs/estrategia-2027.md § 4.5`) | nº 11 |
| 8–10 | `ediciones-a-medida-v2` | nº 12 |
| 11–15 | `amarantia-plus-v1` | nº 15 |
| 16–17 | `contactos-quien-decide-v1` · `asesor-v1` | sin entrevista · sin entrevista (la nº 8 queda como guion) |
| 18–20 | `publicidad-promocion-v1` | nº 6 |
| 21–23 | `vertical-turismo-v1` | nº 9 |

Decisiones del 8-11 que ninguna entrevista vuelve a preguntar: sector = movilidad + transporte + logística («gestión y administración» como ángulo); canales = Brevo para correo, SMS y WhatsApp (voz solo si un cliente de PLUS la pide, con Twilio); conocimiento = extender el motor de `movo-es/movo`, no construir otro; www.moticias.com canónico; el tema propio actual se pule, no se rehace; repositorio público por decisión de Rainer (sin claves ni datos personales dentro).

Para los cambios de `plataforma-2027`, el mensaje de arranque lee además `docs/estrategia-2027.md § 4.x` y la spec en `openspec/changes/plataforma-2027/specs/<módulo>/`.

### Entrevista 1 · `publicar-en-ghost-v1` (fase 1) — HECHA el 8-11-2026
Respuestas y tareas en `openspec/changes/publicar-en-ghost-v1/` (proposal, design, tasks, spec). Lo de abajo queda como guion original.
Spec base: `openspec/specs/publicacion-ghost/spec.md` y `src/ghost_publish.py`.
Decidir: plan de Ghost(Pro) contratado y subdominio final; dominio principal `www.moticias.com`; tema de Ghost (uno de serie adaptado o propio con huecos señalizados; recomendado: de serie con inyección de bloques por código hasta la fase 4); cómo se representan en Ghost las secciones y subsectores (etiquetas internas `#tierra` + etiquetas públicas); qué pasa con el portal-artefacto cuando Ghost esté en marcha (se mantiene como espejo un mes; después, solo hemeroteca); textos legales a nombre de Avionline S.L. (quién los redacta y dónde viven: `data/settings/legal.json`); `llms.txt`, sitemap y Search Console; cuándo entra el paso 7 quater (publicador) en la rutina diaria y en qué estado publica (`published` las rutinarias, `draft` las pendientes).
Entregable: las 74 piezas en moticias.com, rutina publicando sola, variables de entorno en la tarea programada.

### Entrevista 2 · `campanas-tematicas-v1` (campaña PMST ya activa)
Spec base: `openspec/changes/plataforma-v1/specs/campanas-tematicas/spec.md` y `data/campanas/movilidad-al-trabajo-pmst.json`.
Decidir: verificación de la fecha gancho en el BOE (quién, cuándo; hasta entonces `date_verified: false`); cómo se muestra el bloque de campaña en Ghost sin sala de redacción (etiqueta + página pilar + fragmento en el tema); qué descargable propio ofrece la campaña (guía, lista de comprobación, estimación de centros obligados) y dónde vive; CTA y página de aterrizaje en movo.es/pmst (existe, qué recoge); si la campaña admitiría un patrocinador externo y a qué precio; KPI que se pueden medir ya sin Supabase (Ghost: lecturas y altas; UTM: clics) y cuáles esperan a la fase 3; quién es `owner`.
Entregable: campaña visible en moticias.com, piezas con `campaign`, informe de revisión semanal del asesor.

### Entrevista 3 · `sala-de-redaccion-v1` (fase 2)
Spec base: `openspec/changes/plataforma-v1/specs/sala-de-redaccion/spec.md`.
Decidir: proyecto Supabase (nuevo `moticias` o el de MOVO con esquema propio; recomendado: nuevo, por separación de datos personales); autenticación (correo con enlace mágico; Rainer superadmin; segundo usuario editor); dónde vive la aplicación (`moticias.com/redaccion` vía proxy en Ghost no es posible: Vercel con `redaccion.moticias.com`, única excepción a «sin subdominios» por ser herramienta privada, o `movo.es/moticias-redaccion`); pantallas mínimas de la v1 (cola de pendientes con vista previa, Publicar/Retirar/Editar bloques, reordenar portada, lista de campañas); cómo escribe la sala en el repositorio (commit por API de GitHub desde la app o escritura en Supabase + sincronización por la rutina; recomendado: la sala escribe `editorial_items` y la rutina de la mañana reconcilia y hace commit); notificaciones (correo o push al cerrar edición con las piezas pendientes); registro de cambios (quién publicó o retiró qué y cuándo).
Entregable: aprobar, retirar y editar desde el móvil; migración 001 aplicada; RLS por rol (migración 002).

### Entrevista 4 · `suscripciones-v1` (fase 3)
Spec base: `openspec/changes/plataforma-v1/specs/suscripciones/spec.md`.
Decidir: niveles y precios (lector gratis; profesional y corporativa: cifras de `docs/plan-moticias-com.md` o nuevas); qué contenido es de pago desde el primer día (recomendado: todo abierto 30 días, después análisis, radar, licitaciones y datos propios para profesional; alertas, edición a medida y usuarios múltiples para corporativa); formulario de alta con los cinco campos (organización, cargo, modos, comunidades, licita) y dónde se guarda (campos de miembro de Ghost + `contacts`); centro de preferencias; consentimientos separados (boletín, ofertas del grupo); envío del boletín (Ghost newsletter; Brevo solo para campañas comerciales); periodo de prueba y facturas (Stripe vía Ghost; datos de Avionline S.L.).
Entregable: alta, pago y boletín funcionando; primeras cien altas con perfil.

### Entrevista 5 · `crm-leads-v1` (fase 3)
Spec base: `openspec/changes/plataforma-v1/specs/crm-leads/spec.md`.
Decidir: sincronización Ghost → `contacts` (webhook de Ghost o lectura nocturna por Admin API; recomendado: nocturna); qué eventos se capturan (aperturas y clics del boletín, descargas, CTA con UTM, altas de alertas); fórmula de puntuación por solución (pesos por segmento, tema, campaña, recencia) y umbral de lead; quién recibe el aviso de lead y por qué canal (correo a Rainer; después, al comercial); exportación (CSV) y relación con el CRM de MOVO/Movenbus si existe (¿HubSpot, Airtable, ninguno?); retención de datos y textos de privacidad.
Entregable: `/crm` con leads por solución y por campaña; primer informe de leads de la campaña PMST.

### Entrevista 6 · `publicidad-promocion-v1` (fase 4)
Spec base: `openspec/changes/plataforma-v1/specs/publicidad-promocion/spec.md` y `docs/gestores-portal.md`.
Decidir: huecos reales en el tema de Ghost (cuáles de los definidos se implementan en v1); tarifas (patrocinio de sección, banner, contenido patrocinado, campaña patrocinada, edición a medida); etiquetas y declaración de intereses (texto y página); flujo comercial (quién vende, contrato, factura desde Avionline S.L.); panel `/anunciantes` mínimo (campañas, inventario, impresiones y clics); autopromoción del grupo por defecto (`data/ads/`), rotación y peso; relación con las campañas temáticas (`campana_id`).
Entregable: huecos operativos con autopromoción; primer patrocinio ofrecido a una asociación.

### Entrevista 7 · `sensores-amarantia-v1` (fase 5)
Spec base: `openspec/changes/plataforma-v1/specs/sensores/spec.md`.
Decidir: tabla `senales` en el Supabase de MOTICIAS o en un proyecto común del grupo (recomendado: común, porque la leen tres productos); entidades vigiladas de Amarantia (lista inicial y quién la mantiene); relación con el hub Inteligencia (Airtable `appBS92rDurXwwDuv`): migrar a `senales` o sincronizar; barrido extra de mediodía (13:30) como tarea programada; formato de alerta para Amarantia (umbral de `relevance`, sentimiento negativo, canal: correo, Slack, Airtable); qué parte queda en modelo local (información reservada) y qué no.
Entregable: `/sensores` escribiendo en `senales`; primera alerta de Amarantia por entidad.

### Entrevista 8 · `asesor-v1` (ya corre; afinar)
Spec base: `openspec/changes/plataforma-v1/specs/asesor-visibilidad/spec.md` e informes en `docs/asesor/`.
Decidir: a partir del primer informe real, qué categorías sobran o faltan; cómo se aceptan propuestas (desde el móvil: `advisor_items.status`); cómo una propuesta aceptada se convierte en tarea (cambio OpenSpec, pieza encargada a la rutina, acción comercial); métricas de audiencia que el asesor podrá leer (Ghost, Search Console, Supabase).
Entregable: panel `/asesor` o, hasta la sala, el informe semanal con casillas en el propio fichero.

### Entrevista 9 · `vertical-turismo-v1` (fase 6)
Spec base: `openspec/changes/plataforma-v1/specs/verticales/spec.md` y `verticals/turismo.json`.
Antes de la entrevista: el contenido del proyecto «viajar en grupo» (Rainer lo pega en la sesión o lo exporta desde ese proyecto) a `verticals/turismo.json`.
Decidir: nombre, dominio y marca; secciones, subsectores, rotación de análisis; fuentes y entidades; segmentos y soluciones (Movenbus para organizadores de grupos, …); tareas programadas propias (hora, modelo); `data/` por vertical (`data/<vertical>/` o repositorio aparte; recomendado: `data/turismo/` en este repositorio mientras el código sea común).
Entregable: primera edición de prueba del segundo vertical sin tocar código.

### Entrevista 10 · `notas-de-prensa-v1` (semana 47; corta)
Spec base: `openspec/changes/plataforma-2027/specs/notas-de-prensa/spec.md` y `docs/estrategia-2027.md § 4.1`.
Decidir: nombre público de la sección (recomendado: «Notas de prensa»); verificación del emisor (recomendado: correo de dominio corporativo o enlace de confirmación); plazo de publicación (recomendado: mismo día laborable si llega antes de las 14:00); adjuntos permitidos (PDF e imágenes con derechos declarados); texto de la marca «Comunicado de empresa»; si las notas del grupo se publican igual (recomendado: sí, marcadas); quién vacía el buzón (agente `/prensa-buzon` a las 09:30 y 15:30).
Entregable: sección en moticias.com, formulario, buzón `prensa@moticias.com`, ficha de organización, primera nota publicada.

### Entrevista 11 · `conocimiento-v1` (semanas 5–7 de 2027)
Spec base: `openspec/changes/plataforma-2027/specs/conocimiento/spec.md` y `docs/estrategia-2027.md § 4.5`. Antes de la entrevista, Code lee en `movo-es/movo`: `supabase/migrations/097_el_fondo_documental.sql`, `109_el_motor_de_conocimiento.sql`, `lib/conocimiento/`, `lib/consulta/buscar.js` y `docs/CONOCIMIENTO-MOVILIDAD.md`.
Decidido el 8-11: se extiende el motor de MOVO (proceso `moticias`), no se construye otro. Decidir: dónde corre la búsqueda semántica (recomendado: `pgvector` en el Supabase de MOVO, función `security definer` cerrada); si el proceso `moticias` comparte canales con `pmst` (recomendado: canales propios en la misma tabla); corpus inicial (recomendado: Ley 9/2025 y desarrollo, piezas de MOTICIAS, BOE consolidado de transporte); quién aprueba la incorporación de fuentes propuestas; proveedor de embeddings (recomendado: Voyage); límites de consulta por nivel (recomendado: 50 al mes en corporativa, ampliable); formato de cita (recomendado: fuente, artículo o página, fecha de validez); si la consulta se expone por API a MOVO desde el primer día.
Entregable: esquema `conocimiento`, `/conocimiento-ingesta`, consulta IA con citas en `app.moticias.com/conocimiento`.

### Entrevista 12 · `ediciones-a-medida-v2` (semanas 8–10)
Spec base: `openspec/changes/plataforma-2027/specs/ediciones-a-medida/spec.md`, `docs/estrategia-2027.md § 4.6`, `src/selector.py`, `src/empaquetador.py`, `app/public/widget.js`.
Decidir: clientes piloto (tres asociaciones: nombres); cadencia por defecto (recomendado: quincenal para asociaciones, semanal para empresas); plantilla del PDF (recomendado: la de `src/empaquetador.py` con cabecera del cliente); quién revisa el documento colaborativo (recomendado: redactor y un contacto del cliente); contenido del cliente: ¿por formulario, por correo o por la sala?; marca del widget (texto y enlace); métricas que se enseñan al cliente (lecturas, clics, altas).
Entregable: perfiles, página privada, correo, PDF con revisión previa, widget en una web amiga.

### Entrevista 13 · `motor-envios-v1` (semana 3 de 2027)
Spec base: `openspec/changes/plataforma-2027/specs/motor-envios/spec.md` y `docs/estrategia-2027.md § 4.4`.
Decidido el 8-11: todo en Brevo (correo, SMS, WhatsApp); voz fuera de la v1. Decidir: remitentes por canal (correo `alertas@moticias.com`; SMS con remitente alfanumérico «MOTICIAS» o el del cliente; WhatsApp: número de Avionline o del cliente); plantillas iniciales (alerta de licitación, alerta de señal, comunicado, paso de PLUS); política de bajas y de horario (recomendado: nada no urgente entre 22:00 y 8:00); acuses (recomendado: enlace en correo y SMS, botón en WhatsApp, tecla en voz); registro y retención (recomendado: 24 meses).
Entregable: envío a un segmento por correo, SMS y WhatsApp con acuses y registro; alertas de licitaciones por comunidad.

### Entrevista 14 · `amarantia-auscultador-v1` (semanas 1–2 de 2027, adelantada; sustituye a la nº 7)
Spec base: `openspec/changes/plataforma-2027/specs/auscultador/spec.md`, `plataforma-v1/specs/sensores/spec.md` y `docs/estrategia-2027.md § 4.3`.
Decidir: primer cliente o entidades propias del grupo para arrancar; fuentes del anillo 2 que se activan (recomendado: Bluesky, Reddit, YouTube, Google News, Telegram público); umbrales de pico y tendencia (recomendado: 3 desviaciones a 6 horas; pendiente a 14 días); niveles y quién recibe cada uno; qué llega a la redacción como «posible noticia grande» (recomendado: nivel atención o crisis sobre cualquier entidad del sector); si se contrata una herramienta de escucha externa para X (recomendado: no hasta que un cliente lo pague); relación con el hub Inteligencia (Airtable `appBS92rDurXwwDuv`): migrar o sincronizar.
Entregable: entidades, línea base, alertas con niveles, panel `app.moticias.com/amarantia`, aviso por canal.

### Entrevista 15 · `amarantia-plus-v1` (semanas 11–15)
Spec base: `openspec/changes/plataforma-2027/specs/plus/spec.md` y `docs/estrategia-2027.md § 4.4`.
Decidir: cliente piloto y escenario del primer plan (recomendado: interrupción del servicio o accidente sin víctimas); audiencias y canales del piloto; quién aprueba cada paso (recomendado: dos personas designadas por el cliente, cualquiera de las dos); regla de avance por defecto (recomendado: 80 % de acuses o 20 minutos); contenido del flash público y lista de medios; fecha del primer simulacro; contrato de encargado del tratamiento (plantilla a nombre de Avionline).
Entregable: plan piloto, secuencia con aprobación por paso, simulacro con informe.

## 4. Qué hace Rainer en cada entrevista

Contestar a las preguntas (una por una, en el móvil vale), leer el «Qué verás tú» de la propuesta, y decir «aplica» o pedir cambios. Nada más. Si en una entrevista aparece algo que cambia una regla de siempre (firma, aprobación, fuentes, borrado), Code debe decirlo explícitamente y tocar `CLAUDE.md` en el mismo cambio.

## 5. Primer mensaje para la sesión de Code (pegar tal cual)

```
Lee CLAUDE.md, docs/paso-a-code.md y docs/estrategia-2027.md § 5 y § 6. Confirma en cinco líneas qué es MOTICIAS, qué reglas no se rompen, qué cambios están abiertos y qué te toca esta semana. Si OpenSpec no está instalado, instálalo (sección 1, paso 3) y haz commit. La entrevista 1 ya está hecha: aplica openspec/changes/publicar-en-ghost-v1/tasks.md en orden, una tarea por commit con su verificación, y para y pregúntame solo si una tarea exige una decisión que no está en la propuesta. Las variables GHOST_URL y GHOST_ADMIN_KEY tienen que estar en el entorno; si no están, pídemelas y no las escribas nunca en el repositorio.
```
