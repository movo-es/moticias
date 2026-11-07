# Firma y estado en Ghost

## Por qué
El director fijó el 7-11-2026 que las piezas rutinarias salgan firmadas por G. Jordan y se publiquen solas, y que las críticas, los análisis y los reportajes salgan firmados por él y esperen su aprobación. El publicador de Ghost asignaba un autor por defecto y publicaba todo con el mismo estado.

## Qué cambia
- `verticals/movilidad.json` → `editorial.ghost_authors` y `editorial.ghost_status`.
- `src/ghost_publish.py`: autor de Ghost según la firma (por slug y, si no, por nombre; si falta G. Jordan, Rainer y aviso); las críticas siempre en `draft`; opción `--pages` para páginas fijas en borrador.
- `data/articles/*` y `hemeroteca/data/2026-11.json`: `risk`, `review_note`, `author`, `author_role` y `status` en las 74 piezas.
- `data/paginas/`: aviso legal, privacidad, cookies y «Cómo trabajamos».
- `docs/firma-y-publicacion.md`, `docs/tarea-edicion-diaria.md` (paso 7 quáter), `docs/arquitectura.md`, `docs/manual-operativo.md`.
