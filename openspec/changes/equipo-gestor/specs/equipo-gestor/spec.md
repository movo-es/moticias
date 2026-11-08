# Capacidad: equipo del gestor y suscriptores (nueva)

## ADDED Requisito: perfiles y permisos
| Perfil | Piezas (cajas) | Productos | Publicidad | Suscriptores | Equipo |
|---|---|---|---|---|---|
| superadmin | cambia | cambia | cambia | ve (correos completos) | gestiona |
| editor | cambia | ve | ve | ve (correos ocultos) | — |
| comercial | ve | cambia | cambia | ve (correos ocultos) | — |
| oficina | cambia | ve | ve | — | — |
El servidor comprueba el permiso en cada escritura; la página solo oculta o desactiva botones.

## ADDED Requisito: alta por invitación
El superadministrador da de alta nombre, correo y perfil; el gestor genera un enlace `…/gestor/?invitacion=<id>.<token>` de un solo uso, válido 7 días; solo se guarda la huella SHA-256 del token. Al abrirlo, la persona crea su contraseña (mínimo 10 caracteres), que se guarda como PBKDF2-SHA256 con sal (210.000 iteraciones), y entra.

#### Escenario: olvido de contraseña
- CUANDO el superadministrador pulsa «Enlace para cambiar la contraseña»
- ENTONCES se genera un enlace nuevo, se cierran las sesiones abiertas de esa persona y, al usarlo, crea una contraseña nueva.

## ADDED Requisito: suspensión
Nunca se borra a una persona. «Suspender» cierra sus sesiones al momento (como mucho un minuto de caché) e impide entrar; «Reactivar» la devuelve a su estado anterior. Un superadministrador no puede suspenderse ni quitarse el perfil a sí mismo.

## ADDED Requisito: datos personales fuera del repositorio público
`equipo.json` vive en el repositorio privado `EQUIPO_REPO` (por defecto `movo-es/moticias-equipo`). El repositorio público no contiene nombres, correos ni huellas.

## ADDED Requisito: suscriptores
La pestaña «Suscriptores» lee de la Admin API de Ghost los totales (todos, gratuitos, de pago, cortesía) y las ocho últimas altas, y enlaza a Ghost para gestionarlos. No guarda copia.
