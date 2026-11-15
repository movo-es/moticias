# Capacidad: cola del editor (cambio `cola-del-editor`, 16-11-2026)

### Requisito: cola de temas para el editor jefe
El gestor tiene una pestaña «Cola» con los temas nuevos (de las rutinas y de las personas), filtrables y ordenables por medio, modo, tema, región, importancia, fiabilidad, estado, caducidad, solución del grupo y quién lo propuso, con avisos del mismo hecho agrupados y selección individual o en bloque.

#### Escenario: confirmar un tema
- DADO un tema con fiabilidad primaria en la cola
- CUANDO el editor jefe pulsa «Confirmar»
- ENTONCES se crea un encargo para la redacción horaria enlazado al tema, el tema pasa a «Confirmados» y su estado sigue al del encargo (en redacción, para aprobar, publicado o sin fuente)

#### Escenario: tema sin confirmar
- DADO un tema con fiabilidad «sin confirmar»
- CUANDO alguien intenta confirmarlo
- ENTONCES el servidor lo rechaza (409) y la tarjeta explica que hace falta una fuente mejor

#### Escenario: permisos
- DADO un editor
- CUANDO intenta confirmar o mandar a la papelera un tema que no propuso
- ENTONCES el servidor responde 403

#### Escenario: nada se borra
- DADO un tema en la papelera
- CUANDO el editor jefe pulsa «Recuperar»
- ENTONCES vuelve a la cola en el estado que tenía

### Requisito: caducidad y aprendizaje
Un tema caduca al pasar su fecha límite o a los 3 días laborables de su fecha del hecho y pasa al archivo (nunca a la papelera); lo editorial y lo de referencia no caducan. Cada corrección de importancia del editor jefe se guarda con su motivo y el agente la lee antes de proponer.
