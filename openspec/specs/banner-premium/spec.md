# Capacidad: banner premium (cambio `banner-premium`, 16-11-2026)

### Requisito: posición del banner premium
En la portada el banner premium va un escalón por debajo de la apertura, alineado a la derecha y con el ancho de su formato; nunca encima ni al lado del titular de apertura. En el móvil va como franja horizontal debajo de los titulares visuales. Hay como mucho tres huecos de pago por página.

#### Escenario: banda 4x1
- DADO un banner con formato 4x1
- CUANDO un lector abre la portada en un ordenador
- ENTONCES el banner ocupa todo el ancho, 140 px de alto, debajo de la apertura, con su etiqueta visible y enlace `rel="sponsored"`

### Requisito: creatividad (cambio `imagenes-de-banner`, 22-11-2026)
Un banner es una imagen (con texto alternativo obligatorio e imagen opcional para el móvil) o una caja de texto con fondos y tipografías de MOTICIAS, límites de caracteres y contraste mínimo 4,5 : 1. El gestor enseña una tabla con la forma real de cada formato y los píxeles de la imagen que hay que subir (al doble de como se ve), más la del móvil.

### Requisito: la imagen nunca se estira (22-11-2026)
Si la imagen no tiene la proporción del formato, se encaja entera y lo que sobra es banda de color (el del borde de la imagen o uno de la paleta), o se recorta si quien la sube lo elige. En la web la caja guarda la proporción de su formato a cualquier ancho; donde la proporción no coincide, la imagen sale entera y centrada sobre el color de las bandas.

#### Escenario: imagen apaisada en un formato alto
- DADO el formato 2x4 (1176 × 1288 px) y una imagen de 1200 × 400 px
- CUANDO el editor la elige en el gestor
- ENTONCES ve el aviso con las dos medidas, la imagen entera con bandas arriba y abajo, y puede cambiar el color de las bandas o pasar a recortar

#### Escenario: móvil sin imagen propia
- DADO un banner de imagen sin imagen para el móvil
- CUANDO un lector abre la portada en el móvil
- ENTONCES la imagen se ve entera dentro de la franja, con bandas del color elegido, sin estirar ni cortar

### Requisito: vista previa antes de subir (22-11-2026)
Al elegir una imagen, el gestor enseña la caja con su etiqueta tal como se verá en el ordenador y en el móvil. Nada llega al servidor hasta pulsar «Subir esta imagen».

#### Escenario: descartar
- DADO una imagen elegida y su vista previa
- CUANDO el editor pulsa «Elegir otra»
- ENTONCES no se ha subido nada y la caja sigue como estaba

### Requisito: formulario de contacto
«Pide más información» abre un formulario con nombre, correo, código postal y país obligatorios; dice quién recibe los datos y pide consentimiento; cada envío se guarda en la base privada ligado a la campaña y llega al anunciante. Está apagado hasta que el editor jefe aprueba los textos legales.

#### Escenario: formulario apagado
- DADO que `publicidad.formulario.activo` es false
- CUANDO un banner tiene el botón «Pide más información»
- ENTONCES el lector ve «Ir a la web» y el servidor rechaza cualquier envío (403)

### Requisito: medición
Cada banner registra vistas, clics, clics en el botón, formularios abiertos y enviados, por procedencia, dispositivo y sección, sin datos personales; no cuentan robots ni el editor jefe.

### Requisito: nunca dos cajas una encima de otra (cambio `voz-desplegada-y-sin-banners-apilados`, 17-11-2026)
En ninguna página quedan dos cajas de publicidad, patrocinio o «Contenido patrocinado» seguidas en vertical sin contenido entre ellas (texto visible, imagen o vídeo). Se queda la de más rango (contenido patrocinado del texto > pagada > del grupo o de la plantilla) y, a igualdad, la de arriba; la otra se quita con su hueco. Las que van una al lado de otra no cuentan.

#### Escenario: pie de una sección
- DADO una sección cuyo último bloque es una caja y un hueco básico «antes del pie» con otra
- CUANDO se pinta la página
- ENTONCES solo queda una caja al pie

### Requisito: la caja de una sección va delante (17-11-2026)
En las páginas de sección la publicidad sabe en qué sección está, como en los artículos. Entre cajas del mismo rango, la que está pensada para esa sección (`sections`) va delante de las genéricas.

#### Escenario: MOVO bajo «La voz del editor»
- DADO la caja `grupo-movo-pmst-a-tiempo` activa para `la-voz-del-editor` en el hueco estándar
- CUANDO un lector abre `/la-voz-del-editor/` antes del 6-12-2026
- ENTONCES bajo la columna ve esa caja, con «Contenido patrocinado», y ninguna otra encima o debajo de ella
