# MOTICIAS · Estrategia: contenido curado como motor de credibilidad y captación (7 de noviembre de 2026)

Respuesta corta: MOTICIAS vende contenido curado de calidad —por el que un profesional pagaría algo y una gran empresa bastante— para construir credibilidad; esa credibilidad es la puerta por la que entran leads cualificados y por la que las soluciones del grupo (o las de terceros que paguen) se presentan de forma discreta y eficaz. La misma máquina, con otra configuración, sirve a un segundo vertical de turismo («viajar en grupo»), y sus agentes buscadores son a la vez los sensores de Amarantia.

Reflexiones del director, 7-11-2026. Este documento es la referencia estratégica; lo operativo está en `docs/manual-operativo.md` y lo técnico en `docs/arquitectura.md` y `openspec/`.

## 1. El modelo

1. **Contenido curado de pago.** Noticias de fondo, análisis, radar regulatorio, licitaciones y plazos, bases de conocimiento (mapa concesional, DORA, líneas de interés público, buenas prácticas) y bases de contactos («Quién decide»). Calidad de referencia europea; nada que una IA genérica pueda producir.
2. **Credibilidad.** Rigor, fuentes primarias, trazabilidad, declaración de intereses, correcciones públicas. La credibilidad es el activo; todo lo demás se apoya en ella.
3. **Leads cualificados.** Quien se suscribe, lee, descarga y pide alertas deja un perfil (organización, cargo, modos, comunidades, si licita). El sistema puntúa el interés sin preguntar más y señala a quién conviene atender y con qué.
4. **Promoción discreta.** Las soluciones del grupo —y las de terceros que paguen— aparecen donde hay un problema que resuelven: fichas de soluciones verificables, casos, ediciones a medida, patrocinios señalizados; nunca como folleto ni dentro del texto editorial.
5. **Canales problema → solución → presupuesto.** Las licitaciones, consultas públicas, planes y ayudas son presupuestos disponibles; las piezas describen el problema; las fichas y servicios ofrecen la solución; el CRM une a las personas que buscan con quien resuelve.

## 2. A quién queremos llegar y con qué solución

| Segmento | Qué les preocupa | Solución del grupo | Señal que los identifica |
|---|---|---|---|
| Administraciones (consejerías, consorcios, ATM, cabildos, ayuntamientos) | Mapas concesionales, OSP, contratos vencidos, financiación, accesibilidad | **MUFMI** (transporte de viajeros, servicios a la administración) | Leen regulación y concesiones; piden radar regulatorio; licitan |
| Operadores de autobús (interurbano, urbano, discrecional) | Licitaciones, costes, flota, digitalización, demanda | **MOVENBUS** (marketplace y PMS hub) | Leen licitaciones y autobús; piden alertas por comunidad |
| Empresas con obligación o interés en PMST y sostenibilidad | Ley 9/2025, planes de movilidad al trabajo, reporting, flota | **MOVO** (PMST, procesos, valoración de licitaciones) | Leen regulación y movilidad urbana; descargan plantillas y guías |
| Municipios y gestores de grandes campus (multinacionales, universidades, puertos, plataformas logísticas) | Planes de movilidad, organización de tráficos, accesos, aparcamiento, intermodalidad | **Lo nuevo con Jörg Fischer y Francisco González** (planes de movilidad y organización de tráficos) | Leen infraestructuras, puertos, urbano y logística; consultan casos |

Regla: la pieza editorial nunca cita a la solución del grupo como tal; la conexión la hace la plataforma (ficha, ruta, oferta de servicio, edición a medida) y siempre señalizada. MOTICIAS no cubre operaciones propias de Movenbus.

## 3. Capas de la plataforma (lo que hay que construir)

1. **Actualidad**: edición diaria, radar regulatorio semanal, licitaciones de la semana, análisis.
2. **Bases de conocimiento**: páginas pilar con hijas (mapa concesional, DORA, OSP, PMST, líneas de interés público, buenas prácticas), datos propios descargables con método.
3. **Base de contactos**: «Quién decide» (cargos, organigramas, nombramientos) y, en privado, el CRM de lectores, suscriptores, anunciantes y leads.
4. **Canales de solución**: fichas de soluciones verificables (ya existen 14), casos, ediciones a medida para asociaciones y empresas, patrocinios de sección, servicios de MOVO (valoración de licitaciones).
5. **Suscripciones**: gratuita (lector), profesional (de pago, para un profesional), corporativa (de pago, para una empresa grande: usuarios múltiples, alertas, edición a medida, datos), anunciante/patrocinador.
6. **Campañas temáticas**: cuando se acerca un plazo o un hecho (los PMST de la Ley 9/2025, una gran licitación, una transposición), el sistema trabaja ese tema a fondo durante unas semanas —pilar, reportajes, datos propios, radar, cierre— y pone la solución que lo resuelve delante de quien lo sufre, con o sin patrocinio y siempre señalizado. Cada campaña tiene plan, KPI y cierre; es la unidad en la que se mide si el contenido trae leads.
7. **Asesor permanente**: el sistema propone cada semana a editores y superadministradores ideas e instrucciones concretas para mejorar visibilidad y credibilidad (qué pieza pilar falta, qué dato propio publicar, qué fuente citar, qué asociación abordar, qué patrocinio ofrecer, qué canal abrir), con prioridad y esfuerzo.

## 4. Modularidad: un motor, varios verticales

Todo lo específico de MOTICIAS (nombre, dominio, secciones, fuentes, rotación de análisis, segmentos, soluciones del grupo, palabras clave de los sensores) vive en un fichero de configuración del vertical (`verticals/movilidad.json`). El código, los agentes, las specs y la sala de redacción son comunes.

Segundo vertical previsto: **turismo, «viajar en grupo»** (`verticals/turismo.json`): viajes en grupo, transporte turístico, alojamiento colectivo, regulación turística, licitaciones y ayudas, con las mismas capas (actualidad, conocimiento, contactos, canales, suscripciones, asesor). Lo que se construya para MOTICIAS se construye para que el segundo vertical sea un fichero de configuración y una marca, no un segundo desarrollo.

## 5. Sensores compartidos con Amarantia

Los agentes que buscan noticias, novedades, ideas, buenas prácticas y señales de riesgo para MOTICIAS son también los sensores de **Amarantia** (plataforma de construcción y defensa de la reputación corporativa; su parte de información reservada se evalúa con un modelo local). Cada hallazgo se guarda como señal estructurada (`fecha`, `fuente`, `tipo`: noticia / norma / licitación / nombramiento / incidente / riesgo / buena práctica / idea, `entidades`, `ámbito`, `sentimiento`, `relevancia`, `enlace`) en un almacén común que MOTICIAS usa para publicar y Amarantia para vigilar, alertar y responder. Las palabras clave y entidades vigiladas por cada cliente de Amarantia se añaden a la configuración de los sensores sin tocar el motor. Esto enlaza con el hub «Inteligencia» (movo.es/inteligencia) que ya alimenta canales como Innovación y Radar en Airtable: el almacén de señales debe ser el mismo o estar sincronizado.

## 6. Principios de construcción

- Empezar bien para no cambiar después: modelo de datos y configuración por vertical desde el primer día; nada específico de MOTICIAS en el código.
- Automático por defecto; aprobación desde el móvil cuando Rainer la active; nunca una tarea que exija el ordenador abierto.
- Un solo almacén de verdad (este repositorio para reglas y contenido; una base de datos para CRM, señales y métricas) y salidas múltiples (Ghost, boletines, ediciones a medida, LinkedIn, Instagram, informes).
- Independencia editorial visible: patrocinado señalizado, declaración de intereses, correcciones públicas. La promoción vive en la plataforma, no en el texto.
- Datos propios y originales antes que resúmenes: es lo que citan la prensa, las administraciones y los motores generativos.
- Métricas que importan: suscriptores activos por segmento, aperturas y clics por tema, leads cualificados por solución del grupo, conversión a servicio o contrato, ingresos por suscripción y patrocinio.
