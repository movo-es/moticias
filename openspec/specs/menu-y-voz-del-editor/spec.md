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

## Requisito: sin publicidad que compita arriba (cambio `voz-visual`, 17-11-2026)
En `/la-voz-del-editor/` y en cada columna no hay cajas de publicidad ni de contenido patrocinado arriba, en el lateral ni en medio. Como mucho una, al final.

#### Escenario: página de la sección
- CUANDO un lector abre `/la-voz-del-editor/`
- ENTONCES entre la cabecera y las columnas no hay ninguna caja, y al final hay como mucho una

#### Escenario: una columna
- CUANDO un lector abre una columna
- ENTONCES no hay caja lateral ni dentro del texto, y al final hay como mucho una

## Requisito: siempre con imagen, y bien elegida (cambio `voz-visual`, 17-11-2026)
Una columna no se aprueba ni se publica sin imagen con crédito y licencia. La imagen se elige entre tres candidatas miradas una a una: horizontal, de al menos 1.600 px de ancho (`verticals → voz_del_editor.imagen`), nítida, del asunto concreto. Una imagen más pequeña o vertical avisa al editor jefe, que decide.

#### Escenario: aprobar sin imagen
- DADA una columna pendiente sin imagen
- CUANDO el editor jefe intenta aprobarla
- ENTONCES el gestor no la aprueba y le dice que pida la imagen

#### Escenario: columna escrita por el editor jefe
- CUANDO el editor jefe escribe una columna en el gestor
- ENTONCES queda pendiente y el gestor encarga su imagen a la redacción

#### Escenario: imagen pequeña
- DADA una columna cuya imagen mide menos de 1.600 px de ancho
- CUANDO el editor jefe abre la hoja de aprobación
- ENTONCES ve la imagen y el aviso, y puede aprobarla o pedir otra

## Requisito: aspecto de la sección y de la columna (cambio `voz-visual`, 17-11-2026)
La página de la sección enseña la última columna en grande, con su imagen y el titular encima, y las anteriores en rejilla con imagen; ninguna tarjeta sale sin foto. Cada columna se abre con la imagen a toda la anchura, la marca «Opinión · La voz del editor», el titular y la firma; el texto va en serif a una columna y las cifras, la guía rápida y las fuentes quedan recogidas al final, sin desaparecer de la página.

#### Escenario: la marca de opinión
- CUANDO un lector abre una columna
- ENTONCES ve «Opinión · La voz del editor» antes del titular
