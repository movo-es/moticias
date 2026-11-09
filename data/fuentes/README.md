# Fuentes por dominio (`data/fuentes/dominios.json`)

Clasificación de dominios que el editor jefe (o un editor, sin confirmar) registra desde el gestor al encargar una noticia (opción 2 de «Nueva noticia», cambio `seguimiento-y-seo`, decisión de Rainer del 9-11-2026). Vale para **todas** las noticias de ese dominio, no solo para la del encargo. La leen la rutina diaria, `/noticias-gestor` y `/pieza-bajo-demanda` al valorar una fuente.

- `notas_de_prensa`: dominio emisor de comunicados (sala de prensa de una empresa, institución o asociación). Un comunicado nunca es noticia sin verificación independiente (regla de siempre); con verificación, se publica con la fuente citada como emisor.
- `informacion`: fuente de información de confianza (cuenta como una de las «dos fuentes profesionales de confianza» de la regla de publicación directa).
- `no_confianza`: nada que venga de ahí se publica sin la aprobación del editor jefe (`status: pendiente`), aunque se verifique en otra parte.
- `confirmado: false`: lo registró alguien que no es el editor jefe; hasta que él lo confirme en el gestor, cuenta como `no_confianza`.

Solo dominios y su clase: ningún dato personal (el repositorio es público).
