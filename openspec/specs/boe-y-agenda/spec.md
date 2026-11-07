# Capacidad: barrido del BOE y agenda de plazos

## Requisito: cobertura
Cada edición barre con la API de datos abiertos todos los días desde el final del `boe_range` anterior hasta hoy (el BOE del día se espera hasta las 07:50; no hay BOE en domingos ni festivos).

## Requisito: filtro y clasificación
Se conservan los ítems del departamento de Transportes y Movilidad Sostenible y los de otros departamentos o de la sección V con palabras clave de transporte de viajeros. Cada referencia lleva `modos` (`tierra`, `mar`, `aire`, `transversal`) y `tipo`; «línea aérea de contacto» es `tierra`; «Bus Nàutic» es `mar`.

## Requisito: curación
De 5 a 15 referencias con `titulo_corto` (sin «Anuncio de licitación de:» ni expedientes), `nota` (qué significa, con importe y plazo) y `edicion` (hoy). Cada plazo de ofertas, consulta pública o entrada en vigor genera un documento en `agenda` con `edicion` (hoy). `boe_series` guarda por día `total`, `lic` y `disp` (últimos 14 días).

#### Escenario: referencia con peso propio
- CUANDO una referencia es una norma, una concesión relevante o una licitación por encima de 10 M€
- ENTONCES además se escribe como noticia con sección `regulacion` o `licitaciones` y `doc_ref`, `authority`, `amount`, `deadline`.
