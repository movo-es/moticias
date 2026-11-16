# Capacidad: menú y «La voz del editor» · delta del cambio `subidas-que-no-llegan`

## ADDED Requisitos

### Requisito: lo aprobado que no llega a la web se dice y se reintenta (cambio `subidas-que-no-llegan`, 16-11-2026)
Aprobar guarda la pieza como publicada y después la sube a Ghost. Si esa subida falla, el gestor no la da por publicada: lo dice, ofrece subirla y la reintenta solo.

#### Escenario: la subida falla al aprobar
- DADA una columna que el editor jefe aprueba con «Publicar ahora»
- CUANDO Ghost rechaza la subida
- ENTONCES el aviso dice que no ha llegado a la web, la tarjeta «La voz del editor» la enseña como «Aprobada, pero no ha llegado a la web» con el botón «Subir a la web ahora» y sin enlace público

#### Escenario: reintento automático
- DADA una pieza aprobada cuya última subida falló
- CUANDO corre el cron `web_reintentos` (cada 20 minutos)
- ENTONCES se vuelve a subir, el resultado queda en el registro y, si llega, deja de salir como fallida

#### Escenario: tope
- DADA una pieza con 12 reintentos automáticos fallidos
- CUANDO corre el cron
- ENTONCES no se reintenta más y el error sigue a la vista para subirla a mano

#### Escenario: fecha de «Publicar ahora»
- DADA una aprobación con «Publicar ahora»
- CUANDO se guarda la fecha de publicación
- ENTONCES lleva segundos y zona horaria (Ghost rechaza la fecha sin segundos)
