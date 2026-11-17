# Capacidad: menú y «La voz del editor» · delta del cambio `voz-visual`

## ADDED Requisitos

### Requisito: sin publicidad que compita arriba (cambio `voz-visual`, 17-11-2026)
En `/la-voz-del-editor/` y en cada columna no hay cajas de publicidad ni de contenido patrocinado arriba, en el lateral ni en medio. Como mucho una, al final.

#### Escenario: página de la sección
- CUANDO un lector abre `/la-voz-del-editor/`
- ENTONCES entre la cabecera y las columnas no hay ninguna caja, y al final hay como mucho una

#### Escenario: una columna
- CUANDO un lector abre una columna
- ENTONCES no hay caja lateral ni dentro del texto, y al final hay como mucho una

### Requisito: siempre con imagen, y bien elegida (cambio `voz-visual`, 17-11-2026)
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

### Requisito: aspecto de la sección y de la columna (cambio `voz-visual`, 17-11-2026)
La página de la sección enseña la última columna en grande, con su imagen y el titular encima, y las anteriores en rejilla con imagen; ninguna tarjeta sale sin foto. Cada columna se abre con la imagen a toda la anchura, la marca «Opinión · La voz del editor», el titular y la firma; el texto va en serif a una columna y las cifras, la guía rápida y las fuentes quedan recogidas al final, sin desaparecer de la página.

#### Escenario: la marca de opinión
- CUANDO un lector abre una columna
- ENTONCES ve «Opinión · La voz del editor» antes del titular
