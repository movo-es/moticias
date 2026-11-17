# Capacidad: publicación en moticias.com (Ghost) · delta del cambio `entradilla-y-linkedin`

## ADDED Requisitos

### Requisito: el resumen del post es la entradilla (cambio `entradilla-y-linkedin`, 17-11-2026)
El resumen de cada post en Ghost (`custom_excerpt`, 300 caracteres como mucho) es la `entradilla` de la pieza. Ningún texto que se mande a Ghost —resumen, descripción para buscadores, fichas de la agenda, notas de prensa— se corta a media palabra. El cron `web_reintentos` comprueba que el resumen de cada post coincide con la entradilla de su pieza y, si no, cambia solo el resumen.

#### Escenario: tarjeta de una sección
- DADA una pieza publicada
- CUANDO el lector ve su tarjeta en una sección de moticias.com
- ENTONCES el texto bajo el titular termina en una frase completa

#### Escenario: resumen distinto en Ghost
- DADO un post cuyo resumen no coincide con la entradilla de su pieza
- CUANDO pasa el cron `web_reintentos`
- ENTONCES el resumen del post pasa a ser la entradilla, sin tocar el texto, la fecha ni el estado del post

### Requisito: compartir en LinkedIn desde el gestor (cambio `entradilla-y-linkedin`, 17-11-2026)
La ficha de cada pieza publicada del gestor tiene «Compartir en LinkedIn»: prepara una publicación con la entradilla, la línea «Suscríbete gratis para seguir leyendo:» con el enlace a la pieza y la firma «moticias.com - Noticias con M de Movilidad y Transportes» (`verticals/<id>.json → redes.linkedin`). El texto se puede retocar. El botón copia el texto y abre LinkedIn (en el móvil, el menú de compartir del teléfono); la imagen es la tarjeta del enlace que genera LinkedIn con la foto de la pieza. Nunca publica por su cuenta.

#### Escenario: compartir una pieza publicada
- DADA una pieza publicada abierta en el gestor
- CUANDO se pulsa «Compartir en LinkedIn»
- ENTONCES el texto queda copiado y se abre LinkedIn con la publicación preparada, que la persona publica

#### Escenario: pieza pendiente o retirada
- DADA una pieza que no está publicada
- CUANDO se abre en el gestor
- ENTONCES no se ofrece compartirla

#### Escenario: texto sin el enlace
- DADO que la persona borra el enlace a la pieza del texto
- CUANDO pulsa «Compartir en LinkedIn»
- ENTONCES el gestor avisa de que sin el enlace no hay imagen y no abre LinkedIn
