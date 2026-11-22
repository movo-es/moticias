# Cambio: imagenes-de-banner

Fecha: 22 de noviembre de 2026. Origen: petición de Rainer del 22-11-2026 («En el gestor de contenidos patrocinados debes incluir la posibilidad (si no está hecho, comprueba) de subir imágenes que encajen en los diferentes formatos, dando instrucciones claras para qué formato de banner vertical o horizontal se necesitan cuantos pixels. Si no coinciden con la proporción no se estiran sino se encajan. Antes de subir, un preview»). Estado: aplicado.

## Qué había (comprobado)
El banner premium ya admitía imagen desde el 16-11-2026: el gestor daba los píxeles del formato elegido y subía la imagen a Ghost. Faltaba:
1. Una vista de conjunto de las medidas: solo se veían las del formato marcado, y los nombres de los formatos («Vertical mediano», «Cuadrado mediano») no decían la forma real de la caja.
2. Encajar: si la proporción no cuadraba, la única salida era recortar. Y en la web, en el móvil sin imagen propia, la imagen de escritorio se cortaba por abajo.
3. Vista previa: se veía el recorte, pero no cómo quedaba la caja en el ordenador y en el móvil, con su etiqueta.

## Decisiones
1. **Tabla de medidas** en el editor del banner: por cada formato, su forma real (calculada de la rejilla: horizontal, casi cuadrada, banda…) y los píxeles de la imagen que hay que subir (ancho × alto, al doble de como se ve), más la del móvil.
2. **Nunca se estira.** Si la imagen no tiene la proporción del formato, por defecto se **encaja entera** y lo que sobra es banda de color (el del borde de la imagen, o uno de la paleta de MOTICIAS); quien la sube puede elegir **recortar para llenar**, moviendo el encuadre. La imagen se compone en el navegador a los píxeles exactos del formato.
3. **Vista previa antes de subir**: la caja con su etiqueta, tal como se verá en el ordenador y en el móvil. Nada llega al servidor hasta pulsar «Subir esta imagen»; «Elegir otra» lo descarta.
4. **En la web** la caja del banner guarda siempre la proporción de su formato, a cualquier ancho de pantalla (antes el alto dependía de la separación de la rejilla y variaba unos puntos). Una imagen hecha a medida la llena entera; donde la proporción no coincide (el móvil sin imagen propia, una imagen hecha para otro formato) sale entera y centrada sobre el color de las bandas (`imagen_fondo`), nunca estirada ni cortada.
5. Si se cambia el formato con una imagen ya subida para otro, el gestor lo avisa.

## Dónde
`app/public/gestor/index.html` (editor del banner), `api/gestor.py` (`imagen_fondo`: campo, validación y salida pública), `app/public/sitio/m.js` (apartado 1 bis), pruebas en `tests/test_imagen_banner.py` y `tests/navegador/test_imagen_banner.py`.

## Qué no cambia
Formatos y rejilla, texto alternativo obligatorio, etiqueta siempre visible, `rel="sponsored"`, medición, tope de huecos de pago. Las cajas de los demás huecos (lateral, portada, cierre, pie) siguen siendo de texto.

## Pendiente
- El formato de los banners **de texto**: Rainer lo pidió «así», con un ejemplo que no llegó con el mensaje. Se hará cuando lo reenvíe.
- Ningún formato de la rejilla es claramente vertical: el más alto, 2x4, mide 588 × 644 px. Si se quiere un banner vertical de verdad, hace falta un formato nuevo (decisión de Rainer).
