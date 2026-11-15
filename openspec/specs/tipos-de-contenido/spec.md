# Tipos de contenido

Spec viva desde el 15-11-2026 (cambio `tipos-de-contenido`, aprobado por Rainer ese día; archivo en
`openspec/changes/archive/2026-11-15-tipos-de-contenido/`). Código: `src/tipos.py`; textos: `verticals/movilidad.json → tipos_de_contenido`.

## Requisitos

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
- La marca de un análisis es siempre «Análisis», con el autor que lo firme a la vista (cambio `terminologia-editor`, 15-11-2026: desaparece «Análisis del director» como marca, módulo y botón). Los reportajes llevan «Reportaje».
- No hay módulo ni botón propios de los análisis del editor jefe; la etiqueta interna `#analisis-director` se conserva solo como dato.

#### Escenario: análisis de la redacción
- DADO un análisis firmado «G. Jordan»
- CUANDO se publica en Ghost y aparece en un listado
- ENTONCES su marca es «Análisis» y no aparece en el módulo «Análisis»

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
- Marcas: «Contenido patrocinado» cuando el servicio es de una empresa del grupo (sin decirlo; ver modificación del 15-11-2026, noche); «Contenido patrocinado · <cliente>» cuando lo paga un cliente; «Publicidad» en las cajas por niveles de anunciantes.
- Los tipos de anuncio de `data/ads/` son `grupo`, `patrocinio` y `publicidad`.
- La etiqueta es siempre visible y todos los enlaces de la caja llevan `rel="sponsored"`.
- Nunca dentro de un análisis ni en piezas que traten del grupo.
- Lo que anuncia servicios del grupo no se describe con ningún otro término, ni en textos, ni en etiquetas, ni en datos, ni en código.

- **Modificado el 15-11-2026 (noche, decisión de Rainer):** en las cajas de publicidad por niveles, lo del grupo se etiqueta solo «Contenido patrocinado», sin mencionar que la empresa es del grupo; la marca va dentro de la caja. **Ampliado el mismo día:** las cajas dentro del texto también dicen solo «Contenido patrocinado» y ya no llevan la línea «… es un servicio de una empresa del grupo»; la relación sigue declarada en los datos estructurados y en `/empresas-del-grupo/`. Toda caja que enlaza a una empresa del grupo es `type: grupo`, la cree quien la cree.

#### Escenario: caja del grupo en un hueco de nivel premium
- DADO un anuncio con `type: grupo` activo en el hueco `cabecera`
- CUANDO `m.js` lo pinta en moticias.com
- ENTONCES la etiqueta dice «Contenido patrocinado» (sin «del grupo») y el enlace lleva `rel="sponsored noopener"`

#### Escenario: seguimiento tras el cambio de identificador
- DADA una caja cuyo identificador pasó de `casa-…` a `grupo-…`
- CUANDO el editor jefe abre su seguimiento a 30 días
- ENTONCES ve las visualizaciones y los clics anteriores y posteriores al cambio en una sola serie

### Ghost
- Cada post lleva una etiqueta interna por tipo: `#tipo-editorial`, `#tipo-noticia`, `#tipo-nota-de-prensa` o `#tipo-patrocinado`. Las notas conservan además `#comunicado`.
- La marca visible va en el cuerpo del post y en los listados, sin depender del tema.

### Buscador
- Cada entrada de `app/public/buscador/index.json` lleva el tipo (`tc`), y el resultado enseña su marca.

### Límites conocidos (15-11-2026)
- El tema de Ghost no está versionado: la marca de la pieza va en su cuerpo (`src/ghost_publish.py`) y la de los listados la pone `app/public/sitio/m.js` con `app.moticias.com/buscador/tipos.json`; `m.js` corrige también la etiqueta y el `rel` de las cajas del grupo que pinta el tema. Al versionar el tema (`publicar-en-ghost-v1`) todo eso pasa al tema, y se confirma allí que `home.hbs` excluye `#comunicado`.
- No hay boletín diario: Ghost nunca ha enviado una pieza por correo. Cuando se active, solo `editorial` y `noticia`.
- El portal antiguo (`portal/`, espejo hasta el 8-12-2026) acepta también el tipo que aún guarda la base de su artefacto.
