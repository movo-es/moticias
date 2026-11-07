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
- [ ] `python3 -I src/ghost_publish.py --setup --all --status published --edition <última>`: secciones con su respuesta directa, 74 piezas con el formato nuevo y sus fotos (fecha original conservada), apertura y página de la edición
- [ ] `python3 -I src/ghost_theme_deploy.py --upload --activate`
- [ ] Subir `ghost/routes.yaml` y `ghost/redirects.yaml` y cambiar el menú (Rainer, a mano: Ghost no lo permite por API)
- [ ] Zona horaria Europe/Madrid, icono, logotipo y og:image de la marca en Ghost → Ajustes (Rainer o por sesión)
- [ ] Verificar las URL de «Qué verás tú» y archivar el cambio
- [ ] Variables `GHOST_URL` y `GHOST_ADMIN_KEY` en la tarea programada «MOTICIAS · edición diaria»
