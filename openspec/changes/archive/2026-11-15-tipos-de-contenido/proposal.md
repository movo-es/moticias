# Cambio: tipos-de-contenido

Fecha: 14 de noviembre de 2026. Origen: encargo de Rainer del mismo día («lo que falta», cambio A de ocho). Estado: **aprobada por Rainer el 15-11-2026**; pendiente de aplicar.

Respuesta corta: cada documento que MOTICIAS publica lleva un campo `tipo_contenido` con uno de cuatro valores —`editorial`, `noticia`, `nota_de_prensa`, `patrocinado`— y ese campo decide, en un solo sitio, la marca que ve el lector, la etiqueta interna de Ghost, lo que entra en la portada, en el buscador y en el boletín, y el atributo `rel="sponsored"` de los enlaces. Hoy el tipo se deduce en cada script por su cuenta, y por eso hay ambigüedades.

## Por qué (lo comprobado en el código el 14-11-2026)

- No existe `tipo_contenido` en ninguna parte. Las 95 piezas llevan `kind` (83 noticia, 8 análisis, 4 reportaje); las notas se distinguen por su carpeta y los anuncios por `type`.
- El tema «Análisis» de la taxonomía se llama «Análisis del director», pero 3 de los 8 análisis los firma G. Jordan: el lector ve el nombre del director sobre piezas que no son suyas.
- Los reportajes no tienen marca propia.
- Las cajas por niveles que pinta `app/public/sitio/m.js` enlazan sin `rel="sponsored"` cuando el servicio es del grupo (las cajas dentro del texto sí lo llevan).
- En `data/ads/` cuatro cajas de servicios del grupo usan un tipo, un prefijo de identificador y, en un caso, una etiqueta visible que la regla de Rainer prohíbe. El mismo término sigue en `m.js`, `api/gestor.py`, `verticals/movilidad.json`, el gestor y varios documentos.
- `sponsored_by` existe como campo, pero ninguna pieza lo usa y `ghost_publish.py` no lo lee (lo desarrolla el cambio F; aquí solo queda definido su tipo).

## Qué cambia

1. **El campo.** `tipo_contenido` en `data/articles/` (piezas), `data/notas-de-prensa/` (notas) y `data/ads/` (anuncios). Un módulo nuevo, `src/tipos.py`, es el único que sabe deducirlo, validarlo y traducirlo a marca visible, etiqueta de Ghost y `rel`:

   | `tipo_contenido` | Qué es | Marca que ve el lector | Etiqueta interna de Ghost |
   |---|---|---|---|
   | `editorial` | Análisis y reportajes con firma | «Análisis del director» si firma el director; «Análisis» si firma otro; «Reportaje» | `#tipo-editorial` |
   | `noticia` | Noticias | «Noticia» | `#tipo-noticia` |
   | `nota_de_prensa` | Comunicado de un emisor externo | «Nota de prensa · Comunicado de <emisor>» | `#tipo-nota-de-prensa` (además de `#comunicado`, que ya existe) |
   | `patrocinado` | Lo que anuncia un servicio | «Contenido patrocinado · servicio del grupo», «Contenido patrocinado · <cliente>» o «Publicidad» (cajas por niveles) | `#tipo-patrocinado` |

   `src/tipos.py migrar` rellena el campo en lo ya publicado (95 piezas, 5 anuncios) sin tocar texto, firma ni fechas; `validar` falla si falta o no cuadra (un análisis con `sponsored_by`, una nota en portada…).

2. **Análisis.** El tema de la taxonomía pasa a llamarse «Análisis». «Análisis del director» queda como marca solo cuando `author` es la firma del director (`editorial.director`); el módulo fijo de portada y el botón del menú filtran por esa firma, no por el tema.

3. **Reportajes.** Marca propia «Reportaje» en la pieza, los listados, el buscador y Ghost.

4. **Servicios del grupo.** En `data/ads/` el tipo pasa a llamarse `grupo`; los cuatro ficheros se renombran de `casa-…` a `grupo-…` (con `git mv`, se conserva el historial) y su etiqueta visible pasa a «Contenido patrocinado · servicio del grupo». Tipos de anuncio desde ahora: `grupo`, `patrocinio` (lo paga un cliente: «Contenido patrocinado · <cliente>») y `publicidad` («Publicidad»). El código que hoy compara con el nombre antiguo (`m.js`, `api/gestor.py`, `src/seguimiento.py`, el gestor, `verticals/movilidad.json → publicidad.tipos`) compara con `grupo`. Las cajas dentro del texto (menciones) cambian su etiqueta a «Contenido patrocinado · servicio del grupo».

5. **`rel="sponsored"`** en todos los enlaces de todas las cajas, del grupo y de clientes, sin excepción (`m.js`, `src/menciones.py`).

6. **Seguimiento sin perder historia.** Migración `009_tipos_de_contenido.sql`: traslada en `pub_diario` y `pub_comprobaciones` las filas de los cuatro identificadores antiguos a los nuevos y amplía la lista de tipos admitidos. No borra nada.

7. **Quién lee el campo.** `ghost_publish.py` (etiqueta interna y marca en el cuerpo), `ghost_edicion.py` (la portada solo admite `editorial` y `noticia`), `export_search_index.py` (campo `tc`; las notas entran en el buscador con su marca, lo completa el cambio D), `m.js` (marca y `rel`), `prensa_publicar.py` (escribe `nota_de_prensa`) y el boletín.

8. **Documentación y comandos.** `CLAUDE.md`, `docs/manual-operativo.md`, `docs/gestores-portal.md`, `docs/arquitectura.md`, `docs/tarea-edicion-diaria.md` y los comandos `/edicion-diaria`, `/noticias-gestor`, `/pieza-bajo-demanda` y `/prensa-buzon` (toda pieza nueva nace con su `tipo_contenido`).

## Qué no cambia

El texto de ninguna pieza, la firma, el cupo del director, la aprobación, los tres ejes, `kind`/`section` (se conservan), las tarifas, ni el circuito de publicación: las tareas siguen dejando contenido en el buzón y `ghost_al_dia` lo lleva a la web. Nada se borra.

## Límites conocidos

- **El tema de Ghost no está en el repositorio** (`ghost/theme/` no existe; sigue pendiente de `publicar-en-ghost-v1`). La marca visible se pinta por dos vías que no dependen de él: dentro del cuerpo del post (`ghost_publish.py`) y con `m.js` en los listados. Cuando el tema se versione, pasa al tema.
- **El boletín.** No hay en el repositorio código que envíe el boletín diario: lo manda Ghost con sus propios ajustes o no sale. La tarea 1 de `tasks.md` lo comprueba antes de prometer nada sobre él.
- El portal antiguo (`portal/`, espejo hasta el 8-12-2026) usa el nombre antiguo en su código. Decisión 2.

## Decisiones de Rainer (15-11-2026)

1. **Cajas de servicios de la propia MOTICIAS** («Anúnciate», «Ediciones a medida»): **sí**, llevan también «Contenido patrocinado · servicio del grupo». Una sola etiqueta para todo lo que es del grupo.
2. **Portal antiguo** (`portal/`, el artefacto de Claude que fue la primera web de MOTICIAS; espejo hasta el 8-12-2026): se aplica la propuesta —solo lo que ve el lector (etiquetas y datos) y que su código acepte el tipo nuevo— salvo que Rainer diga otra cosa. No se reescribe su código por dentro.
3. **Documentos históricos**: **sí**. El término antiguo se sustituye en los documentos vivos (`CLAUDE.md`, manuales, estrategia); las propuestas de cambios anteriores llevan una nota al principio que remite a este cambio, sin reescribir lo que se decidió entonces.
