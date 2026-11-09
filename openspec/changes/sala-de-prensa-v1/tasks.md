# Tareas: sala-de-prensa-v1

## Hecho el 9-11-2026
- [x] 1. Configuración `prensa` en `verticals/movilidad.json` (planes con tarifas confirmadas, visibilidad, filtro de valor, asesor, método de impacto).
- [x] 2. `src/prensa_asesor.py`: puntuación, avisos con la frase, propuestas, segunda pasada IA opcional, recomendador con la audiencia real de la base.
- [x] 3. Unión con `prensa-y-medios`: `src/prensa_valor.py` (relevancia por ejes sobre medios y periodistas, tope semanal, LinkedIn → `src/prensa.py sql`); sin lista propia.
- [x] 4. Migración `006_sala_de_prensa.sql`: `prensa_notas` y ampliación de `prensa_coberturas`.
- [x] 5. `src/prensa_difusion.py`: borrador en `prensa_envios` con motivo por destinatario, aviso a quien aprueba, resumen B2C por Ghost.
- [x] 6. Aprobación de la oficina en notas pagadas de clientes (`notas_clientes` en `src/equipo.py`, `api/gestor.py`, gestor); enlace `?envio=<n>`.
- [x] 7. `src/prensa_publicar.py` (desde-pedido, nueva, publicar, retirar, lista) y `src/prensa_impacto.py` sobre la base.
- [x] 8. `app/public/prensa/` + `api/prensa.py` (cliente al CRM, pedido a la base, confirmación, informe al día).
- [x] 9. Comandos `/prensa-difusion`, `/prensa-impacto`; `/prensa-buzon` al día. Docs en `docs/prensa/`.
- [x] 10. `src/ghost_theme.py` (descargar, buscar, reemplazar, subir) para versionar el tema y cambiar el pie.
- [x] 11. Pruebas sin base con datos ficticios (`ejemplo/`).

## Pendiente
- [ ] 12. Aplicar en Supabase la `005_prensa_medios` (de `prensa-y-medios`) y después la `006_sala_de_prensa`. Ojo: en la base ya hay otra «005» (`005_seguimiento_y_encargos`, del cambio `seguimiento-y-seo`): conviene renumerar el fichero de prensa a 007 y esta a 008 al fundir, o aplicarlas con su nombre tal cual.
- [ ] 13. Rainer: exportación de LinkedIn (`Connections.csv`).
- [ ] 14. Ghost (con GHOST_ADMIN_KEY): etiqueta `notas-de-prensa` (`prensa_publicar.py lista`), boletín «Notas de prensa» con etiquetas `np-<modo>` en el alta, página `/difunde-tu-nota/` con `docs/prensa/oferta.md` y enlace a `app.moticias.com/prensa/`; pie del tema con «Rainer Uphoff».
- [ ] 15. Brevo: dominio moticias.com autenticado (DNS en Hostinger) y remitente de `PRENSA_REMITENTE`.
- [ ] 16. Vercel (proyecto `moticias-app`): `ANTHROPIC_API_KEY` (opcional) y `BREVO_API_KEY` si no está.
- [ ] 17. Tarea programada «MOTICIAS · sala de prensa» (laborables 09:3x): `/prensa-buzon`, `/prensa-difusion`, `/prensa-impacto`, en el entorno con las claves.
- [ ] 18. Al versionar el tema de Ghost: excluir `tag:hash-comunicado` de la portada y del boletín diario.
- [ ] 19. Revisión de `docs/prensa/legal-contactos.md` por un abogado antes del primer envío a periodistas en nombre de un cliente.
