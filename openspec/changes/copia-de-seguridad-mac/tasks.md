# Tareas · copia-de-seguridad-mac

Propuesta del 15-11-2026. Aprobada por Rainer el 15-11-2026 (`proposal.md § Decisiones de Rainer`).

## 0. Antes de aplicar
- [x] 0.1 «Sí» de Rainer: frecuencia, conservación y segunda copia en la nube. «Sí» del 15-11-2026 a las tres propuestas.
- [x] 0.2 Elegir el cifrado: imagen de disco cifrada de macOS (`hdiutil`, AES-256, sin instalar nada) o `age` (un fichero por parte, más fácil de comprobar). Recomendación: imagen cifrada. Imagen cifrada.

## 1. Accesos de solo lectura
- [x] 1.1 Usuario de Postgres `copia_lectura` en Supabase «moticias» con `select` sobre `public` y nada más (migración 010). Migración 010 aplicada el 15-11-2026: `copia_lectura` sin poder entrar hasta que el instalador del Mac le pone contraseña (Rainer la pega en el editor SQL; nunca pasa por el chat ni por el repositorio).
- [x] 1.2 Token de GitHub de solo lectura para `movo-es/moticias` (y el espejo, si se decide). No hace falta: el repositorio es público y el Mac lo clona sin token. El espejo usa su propio secreto `ESPEJO_TOKEN` en GitHub.
- [x] 1.3 Guía para que Rainer guarde las claves en el llavero de macOS (pasos de copiar y pegar, con `security add-generic-password`; nunca en el chat). Lo hace `instalar.sh` (`security add-generic-password`), sin que Rainer teclee comandos de llavero.

## 2. Guiones (en el repositorio, sin claves)
- [x] 2.1 `scripts/copia-mac/copia.sh`: bundle del repositorio, `pg_dump` cifrado, exportación de Ghost cifrada, huellas, conservación, envío del registro.
- [x] 2.2 `scripts/copia-mac/com.moticias.copia.plist` y `instalar.sh` (copia el agente a `~/Library/LaunchAgents/` y lo carga). El `.plist` lo escribe `instalar.sh` con las rutas del Mac.
- [x] 2.3 `scripts/copia-mac/restaurar-prueba.sh` y su anotación en el registro.

## 3. Registro y aviso
- [x] 3.1 Migración 010: tabla `copias_registro` (fecha, duración, partes, tamaños, huellas, filas por tabla, ok, prueba_ok, error), de solo añadir, sin datos personales. Aplicada; también la puerta `copia_anotar(token, datos)` y la huella del token en `privado.copias_llave`.
- [x] 3.2 `api/gestor.py`: `?a=copia` (POST con token, solo el Mac) y el resumen en la pantalla del editor jefe («Última copia», «Última copia probada»). En Equipo → «Copias de seguridad».
- [x] 3.3 Aviso por correo (Brevo) desde el cron diario existente cuando pasen más días de los fijados o falle. Cron `copias_vigilar`, diario a las 08:05 UTC.

## 4. Documentación
- [x] 4.1 `docs/copia-de-seguridad.md`: qué se copia, dónde, cómo restaurar de verdad y cómo hacer la prueba.
- [x] 4.2 `docs/arquitectura.md`, `docs/puesta-en-marcha.md`, `CLAUDE.md`.

## 5. Pruebas (en el Mac de Rainer: tras `instalar.sh`)
- [ ] 5.1 Una copia completa en el Mac de Rainer y su registro en el gestor.
- [ ] 5.2 Una prueba de restauración completa, con el resultado anotado.
- [ ] 5.3 Aviso forzado (umbral a 0 días) recibido por correo.

- [ ] 5.4 Espejo: crear `movo-es/moticias-respaldo` y el secreto `ESPEJO_TOKEN`; Actions → «espejo» en verde.

## 6. Cierre
- [ ] 6.1 Fundir la spec en `openspec/specs/copia-de-seguridad/` y archivar.
