## MODIFIED

### Requisito: creatividad
Un banner es una imagen (con texto alternativo obligatorio e imagen opcional para el móvil) o una caja de texto con fondos y tipografías de MOTICIAS, límites de caracteres y contraste mínimo 4,5 : 1. El gestor enseña una tabla con la forma real de cada formato y los píxeles de la imagen que hay que subir (al doble de como se ve), más la del móvil.

## ADDED

### Requisito: la imagen nunca se estira
Si la imagen no tiene la proporción del formato, se encaja entera y lo que sobra es banda de color (el del borde de la imagen o uno de la paleta), o se recorta si quien la sube lo elige. En la web la caja guarda la proporción de su formato a cualquier ancho; donde la proporción no coincide, la imagen sale entera y centrada sobre el color de las bandas.

#### Escenario: imagen apaisada en un formato alto
- DADO el formato 2x4 (1176 × 1288 px) y una imagen de 1200 × 400 px
- CUANDO el editor la elige en el gestor
- ENTONCES ve el aviso con las dos medidas, la imagen entera con bandas arriba y abajo, y puede cambiar el color de las bandas o pasar a recortar

#### Escenario: móvil sin imagen propia
- DADO un banner de imagen sin imagen para el móvil
- CUANDO un lector abre la portada en el móvil
- ENTONCES la imagen se ve entera dentro de la franja, con bandas del color elegido, sin estirar ni cortar

### Requisito: vista previa antes de subir
Al elegir una imagen, el gestor enseña la caja con su etiqueta tal como se verá en el ordenador y en el móvil. Nada llega al servidor hasta pulsar «Subir esta imagen».

#### Escenario: descartar
- DADO una imagen elegida y su vista previa
- CUANDO el editor pulsa «Elegir otra»
- ENTONCES no se ha subido nada y la caja sigue como estaba
