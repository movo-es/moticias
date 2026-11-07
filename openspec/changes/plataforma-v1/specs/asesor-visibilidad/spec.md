# Capacidad: asesor de visibilidad y credibilidad (delta)

## ADDED Requisito: propuestas semanales
Cada lunes el asesor entrega a editores y superadministradores entre 5 y 10 propuestas concretas, cada una con categoría (visibilidad, credibilidad, conocimiento, contactos, canales, ingresos), instrucción ejecutable, prioridad, esfuerzo y evidencia (métrica, hueco detectado, oportunidad de fuente, menciones, licitación o consulta abierta).

#### Escenario: hueco en una base de conocimiento
- CUANDO en la semana se han publicado tres piezas sobre un tema sin página pilar
- ENTONCES el asesor propone la página pilar con título, estructura, datos propios a reunir y piezas hijas a enlazar.

## ADDED Requisito: ciclo
Cada propuesta tiene estado (propuesto, aceptado, hecho, descartado); una propuesta aceptada se convierte en tarea de un agente o en cambio OpenSpec; el asesor revisa la semana siguiente qué se hizo y qué efecto tuvo.

## ADDED Requisito: criterios
Recomendaciones de Google y optimización para motores generativos (respuesta directa de 40–60 palabras, clúster pilar e hijas, Schema.org, `llms.txt`, datos propios, menciones y co-ocurrencia, búsquedas transaccionales), mecánica de confianza de `docs/benchmark-referencias.md § B`, y los segmentos y soluciones de `verticals/<id>.json`.
