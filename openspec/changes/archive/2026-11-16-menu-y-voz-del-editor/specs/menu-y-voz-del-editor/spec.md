## ADDED Requirements

### Requisito: menú con submenús
moticias.com tiene un menú compacto con acceso directo a medios y sus modos, logística, temas y regiones, con «La voz del editor» destacada; en el móvil no tapa los titulares y los submenús se abren como hoja inferior.

#### Escenario: abrir Tierra en el móvil
- DADO un lector en el móvil
- CUANDO toca «Tierra»
- ENTONCES se abre una hoja inferior con «Todo tierra» y cada modo con su número de piezas, y se cierra al tocar fuera o con Escape

### Requisito: La voz del editor
Las columnas de opinión del editor jefe se marcan «Opinión · La voz del editor», van firmadas «Rainer Uphoff», tienen su página y no cuentan en su cupo de firma. Los sábados se proponen dos o tres; solo se publica lo que el editor jefe aprueba (texto e imagen), el lunes a las 08:00.

#### Escenario: sin aprobación
- DADO una propuesta del sábado
- CUANDO el editor jefe no la aprueba
- ENTONCES sigue en borrador y no se publica

#### Escenario: aprobación
- DADO una propuesta con imagen
- CUANDO el editor jefe marca el texto y la imagen y pulsa «Aprobar y programar»
- ENTONCES la pieza queda programada en Ghost para el lunes siguiente a las 08:00 (Europe/Madrid)
