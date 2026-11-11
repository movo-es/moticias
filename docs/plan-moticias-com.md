# MOTICIAS · Plan de publicación en moticias.com, suscriptores y negocio (v1.1, 7-11-2026)

Respuesta corta: moticias.com se publica en Ghost(Pro) (plan Publisher), decidido el 7-11-2026 para no mantener servidores; el repositorio `movo-es/moticias` es la fuente de verdad y la rutina diaria escribe en él y publica en Ghost por su API. La redacción y la aprobación siguen en la sala de redacción (hoy el artefacto; mañana, Ghost y el repositorio); los suscriptores gratuitos se gestionan en Brevo, ya conectado; los servicios de pago de licitaciones se venden y cobran en MOVO (Stripe), que es donde queda el dato.

> Versión anterior (v1, 4-11-2026): web estática en Hostinger alimentada por GitHub. Sustituida por Ghost(Pro) el 7-11-2026; se conservan los apartados que no dependen del alojamiento.

## 1. Arquitectura

**Fuente de verdad: el repositorio** (`docs/arquitectura.md`). Contenido en `data/` (un JSON por pieza, boletín, plazo y edición), documentación en `docs/`, especificaciones en `openspec/`, código en `src/`.

**Sala de redacción (hoy).** Artefacto de Claude con base de datos, panel de superadministrador y redacción automática a las 07:05. Aquí se escribe, corrige y aprueba mientras Ghost no esté listo.

**Escaparate público: moticias.com en Ghost(Pro).**
- Ghost gestiona web, boletines por correo, miembros y suscripciones de pago; evita Hostinger, WordPress y el mantenimiento de servidores.
- La rutina diaria publica por la Admin API de Ghost: cada pieza, un post con su etiqueta de sección (`#tierra`, `#mar`, `#aire`, `#regulacion`, `#licitaciones`, `#analisis`) y sus metadatos; cada edición, una página o boletín.
- Páginas en subdirectorios, nunca subdominios: `/tierra/`, `/mar/`, `/aire/`, `/regulacion/`, `/licitaciones/`, `/analisis/`, `/datos/`; cada pieza con su URL propia.
- Cada pieza como HTML propio: Google y los motores generativos la leen entera. Respuesta directa de 40–60 palabras arriba, marcado Schema.org `NewsArticle` y `Organization` con `sameAs`, `FAQPage` en los explicadores, `sitemap.xml`, RSS, `llms.txt` en la raíz y alta en Google Search Console y Google News Publisher Center.
- Formulario de suscripción: el de Ghost (miembros) o el de Brevo, según se decida dónde vive la lista.

## 2. Actualización automática

1. 07:05: la redacción automática escribe la edición (hoy en el artefacto; después en Ghost como borrador o publicado) y en el repositorio.
2. Mientras no haya aprobación previa: al cerrar, publica. Cuando Rainer quiera aprobar: la rutina deja los posts en borrador en Ghost; él publica desde el móvil.
3. La misma tarea crea el boletín del día (Ghost newsletter o campaña de Brevo en borrador; el envío a contactos reales lo confirma Rainer salvo que decida por escrito que se envíe solo).

## 3. Fechas: cuándo se generó cada cosa (ya implantado en el prototipo)

Cada pieza muestra un recuadro de trazabilidad: fecha de los hechos; documento oficial más reciente y su fecha de publicación; fecha de consulta de las fuentes; hora real de redacción; y, si la hubo, hora de ampliación o corrección. Si los hechos tienen más de 7 días, la pieza lleva la marca «seguimiento».

Reglas para la redacción (en la tarea diaria): hechos de las últimas 72 horas; más de 7 días solo como seguimiento con novedad documentada; fecha de publicación leída en la propia fuente (si no consta, se deja vacía, no se deduce); hora de redacción real; correcciones con hora y nota al pie; ante la duda sobre una fecha, no se publica.

## 4. Suscriptores gratuitos y datos

**Herramienta: Brevo** (ya conectado y usado por MOVO) o los miembros de Ghost; decidir una sola lista maestra. Listas: «Boletín diario», «Radar regulatorio (lunes)», «Licitaciones (viernes)», «Alertas de licitaciones por comunidad». Doble confirmación obligatoria.

**Datos a pedir, en dos tiempos (perfilado progresivo).**
- Alta, para no espantar: correo, nombre, empresa u organismo, cargo y tipo de entidad (operador, administración, consorcio o ATM, asociación, consultora, industria, prensa, otro).
- Después (centro de preferencias y segundo correo de bienvenida): modos que le interesan (autobús, ferrocarril, aéreo, marítimo, urbano), comunidades autónomas, tamaño de la empresa, si licita (sí o no, en qué ámbitos), CIF opcional y teléfono opcional.
- Comportamiento: aperturas, clics por tema y por licitación, descargas del calendario y de documentos. Con esto se segmenta y se puntúa el interés sin preguntar más.

**Consentimientos separados (RGPD, LOPDGDD y artículo 21 de la LSSI).** Casilla 1 (obligatoria): recibir los boletines de MOTICIAS. Casilla 2 (opcional y separada): recibir ofertas de servicios de las empresas del grupo (MOVO, Movenbus, MUFMI), nombradas. Sin la casilla 2 no se puede usar el contacto para vender, tampoco a direcciones de empresa. Responsable del tratamiento: Avionline S.L. (decidido el 7-11-2026); figura en la política de privacidad. Analítica web con consentimiento (o una herramienta sin cookies, como Plausible o Umami) y sin muro de «pagar o aceptar cookies».

**Imanes de suscripción (lo que hace que alguien deje su correo).**
- Alertas de licitaciones filtradas por comunidad y modo, con plazo e importe.
- Calendario de plazos descargable (ICS) que se actualiza solo.
- Radar regulatorio semanal: normas, consultas públicas y fechas límite.
- Cuadro de mando mensual con datos descargables (INE, Aena, Puertos del Estado, Renfe).
- Acceso al archivo completo de reportajes a cambio del registro gratuito: la portada y el primer tercio de cada reportaje, abiertos; el resto, con el correo.

## 5. Cómo hacerlo crecer

- **LinkedIn de Rainer como motor.** El análisis diario, resumido en un post con el dato clave y el enlace; los reportajes, en carrusel. Instagram con la misma lógica. Publicaciones generadas con cada edición.
- **Asociaciones como canal.** Ofrecerles (gratis al principio) una edición con su cabecera para sus socios, con alta voluntaria a MOTICIAS al pie: Confebus, Anetra, FET en Canarias, Atuc, ALA, Anave y las federaciones autonómicas.
- **Citabilidad.** Datos propios (series de licitaciones, plazos, concesiones que vencen) que la prensa y las administraciones puedan citar con enlace.
- **Buscadores y motores generativos.** Los descritos en el apartado 1, más una página pilar por tema (mapa concesional, DORA, líneas de interés público) con sus piezas hijas enlazadas.
- **Programa de recomendación.** Cada suscriptor con un enlace propio y, por ejemplo, un informe gratuito a partir de tres altas.
- **Encuentros.** Un desayuno o seminario trimestral sobre un expediente caliente, con grabación para suscriptores.

## 6. Versiones personalizadas (asociaciones, empresas, boletines)

Un mismo motor y muchas salidas. Cada cliente tiene un perfil: modos, comunidades, palabras clave, órganos de contratación, códigos CPV, marca y frecuencia. La redacción filtra la base de piezas, boletines y licitaciones con ese perfil y genera su edición: correo con su cabecera, página privada `/clientes/<cliente>/` y PDF.

| Producto | Para quién | Contenido |
|---|---|---|
| Boletín de marca blanca | Asociaciones | Edición con su cabecera para sus socios; MOTICIAS al pie |
| Vigilancia a medida | Empresas | Alertas diarias de su ámbito (licitaciones, normas, competidores) |
| Informe semanal ejecutivo | Direcciones y consejos | Dos páginas con lo que les afecta y qué hacer |
| Contenido para boletines ajenos | Medios y entidades | Piezas con licencia para republicar, con enlace |

Precios orientativos para validar con los primeros clientes, no cifras de mercado: asociación, de 300 a 1.500 € al mes según el número de socios; empresa, de 150 a 600 € al mes.

## 7. Licitaciones: servicio de pago en MOVO

Cada licitación en MOTICIAS lleva un botón «Valorar esta licitación con MOVO». En MOVO, previo pago con Stripe:

1. **Valoración (decisión de ir o no ir).** Encaje con la solvencia del cliente, criterios y ponderaciones, precio base frente a costes de referencia, plazos, riesgos del pliego y competidores probables (histórico de adjudicaciones y número de ofertas de TED y PLACSP).
2. **Propuesta.** Estrategia de oferta, mejoras puntuables y precio orientativo.
3. **Borrador de oferta.** Memoria técnica y anexos redactados con IA a partir de los pliegos y de los datos del cliente, para que los revise y presente él.

Precios orientativos para validar: valoración, de 90 a 250 €; propuesta, de 400 a 900 €; borrador de oferta, de 900 a 3.000 € según el importe y la complejidad del contrato.

**Inteligencia de negocio.** Cada consulta deja quién mira qué licitación, de qué tamaño y en qué comunidad, y cada adjudicación publicada cierra el ciclo (quién ganó y por cuánto). Con eso se construye el mapa del mercado: demanda por territorio y modo, tasas de concurrencia, precios de adjudicación frente a precio base y empresas activas. Es un producto en sí mismo (informes sectoriales de pago) y es el combustible del generador de pliegos y del de ofertas previstos en MOVO.

**Cortafuegos obligatorio.** Si MUFMI o Movenbus pueden presentarse a las mismas licitaciones que analizan sus clientes, hace falta separación estricta: los datos de las consultas de clientes no los ve la parte que oferta, compromiso de confidencialidad por escrito en las condiciones del servicio y, si hay coincidencia, se avisa y se ofrece no prestar el servicio. Sin esto, un solo caso de conflicto destruye la confianza en MOTICIAS y en MOVO.

## 8. El embudo

MOTICIAS (lectores, gratis) → suscriptor con perfil → alerta de licitación o norma que le afecta → consulta de pago en MOVO (valoración, propuesta u oferta) → proyecto mayor: PMST y procesos de MOVO, transporte de Movenbus o MUFMI, contrato de vigilancia a medida.

Métricas: suscriptores activos y su perfil; aperturas y clics por tema; clics en «Valorar con MOVO»; conversión a pago; ingreso por cliente; y origen de cada proyecto de Movenbus o MUFMI.

**Independencia editorial.** MOTICIAS no puede ser un folleto del grupo: la declaración de intereses ya figura en el análisis y en «Cómo trabajamos»; los botones comerciales se marcan como servicio de MOVO; y la selección y el tratamiento de noticias no dependen de ser cliente.

## 9. Pasos y lo que hace falta decidir

1. Sociedad titular de MOTICIAS y responsable del tratamiento de datos: **Avionline S.L.** (decidido el 7-11-2026).
2. Ghost(Pro): cuenta creada el 7-11-2026 (usuario ruphoff@avionline.es); falta elegir plan, conectar el dominio moticias.com y crear la clave de Admin API para la rutina.
3. Confirmar la cuenta de Brevo que se usa (la de MOVO u otra) y el remitente verificado, por ejemplo boletin@moticias.com, o decidir que la lista vive en Ghost.
4. Textos legales: aviso legal, privacidad y cookies.
5. Construcción: publicador a Ghost (`src/ghost_publish.py`), plantillas de correo, integrados en la tarea diaria; después, el botón y el flujo de pago en MOVO.
6. Lanzamiento con tres asociaciones piloto y un mes de boletín gratuito.
