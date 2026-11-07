# Tareas: tema-ghost-v1

## Hecho (7-11-2026)
- [x] Comprobar plan de Ghost(Pro) por API: Publisher (temas propios permitidos)
- [x] Borrar en Ghost «Coming soon» (ya no estaba) y la página «About» (borrada)
- [x] Marca v1 en `verticals/movilidad/marca/`, `docs/marca.md` y bloque `brand` del vertical
- [x] Tema `ghost-theme/` con portada de edición, ficha, secciones, páginas, `llms.txt`; gscan sin errores ni avisos
- [x] `ghost/routes.yaml` y `ghost/redirects.yaml`; probados en Ghost local (todas las secciones 200, `/llms.txt` 200 text/plain, 301 de las URL antiguas)
- [x] Publicador: tarjeta HTML, respuesta directa, etiquetas de sección, apertura y segunda, fotos, JSON-LD, `edicion-hoy`, `--setup`
- [x] Ghost local con las 74 piezas y sus 74 fotos; capturas a 1366 y 390 px en `docs/tema-ghost/`
- [x] Action de GitHub y `src/ghost_theme_deploy.py`
- [x] Rutina diaria (paso 7 quáter y campo `answer`) y documentación

## Tras el visto bueno del director
- [ ] Secretos `GHOST_URL` y `GHOST_ADMIN_KEY` en GitHub (Rainer)
- [ ] Repositorio en privado (Rainer)
- [x] `python3 -I src/ghost_publish.py --setup --all --status published --edition 2026-11-06` (7-11-2026, 20:50): 7 secciones con su respuesta directa; 74 piezas con el formato nuevo y sus 74 fotos, fecha original conservada (62 publicadas, 12 en borrador); apertura Cantabria (la prevista, Ouigo-Semaf, espera al director), segunda A-32; página `edicion-hoy` publicada
- [x] `python3 -I src/ghost_theme_deploy.py --upload --activate` (7-11-2026): tema «moticias» activo en www.moticias.com; portada y ficha comprobadas a 1366 y 390 px
- [ ] Subir `ghost/routes.yaml` y `ghost/redirects.yaml` y cambiar el menú (Rainer, a mano: Ghost no lo permite por API)
- [ ] Ghost → Ajustes → General: título «MOTICIAS», descripción «Noticias con M de Movilidad y Transportes», zona horaria Europe/Madrid; Design & branding: icono, logotipo, color #0033A1 y og:image de `verticals/movilidad/marca/` (Rainer; la integración no puede cambiar ajustes). Ghost genera ya su propio `/llms.txt` con el título y la descripción del sitio; al subir `routes.yaml` lo sustituye el del tema
- [ ] Verificar las URL de «Qué verás tú» y archivar el cambio
- [ ] Variables `GHOST_URL` y `GHOST_ADMIN_KEY` en la tarea programada «MOTICIAS · edición diaria»
