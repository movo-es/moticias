# Capacidad: fuentes de segundo nivel (delta)

## ADDED Requisito: alta de fuente con licencia y método
Toda fuente nueva se da de alta en `portal/data/sources.json` con tipo, método (`api` | `rss` | `pagina`), licencia de reutilización, `robots` comprobado y cadencia. Lo que una fuente prohíbe reutilizar no se copia: se cita y se enlaza.

## ADDED Requisito: fuentes iniciales
En este orden: BDNS (convocatorias y concesiones de transporte y movilidad); Portal de Transparencia de la AGE y portales autonómicos (contratos menores, convenios); CNMC (expedientes de ferroviario, aeroportuario y competencia; registro de grupos de interés); Congreso y Senado (preguntas, PNL, comparecencias de la Comisión de Transportes); Tribunal de Cuentas y OCEX; actas y órdenes del día de consorcios y ATM; CNMV (hechos relevantes de cotizadas del sector); BORME (nombramientos, concursos); convocatorias de huelga; declaraciones de impacto ambiental.

## ADDED Requisito: señales y datos
Cada hallazgo escribe una señal en `senales` y, cuando es un registro estructurado (subvención, contrato, nombramiento, pregunta parlamentaria), una fila en `datasets` (id, vertical_id, dataset, source_id, ref, date, fields jsonb, url). Con `datasets` se publican series propias descargables (CSV con método y fecha) y se alimenta el radar regulatorio.

#### Escenario: convocatoria de ayudas al transporte
- CUANDO la BDNS publica una convocatoria cuyo objeto toca transporte, movilidad o PMST
- ENTONCES el barrido de mediodía la escribe en `senales` (`kind: norma`) y en `datasets` (`dataset: subvenciones`) con plazo e importe, y el plazo entra en `agenda` con `edicion` del día.

## ADDED Requisito: barrido
Corre con `/sensores` a las 13:30 en laborables; cada fuente tiene tope de tiempo y, si falla, se anota en `docs/fuentes.md` sin detener el resto.
