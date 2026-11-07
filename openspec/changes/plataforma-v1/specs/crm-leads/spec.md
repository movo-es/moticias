# Capacidad: CRM y leads (delta)

## ADDED Requisito: contactos con perfil y comportamiento
Cada suscriptor es un contacto con organización, cargo, tipo de entidad, intereses declarados y eventos de comportamiento (aperturas, clics por tema, descargas, alertas, visitas, respuestas, peticiones).

## ADDED Requisito: puntuación por solución del grupo
Cada noche se calcula para cada contacto una puntuación por segmento y por solución (MUFMI, MOVENBUS, MOVO, PLANES) a partir de su tipo de entidad, intereses y eventos, según las señales definidas en `verticals/<id>.json`. Un contacto supera el umbral → lead nuevo con el motivo (qué leyó, qué pidió) y aviso al comercial.

#### Escenario: operador que pide alertas
- CUANDO un contacto de tipo `operador` activa alertas de licitaciones de autobús en su comunidad y abre tres piezas de licitaciones en dos semanas
- ENTONCES se crea un lead para MOVENBUS con esos hechos como motivo.

## ADDED Requisito: seguimiento
Estados del lead: nuevo, contactado, reunión, propuesta, ganado, perdido; propietario; historial. Exportación CSV. Métricas: leads por solución, conversión, origen de cada proyecto del grupo.

## ADDED Requisito: anunciantes
Anunciantes y patrocinadores son contactos con organización y campañas; ven solo sus campañas y métricas.
