# Capacidad: pieza · delta del cambio `entradilla-y-linkedin`

## ADDED Requisitos

### Requisito: entradilla (cambio `entradilla-y-linkedin`, 17-11-2026)
Toda pieza lleva `entradilla`: el texto que se lee en las tarjetas, en los listados, en el resumen de Ghost y al compartir. Una o dos frases completas en un solo párrafo, como mucho 280 caracteres contando espacios (`verticals/<id>.json → editorial.entradilla.max`), acabada en punto, sin puntos suspensivos y solo con hechos que están en la pieza. No sustituye al `summary`. Lo comprueba `src/entradilla.py validar`.

#### Escenario: pieza nueva
- CUANDO la redacción escribe una pieza
- ENTONCES le pone una `entradilla` que cabe y `python3 -I src/entradilla.py validar` no da errores antes de guardar

#### Escenario: entradilla que no cabe
- DADA una entradilla de más de 280 caracteres, o que no acaba en frase completa
- CUANDO se valida o se guarda desde el editor del gestor
- ENTONCES se rechaza diciendo por qué y no se recorta sola

#### Escenario: pieza sin entradilla válida
- DADA una pieza antigua o defectuosa sin `entradilla`
- CUANDO se publica o se enseña en una tarjeta
- ENTONCES se usan las frases completas de su `summary` que quepan y nunca se corta a media palabra

## MODIFIED Requisitos

### Requisito: estructura y bloques
Título en tres niveles (`kicker`, `title` ≤ 110 caracteres, `subtitle`), la `entradilla` (≤ 280 caracteres, frases completas) y los cinco bloques (`summary` 60–110 palabras, `actors`, `relevance_for`, `why`, `next`) más `key_fact`. El cuerpo abre con el hecho (fecha, lugar, cifra, quién decide) y sigue con 5–8 secciones `##` de una a tres palabras; cierra con «Lo que hay que vigilar», sin moraleja.
