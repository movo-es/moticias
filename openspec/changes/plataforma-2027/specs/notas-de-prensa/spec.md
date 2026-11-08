# Capacidad: sala de prensa (delta)

## ADDED Requisito: recepción con emisor verificado
Un comunicado entra por el formulario de `app.moticias.com/prensa/enviar` o por el buzón `prensa@moticias.com`. Queda ligado a una organización (`organizations`) y a un contacto profesional. No se publica sin verificar al emisor: correo de dominio corporativo de la organización o enlace de confirmación.

#### Escenario: nota desde un correo personal
- CUANDO llega una nota desde un dominio que no es el de la organización declarada
- ENTONCES se guarda como `recibida`, se envía un enlace de confirmación al correo corporativo de la organización y no se publica hasta que se confirme.

## ADDED Requisito: publicación marcada, fuera de lo editorial
Cada comunicado se publica en Ghost en `/notas-de-prensa/` con la etiqueta interna `#comunicado`, autor «Comunicado», la organización, la fecha y la marca visible «Comunicado de empresa · no es contenido editorial». Nunca aparece en la portada editorial, en el boletín diario ni en las secciones de noticias; nunca se reescribe como noticia sin verificación independiente.

#### Escenario: comunicado con valor informativo
- CUANDO un comunicado publicado contiene un hecho relevante para el sector
- ENTONCES entra en `senales` con `kind: comunicado` y en `work/sensores/candidatas.md`, y la rutina diaria lo trata como cualquier otra candidata: busca fuente primaria y lo escribe con sus propias fuentes, citando el comunicado como una más.

## ADDED Requisito: valoración opcional para el emisor
El emisor puede pedir una valoración (novedad, impacto por segmento, claridad, datos que faltan, titular alternativo, destinatarios recomendados). Se entrega solo al emisor, no se publica, y se cobra según tarifa.

## ADDED Requisito: difusión opcional solo a quien optó
La difusión envía el comunicado, por el motor de envíos, a los suscriptores con el consentimiento separado «recibir comunicados» del sector correspondiente y a redes con la plantilla de `/promo-social`. Sin ese consentimiento no se envía nada.

## ADDED Requisito: notas del grupo
Los comunicados de Movenbus, MUFMI, MOVO o Avionline se publican con las mismas reglas y además con la marca «Empresa del grupo editor».

## ADDED Requisito: datos
`press_releases` (id, vertical_id, org_id, contact_id, title, body_md, attachments jsonb, status: recibida | publicada | retirada, verified_at, ghost_post_id, ghost_url, assessment jsonb, distribution jsonb, received_at, published_at). Nunca se borra; retirar = `retirada`.
