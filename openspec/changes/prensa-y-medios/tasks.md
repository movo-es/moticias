# Tareas · prensa-y-medios

- [x] Migración 005 (`medios`, `periodistas`, `prensa_envios`, `prensa_destinatarios`, `prensa_coberturas`, `prensa_recalcular()`, vistas `medios_hoy` y `periodistas_hoy`)
- [ ] Aplicar la 005 en Supabase «moticias» (pide confirmación de Rainer en el conector)
- [x] `src/prensa.py` (lectura, edición, envíos por Brevo, baja firmada, sincronización, detección de suscriptores, `validar` y `sql` para la tarea)
- [x] `api/gestor.py`: `prensa_*` (GET), `prensa` (POST), `prensa_baja` (pública, firmada), `prensa_cron` (Vercel Cron con CRON_SECRET)
- [x] Pestaña «Prensa» en el gestor
- [x] Comando `/medios-actualizar`
- [x] Semilla inicial (124 medios, 10 periodistas con fuente) en `work/` (fuera del repositorio)
- [ ] Cargar la semilla en la base
- [ ] Tarea programada «MOTICIAS · base de prensa» (miércoles 15:30)
- [ ] Variables en Vercel: BREVO_API_KEY, CRON_SECRET (y opcionales PRENSA_REMITENTE, PRENSA_RESPONDER_A); remitente verificado en Brevo
- [ ] Primer envío de prueba a una dirección propia
