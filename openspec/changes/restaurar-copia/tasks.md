# Tareas · restaurar-copia

Propuesta del 15-11-2026. Aprobada por Rainer el 15-11-2026, con las tres decisiones como se proponían.

## 0. Antes de aplicar
- [x] 0.1 «Sí» de Rainer y decisiones 1–3. «Sí» del 15-11-2026.

## 1. Contenido
- [x] 1.1 `api/gestor.py`: `?a=versiones` (commits de un fichero de `data/` por la API de GitHub, con diferencias campo a campo) y `?a=restaurar_version` (commit nuevo, `revisiones`, `revised_at`, republicación en Ghost, aviso, deshacer).
- [x] 1.2 Permiso nuevo `restaurar` en `src/equipo.py` (editor y superadmin; piezas firmadas por el director, solo superadmin). Editor y superadministrador; el servidor lo comprueba (403).
- [x] 1.3 Validación antes de publicar: `src/tipos.py` y tres ejes. `T.comprobar` antes de escribir; tipo y ejes se completan desde la versión de hoy si faltan.

## 2. Base privada
- [x] 2.1 Migración 011: esquema `copia` (fuera de la API), función `copia.instantanea()` con `pg_cron` a las 03:40 y conservación de 14 días; funciones `copia_diferencias(tabla, fecha)` y `copia_recuperar(tabla, id, campos)` con las reglas de «No contactar» y de solo añadir. Aplicada el 15-11-2026 (y primera copia hecha: 17 tablas). Equipo, llave del gestor, buzón y registro de copias, fuera.
- [x] 2.2 `api/gestor.py`: `?a=copia_diferencias` y `?a=copia_recuperar`, con `gestor_registro`.

## 3. Gestor
- [x] 3.1 Pestaña «Restaurar» en `app/public/gestor/index.html`: contenido (buscar, versiones, diferencia, restaurar, deshacer) y base privada (tabla, fecha, diferencias, recuperar).
- [x] 3.2 Correo al director en cada restauración.

## 4. Documentación
- [x] 4.1 `docs/copia-de-seguridad.md § Restaurar desde el gestor`, `docs/gestores-portal.md`, `docs/manual-operativo.md`, `CLAUDE.md`.

## 5. Pruebas
- [ ] 5.1 (pendiente: desde esta sesión GitHub no permite escribir por su API; lectura de versiones y comparación comprobadas contra el repositorio real) Restaurar y deshacer una pieza de prueba (un anuncio en borrador), con el commit, la revisión y el aviso.
- [x] 5.2 Recuperar un campo cambiado de una ficha de prueba del CRM y comprobar que «No contactar» no se puede quitar. Hecho en la base dentro de una transacción que se deshizo al terminar: campos recuperados, ficha borrada reinsertada, «No contactar» conservado, equipo rechazado, sin llave no se ve nada.
- [x] 5.3 Un editor de prueba no puede restaurar una pieza firmada por el director (403). Hecho: 403 «las piezas que firma el director solo las restaura él».

## 6. Cierre
- [ ] 6.1 Fundir la spec en `openspec/specs/restauracion/` y archivar.
