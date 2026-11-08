# Capacidad: navegación por facetas y portada (tema de Ghost)

Se aplica al tema de moticias.com cuando `publicar-en-ghost-v1` lo versione en `ghost/theme/`. La maqueta de referencia es `openspec/changes/navegacion-y-buscador/maqueta/index.html`.

## Requisito: una barra, tres menús
Bajo la cabecera hay una sola barra fija con: menú Modo, menú Tema, menú Territorio, botón «Análisis del director» y buscador. Cada menú muestra el número de piezas de cada opción contando los demás filtros activos; las opciones a cero se atenúan pero siguen pulsables. Los filtros activos se muestran como fichas con aspa y «Quitar filtros». El estado va en la URL (`?sub=…&tema=…&terr=…&q=…`) y las páginas de etiqueta de Ghost (`/tag/m-autobus/`, `/tag/t-cantabria/`, `/tag/tema-concesiones/`) son el equivalente indexable de cada filtro simple; `routes.yaml` da rutas limpias a los modos (`/tierra/`, `/mar/`, `/aire/`, `/logistica/`), a `/analisis/` (con RSS) y a `/territorio/<id>/`.

#### Escenario: cruce de filtros
- CUANDO el lector elige Autobús y después abre Territorio
- ENTONCES el mapa y la lista muestran solo cuántas piezas de autobús hay en cada comunidad.

## Requisito: territorio en mapa
El menú Territorio ofrece los tres ámbitos como fichas y las comunidades en un mapa (provincias de `portal/spain.js` agrupadas por comunidad, coloreadas en tres tonos según el número de piezas) y en lista. En móvil el mapa ocupa como mucho 210 px de alto y la lista va en dos columnas.

## Requisito: análisis del director
La portada lleva un módulo propio «Análisis del director» con el último análisis (titular, firma «Rainer, director de MOTICIAS», fecha), los tres anteriores y «Todos los análisis →». En escritorio es la columna derecha, fija al hacer scroll; en móvil es la segunda tarjeta, tras la apertura. El módulo no lleva nunca cajas patrocinadas ni publicidad.

## Requisito: móvil visual
Por debajo de 760 px no se muestran la franja superior, el claim ni la presentación; la portada empieza con la apertura (foto, modo · territorio, titular, fecha) y sigue con tarjetas de dos columnas con foto y titular, sin resúmenes. Los resúmenes y los subtítulos se muestran solo en escritorio.

## Requisito: fichas de pieza
Cada tarjeta lleva un punto de color del modo, el submodo y hasta dos comunidades, el titular, la fecha, «Rainer, director» si es análisis y la marca «patrocinio» si la pieza lleva cajas (art. 20 LSSI). Una foto no se repite en la misma página.
