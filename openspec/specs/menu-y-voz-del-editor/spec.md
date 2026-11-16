# Capacidad: menú y «La voz del editor» (cambio `menu-y-voz-del-editor`, 16-11-2026)

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

### Requisito: lo aprobado que no llega a la web se dice y se reintenta (cambio `subidas-que-no-llegan`, 16-11-2026)
Aprobar guarda la pieza como publicada y después la sube a Ghost. Si esa subida falla, el gestor no la da por publicada: lo dice, ofrece subirla y la reintenta solo.

#### Escenario: la subida falla al aprobar
- DADA una columna que el editor jefe aprueba con «Publicar ahora»
- CUANDO Ghost rechaza la subida
- ENTONCES el aviso dice que no ha llegado a la web, la tarjeta «La voz del editor» la enseña como «Aprobada, pero no ha llegado a la web» con el botón «Subir a la web ahora» y sin enlace público

#### Escenario: reintento automático
- DADA una pieza aprobada cuya última subida falló
- CUANDO corre el cron `web_reintentos` (cada 20 minutos)
- ENTONCES se vuelve a subir, el resultado queda en el registro y, si llega, deja de salir como fallida

#### Escenario: tope
- DADA una pieza con 12 reintentos automáticos fallidos
- CUANDO corre el cron
- ENTONCES no se reintenta más y el error sigue a la vista para subirla a mano

#### Escenario: fecha de «Publicar ahora»
- DADA una aprobación con «Publicar ahora»
- CUANDO se guarda la fecha de publicación
- ENTONCES lleva segundos y zona horaria (Ghost rechaza la fecha sin segundos)
