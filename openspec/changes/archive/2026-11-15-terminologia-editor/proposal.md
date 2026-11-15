# Cambio: terminologia-editor

Fecha: 15 de noviembre de 2026. Origen: encargo de Rainer del mismo día (punto 1 de su cola, «sin entrevista»). Estado: aplicado y archivado el 15-11-2026.

Respuesta corta: en una publicación se dice «editor», no «director». Rainer es el **editor jefe** de MOTICIAS y firma «Rainer Uphoff». «Análisis del director» desaparece como marca, módulo y botón: el tema y la marca se llaman «Análisis», con el autor que firme cada pieza.

## Qué cambia
- Textos visibles: moticias.com (marca de los análisis, cargo en los datos estructurados `jobTitle`, nota de intereses de las piezas de la redacción, descripción de la sección y página «Análisis», página «Cómo trabajamos», `llms.txt`), gestor (firma «Editor jefe de MOTICIAS», botón de firma, avisos de restauración), correos y avisos (asuntos y cuerpos), comandos de las tareas y documentación (`CLAUDE.md`, `docs/`, specs vivas y cambios en curso).
- `verticals/movilidad.json`: `director_role` = «Editor jefe de MOTICIAS»; `marcas.analisis_director` = «Análisis» (la marca ya no distingue al autor); sinónimos del buscador: «editor jefe».
- Datos: `author_role` de las 5 piezas firmadas por Rainer y las notas de intereses de 4 piezas de la redacción. No se añade `revised_at`: es un cambio de denominación, no una corrección de un hecho.
- Republicadas en moticias.com las 9 piezas afectadas (las 5 en borrador siguen en borrador).
- «Cuaderno del director»: no existe en moticias.com (devuelve 404, nunca se publicó allí); solo estaba en el portal espejo de artefactos. Se retira allí (borrador y solo con enlace, `data/blogs/cuaderno-del-director.json`), sin borrarlo; sus piezas siguen en «Análisis» y «Reportaje». No hace falta redirección.

## Nombres internos que NO cambian (cambiarlos rompería datos, enlaces o la base)
Campos `firma_director`, `editorial.director`, `director_role`, `director_firma_antigua`, `prensa.aviso_director`; funciones `es_del_director`; etiqueta interna de Ghost `#analisis-director` (ya sin módulo ni botón, solo dato); id del blog `cuaderno-del-director`; comando `/retoques` y fichero `.claude/commands/retoques.md`; nombre de la tarea programada «MOTICIAS · retoques del director» (el guardián de tareas la cita por ese nombre); historiales (`docs/ediciones.md`, `docs/asesor/`, cambios archivados) y migraciones ya aplicadas.
