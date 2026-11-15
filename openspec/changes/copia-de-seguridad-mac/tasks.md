# Tareas · copia-de-seguridad-mac

Propuesta del 15-11-2026. **No aplicar sin el «sí» de Rainer y sus tres decisiones** (`proposal.md § Decisiones`).

## 0. Antes de aplicar
- [ ] 0.1 «Sí» de Rainer: frecuencia, conservación y segunda copia en la nube.
- [ ] 0.2 Elegir el cifrado: imagen de disco cifrada de macOS (`hdiutil`, AES-256, sin instalar nada) o `age` (un fichero por parte, más fácil de comprobar). Recomendación: imagen cifrada.

## 1. Accesos de solo lectura
- [ ] 1.1 Usuario de Postgres `copia_lectura` en Supabase «moticias» con `select` sobre `public` y nada más (migración 010).
- [ ] 1.2 Token de GitHub de solo lectura para `movo-es/moticias` (y el espejo, si se decide).
- [ ] 1.3 Guía para que Rainer guarde las claves en el llavero de macOS (pasos de copiar y pegar, con `security add-generic-password`; nunca en el chat).

## 2. Guiones (en el repositorio, sin claves)
- [ ] 2.1 `scripts/copia-mac/copia.sh`: bundle del repositorio, `pg_dump` cifrado, exportación de Ghost cifrada, huellas, conservación, envío del registro.
- [ ] 2.2 `scripts/copia-mac/com.moticias.copia.plist` y `instalar.sh` (copia el agente a `~/Library/LaunchAgents/` y lo carga).
- [ ] 2.3 `scripts/copia-mac/restaurar-prueba.sh` y su anotación en el registro.

## 3. Registro y aviso
- [ ] 3.1 Migración 010: tabla `copias_registro` (fecha, duración, partes, tamaños, huellas, filas por tabla, ok, prueba_ok, error), de solo añadir, sin datos personales.
- [ ] 3.2 `api/gestor.py`: `?a=copia` (POST con token, solo el Mac) y el resumen en la pantalla del editor jefe («Última copia», «Última copia probada»).
- [ ] 3.3 Aviso por correo (Brevo) desde el cron diario existente cuando pasen más días de los fijados o falle.

## 4. Documentación
- [ ] 4.1 `docs/copia-de-seguridad.md`: qué se copia, dónde, cómo restaurar de verdad y cómo hacer la prueba.
- [ ] 4.2 `docs/arquitectura.md`, `docs/puesta-en-marcha.md`, `CLAUDE.md`.

## 5. Pruebas
- [ ] 5.1 Una copia completa en el Mac de Rainer y su registro en el gestor.
- [ ] 5.2 Una prueba de restauración completa, con el resultado anotado.
- [ ] 5.3 Aviso forzado (umbral a 0 días) recibido por correo.

## 6. Cierre
- [ ] 6.1 Fundir la spec en `openspec/specs/copia-de-seguridad/` y archivar.
