# Restauración desde el gestor

Spec viva desde el 15-11-2026 (cambio `restaurar-copia`, aprobado por Rainer ese día; archivo en `openspec/changes/archive/2026-11-15-restaurar-copia/`). Código: `src/restaurar.py`, `api/gestor.py`, migración 011; reglas en `verticals/movilidad.json → restauracion`.

## Requisitos

### Quién
- Restauran el editor y el editor jefe, desde la pestaña «Restaurar» del gestor, en el móvil y sin el Mac. Las piezas firmadas por el director solo las restaura el editor jefe.

### Nunca encima
- Toda restauración enseña antes qué cambia, deja registro (commit nuevo o línea en `gestor_registro`), avisa al director y se puede deshacer. Nunca borra nada ni reescribe la historia.

#### Escenario: pieza devuelta a una versión anterior
- DADA una pieza publicada cuyo titular se cambió por error
- CUANDO un editor elige la versión de ayer y pulsa «Restaurar esta versión»
- ENTONCES se escribe un commit nuevo con esa versión, la pieza lleva `revised_at` y una línea en `revisiones`, se republica en Ghost con su estado y el director recibe el aviso con «Deshacer»

### Contenido
- Se restauran documentos de `data/` (piezas, anuncios, productos, ediciones, plazos, boletines) a cualquier versión de su historial que ya estuviera publicada; antes de publicarse pasa las validaciones de tipo de contenido y de tres ejes.

### Base privada
- Supabase guarda cada noche una copia interna de las tablas de `public` en el esquema privado `copia`, 14 días, fuera de la API.
- El editor recupera filas que faltan o campos cambiados del CRM y de la base de prensa; el editor jefe, también del equipo y del seguimiento.
- Una recuperación nunca quita un «No contactar» ni un estado de solo añadir.

#### Escenario: «No contactar»
- DADA una cuenta marcada «No contactar» después de la copia del día elegido
- CUANDO un editor recupera sus campos de ese día
- ENTONCES el «No contactar» se mantiene y el gestor lo explica

### Fuera de alcance
- Ghost (miembros, ajustes, tema), las contraseñas del equipo y el proyecto entero: solo el editor jefe, con la copia del Mac (`docs/copia-de-seguridad.md`).
