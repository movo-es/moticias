# Capacidad: menú y «La voz del editor» · delta del cambio `voz-desde-el-panel`

## ADDED Requisitos

### Requisito: La voz del editor desde el gestor (cambio `voz-desde-el-panel`, 16-11-2026)
La tarjeta «La voz del editor» está siempre arriba de la «Cola» del editor jefe. Desde ella encarga el borrador de una columna a la redacción (tema y enfoque) o la escribe él mismo; en los dos casos la columna queda pendiente. Al aprobar elige si sale en el momento o el lunes a las 08:00. Solo el editor jefe escribe, encarga y aprueba.

#### Escenario: encargar el borrador
- DADO el editor jefe en `app.moticias.com/gestor/?vista=cola&voz=nueva`
- CUANDO escribe el tema y su enfoque y pulsa «Encargar»
- ENTONCES queda un encargo para la redacción horaria, que deja en la tarjeta una propuesta pendiente con fuentes e imagen candidata y no publica nada

#### Escenario: escribirla él mismo
- DADO un título y un texto de al menos 120 palabras
- CUANDO pulsa «Guardar como pendiente»
- ENTONCES se crea una pieza `kind: opinion`, `status: pendiente`, firmada «Rainer Uphoff», con las etiquetas comunes, y se abre en el editor con vista previa

#### Escenario: publicar ahora
- DADA una columna pendiente
- CUANDO el editor jefe marca el texto y la imagen, elige «Publicar ahora» y pulsa «Aprobar»
- ENTONCES la columna se publica en moticias.com en ese momento con la marca «Opinión · La voz del editor»

#### Escenario: sin elegir
- DADA una columna pendiente
- CUANDO el editor jefe aprueba sin cambiar la opción marcada
- ENTONCES queda programada para el lunes siguiente a las 08:00 (Europe/Madrid)

#### Escenario: tema que toca a una empresa del grupo
- DADA una columna del editor jefe sobre un asunto en el que trabaja una empresa del grupo
- CUANDO se publica
- ENTONCES la nota de intereses nombra esa relación y la pieza no lleva cajas de contenido patrocinado
