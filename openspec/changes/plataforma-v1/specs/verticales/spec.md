# Capacidad: verticales (delta)

## ADDED Requisito: configuración por vertical
Todo lo específico de un medio (nombre, dominio, secciones, subsectores, rotación, fuentes, segmentos, soluciones, niveles, sensores, artefactos, calendario) vive en `verticals/<id>.json`. El código, los agentes, las specs y la sala de redacción leen esa configuración y no contienen nada específico de un vertical.

#### Escenario: alta del vertical de turismo
- CUANDO se rellena `verticals/turismo.json` y se crea su carpeta de datos
- ENTONCES los mismos comandos y la misma sala de redacción producen y gestionan su edición sin cambios de código.

## ADDED Requisito: datos por vertical
Toda tabla de negocio lleva `vertical_id`; el contenido de cada vertical vive en su propia carpeta de datos del repositorio.
