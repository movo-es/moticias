# Tareas · agenda-de-eventos

Propuesta del 15-11-2026. **No aplicar sin el «sí» de Rainer y sus decisiones 1–6** (`proposal.md § Decisiones`). La decisión 7 va en el cambio aparte `comprobador-diario`.

Coordinación con otras sesiones abiertas: la migración de este cambio es la **012** (la 011 es de `restaurar-copia`). Antes de cada `push` a `main` se recoge `main` y se rebasa encima, sin forzar. En ficheros compartidos (`api/gestor.py`, `app/public/gestor/index.html`, `CLAUDE.md`, `vercel.json`, `verticals/movilidad.json`) se suma, nunca se pisa.

## 0. Antes de aplicar
- [ ] 0.1 «Sí» de Rainer y decisiones 1–6.
- [ ] 0.2 `restaurar-copia` con su 011 aplicada y en `main` (o confirmado que no choca).

## 1. Datos y validador
- [ ] 1.1 `verticals/movilidad.json → agenda`: temas (10, con color), formatos, modalidades, públicos, estados, origenes, periodo (3 meses), fuentes del barrido, textos de la página.
- [ ] 1.2 `src/eventos.py`: `validar · listar · alta · pasar-a-pasado`; territorio contra la taxonomía; fuente con URL y fecha obligatoria; resumen ≤ 60 palabras.
- [ ] 1.3 Semilla: re-comprobación en la web de cada organizador (WebFetch solo de las URL de la semilla) y alta de los 12 + 3 por confirmar + 3 posteriores en `data/eventos/`.

## 2. Página pública
- [ ] 2.1 `src/ghost_agenda.py` (`--html`, `--publicar`, `--hoy` para pruebas): agenda, archivo, fichas, «Subir mi evento»; `ItemList`, `FAQPage`, `Event`.
- [ ] 2.2 Mapa (SVG generado con la proyección de `portal/spain.js`) y filtros en el pie (`ghost/inyeccion-pie.html` o `m.js`): mes × ciudad × tema, contadores, teclado, 44 px, móvil.
- [ ] 2.3 Dirección de las fichas según la decisión 3 (rutas de Ghost: descargar las actuales, añadir, subir).
- [ ] 2.4 Menú principal, `ghost/llms.txt`, `src/export_search_index.py`, `app/public/feed/agenda.ics`.
- [ ] 2.5 `ghost_al_dia`: rehace la agenda cuando cambia `data/eventos/` (huella de la colección).

## 3. Formulario y base privada
- [ ] 3.1 Migración `012_agenda_eventos.sql` (aplicable dos veces): `agenda_envios`, `agenda_avisos`, `agenda_barridos`, `crm_contactos`; ampliar el `check` de `crm_actividades.tipo` con `evento_agenda`; RLS como el resto.
- [ ] 3.2 `api/agenda.py` (o acción en `api/gestor.py`): recepción con campo trampa, tiempo mínimo y límite por origen; acuse; aviso al editor jefe.
- [ ] 3.3 Página `subir-mi-evento` con los cuatro bloques y los tres permisos.

## 4. Gestor y CRM
- [ ] 4.1 Pestaña «Agenda»: por revisar, publicados, organizadores y responsables, alta manual; acciones en bloque; 403 para publicar/retirar sin superadmin.
- [ ] 4.2 Publicar → cuenta (casada por dominio; por dominio + nombre en dominios compartidos), persona, `crm_contactos` con nivel y fuente, actividad `evento_agenda`, paso a 14 días; «No contactar» respetado.
- [ ] 4.3 Semilla del CRM directa a Supabase (`execute_sql`), nunca a un fichero del repositorio.
- [ ] 4.4 Panel de actividades según la decisión 2.
- [ ] 4.5 ✎ de `m.js` en cada cita.

## 5. Mantenimiento
- [ ] 5.1 `.claude/commands/agenda-barrido.md` y `docs/tarea-agenda-barrido.md`; tarea programada semanal (Opus).
- [ ] 5.2 Cron `comprobar`: enlaces de inscripción de los eventos publicados.

## 6. Pruebas sin red (`tests/test_agenda.py`, fecha fija 15-11-2026)
- [ ] 6.1 Validador: semilla sin errores; sin fuente, sin fecha o tema inexistente → rechazado.
- [ ] 6.2 Página: 12 citas, 8 ciudades; meses 7·3·2·1; temas 5·2·1·1·1·1·1; Madrid 4 con aro; Valencia 2.
- [ ] 6.3 Filtros: diciembre + Valencia = 2; filtro vacío → aviso.
- [ ] 6.4 JSON-LD válido en ficha y página.
- [ ] 6.5 Formulario: queda `propuesto`, no sale en la web, crea aviso; sin permiso obligatorio → rechazado.
- [ ] 6.6 CRM: dos eventos de la misma entidad → una cuenta; sin contacto → «Falta contacto».
- [ ] 6.7 Ningún nombre, correo ni teléfono de la semilla del CRM en el repositorio.

## 7. Cierre
- [ ] 7.1 Documentación (punto 9 de la propuesta) y spec viva.
- [ ] 7.2 Commit `agenda-de-eventos`, `push` a `main`, migración aplicada, despliegue de Vercel comprobado, `moticias.com/agenda/` revisada en móvil.
- [ ] 7.3 Archivar el cambio y poner al día el «Estado» de `CLAUDE.md`.
