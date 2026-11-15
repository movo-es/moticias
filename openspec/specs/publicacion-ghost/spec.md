# Capacidad: publicación en moticias.com (Ghost)

Estado: pendiente. Decidido el 7-11-2026: Ghost(Pro), plan Publisher; cuenta creada. Sin requisitos activos hasta el cambio `publicar-en-ghost`.

## Requisito previsto: publicación por API
Cada pieza cerrada se publica como post de Ghost con etiqueta de sección (`#tierra`, `#mar`, `#aire`, `#regulacion`, `#licitaciones`, `#analisis`), URL en subdirectorio, metadatos Schema.org `NewsArticle`, fuentes al pie con fechas y trazabilidad; cada edición, un boletín. Mientras Rainer no active la aprobación previa, se publica directamente; con aprobación, queda en borrador y él publica desde el móvil.

## Requisito: cabecera sin número de edición (cambio `cabecera-sin-numero`, 15-11-2026)
La cabecera de moticias.com muestra solo la fecha y la hora de la edición; el número no se enseña al lector y se conserva en `data/editions/` y en la etiqueta interna `<meta name="moticias-edicion">` de la página `edicion-hoy`, de la que lo lee el cron `ghost_al_dia`.
