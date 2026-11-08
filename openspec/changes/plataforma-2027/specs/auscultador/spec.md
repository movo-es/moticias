# Capacidad: auscultador (Amarantia) (delta)

## ADDED Requisito: fuentes en tres anillos
Anillo 1: lo que ya barren los sensores (prensa, RSS, boletines, licitaciones, comunicados). Anillo 2: redes y agregadores con acceso gratuito o barato (Bluesky, Reddit, YouTube, Telegram público, Mastodon, Google News y Alerts). Anillo 3: de pago (X, herramientas de escucha) solo si el cliente lo asume; LinkedIn se cubre por buscadores.

## ADDED Requisito: señal enriquecida
Cada señal de una entidad vigilada lleva sentimiento (−1 a 1), confirmación (`confirmado` con fuente primaria; `sin-confirmar` con medios o redes; `rumor` solo redes o anónimos), alcance cuando la fuente lo da, y `entity_id`.

## ADDED Requisito: línea base y detectores
Por entidad, línea base móvil de 30 días (volumen diario, sentimiento medio). Detector de pico: volumen o sentimiento negativo fuera de tres desviaciones en 6 horas. Detector de tendencia: pendiente del sentimiento a 14 días que cruza el umbral del cliente. Umbrales por entidad.

#### Escenario: pico de menciones negativas sin confirmar
- CUANDO en 6 horas una entidad vigilada recibe menciones negativas fuera de su línea base y ninguna tiene fuente primaria
- ENTONCES se abre una alerta de nivel «atención» marcada `sin-confirmar`, con las evidencias enlazadas, y se avisa a los contactos del plan; no se escala a «crisis» sin confirmación humana.

## ADDED Requisito: alertas con humano en el bucle
`alerts` (entity_id, nivel: vigilar | atención | crisis, estado: nueva | vista | confirmada | descartada | en-accion, evidencias, abierta_en, cerrada_en, por). Confirmar, descartar y «abrir PLUS» son acciones de una persona en el panel `app.moticias.com/amarantia`.

## ADDED Requisito: aviso a la redacción
Las alertas de nivel atención o crisis sobre entidades del sector (vigiladas o no) van a `work/sensores/candidatas.md` y al aviso del director como «posible noticia grande».

## ADDED Requisito: datos de cliente y reservado
Cada cliente ve solo sus entidades (RLS). La información reservada no entra en este módulo.
