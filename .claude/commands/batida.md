---
description: Batida de grandes noticias de fin de semana o a demanda (edición extra solo si algo lo merece; lo demás a data/reserva/ para el lunes)
---

Ejecuta la rutina «batida de fin de semana» de MOTICIAS tal como está escrita en `docs/tarea-batida.md`. Léela entera antes de empezar y síguela paso a paso; `docs/tarea-edicion-diaria.md` y `docs/manual-operativo.md` mandan en todo lo que no diga (estándar de las piezas, firma, portal, hemeroteca, repositorio, Ghost, menciones). Hoy es $ARGUMENTS (si está vacío, usa la fecha de `current_time` en Europe/Madrid).

Tipo de contenido (cambio `tipos-de-contenido`, 15-11-2026): toda pieza de la edición extra lleva `tipo_contenido` (`noticia` o `editorial`) y pasa `python3 -I src/tipos.py validar` antes de guardarse.

Secciones (15-11-2026): si hubo edición extra, `python3 -I src/secciones.py comprobar --navegador` y lo que no cuadre, al aviso.
