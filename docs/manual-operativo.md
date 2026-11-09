# MOTICIAS · Manual operativo del prototipo (v1.2, 5 de noviembre de 2026)

Portal: https://claude.ai/artifact/6r3hgcemzjFR7LcweAXgEZ (artefacto `2f56cd87-523c-490a-b970-7d2bda59a9ee`, título «MOTICIAS», privado para Rainer hasta que lo comparta).
Hemeroteca: https://claude.ai/artifact/Eidh6WEBzGJMR2LH11PcUU (artefacto `6f16e8b1-b3dc-4320-bb92-f5d1e0b37615`, «Hemeroteca MOTICIAS», privado; ver apartado 8).

> Desde el 7 de noviembre de 2026 la fuente de verdad de todo esto es el repositorio `movo-es/moticias` (ver `docs/arquitectura.md`). Este manual describe el prototipo en artefactos de Claude tal como funciona hoy; los cambios se hacen por OpenSpec y se reflejan aquí.

## 1. Qué es y cómo está montado

Un solo sitio estático (HTML, CSS y JavaScript sin dependencias) publicado como artefacto de Claude, con tres capacidades de la plataforma:

- `db`: base de datos del artefacto. Lectura para cualquier persona con acceso al enlace; escritura solo para el propietario y los editores (`rules: [{path:"", read:"view", write:"admin"}]`).
- `user`: identifica al visitante. Si es el propietario o un editor, la página muestra los controles de administración.
- `assets`: subida de fotos desde el panel de administración; cada foto queda en `/_blob/<id>`.

Si la base no responde (por ejemplo, al abrir el artefacto sin sesión), la página carga `data/fallback.json`, la última edición compilada, y lo avisa con una franja amarilla. En ese modo no se puede editar.

Aunque la base responda, la página fusiona `data/fallback.json` con ella: para cada pieza del fallback que tenga `deep_rev`, los campos de fondo (`image`, `body_md`, `key_data`, `timeline`, `sources`, `title`, `subtitle`, `summary`, `actors`, `relevance_for`, `why`, `next`, `key_fact`, `revised_at`, `published_at`, `published_time`) sustituyen a los de la base cuando su `deep_rev` es mayor que el del documento guardado. Así se publicaron los reportajes de fondo de la edición nº 1: en la base esas piezas no tienen `body_md`, pero los lectores sí lo ven. Desde la edición nº 2 la rutina escribe el `body_md` directamente en la base.

Ficheros publicados: `index.html`, `styles.css`, `app.js`, `spain.js` (mapa de provincias precalculado), `data/fallback.json`, `data/sources.json` (76 fuentes verificadas), `img/*.jpg` (fotos con licencia Creative Commons) e `img/credits.json` (autor, licencia y origen de cada foto). En el repositorio están en `portal/`.

Rutas (hash): `#portada`, `#tierra`, `#mar`, `#aire`, `#regulacion`, `#licitaciones`, `#analisis`, `#datos`, `#fuentes`, `#a-<id>` para una pieza.

## 2. Modelo de datos

Colección `articles/{id}` — una pieza (noticia, análisis o reportaje):

| Campo | Uso |
|---|---|
| `kind` | `noticia`, `analisis` o `reportaje` |
| `section` | `tierra`, `mar`, `aire`, `regulacion`, `licitaciones`, `analisis` |
| `subsector` | `autobús`, `ferrocarril`, `carretera`, `urbano`, `aéreo`, `marítimo`, `transversal` |
| `modo`, `submodo` | Qué se mueve (eje 1 de la taxonomía, `verticals/movilidad.json → taxonomia`): `tierra` (autobus, ferrocarril, urbano, carretera), `mar` (puertos, maritimo), `aire` (aerolineas, aeropuertos), `logistica` (logistica-tierra, logistica-mar, logistica-aire), `transversal`. Uno por pieza. Lo propone `python3 -I src/taxonomia.py pieza <ruta>` |
| `temas` | Qué tipo de hecho es (eje 2): lista de uno o dos ids —`regulacion`, `concesiones`, `empresas`, `infraestructuras`, `tecnologia`, `seguridad`, `analisis`—; el primero manda |
| `territorios` | Dónde se decide o a quién afecta (eje 3): lista de ids de comunidad (`cantabria`, `madrid`…, `ceuta`, `melilla`) y ámbitos (`estado`, `ue`, `internacional`). Alimenta el menú Territorio, el mapa y el buscador. `taxonomia_manual: true` protege una corrección a mano |
| `kicker`, `title`, `subtitle` | Tema general y sector · Título · Subtítulo (formato obligatorio) |
| `summary`, `actors`, `relevance_for`, `why`, `next` | Los cinco bloques obligatorios: de qué trata, protagonistas, para quién es relevante, por qué importa, qué puede pasar ahora |
| `key_fact` | El dato que sostiene la pieza (cifra, fecha, referencia) |
| `body_md` | El reportaje de fondo en Markdown (## secciones, **negrita**, > cita, >> cita destacada). Obligatorio en toda pieza: 1.000–1.500 palabras en noticias, 900–1.300 en el análisis, 1.800–2.500 en reportajes. Los enlaces, solo `https://…`: el portal no convierte `[texto](#a-…)` |
| `key_data` | Cifras clave: lista de `{label, value, source}` (4–8) que la página muestra en la columna lateral |
| `timeline` | Cronología: lista de `{date, text}` (4–10) pasados y futuros; los futuros se marcan en color |
| `scope` | Ámbito del análisis (rotación diaria) |
| `author`, `author_role`, `author_note` | Firma («G. Jordan» por defecto; «Rainer Uphoff» solo en piezas importantes y dentro del cupo del 10 %, `src/firma.py`), cargo y declaración de intereses (sin nombre si firma la redacción). `firma_director` (true/false) fija la firma a mano; `motivo_importante` y `firma_motivo` explican la decisión |
| `risk`, `review_note` | `rutinaria` o `critica`, y la frase que lo justifica (ver § 3, aprobación) |
| `campaign` | id de la campaña temática activa a la que pertenece la pieza (`data/campanas/`), o `null` |
| `menciones` | Lista (dos publicadas como mucho; una si es exclusiva) de `{producto, nombre, texto, cta, url, exclusividad, estado: publicada · propuesta · retirada, motivo, puntuacion, origen: automatica · manual, propuesta_en, historial}`: las cajas «Contenido patrocinado» que el publicador pinta en medio del texto. Se gestionan en `app.moticias.com/gestor/`. La escribe `src/menciones.py` desde `data/productos/`; retirar es cambiar `estado`, nunca borrar |
| `origen`, `encargo` | `bajo-demanda` y `{id, consulta, fecha}` cuando la pieza nació de una consulta de un cliente (`/pieza-bajo-demanda`); nunca datos del solicitante |
| `date`, `event_date`, `published_at`, `published_time` | Fecha de edición, fecha de los hechos, sello de publicación |
| `status` | `publicado`, `pendiente` (crítica a la espera del director) o `borrador`; solo `publicado` se muestra a los lectores |
| `featured` | `1` apertura, `2` segunda, `0` resto |
| `relevance` | `ALTA` o `MEDIA` |
| `geo` | `{place, lat, lon}` para el mapa |
| `image` | `{src, assetId, alt, credit, license, source}`; `src` relativo (`img/x.jpg`) o `/_blob/<id>` |
| `sources` | Lista de `{kind: oficial|medios, outlet, title, url, published, accessed}` |
| `tags`, `reg_kind`, `doc_ref`, `authority`, `amount`, `deadline` | Metadatos para Regulación y Licitaciones |

Colección `boletines/{id}` — cada referencia curada del BOE: `fecha`, `boletin`, `referencia` (BOE-A/B-2026-NNNNN), `seccion_codigo`, `organo`, `titulo`, `titulo_corto`, `tipo`, `modos[]`, `url`, `nota` (la lectura editorial en una línea), `edicion` (fecha de la edición que la publicó; desde el 5-11-2026, todas las referencias lo tienen).

Colección `agenda/{id}` — plazos y fechas: `date`, `kind` (`plazo`, `consulta`, `vigor`, `evento`), `title`, `authority`, `amount`, `amount_eur`, `mode`, `url`, `edicion` (fecha de la edición que lo anotó).

Documento `editions/{AAAA-MM-DD}` — la edición del día: `number`, `closed_at`, `lead_id`, `analysis_id`, `note_metodologica`, `document` (el documento del día), `boe_series` (barras del gráfico por día: `total`, `lic`, `disp`), `boe_range`, `ticker` (diez titulares de boletines) y `ticker_label`.

Documento `settings/site` — `rotation` (los siete ámbitos del análisis diario), `recent_scopes` (los últimos ámbitos usados, para no repetir), `editor`, `contact`.

Colecciones de los gestores (ver `docs/gestores-portal.md`): `blogs/{id}` (ediciones a medida), `ads/{id}` (publicidad y autopromoción), `soluciones/{id}` (escaparate tecnológico).

En el repositorio, cada documento de cada colección es un fichero `data/<colección>/<id>.json` (ver `docs/arquitectura.md`).

## 3. Administración (Rainer, superadministrador)

Con la sesión de Claude abierta, el artefacto detecta al propietario y muestra el botón «Administrar» (arriba a la derecha) y el botón flotante. El cajón de administración tiene estas pestañas: Piezas, Edición, Boletines, Agenda, Blogs, Tecnología, Publicidad.

- **Piezas**: lista de todas las noticias y análisis; «Nueva pieza» abre el formulario completo (bloques, fuentes con fechas, imagen con subida de archivo, geolocalización, destacado, estado). Borrar pide una segunda pulsación.
- **Edición**: cabecera del día (apertura, análisis, documento del día, nota metodológica, titulares del ticker).
- **Boletines**: altas y bajas de referencias del BOE.
- **Agenda**: plazos y fechas.

Desde cada pieza, el enlace «Editar esta pieza» abre su formulario. Los cambios se guardan en la base al instante y los ven todos los lectores en la siguiente carga.

Aprobación (criterio del director, 7-11-2026): las piezas rutinarias —una fuente oficial, o dos fuentes profesionales de confianza que coincidan— se publican directamente con la firma «G. Jordan, Redactor responsable»; las críticas para la reputación o con implicaciones legales (criterios en `verticals/movilidad.json` → `editorial.critical_criteria`) y los análisis que firma el director se guardan en `pendiente` y los publica él. Firmar no es aprobar (9-11-2026): el nombre del director firma como mucho el 10 % de las piezas de 30 días y solo las importantes (`src/firma.py`); las críticas que no cumplen eso las firma la redacción y siguen esperando su aprobación. El editor jefe edita, reenfoca con IA (con vista previa), aprueba, retira y restaura desde el gestor o desde el icono ✎ de cada noticia en moticias.com; nadie más publica (cambio `editor-jefe-y-crm`).

## 3 bis. Campañas temáticas

Una campaña temática es un periodo acotado (semanas) en el que MOTICIAS trabaja a fondo un tema con una fecha o un hecho detrás —un plazo legal, una gran licitación, una transposición, un congreso— para ganar autoridad sobre él y poner una solución (del grupo o de un anunciante) delante de quien tiene ese problema. Vive en `data/campanas/<id>.json` (plan, palabras clave, cadencia, creatividades, CTA, KPI) y su estado y resultados en Supabase (`campanas_tematicas`). Se crea, planifica y cierra con `/campana-tematica`. Reglas: orienta la selección (barridos, peso, cadencia), nunca el tratamiento ni la firma; el texto de la pieza nunca menciona la solución (la relación la hace la plataforma en huecos señalizados y en las cajas «Contenido patrocinado» del gestor de productos propios, separadas del texto, `data/productos/`); monetización en cuatro modos (`sin-publicidad` = autopromoción del grupo, `patrocinada`, `banner`, `mixta`), siempre señalizada y separada del texto; la fecha gancho no se publica hasta verificarla en fuente primaria (`hook.date_verified`); al cerrar, informe en `docs/campanas/<id>-cierre.md` y página pilar permanente. Primera campaña: «Movilidad al trabajo: la cuenta atrás de los PMST» (10-11 → 19-12-2026, MOVO, sin publicidad). Especificación: `openspec/changes/plataforma-v1/specs/campanas-tematicas/spec.md`.

## 4. Reglas editoriales (operativas)

- Profundidad obligatoria: cada pieza es un reportaje de fondo según `docs/estandar-profundidad.md` (estructura por secciones, cifras con fuente, marco legal con número y artículo, actores con cargo, calendario, lo que hay que vigilar), más la «Guía rápida» de cinco bloques que se muestra al final del cuerpo. Las piezas sin `body_md`, `key_data` y `timeline` no se publican.
- Una edición al día, por la mañana, solo en días laborables españoles. Sábados, domingos y festivos nacionales (decisión de Rainer, 9-11-2026): batidas a las 11:00 y a las 17:30 solo de grandes noticias, con edición extra si alguna lo merece; lo demás se guarda en `data/reserva/` para el lunes (`docs/tarea-batida.md`). El botón «Iniciar barrido de noticias ahora» (gestor y menú ✎ de moticias.com) lanza esa batida en cualquier momento. Nunca dos piezas sobre el mismo hecho: antes de escribir se consulta `articles` de los últimos siete días.
- Cada pieza lleva los seis bloques (resumen, protagonistas, relevancia, importancia, qué puede pasar, para saber más) y el título en tres niveles.
- Fuentes: al menos una primaria (`oficial`: BOE, DOUE, ministerio, regulador, autoridad portuaria, Adif, Aena, nota de prensa) y las de prensa (`medios`), cada una con fecha de publicación y de consulta. Lo que no tiene fuente enlazable no se publica.
- Prioridad: regulación, concesiones y contratos, plazos, movimientos empresariales de alcance estatal, infraestructuras. Fuera: sucesos locales sin efecto sectorial, promociones, incidencias del día.
- Cifras con unidad, fecha y origen. Las hipótesis se presentan como hipótesis; las investigaciones en curso, como en curso.
- Para remitir a una pieza anterior se cita su título y su fecha; el cuerpo no lleva enlaces internos.
- Fotos solo con licencia (CC BY, CC BY-SA, CC0, dominio público) y crédito visible; nada de rostros reconocibles ni fotos de prensa ajenas. La foto muestra el sujeto concreto de la pieza (el buque de esa naviera, la estación citada), y el portal nunca repite una foto en la misma página.
- Cierre: «FIN DE EDICIÓN» con fecha y hora CET, en el pie de la página.
- Declaración de intereses: en el análisis y en «Cómo trabajamos» consta la relación de Rainer con Movenbus; MOTICIAS no cubre operaciones propias de Movenbus.

## 5. El análisis diario («mi estilo»)

Ámbitos en rotación (`settings/site.rotation`): Regulación y gobernanza · Autobús y carretera · Ferrocarril · Aéreo · Marítimo y puertos · Movilidad urbana y tecnología · Infraestructuras, financiación y Europa. Cada día se elige el tema más caliente del ámbito que toca (el que lleva más días sin usarse en `recent_scopes`); si el día exige otra cosa (un accidente, una ley, una dimisión), se rompe la rotación y se anota.

Forma: 900–1.300 palabras; entrada que fija el hecho en dos frases; después secciones cortas con título de una o dos palabras («La regla», «El dinero», «El regulador», «El pasajero», «Lo que toca»); una cita destacada; cierre con lo que hay que vigilar y una fecha. Frases cortas, sustantivos de arranque en negrita, vocabulario institucional exacto (obligación de servicio público, declaración sobre la red, canon, contrato-programa), ningún adjetivo que no aporte dato, ninguna fórmula de relleno ni de inteligencia artificial, sin exclamaciones ni preguntas retóricas encadenadas. Firma: Rainer, director de MOTICIAS, con nota de intereses. Se apoya en seis fuentes como mínimo, dos de ellas primarias.

## 6. Rutina diaria automática (tarea programada «MOTICIAS · edición diaria»)

Corre cada día a las 06:38 (hora de Madrid) en una sesión nueva. El texto completo está en `docs/tarea-edicion-diaria.md`; en Claude Code es el comando `/edicion-diaria`. Pasos:

1. Lee este manual, `docs/estandar-profundidad.md` y `docs/ediciones.md`; lee en la base `settings/site`, la última `editions/*` y los `articles` de la última semana.
2. Barrido de noticias (WebSearch y RSS de `portal/data/sources.json`): tierra, mar, aire, regulación, licitaciones (TED y PLACSP), nombramientos. Selección de 5 a 8 piezas nuevas con fuente primaria, cada una desarrollada como reportaje de fondo (1.000–1.500 palabras, cifras clave y cronología).
3. Barrido del BOE con la API de datos abiertos (`src/boe_sweep.py`): el BOE del día (sale hacia las 07:00–07:30; se espera hasta las 07:50) y los días no barridos desde el último `boe_range`. Filtro por departamento (Transportes) y palabras clave de transporte de viajeros; clasificación por modos; de 5 a 15 referencias curadas con nota; plazos a `agenda`; serie diaria para el gráfico. Boletines y plazos nuevos llevan `edicion` con la fecha del día.
4. Análisis del día según el apartado 5.
5. Fotos: Openverse (`license_type=commercial`, preferencia por Flickr), comprobación visual, `upload_asset` al artefacto y crédito en `image`.
6. Escritura en la base con `db_write` (artículos, boletines, agenda, `editions/{fecha}`, `settings/site.recent_scopes`), con `ifVersion` en todo documento que ya exista.
7. Verificación: lectura de la portada, comprobación de enlaces de las fuentes primarias, y una línea en `docs/ediciones.md`. Después, actualización de la hemeroteca (apartado 8) y del repositorio (`data/`, `docs/ediciones.md`, `docs/fuentes.md` si alguna fuente cambió), con `git push`.
8. Aviso a Rainer solo con la edición cerrada o si algo impidió cerrarla.

## 7. Herramientas y scripts

En `src/`:

- `export_data.py`: vuelca el contenido de la hemeroteca y del fallback del portal a `data/` (un fichero por documento).
- `hemeroteca_build.py`: compila los datos de la hemeroteca (modos `daily` y `full`).
- `boe_sweep.py`: barrido de sumarios del BOE por API, filtro y clasificación por modos (corregidos los falsos positivos «línea aérea de contacto» y «Bus Nàutic»).

Scripts de la sesión fundacional que no se conservaron y conviene reescribir cuando hagan falta: `fetch_photos.py` (Openverse, hojas de contactos, descarga a 1600 px y créditos), `compile.py` (compila `data/fallback.json` y los lotes de carga), `check_deep.py` (control de calidad de cada reportaje: palabras, secciones, cifras, cronología, fuentes, frases prohibidas), `shot.py` (captura con Playwright a 1366 y 390 px).

## 8. Hemeroteca (desde el 5 de noviembre de 2026)

Artefacto aparte, «Hemeroteca MOTICIAS», con todas las ediciones archivadas tal como quedaron al cierre. No lee la base del portal: guarda su propia copia de los datos, que la rutina amplía cada mañana. En el repositorio: `hemeroteca/` (código y `data/`); las fotos están en `portal/img/`.

- **Máquina del tiempo** (`#maquina`, `#e-AAAA-MM-DD`): una vía con una estación por edición; flechas ◀ ▶, teclas ← → y pestañas de las ediciones anteriores detrás de la portada. Cada portada reconstruye la edición de ese día: apertura, segunda, análisis, piezas por sección, documento del día, boletines, plazos abiertos en esa fecha, gráfico del BOE, nota metodológica y «Fin de edición».
- **Búsqueda** (`#buscar`): texto completo sobre piezas, boletines y plazos; sin distinción de acentos ni mayúsculas, con frases entre comillas y exclusiones con «-». Filtros por tipo, ámbito y rango de ediciones; orden por relevancia o fecha.
- **Lector** (`#a-<id>`): la pieza completa con guía rápida, fuentes con fechas, trazabilidad, cifras clave, cronología y etiquetas.
- **Descarga**: la hemeroteca entera en un solo archivo `.html` que funciona sin conexión (sin fotos) o los datos en `.json`.
- **Ficheros**: `index.html`, `app.css` y `app.js` (código fijo); `data/index.json` (resumen de ediciones, totales y lista de fotos); `data/AAAA-MM.json` (un fichero por mes con las ediciones, piezas, boletines y plazos de ese mes); `img/` (fotos; las de `/_blob/<id>` se guardan como `img/b-<id>.jpg`).
- **Compilador**: `src/hemeroteca_build.py`. Modo `daily` (lo usa la rutina) y modo `full` (reconstrucción desde `data/` y `portal/data/fallback.json`).
- **Límites**: si una pieza se corrige en el portal después de archivada, la hemeroteca conserva la versión del día salvo reconstrucción `full`. Cada fichero de mes debe quedar por debajo de 16 MB.

## 9. Pendiente y hoja de ruta

- Publicación en moticias.com con Ghost(Pro) (plan Publisher), decidido el 7-11-2026: `src/ghost_publish.py` (posts) y `src/ghost_edicion.py` (página `edicion-hoy`, la portada), paso 7 quater de la rutina. El resumen de la edición va al final de la portada, en pequeño, nunca bajo el título (decisión de Rainer, 9-11-2026).
- Apellido para la firma de los análisis («Rainer Uphoff», siempre con apellido).
- Flujo de aprobación (borrador → publicado) desde el móvil y gestión de usuarios/suscriptores.
- Dominio propio moticias.com y correo (Brevo) para el briefing de las 7:30.
- Radar regulatorio semanal (lunes), licitaciones de la semana (viernes) y cuadro de mando mensual con CSV, según el benchmark.
- Página pública de correcciones.
- Promoción automática: publicaciones para LinkedIn e Instagram generadas con cada edición.
