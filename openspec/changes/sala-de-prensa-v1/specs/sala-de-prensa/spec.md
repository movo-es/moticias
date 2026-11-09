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

## ADDED Requisito: base de contactos privada
Los contactos (nombre, correo, cargo, organización, medio, tipo, intereses en los tres ejes, base legal, consentimiento con fecha y origen, frecuencia, estado, métricas) viven en `movo-es/moticias-equipo/prensa/contactos.json`. Nunca en este repositorio. Tipos: `redaccion`, `periodista`, `newsletter`, `decisor-b2b`, `profesional`, `particular`. Estados: `activo`, `pendiente-opt-in`, `pausado`, `baja`, `rebotado`. Una baja nunca se borra (se conserva para no volver a escribir).

#### Escenario: importación de LinkedIn
- CUANDO se importa `Connections.csv`
- ENTONCES los periodistas y redacciones identificados por cargo o por empresa del catálogo de medios entran `activo` con base `interes-legitimo-prensa` e información en el primer envío, el resto entra `pendiente-opt-in` y no recibe nada hasta darse de alta, y ningún contacto ya dado de baja vuelve a activarse.

## ADDED Requisito: difusión con filtro de valor y aprobación
`src/prensa_difusion.py planificar` aplica las tres puertas (nota ≥ umbral, relevancia del destinatario ≥ 3, frecuencia semanal) y deja el plan con cada destinatario y su motivo. `enviar` solo actúa con el plan aprobado (`aprobado_por`, `aprobado_en`), en horario laborable de 08:30 a 11:30, por Brevo, con etiqueta `np-<id>`, enlace de baja por sector y «Por qué le llega». B2C nunca recibe una nota suelta: va al resumen semanal.

#### Escenario: plan sin aprobar
- CUANDO se ejecuta `enviar` sobre un plan sin aprobación
- ENTONCES no se envía nada y se dice quién tiene que aprobarlo.

## ADDED Requisito: informe de repercusión
`src/prensa_impacto.py` clasifica candidatos en `reproduccion`, `adaptacion`, `mencion` o `descartado` por contención de frases de seis palabras, cita, cifras y nombre de la organización, con fecha posterior a la publicación o al embargo. Solo `reproduccion` y `adaptacion` se verifican solas; `mencion` necesita revisión humana. El informe muestra cada impacto con medio, fecha, URL, tipo y evidencia; alcance potencial solo con audiencia declarada y su fuente; impactos estimados como horquilla con los coeficientes declarados; métricas propias medidas. Nunca AVE.

#### Escenario: medio sin audiencia declarada
- CUANDO un impacto está en un medio sin audiencia declarada
- ENTONCES el impacto cuenta y se lista, pero no suma alcance ni impactos estimados, y el informe lo dice.

## ADDED Requisito: oferta
Planes y opciones de visibilidad en `verticals/movilidad.json → prensa`; texto público en `docs/prensa/oferta.md`. Las tarifas son hipótesis hasta que Rainer las confirme.
