# Capacidad: publicidad y promoción discreta (delta)

## ADDED Requisito: la promoción vive fuera del texto
El cuerpo editorial nunca menciona soluciones del grupo ni de anunciantes. La relación pieza ↔ solución es un dato (`relaciones_solucion`) que la interfaz muestra en huecos señalizados: ficha de solución, caso, servicio («Valorar esta licitación con MOVO»), edición a medida, patrocinio.

#### Escenario: pieza sobre un mapa concesional
- CUANDO se publica una pieza de concesiones de autobús
- ENTONCES el hueco lateral puede mostrar la ficha de una solución relacionada (del grupo o de un anunciante) con la etiqueta visible «Contenido patrocinado» o «Servicio de MOVO», y el texto de la pieza no cambia.

## ADDED Requisito: huecos e inventario
Huecos según `docs/gestores-portal.md`: portada (tres posiciones), cabecera y banner de sección, artículo (lateral y cierre), blogs, boletín. Nunca sobre la apertura ni dentro del texto. Etiqueta siempre visible (art. 20 LSSI). Sin campaña de pago, autopromoción del grupo. Enlaces con UTM.

## ADDED Requisito: productos
Patrocinio de sección, banner, contenido patrocinado (señalizado y fuera de la selección automática de portada), edición a medida (asociación o empresa), ficha destacada en Soluciones tecnológicas. Importe, fechas, estado e inventario en el panel de anunciantes.

## ADDED Requisito: independencia editorial
La selección y el tratamiento de noticias no dependen de ser cliente; la declaración de intereses y la página «Cómo trabajamos» están siempre publicadas; existe una página pública de correcciones.
