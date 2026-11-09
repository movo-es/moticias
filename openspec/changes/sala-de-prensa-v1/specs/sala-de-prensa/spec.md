# Capacidad: sala de prensa (delta; sustituye a `plataforma-2027/specs/notas-de-prensa/`)

## ADDED Requisito: lista pública segmentada
Cada nota publicada es un post de Ghost con la etiqueta pública `notas-de-prensa`, la interna `#comunicado`, autor «Comunicado» y las etiquetas de ejes `m-<submodo>`, `tema-<tema>` y `t-<territorio>` calculadas con `src/taxonomia.py`. Se ve en `/notas-de-prensa/` y se filtra por modo, tema y comunidad como las piezas. Lleva visible «Nota de prensa · Comunicado de empresa · no es contenido editorial de MOTICIAS» y, si es del grupo, «Empresa del grupo editor».

#### Escenario: nota sin ejes
- CUANDO una nota no tiene modo, tema o territorio
- ENTONCES `src/prensa_publicar.py` los propone con la taxonomía y no publica sin ellos.

## ADDED Requisito: asesor de comunicación
`src/prensa_asesor.py` puntúa de 0 a 100 en cinco dimensiones (noticiabilidad 30, estructura 20, claridad y longitud 20, tono 15, datos y verificabilidad 15), lista avisos con la frase concreta y su arreglo, propone titular y entradilla, y nunca añade hechos. La segunda pasada con la API de Claude es opcional y marca `[DATO]` lo que falte.

#### Escenario: nota promocional
- CUANDO la nota describe un producto sin hecho fechado ni cifra
- ENTONCES el asesor lo dice («esto es publicidad, no una nota de prensa») y recomienda contenido patrocinado o publicación gratuita, nunca difusión.

## ADDED Requisito: recomendación honesta
La recomendación usa la audiencia real (contactos que pasan los filtros para los ejes de la nota y medios del catálogo) y la explica en una frase por opción. Si con la audiencia disponible la difusión de pago no alcanza el mínimo del plan, dice que no conviene pagarla y cuántos destinatarios hay.

## ADDED Requisito: destinatarios de la base de prensa
No hay lista propia: los destinatarios son los medios y periodistas de la base de prensa (`prensa-y-medios`). `src/prensa_valor.py` elige por relevancia en los tres ejes (≥ 3), excluye «No contactar», archivados y «poco colaboradores», y respeta el tope semanal (2 notas por periodista, 3 por buzón). Lectores B2C, solo por el boletín «Notas de prensa» de Ghost.

#### Escenario: importación de LinkedIn
- CUANDO se procesa `Connections.csv`
- ENTONCES solo salen los periodistas de medios que ya están en la base, con rol y fuente, en el formato de `src/prensa.py sql`; los demás contactos no entran en la base de prensa.

## ADDED Requisito: difusión con filtro de valor y aprobación
`src/prensa_difusion.py planificar` aplica las tres puertas (nota ≥ umbral, relevancia ≥ 3, tope semanal) y deja un envío en borrador de la base de prensa con cada destinatario y su motivo, y avisa a quien aprueba. Se aprueba y envía en la pestaña «Prensa» del gestor: el editor jefe siempre; la oficina, solo notas de prensa de clientes. B2C nunca recibe una nota suelta: va al resumen semanal.

#### Escenario: plan sin aprobar
- CUANDO alguien sin permiso pulsa «Aprobar y enviar» (oficina en un envío de MOTICIAS, o editor/comercial)
- ENTONCES el servidor responde 403 y no sale nada.

## ADDED Requisito: informe de repercusión
`src/prensa_impacto.py` clasifica candidatos en `reproduccion`, `adaptacion`, `mencion` o `descartado` por contención de frases de seis palabras, cita, cifras y nombre de la organización, con fecha posterior a la publicación o al embargo. Solo `reproduccion` y `adaptacion` se verifican solas; `mencion` necesita revisión humana. El informe muestra cada impacto con medio, fecha, URL, tipo y evidencia; alcance potencial solo con audiencia declarada y su fuente; impactos estimados como horquilla con los coeficientes declarados; métricas propias medidas. Nunca AVE.

#### Escenario: medio sin audiencia declarada
- CUANDO un impacto está en un medio sin audiencia declarada
- ENTONCES el impacto cuenta y se lista, pero no suma alcance ni impactos estimados, y el informe lo dice.

## ADDED Requisito: oferta
Planes y opciones de visibilidad en `verticals/movilidad.json → prensa`; texto público en `docs/prensa/oferta.md`. Las tarifas son hipótesis hasta que Rainer las confirme.
