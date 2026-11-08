# Cambio: equipo-gestor

Fecha: 9 de noviembre de 2026. Origen: Rainer pide «un gestor de suscriptores y administradores, editores…» y elige la opción «Ghost + equipo en mi gestor».

## Qué cambia

1. **Suscriptores**: siguen en Ghost (Members: altas, bajas, boletines, planes). El gestor añade la pestaña «Suscriptores» con los totales (gratuitos, de pago, cortesía), las últimas altas y el enlace a Ghost. Solo el superadministrador ve los correos completos.
2. **Redacción en Ghost** (Administrador, Editor, Autor, Colaborador): se invita en Ghost; el gestor enlaza a esa pantalla.
3. **Equipo del gestor**: una cuenta por persona (correo y contraseña) en lugar de contraseñas compartidas, con cuatro perfiles: superadministrador, editor, comercial y oficina. Alta por enlace de invitación de un solo uso (7 días) que el superadministrador manda por WhatsApp o correo; con él la persona crea su contraseña. Suspender en vez de borrar. Cambiar el perfil, suspender o generar un enlace nuevo cierra las sesiones de esa persona.
4. **Dónde viven los datos**: nombre, correo y huella de la contraseña (PBKDF2) no van al repositorio público; van a `movo-es/moticias-equipo` (privado), `equipo.json`, por la misma llave de GitHub del gestor. El código está en `src/equipo.py` y `api/gestor.py`.
5. La contraseña común (`GESTOR_CLAVE_SUPERADMIN`) queda como acceso de emergencia del superadministrador; `GESTOR_CLAVE_OFICINA`, como acceso antiguo de oficina hasta que la oficina tenga cuentas.

## Qué no cambia

Las reglas de las cajas, la escritura en GitHub y la publicación en Ghost. El historial de cada mención registra ahora el nombre de quien hizo el cambio.
