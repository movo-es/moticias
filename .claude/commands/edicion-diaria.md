---
description: Redacta, verifica y publica la edición diaria de MOTICIAS (portal, hemeroteca y repositorio)
---

Ejecuta la rutina «edición diaria» de MOTICIAS tal como está escrita en `docs/tarea-edicion-diaria.md`. Léela entera antes de empezar y síguela paso a paso; `docs/manual-operativo.md` manda si discrepan. Hoy es $ARGUMENTS (si está vacío, usa la fecha de `current_time` en Europe/Madrid).

Si la edición de hoy ya está cerrada en el portal (`editions/{hoy}` existe) pero falta algún paso posterior —hemeroteca (7 bis), repositorio (7 ter), moticias.com (7 quater) o menciones (7 quinquies)—, no escribas piezas nuevas: completa solo los pasos que falten, en ese orden, y avisa.

Tipo de contenido (cambio `tipos-de-contenido`, 15-11-2026): toda pieza nueva nace con `tipo_contenido` (`noticia`; `editorial` para el análisis y los reportajes) y, antes del commit, `python3 -I src/tipos.py migrar && python3 -I src/tipos.py validar && python3 -I src/taxonomia.py etiquetas --aplicar && python3 -I src/taxonomia.py validar` no da errores. Sin él, `ghost_publish.py` no sube la pieza.

Entradilla (cambio `entradilla-y-linkedin`, 17-11-2026): toda pieza nace con `entradilla`, el texto de las tarjetas, de los listados y de lo que se comparte en LinkedIn —una o dos frases completas que dicen el hecho, como mucho 280 caracteres contando espacios, acabada en punto, sin puntos suspensivos y solo con hechos que están en la pieza—. No es el `summary` recortado: se escribe para caber. `python3 -I src/entradilla.py proponer data/articles/<id>.json` la propone y `python3 -I src/entradilla.py validar` no da errores antes de guardar.

Secciones (15-11-2026): tras publicar, `python3 -I src/secciones.py comprobar --navegador` (paso 7 septies); lo que no cuadre va en el aviso.
