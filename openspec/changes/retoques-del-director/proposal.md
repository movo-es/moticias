# Cambio: retoques-del-director

Fecha: 9 de noviembre de 2026. Origen: Rainer pide poder entrar a una noticia desde su gestor «y pedir que la IA le dé un determinado toque, titular o referencia a algo que me parece importante», con el ejemplo «Iberia incluye Granada en su operación especial a Andalucía tras el accidente del AVE». Decisiones suyas: el resultado se publica directo y se le avisa (no espera aprobación); vale con que tarde menos de una hora y sin claves nuevas.

## Qué cambia

1. **Cola de retoques** en `data/retoques/` (un JSON por encargo; formato y reglas en su `README.md`). Sin datos personales: `pedido_por` es el perfil del gestor.
2. **Gestor** (`app.moticias.com/gestor/` → pieza): caja «Pedir un toque a la redacción» con el texto libre de la instrucción; lista de retoques de la pieza con su estado (pendiente, aplicado, sin fuente, cancelado), resumen, cambios y fuentes; botón «Cancelar» mientras está pendiente. Acciones de la API: `GET ?a=retoques[&pieza=]`, `POST ?a=retoque` (`crear`, `cancelar`); permiso `piezas` (superadministrador, editor, oficina). El gestor guarda el encargo por commit en GitHub, como las menciones.
3. **Rutina `/retoques`** (`.claude/commands/retoques.md`), tarea programada «MOTICIAS · retoques del director» (laborables, cada hora de 8 a 21, Opus 5.5): verifica en fuente primaria lo que se pide; si hay fuente, reescribe lo necesario (titular, subtítulo, párrafo, cifras, cronología, fuentes), deja `revised_at` y la línea «Revisión» al final, republica en moticias.com y en el portal, cierra el retoque y avisa con el enlace; si no hay fuente, cierra el retoque como `sin_fuentes` con el motivo y la pieza no cambia.
4. `src/retoques.py`: `pendientes`, `crear`, `cerrar`, `revisar` (contabilidad de la cola y nota de revisión).

## Qué no cambia

Firma y aprobación (una pieza de G. Jordan retocada sigue firmada por G. Jordan; un análisis del director en borrador sigue en borrador), las cajas «Contenido patrocinado», el estándar de profundidad y la regla de oro: sin fuente primaria no se escribe, tampoco por encargo del director.
