# Cambio: navegacion-y-buscador

Fecha: 9 de noviembre de 2026 (madrugada). Origen: Rainer no encontraba en moticias.com la pieza «Cantabria declara servicio público sus 27 líneas de autobús vencidas y paga 3,69 millones de déficit» (6-11, con la mención de MUFMI). La buscó como «concesiones caducadas en Asturias o Cantabria».

## Por qué

La pieza no aparecía por tres fallos distintos, y los tres son de diseño, no de esa pieza:

1. **Las secciones mezclan dos ejes.** `tierra`, `mar`, `aire` y `logistica` dicen *qué se mueve*; `regulacion`, `licitaciones` y `analisis` dicen *qué tipo de hecho es*. Una pieza solo tiene una sección, así que un decreto sobre autobuses de Cantabria va a Regulación y desaparece de Tierra › Autobús.
2. **El territorio no es un dato.** «Cantabria» solo estaba como etiqueta libre: ni se filtra ni se cuenta, y «Santander» o «BOC» no llevan a ella.
3. **El buscador compara palabras exactas.** «Caducadas» no encuentra «vencidas» ni «prórroga»; y buscar Asturias cuando la noticia era de Cantabria no da ninguna pista.

Sus palabras: «Necesitamos un buscador inteligente (que entienda lo que quiere buscar aunque no busque bien) y unos menús estructurados que vayan filtrando. […] También necesitamos tags filtrables regionales por comunidades autónomas. Piensa a fondo cómo mejorar eso sin ocupar excesivo espacio. Ten también un espacio prominente para "Análisis del director". En la versión móvil quita los textos y empieza debajo de la cabecera con titulares visuales».

## Qué cambia

1. **Tres ejes por pieza** (`verticals/movilidad.json → taxonomia`), independientes entre sí, además de `section` y `subsector`, que se conservan para el portal, la hemeroteca y las etiquetas internas de Ghost:
   - `modo` y `submodo` — qué se mueve: Tierra (autobús, ferrocarril, movilidad urbana, carretera), Mar (puertos, transporte marítimo), Aire (aerolíneas, aeropuertos), Logística (mercancías por tierra, por mar, carga aérea), Transversal. Uno por pieza.
   - `temas` — qué tipo de hecho es: Regulación, Concesiones y licitaciones, Empresas y mercado, Infraestructuras y obras, Tecnología y datos, Seguridad e incidentes, Análisis del director. Uno o dos por pieza, el primero manda.
   - `territorios` — dónde se decide o a quién afecta: las 17 comunidades, Ceuta y Melilla, y tres ámbitos (España/Estado, Unión Europea, Internacional). Uno o varios. Cada territorio tiene alias (provincias, capitales, puertos, aeropuertos, operadores, boletín) y vecinos.
   `src/taxonomia.py` clasifica una pieza a partir de sección, subsector, etiquetas, cabecera, `geo` y resumen; las 74 piezas publicadas quedan clasificadas (revisadas a mano en el informe). Desde ahora la edición diaria rellena los tres campos en cada pieza nueva (`python3 -I src/taxonomia.py pieza <ruta>` propone; el redactor confirma o corrige; `taxonomia_manual: true` protege la corrección).
2. **Buscador que entiende** (`src/buscador.py` y el índice web): diccionario de sinónimos del sector en el vertical (`busqueda.sinonimos`: caducadas = vencidas = prórroga; concesión = OSP = contrato de servicio público; tren = ferrocarril…); si la consulta nombra una comunidad, provincia o ciudad, el topónimo pasa a ser filtro de territorio, y si allí hay poco o nada, el buscador lo dice y enseña lo de las comunidades vecinas («Poco de Asturias; sí de Cantabria»); los términos que no existen en nada publicado se corrigen con la palabra más parecida («consecion» → «concesion», «¿quisiste decir…?»). El mismo diccionario sirve al agente (`/pieza-bajo-demanda`) y al lector en la web, así que los dos encuentran lo mismo.
3. **Índice estático para la web** (`src/export_search_index.py` → `app/public/buscador/index.json`, servido por Vercel en `app.moticias.com/buscador/index.json` con CORS para `www.moticias.com`): taxonomía, sinónimos y una entrada compacta por pieza. El tema de Ghost lo carga una vez y busca y filtra en el navegador, sin servidor ni coste por consulta; cuando pase de 2 MB se parte por años. Si el lector no encuentra lo que busca, el mismo cuadro ofrece «Pídela: la investigamos y la escribimos» (encargo de `/pieza-bajo-demanda`).
4. **Menús que se filtran entre sí, en una sola barra** (menús Modo · Tema · Territorio, botón «Análisis del director» y lupa): cada menú muestra el número de piezas de cada opción *con los demás filtros puestos*, las opciones a cero quedan atenuadas y los filtros activos se ven como fichas con su aspa. Territorio se elige en un mapa de comunidades (coloreado por número de piezas) o en la lista. El estado va en la URL del tema (`?sub=autobus&terr=cantabria`), así que cualquier combinación se comparte y enlaza. En móvil la barra es una fila de fichas deslizable y los menús se abren en una hoja inferior con pestañas.
5. **Análisis del director, siempre a la vista**: en escritorio, módulo fijo en la columna derecha de la portada (último análisis con firma y fecha, los tres anteriores, «Todos los análisis →»); en móvil, la segunda tarjeta de la portada, con el mismo color propio; botón en la barra y ruta `/analisis/` con RSS. La maqueta pinta el módulo con el color de tinta y la baliza ámbar; el tema puede usar el burdeos de la sección si Rainer lo prefiere.
6. **Móvil visual**: debajo de la cabecera no hay textos de presentación ni resúmenes; empieza la apertura (foto, modo y territorio, titular) y siguen tarjetas de dos en dos con foto y titular. Los resúmenes solo se ven en escritorio.
7. **Etiquetas en Ghost** (`src/ghost_publish.py`): cada pieza lleva, además de `#<section>`, las etiquetas públicas de sus ejes con slug fijo —`m-<submodo>`, `tema-<id>`, `t-<territorio>`— y una descripción por etiqueta (Ghost la saca en `llms.txt` y en la página de la etiqueta); las etiquetas libres que repiten un eje («Cantabria») no se duplican. `ghost_publish.py --etiquetas` crea o corrige las 41 etiquetas en Ghost y renombra el slug de las que ya existían con ese nombre.

## Maqueta

`openspec/changes/navegacion-y-buscador/maqueta/index.html` es un prototipo navegable con los datos reales (publicado como artefacto de Claude el 9-11-2026 para que Rainer lo pruebe desde el móvil; `construir.py` lo monta en `work/maqueta/` con las fotos reducidas). El JavaScript de búsqueda y filtros de la maqueta es el que pasa al tema de Ghost (`ghost/theme/assets/buscador.js`) cuando `publicar-en-ghost-v1` versione el tema.

## Qué no cambia

Las secciones actuales, el portal y la hemeroteca (artefactos, espejo hasta el 8-12-2026) siguen funcionando con `section` y `subsector`. Ninguna pieza cambia de texto, firma ni aprobación: solo se añaden cuatro campos. Las etiquetas libres (`tags`) siguen existiendo para lo que no es un eje (Adif, Reglamento 1370/2007, Urda). El buscador sigue sin escribir piezas: el veredicto es para `/pieza-bajo-demanda`.

## Riesgos y cómo se cubren

- **Clasificación automática equivocada.** El informe (`taxonomia.py informe`) se revisa a mano cuando cambie la taxonomía; la rutina propone y el redactor confirma; `taxonomia_manual` protege lo corregido. Una pieza mal clasificada se corrige editando sus campos y republicando.
- **Sinónimos demasiado anchos** («puente» = ministro y = obra). El diccionario vive en el vertical, se revisa cuando el asesor semanal detecte búsquedas sin acierto, y la corrección de erratas solo actúa sobre términos que no aparecen en nada publicado.
- **Índice grande.** 210 KB hoy; se parte por años al pasar de 2 MB; el tema carga primero el año en curso.
- **Dependencia de Vercel para el índice.** Si `app.moticias.com` falla, el tema cae a la búsqueda nativa de Ghost (título y extracto).
