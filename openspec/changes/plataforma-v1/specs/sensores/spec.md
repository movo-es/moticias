# Capacidad: sensores compartidos (delta)

## ADDED Requisito: toda búsqueda deja señal
Cada hallazgo de los agentes (edición diaria, radar, licitaciones, barrido de mediodía) se guarda como señal estructurada en la tabla común `senales`: fecha, fuente, tipo (noticia, norma, licitación, nombramiento, incidente, riesgo, buena práctica, idea), entidades, ámbito, sentimiento, relevancia, resumen, enlace, y quién la usa (moticias, amarantia, inteligencia).

## ADDED Requisito: entidades vigiladas
`verticals/<id>.json` y la configuración de Amarantia definen entidades y palabras de riesgo; una señal que las toque se marca y se expone en una vista por entidad para Amarantia, sin tocar el motor.

#### Escenario: señal de riesgo sobre una entidad vigilada
- CUANDO una señal de tipo `riesgo` o `incidente` menciona una entidad vigilada
- ENTONCES queda disponible para Amarantia con relevancia alta en menos de una hora desde el barrido.

## ADDED Requisito: un solo almacén
La tabla `senales` es la misma para MOTICIAS, Amarantia y el hub Inteligencia de MOVO, o se sincroniza con el Airtable actual de Inteligencia hasta la migración. La parte de información reservada de Amarantia se procesa con el modelo local y no sale del almacén reservado.
