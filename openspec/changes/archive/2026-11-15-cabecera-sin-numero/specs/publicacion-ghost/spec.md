## ADDED Requirements

### Requisito: cabecera sin número de edición
La cabecera de moticias.com muestra solo la fecha y la hora de la edición; el número de edición no se enseña al lector y se conserva en `data/editions/` y en la etiqueta interna `moticias-edicion` de la página `edicion-hoy`.

#### Escenario: edición publicada
- DADO que se publica la edición nº 9 del 14-11-2026
- CUANDO el lector abre www.moticias.com
- ENTONCES la cabecera dice «sábado, 14 de noviembre de 2026» y la hora de cierre o actualización, y no dice «Edición nº 9»
- Y el cron `ghost_al_dia` sigue sabiendo que la web tiene la nº 9
