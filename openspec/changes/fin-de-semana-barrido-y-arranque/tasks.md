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

## 3. Verificación
- [ ] 3.1 Martes 10-11: arranque sin avisos, commit de G. Jordan en `main`, moticias.com al día.
- [ ] 3.2 Sábado 14-11: las dos batidas corren; sin novedades no avisan; `data/reserva/` en `main` si hay algo.
- [ ] 3.3 Botón: barrido de prueba con la pista «prueba»; el gestor da la hora y llega el aviso.
