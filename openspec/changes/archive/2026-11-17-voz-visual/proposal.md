# Cambio: voz-visual

Fecha: 17 de noviembre de 2026. Origen: petición de Rainer del 17-11-2026 por la noche («En cuanto a "La Voz del Editor" tiene que quedar mucho más bonito y visual: nada de banners que compitan arriba (sólo al final) y siempre con una buena imagen bien seleccionada»). Estado: aplicado; pendiente de que lo vea en la web.

## Qué se veía
- La página `/la-voz-del-editor/` era la lista común de las secciones: una tarjeta pequeña —con un rótulo «Todos los modos» en lugar de la foto, porque el índice no traía la imagen que subió el gestor— y, pegadas debajo, dos cajas «Contenido patrocinado» que ocupaban más que la columna.
- Cada columna usaba la plantilla de las noticias: titular, entradilla cortada, foto y un bloque de texto en palo seco, con cifras, guía rápida y fuentes al mismo tamaño que el argumento. No se leía como una columna.
- La única columna publicada lleva una foto de 1.024 px, blanda al abrirla a toda la anchura. Y una columna escrita por el editor jefe podía aprobarse sin imagen.

## Decisiones
1. **Publicidad.** En la página de la sección y en cada columna, ninguna caja arriba ni en medio: se quitan el lateral del artículo y las cajas intermedias de la sección; queda una sola, al final (el cierre de la columna o la de antes del pie, nunca las dos).
2. **La página de la sección.** Cabecera propia en azul marino con el nombre, lo que es y la firma; la última columna en grande, con su imagen a toda la anchura y el titular encima; las anteriores, en rejilla de tarjetas con imagen; cierre con «Una columna nueva cada lunes · Suscríbete gratis».
3. **Cada columna.** La imagen abre a toda la anchura con la marca «Opinión · La voz del editor», el titular y la firma encima (la marca de opinión sigue siempre visible); el primer párrafo —la respuesta directa— pasa a entrada destacada; el texto, en la serif de la casa (Newsreader) y a una columna de 720 px, con capitular e intertítulos con filete naranja; cifras, guía rápida y fuentes siguen en la página, recogidas al final en «Datos y fuentes de esta columna» (abierto en el ordenador, plegado en el móvil); cierre con «Todas las columnas» y «Suscríbete gratis».
4. **Siempre con imagen.** El gestor no deja aprobar una columna sin imagen, sin crédito o sin licencia. La que escribe el editor jefe nace sin foto: el gestor encarga la imagen a la redacción en el momento.
5. **Bien elegida.** Tres candidatas miradas una a una; horizontal, de 1.600 px de ancho o más, nítida, del asunto concreto y con una idea visual clara; la mejor en `image` y las otras dos guardadas como alternativas. Lo que se puede medir (ancho, proporción, crédito, licencia, texto alternativo) lo comprueba `src/voz.py`; una imagen pequeña o vertical avisa en el gestor, pero la decisión es del editor jefe.
6. **Nunca una tarjeta sin foto.** Si el índice no trae la imagen de una columna, la página la toma de la propia columna.
7. **Dónde vive.** En `app/public/sitio/m.js` (apartados 1 y 9), como el menú, hasta que el tema de Ghost se versione: entra en vigor con el despliegue, sin tocar Ghost.

## De paso
- El índice del buscador dejaba fuera durante una hora lo recién publicado (comparaba textos de fecha con distinto huso). Ahora compara instantes (`export_search_index.en_el_futuro`); lo mismo en las tarjetas de «La voz del editor» del gestor.

## Qué no cambia
La firma, la aprobación obligada del texto y de la imagen, la salida de los lunes, la nota de intereses, y que una columna no lleva cajas de contenido patrocinado dentro del texto.

## Lo que queda para Rainer
- Verlo en `https://www.moticias.com/la-voz-del-editor/` tras el despliegue.
- La foto de «El polígono no tiene plan» no cumple el listón nuevo (1.024 px): elegir una de las candidatas que se le proponen o pedir otras.
