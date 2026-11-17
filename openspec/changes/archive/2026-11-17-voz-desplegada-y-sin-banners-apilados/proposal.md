# Cambio: voz-desplegada-y-sin-banners-apilados

Fecha: 17 de noviembre de 2026. Origen: petición de Rainer del 17-11-2026 por la noche, sobre una captura de `moticias.com/la-voz-del-editor/` («El último "Voz del Editor" debe aparecer desplegado y una columna a la derecha (no dominante) tendrá referencia a los artículos previos. Y abajo no debe haber nunca dos banners uno encima de otro en ninguna sección»). Estado: aplicado.

## Por qué
1. La página de «La voz del editor» era un listado como el de cualquier sección: titular, entradilla cortada y un cuadro azul sin foto. Una columna de opinión se lee entera; el listado obligaba a un clic más y la hacía parecer una noticia.
2. Al pie de las páginas de sección (y del artículo) salían dos cajas seguidas: la del hueco estándar de la plantilla y la del hueco básico «antes del pie» que pone `m.js`. Dos cajas una encima de otra parecen un bloque de anuncios y restan credibilidad.

## Decisiones
1. **Última columna desplegada.** En `/la-voz-del-editor/` la columna más reciente se ve completa: marca «Opinión · La voz del editor», tema y fecha, titular, subtítulo, firma con fecha y hora, foto con su crédito y el texto entero. El texto se toma tal cual de la página de la columna (mismo dominio); no se reescribe nada. Si no se puede leer, queda el resumen con «Leer la columna completa». Al final, enlace a su página para compartir o comentar.
2. **Columna derecha, no dominante** (280 px, letra pequeña, filete a la izquierda, fija al desplazar): «Columnas anteriores», con fecha, tema y titular de cada una, de la más reciente a la más antigua. Si solo hay una: «Esta es la primera columna. Las siguientes dejarán aquí las anteriores». En el móvil va debajo de la columna.
3. **Nunca dos cajas una encima de otra**, en ninguna página: si dos cajas de publicidad, patrocinio o «Contenido patrocinado» quedan seguidas en vertical sin contenido entre ellas (texto visible, imagen o vídeo; los comentarios, que suelen estar vacíos, no separan), se queda la de más rango —contenido patrocinado del texto > pagada > del grupo o de la plantilla— y, a igualdad, la de arriba; la otra se quita con su hueco. Las que van una al lado de otra (lateral del artículo) no cuentan. Se comprueba al poner la publicidad y cada vez que se pinta una sección. Una caja quitada no cuenta visualizaciones.

4. **Caja de MOVO bajo la columna** (petición de Rainer, misma noche: «pon debajo un banner de movo con mensaje de que todavía están a tiempo»): `data/ads/grupo-movo-pmst-a-tiempo.json`, «Plan de movilidad al trabajo: todavía estás a tiempo», hueco estándar de `/la-voz-del-editor/`, del 17-11 al 5-12-2026 (el día del plazo), enlace a `movo.es/pmst/`, etiqueta «Contenido patrocinado». Va fuera del texto de la columna, que sigue sin cajas. Para que salga ahí: en las páginas de sección la publicidad conoce ya su sección (antes solo la conocía en los artículos) y una caja pensada para una sección va delante de las genéricas del mismo rango.

## Dónde
`app/public/sitio/m.js` (apartados 1 ter y 6 bis), hasta que el tema se versione (`publicar-en-ghost-v1`); entonces pasa a la plantilla.

## Qué no cambia
El tope de tres huecos de pago por página, las etiquetas, `rel="sponsored"`, la firma y la marca de la columna, las demás secciones (siguen como listado) y que las columnas nunca llevan cajas de contenido patrocinado.
