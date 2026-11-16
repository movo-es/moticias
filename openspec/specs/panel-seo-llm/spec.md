# Capacidad: panel SEO y asistentes de IA (cambio `panel-seo-llm`, 16-11-2026)

### Requisito: batería de asistentes
Cada semana, y a mano desde el panel, las preguntas fijas del sector se hacen a cada asistente configurado; se guarda si citan moticias.com y si nombran a MOVO, Movenbus y MUFMI asociadas con lo suyo, y el panel compara con la ronda anterior.

### Requisito: propuestas y «Hazlo con IA»
El panel ordena las propuestas por impacto. Título y descripción para buscadores, enlaces internos y marcado se aplican directo, se republican y se pueden deshacer, editar o regenerar; lo que toque el texto de una pieza pasa por la vista previa del editor.

#### Escenario: deshacer
- DADO un título para buscadores aplicado con «Hazlo con IA»
- CUANDO el editor jefe pulsa «Deshacer»
- ENTONCES la pieza vuelve al valor anterior en el repositorio y en moticias.com y el cambio queda como «deshecho»

#### Escenario: sin cifras inventadas
- DADO que la IA propone un título con una cifra que no está en la pieza
- CUANDO se pide «Hazlo con IA»
- ENTONCES no se aplica y el panel pide regenerarlo

### Requisito: Search Console
Las cifras de Google entran solo con una cuenta de servicio de permiso restringido cuyas claves viven en Vercel; nunca en el repositorio.
