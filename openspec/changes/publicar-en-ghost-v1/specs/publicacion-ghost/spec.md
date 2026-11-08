# Capacidad: publicación en moticias.com (Ghost) (delta)

## MODIFIED Requisito: estado «pendiente» → activo
Desde el 8-11-2026 moticias.com se sirve desde Ghost(Pro) en `https://www.moticias.com/` (canónico, con `www`); el dominio sin `www` redirige. Las piezas, páginas y el tema se publican desde el repositorio por la Admin API; el panel de Ghost no es un sitio donde editar.

## ADDED Requisito: una pieza, un post, por su slug
Cada pieza de `data/articles/<id>.json` con `status` distinto de `borrador` se proyecta en un post de Ghost cuyo `slug` es el `id`. El JSON guarda en `ghost` el `post_id`, la `url`, el `status`, `updated_at` y `html_hash`. Un post no se reenvía si su `html_hash` no cambió.

#### Escenario: pieza corregida
- CUANDO una pieza publicada cambia su `body_md` y añade `revised_at`
- ENTONCES la siguiente publicación actualiza el post (no crea otro), conserva `published_at` original y el HTML muestra la nota de corrección al final.

## ADDED Requisito: el estado lo dicta la regla editorial
`estado_de_publicacion(pieza, vertical)` devuelve `published` para las piezas rutinarias (firma «G. Jordan, Redactor responsable») y `draft` para las de firma del director, las críticas para la reputación o con implicaciones legales y las marcadas `status: pendiente`, según `verticals/<vertical>.json → editorial`. Ninguna bandera global cambia esto; Rainer publica los borradores desde la app de Ghost.

#### Escenario: análisis del día
- CUANDO la rutina cierra la edición con un `kind: analisis` firmado por el director
- ENTONCES el post entra en Ghost como `draft` y el aviso de cierre dice «1 en borrador».

## ADDED Requisito: reconciliación sin borrados
`--reconciliar` compara el repositorio con Ghost: crea lo que falta con su fecha original, actualiza lo cambiado, pasa a `draft` lo retirado y nunca borra. Deja un informe en `work/`.

## ADDED Requisito: tema versionado
El tema activo vive en `ghost/theme/`; se descarga y se sube con `src/ghost_theme.py`. Un tema editado en el panel y no en el repositorio es una desviación que el asesor semanal señala.

## ADDED Requisito: páginas desde documentos
Las páginas legales y «Cómo trabajamos» se publican desde `docs/legal/*.md` con slug fijo y fecha de versión al pie, y se enlazan en el pie del tema. La misma vía sirve para páginas pilar.

## ADDED Requisito: alta gratuita con consentimientos separados
El Portal de Ghost ofrece el alta gratuita con tres casillas: boletines de MOTICIAS (obligatoria), comunicados del sector (opcional) y ofertas de las empresas del grupo (opcional), con enlace a `/privacidad/`. Sin la casilla correspondiente no se envía nada de ese tipo.

## ADDED Requisito: legibilidad por máquinas
`llms.txt`, `llms-full.txt`, `robots.txt`, `sitemap.xml`, RSS y la versión `.md` de cada pieza los genera Ghost; el repositorio gobierna su contenido a través de la descripción del sitio, de las etiquetas de sección y del `custom_excerpt` de cada pieza. Cada pieza lleva Schema.org `NewsArticle` y la trazabilidad (fechas de hechos, documento oficial, consulta y redacción) visible.

## ADDED Requisito: secretos
`GHOST_URL` y `GHOST_ADMIN_KEY` solo como variables de entorno de la tarea programada y de Vercel. Sin ellos, el publicador se detiene con un mensaje claro y no publica nada.
