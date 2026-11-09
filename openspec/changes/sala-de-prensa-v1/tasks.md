# Tareas: sala-de-prensa-v1

## Hecho el 9-11-2026
- [x] 1. Configuración `prensa` en `verticals/movilidad.json` (planes, visibilidad, filtro de valor, asesor, método de impacto).
- [x] 2. `src/prensa_asesor.py`: puntuación, avisos con la frase, propuestas, segunda pasada IA opcional, recomendador con audiencia real.
- [x] 3. `src/contactos.py`: base privada, importador de LinkedIn, bases legales, relevancia, recuentos por segmento.
- [x] 4. `data/medios/`: catálogo inicial de medios y newsletters del sector (datos públicos; audiencia solo con fuente).
- [x] 5. `src/prensa_difusion.py`: planificar (tres puertas), aprobar, enviar por Brevo con etiqueta y baja, resumen B2C.
- [x] 6. `src/prensa_publicar.py`: nota → post de Ghost con etiquetas y marca; lista `/notas-de-prensa/`.
- [x] 7. `src/prensa_impacto.py`: huellas, consultas, clasificación con evidencia, alcance, estimación, informe HTML.
- [x] 8. `app/public/prensa/` + `api/prensa.py`: asesor en vivo, opciones y envío de la nota a la cola privada.
- [x] 9. Comandos `/prensa-difusion`, `/prensa-impacto`; `/prensa-buzon` actualizado.
- [x] 10. Docs: `docs/prensa/oferta.md`, `metodo-repercusion.md`, `legal-contactos.md`, `plantillas.md`; borrador `supabase/migrations/003_sala_de_prensa.sql`.
- [x] 11. Prueba completa sobre una nota ficticia (`ejemplo/`).
- [x] 12. `src/ghost_theme.py` (descargar, buscar, reemplazar, subir) para versionar el tema y cambiar el pie.

## Pendiente (Rainer o claves)
- [ ] 13. Rainer: exportación de LinkedIn (`Connections.csv`) → `python3 -I src/contactos.py importar-linkedin`.
- [ ] 14. Rainer: confirmar tarifas, nombre de la sección y textos de marca (`docs/prensa/oferta.md`).
- [ ] 15. Con `GHOST_ADMIN_KEY`: etiqueta `notas-de-prensa`, newsletter «Notas de prensa» con etiquetas `np-<modo>`, página `/difunde-tu-nota/` con `docs/prensa/oferta.md`.
- [ ] 16. Vercel: `ANTHROPIC_API_KEY` (segunda pasada del asesor) y `BREVO_API_KEY` (aviso de nota recibida) en el proyecto de la app.
- [ ] 17. Tarea programada «MOTICIAS · sala de prensa» (laborables 09:3x): `/prensa-buzon` + `/prensa-difusion` + `/prensa-impacto`.
- [ ] 18a. Al versionar el tema de Ghost: excluir `tag:hash-comunicado` de la portada, de las listas de sección y del boletín (las notas solo en `/tag/notas-de-prensa/` y en las páginas de ejes).
- [ ] 18. Revisión de `docs/prensa/legal-contactos.md` por un abogado antes del primer envío a periodistas.
