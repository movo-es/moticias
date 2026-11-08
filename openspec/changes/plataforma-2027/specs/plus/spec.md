# Capacidad: PLUS, comunicación de crisis (Amarantia) (delta)

## ADDED Requisito: plan como secuencia ejecutable
`planes` (cliente, escenario, propietario, versión, aprobado_en), `audiencias` (internas, stakeholders, clientes, medios, público que optó; cada una con contactos y canales), `secuencias` (pasos del motor de envíos con condición de avance), `ejecuciones` (plan, tipo: real | simulacro, lanzada_por, estado), `aprobaciones` (ejecución, paso, quién, cuándo).

## ADDED Requisito: aprobación humana por paso
Ningún paso dirigido a stakeholders, medios o público se envía sin aprobación de una de las personas designadas por el cliente. Los pasos internos pueden ser automáticos si el plan lo dice.

#### Escenario: lanzamiento desde una alerta confirmada
- CUANDO una persona pulsa «Abrir PLUS» en una alerta confirmada y elige un plan
- ENTONCES se crea una ejecución real, el primer paso interno se envía y la ejecución se detiene antes del primer paso externo a la espera de aprobación.

## ADDED Requisito: flash público como comunicado
El flash público es una nota en la sala de prensa, más redes y lista de medios, firmada «Comunicado de <empresa>». Nunca se presenta como alerta oficial: las alertas a la población son competencia de Protección Civil (ES-Alert).

## ADDED Requisito: simulacros
Toda ejecución puede ser `simulacro` contra una audiencia de prueba; genera un informe de tiempos, entregas y acuses. El primer uso real de un plan exige un simulacro previo.

## ADDED Requisito: legal
Contrato de encargado del tratamiento (art. 28 RGPD) firmado al dar de alta el plan; base jurídica documentada por audiencia; WhatsApp con opt-in y plantillas aprobadas; registro de auditoría de toda ejecución.
