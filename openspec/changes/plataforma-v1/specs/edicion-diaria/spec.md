# Capacidad: edición diaria (delta)

## MODIFIED Requisito: el barrido tiene en cuenta las campañas temáticas activas
Antes de seleccionar, la rutina lee `verticals/<vertical>.json` → `campaigns.active` y cada `data/campanas/<id>.json` con `status: activa`: añade sus `keywords` al barrido, aplica `cadence.weight` en la selección, asegura `cadence.min_pieces_per_week` piezas sobre el tema a lo largo de la semana cuando hay hechos que lo merezcan, y marca esas piezas con `campaign: <id>`. Si `hook.date_verified` es `false`, ninguna pieza cita la fecha gancho. Sin actualidad sobre el tema no se fuerza una pieza.

#### Escenario: campaña PMST activa y BOE con una convocatoria de ayudas
- CUANDO el BOE publica una convocatoria de ayudas para planes de movilidad al trabajo durante la campaña `movilidad-al-trabajo-pmst`
- ENTONCES la referencia entra con peso alto, se escribe como pieza propia de `regulacion` con `campaign: "movilidad-al-trabajo-pmst"`, firma y clasificación según las reglas normales, y sin mención a MOVO en el texto.

## ADDED Requisito: la nota metodológica declara las campañas
La edición indica en su nota metodológica qué campañas estaban activas y cuántas piezas del día llevan `campaign`.
