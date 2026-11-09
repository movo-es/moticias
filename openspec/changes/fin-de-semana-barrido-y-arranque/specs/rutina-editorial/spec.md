# Rutina editorial · cambios

## ADDED Requirements

### Requirement: Arranque que avisa
La rutina diaria SHALL comprobar antes de las 06:45 que puede subir a `main`, que tiene `GHOST_URL` y `GHOST_ADMIN_KEY` y las herramientas de la base del portal, y SHALL avisar en ese momento si falta algo.

#### Scenario: falta la clave de Ghost
- **WHEN** la sesión arranca sin `GHOST_ADMIN_KEY`
- **THEN** a las 06:4x llega una notificación con lo que falta y su arreglo, y la edición sigue en el portal

### Requirement: Nada se pierde si no se puede subir
Una sesión que no puede hacer `git push` SHALL guardar su trabajo (sin datos regenerables) como parche en el proyecto de Claude, `claude/moticias-pendiente/`, y la siguiente sesión con permiso SHALL aplicarlo, subirlo y borrarlo.

#### Scenario: el proxy rechaza el push
- **WHEN** `git push origin HEAD:main` falla dos veces
- **THEN** queda `claude/moticias-pendiente/<AAAAMMDD-HHMM>-edicion.patch` y la primera línea del aviso lo dice

### Requirement: Batidas de fin de semana
Los sábados, domingos y festivos nacionales SHALL correr batidas de grandes noticias (11:00 y 17:30, hora de Madrid); SHALL publicar una edición extra solo si una noticia lo merece y SHALL guardar lo demás en `data/reserva/` para la edición siguiente, que lo usa en su selección.

#### Scenario: sábado sin grandes noticias
- **WHEN** la batida no encuentra nada que merezca edición extra
- **THEN** no publica ni avisa, y lo que tenga interés queda en `data/reserva/{fecha}.json`

### Requirement: Barrido a demanda
El gestor y el menú ✎ del editor jefe en moticias.com SHALL ofrecer al editor jefe y a los editores «Iniciar barrido de noticias ahora», que lanza la batida por el disparador de API de su tarea, con el token solo en el servidor.

#### Scenario: Rainer pulsa el botón
- **WHEN** pulsa el botón con la pista «corte Madrid-Sevilla»
- **THEN** la tarea arranca, el gestor muestra la hora y el resultado llega como aviso al móvil
