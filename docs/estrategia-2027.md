# MOTICIAS · Estrategia 2027: de portal de referencia a plataforma que se financia sola

Fecha: 8 de noviembre de 2026 (revisado la misma tarde con las respuestas de Rainer a las cinco preguntas, la entrevista 1 y su decisión sobre menciones del grupo y piezas bajo demanda). Origen: anotaciones manuscritas del director («Estrategia_2027», cuatro páginas) y su encargo del mismo día. Destino: `docs/estrategia-2027.md` en `movo-es/moticias`, que manda sobre esta copia. Complementa, no sustituye, a `docs/estrategia.md` (7-11-2026) y al cambio `plataforma-v1`.

Respuesta corta: MOTICIAS gana autoridad siendo la referencia informativa de movilidad, transporte y logística sin sobrecarga publicitaria; esa autoridad se convierte en ingresos por cinco vías (suscripción profesional, sala de prensa, revistas y ediciones a medida, datos y conocimiento premium, Amarantia) construidas sobre diez módulos reutilizables. Ghost muestra; el repositorio manda; Supabase guarda estado; Vercel ejecuta; los agentes de Claude Code trabajan. Nueve cambios OpenSpec entre noviembre de 2026 y junio de 2027, uno por semana de media, cada uno con algo visible desde el móvil.

## 0. Qué añaden las anotaciones a lo que ya existe

| Anotación (página) | Ya existe en `plataforma-v1` | Nuevo (este documento) |
|---|---|---|
| Noticias sin sobrecarga de publicidad; referencia informativa; SEO (1) | Estrategia, benchmark, huecos señalizados, `llms.txt`, Schema.org | Límite explícito de inventario publicitario; GEO como objetivo medible; «gestión y administración» como ángulo editorial |
| Embudo de productos propios sin etiquetar en exceso (1) | `relaciones_solucion`, campañas temáticas, autopromoción | Nada nuevo: se mantiene la regla «fuera del texto, siempre señalizado» |
| Artefactos reutilizables (1, 2) | Verticales por configuración | Catálogo de ocho módulos con dueño, spec y consumidores (§ 3) |
| Revistas corporativas con contenido del cliente y del sector; selector por tipo, sector, etiquetas y palabras clave (2) | `custom_editions`, blogs del portal | **Selector de contenidos** como módulo; perfil de cliente; contenido propio del cliente mezclado y marcado |
| Empaquetador periódico que genera revista en PDF con documento de revisión colaborativo (2) | — | **Empaquetador** (PDF, HTML, correo) con revisión en documento de Claude antes de emitir |
| Widget para incluir en cualquier web; coste y monetización si es gratis (2) | — | **Widget embebible** servido desde Vercel sobre la Content API de Ghost; análisis de coste (§ 4.6) |
| Amarantia: auscultador de sucesos sin confirmar, cambios de sentimiento repentinos frente a tendencia, rumores; aviso a clientes y a la redacción; humano en el bucle (3) | Tabla `senales`, comando `/sensores`, entidades vigiladas | **Auscultador**: fuentes sociales, línea base por entidad, detección de picos y de tendencia, estados de alerta, canales |
| Generador y difusor de notas de prensa: publicación gratuita, valoración opcional, envío a suscriptores que opten (4) | — | **Sala de prensa** completa; es la vía de entrada a las empresas «que se preocupan por tener algo que decir» |
| Inyector «PLUS»: flujos urgentes internos y a stakeholders por SMS, WhatsApp y llamada con o sin acuse; flash público; emisión a canales tradicionales, sector y redes (4) | — | **Motor de envíos** (compartido) y **PLUS** (planes, secuencias, aprobación humana, simulacros) |
| Acceso a información pública «y más oculta» (encargo) | BOE, TED, PLACSP, participación pública | **Fuentes de segundo nivel**: BDNS, transparencia, plenos, Congreso, CNMC, Tribunal de Cuentas… como datos propios |
| Bases de contactos y responsables actualizadas para premium (encargo) | «Quién decide» citado en la estrategia | **Contactos «Quién decide»** como módulo con agente de actualización y límites RGPD |
| Bases de conocimiento con interrogación inteligente, empezando por «conocimiento» (encargo) | — | **Conocimiento** como servicio común del grupo (MOVO, MOTICIAS, Amarantia) con consulta IA citada |

## 1. Tesis y financiación

**La tesis.** Un medio sectorial se financia sin vender su portada si tiene tres cosas: lectores profesionales que vuelven porque encuentran lo que no está en otro sitio (regulación, licitaciones, plazos, datos, nombramientos), empresas que quieren estar en él porque los lectores son sus clientes y sus reguladores, y una capa de servicios que el propio contenido hace creíbles. MOTICIAS tiene ya la primera pieza en construcción (74 reportajes de fondo, rutina diaria, hemeroteca). Este documento construye las otras dos.

**El cortafuegos.** La parte editorial no vende nada ni cita soluciones del grupo. La parte comercial (sala de prensa, revistas, patrocinios, Amarantia, datos) está señalizada y separada en la web, en los correos y en el equipo. Un comunicado de empresa nunca se convierte en noticia sin verificación independiente. Esta regla es la que permite cobrar: nadie paga por aparecer en un medio en el que todo el mundo aparece pagando.

**Las cinco vías de ingreso, en el orden en que pueden empezar a cobrar.** Precios como hipótesis para validar con los primeros clientes, no cifras de mercado.

| Vía | Qué se vende | A quién | Precio orientativo | Depende de |
|---|---|---|---|---|
| A. Sala de prensa | Publicación gratuita del comunicado en `/notas-de-prensa/`; **valoración** de novedad e impacto con propuesta de mejora; **difusión** a suscriptores que optaron y a redes | Direcciones de comunicación de operadores, industria, administraciones, asociaciones | Publicación 0 €; valoración 60–120 €; difusión 150–300 € por nota; bono anual 900–2.400 € | Ghost + formulario + buzón (semana 47) |
| B. Suscripción | Profesional: radar regulatorio, licitaciones con alertas, datos descargables, archivo completo. Corporativa: lo anterior más consulta IA al conocimiento, «Quién decide», usuarios múltiples, edición a medida | Técnicos y directivos; departamentos | Profesional 29–49 €/mes; corporativa 249–599 €/mes | Ghost miembros (dic) + conocimiento y contactos (feb) |
| C. Revistas y ediciones a medida | Edición periódica con cabecera del cliente (asociación, empresa), contenido del sector más el suyo, en web privada, correo y PDF; widget gratuito como gancho | Asociaciones, operadores grandes, consorcios, industria | Asociación 300–1.500 €/mes; empresa 150–600 €/mes; widget gratis con enlace | Selector + empaquetador (feb) |
| D. Datos y conocimiento | Series propias (licitaciones por comunidad, plazos, concesiones que vencen, nombramientos), informes trimestrales, API | Consultoras, industria, inversores, administraciones | Informe 300–900 €; API bajo contrato | Fuentes de segundo nivel (dic–ene) |
| E. Amarantia | Auscultación por entidad con alertas; PLUS: planes de comunicación de crisis con envíos secuenciados y acuse; simulacros | Operadores, gestores de infraestructuras, administraciones, empresas con exposición reputacional | Auscultación 300–900 €/mes por entidad; PLUS 500–2.000 €/mes según audiencias y canales; simulacro 900–3.000 € | Sensores (dic), auscultador (ene), motor de envíos (ene), PLUS (mar–abr) |

Más la publicidad limitada (patrocinio de sección, contenido patrocinado señalizado) ya definida en `docs/gestores-portal.md`, con un tope: nunca más de tres huecos de pago por página y ninguno sobre la apertura. Esa limitación es parte del producto.

**Umbral de autofinanciación.** Coste de explotación estimado: 450–900 € al mes (Anexo C). Se cubre, por ejemplo, con dos ediciones a medida de asociación (600 €), diez suscriptores profesionales (390 €) y un cliente de auscultación (500 €): 1.490 € al mes. Objetivo realista: alcanzarlo en el segundo trimestre de 2027; duplicarlo antes de fin de año. Lo que no cubre es el tiempo del director: ese se paga con los leads de MUFMI, MOVENBUS, MOVO y la nueva línea de planes de movilidad, que es para lo que nació MOTICIAS.

## 2. Arquitectura: qué hace cada plataforma

Principio: **Ghost muestra, el repositorio manda, Supabase guarda estado, Vercel ejecuta, los agentes trabajan.** Ningún dato tiene dos dueños.

Estado real el 8-11-2026 (comprobado): www.moticias.com ya sirve 62 piezas en Ghost(Pro) 6.75 con un tema propio, secciones, redirección del dominio sin `www`, y `llms.txt`, `llms-full.txt` y `.md` por pieza generados por Ghost. Lo que falta es versionar ese tema y reconciliar las 12 piezas pendientes de la firma del director: cambio `publicar-en-ghost-v1`.

| Capa | Plataforma | Qué hace | Qué no hace |
|---|---|---|---|
| Web pública, miembros, boletines | **Ghost(Pro)** en `moticias.com` | Piezas, secciones, páginas pilar, sala de prensa pública, niveles de suscripción y cobro, newsletters, Content API (lectura pública para el widget) | Lógica de negocio, CRM, cálculo; no se programa dentro de Ghost |
| Fuente de verdad | **GitHub `movo-es/moticias`** | Reglas, specs, configuración por vertical, contenido publicado (`data/`), comandos de los agentes, migraciones | Datos personales, claves, estado que cambia con cada visita |
| Agentes | **Tareas programadas de Claude Code** (clonan el repo, ejecutan un comando, hacen push) | Edición diaria, sensores, radar, licitaciones, asesor, ingesta de conocimiento, actualización de contactos, empaquetado de revistas | Nada interactivo en tiempo real |
| Estado y datos | **Supabase** (proyecto `moticias`; esquema compartido `grupo` para conocimiento y señales) | Postgres con RLS: estado editorial, contactos, organizaciones, leads, señales, alertas, planes PLUS, envíos y acuses, conocimiento con `pgvector`, métricas | Contenido editorial (vive en el repo y en Ghost) |
| Aplicación privada y API | **Next.js en Vercel** (`app/` del repo; `app.moticias.com`) | Sala de redacción, CRM, panel Amarantia, PLUS, consulta IA, «Quién decide», gestor de ediciones a medida, `widget.js`, formularios públicos, webhooks | SEO: lo público indexable está en Ghost |
| Secuencias durables | **Vercel Workflow** | Secuencias PLUS (paso, espera, acuse, aprobación humana, siguiente paso), campañas de difusión de notas, reintentos | Envío directo de mensajes (lo hacen los adaptadores) |
| Canales | **Brevo** para correo, SMS y WhatsApp Business (ya contratado; decisión del 8-11) · Ghost (newsletters editoriales) · Twilio solo si un cliente de PLUS pide llamadas de voz | Envíos, plantillas aprobadas, acuses, bajas | Decidir a quién se envía (lo decide el motor de envíos) |
| Inteligencia | **API de Claude** (valoración de notas, clasificación de señales y sentimiento, respuestas con citas) · **Voyage AI** (embeddings; Anthropic no los ofrece) · **Motor de conocimiento de MOVO** (`procesos`, `fuentes`, `fuente_usable()`, canales y hallazgos; `lib/conocimiento/anclaje.js`: el modelo no aporta hechos) | Lo que requiere lenguaje | Cálculo: cifras y fechas salen de datos, no del modelo |
| Fuentes | APIs del BOE, TED, PLACSP, INE, Eurostat; RSS verificados; Openverse; redes con API abierta (Bluesky, Reddit, YouTube, Telegram público, Mastodon); X solo si un cliente paga su API | Entrada de señales y documentos | LinkedIn no ofrece API de escucha: se cubre por buscadores y alertas |
| Información reservada (Amarantia) | Modelo local en el rack de Mac (plan ya anotado) | La parte clasificada, fuera de todo lo anterior | Nunca pasa por la nube |

**Dominios.** `moticias.com` y todo lo indexable en subdirectorios de Ghost. La aplicación privada y las zonas con sesión (sala de redacción, consulta IA, paneles de cliente) en `app.moticias.com`: es la única excepción a «sin subdominios», porque nada de lo que hay detrás de una contraseña suma autoridad temática. El widget se sirve desde `app.moticias.com/widget.js` pero enlaza a `moticias.com`.

**Una sola identidad.** Cuenta `ruphoff@avionline.es` (GitHub `movo-es`, Ghost, Vercel, Supabase). Claves solo como variables de entorno en Vercel y en las tareas programadas. El repositorio es público por decisión de Rainer (8-11-2026): por eso no contiene claves, datos personales ni perfiles de clientes reales; lo que sea de un cliente vive en Supabase.

## 3. Los diez módulos reutilizables

Cada módulo tiene una spec en `openspec/specs/<módulo>/`, código en `app/lib/<módulo>/` (TypeScript) o `src/<módulo>.py` (agentes), y una lista cerrada de consumidores. «Reutilizable» significa: lo usa más de un producto sin copiar código y se configura por vertical o por cliente, nunca por rama de código.

| Módulo | Qué hace | Consumidores | Configuración |
|---|---|---|---|
| 1. **Selector de contenidos** | Dada una consulta (tipo de pieza, sección, subsector, etiquetas, palabras clave, campaña, rango de fechas, relevancia, idioma) devuelve piezas, boletines, plazos y señales ordenados. Dos fuentes: `data/` (repo) y Content API de Ghost | Ediciones a medida, widget, empaquetador, boletines temáticos, difusión de notas, radar, asesor | `perfil` JSON por cliente o por vertical |
| 2. **Empaquetador** | Convierte una selección más contenido propio del cliente en revista (PDF con portada y sumario), página HTML privada y correo; antes de emitir crea un documento de revisión colaborativo (Claude Docs) para redactores y cliente | Revistas corporativas, ediciones de asociación, informe semanal ejecutivo, cuadro de mando mensual | Plantilla, cadencia, marca |
| 3. **Widget** | `<script>` que pinta en cualquier web una lista de titulares filtrada por el selector, con enlace a MOTICIAS y marca «Powered by» | Asociaciones, operadores, ayuntamientos, blogs; gancho de la vía C | Atributos `data-*` (sector, etiquetas, número) |
| 4. **Motor de envíos** | Envía mensajes a segmentos por canal (correo, SMS, WhatsApp, voz) con plantillas, estado por destinatario, acuses, bajas y registro; ejecuta secuencias con esperas, condiciones y aprobación humana | PLUS, difusión de notas de prensa, alertas de licitaciones y de señales, boletines de ediciones a medida | Canales y remitentes por cliente; plantillas aprobadas |
| 5. **Sensores y auscultador** | Barren fuentes y redes, escriben `senales`; calculan línea base por entidad (volumen y sentimiento a 30 días), detectan picos repentinos y cambios de tendencia, clasifican confirmado / sin confirmar / rumor; abren alertas | MOTICIAS (candidatas a pieza, aviso de «posible noticia grande»), Amarantia (alertas por entidad), hub Inteligencia de MOVO | Temas, entidades vigiladas, palabras de riesgo, umbrales por cliente |
| 6. **Conocimiento** | Gestor de fuentes y documentos con clasificación (primaria, secundaria reputada, sin confirmar), ponderación, fechas de incorporación, publicación y validez, estado (activa, desactivada, baneada, compartida); fragmentos con embeddings; consulta IA con citas y «no consta» | MOVO (PMST y futuros procesos), MOTICIAS corporativa, Amarantia, la nueva línea de planes | Colecciones por proyecto y por cliente |
| 7. **Contactos «Quién decide»** | Organizaciones, cargos y responsables con fuente y fecha de verificación; CRM privado (contactos, intereses, eventos, leads por solución); agente mensual de actualización desde nombramientos | Premium corporativa, comercial del grupo, difusión de notas (listas de prensa y de cargos), PLUS (audiencias de stakeholders) | Segmentos y soluciones del vertical |
| 8. **Sala de prensa** | Recepción de comunicados (formulario y buzón), ficha de la organización emisora, publicación marcada como comunicado, valoración IA opcional, difusión opcional, histórico por empresa | MOTICIAS (vía A), Amarantia (emisión a canales en una crisis), vertical turismo | Sección, etiquetas, tarifas |
| 9. **Gestor de productos propios y menciones** | Catálogo de productos del grupo con el contexto que les da entrada; puntúa cada pieza, escribe una mención señalizada («Nota de la casa») al pie y avisa al director por correo con enlace de edición | MOTICIAS (todas las piezas), ediciones a medida (con los productos del cliente), vertical turismo (Movenbus para grupos) | `data/productos/<id>.json` por vertical; declaración y etiqueta en el vertical |
| 10. **Buscador y piezas bajo demanda** | Búsqueda sobre lo publicado con veredicto; si no hay cobertura, encargo → investigación → pieza con el estándar de siempre, guardada para siempre | Suscripción profesional y corporativa (vía B), consulta IA (cuando no consta en el conocimiento, puede abrir un encargo), ediciones a medida | Cuota por nivel; fuentes del vertical |

Lo que ya está en `plataforma-v1` (sala de redacción, suscripciones, CRM, campañas temáticas, publicidad, asesor, verticales) se mantiene y se apoya en estos módulos: el CRM es el módulo 7; las ediciones a medida son 1 + 2 + 3; los sensores son el 5; la autopromoción de las campañas se apoya en el 9.

## 4. Los módulos nuevos en detalle

### 4.1 Sala de prensa (`notas-de-prensa-v1`)

**Actualización del 9-11-2026:** adelantado y ampliado por el cambio `sala-de-prensa-v1` (difusión a medios, boletines y redes con filtro de valor; asesor de comunicación virtual y recomendador honesto; base de contactos B2B y B2C; informe de repercusión verificado). Manda `openspec/changes/sala-de-prensa-v1/` sobre lo que sigue.

**Para qué.** Es la puerta de entrada a las empresas. Quien envía una nota deja organización, responsable de comunicación, correo y teléfono profesional: la base de contactos crece con quien tiene interés en hablar con el sector. Y la valoración de la nota es un servicio que ningún medio español ofrece.

**Lo que verá el usuario.** En `moticias.com/notas-de-prensa/`, una sección con los comunicados tal cual, cada uno con la marca «Comunicado de empresa · no es contenido editorial», la organización, la fecha y los documentos adjuntos. Un formulario de envío (en `app.moticias.com/prensa/enviar`, incrustado en la página de Ghost) y un buzón `prensa@moticias.com` (Hostinger Mail, ya conectado) que un agente vacía dos veces al día.

**Flujo.** Recepción → ficha de organización (alta o enlace a existente) → comprobación mínima (remitente de dominio corporativo o verificación por correo; sin esto no se publica) → publicación en Ghost con etiqueta interna `#comunicado` y autor «Comunicado» → aviso al emisor con enlace → opcional: valoración (novedad, impacto para cada segmento, claridad, datos que faltan, titular alternativo, a quién debería enviarse) que recibe solo el emisor → opcional: difusión a los suscriptores que marcaron «recibir comunicados» de ese sector, y a redes con la plantilla de `/promo-social` → la señal entra en `senales` como `kind: comunicado` y, si tiene valor informativo, en candidatas de la próxima edición, donde se verifica de forma independiente.

**Reglas.** Nunca en portada editorial ni en el boletín diario; nunca reescrito por la redacción como si fuera noticia; sin fotos de personas sin consentimiento documentado; la valoración se entrega al emisor, no se publica; la difusión solo a quien optó por ese tipo de correo (consentimiento separado, LSSI art. 21). Si la nota toca a Movenbus, MUFMI o MOVO se publica igual, marcada como del grupo.

**Datos.** `organizations` (ya existe) más `press_releases` (id, org_id, contact_id, title, body, attachments, status: recibida | publicada | retirada, ghost_post_id, assessment jsonb, distribution jsonb, received_at, published_at). **KPI:** notas recibidas, organizaciones nuevas, valoraciones vendidas, difusiones vendidas, candidatas que acabaron en pieza.

### 4.2 Fuentes de segundo nivel: la información «más oculta» (`fuentes-segundo-nivel-v1`)

**Para qué.** La información que vale dinero es pública pero no está donde se busca: convocatorias de subvenciones, contratos menores, actas de pleno, preguntas parlamentarias, expedientes del regulador, informes de fiscalización. Quien la junta y la ordena se vuelve cita obligada. Es el núcleo de la vía D y una parte de la credibilidad.

**Fuentes a incorporar, por valor y facilidad.**
1. BDNS (Base de Datos Nacional de Subvenciones): convocatorias y concesiones de transporte y movilidad, con API pública. Ayudas al transporte, PMST, flotas, bono joven.
2. Portal de Transparencia de la AGE y portales autonómicos: contratos menores, convenios, encomiendas; CNMC (expedientes de ferroviario, aeroportuario y competencia; registro de grupos de interés).
3. Congreso y Senado: preguntas escritas, proposiciones no de ley, comparecencias de la Comisión de Transportes (datos abiertos de ambas cámaras).
4. Tribunal de Cuentas y OCEX autonómicos: informes de fiscalización de consorcios, empresas públicas y contratos de transporte.
5. Actas y órdenes del día de los órganos de gobierno de consorcios y ATM (CRTM, ATM Barcelona, Consorcio de Transportes de Bizkaia, Andalucía, Canarias) y plenos de capitales en lo que toque movilidad.
6. CNMV (hechos relevantes de cotizadas del sector), BORME (nombramientos, concursos), registros de convocatorias de huelga, declaraciones de impacto ambiental de infraestructuras.
7. Ya existe: BOE, boletines autonómicos, DOUE, TED, PLACSP, participación pública del Ministerio.

**Cómo.** Cada fuente se da de alta en `portal/data/sources.json` con tipo, método (API, RSS, lectura de página), licencia de reutilización y `robots` respetado; el barrido de mediodía de `/sensores` (laborables 13:30) las lee y escribe señales y, cuando procede, filas en tablas de datos (`datasets`: subvenciones, contratos, nombramientos, preguntas parlamentarias). Con ellas se publican las series propias descargables (CSV con método) y el «Radar regulatorio» de los lunes. Lo que una fuente prohíbe reutilizar no se copia: se cita y se enlaza.

### 4.3 Auscultador Amarantia (`amarantia-auscultador-v1`)

**Para qué.** Detectar antes que nadie un suceso sin confirmar, un cambio de sentimiento o un rumor sobre una entidad vigilada; avisar al cliente y a la redacción; no actuar solo.

**Fuentes, en tres anillos.** (1) Lo que ya barren los sensores: prensa, RSS, boletines, licitaciones. (2) Redes con API abierta o barata: Bluesky (firehose público, gratis), Reddit, YouTube (comentarios por API), Telegram (canales públicos), Mastodon; Google News y Alerts por RSS; Talkwalker Alerts. (3) De pago y solo si el cliente lo asume: X (API de pago, varios cientos de euros al mes), o una herramienta de escucha contratada (Brand24, Mention) conectada por API a la misma tabla. LinkedIn no tiene API de escucha: se cubre con buscadores y con lo que publique la propia entidad.

**Método.** Cada señal lleva entidad, fuente, hora, sentimiento (−1 a 1), confirmación (`confirmado` si hay fuente primaria; `sin-confirmar` si solo hay medios o redes; `rumor` si solo redes o fuentes anónimas), alcance (autor, seguidores, reenvíos cuando la fuente los da). Por entidad se mantiene una línea base móvil de 30 días (volumen diario y sentimiento medio). Dos detectores: **pico repentino** (volumen o sentimiento negativo fuera de tres desviaciones en una ventana de 6 horas) y **cambio de tendencia** (pendiente del sentimiento a 14 días que cruza un umbral). Cada detección abre una **alerta** con nivel (vigilar, atención, crisis), evidencias enlazadas y estado (`nueva → vista → confirmada | descartada → en acción`). Nunca se escala sola: una persona la confirma. Las señales de la redacción («posible noticia grande») van a `work/sensores/candidatas.md` y al aviso del director.

**Canales de aviso.** Por plan del cliente: correo siempre; SMS y WhatsApp (Brevo) para atención y crisis; la llamada de voz queda para cuando un cliente la pida. Todo por el motor de envíos. **Calendario:** el auscultador se adelanta a las semanas 1–2 de 2027 por el interés de un cliente; hasta que exista el motor de envíos avisa por correo.

**Panel** (`app.moticias.com/amarantia`): entidades, línea base, alertas abiertas, evidencias, botones Confirmar / Descartar / Abrir PLUS. Vista de cliente con solo sus entidades (RLS). **Datos:** `entities` (cliente, nombre, alias, palabras de riesgo, umbrales), `baselines`, `alerts`, `alert_events`. **Reservado:** lo clasificado no entra aquí; el modelo local es otro proyecto y otra máquina.

### 4.4 Inyector PLUS (`amarantia-plus-v1`) sobre el motor de envíos (`motor-envios-v1`)

**Para qué.** Cuando una alerta se confirma, el cliente necesita ejecutar su plan de comunicación de crisis sin improvisar: a quién, en qué orden, por qué canal, con qué texto, con acuse de recibo, y poder parar en cualquier paso. PLUS es ese plan convertido en secuencia ejecutable, con una persona que aprueba cada tramo.

**Modelo.** `planes` (cliente, escenario: accidente, huelga, ciberataque, sanción, interrupción del servicio…, propietario, versión), `audiencias` (internas: dirección, operaciones, conductores; stakeholders: administración concedente, consorcio, alcaldes, representantes políticos, asociaciones; clientes; medios; público que optó), `secuencias` (pasos ordenados: audiencia, canal o canales, plantilla con variables, condición de avance: tiempo, porcentaje de acuses, aprobación humana), `ejecuciones` (una por crisis o simulacro), `envios` (destinatario, canal, estado: enviado, entregado, leído, acusado, fallido; reintentos), `aprobaciones` (quién, cuándo, qué paso).

**Ejecución.** Vercel Workflow: cada paso es durable; «esperar acuse del 80 % o 20 minutos» y «esperar aprobación del responsable» son pasos que sobreviven a reinicios. Canales: Brevo (correo, SMS y WhatsApp con plantillas aprobadas por Meta); la voz con «pulse 1 para confirmar» entra con Twilio solo si un cliente la pide. El **flash público** es una nota en la sala de prensa (4.1) más redes y lista de medios; se firma siempre como comunicado de la empresa y nunca se presenta como alerta oficial (las alertas a la población son competencia de Protección Civil, sistema ES-Alert del 112). **Simulacros:** la misma secuencia contra una audiencia de prueba, con informe de tiempos y acuses; es lo primero que se vende.

**Legal.** El cliente es responsable del tratamiento y Avionline encargado (contrato del art. 28 RGPD); los contactos de emergencia internos se tratan por ejecución del contrato laboral o interés legítimo documentado; WhatsApp exige opt-in previo y plantillas aprobadas; los SMS llevan remitente identificado; todo queda en registro de auditoría. Nada de esto se improvisa en la crisis: se firma al dar de alta el plan.

### 4.5 Conocimiento (`conocimiento-v1`)

**Para qué.** Una base de conocimiento verídica, de fuente primaria y actualizada es lo que convierte a MOVO en «el modelo IA de la movilidad», lo que justifica la suscripción corporativa de MOTICIAS y lo que Amarantia necesita para contextualizar una crisis. Se construye una vez, como servicio del grupo, y empieza por el corpus del proyecto «conocimiento» (PMST, Ley 9/2025 y su desarrollo).

**Lo que ya existe (comprobado el 8-11-2026 en `movo-es/movo`).** MOVO tiene el motor construido y en producción, con la misma filosofía que este documento pedía: `procesos` (catálogo de repositorios; hoy `pmst`; «un dominio nuevo es una fila, no un sistema nuevo»), `fuentes` (una fila por documento oficial, con identificador, emisor, ámbito, municipio por código INE, fechas de publicación y vigencia), `fuente_rango` (`primaria` 1,00 · `secundaria_reputada` 0,60 · `sin_confirmar` 0,25), `fuente_proceso` (alcance por proceso y veto), `fuente_uso` (libro de solo añadir: qué documento se apoyó en qué fuente), `fuente_usable()` (la única respuesta a «¿puedo citar esto?»), `conocimiento_canales` / `_hallazgos` / `_barridos` (el barrido automático con la verificación como propiedad del canal, marcada por una persona), `lib/conocimiento/anclaje.js` (las reglas que impiden que el modelo aporte hechos), `lib/consulta/buscar.js` (consulta técnica determinista con comprobación de citas) y el briefing `docs/CONOCIMIENTO-MOVILIDAD.md`. Tres estados de frescura: firmado, comprobado, nada. Lo que no tiene: búsqueda semántica (no hay `pgvector`), ni un proceso para MOTICIAS o Amarantia, ni una consulta abierta a clientes.

**Decisión (8-11-2026): extender, no duplicar.** `conocimiento-v1` añade al motor de MOVO los procesos `moticias` (y después `amarantia`) como filas de `procesos`, da de alta los canales de MOTICIAS (BOE por API, boletines autonómicos, las propias piezas como fuente `secundaria_reputada` con sus fuentes primarias dentro), y construye encima la capa que falta: fragmentos con embeddings (Voyage) y una función de búsqueda semántica que devuelve solo fragmentos de fuentes que `fuente_usable()` aprueba para el proceso, con cita (identificador, artículo o página, fecha de vigencia) y «no consta» cuando no hay base. La consulta para el nivel corporativa de MOTICIAS vive en `app.moticias.com/conocimiento` y llama a esa función; MOVO la usa en su consola; Amarantia, por API interna. El esquema sigue en el Supabase de MOVO (Frankfurt), bajo sus reglas: tablas nuevas con RLS y permisos explícitos, funciones cerradas, la IA no calcula.

**Ingesta.** `/conocimiento-ingesta` (diario, 03:00) escribe hallazgos en `conocimiento_hallazgos` por los canales de MOTICIAS y propone desarrollos normativos como hallazgos sin ascender; `ascender_hallazgo()` de MOVO decide qué entra en `fuentes` según el rango del canal. Las piezas de MOTICIAS entran como fuentes secundarias reputadas con `fuente_relacion` hacia sus fuentes primarias.

**Lo que decide la entrevista 11:** dónde corre la búsqueda semántica (función en Supabase con `pgvector` o servicio en Vercel), cuota por nivel, formato de cita en pantalla, y si el proceso `moticias` comparte canales con `pmst` o los duplica como filas propias.

### 4.6 Ediciones a medida, revistas, empaquetador y widget (`ediciones-a-medida-v2`)

**Selector.** Un `perfil` por cliente: tipos de pieza, secciones, subsectores, etiquetas incluidas y excluidas, palabras clave, campañas, idioma, número máximo, periodo. El mismo perfil alimenta la edición web privada, el correo, el PDF y el widget. Las etiquetas y palabras clave se gestionan desde la sala de redacción, no en código.

**Contenido del cliente.** El cliente (o su edición a medida) puede aportar piezas propias (noticias internas, comunicados, agenda); se marcan como «Contenido de <cliente>» y se maquetan igual, nunca mezcladas sin marca con las de MOTICIAS.

**Empaquetador.** Cadencia (semanal, quincenal, mensual) por perfil. Produce: página privada en `app.moticias.com/ediciones/<cliente>`, correo (plantilla Brevo con la cabecera del cliente) y PDF (portada, sumario, piezas con fuentes, agenda de plazos). Antes de emitir, crea un documento colaborativo de Claude con la selección y el texto, lo comparte con los redactores y, si se decide, con el cliente; el envío espera a la aprobación en ese documento o en la sala. El PDF se genera en una tarea de Claude Code (Python, como la hemeroteca) para no depender de servicios de terceros.

**Widget.** `app.moticias.com/widget.js` lee la Content API de Ghost (pública, solo lectura), aplica los filtros de los atributos `data-*` y pinta una lista con estilo neutro y enlace a cada pieza y a MOTICIAS. Gratis y con marca.

**Coste y monetización si es gratis.** Coste marginal del widget: cero contenido nuevo, tráfico de lectura de una API pública, alojamiento incluido en Vercel; su valor son los enlaces entrantes desde dominios del sector (autoridad) y las altas que generan. Coste de una revista mensual de asociación: selección automática más revisión humana de 30–60 minutos y unos céntimos de generación; por eso la revista se cobra y el widget no. Regla: gratis lo que trae enlaces y lectores; de pago lo que requiere horas o exclusividad.

### 4.7 Contactos «Quién decide» (`contactos-quien-decide-v1`)

**Qué contiene.** Organizaciones (administraciones, consorcios, operadores, asociaciones, industria, consultoras, medios) y cargos (persona, cargo, organismo, desde, hasta, fuente, fecha de verificación) con datos de contacto **profesionales** (correo y teléfono del cargo, no personales). Fuentes: nombramientos del BOE y boletines autonómicos (ya los recoge la rutina), BORME, webs oficiales, notas de prensa, la sala de prensa (4.1). Un agente mensual revisa vigencias y marca lo caducado.

**Límites.** Solo datos de cargos públicos y de contacto profesional en el sentido del art. 19 de la LOPDGDD; información del derecho a oponerse en cada uso; ninguna exportación masiva al nivel profesional (consulta y fichas); exportación al nivel corporativa bajo contrato con finalidad declarada. Las listas de la sala de prensa y de PLUS se nutren de aquí.

**Dónde se ve.** `app.moticias.com/quien-decide` para corporativa; `/crm` interno para el comercial del grupo (leads por solución, como en `plataforma-v1`).

### 4.8 Menciones del grupo y gestor de productos propios (`menciones-del-grupo-v1`)

**Decisión de Rainer (8-11-2026).** Cuando MOTICIAS publica algo que una solución del grupo resuelve, la pieza incluye una referencia sin parecer publicidad: MUFMI cuando trata de transporte a la demanda, MOVO en PMST, Movenbus cuando una compra grande de autobús discrecional necesita un agregador (ejemplo: los 14 lotes de Renfe para planes alternativos). El director recibe por correo cada mención con enlace directo para editarla. Y existe un gestor de productos propios con la descripción del contexto que da entrada a cada uno.

**Cómo se concilia con el cortafuegos.** La referencia existe, pero no está en el texto: es un bloque señalizado «Nota de la casa» al pie de la pieza, después de las fuentes, con el texto del producto, el enlace con UTM y una declaración de una frase (mismo grupo; no es publicidad pagada; no ha intervenido en la selección ni en la redacción). Una pieza lleva una mención como mucho; los análisis del director y las piezas que tratan del grupo no llevan ninguna; la mención no cambia la firma ni la aprobación. Lo que convierte esto en credibilidad y no en folleto es que se declara y que el director lo revisa pieza a pieza.

**El gestor** (`data/productos/<id>.json`, módulo 9): `contexto` en prosa (cuándo sí y cuándo no), `disparadores` (subsectores, secciones, palabras clave, frases), `excluir`, `umbral`, `max_por_semana`, `textos.corto`, `textos.cta`, `utm_campaign`, `status`. Hoy: Movenbus, MUFMI y MOVO·PMST activos; MOVO·licitaciones y la nueva línea de planes de movilidad en borrador hasta que Rainer confirme URL y texto. `src/menciones.py` puntúa (la cabecera de la pieza pesa doble y tiene que tratar del tema), escribe `menciones` en la pieza, el publicador pinta el bloque, y `informe` + `enviar` mandan a `ruphoff@avionline.es` el resumen con dos enlaces por mención: el fichero en GitHub (fuente de verdad: cambiar el texto o poner `estado: retirada`) y el editor de Ghost. Solo se envía si hubo menciones. Probado el 8-11 sobre las tres ediciones: 6 menciones en 74 piezas (Renfe → Movenbus con 36 puntos; Jaén y Dbus → MUFMI; ZBE → MOVO; dos dudosas que el correo deja a su criterio).

**Actualización (8-11-2026, noche; cambio `patrocinios-en-linea`).** Rainer decide que la mención vaya en una caja «Contenido patrocinado» en medio del texto, no al pie, con modo (automático con umbral, revisión, a mano, apagado) y exclusividad por producto, gestionada desde un gestor móvil en `app.moticias.com/gestor/` (perfiles superadministrador y oficina) al que lleva el correo. Lo anterior sobre el bloque «Nota de la casa» queda sustituido.

### 4.9 Buscador y piezas bajo demanda (`buscador-bajo-demanda-v1`)

**Decisión de Rainer (8-11-2026).** Hace falta un buscador. Si lo que busca un cliente no está en las noticias publicadas, se busca fuera y, si se encuentra, se construye una noticia con la información encontrada, con el mismo formato y el mismo método, y se guarda para que esté disponible en el futuro.

**Cómo.** Búsqueda nativa de Ghost en el tema para lo público; `src/buscador.py` (módulo 10) sobre `data/` para los agentes, con veredicto `cubierto` / `parcial` / `sin_cobertura`. Cuando no hay cobertura, el miembro con sesión pulsa «Pedir esta pieza a la redacción» y se abre un encargo (consulta, fecha, `miembro_id` de Ghost, nivel; nunca correo ni nombre: el repositorio es público) con cuota por nivel (profesional 2 al mes, corporativa 10). `/pieza-bajo-demanda` (tarea cada dos horas en laborables) busca primero, investiga después con el estándar de profundidad y escribe la pieza completa con `origen: bajo-demanda`; sin fuente primaria no se escribe y el solicitante recibe las referencias que sí existen. La pieza pasa por el gestor de menciones, se publica, entra en la hemeroteca y queda para siempre. Es un servicio de la vía B que ningún medio sectorial ofrece: la pregunta del lector se convierte en archivo.

## 5. Plan por semanas (noviembre de 2026 – junio de 2027)

Criterios: una entrevista por semana como máximo (30 minutos desde el móvil); cada cambio deja algo visible; lo que ya produce valor va antes; los sensores se adelantan porque son baratos y alimentan tres productos; el auscultador de Amarantia se adelanta a enero porque hay interés de un cliente (decisión del 8-11); PLUS va después del motor de envíos porque lo necesita; la publicidad y el segundo vertical, al final, cuando haya audiencia.

| Semana | Cambio OpenSpec | Entrevista | Qué verá Rainer | Dependencias |
|---|---|---|---|---|
| 46 (10–16 nov) | `publicar-en-ghost-v1` + `menciones-del-grupo-v1` | Hecha el 8-11 (`openspec/changes/publicar-en-ghost-v1/`) + sin entrevista | Las 74 piezas en www.moticias.com (12 pendientes de su «Publicar»), tema versionado, legales publicadas, alta con consentimientos; la «Nota de la casa» visible en la pieza de Renfe y el primer correo de menciones con enlaces de edición | `GHOST_ADMIN_KEY` y `BREVO_API_KEY` en la tarea |
| 47 (17–23 nov) | `notas-de-prensa-v1` | Corta (nº 10) | Sección `/notas-de-prensa/`, formulario, buzón `prensa@`, primera nota publicada; ficha de organización | Ghost; buzón en Hostinger |
| 48 (24–30 nov) | `sala-de-redaccion-v1` + `buscador-bajo-demanda-v1` | Sí (nº 3) + corta (nº 16) | Supabase `moticias` con migración 001; `app.moticias.com/redaccion` con cola de aprobación desde el móvil; buscador visible en el tema, «Pedir esta pieza» para miembros, primera pieza bajo demanda publicada | Vercel, Supabase |
| 49 (1–7 dic) | `sensores-v1` | No (spec clara) | `/sensores` escribe en `senales`; barrido de mediodía programado; vista por entidad | Supabase |
| 50 (8–14 dic) | `campanas-tematicas-v1` | Sí (nº 2) | Panel `/campanas` con la campaña PMST; la semilla de «Quién decide» ya está en `data/cargos/` | Sala |
| 51–52 (15–28 dic) | `suscripciones-v1` | Sí (nº 4) | Niveles en Ghost, alta con perfil, centro de preferencias; primeras altas | Ghost miembros |
| 1–2 (4–17 ene) | `amarantia-auscultador-v1` (adelantado: hay interés de un cliente) | Sí (nº 14) | Entidades, línea base, alertas con niveles, panel Amarantia, aviso por correo (Brevo); primera entidad de cliente | Sensores |
| 3 (18–24 ene) | `motor-envios-v1` + `fuentes-segundo-nivel-v1` | Sí (nº 13) + no | Envío por correo, SMS y WhatsApp (Brevo) a un segmento con acuses y registro; cinco fuentes nuevas y primera serie propia | Brevo |
| 4 (25–31 ene) | `crm-leads-v1` + `notas-de-prensa-v2` | Sí (nº 5) + no | `/crm` con leads por solución; «Valorar» y «Difundir» con pago en MOVO | Suscripciones, motor |
| 5–7 (1–21 feb) | `conocimiento-v1` (extiende el motor de MOVO) | Sí (nº 11) | Proceso `moticias` en el motor de conocimiento de MOVO, búsqueda semántica con citas en `app.moticias.com/conocimiento` para corporativa | Decisiones de la nº 11; Voyage |
| 8–10 (22 feb–14 mar) | `ediciones-a-medida-v2` | Sí (nº 12) | Perfiles, página privada, correo, PDF con documento de revisión; widget en una web amiga; tres asociaciones piloto | Selector; Brevo |
| 11–15 (15 mar–18 abr) | `amarantia-plus-v1` | Sí (nº 15) | Plan de crisis de un cliente piloto, secuencia, aprobación por paso, simulacro con informe | Motor, auscultador, Workflow |
| 16–17 (19 abr–2 may) | `contactos-quien-decide-v1` + `asesor-v1` | No + no | «Quién decide» para corporativa; agente mensual; asesor con aceptación desde el móvil | Semilla |
| 18–20 (3–23 may) | `publicidad-promocion-v1` | Sí (nº 6) | Huecos operativos con autopromoción, `/anunciantes`, primer patrocinio ofrecido a una asociación | Audiencia |
| 21–23 (24 may–13 jun) | `vertical-turismo-v1` | Sí (nº 9) | Primera edición de prueba de «viajar en grupo» sin tocar código | Todo lo anterior |

Voz (llamadas con acuse por teclado) queda fuera de 2027 salvo que un cliente de PLUS la pida; entonces entra Twilio solo para eso.

Segundo semestre de 2027: API pública de datos, informes trimestrales de pago, modelo local para la parte reservada de Amarantia, segundo cliente de PLUS, «Quién decide» con organigramas.

**Ritmo semanal.** Lunes 09:17, el asesor propone y revisa la semana anterior. Martes, entrevista (si toca) desde el móvil, 10–15 preguntas de una en una. Miércoles y jueves, Code aplica (specs, docs, código, comando, migración) y hace commits. Viernes, Rainer comprueba el bloque «Qué verás tú» y dice «archiva» o pide cambios. Las tareas programadas hacen el resto (Anexo B).

**Horas de Rainer.** Dos a tres horas a la semana: entrevista, comprobación, decisiones comerciales (precios, pilotos, contratos). Todo lo demás es de los agentes y de Code.

## 6. Cómo comunicarlo a Code

1. **El paquete ya está escrito** (rama `estrategia-2027`, 8-11-2026): este documento; el cambio OpenSpec `openspec/changes/plataforma-2027/` con `proposal.md`, `tasks.md` y `specs/<módulo>/spec.md` para los ocho módulos nuevos; el borrador `supabase/migrations/002_plataforma_2027.sql`; y una primera versión funcional de los módulos 1, 2 y 3 (`src/selector.py`, `src/empaquetador.py`, `app/public/widget.js` con `src/export_feed.py`), la semilla de «Quién decide» (`data/cargos/`), el barrido de la BDNS (`src/bdns_sweep.py`), los cinco comandos de agentes nuevos, los borradores legales (`docs/legal/`) y `ghost/llms.txt`. Lo que `tasks.md` marca como hecho el 8-11 no se vuelve a construir: cada cambio hijo lo afina, lo prueba y lo conecta a Supabase, Ghost o Vercel según toque. El cambio no se aplica entero: como `plataforma-v1`, es el mapa; cada semana se abre el cambio hijo de la tabla del § 5.
2. **Ya está en `main`** (pull request #1, fundido el 8-11-2026 por la tarde), junto con las decisiones de las cinco preguntas y la entrevista 1 (`openspec/changes/publicar-en-ghost-v1/`).
3. **Ya hecho en la rama:** `docs/paso-a-code.md § 3` reordenado con las entrevistas 10–15; `CLAUDE.md` con las tres reglas nuevas y el mapa; `docs/arquitectura.md` con las carpetas nuevas. Code solo sincroniza después la copia de lectura del proyecto de Claude.
4. **Primer mensaje para la sesión de Code** (pegar tal cual):

```
Lee CLAUDE.md, docs/estrategia-2027.md (sobre todo § 5 y § 6) y openspec/changes/publicar-en-ghost-v1/ (proposal, design, tasks, spec). Confirma en cinco líneas qué está ya hecho, qué decidió la entrevista 1 y qué te toca. Comprueba que las variables GHOST_URL y GHOST_ADMIN_KEY están definidas en esta sesión (si no, para y pídemelas: nunca las escribas en el repositorio). Después aplica openspec/changes/publicar-en-ghost-v1/tasks.md en orden, una tarea por commit con su verificación ejecutada, y al terminar escribe el bloque «Qué verás tú» con las URL reales y haz push. Si una tarea exige una decisión que no está en la propuesta, pregúntamela de una en una con tu recomendación.
```

5. **Las semanas siguientes**, el mensaje es siempre el mismo patrón: `/opsx:explore` + «Entrevístame para el cambio <nombre>. Lee antes CLAUDE.md, docs/estrategia-2027.md § 4.x, docs/paso-a-code.md § 3 (entrevista <n>) y la spec en openspec/changes/plataforma-2027/specs/<módulo>/. Pregunta de una en una, solo lo que no esté decidido, con tu recomendación. Al terminar, resume y pasa a /opsx:propose <nombre>.»
6. **Lo que no se negocia en ninguna entrevista** (Code debe darlo por decidido): pila (Ghost, repo, Supabase, Next.js en Vercel, Brevo para correo, SMS y WhatsApp, Claude, Voyage, el motor de conocimiento de MOVO); subdirectorios salvo `app.`; cortafuegos editorial-comercial; multi-vertical por configuración; claves solo en variables de entorno; nada se borra; aprobación desde el móvil.

## 7. Riesgos y cortafuegos

- **Mezcla editorial-comercial.** La sala de prensa y las revistas pueden parecer «pagar por salir». Cortafuegos: marcas visibles, secciones separadas, el boletín diario nunca lleva comunicados, página «Cómo trabajamos» con las reglas.
- **Datos personales.** Contactos de cargos, listas de emergencia, suscriptores. Cortafuegos: Avionline como responsable (o encargado en PLUS), consentimientos separados, solo contacto profesional, registro de actividades, textos legales antes de la primera alta (semana 46).
- **Alertas y comunicación de crisis.** Confundir un comunicado con una alerta oficial, o enviar sin aprobación. Cortafuegos: aprobación humana por paso, denominación «Comunicado de <empresa>», simulacros antes del primer uso real, registro de auditoría.
- **Fuentes y reutilización.** Scraping prohibido por robots o licencias. Cortafuegos: alta de cada fuente con licencia y método; lo prohibido se cita y enlaza.
- **Coste de APIs de redes.** X y herramientas de escucha son caras. Cortafuegos: anillos 1 y 2 gratis; el anillo 3 lo paga el cliente que lo pide.
- **Carga del director.** Nueve entrevistas en siete meses. Cortafuegos: un cambio por semana, entrevistas de 15 preguntas, «Qué verás tú» en cada propuesta; si una semana no hay tiempo, el calendario corre una semana, no se acumulan dos cambios.
- **Tokens y tiempo de los agentes.** La edición diaria ya roza su tope. Cortafuegos: topes por comando, barrido de mediodía separado de la edición, ingesta de conocimiento fuera de hora punta.
- **Información reservada de Amarantia.** No entra en la nube. El modelo local es un proyecto aparte con su propia fecha.

## 8. Indicadores por trimestre

| Trimestre | Audiencia y credibilidad | Ingresos y leads |
|---|---|---|
| T4 2026 | moticias.com publicado; 100 altas con perfil; 10 notas de prensa recibidas; 5 fuentes nuevas | Primera valoración de nota vendida; 3 asociaciones piloto invitadas |
| T1 2027 | 500 altas; 20 organizaciones en la sala de prensa; primera serie propia citada por un tercero; consulta IA operativa | 10 profesionales; 1 asociación de pago; primeros leads por solución medidos |
| T2 2027 | 1.000 altas; 50 organizaciones; auscultador con 3 entidades; primer simulacro PLUS | 1.490 €/mes cubiertos (umbral); 1 cliente Amarantia; 2 corporativas |
| T3–T4 2027 | 2.500 altas; segundo vertical en pruebas; API de datos | 3.000 €/mes; patrocinios de sección; informes de pago |

Los números son metas para orientar, no previsiones: se revisan en el informe del asesor del primer lunes de cada trimestre.

## Anexo A · Guion de las entrevistas nuevas

Cada entrevista: 8–12 preguntas, una por mensaje, con la recomendación marcada; lo ya decidido en este documento no se vuelve a preguntar.

**A.1 `notas-de-prensa-v1` (semana 47).** Nombre público de la sección (recomendado: «Notas de prensa»); verificación del emisor (recomendado: correo de dominio corporativo o enlace de confirmación); plazo de publicación (recomendado: mismo día laborable si llega antes de las 14:00); adjuntos permitidos (PDF e imágenes con derechos declarados); texto de la marca «Comunicado de empresa»; si las notas del grupo se publican igual (recomendado: sí, marcadas); quién vacía el buzón (agente a las 09:30 y 15:30).

**A.2 `conocimiento-v1` (semanas 5–7).** Resuelto el 8-11: el motor existe en `movo-es/movo` y se extiende (§ 4.5). Quedan: dónde corre la búsqueda semántica (recomendado: `pgvector` en el Supabase de MOVO, función `security definer` cerrada); si el proceso `moticias` comparte canales con `pmst` (recomendado: canales propios, misma tabla); corpus inicial (recomendado: Ley 9/2025 y desarrollo, piezas de MOTICIAS, BOE consolidado de transporte); quién aprueba la incorporación de fuentes propuestas; proveedor de embeddings (recomendado: Voyage); límites de consulta por nivel (recomendado: 50 al mes en corporativa, ampliable); formato de cita (recomendado: fuente, artículo o página, fecha de validez); si la consulta se expone por API a MOVO desde el primer día.

**A.3 `ediciones-a-medida-v2` (semanas 8–10).** Clientes piloto (tres asociaciones: nombres); cadencia por defecto (recomendado: quincenal para asociaciones, semanal para empresas); plantilla del PDF (recomendado: la de la hemeroteca con cabecera del cliente); quién revisa el documento colaborativo (recomendado: redactor y un contacto del cliente); contenido del cliente: ¿por formulario, por correo o por la sala?; marca del widget (texto y enlace); métricas que se enseñan al cliente (lecturas, clics, altas).

**A.4 `motor-envios-v1` (semana 3).** Todo en Brevo (correo, SMS, WhatsApp; decidido el 8-11); remitentes por canal (correo `alertas@moticias.com`; SMS con remitente alfanumérico «MOTICIAS» o el del cliente; WhatsApp: número de Avionline o del cliente); voz fuera de la v1; plantillas iniciales (alerta de licitación, alerta de señal, comunicado, paso de PLUS); política de bajas y de horario (recomendado: nada no urgente entre 22:00 y 8:00); acuses (recomendado: enlace de confirmación en correo y SMS, botón en WhatsApp, tecla en voz); registro y retención (recomendado: 24 meses).

**A.5 `amarantia-auscultador-v1` (semanas 1–2 de 2027; adelantado).** Primer cliente o entidades propias del grupo para arrancar; fuentes del anillo 2 que se activan (recomendado: Bluesky, Reddit, YouTube, Google News, Telegram público); umbrales de pico y tendencia (recomendado: 3 desviaciones a 6 horas; pendiente a 14 días); niveles y quién recibe cada uno; qué llega a la redacción como «posible noticia grande» (recomendado: nivel atención o crisis sobre cualquier entidad del sector, no solo vigiladas); si se contrata una herramienta de escucha externa para X (recomendado: no hasta que un cliente lo pague).

**A.6 `amarantia-plus-v1` (semanas 11–15).** Cliente piloto y escenario del primer plan (recomendado: interrupción del servicio o accidente sin víctimas); audiencias y canales del piloto; quién aprueba cada paso (recomendado: dos personas designadas por el cliente, cualquiera de las dos); regla de avance por defecto (recomendado: 80 % de acuses o 20 minutos); contenido del flash público y lista de medios; fecha del primer simulacro; contrato de encargado del tratamiento (plantilla a nombre de Avionline).

**A.8 `buscador-bajo-demanda-v1` (semana 48; corta).** Dónde se pulsa «Pedir esta pieza» (recomendado: en la página de resultados de la búsqueda de Ghost y en el pie de cada pieza); quién puede (recomendado: profesional 2 al mes, corporativa 10; lector, ninguna); cómo llega el encargo antes de Supabase (recomendado: formulario en `app.moticias.com` que escribe `data/encargos/` por la API de GitHub); plazo prometido (recomendado: «en el próximo día laborable», sin hora); qué recibe el solicitante si no hay fuentes; si las piezas bajo demanda se marcan públicamente como tales (recomendado: sí, una línea «Pieza publicada a petición de un suscriptor», sin identificarlo).

**A.9 `menciones-del-grupo-v1` (semana 46).** Sin entrevista: decidido el 8-11 por Rainer. Code conecta el correo (Brevo), republica las piezas con mención y añade el paso a la rutina; los textos de cada producto los revisa Rainer desde el primer correo.

**A.7 `fuentes-segundo-nivel-v1`, `sensores-v1`, `quien-decide-semilla`, `contactos-quien-decide-v1`, `asesor-v1`.** Sin entrevista: la spec de este documento basta; Code propone y aplica, y pregunta solo si encuentra una decisión no cubierta.

## Anexo B · Tareas programadas (todas en la nube, cuenta de Rainer, Europe/Madrid)

| Tarea | Cuándo | Comando | Desde |
|---|---|---|---|
| Edición diaria | laborables 06:38 | `/edicion-diaria` | ya corre |
| Asesor de visibilidad y credibilidad | lunes 09:17 | `/consejo-visibilidad` | ya corre |
| Buzón de prensa | laborables 09:30 y 15:30 | `/prensa-buzon` | semana 47 |
| Piezas bajo demanda | laborables cada 2 h, 8–20 | `/pieza-bajo-demanda` | semana 48 |
| Sensores y fuentes de segundo nivel | laborables 13:30 | `/sensores` (incluye segundo nivel desde enero) | semana 49 |
| Radar regulatorio | lunes 07:30 | `/radar-regulatorio` | semana 51 |
| Licitaciones de la semana | viernes 07:30 | `/licitaciones-semana` | semana 51 |
| Promoción social | laborables 08:15 | `/promo-social` | semana 51 |
| Puntuación de leads | diario 02:00 | `/leads-puntuar` | semana 2 |
| Ingesta de conocimiento | diario 03:00 | `/conocimiento-ingesta` | semana 7 |
| Ediciones a medida | según perfil (p. ej. quincenal 07:00) | `/edicion-a-medida <perfil>` | semana 10 |
| Auscultador (anillo 2) | cada 2 horas, 7–23 | `/auscultar` | semana 2 (ene 2027) |
| Quién decide | día 1 de cada mes 04:00 | `/quien-decide-actualizar` | semana 17 |
| Cuadro de mando mensual | día 12, 07:30 | `/cuadro-de-mando` | semana 17 |

Las secuencias PLUS no son tareas programadas: las ejecuta Vercel Workflow cuando una persona las lanza.

## Anexo C · Coste de explotación estimado (mensual, orientativo)

| Partida | Estimación | Nota |
|---|---|---|
| Ghost(Pro) | 25–200 € | según el plan y el número de miembros; ya contratado |
| Vercel Pro | ~20 € | el equipo de MOVO ya está en Pro: un proyecto más |
| Supabase | 25–60 € | proyecto `moticias` más el esquema común |
| Uso de Claude (agentes, valoraciones, consultas RAG) | 200–450 € | la edición diaria es la mayor partida; se revisa con topes por comando |
| Voyage AI (embeddings) | 5–30 € | solo en ingesta |
| Brevo | 0–60 € | plan actual; SMS a coste por unidad (~0,07 €) |
| Brevo WhatsApp / Twilio voz | 0 € en reposo | coste por mensaje y minuto; se repercute al cliente de PLUS; Twilio solo si hay voz |
| APIs de redes (anillo 3) | 0 € | solo si un cliente paga X o una herramienta de escucha |
| Dominio, correo (Hostinger) | ~5 € | ya contratado |
| **Total** | **450–900 €** | sin contar horas de personas |

## Anexo D · Decisiones que este documento da por tomadas

Pila y plataformas del § 2 (Brevo para correo, SMS y WhatsApp; conocimiento sobre el motor de MOVO) · diez módulos del § 3 · menciones del grupo solo en el bloque señalizado «Nota de la casa», decididas por el gestor de productos propios y revisadas por el director por correo · piezas bajo demanda con el mismo estándar, firma y aprobación · orden del § 5 · `app.moticias.com` como única excepción a los subdirectorios · Avionline S.L. titular y responsable · comunicados marcados y fuera de lo editorial · la comunicación de crisis nunca se presenta como alerta oficial · información reservada fuera de la nube · precios del § 1 como hipótesis a validar, no como tarifa publicada.
