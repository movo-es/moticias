# Capacidad: campañas temáticas (delta)

Una campaña temática es un periodo acotado en el que MOTICIAS trabaja a fondo un tema con una fecha o un hecho detrás (un plazo legal, una licitación grande, un congreso, una transposición), para ganar autoridad sobre ese tema y, en el mismo movimiento, poner una solución —del grupo o de un anunciante— delante de quien tiene ese problema. Ejemplo fundador: «Movilidad al trabajo: la cuenta atrás de los PMST», que acompaña el plazo de la Ley 9/2025 para presentar planes de movilidad sostenible al trabajo y ofrece MOVO a los rezagados.

La campaña es un objeto distinto de la campaña publicitaria (`campaigns`, producto de un anunciante): la temática es editorial y comercial a la vez; la publicitaria es solo comercial y, cuando existe, cuelga de una temática o va suelta.

## ADDED Requisito: una campaña es un documento del repositorio

Cada campaña vive en `data/campanas/<id>.json` (fuente de verdad) y su estado y métricas en Supabase (`campanas_tematicas`). Campos obligatorios: `id`, `vertical_id`, `name`, `claim` (una frase para lectores), `topic` (tema), `keywords` (para barridos y sensores), `hook` (`{kind: plazo|licitacion|evento|norma|temporada, text, date, source_url, date_verified}`), `start`, `end`, `status` (`prevista` | `activa` | `cerrada`), `goal` (frase: a quién y para qué), `segment_id`, `solution` (`MUFMI` | `MOVENBUS` | `MOVO` | `PLANES` | id de anunciante | `ninguna`), `monetization` (`sin-publicidad` | `patrocinada` | `banner` | `mixta`), `sponsor` (`grupo` | id de anunciante | `null`), `editorial_plan` (piezas previstas: pilar, reportajes, datos propios, radar, entrevistas, cada una con `kind`, `title`, `week`, `status`), `cadence` (`min_pieces_per_week`, `weight` 1–3 para el barrido), `channels` (`web`, `boletin`, `linkedin`, `instagram`, `edicion-a-medida`), `creatives` (banners y bloques patrocinados por hueco, con etiqueta visible), `cta` (`{label, url, utm_campaign}`), `kpis` (objetivos numéricos: piezas, lecturas, descargas, altas, leads por solución, conversiones), `owner` (editor responsable), `review` (notas de cierre).

#### Escenario: alta de la campaña piloto
- CUANDO el director crea `data/campanas/movilidad-al-trabajo-pmst.json` con `status: activa`, `solution: MOVO`, `monetization: sin-publicidad` y `sponsor: grupo`
- ENTONCES desde la siguiente edición el barrido da peso al tema, la portada muestra el bloque de campaña con sus piezas, el hueco lateral de esas piezas muestra la ficha de MOVO etiquetada «Servicio de MOVO», y el asesor semanal informa del avance frente a los `kpis`.

## ADDED Requisito: la campaña orienta la selección, no el tratamiento

Con una campaña `activa`, la rutina diaria busca además con sus `keywords`, garantiza `min_pieces_per_week` piezas sobre el tema (si hay hechos que lo merezcan; nunca se inventa actualidad), marca esas piezas con `campaign: <id>` y, en la semana del `hook.date`, prepara la pieza de cierre («qué pasa mañana»). Lo que no cambia: el estándar de profundidad, las fuentes, la firma, la clasificación rutinaria/crítica, la prohibición de citar la solución en el texto. Una pieza de campaña es una pieza normal con una etiqueta.

#### Escenario: semana sin hechos
- CUANDO en una semana no hay actualidad sobre el tema de la campaña
- ENTONCES la rutina no fuerza piezas: publica, si procede, una pieza de fondo del `editorial_plan` (pilar, explicador, datos propios) y lo anota en la nota metodológica.

## ADDED Requisito: monetización señalizada y separada

- `sin-publicidad`: autopromoción del grupo en los huecos (`data/ads/`), etiqueta «Servicio de MOVO» o equivalente.
- `patrocinada`: un anunciante paga por asociarse a la campaña: logotipo en el bloque de campaña y en el boletín, etiqueta «Campaña patrocinada por …», contenido patrocinado solo con la etiqueta «Contenido patrocinado», fuera de la apertura y fuera de la selección automática de portada.
- `banner`: banners del anunciante en los huecos de web y boletín durante la campaña, con UTM propio.
- `mixta`: patrocinio y banner.

Las piezas de campaña no cambian por tener patrocinador; si la campaña se patrocina después de publicar piezas, se conservan tal cual. El patrocinador nunca ve una pieza antes de publicarse. Toda campaña patrocinada se registra en `campaigns` (publicitaria) con `campana_id` apuntando a la temática.

#### Escenario: cambio de patrocinador
- CUANDO una campaña pasa de `sin-publicidad` a `patrocinada`
- ENTONCES cambian el bloque de campaña, los huecos y el boletín; no cambia ningún `body_md`, y la declaración de intereses lista la campaña y su patrocinador.

## ADDED Requisito: la campaña es un canal de leads

Quien lee, descarga o pulsa el `cta` de una campaña genera eventos con `campana_id`; la puntuación nocturna crea o sube `leads` con esa `campana_id` y la `solution` de la campaña. El panel `/campanas/<id>` muestra piezas publicadas frente a plan, lecturas, descargas, altas, leads y conversiones, y el comercial ve la lista de organizaciones que han interactuado.

#### Escenario: rezagado que descarga la plantilla
- CUANDO un contacto de una empresa descarga la guía de PMST de la campaña
- ENTONCES se crea un evento `download` con `campana_id`, el contacto sube de puntuación en `MOVO` y aparece en la lista de la campaña para el comercial.

## ADDED Requisito: los agentes conocen las campañas

- `/edicion-diaria`: lee las campañas `activas`, aplica `keywords` y `cadence`, etiqueta `campaign`.
- `/sensores`: etiqueta las señales con `campana_id` cuando casan con `keywords`.
- `/consejo-visibilidad`: dedica un apartado a cada campaña activa (avance, piezas que faltan, dato propio que publicar, a quién dirigirse, qué patrocinio ofrecer).
- `/promo-social`: prioriza las piezas de campaña y propone el post de campaña de la semana.
- `/campana-tematica`: crea, planifica, revisa y cierra campañas (alta del JSON, plan editorial, creatividades, informe de cierre).

## ADDED Requisito: ciclo de vida

`prevista` (planificada, no visible) → `activa` (en `start`, o cuando el director la active) → `cerrada` (en `end` o tras el `hook`): el bloque desaparece de portada, las piezas quedan agrupadas en una página pilar permanente («Todo sobre los PMST»), el informe de cierre va a `docs/campanas/<id>-cierre.md` con resultados frente a `kpis` y lo aprendido. Nunca se borra una campaña.
