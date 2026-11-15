# Capacidad: agenda de eventos (delta ADDED)

## Requisito: colección propia
Los eventos (ferias, congresos, jornadas…) viven en `data/eventos/<inicio>-<slug>.json`, separados de `data/agenda/` (plazos de la edición diaria). Temas, colores, formatos, modalidades y estados se leen de `verticals/movilidad.json → agenda`.

#### Escenario: evento incompleto
- CUANDO un evento no tiene fuente con URL y fecha, o no tiene fecha de inicio, o su tema no está en el vertical, o su territorio no está en la taxonomía
- ENTONCES `src/eventos.py validar` lo rechaza y no se publica.

## Requisito: nada sin comprobar
Fecha, sede y enlace se comprueban en la web del organizador o en un comunicado suyo; si dos fuentes discrepan, manda el organizador. Lo no comprobado se dice («sede por anunciar», «hora sin publicar»).

## Requisito: la página
`moticias.com/agenda/` enseña de hoy a tres meses, con respuesta directa calculada, mapa, filtros combinables (mes, ciudad, tema), lista ordenable, columna lateral y pie con la última comprobación. Lleva `ItemList` y `FAQPage`; cada ficha, `Event`. Todo el contenido está en el HTML servido; el script solo filtra.

#### Escenario: cita que cruza dos meses
- CUANDO un evento empieza el 30 de noviembre y acaba el 3 de diciembre
- ENTONCES cuenta en la pestaña de noviembre y en la de diciembre.

#### Escenario: ciudad con varios temas
- CUANDO en una ciudad hay citas de más de un tema
- ENTONCES su marca es blanca con aro discontinuo y el número de citas.

#### Escenario: filtro sin resultados
- CUANDO la combinación de filtros no deja ninguna cita
- ENTONCES se enseña el aviso y el botón «Quitar filtros».

## Requisito: terceros proponen, el editor jefe publica
Lo que llega por «Subir mi evento» o por el barrido entra como `propuesto`. Publicar y retirar solo los hace el superadministrador; el servidor responde 403 a los demás.

#### Escenario: envío sin el permiso obligatorio
- CUANDO el formulario llega sin el consentimiento de tratamiento
- ENTONCES no se guarda y se explica por qué.

## Requisito: CRM sin duplicados y con el contacto más cercano
Publicar un evento crea o actualiza la cuenta de cada organizador casándola por dominio (por dominio y nombre en dominios compartidos por muchos organismos), con `origen: agenda` y etiqueta `organizador-eventos`. Cada contacto lleva nivel (`directo`, `prensa`, `general`, `centralita`), URL de fuente y fecha; sin ninguno, «Falta contacto». Nada deducido; «No contactar» es para siempre; sin permiso expreso no hay envíos comerciales.

## Requisito: nada se borra
Un evento se retira con `estado: retirado`; al pasar su fecha de fin sale de la página y queda en el archivo como `pasado`.

## Requisito: datos personales fuera del repositorio
Nombres, correos y teléfonos de responsables y organizadores solo en la base privada. Una prueba busca en el repositorio los de la semilla y debe dar cero.
