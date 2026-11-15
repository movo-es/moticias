# Copia de seguridad en el Mac

## ADDED Requisitos

### Respaldo, nunca dependencia
- Producción y tareas programadas no leen nada del Mac. Si el Mac no hace copias, lo único que cambia es que llega un aviso.

### Qué se copia
- El repositorio `movo-es/moticias` completo, con todas sus ramas e historial (`git bundle`).
- La base privada de Supabase «moticias» (`pg_dump`), cifrada antes de escribirse en disco.
- Lo que solo está en Ghost (miembros, ajustes, boletines, planes, etiquetas, páginas y posts), cifrado; el tema, mientras no esté versionado, por descarga manual mensual.

#### Escenario: datos personales
- DADA una copia de la base privada o de los miembros de Ghost
- CUANDO se guarda
- ENTONCES está cifrada, solo en `~/Copias/MOTICIAS/`, y nunca en el repositorio ni en otro servicio

### Dónde y cuándo
- La lanza `launchd` cuando el Mac está encendido (o al despertar, si se perdió la hora), en `~/Copias/MOTICIAS/AAAA-MM-DD/`, fuera de las carpetas de trabajo y de iCloud.
- Se conservan las copias que fije Rainer; el guion solo borra copias viejas de esa carpeta.

### Claves
- Todas en el llavero de macOS; nunca en ficheros, en el `.plist` ni en el repositorio. Accesos de solo lectura.

### Registro y aviso
- Cada copia y cada prueba dejan en `copias_registro` fecha, tamaños, huellas y recuentos, sin ningún dato.
- El gestor muestra la fecha de la última copia y de la última copia probada.

#### Escenario: Mac apagado
- DADO que pasan más días de los fijados sin una copia correcta
- CUANDO corre el cron diario
- ENTONCES Rainer recibe un correo con la fecha de la última copia

### Prueba de restauración
- Una copia solo cuenta como probada si se ha restaurado: bundle clonado y con el commit esperado, base restaurada en local con las filas registradas, datos de Ghost descifrados y completos.

#### Escenario: prueba mensual
- DADO el primer lunes del mes
- CUANDO corre la prueba
- ENTONCES el gestor muestra «Última copia probada: <fecha>» o el motivo del fallo
