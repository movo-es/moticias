# Tareas · patrocinios-en-linea

- [x] `src/menciones.py`: `modo`, `exclusividad`, `candidatos`, `proponer` con varias cajas, `cajas_html` (tarjeta HTML de Ghost con estilos en línea), `insertar_en_medio`, `url_gestor`; correo con «Gestionar».
- [x] `src/ghost_publish.py`: cajas en medio del cuerpo; `republicar()` para el gestor.
- [x] `verticals/movilidad.json → productos`: etiqueta, declaración, `max_por_pieza: 2`, `gestor_url`, reglas.
- [x] `data/productos/*.json`: `modo` y `exclusividad` (activos: automático y compartida; borradores: apagado). Las seis menciones existentes, `exclusividad: compartida`.
- [x] Gestor: `api/gestor.py`, `app/public/gestor/index.html`, `vercel.json`, `.vercelignore`.
- [x] Docs: `CLAUDE.md`, `docs/manual-operativo.md`, `docs/tarea-edicion-diaria.md`, `docs/gestores-portal.md`, `docs/arquitectura.md`, `data/productos/README.md`, `.claude/commands/menciones.md`, regla de campañas en el vertical.
- [x] Rainer: crear el proyecto de Vercel `moticias-app` (equipo MOVO) importando `movo-es/moticias` (Claude no tiene permiso para crear proyectos en el equipo).
- [x] Posición por mención y por producto (premium · estándar · referencia), editable en el gestor; marca `en_web` y subida automática a Ghost tras cada cambio; botón «Subir todo a la web ahora».
- [x] Rainer: variables en Vercel (`GESTOR_CLAVE_SUPERADMIN`, `GESTOR_CLAVE_OFICINA`, `GITHUB_TOKEN`, `GHOST_URL`, `GHOST_ADMIN_KEY`) y redesplegar.
- [x] Dominio `app.moticias.com` añadido al proyecto de Vercel.
- [ ] Registro CNAME `app` → `d56b46d5e1e89f90.vercel-dns-016.com` en Hostinger.
- [ ] Republicar en Ghost las seis piezas con caja (desde el gestor, botón «Republicar», o con `ghost_publish.py --ids …`).
- [ ] Tema de Ghost: estilo `.contenido-patrocinado` en `ghost/theme/` cuando se versione (hoy los estilos van en línea).
- [ ] Archivar el cambio cuando el gestor funcione en `app.moticias.com`.
