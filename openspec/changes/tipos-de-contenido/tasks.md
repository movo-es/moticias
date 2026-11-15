# Tareas · tipos-de-contenido

Propuesta del 14-11-2026, aprobada por Rainer el 15-11-2026.

## 0. Antes de aplicar
- [x] 0.1 «Sí» de Rainer y sus tres decisiones (15-11-2026; `proposal.md § Decisiones de Rainer`).
- [x] 0.2 Permiso de escritura en `movo-es/moticias` para la sesión que aplica (el código no puede ir por el buzón).

## 1. Explorar lo que falta por saber
- [x] 1.1 Boletín diario: comprobar en Ghost cómo sale hoy (envío automático de Ghost, a mano o ninguno) y anotarlo en `docs/manual-operativo.md`. Hecho (15-11-2026, Admin API): no sale ningún boletín diario. Hay dos boletines activos en Ghost («Moticias.com Noticias con M de Movilidad» y «Notas de prensa», semanal) y ninguna de las 95 piezas se ha enviado nunca por correo. Anotado en `docs/manual-operativo.md § 9`.
- [ ] 1.2 Tema de Ghost: confirmar que `home.hbs` sigue excluyendo `tag:hash-comunicado` y qué etiquetas internas lee. **No verificable desde aquí:** la clave de integración de Ghost no puede leer el tema (403, «API tokens do not have permission»). Lo que sí se vio en la portada en vivo: el tema pinta por su cuenta dos cajas del grupo con la etiqueta antigua y sin `rel="sponsored"`; `m.js` las corrige en el navegador (`cajasDelTema`). La exclusión de `#comunicado` en `home.hbs` se confirma al versionar el tema (`publicar-en-ghost-v1`); hoy hay 0 notas publicadas, así que no hay nada que pueda colarse.

## 2. El campo y su módulo
- [x] 2.1 `src/tipos.py`: `deducir`, `marca`, `etiqueta_ghost`, `rel`, y los comandos `migrar`, `validar`, `informe`.
- [x] 2.2 `verticals/movilidad.json → tipos_de_contenido` (los cuatro tipos con su marca y su etiqueta; nada de esto en el código).
- [x] 2.3 `python3 -I src/tipos.py migrar`: 95 piezas y 5 anuncios con `tipo_contenido`; `validar` sin errores.

## 3. Servicios del grupo
- [x] 3.1 `git mv` de los cuatro `data/ads/casa-*.json` a `grupo-*.json`; `id`, `type: grupo`, `label`, `name` y `pricing` al día.
- [x] 3.2 `verticals/movilidad.json → publicidad.tipos` (`grupo`, `patrocinio`, `publicidad`), `productos.etiqueta`, y la referencia de `data/campanas/movilidad-al-trabajo-pmst.json`.
- [x] 3.3 `app/public/sitio/m.js`, `api/gestor.py`, `src/seguimiento.py`, `app/public/gestor/index.html`: comparan con `grupo`; `rel="sponsored noopener"` en todas las cajas.
- [x] 3.4 `src/menciones.py`: etiqueta «Contenido patrocinado · servicio del grupo».
- [ ] 3.5 Migración `supabase/migrations/009_tipos_de_contenido.sql` (identificadores del seguimiento y lista de tipos). Aplicarla en Supabase «moticias».

## 4. Lectores del campo
- [x] 4.1 `src/ghost_publish.py`: etiqueta interna `#tipo-…` y marca visible en el cuerpo; «Análisis del director» solo con la firma del director; «Reportaje».
- [x] 4.2 `verticals/movilidad.json → taxonomia.temas[analisis].nombre` = «Análisis»; módulo y botón «Análisis del director» por firma (`ghost_edicion.py`, maqueta).
- [x] 4.3 `src/ghost_edicion.py`: la portada solo admite `editorial` y `noticia`.
- [x] 4.4 `src/export_search_index.py`: campo `tc` en el índice; regenerar `app/public/buscador/index.json`.
- [x] 4.5 `src/prensa_publicar.py`: las notas nacen con `tipo_contenido: nota_de_prensa`.
- [x] 4.6 `m.js`: marca por tipo en los listados.
- [x] 4.7 Boletín: según 1.1. Según 1.1 no hay boletín diario que tocar; la regla queda en `verticals → tipos_de_contenido.boletin` (`editorial`, `noticia`) y en el manual para cuando se active.

## 5. Documentación y comandos
- [x] 5.1 `CLAUDE.md`, `docs/manual-operativo.md`, `docs/gestores-portal.md`, `docs/arquitectura.md`, `docs/tarea-edicion-diaria.md`, `docs/tarea-batida.md`, `docs/estrategia-2027.md`.
- [x] 5.2 Comandos `/edicion-diaria`, `/batida`, `/noticias-gestor`, `/pieza-bajo-demanda`, `/prensa-buzon`, `/retoques`: toda pieza nueva lleva `tipo_contenido`.
- [x] 5.3 Según la decisión 3: nota de remisión en las propuestas anteriores.

## 6. Pruebas (sin red)
- [x] 6.1 `src/tipos.py validar` sobre todo `data/`.
- [x] 6.2 Post de Ghost construido en seco para una pieza de cada tipo: etiqueta interna, marca y `rel` correctos.
- [x] 6.3 `m.js` sobre copias de una portada y una pieza: cajas del grupo con la etiqueta nueva y `rel="sponsored"`.
- [x] 6.4 Búsqueda del término antiguo en el repositorio: cero resultados fuera de lo que la decisión 3 deje como histórico. Resultado: 0 fuera de lo histórico salvo una constante en `portal/app.js` (el portal antiguo acepta el tipo que aún guarda la base de su artefacto, hasta el 8-12-2026; decisión 2). 11 en propuestas antiguas, con nota de remisión.

## 7. Cierre
- [ ] 7.1 Commit `tipos-de-contenido`, `push` a `main`, despliegue de Vercel comprobado.
- [ ] 7.2 Republicar en Ghost las piezas (botón «Subir todo a la web ahora» o el cron) y comprobar una de cada tipo en moticias.com.
- [ ] 7.3 Fundir la spec en `openspec/specs/tipos-de-contenido/` y archivar el cambio.
