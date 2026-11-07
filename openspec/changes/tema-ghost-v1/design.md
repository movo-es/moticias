# Diseño: tema-ghost-v1

## Principios

1. **Servidor primero.** Toda la portada se compone en el servidor con `{{#get}}`: apertura (`featured:true`), análisis (`tag:analisis`), segunda (`tag:hash-segunda`), cinco titulares, «Lo esencial» por sección (`primary_tag:<sección>`), reportajes (`tag:hash-reportaje`) y la página `edicion-hoy`. El JavaScript (`assets/js/moticias.js`) solo mejora: sube el teletipo bajo la cabecera, dibuja el mapa con `spain.js`, calcula «hoy / mañana / en N días» y recalcula la cronología «por venir».
2. **El repositorio manda.** Ghost recibe HTML generado desde `data/` por `src/ghost_publish.py`; editar una pieza en el panel de Ghost es una corrección de urgencia que la siguiente publicación sobrescribe (se corrige en `data/` y se republica).
3. **La ficha va en una tarjeta HTML.** Ghost convierte el HTML entrante a su formato y borra clases y atributos; envuelto entre `<!--kg-card-begin: html-->` y `<!--kg-card-end: html-->` se conserva tal cual. Comprobado en producción el 7-11-2026.

## Ficha de pieza (post.hbs + HTML del publicador)

`.m-art` es una rejilla con áreas: `answer` (respuesta directa, 40–60 palabras), `body` (cuerpo), `aside` (trazabilidad, dato clave, cifras clave con fuente, cronología con `data-date` y futuros marcados en Señal, firma y declaración de intereses), `quick` (guía rápida de cinco bloques), `sources` (oficiales y medios con fecha de publicación y de consulta) y `fin`. En móvil la columna lateral baja tras el cuerpo. La foto destacada se sube a Ghost desde `portal/img/` y su pie lleva crédito, licencia y enlace al original. Cabecera de la ficha: sección y subsector, título, subtítulo (extracto de Ghost), firma enlazada a `/firma/<slug>/`, fecha y hora CET, tiempo de lectura.

## Portada de edición (home.hbs)

Franja: título de la edición y «Actualizado HH:MM CET» (`updated_at` de `edicion-hoy`). Cabecera con el logotipo horizontal (compacto bajo 560 px). Teletipo del BOE. Línea de edición con cierre y respuesta directa (meta descripción de `edicion-hoy`). Portada 7/5: apertura a sangre con foto, análisis firmado, segunda y cinco titulares. «Lo esencial» en cinco columnas (Tierra, Mar, Aire, Regulación, Licitaciones). Autopromoción (hueco «portada-medio»). Reportajes. Página de la edición: documento del día, mapa de la semana, boletines oficiales, próximos plazos, nota metodológica y «FIN DE EDICIÓN · fecha, hora CET». Autopromoción («portada-pie»). Cómo trabajamos. Pie con suscripción.

## Página `edicion-hoy`

La genera `ghost_publish.py --edition AAAA-MM-DD` a partir de `data/editions/<fecha>.json`, `data/boletines/` (los de la edición), `data/agenda/` (ocho próximos) y `data/articles/` (publicadas con lugar de los últimos siete días). Título «Edición nº N · día»; extracto «Cierre HH:MM CET»; meta descripción = respuesta directa de la edición; `canonical_url` = portada. Solo enlaza piezas publicadas: nunca una crítica en borrador.

## Secciones (routes.yaml)

Colecciones en orden: `/analisis/` (análisis y reportajes; plantilla `seccion-analisis`, sin `data` para no dar 404 vacía), `/tierra/`, `/mar/`, `/aire/`, `/logistica/`, `/regulacion/`, `/licitaciones/` (plantilla `seccion` con `data: tag.<sección>`, que aporta nombre y respuesta directa) y `/` (resto). Etiquetas en `/tema/`, autores en `/firma/`. `/llms.txt` como ruta de texto.

## SEO y GEO

`{{ghost_head}}` da canonical, Open Graph, `Article` y el `sitemap.xml`. El publicador añade por pieza `NewsArticle` (con `citation` de las fuentes y `publisher` NewsMediaOrganization) y `FAQPage` con la guía rápida. La portada añade `NewsMediaOrganization` con titular (Avionline S.L., CIF, domicilio), principios de publicación y correcciones (→ Cómo trabajamos) y `sameAs` con los perfiles que se configuren en Ghost (Ajustes → General → Social accounts). Respuesta directa de 40–60 palabras arriba en portada, secciones (descripción de la etiqueta, desde `verticals/movilidad.json`) y piezas.

## Publicidad

Solo los huecos de `docs/gestores-portal.md` implementados en v1: portada-medio, portada-pie y artículo (cierre), con autopromoción del grupo (`data/ads/`), etiqueta visible «Autopromoción · …» y UTM. Nunca sobre la apertura ni dentro del texto. El anuncio de MOVO licitaciones enlaza a movo.es (no al correo personal que figura en `data/ads/`).

## Despliegue

`.github/workflows/tema-ghost.yml`: en cada push a `main` que toque `ghost-theme/`, gscan y `TryGhost/action-deploy-theme@v1` (sube y activa) con los secretos `GHOST_URL` y `GHOST_ADMIN_KEY`. A mano o sin GitHub: `python3 -I src/ghost_theme_deploy.py --upload [--activate]`.
