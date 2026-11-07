# Capacidad: edición diaria

## Requisito: calendario
La rutina produce una edición cada día laborable español a las 06:38 (Europe/Madrid) y cierra antes de las 08:30.

#### Escenario: fin de semana o festivo
- CUANDO la rutina arranca en sábado, domingo o festivo nacional
- ENTONCES termina con «MOTICIAS: hoy no hay edición» sin escribir nada, salvo noticia flash de gran importancia (entonces publica solo esa pieza y lo explica en la nota metodológica).

#### Escenario: edición ya cerrada
- CUANDO existe `editions/{hoy}`
- ENTONCES termina con «MOTICIAS: la edición de hoy ya estaba cerrada» sin escribir nada.

## Requisito: contenido mínimo
Cada edición tiene de 5 a 8 noticias nuevas con fuente primaria, un análisis firmado por Rainer en el ámbito que toca por rotación, de 5 a 15 referencias del BOE con nota, los plazos derivados en agenda, el documento del día, el ticker y la nota metodológica.

#### Escenario: tope de tokens
- CUANDO la sesión supera 450.000 tokens
- ENTONCES cierra con lo que tenga, lo dice en la nota metodológica y en el aviso.

## Requisito: no repetir
Ningún hecho publicado en los siete días anteriores vuelve como noticia; una novedad documentada de las últimas 72 horas sobre un hecho ya cubierto es una pieza nueva que cita la anterior por título y fecha.

## Requisito: verificación y registro
Antes del aviso: la edición, la apertura y el análisis existen; todas las piezas del día tienen estado, fuentes con URL y fecha, kicker, título, subtítulo y los cinco bloques; los enlaces oficiales responden; `featured: 1` solo en una pieza; ningún cuerpo contiene `](#`. Después: línea en `docs/ediciones.md`, hemeroteca y `data/` al día, `git push`, aviso corto.
