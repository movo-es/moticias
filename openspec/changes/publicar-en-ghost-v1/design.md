# Diseño: publicar-en-ghost-v1

**Estado y fuente de verdad.** `data/articles/<id>.json` manda; el post de Ghost es su proyección. La clave de unión es `slug == id`. Un campo `ghost` dentro del JSON de la pieza guarda `post_id`, `url`, `status`, `updated_at` y `html_hash` para no reenviar lo que no cambió (lo escribe la rutina y se versiona con la pieza).

**Estado al publicar.** Lo decide una función única, `estado_de_publicacion(pieza, vertical)` en `src/ghost_publish.py`, leyendo `verticals/movilidad.json → editorial` (reglas de firma y aprobación): `published` para las rutinarias; `draft` para las de firma del director, las críticas para la reputación o con implicaciones legales, y las que tienen `status: pendiente`. La bandera `--status` deja de existir salvo `--forzar-borrador` para emergencias.

**Reconciliación.** `--reconciliar` lista los posts de Ghost (`GET /posts/?limit=all&fields=id,slug,status,updated_at`), compara con `data/articles/` y: crea los que faltan con su `published_at` original, actualiza los que cambiaron (`html_hash` distinto), no borra nunca (una pieza retirada se pasa a `draft` y se anota), y escribe un informe `work/ghost-reconciliacion-<fecha>.md` que la rutina resume en el aviso.

**Tema.** `ghost/theme/` con `package.json`, `*.hbs`, `assets/` y `partials/`. `src/ghost_theme.py descargar` (Admin API) y `src/ghost_theme.py subir` (zip + `POST /themes/upload/` + `PUT /themes/<name>/activate/`). El tema no se toca en el panel: la comprobación semanal del asesor compara el `package.json` del tema activo con el del repositorio.

**Páginas.** `--paginas` convierte `docs/legal/*.md` (y `docs/legal/como-trabajamos.md`) en páginas de Ghost con slug fijo, fecha de versión al pie y `noindex` solo en cookies. La misma función sirve para páginas pilar futuras.

**Alta de suscriptores.** Portal de Ghost activado para el nivel gratuito; los tres consentimientos como newsletters/etiquetas de miembro («Boletines de MOTICIAS» obligatoria; «Comunicados del sector» y «Ofertas del grupo» opcionales); el texto legal del Portal enlaza a `/privacidad/`. La lectura de esos consentimientos hacia `contacts` es de `suscripciones-v1`.

**llms.txt y robots.** Ghost 6 los genera (`/llms.txt`, `/llms-full.txt`, `/<slug>.md`). Se gobiernan desde la descripción del sitio, la descripción de cada etiqueta de sección y el `custom_excerpt` de cada pieza (que ya escribe la rutina). `ghost/llms.txt` del repositorio es el texto de referencia que se pega en esas descripciones.

**Secretos.** `GHOST_URL`, `GHOST_ADMIN_KEY` en la tarea programada y en Vercel. El script falla con mensaje claro si faltan.
