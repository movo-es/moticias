# Tareas · fin-de-semana-barrido-y-arranque

## 1. Hecho el 9-11-2026
- [x] 1.1 Texto nuevo de «MOTICIAS · edición diaria» (repositorio adjunto o clonado, identidad G. Jordan, arranque con aviso, parches pendientes, puesta al día, días, git).
- [x] 1.2 Tareas «MOTICIAS · batida de fin de semana (mañana)» (sáb. y dom. 10:55) y «(tarde)» (17:26).
- [x] 1.3 `docs/tarea-batida.md` y `.claude/commands/batida.md`; DÍAS y ARRANQUE en `docs/tarea-edicion-diaria.md`.
- [x] 1.4 Botón «Iniciar barrido de noticias ahora»: acción `barrido` del gestor, caja en Piezas, menú ✎ de moticias.com; permiso `barrido` para editor jefe y editor; probado con una petición simulada.

## 2. Pendiente de Rainer (una sola vez; no hay herramienta que lo haga desde una sesión)
- [ ] 2.1 claude.ai/code/routines → cada tarea MOTICIAS (edición diaria, las dos batidas, asesor, retoques) → Edit → Advanced settings → Repository: añadir `movo-es/moticias`.
- [ ] 2.2 Mismo sitio → Cloud environment → variables: `GHOST_URL`, `GHOST_ADMIN_KEY`, `BREVO_API_KEY`.
- [ ] 2.3 En las dos batidas: «Automatically approve», como la edición diaria.
- [ ] 2.4 En «MOTICIAS · batida de fin de semana (mañana)» → Edit → Trigger → + → API → Generate token → Vercel `RUTINA_BARRIDO_TOKEN`; redesplegar.

## 2 bis. Arreglos del 14-11-2026 (batida del sábado sin permiso de subida)
- [x] 2b.1 `src/boe_sweep.py`: la cabecera User-Agent lleva `redaccion@moticias.com` (o `MOTICIAS_CONTACTO`), no un correo personal; con el correo de la cuenta, el filtro de privacidad de las sesiones bloqueaba el script. Lo mismo en la cabecera de Openverse de `docs/tarea-edicion-diaria.md`.
- [x] 2b.2 `vercel.json`: `ghost_al_dia` corre todos los días (`*/15 6-19 * * *`), para que las ediciones extra de sábado, domingo y festivo lleguen a moticias.com sin esperar al lunes. `CLAUDE.md` y el comentario de `api/gestor.py`, al día.
- [x] 2b.3 `docs/puesta-en-marcha.md`: lista única de lo que necesita cada tarea (repositorio, variables, aprobación automática, token del botón) y cómo comprobarlo.

## 2 ter. Buzón del repositorio (14-11-2026, a petición de Rainer: «repara todo»)
- [x] 2t.1 Diagnóstico: las ediciones nº 5 y nº 6 las subieron las tareas; desde el 12-11 sus sesiones arrancan sin el repositorio autorizado (el proxy rechaza el `push`) y la pantalla de tareas de Claude no tiene campo de repositorio, así que 2.1 no se puede hacer.
- [x] 2t.2 Migración `008_buzon_repositorio.sql` (tabla `repo_buzon`, política del gestor, sin borrado).
- [x] 2t.3 `src/buzon.py preparar`: de `origin/main..HEAD` a los `insert` del buzón, por partes de 350 KB, con el blob de partida de cada fichero; solo contenido.
- [x] 2t.4 `api/gestor.py` → `aplicar_buzon` (un commit por lote, en orden, sin pisar cambios, idempotente) y cron de Vercel cada 10 minutos. Probado sin red con GitHub y Supabase simulados: el árbol resultante es idéntico al de la edición nº 9 y el conflicto se detecta.
- [x] 2t.5 `docs/tarea-edicion-diaria.md` y `docs/tarea-batida.md`: el buzón antes que el parche en el proyecto; `CLAUDE.md` y `docs/puesta-en-marcha.md`, al día.
- [ ] 2t.6 Rainer: aplicar la migración 008 en Supabase y subir a `main` este cambio con los parches pendientes (una vez; el código no puede ir por el buzón).
- [ ] 2t.7 Verificar con la primera tarea que no pueda subir: lote en `aplicado` y edición en moticias.com.

- Estado de 2.1–2.4 el 14-11: sin hacer en las tareas que corrieron (la batida de la mañana no tenía el repositorio adjunto ni las claves de Ghost, y su configuración no tiene «Automatically approve»).

## 3. Verificación
- [ ] 3.1 Martes 10-11: arranque sin avisos, commit de G. Jordan en `main`, moticias.com al día.
- [ ] 3.2 Sábado 14-11: las dos batidas corren; sin novedades no avisan; `data/reserva/` en `main` si hay algo.
- [ ] 3.3 Botón: barrido de prueba con la pista «prueba»; el gestor da la hora y llega el aviso.
