# Prensa y medios

## ADDED Requisito: ficha de medio y de periodista
Todo medio es una cuenta `medio` del CRM con ficha en `medios`; todo periodista, una persona del CRM con ficha en `periodistas`. Cada dato de contacto lleva su fuente (`fuentes`) y la fecha de verificación.

#### Escenario: dato sin fuente
- CUANDO la tarea de los miércoles propone un correo, un teléfono o una dirección sin enlace a la página que lo publica
- ENTONCES `src/prensa.py validar` lo rechaza y no se carga.

## ADDED Requisito: colaboración vacía hasta el primer contacto
- CUANDO un medio o un periodista no tiene ninguna actividad de contacto ni ningún envío recibido
- ENTONCES su colaboración es vacía («Sin contacto aún»), nunca «poco colaborador».
- CUANDO alguien la fija a mano
- ENTONCES el recálculo no la toca; si la deja vacía, vuelve al cálculo.

## ADDED Requisito: envíos con aprobación del editor jefe
- CUANDO un perfil que no es superadministrador pide enviar
- ENTONCES el servidor contesta 403; solo puede crear borradores.
- CUANDO se envía
- ENTONCES cada destinatario recibe un correo propio con enlace de baja firmado; quien tiene «No contactar» no recibe nada, aunque estuviera en el borrador.

## ADDED Requisito: invitaciones
- CUANDO el envío es una invitación a suscribirse
- ENTONCES se excluye a los suscriptores de MOTICIAS y a quien recibió otra invitación en los últimos 90 días.

## ADDED Requisito: suscriptores de MOTICIAS
- CUANDO un miembro de Ghost tiene el correo de un periodista de la base o un correo del dominio de un medio (no genérico)
- ENTONCES el periodista queda marcado como suscriptor (y, si no existía, se crea en ese medio).

## ADDED Requisito: actualización semanal
Los miércoles a las 15:30 (Europe/Madrid) la tarea `/medios-actualizar` verifica, completa y amplía la base y busca coberturas; a las 14:45 UTC el cron de Vercel detecta suscriptores, sincroniza Brevo y recalcula.
