# Capacidad: comprobador de los enlaces promocionados

## Requisito: una vez al día, todos los días
Cada enlace activo de publicidad, patrocinio y contenido patrocinado se visita una vez al día, a hora al azar entre las 9 y las 21 de Madrid, con `utm_medium=comprobacion`, y el resultado queda en `pub_comprobaciones`.

## Requisito: nunca es un lector
Las visitas del comprobador no cuentan como vistas ni clics, no se presentan como SEO y no se venden al anunciante como tráfico.

## Requisito: auditable
El panel enseña la comprobación del día con su hora y su resultado; el historial de 30 días se descarga en CSV.

#### Escenario: enlace caído
- CUANDO un enlace falla dos comprobaciones seguidas
- ENTONCES el editor jefe recibe un correo, una sola vez por racha.
