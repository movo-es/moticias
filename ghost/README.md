# Ficheros para la raíz de moticias.com (Ghost)

- `llms.txt`: para GPTBot, ClaudeBot, Google-Extended y similares. En Ghost(Pro) no se pueden subir ficheros a la raíz: se publica como **ruta** en `routes.yaml` (Settings → Labs → Routes) apuntando a una página estática, o se sirve desde la aplicación en Vercel con una redirección `/llms.txt` → `app.moticias.com/llms.txt` en `redirects.yaml`. Decidir en la entrevista 1 (`publicar-en-ghost-v1`).
- `robots.txt`: Ghost genera el suyo; para sustituirlo se usa la misma técnica (ruta o redirección). Mantener alineado con `llms.txt`.
- Páginas legales: `docs/legal/*.md` → páginas de Ghost en `/aviso-legal/`, `/privacidad/`, `/cookies/`, `/como-trabajamos/`.
