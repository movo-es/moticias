# Cambio: plataforma-2027 — sala de prensa, fuentes de segundo nivel, conocimiento, ediciones a medida, motor de envíos, auscultador y PLUS de Amarantia, contactos «Quién decide»

Estado: propuesto (8-11-2026). Origen: anotaciones manuscritas del director «Estrategia_2027» y `docs/estrategia-2027.md` (manda sobre este resumen). Relación con `plataforma-v1`: lo amplía; no lo sustituye. Las fases de `plataforma-v1` se reordenan según `docs/estrategia-2027.md § 5` y quedan registradas en `tasks.md` de este cambio.

## Por qué

MOTICIAS tiene el contenido y el método; le falta la capa que lo convierte en una publicación que se financia sola: una sala de prensa que atraiga a las empresas con algo que decir, fuentes de segundo nivel que nadie más junta, un conocimiento consultable que justifique la suscripción corporativa, ediciones y revistas a medida empaquetables, y los dos productos de Amarantia (auscultador y PLUS) montados sobre un motor de envíos común. Todo ello como módulos reutilizables, configurados por vertical y por cliente, nunca por rama de código.

## Qué cambia

1. **Sala de prensa** (`notas-de-prensa`): recepción por formulario y buzón, ficha de organización, publicación marcada como comunicado, valoración IA opcional y difusión opcional a quien optó.
2. **Fuentes de segundo nivel** (`fuentes-segundo-nivel`): BDNS, transparencia, Congreso y Senado, Tribunal de Cuentas, actas de consorcios, CNMV, BORME, convocatorias de huelga y DIA; series propias descargables.
3. **Conocimiento** (`conocimiento`): servicio común del grupo con fuentes clasificadas y ponderadas, fragmentos con embeddings y consulta IA con citas; empieza por el corpus del proyecto «conocimiento» (PMST, Ley 9/2025).
4. **Ediciones a medida v2** (`ediciones-a-medida`): selector de contenidos por perfil, contenido del cliente marcado, empaquetador (página privada, correo, PDF) con documento de revisión colaborativo, widget embebible.
5. **Motor de envíos** (`motor-envios`): correo, SMS, WhatsApp y voz con plantillas, segmentos, acuses, bajas, registro y secuencias durables.
6. **Auscultador de Amarantia** (`auscultador`): fuentes sociales en anillos, línea base por entidad, picos y tendencia, estados de alerta, aviso a clientes y a la redacción con humano en el bucle.
7. **PLUS de Amarantia** (`plus`): planes de comunicación de crisis como secuencias ejecutables con aprobación por paso, acuses y simulacros; flash público como comunicado, nunca como alerta oficial.
8. **Contactos «Quién decide»** (`contactos-quien-decide`): organizaciones y cargos con fuente y fecha de verificación, agente mensual, límites RGPD, acceso corporativa y CRM interno.

Reglas nuevas para `CLAUDE.md` (se añaden en este cambio): *un comunicado nunca es noticia sin verificación independiente; la comunicación de crisis nunca se presenta como alerta oficial; `app.moticias.com` es la única excepción a «sin subdominios» (nada con sesión suma autoridad)*.

## Fuera de alcance

Modelo local para la información reservada de Amarantia (proyecto aparte); app móvil nativa; APIs de redes de pago (anillo 3) salvo que un cliente las pague; pasarela de pago propia (Ghost para suscripciones, MOVO/Stripe para servicios).

## Riesgos

Mezcla editorial-comercial (cortafuegos: marcas, secciones separadas, el boletín diario nunca lleva comunicados) · datos personales (Avionline responsable o encargado; consentimientos separados; solo contacto profesional) · confusión con alertas oficiales (denominación, aprobación humana, simulacros) · coste de APIs sociales (anillos 1 y 2 gratis) · carga del director (un cambio por semana).

## Qué verás tú

Al archivar este cambio no hay nada nuevo en pantalla: es el mapa. Lo que verás cada semana está en la columna «Qué verá Rainer» de `tasks.md` y de `docs/estrategia-2027.md § 5`.
