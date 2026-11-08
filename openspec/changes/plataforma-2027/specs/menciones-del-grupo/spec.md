# Capacidad: menciones del grupo y gestor de productos propios (delta)

Decisión de Rainer (8-11-2026, tarde): cuando MOTICIAS publica algo que una solución del grupo resuelve —MUFMI en transporte a la demanda, MOVO en PMST, Movenbus como agregador de autobús discrecional (ejemplo: la pieza de los 14 lotes de Renfe)— la pieza incluye una referencia, sin parecer publicidad; el director recibe por correo un resumen con enlace directo para editar cada mención; existe un gestor de productos propios con la descripción del contexto que da entrada a cada uno. Esta spec concilia esa decisión con el cortafuegos editorial: la referencia existe, pero está señalizada, fuera del texto y bajo control del director.

## ADDED Requisito: gestor de productos propios
Cada producto o servicio del grupo vive en `data/productos/<id>.json` con nombre, URL, titular, `status`, `one_liner`, `contexto` (prosa: cuándo sí y cuándo no), `disparadores` (subsectores, secciones, palabras clave, frases), `excluir`, `umbral`, `max_por_semana`, `textos.corto`, `textos.cta` y `utm_campaign`. Lo edita el director (o la sala de redacción cuando exista) sin tocar código. Nunca se borra un producto: se pasa a `retirado`.

#### Escenario: producto sin URL o en borrador
- CUANDO un producto tiene `status` distinto de `activo` o no tiene `url`
- ENTONCES no se propone ninguna mención suya, aunque la pieza encaje.

## ADDED Requisito: la mención va al pie, señalizada, una por pieza
La mención se pinta como bloque «Nota de la casa» después de «Para saber más» y antes de la trazabilidad, con el texto corto, el enlace con UTM y la declaración («MOTICIAS pertenece al mismo grupo empresarial que este servicio. La mención no es publicidad pagada y no ha intervenido en la selección ni en la redacción de la pieza.»). El cuerpo de la pieza, el titular, el resumen y las fuentes no se tocan. Una pieza lleva una mención como mucho. Los análisis del director y las piezas que ya tratan del grupo (`excluir`) no llevan ninguna. La mención no cambia la firma ni los criterios de aprobación.

#### Escenario: pieza que trata del problema
- CUANDO la cabecera de una pieza (título, subtítulo, resumen, antetítulo) contiene una frase disparadora o dos palabras clave de un producto activo y la puntuación total supera su `umbral`
- ENTONCES la rutina escribe en la pieza `menciones: [{producto, nombre, texto, cta, url, estado: publicada, motivo, puntuacion, origen, propuesta_en}]` y el publicador pinta el bloque.

#### Escenario: pieza que solo roza el tema
- CUANDO las palabras clave aparecen solo en el cuerpo y la cabecera no trata del problema
- ENTONCES no se propone mención (evita «autobús» en una pieza sobre una dimisión).

#### Escenario: tope semanal
- CUANDO el producto ya tiene `max_por_semana` menciones publicadas en los últimos siete días
- ENTONCES la mención se guarda como `propuesta` (no se pinta) y aparece en el informe para que el director decida.

## ADDED Requisito: el director recibe cada mención con enlace de edición
Tras cada edición (paso 7 quinquies de la rutina) y tras cada pieza bajo demanda, si hubo menciones (publicadas o propuestas), se envía a `ruphoff@avionline.es` un correo con, por mención: título y URL de la pieza, producto, texto, motivo y dos enlaces de edición: el fichero de la pieza en GitHub (`edit/main/data/articles/<id>.json`, que es la fuente de verdad: cambiar `texto` o poner `estado: retirada`) y el editor del post en Ghost (`/ghost/#/editor/post/<post_id>` cuando la pieza tiene `ghost.post_id`). Sin menciones no se envía nada. El remitente es `redaccion@moticias.com` por Brevo (`BREVO_API_KEY`); si falta la clave, el informe queda en `work/menciones/<fecha>.html` y el aviso lo dice.

#### Escenario: el director retira una mención
- CUANDO el director pone `estado: retirada` en la mención (desde el enlace de GitHub) o borra el bloque en el editor de Ghost
- ENTONCES la siguiente publicación respeta su decisión: el bloque desaparece, la mención queda en el JSON con su historia y la reconciliación de Ghost no vuelve a escribirla (el post editado a mano tiene `html_hash` distinto y se anota en el informe de reconciliación).

## ADDED Requisito: medición
Cada enlace lleva `utm_source=moticias&utm_medium=nota-de-la-casa&utm_campaign=<producto>&utm_content=<id de pieza>`. El asesor semanal lee las menciones publicadas (`menciones` en `data/articles/`) y los clics (analítica de destino) y propone ajustes de `contexto`, `disparadores` y `excluir`; nunca los cambia solo.

## MODIFIED Requisito (campañas temáticas): «ninguna pieza menciona la solución»
Pasa a: ninguna pieza menciona la solución **dentro del texto**; la relación la hace la plataforma en huecos señalizados y en el bloque «Nota de la casa» del gestor de productos propios. `verticals/movilidad.json → campaigns.rules` y `manual-operativo.md` lo recogen.
