# Delta: publicacion-ghost (tema-ghost-v1)

## MODIFIED Requisito: publicación por API
Cada pieza se publica como post de Ghost con la sección como etiqueta principal pública (Tierra, Mar, Aire, Logística, Regulación, Licitaciones, Análisis), en la URL `/<sección>/<slug>/` (análisis y reportajes, `/analisis/<slug>/`), con su foto subida a Ghost y pie de crédito y licencia, y su fecha original.

### Escenario: ficha completa
- DADO una pieza de `data/articles/`
- CUANDO se publica
- ENTONCES la ficha muestra arriba una respuesta directa de 40–60 palabras, el cuerpo, una columna con trazabilidad, cifras clave, cronología con las fechas por venir marcadas, firma y declaración de intereses, la guía rápida de cinco bloques y las fuentes con fecha de publicación y de consulta

## ADDED Requisito: tema propio
moticias.com usa el tema `ghost-theme/` (aspecto del portal MOTICIAS, marca v1), validado con gscan sin errores y desplegado por la Action `tema-ghost.yml`.

### Escenario: portada legible sin JavaScript
- DADO un buscador que no ejecuta JavaScript
- CUANDO lee https://www.moticias.com/
- ENTONCES encuentra la apertura, el análisis, la segunda, lo esencial por sección, el documento del día, los boletines, los plazos, la nota metodológica y el «FIN DE EDICIÓN»

## ADDED Requisito: página de la edición
La rutina diaria reescribe la página `edicion-hoy` (etiqueta `#edicion`) con boletines, plazos, documento del día, mapa y nota metodológica; la portada la lee en el servidor.

### Escenario: apertura crítica
- DADO que la apertura prevista del día es una pieza crítica en borrador
- ENTONCES Ghost destaca la mejor rutinaria del día y la portada nunca enlaza una pieza en borrador

## ADDED Requisito: secciones y llms.txt
Secciones en subdirectorios (`ghost/routes.yaml`), nunca `/tag/`; cada sección abre con su respuesta directa (descripción de la etiqueta); `/llms.txt` en texto plano.
