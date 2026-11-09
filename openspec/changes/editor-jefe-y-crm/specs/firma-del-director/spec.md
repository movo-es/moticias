# Firma del director

## ADDED Requisito: cupo
El nombre del director firma como mucho el `max_pct` (10 %) de las piezas publicadas o pendientes de los últimos `ventana_dias` (30) días; la rutina apunta al `objetivo_pct` (7 %). `python3 -I src/firma.py informe` lo mide y sale con error si se pasa.

#### Escenario: análisis corriente
- CUANDO la rutina escribe el análisis del día y el tema no cumple ningún `motivo_importante`
- ENTONCES lo firma «G. Jordan, Redactor responsable», con la nota de intereses sin nombre.

#### Escenario: análisis importante con cupo
- CUANDO el análisis es de relevancia ALTA, tiene `motivo_importante` y queda cupo hasta el objetivo
- ENTONCES lo firma «Rainer Uphoff, Director de MOTICIAS» y queda `pendiente` hasta su aprobación.

#### Escenario: el director quiere firmar sin cupo
- CUANDO el editor jefe pide en el gestor su firma y ya está en el tope del 10 %
- ENTONCES el gestor se niega y lo dice; la firma sigue siendo de la redacción.

## ADDED Requisito: firmar no es aprobar
Una pieza crítica (`risk: critica`) espera la aprobación del director aunque la firme la redacción.
