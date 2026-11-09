# Retoques del director

## Requisitos

### Encargo
- Un retoque pertenece a una pieza existente de `data/articles/` y lleva una instrucción de 8 a 1.200 caracteres.
- Se crea desde el gestor (perfil con permiso `piezas`) o con `src/retoques.py crear`; queda `pendiente` en `data/retoques/<fecha>-<pieza>-<hex>.json` por commit.
- Un retoque pendiente puede cancelarse (`cancelado`); nunca se borra.

### Atención
- La rutina `/retoques` corre cada hora en horario laboral y atiende los pendientes por orden de petición, hasta cuatro por pasada.
- Todo hecho, cifra, fecha o nombre que entre nuevo se verifica en fuente primaria abierta en la sesión; sin fuente, el retoque se cierra `sin_fuentes` con el motivo y la pieza no cambia.
- Un retoque aplicado deja en la pieza `revised_at` y una línea «Revisión (fecha, hora): a petición del director: …» al final de `body_md`, añade las fuentes nuevas con fecha de publicación y consulta, y no altera `author`, `status` ni `menciones`.
- La pieza retocada se republica en Ghost (mismo estado que tuviera) y en el portal; se comprueba en la web.
- Se avisa al director con el titular nuevo, el enlace y la fuente, o con el motivo si no hubo fuente.

### Gestor
- La pieza muestra la caja de petición y el historial de sus retoques con estado, resumen, cambios y fuentes.
