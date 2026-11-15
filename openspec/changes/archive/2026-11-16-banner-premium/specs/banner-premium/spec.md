## ADDED Requirements

### Requisito: posición del banner premium
En la portada el banner premium va un escalón por debajo de la apertura, alineado a la derecha y con el ancho de su formato; nunca encima ni al lado del titular de apertura. En el móvil va como franja horizontal debajo de los titulares visuales. Hay como mucho tres huecos de pago por página.

#### Escenario: banda 4x1
- DADO un banner con formato 4x1
- CUANDO un lector abre la portada en un ordenador
- ENTONCES el banner ocupa todo el ancho, 140 px de alto, debajo de la apertura, con su etiqueta visible y enlace `rel="sponsored"`

### Requisito: creatividad
Un banner es una imagen con la proporción exacta del formato (con texto alternativo obligatorio e imagen opcional para el móvil) o una caja de texto con fondos y tipografías de MOTICIAS, límites de caracteres y contraste mínimo 4,5 : 1. El gestor da los píxeles ideales al doble y ofrece el recorte si la imagen no cuadra.

### Requisito: formulario de contacto
«Pide más información» abre un formulario con nombre, correo, código postal y país obligatorios; dice quién recibe los datos y pide consentimiento; cada envío se guarda en la base privada ligado a la campaña y llega al anunciante. Está apagado hasta que el editor jefe aprueba los textos legales.

#### Escenario: formulario apagado
- DADO que `publicidad.formulario.activo` es false
- CUANDO un banner tiene el botón «Pide más información»
- ENTONCES el lector ve «Ir a la web» y el servidor rechaza cualquier envío (403)

### Requisito: medición
Cada banner registra vistas, clics, clics en el botón, formularios abiertos y enviados, por procedencia, dispositivo y sección, sin datos personales; no cuentan robots ni el editor jefe.
