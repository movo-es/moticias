# Cambio: copia-de-seguridad-mac

Fecha: 15 de noviembre de 2026. Origen: decisión de Rainer del mismo día («todo vive en la nube y el MacBook recibe copias regulares, solo como respaldo»). Estado: **aprobada por Rainer el 15-11-2026** («sí» a la propuesta y a las tres decisiones tal como se proponen); en aplicación.

Respuesta corta: el propio macOS lanza, cuando el Mac está encendido, una copia de tres cosas —el repositorio con todo su historial, la base privada de Supabase y lo que solo está en Ghost— en una carpeta aparte (`~/Copias/MOTICIAS/`), cifrada en lo que tiene datos personales y con las claves en el llavero. Cada copia deja un registro sin datos (fecha, tamaños, huellas) que el gestor enseña; si pasan demasiados días sin copia, avisa. Una prueba de restauración documentada y periódica dice si la copia sirve. Nada en producción ni ninguna tarea programada depende del Mac: si el Mac no se enciende, lo único que pasa es que llega el aviso.

## Por qué (lo comprobado el 15-11-2026)

- **El repositorio no lo contiene todo.** Fuera de él viven:
  - la base privada de Supabase «moticias» (19 tablas, ~1,3 MB hoy): CRM (`crm_*`), equipo (`equipo`, `gestor_llave`, `gestor_registro`), base de prensa (`medios`, `periodistas`, `prensa_*`), seguimiento (`pub_diario`, `pub_comprobaciones`), encargos (`encargos_gestor`) y buzón (`repo_buzon`). Tiene nombres y correos: nunca puede ir al repositorio, que es público;
  - en Ghost: los miembros (suscriptores con su etiqueta `cat:`), los ajustes, los boletines, los planes, las páginas y el **tema**, que sigue sin versionar (`ghost/theme/` no existe).
- **Qué se puede sacar de Ghost con la clave de integración** (probado, solo lectura): miembros, ajustes, boletines, planes, páginas y posts responden 200; el tema y la exportación completa de la base de Ghost responden 403 (Ghost los reserva a una sesión de usuario). Hasta que el tema se versione (`publicar-en-ghost-v1`), su copia es manual desde el panel.
- Hoy no existe ninguna copia fuera de los propios servicios.

## Qué cambia

1. **Lanzador del Mac.** Un agente de `launchd` (`~/Library/LaunchAgents/com.moticias.copia.plist`) con hora fija; si el Mac estaba dormido o apagado a esa hora, macOS la ejecuta al despertar. Llama a un único guion versionado en el repositorio (`scripts/copia-mac/copia.sh`, sin ninguna clave dentro) y escribe su salida en `~/Copias/MOTICIAS/registro.log`.
2. **Carpeta aparte.** `~/Copias/MOTICIAS/AAAA-MM-DD/`, fuera de cualquier carpeta de trabajo y de cualquier clon del repositorio, excluida de iCloud Drive.
3. **Las tres copias.**
   1. **Repositorio:** `git bundle` de `movo-es/moticias` con todas las ramas y todo el historial (un solo fichero, comprobable con `git bundle verify`). Es público: va sin cifrar.
   2. **Base privada:** `pg_dump` de Supabase en formato propio de PostgreSQL, **cifrado** antes de tocar el disco (imagen de disco cifrada de macOS o `age`; decisión técnica en `tasks.md`). Solo en el Mac, nunca en el repositorio ni en ningún servicio de terceros.
   3. **Ghost:** con la Admin API, miembros, ajustes, boletines, planes, etiquetas, páginas y posts en JSON, **cifrados** (los miembros son datos personales). El tema, mientras no esté en el repositorio, lo descarga Rainer a mano una vez al mes desde el panel (el guion le recuerda cuándo toca) y se guarda en la misma carpeta.
4. **Claves en el llavero de macOS.** Conexión de solo lectura a Supabase, clave de Ghost, token de lectura de GitHub, frase del cifrado y token del registro: se leen con `security find-generic-password` en el momento de usarlas. Nunca en ficheros, ni en el `.plist`, ni en el repositorio. Para la base se crea un usuario de Postgres de **solo lectura**.
5. **Registro visible.** Al terminar, el guion envía al gestor (`POST /api/gestor?a=copia`, con su token) solo fecha, duración, tamaños y huellas SHA-256 de cada parte —ningún dato— a una tabla nueva `copias_registro` (migración 010). El gestor enseña «Última copia: hace N días» y, si pasan más días de los fijados sin copia o la última falló, el cron diario que ya existe avisa por correo a Rainer. Que el Mac no avise nunca bloquea nada.
6. **Conservación.** El guion borra solo copias antiguas **de la carpeta de copias** según la regla que fije Rainer; nunca toca nada de producción.
7. **Prueba de restauración.** `scripts/copia-mac/restaurar-prueba.sh` restaura la última copia en una carpeta temporal y comprueba: el bundle se clona y su último commit coincide con `main` de ese día; el volcado de la base se restaura en un PostgreSQL local y cada tabla tiene las filas que dice el registro; los JSON de Ghost se descifran y tienen los miembros esperados. El resultado se anota en `copias_registro` (`prueba_ok`). Una copia sin prueba de restauración no cuenta: el gestor distingue «copias» de «copias probadas». Procedimiento escrito en `docs/copia-de-seguridad.md`, también para restaurar de verdad.

## Qué no cambia

Producción sigue entera en la nube (Vercel, Supabase, Ghost, GitHub, tareas programadas de Claude). Ninguna tarea ni ningún cron lee del Mac. No se guarda ningún dato personal en el repositorio. Las copias propias de Supabase y Ghost(Pro), si su plan las incluye, siguen como estén.

## Límites conocidos

- El tema de Ghost y la exportación completa de Ghost no se pueden sacar con la clave de integración: copia manual del tema hasta `publicar-en-ghost-v1`.
- Si el Mac pasa semanas apagado, no hay copia nueva: para eso es el aviso, y la decisión 3.
- La restauración de la base en local necesita PostgreSQL en el Mac (Postgres.app, gratuito); se instala una vez.

## Decisiones que le tocan a Rainer

1. **Cada cuánto.** Propuesta: a diario a las 13:30 (hora a la que el Mac suele estar encendido) y aviso si pasan **3 días** sin copia correcta; prueba de restauración automática **cada mes** (el primer lunes).
2. **Cuántas copias se conservan.** Propuesta: las 7 últimas diarias, 4 semanales y 12 mensuales (con el tamaño de hoy, menos de 100 MB en total).
3. **Segunda copia en la nube.** Propuesta: **sí, solo del repositorio**, en un repositorio privado espejo (`movo-es/moticias-respaldo`, actualizado por un cron de Vercel, sin depender del Mac). La base privada y los miembros de Ghost seguirían **solo en el Mac**, como pidió; si quiere también una segunda copia cifrada de esos datos fuera del Mac, hay que elegir dónde (un disco externo o un servicio europeo) y decidirlo aparte.

## Decisiones de Rainer (15-11-2026)

1. **Frecuencia:** a diario a las 13:30; aviso si pasan más de 3 días sin copia correcta; prueba de restauración el primer lunes de cada mes (y siempre que la última correcta tenga más de 35 días).
2. **Conservación:** 7 diarias, 4 semanales y 12 mensuales.
3. **Segunda copia en la nube:** sí, solo del repositorio, en `movo-es/moticias-respaldo` (privado). La base privada y los miembros de Ghost, solo en el Mac.

Decisión técnica (0.2): imagen de disco cifrada de macOS (AES-256, `hdiutil`), sin instalar nada; los datos se escriben directamente dentro de la imagen.
