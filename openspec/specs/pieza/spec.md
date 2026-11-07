# Capacidad: pieza (noticia, análisis, reportaje)

## Requisito: profundidad
Toda pieza publicada tiene `body_md` de fondo (noticia 1.000–1.500 palabras; análisis 900–1.300; reportaje 1.800–2.500), `key_data` (4–8), `timeline` (4–10) y `sources` (6–12, al menos 2 oficiales con `published` y `accessed`).

#### Escenario: pieza incompleta
- CUANDO una pieza carece de `body_md`, `key_data` o `timeline`
- ENTONCES no se publica.

## Requisito: estructura y bloques
Título en tres niveles (`kicker`, `title` ≤ 110 caracteres, `subtitle`) y los cinco bloques (`summary` 60–110 palabras, `actors`, `relevance_for`, `why`, `next`) más `key_fact`. El cuerpo abre con el hecho (fecha, lugar, cifra, quién decide) y sigue con 5–8 secciones `##` de una a tres palabras; cierra con «Lo que hay que vigilar», sin moraleja.

## Requisito: voz
Frases cortas, vocabulario institucional exacto, juicio firme y no partidista, incisos con raya; sin las frases prohibidas de `docs/estandar-profundidad.md`, sin exclamaciones, preguntas retóricas, emoticonos ni mención a la inteligencia artificial. Citas textuales solo de documentos primarios, menos de 20 palabras, con atribución; de prensa no se citan más de 15 palabras seguidas.

## Requisito: fechas y frescura
`event_date` comprobado en el documento; `published_at`/`published_time` con la hora real de redacción; hechos de las últimas 72 horas (más de 7 días solo como seguimiento con novedad documentada, dicho en el primer párrafo). Una corrección añade `revised_at` y «Corrección: …» al final.

## Requisito: enlaces
En `body_md` solo URL `https://…`; las piezas anteriores se citan por título y fecha, sin enlace interno.

## Requisito: análisis
`kind: analisis`, firmado «Rainer», `author_role: Director de MOTICIAS`, `author_note` con la declaración de intereses, `scope` del ámbito de rotación; añade `{date, scope}` a `settings/site.recent_scopes` (últimos 30).
