# MOTICIAS · Arquitectura del conocimiento y del sistema (7 de noviembre de 2026)

Respuesta corta: este repositorio es la única fuente de verdad de MOTICIAS. Todo lo que el sistema sabe —reglas, fuentes, contenido publicado, decisiones— está aquí, versionado. Lo que no está en el repositorio no existe para el sistema. Los demás sitios (artefactos de Claude, proyecto de Claude, memoria de Claude, Ghost) son salidas o ventanas de lectura.

## 1. Dónde está cada cosa

| Qué | Dónde | Quién lo cambia |
|---|---|---|
| Identidad, reglas de siempre, cómo trabajar | `CLAUDE.md` | Rainer, por cambio OpenSpec |
| Manual operativo (modelo de datos, reglas, rutina) | `docs/manual-operativo.md` | cambio OpenSpec |
| Estándar de cada reportaje (estructura, voz, prohibiciones) | `docs/estandar-profundidad.md` | cambio OpenSpec |
| Texto de la rutina diaria | `docs/tarea-edicion-diaria.md` (invocada por `.claude/commands/edicion-diaria.md`) | cambio OpenSpec |
| Inventario de fuentes y su estado | `docs/fuentes.md` (legible) y `portal/data/sources.json` (máquina) | la rutina, cada mañana, cuando detecta un cambio |
| Benchmark y plan de negocio | `docs/benchmark-referencias.md`, `docs/plan-moticias-com.md` | Rainer |
| Gestores del portal (blogs, publicidad, licitaciones, logística, tecnología) | `docs/gestores-portal.md` | cambio OpenSpec |
| Registro de ediciones | `docs/ediciones.md` | la rutina, cada mañana |
| Estrategia (modelo, segmentos, verticales, sensores) | `docs/estrategia.md` | Rainer |
| Configuración de cada vertical | `verticals/<id>.json` | cambio OpenSpec |
| Esquema de la plataforma (CRM, señales, asesor) | `supabase/migrations/` | cambio OpenSpec |
| Informes del asesor y borradores de promoción | `docs/asesor/`, `docs/promo/` | los agentes, cada semana / cada edición |
| Campañas temáticas (plan, palabras clave, creatividades, KPI) e informes de cierre | `data/campanas/<id>.json`, `docs/campanas/` | `/campana-tematica` (Rainer o un editor); cierre: el agente |
| Especificaciones vivas y cambios en curso | `openspec/` | Rainer y Claude Code, método OpenSpec |
| Contenido publicado (piezas, boletines, plazos, ediciones, ajustes, blogs, anuncios, soluciones) | `data/<colección>/<id>.json` | la rutina (altas); Rainer (correcciones) |
| Fotos con licencia y sus créditos | `portal/img/*.jpg`, `portal/img/credits.json` | la rutina |
| Código del portal (artefacto) | `portal/` | cambio OpenSpec (hoy no se toca) |
| Código y datos de la hemeroteca | `hemeroteca/` | código: OpenSpec; datos: la rutina |
| Scripts | `src/` | cambio OpenSpec |
| Perfiles de ediciones a medida y widgets (módulo 1) | `data/perfiles/<id>.json` (+ `contenido/<id>/` del cliente) | sala de redacción; hoy, a mano |
| Feeds del widget y el propio widget (módulo 3) | `app/public/feed/*.json` (los genera `src/export_feed.py`), `app/public/widget.js` | la rutina, cada mañana; código por OpenSpec |
| Ediciones a medida emitidas (módulo 2) | `work/ediciones/<perfil>/<fecha>/` (temporal); archivo opcional en `data/ediciones-a-medida/` | `/edicion-a-medida` |
| Gestor de productos propios y menciones (cajas «Contenido patrocinado» en el texto) | `data/productos/<id>.json` (modo, exclusividad, umbral, contexto, disparadores, textos); `menciones` dentro de cada pieza; informes en `work/menciones/` | `src/menciones.py` desde la rutina (7 quinquies) y `/menciones`; el director y la oficina, en el gestor móvil `app.moticias.com/gestor/` (`api/gestor.py`, Vercel), que escribe aquí por commit y republica en Ghost |
| Taxonomía de tres ejes (modo · tema · territorio) y sinónimos | `verticals/movilidad.json → taxonomia, busqueda`; campos `modo`, `submodo`, `temas`, `territorios` en cada pieza; `src/taxonomia.py` (informe · aplicar · pieza) | la rutina en cada pieza nueva; el diccionario, por OpenSpec |
| Índice del buscador web y navegación por facetas | `app/public/buscador/index.json` (lo genera `src/export_search_index.py`; Vercel lo sirve con CORS); maqueta y JavaScript de referencia en `openspec/changes/navegacion-y-buscador/maqueta/` hasta que el tema de Ghost se versione | la rutina (7 ter); tema por OpenSpec |
| Buscador y piezas bajo demanda | `src/buscador.py` (veredicto sobre `data/`, con sinónimos, territorio, vecinas y erratas); `data/encargos/<id>.json` (sin datos personales); piezas con `origen: bajo-demanda` | `/pieza-bajo-demanda` (tarea cada 2 h, prevista) y a mano |
| «Quién decide» (módulo 7) | `data/cargos/<id>.json`, `data/organizaciones/`, listas revisadas en `docs/quien-decide/` | `/quien-decide-actualizar` (mensual); altas a mano con `src/quien_decide_semilla.py sembrar` |
| Sala de prensa (módulo 8) | `data/notas-de-prensa/<id>.json`, plantillas en `docs/prensa/` | `/prensa-buzon` |
| Conocimiento (módulo 6, hasta Supabase) | `data/conocimiento/` (fuentes, propuestas, estado) | `/conocimiento-ingesta` |
| Textos legales | `docs/legal/` (con los datos de Avionline) → páginas de Ghost | Rainer (revisión profesional después) |
| Tema de moticias.com y textos de referencia de `llms.txt` | `ghost/theme/`, `ghost/` | `src/ghost_theme.py`; nunca el panel de Ghost |
| Estrategia 2027 y su cambio | `docs/estrategia-2027.md`, `openspec/changes/plataforma-2027/` | Rainer y Code, método OpenSpec |
| Trabajo temporal de una sesión | `work/` (ignorado por git) | nadie lo conserva |

## 2. Las tres vías de actualización

1. **La rutina diaria** (06:38, laborables). Escribe la edición en el portal, la hemeroteca y `data/`; añade una línea a `docs/ediciones.md`; anota en `docs/fuentes.md` toda fuente caída o cambiada; hace `git push`. Si algo falla, lo dice en el aviso y deja lo que tenga guardado.
2. **Rainer, por chat o desde el móvil.** Una instrucción («a partir de ahora el análisis sale solo lunes y jueves») se convierte en un cambio OpenSpec: `openspec/changes/<nombre>/` con la propuesta, las specs afectadas y las tareas; se aplica (specs, docs, código, comando) y se archiva. Un cambio, todos los sitios a la vez.
3. **Decisiones tomadas en conversación.** Si son reglas del sistema, van al repositorio como cambio OpenSpec. La memoria de Claude queda para lo personal (cómo escribe Rainer, qué prefiere), nunca para reglas operativas.

## 3. Qué pasa con lo que ya existía

- **Proyecto de Claude «moticias.com con M de Movilidad»**: pasa a ser espejo de lectura. Sus documentos `moticias/*` ya no se editan; cuando cambie algo aquí se copia allí (o se enlaza). El archivo histórico se conserva.
- **Artefacto MOTICIAS (portal)** y **Hemeroteca**: siguen funcionando y recibiendo la edición diaria hasta que Ghost esté listo; su contenido se refleja en `data/` y `hemeroteca/data/`.
- **Tarea programada «MOTICIAS · edición diaria»**: desde el 7-11-2026 clona este repositorio y ejecuta `/edicion-diaria` (con `project_read` del proyecto de Claude como respaldo si no puede clonar). La tarea «asesor de visibilidad y credibilidad» corre los lunes a las 09:17.
- **Ghost(Pro)**: destino de publicación de moticias.com (cuenta creada el 7-11-2026). El publicador (`src/ghost_publish.py`) se añade por OpenSpec cuando el dominio y la clave de API estén listos.

## 4. Convenciones

- Un documento, un fichero: `data/<colección>/<id>.json`, JSON con `indent=1` y claves ordenadas, UTF-8 sin escapar acentos. El `id` es el nombre del fichero.
- Fechas ISO (`AAAA-MM-DD`), horas en Europe/Madrid con zona (`2026-11-05T07:40:00+01:00`).
- Nunca se borra contenido publicado; una corrección añade `revised_at` y una nota al final del cuerpo.
- Los mensajes de commit de la rutina: `Edición nº N (AAAA-MM-DD)`. Los de cambios: el nombre del cambio OpenSpec.
- Todo comando para copiar y pegar lleva delante el cambio de carpeta al proyecto (Rainer trabaja con varios repositorios a la vez).

## 5. Reconstrucciones

- Hemeroteca desde cero: `python3 -I src/hemeroteca_build.py full --db data --fallback portal/data/fallback.json --out work/hemeroteca-out --blobs portal/img`, y publicar los ficheros de `work/hemeroteca-out/files.json` en el artefacto.
- `data/` desde la hemeroteca publicada: `python3 -I src/export_data.py`.
- Barrido del BOE de un rango: `python3 -I src/boe_sweep.py --desde AAAA-MM-DD --hasta AAAA-MM-DD --json work/boe.json`.
