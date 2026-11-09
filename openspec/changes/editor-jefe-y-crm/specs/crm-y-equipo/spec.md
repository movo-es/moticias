# CRM y equipo

## ADDED Requisito: base privada
Supabase «moticias» (Frankfurt), migración 003. Solo entra el gestor, con la cabecera `x-moticias-clave` (la base guarda su huella). Ninguna tabla admite borrado; los estados, las actividades y el registro son de solo añadir.

## ADDED Requisito: módulo de MOVO
Mismo modelo que el CRM de MOVO (433–437): cuentas con `producto` y `tipo`, personas, estado como libro, actividades, siguiente paso con fecha, «No contactar» para siempre. Tipos y estados en `verticals/movilidad.json → crm`.

#### Escenario: regla de oro
- CUANDO una cuenta pasa a un estado activo (`crm.activos`) sin ningún paso abierto
- ENTONCES el gestor exige un siguiente paso con fecha.

## ADDED Requisito: suscriptores
Son los miembros de Ghost y no se copian. La categoría es una etiqueta `cat:<categoría>` en Ghost (lista en `crm.suscriptores.categorias`); una persona del CRM puede llevar su `ghost_member_id`.

## ADDED Requisito: equipo
Las personas del gestor viven en la tabla `equipo` (antes, en el repositorio privado `movo-es/moticias-equipo`, que queda de respaldo si la base no está configurada).
