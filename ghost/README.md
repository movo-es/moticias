# Ficheros de referencia para moticias.com (Ghost)

Comprobado el 8-11-2026: Ghost 6 genera por sí mismo `https://www.moticias.com/llms.txt`, `/llms-full.txt`, `/robots.txt`, `/sitemap.xml`, `/rss/` y la versión `.md` de cada pieza (`/<slug>.md`). No hay que subir ficheros a la raíz.

- `llms.txt`: **texto de referencia**. Lo que Ghost publica en `llms.txt` sale de la descripción del sitio (Settings → General), de la descripción de cada etiqueta de sección y del `custom_excerpt` de cada pieza. El cambio `publicar-en-ghost-v1` copia estas descripciones en Ghost; si cambian, se cambian aquí primero.
- `robots.txt`: referencia de lo que Ghost ya hace (bloquea `/ghost/`, `/email/`, `/r/`…). Los rastreadores de IA están permitidos por defecto; si algún día hay que limitarlos, el tema puede llevar su propio `robots.txt`.
- `theme/` (desde `publicar-en-ghost-v1`): el tema propio de moticias.com, descargado de Ghost con `src/ghost_theme.py descargar` y subido con `src/ghost_theme.py subir`. **No se edita en el panel de Ghost.**
- Páginas legales: `docs/legal/*.md` → páginas de Ghost `/aviso-legal/`, `/privacidad/`, `/cookies/`, `/como-trabajamos/` (`src/ghost_publish.py --paginas`).
