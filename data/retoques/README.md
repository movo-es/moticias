# Retoques del director (`data/retoques/`)

Cola de instrucciones editoriales sobre piezas ya publicadas, pedidas desde el gestor (`app.moticias.com/gestor/` → pieza → «Pedir un toque a la redacción») o con `src/retoques.py crear`. Ejemplo: «Iberia incluye Granada en su operación especial a Andalucía tras el accidente del AVE». Las atiende `/retoques` (tarea programada «MOTICIAS · retoques del director», laborables cada hora de 8 a 21). Especificación: `openspec/changes/retoques-del-director/`.

Reglas: lo que se pide se verifica en fuente primaria antes de escribirlo; si no hay fuente, el retoque queda `sin_fuentes` con el motivo y la pieza no cambia. El retoque aplicado deja `revised_at` y una línea «Revisión» al final del cuerpo, se republica en moticias.com y se avisa al director con el enlace. Decisión de Rainer (9-11-2026): se publica directo y se le avisa; no espera aprobación. Nunca se borra un retoque: cancelar es `estado: cancelado`.

**El repositorio es público: aquí no entra ningún dato personal.** `pedido_por` es el perfil del gestor (superadmin, editor…), nunca un nombre ni un correo.

## Formato (`<AAAA-MM-DD>-<pieza>-<4 hex>.json`)

```json
{
 "id": "2026-11-09-aire-puente-aereo-madrid-andalucia-urda-3f2a",
 "pieza": "aire-puente-aereo-madrid-andalucia-urda",
 "instruccion": "Iberia incluye Granada en su operación especial a Andalucía tras el accidente del AVE: titular y párrafo con la fuente.",
 "pedido_por": "superadmin",
 "pedido_en": "2026-11-09T13:40+01:00",
 "estado": "pendiente" | "aplicado" | "sin_fuentes" | "cancelado",
 "resultado": null | {"en": "…", "resumen": "qué se cambió o por qué no", "fuentes": ["https://…"], "cambios": ["titular", "subtítulo", "párrafo «Los hechos»"]}
}
```
