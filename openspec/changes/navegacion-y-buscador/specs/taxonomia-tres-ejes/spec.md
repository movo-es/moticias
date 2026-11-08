# Capacidad: taxonomía de tres ejes (modo · tema · territorio)

Añade a la capacidad `pieza`. Fuente: `verticals/<vertical>.json → taxonomia`; código: `src/taxonomia.py`.

## Requisito: tres ejes en toda pieza
Toda pieza publicada lleva `modo` y `submodo` (uno, de la lista del vertical), `temas` (lista de uno o dos ids; el primero es el principal) y `territorios` (lista de uno o varios ids: comunidades autónomas, Ceuta, Melilla y los ámbitos `estado`, `ue`, `internacional`). `section` y `subsector` se conservan.

#### Escenario: pieza nueva en la edición diaria
- CUANDO la rutina crea una pieza
- ENTONCES propone los tres ejes con `python3 -I src/taxonomia.py pieza <ruta>`, el redactor los confirma o corrige y la pieza no se publica sin ellos.

#### Escenario: corrección a mano
- CUANDO una pieza lleva `taxonomia_manual: true`
- ENTONCES `taxonomia.py aplicar --forzar` no la toca.

## Requisito: inferencia
La clasificación automática usa, por este orden: `subsector` y `section` para el modo (la sección `logistica` fuerza un submodo `logistica-*`; `aéreo` y `marítimo` se afinan por alias de cabecera); la sección para el tema principal y los alias de cabecera y etiquetas para el segundo; etiquetas, cabecera, `geo.place` y resumen para los territorios, con sedes estatales en Madrid (ministerio, Consejo de Ministros, Adif, DGT) contadas como `estado` y no como Comunidad de Madrid. Una pieza con comunidades citadas no lleva más de tres, más un ámbito.

## Requisito: alias y vecinos
Cada territorio tiene alias (gentilicios, provincias, capitales, puertos, aeropuertos, operadores, boletín oficial) y una lista de comunidades vecinas; cada submodo y cada tema tienen alias. Los alias se comparan sin tildes, en minúsculas y por palabra o expresión completa.

#### Escenario: alias ambiguo
- CUANDO un alias coincide con una palabra común («tarifa», «puente»)
- ENTONCES no se añade al diccionario; se prefiere perder un acierto a clasificar mal.
