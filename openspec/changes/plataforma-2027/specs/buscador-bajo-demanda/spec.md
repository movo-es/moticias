# Capacidad: buscador y piezas bajo demanda (delta)

Decisión de Rainer (8-11-2026, tarde): hace falta un buscador; cuando un cliente busca algo que no está en las noticias publicadas, se busca fuera y, si se encuentra, se construye una noticia con la información encontrada, con el mismo formato y el mismo método de siempre, y se guarda para que esté disponible en el futuro.

## ADDED Requisito: buscador sobre lo publicado
El sitio ofrece búsqueda de texto completo sobre piezas, boletines, plazos y fichas de soluciones. En Ghost se usa la búsqueda nativa del tema (índice de posts y páginas) para lo público; en el repositorio, `src/buscador.py` busca en `data/` y emite un veredicto (`cubierto`, `parcial`, `sin_cobertura`) que usan los agentes. La hemeroteca conserva su búsqueda propia.

#### Escenario: la consulta está cubierta
- CUANDO el buscador encuentra una pieza cuya cabecera contiene los términos fuertes de la consulta
- ENTONCES se responde con esa pieza (y las relacionadas) y no se escribe nada nuevo.

## ADDED Requisito: encargo cuando no hay cobertura
Cuando la búsqueda pública devuelve pocos o ningún resultado, la página ofrece a los miembros con sesión «Pedir esta pieza a la redacción». El encargo guarda la consulta, la fecha, el `miembro_id` de Ghost (opaco) y el nivel; nunca el correo ni el nombre (el repositorio es público; con Supabase, la tabla `encargos` con RLS). Cuota por nivel (`verticals/movilidad.json → encargos.cuota`: lector 0, profesional 2 al mes, corporativa 10). Hasta que exista `app.moticias.com`, los encargos entran a mano (Rainer pasa la consulta a `/pieza-bajo-demanda`) o por un formulario que escribe `data/encargos/<id>.json` vía API de GitHub desde Vercel (`GITHUB_TOKEN` en Vercel, nunca en el repo).

## ADDED Requisito: la pieza bajo demanda es una pieza como las demás
`/pieza-bajo-demanda` busca primero; si el veredicto es `parcial` o `sin_cobertura`, investiga con el estándar de profundidad (fuentes primarias por API y medios profesionales, cada una abierta y fechada) y escribe `data/articles/<id>.json` completo (cuerpo de 1.000–1.500 palabras, cifras clave, cronología, 6–12 fuentes con al menos una primaria, los cinco bloques, foto con licencia o ninguna) con `origen: "bajo-demanda"` y `encargo: {id, consulta, fecha}`. Firma y aprobación según los criterios del vertical: rutinaria se publica directa; crítica queda `pendiente` para el director. Pasa por el gestor de menciones. Se publica en Ghost, entra en la hemeroteca con la edición siguiente y queda en `docs/ediciones.md` como «fuera de edición · bajo demanda». Queda disponible para siempre.

#### Escenario: no hay fuente primaria
- CUANDO la investigación no reúne una fuente primaria enlazable y seis fuentes fechadas
- ENTONCES no se escribe la pieza; el encargo pasa a `sin_fuentes` con qué se buscó y dónde, y el solicitante recibe las referencias externas que sí existen.

#### Escenario: novedad sobre una pieza antigua
- CUANDO la pieza que cubre la consulta tiene más de 60 días y hay hechos nuevos
- ENTONCES se escribe una pieza nueva que cita la anterior; la anterior no se modifica.

## ADDED Requisito: aviso al solicitante sin guardar su correo
El correo del miembro se lee de la Admin API de Ghost en el momento de avisar y no se escribe en ningún fichero ni registro del repositorio. El aviso sale por Brevo desde `redaccion@moticias.com` y contiene el resultado y el enlace. Las consultas pasadas a mano se responden en la sesión.

## ADDED Requisito: tarea programada
«MOTICIAS · piezas bajo demanda»: laborables cada dos horas de 8:00 a 20:00 (Europe/Madrid), ejecuta `/pieza-bajo-demanda` sobre los encargos pendientes, tres por sesión como máximo. Sin encargos pendientes, termina en una línea.
