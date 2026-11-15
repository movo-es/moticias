# Cambio: cabecera-sin-numero

Fecha: 15 de noviembre de 2026. Origen: encargo de Rainer del mismo día (punto 0 de su cola, «sin entrevista»). Estado: aplicado y archivado el 15-11-2026.

Respuesta corta: la cabecera de www.moticias.com deja de enseñar «Edición nº N». Enseña solo la fecha («sábado, 14 de noviembre de 2026») y la hora (cierre y última actualización). El número se conserva en los datos internos.

## Qué cambia
- `src/ghost_edicion.py`: el título de la página `edicion-hoy` (que el tema pinta en la barra superior y como titular de la edición) es solo el día. El número va en la inyección de cabecera de esa página, `<meta name="moticias-edicion" content="N">`, que el lector no ve.
- `api/gestor.py → ghost_al_dia`: sabe qué edición tiene la web leyendo esa etiqueta (y, para las páginas antiguas, el título). Si no encuentra ninguna de las dos, no republica todas las ediciones a ciegas: avisa con error.
- `docs/tarea-edicion-diaria.md`: la comprobación final busca la fecha, no el número.

## Qué no cambia
`data/editions/*.json` sigue llevando `number`; `docs/ediciones.md`, la nota metodológica y el resumen al pie de la edición siguen citando el número (no son cabecera).
