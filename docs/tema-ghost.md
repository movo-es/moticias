# El tema de moticias.com (Ghost)

Respuesta corta: moticias.com usa un tema propio, `ghost-theme/`, con el aspecto del portal MOTICIAS y la marca v1 (`docs/marca.md`). La portada se compone en el servidor a partir de las piezas publicadas en Ghost y de una página oculta, `edicion-hoy`, que la rutina diaria reescribe con los boletines, los plazos y el documento del día. Las secciones viven en subdirectorios (`/tierra/`, `/mar/`…). Decisión del director, 7-11-2026; cambio OpenSpec `tema-ghost-v1`.

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Plantillas, estilos, JavaScript, iconos | `ghost-theme/` (`home.hbs` portada, `post.hbs` ficha, `seccion.hbs` y `seccion-analisis.hbs` secciones, `page.hbs`, `llms.hbs`) |
| Secciones en subdirectorios y `/llms.txt` | `ghost/routes.yaml` (se sube a mano: Ghost → Ajustes → Labs → Routes) |
| Redirecciones de las URL antiguas | `ghost/redirects.yaml`, generado por `src/ghost_redirects.py` (Ajustes → Labs → Redirects) |
| Menú, URL pública, secciones con su respuesta directa | `verticals/movilidad.json` → `ghost` |
| Marca (logos, favicon, colores, tipografías) | `verticals/movilidad/marca/`, `docs/marca.md` |
| Publicar piezas, página de la edición, secciones | `src/ghost_publish.py` |
| Subir el tema | `.github/workflows/tema-ghost.yml` (automático en `main`) o `src/ghost_theme_deploy.py` |
| Capturas de la vista previa | `docs/tema-ghost/` |

## Cómo llega cada bloque a la portada

| Bloque | Origen |
|---|---|
| Edición nº, fecha, «Actualizado HH:MM CET», cierre | página `edicion-hoy` (título, extracto, hora de actualización) |
| Respuesta directa de la portada | meta descripción de `edicion-hoy` |
| Apertura | la entrada destacada de Ghost |
| Segunda | etiqueta interna `#segunda` |
| Análisis del día | la última pieza con etiqueta Análisis |
| Cinco titulares y Lo esencial | últimas publicadas, por etiqueta principal |
| Reportajes | etiqueta interna `#reportaje` |
| Teletipo del BOE, documento del día, mapa, boletines, plazos, nota metodológica, FIN DE EDICIÓN | contenido de `edicion-hoy` |

## Comandos

Publicar la edición del día (lo hace la rutina, paso 7 quáter):

```bash
cd ~/moticias && python3 -I src/ghost_publish.py --date AAAA-MM-DD --status published --edition AAAA-MM-DD
```

Subir el tema sin activarlo, o activarlo:

```bash
cd ~/moticias && python3 -I src/ghost_theme_deploy.py --upload
```

```bash
cd ~/moticias && python3 -I src/ghost_theme_deploy.py --upload --activate
```

Los dos necesitan `GHOST_URL` y `GHOST_ADMIN_KEY` en el entorno; nunca en el repositorio.

## Lo que Ghost no deja hacer a la integración

Subir `routes.yaml`, subir redirecciones y cambiar el menú: devuelven 403 con la clave de API. Se hacen una vez a mano en el panel de Ghost.

## Probar sin tocar moticias.com

Una copia local de Ghost (`ghost install local`, con un usuario que no sea root) recibe el tema, las rutas y las piezas con los mismos comandos cambiando `GHOST_URL` y `GHOST_ADMIN_KEY`; las capturas se sacan con Playwright a 1366 y 390 px.
