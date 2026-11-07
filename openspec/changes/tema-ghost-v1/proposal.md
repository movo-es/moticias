# Cambio: tema-ghost-v1 — moticias.com con el aspecto del portal MOTICIAS

Estado: aplicado en local y validado (7-11-2026); pendiente del visto bueno del director para activarlo en moticias.com.

## Por qué

Decisión del director (7-11-2026): moticias.com no se queda con el tema de serie de Ghost (Source). El sitio público debe tener el aspecto del prototipo del portal (el artefacto «MOTICIAS»): muy visual, con su tipografía, colores, cabecera, portada de edición y ficha de pieza, y con la marca v1 (`docs/marca.md`: la Glorieta, azul 286, Plus Jakarta Sans). **Esto cambia la recomendación de la Entrevista 1** de `docs/paso-a-code.md` («tema de serie con inyección de bloques hasta la fase 4»): el tema propio entra ya, en la fase 1.

## Entrevista (/opsx:explore): lo que faltaba por decidir

1. **Plan de Ghost(Pro).** Comprobado por la Admin API: **Publisher** (3 usuarios, 1.000 miembros, 3 boletines, integraciones personalizadas). Admite temas propios. No hizo falta preguntar.
2. **Claves.** La integración personalizada ya existe y sus datos están como variables de entorno de la sesión (`GHOST_URL`, `GHOST_ADMIN_KEY`); no están en el repositorio. Falta copiarlos como **secretos del repositorio en GitHub** para la Action (lo hace Rainer: ver «Qué tienes que hacer tú»).
3. **Repositorio público.** Decisión de Rainer: se cierra (privado). Lo cambia él en GitHub → Settings → General → Danger Zone → Change visibility.
4. **Boletines, plazos y documento del día en la portada.** Se adopta la preferencia del director: una **página de Ghost `edicion-hoy`** con la etiqueta interna `#edicion`, que la rutina diaria reescribe y que `home.hbs` lee con `{{#get "pages"}}` en el servidor. Se descartó guardarlo en «ajustes del tema» (límite de 20 campos cortos, sin listas) y en JavaScript contra un JSON externo (Google y los motores generativos no lo leerían). La página tiene `canonical` a la portada para no competir con ella.
5. **Apertura y segunda.** La apertura es la entrada destacada (`featured`) de Ghost; la segunda lleva la etiqueta interna `#segunda`. Si la apertura prevista es una pieza crítica que espera al director (pasó el 6-11: Ouigo-Semaf), sube la segunda y la siguiente rutinaria del día pasa a segunda; cuando Rainer la apruebe, puede destacarla él en Ghost.
6. **Rutas.** Integraciones no pueden subir `routes.yaml`, redirecciones ni menú (Ghost responde 403): se suben a mano una vez (Ajustes → Labs y Ajustes → Navegación). El tema sí se sube por API y por la Action.
7. **llms.txt.** Ghost(Pro) no sirve ficheros en la raíz, pero `routes.yaml` admite una ruta `/llms.txt` con plantilla de texto (`content_type: text/plain`): probado, responde 200 en `text/plain` con las secciones y las 30 últimas piezas.
8. **Análisis vacío.** Una colección con `data: tag.x` sin piezas publicadas da 404 en Ghost. Hoy los seis textos del director están en borrador, así que `/analisis/` usa una plantilla propia que no depende de eso.

## Qué cambia

- `ghost-theme/` — tema propio validado con gscan sin errores ni avisos («compatible con Ghost 6.x»): portada de edición, ficha de pieza, portadas de sección, páginas, autor, error, `llms.txt`; marca v1 en `assets/marca/` (favicon SVG e ICO, iconos de móvil, manifiesto); textos en español.
- `ghost/routes.yaml` (secciones en `/tierra/`, `/mar/`, `/aire/`, `/logistica/`, `/regulacion/`, `/licitaciones/`, `/analisis/`; etiquetas en `/tema/`, firmas en `/firma/`; `/llms.txt`) y `ghost/redirects.yaml` (301 de las 74 URL en la raíz a su sección; `src/ghost_redirects.py`).
- `src/ghost_publish.py` — ficha estructurada dentro de una tarjeta HTML de Ghost (si no, Ghost borra las clases), respuesta directa de 40–60 palabras (campo nuevo `answer`; si falta, frases completas del resumen), etiquetas de sección, apertura y segunda, subida de fotos con crédito y licencia, JSON-LD NewsArticle + FAQPage, página `edicion-hoy` (`--edition`), secciones con su respuesta directa (`--setup`).
- `src/ghost_theme_deploy.py` y `.github/workflows/tema-ghost.yml` — empaquetar, validar, subir y activar el tema.
- `verticals/movilidad.json` — bloques `brand` y `ghost` (URL pública, menú, secciones con su texto de 40–60 palabras, etiquetas internas). `verticals/movilidad/marca/` — paquete de marca v1.
- Documentación: `docs/tema-ghost.md` (nuevo), `docs/marca.md` (nuevo), `docs/tarea-edicion-diaria.md` (pasos 3 y 7 quáter), `docs/firma-y-publicacion.md`, `docs/arquitectura.md`, `docs/paso-a-code.md`, `CLAUDE.md`.

## Fuera de alcance

Tarifas y panel de anunciantes (fase 4: los huecos ya existen con autopromoción), boletín por correo con diseño propio (Ghost lo envía con su plantilla y la cabecera `logo-boletin.png`), «Sucederá pronto», blogs y tecnología del prototipo (vendrán como páginas o colecciones en cambios propios).

## Qué verás tú

**Ahora mismo, sin activar nada** (en la app de Claude o en GitHub, desde el móvil):
- Capturas de la vista previa: `docs/tema-ghost/portada-1366.jpg`, `portada-390.jpg`, `pieza-1366.jpg`, `pieza-390.jpg` (Ghost local con las 74 piezas reales).

**Cuando digas «activa el tema»** (lo hago yo por API en un minuto, salvo los tres pasos manuales de abajo):
- Portada de edición: https://www.moticias.com/
- Secciones: https://www.moticias.com/tierra/ · https://www.moticias.com/mar/ · https://www.moticias.com/aire/ · https://www.moticias.com/regulacion/ · https://www.moticias.com/licitaciones/ · https://www.moticias.com/analisis/
- Una ficha: https://www.moticias.com/aire/air-europa-agrupa-su-mantenimiento-en-la-marca-air-europa-cshv/
- La dirección antigua de esa pieza redirige sola: https://www.moticias.com/air-europa-agrupa-su-mantenimiento-en-la-marca-air-europa-cshv/
- Para los motores generativos: https://www.moticias.com/llms.txt · mapa del sitio: https://www.moticias.com/sitemap.xml

## Qué tienes que hacer tú (una vez)

1. GitHub → movo-es/moticias → Settings → General → Danger Zone → **Change visibility → Private**.
2. GitHub → Settings → Secrets and variables → Actions → **New repository secret**: `GHOST_URL` (la URL de la Admin API de la integración) y `GHOST_ADMIN_KEY` (la Admin API key). Están en Ghost → Ajustes → Integraciones → tu integración.
3. Tras el visto bueno, en Ghost → Ajustes → **Labs**: «Upload routes YAML» con `ghost/routes.yaml` y «Upload redirects» con `ghost/redirects.yaml` (te los dejo descargables), y en **Navegación**: Portada, Tierra, Mar, Aire, Regulación, Licitaciones, Análisis (y en la secundaria: Cómo trabajamos, Aviso legal, Privacidad, Cookies). Ghost no deja hacer esto a las integraciones.
