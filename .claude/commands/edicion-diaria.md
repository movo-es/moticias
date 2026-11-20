---
description: Redacta, verifica y publica la edición diaria de MOTICIAS (portal, hemeroteca y repositorio)
---

Ejecuta la rutina «edición diaria» de MOTICIAS tal como está escrita en `docs/tarea-edicion-diaria.md`. Sale todos los días, también sábados, domingos y festivos (decisión de Rainer, 20-11-2026). Léela entera antes de empezar y síguela paso a paso; `docs/manual-operativo.md` manda si discrepan. Hoy es $ARGUMENTS (si está vacío, usa la fecha de `current_time` en Europe/Madrid).

Si la edición de hoy ya está cerrada en el portal (`editions/{hoy}` existe) pero falta algún paso posterior —hemeroteca (7 bis), repositorio (7 ter), moticias.com (7 quater) o menciones (7 quinquies)—, no escribas piezas nuevas: completa solo los pasos que falten, en ese orden, y avisa.

Tipo de contenido (cambio `tipos-de-contenido`, 15-11-2026): toda pieza nueva nace con `tipo_contenido` (`noticia`; `editorial` para el análisis y los reportajes) y, antes del commit, `python3 -I src/tipos.py migrar && python3 -I src/tipos.py validar && python3 -I src/taxonomia.py etiquetas --aplicar && python3 -I src/taxonomia.py validar` no da errores. Sin él, `ghost_publish.py` no sube la pieza.

Secciones (15-11-2026): tras publicar, `python3 -I src/secciones.py comprobar --navegador` (paso 7 septies); lo que no cuadre va en el aviso.
