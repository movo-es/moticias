# Capacidad: conocimiento (delta)

## ADDED Requisito: servicio común del grupo
El conocimiento vive en un esquema `conocimiento` de Supabase compartido por MOVO, MOTICIAS y Amarantia, con `owner` y `shared_with` en cada fuente y RLS por colección. Ningún producto copia fuentes: las comparte o las excluye.

## ADDED Requisito: fuentes clasificadas y fechadas
`fuentes` (id, tipo: ley | reglamento | orden | resolución | sentencia | informe | nota-oficial | artículo | documento, clase: primaria | secundaria-reputada | sin-confirmar, ponderación, url, incorporada_en, publicada_en, valida_hasta, estado: activa | desactivada-en-proyecto | baneada | compartida, origen: claude | rol-autorizado, owner, shared_with text[]). Una fuente baneada no se usa en ningún proyecto.

## ADDED Requisito: desarrollos propuestos, no incorporados
Al incorporar una ley, el agente busca reglamentos, órdenes, normativa autonómica, ordenanzas y jurisprudencia relacionadas y las propone con estado `propuesta`; solo un rol autorizado las incorpora.

#### Escenario: ley con desarrollo autonómico
- CUANDO se incorpora la Ley 9/2025 de Movilidad Sostenible
- ENTONCES el agente propone sus reales decretos de desarrollo y la normativa autonómica de PMST, con fecha de publicación leída en el BOE o boletín, y nada entra en las consultas hasta que se apruebe.

## ADDED Requisito: fragmentos y consulta con citas
`documentos` (texto limpio, versión, hash) y `fragmentos` (texto, posición, embedding vector). La consulta devuelve una respuesta de 40–60 palabras, el detalle y una cita por afirmación (fuente, artículo o página, fecha de validez), ponderada por clase de fuente; si no hay base: «no consta en las fuentes». Cifras y fechas se extraen del fragmento citado, nunca se generan. Cada consulta queda en `consultas` con usuario, citas y coste.

#### Escenario: pregunta sin base
- CUANDO una consulta no encuentra fragmentos con similitud suficiente en la colección del usuario
- ENTONCES responde «no consta en las fuentes de esta colección» y no redacta una respuesta general.

## ADDED Requisito: corpus inicial e ingesta
Corpus inicial: proyecto «conocimiento» (PMST, Ley 9/2025 y desarrollo), legislación consolidada del BOE en transporte (API de datos abiertos), piezas de MOTICIAS (fuente secundaria reputada), boletines y plazos. `/conocimiento-ingesta` corre a diario a las 03:00. Embeddings con Voyage AI.

## ADDED Requisito: acceso
Consulta en `app.moticias.com/conocimiento` para el nivel corporativa (cuota mensual configurable), dentro de MOVO para sus procesos, y por API interna para Amarantia. La información reservada de Amarantia no entra en este servicio.
