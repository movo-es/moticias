# Capacidad: pieza (noticia, análisis, reportaje)

## Requisito: profundidad
Toda pieza publicada tiene `body_md` de fondo (noticia 1.000–1.500 palabras; análisis 900–1.300; reportaje 1.800–2.500), `key_data` (4–8), `timeline` (4–10) y `sources` (6–12, al menos 2 oficiales con `published` y `accessed`).

#### Escenario: pieza incompleta
- CUANDO una pieza carece de `body_md`, `key_data` o `timeline`
- ENTONCES no se publica.

## Requisito: estructura y bloques
Título en tres niveles (`kicker`, `title` ≤ 110 caracteres, `subtitle`), la `entradilla` (≤ 280 caracteres, frases completas) y los cinco bloques (`summary` 60–110 palabras, `actors`, `relevance_for`, `why`, `next`) más `key_fact`. El cuerpo abre con el hecho (fecha, lugar, cifra, quién decide) y sigue con 5–8 secciones `##` de una a tres palabras; cierra con «Lo que hay que vigilar», sin moraleja.

## Requisito: entradilla (cambio `entradilla-y-linkedin`, 17-11-2026)
Toda pieza lleva `entradilla`: el texto que se lee en las tarjetas, en los listados, en el resumen de Ghost y al compartir. Una o dos frases completas en un solo párrafo, como mucho 280 caracteres contando espacios (`verticals/<id>.json → editorial.entradilla.max`), acabada en punto, sin puntos suspensivos y solo con hechos que están en la pieza. No sustituye al `summary`. Lo comprueba `src/entradilla.py validar`.

#### Escenario: pieza nueva
- CUANDO la redacción escribe una pieza
- ENTONCES le pone una `entradilla` que cabe y `python3 -I src/entradilla.py validar` no da errores antes de guardar

#### Escenario: entradilla que no cabe
- DADA una entradilla de más de 280 caracteres, o que no acaba en frase completa
- CUANDO se valida o se guarda desde el editor del gestor
- ENTONCES se rechaza diciendo por qué y no se recorta sola

#### Escenario: pieza sin entradilla válida
- DADA una pieza antigua o defectuosa sin `entradilla`
- CUANDO se publica o se enseña en una tarjeta
- ENTONCES se usan las frases completas de su `summary` que quepan y nunca se corta a media palabra

## Requisito: voz
Frases cortas, vocabulario institucional exacto, juicio firme y no partidista, incisos con raya; sin las frases prohibidas de `docs/estandar-profundidad.md`, sin exclamaciones, preguntas retóricas, emoticonos ni mención a la inteligencia artificial. Citas textuales solo de documentos primarios, menos de 20 palabras, con atribución; de prensa no se citan más de 15 palabras seguidas.

## Requisito: fechas y frescura
`event_date` comprobado en el documento; `published_at`/`published_time` con la hora real de redacción; hechos de las últimas 72 horas (más de 7 días solo como seguimiento con novedad documentada, dicho en el primer párrafo). Una corrección añade `revised_at` y «Corrección: …» al final.

## Requisito: enlaces
En `body_md` solo URL `https://…`; las piezas anteriores se citan por título y fecha, sin enlace interno.

## Requisito: análisis
`kind: analisis`, firma según `src/firma.py decidir` («Rainer Uphoff, Editor jefe de MOTICIAS» solo si es importante y queda cupo; si no, «G. Jordan, Redactor responsable»), `author_note` con la declaración de intereses (sin nombre si firma la redacción), `scope` del ámbito de rotación; añade `{date, scope}` a `settings/site.recent_scopes` (últimos 30).

## Requisito: firma y aprobación
Toda pieza lleva `author`, `author_role`, `risk` (`rutinaria` | `critica`) y `review_note`. Rutinaria (una fuente oficial, o dos profesionales de confianza coincidentes): firma «G. Jordan, Redactor responsable», publicación directa. Crítica (criterios de `verticals/<id>.json` → `editorial.critical_criteria`) o análisis del editor jefe: firma «Rainer Uphoff, Editor jefe de MOTICIAS», `status: pendiente`, aviso al editor jefe con el motivo; solo él la publica. Ante la duda, crítica.

#### Escenario: pieza que atribuye responsabilidad a una empresa con nombre
- CUANDO una pieza afirma que una empresa o persona con nombre incumplió, causó o es responsable de algo
- ENTONCES se guarda como `critica` y `pendiente`, firmada por el editor jefe, y no se muestra a los lectores hasta que él la publique.
