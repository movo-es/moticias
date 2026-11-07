# Capacidad: publicación en moticias.com (Ghost)

Estado: activa desde el 7-11-2026 (Ghost(Pro), plan Publisher). Publicador: `src/ghost_publish.py` (Admin API). Regla completa: `docs/firma-y-publicacion.md`.

## Requisito: publicación por API
Cada pieza cerrada se publica como post de Ghost con etiqueta de sección (`#tierra`, `#mar`, `#aire`, `#regulacion`, `#licitaciones`, `#analisis`), metadatos Schema.org `NewsArticle`, fuentes al pie con fechas y trazabilidad. Pendiente: URL en subdirectorio por sección y un boletín por edición.

## Requisito: firma y estado
El autor de Ghost sale de la firma de la pieza (`verticals/<id>.json` → `editorial.ghost_authors`) y el estado, de su clasificación.

### Escenario: pieza rutinaria
- DADO una pieza con `risk: rutinaria`
- CUANDO se ejecuta `ghost_publish.py --status published`
- ENTONCES el post queda `published` con autor G. Jordan

### Escenario: pieza crítica, análisis o reportaje
- DADO una pieza con `risk: critica` o `status: pendiente`
- CUANDO se ejecuta `ghost_publish.py --status published`
- ENTONCES el post queda `draft` con autor Rainer, a la espera de su aprobación

### Escenario: falta el usuario de G. Jordan
- DADO que Ghost no tiene usuario con slug `g-jordan` ni con nombre «G. Jordan»
- ENTONCES las piezas rutinarias salen a nombre de Rainer y el resultado lo avisa

## Requisito: páginas fijas
Las páginas de `data/paginas/` (aviso legal, privacidad, cookies, cómo trabajamos) se suben con `--pages` siempre como borrador; solo se publican por orden expresa del director.
