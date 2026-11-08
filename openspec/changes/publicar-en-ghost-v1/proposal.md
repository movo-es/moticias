# Cambio: publicar-en-ghost-v1 — moticias.com en Ghost(Pro), versionado y publicando solo

Estado: propuesto tras la entrevista 1 (8-11-2026, con Rainer). Spec base: `openspec/specs/publicacion-ghost/spec.md`; código: `src/ghost_publish.py`.

## Lo que la entrevista encontró

www.moticias.com **ya está publicado** en Ghost(Pro) 6.75 con un tema propio (`assets/css/moticias.css`, `assets/js/moticias.js`), 62 de las 74 piezas del repositorio, páginas de sección (`/tierra/`, `/mar/`, `/aire/`, `/regulacion/`, `/licitaciones/`, `/analisis/`, `/logistica/`), el dominio sin `www` redirigiendo al canónico, y `llms.txt`, `llms-full.txt`, `robots.txt` y la versión `.md` de cada pieza **generados por el propio Ghost 6**. Nada de eso está en el repositorio, y Rainer no recuerda en qué sesión se hizo. Las 12 piezas que faltan son exactamente las que la política editorial reserva a su firma o su aprobación: tres análisis, tres reportajes y seis noticias sobre Urda, Puente y Adif.

## Decisiones de la entrevista

1. Dirección canónica `https://www.moticias.com/`; `moticias.com` redirige (ya lo hace).
2. El tema propio que se ve hoy **vale como base y se pule**: trazabilidad visible, huecos señalizados, páginas legales, medida a 390 px. No se rehace.
3. La Admin API key existe; va como variable de entorno `GHOST_ADMIN_KEY` (y `GHOST_URL=https://www.moticias.com`) de la tarea programada y de Vercel, nunca en el repositorio ni en el chat.
4. Legales: se publican ya los borradores de `docs/legal/` con los datos de Avionline S.L. tomados de `movo-es/movo` (`lib/legal.js`); revisión profesional después, no antes. Buzones por crear en Hostinger: `redaccion@moticias.com` y `prensa@moticias.com` (o alias de `ruphoff@avionline.es`).
5. Las 12 piezas pendientes se reconcilian con sus fechas originales: las rutinarias publicadas (firma «G. Jordan, Redactor responsable»); las de firma del director o críticas, en borrador para que Rainer las publique desde el móvil.
6. El portal-artefacto queda de espejo un mes (hasta el 8-12-2026) y después solo la hemeroteca.
7. `ghost/llms.txt` y `ghost/robots.txt` del repositorio pasan a ser **texto de referencia**: Ghost 6 los genera; lo que se ajusta es la descripción del sitio y de las secciones en Ghost (Settings → General y la descripción de cada etiqueta), que es lo que `llms.txt` lee.

## Qué cambia

- **El tema entra en el repositorio** (`ghost/theme/`): Code lo descarga por la Admin API (`GET /ghost/api/admin/themes/`, y la descarga del activo) o Rainer lo baja desde Settings → Design → Change theme; desde entonces, el tema se edita en el repositorio y se sube con `src/ghost_theme.py` (empaquetar y `POST /ghost/api/admin/themes/upload/`). Regla: no se toca el tema en el panel de Ghost.
- **`src/ghost_publish.py`** gana: reconciliación (`--reconciliar`: compara `data/articles/` con los posts de Ghost por `slug` y publica o deja en borrador según `verticals/movilidad.json → editorial`), estado por regla (no por bandera global), páginas (`--paginas`: las cuatro legales y «Cómo trabajamos» desde `docs/legal/`), y la comprobación posterior (lee la URL publicada y compara título y fecha).
- **La rutina diaria** incorpora el paso 7 quater: al cerrar la edición, `ghost_publish.py --date <hoy>` con el estado que dicta la regla editorial, y el aviso dice cuántas quedaron en borrador.
- **Páginas legales** publicadas en `/aviso-legal/`, `/privacidad/`, `/cookies/` y `/como-trabajamos/`, enlazadas en el pie del tema; el Portal de Ghost (alta de suscriptores) enseña los tres consentimientos de `docs/legal/consentimientos.md` (el primero obligatorio; los otros dos como etiquetas de newsletter/segmento hasta `suscripciones-v1`).
- **Search Console y Google News Publisher Center**: alta con la cuenta de Google de Rainer, verificación por registro DNS en Hostinger (instrucciones en `tasks.md`).
- **Documentación**: `openspec/specs/publicacion-ghost/spec.md` pasa de «pendiente» a los requisitos de abajo; `docs/manual-operativo.md` y `docs/tarea-edicion-diaria.md` añaden el paso 7 quater; `docs/arquitectura.md` añade `ghost/theme/`.

## Fuera de alcance

Suscripciones de pago y niveles (`suscripciones-v1`), sala de prensa (`notas-de-prensa-v1`), tema nuevo desde cero, boletín diario por correo desde Ghost (se decide en `suscripciones-v1`).

## Riesgos

El tema se ha editado fuera del repositorio: hasta que esté versionado, cualquier cambio en el panel se pierde en la siguiente subida. Las 12 piezas en borrador contienen el análisis del día de tres ediciones: mientras Rainer no las publique, la portada de Ghost no tiene análisis. La Admin API key da control total del sitio: solo en variables de entorno.

## Qué verás tú

- `https://www.moticias.com/` con las 74 piezas (las 12 pendientes aparecen al pulsar «Publicar» en la app de Ghost en tu móvil: Posts → Drafts).
- `/aviso-legal/`, `/privacidad/`, `/cookies/` y `/como-trabajamos/` con los datos de Avionline, enlazados en el pie.
- Al suscribirte de prueba, las tres casillas de consentimiento.
- En el repositorio, `ghost/theme/` con el tema, y en la línea de `docs/ediciones.md` de cada mañana: «publicadas N en Ghost, M en borrador».
