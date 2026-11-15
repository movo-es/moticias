# Tipos de contenido

## ADDED Requisitos

### Campo único
- Toda pieza de `data/articles/`, toda nota de `data/notas-de-prensa/` y todo anuncio de `data/ads/` lleva `tipo_contenido` con uno de estos valores: `editorial`, `noticia`, `nota_de_prensa`, `patrocinado`.
- `src/tipos.py` es el único sitio que deduce, valida y traduce el tipo a marca visible, etiqueta interna de Ghost y atributo `rel`. Los textos de las marcas viven en `verticals/<id>.json → tipos_de_contenido`.
- Un documento sin `tipo_contenido`, o con uno que contradice sus otros campos, no se publica.

#### Escenario: pieza nueva de la rutina
- DADA una pieza con `kind: noticia` escrita por la edición diaria
- CUANDO se guarda en `data/articles/`
- ENTONCES lleva `tipo_contenido: noticia` y `src/tipos.py validar` no da errores

#### Escenario: contradicción
- DADA una pieza con `kind: analisis` y `sponsored_by` relleno
- CUANDO corre `src/tipos.py validar`
- ENTONCES falla con el motivo «un análisis no puede ser contenido patrocinado» y la pieza no se sube a Ghost

### Contenido editorial
- Es `editorial` toda pieza con `kind` `analisis` o `reportaje`, con firma.
- La marca es «Análisis del director» solo si `author` es la firma del director (`editorial.director`); con cualquier otra firma es «Análisis». Los reportajes llevan «Reportaje».
- El módulo de portada y el botón «Análisis del director» muestran únicamente análisis firmados por el director.

#### Escenario: análisis de la redacción
- DADO un análisis firmado «G. Jordan»
- CUANDO se publica en Ghost y aparece en un listado
- ENTONCES su marca es «Análisis» y no aparece en el módulo «Análisis del director»

### Noticias
- Es `noticia` toda pieza con `kind: noticia` sin `sponsored_by`. Marca: «Noticia».

### Notas de prensa
- Es `nota_de_prensa` todo comunicado de un emisor externo. Marca: «Nota de prensa · Comunicado de <emisor>».
- Nunca entra en la portada editorial ni en el boletín diario, y nunca se presenta como noticia sin verificación independiente.

#### Escenario: portada
- DADA una nota de prensa publicada hoy
- CUANDO `src/ghost_edicion.py` reconstruye la portada
- ENTONCES la nota no aparece en ella

### Contenido patrocinado
- Es `patrocinado` todo lo que anuncia un servicio: las cajas dentro del texto, las cajas por niveles y las piezas con `sponsored_by`.
- Marcas: «Contenido patrocinado · servicio del grupo» cuando el servicio es de una empresa del grupo; «Contenido patrocinado · <cliente>» cuando lo paga un cliente; «Publicidad» en las cajas por niveles de anunciantes.
- Los tipos de anuncio de `data/ads/` son `grupo`, `patrocinio` y `publicidad`.
- La etiqueta es siempre visible y todos los enlaces de la caja llevan `rel="sponsored"`.
- Nunca dentro de un análisis ni en piezas que traten del grupo.
- Lo que anuncia servicios del grupo no se describe con ningún otro término, ni en textos, ni en etiquetas, ni en datos, ni en código.

#### Escenario: caja del grupo en un hueco de nivel premium
- DADO un anuncio con `type: grupo` activo en el hueco `cabecera`
- CUANDO `m.js` lo pinta en moticias.com
- ENTONCES la etiqueta dice «Contenido patrocinado · servicio del grupo» y el enlace lleva `rel="sponsored noopener"`

#### Escenario: seguimiento tras el cambio de identificador
- DADA una caja cuyo identificador pasó de `casa-…` a `grupo-…`
- CUANDO el editor jefe abre su seguimiento a 30 días
- ENTONCES ve las visualizaciones y los clics anteriores y posteriores al cambio en una sola serie

### Ghost
- Cada post lleva una etiqueta interna por tipo: `#tipo-editorial`, `#tipo-noticia`, `#tipo-nota-de-prensa` o `#tipo-patrocinado`. Las notas conservan además `#comunicado`.
- La marca visible va en el cuerpo del post y en los listados, sin depender del tema.

### Buscador
- Cada entrada de `app/public/buscador/index.json` lleva el tipo (`tc`), y el resultado enseña su marca.
