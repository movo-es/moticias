# Gestores del portal MOTICIAS (4 de noviembre de 2026)

Todo se gestiona desde **Administrar**, que solo ve el superadministrador. Pestañas: Piezas, Edición, Boletines, Agenda, Blogs, Tecnología, Publicidad.

## Blogs y ediciones a medida
- Ruta pública: #blogs (índice) y #blog-<slug>.
- Cada blog tiene sus propios ajustes:
  - color, logotipo (iniciales), portada, presentación en Markdown y botón;
  - diseño: revista, lista o boletín;
  - módulos: entradas propias, selección automática, plazos, boletines y contacto.
- La selección automática filtra por tipo de pieza, sección, subsector y palabras clave.
- Visibilidad «solo con enlace»: no sale en el índice. Sirve para versiones privadas de asociaciones o empresas.
- «Copiar versión boletín (HTML)» copia un correo listo para Brevo.
- Ejemplos creados (en `data/blogs/`):
  - Cuaderno del director: retirado el 15-11-2026 (en borrador y solo con enlace; sus piezas están en «Análisis» y «Reportaje»). Nunca existió en moticias.com.
  - Edición Autobús y Carretera: plantilla de edición para una asociación, solo con enlace.

## Publicidad y patrocinios
- Huecos disponibles:
  - portada: tras «Lo esencial», tras «Reportajes» y antes de «Cómo trabajamos»;
  - cabecera y banner de sección;
  - artículo: lateral y cierre;
  - blogs;
  - boletín (reservado).
- Los huecos de publicidad nunca aparecen sobre la apertura ni dentro del texto. La etiqueta es siempre visible (art. 20 LSSI).
- Excepción, desde el 8-11-2026: las cajas «Contenido patrocinado» de los productos del grupo, en medio del texto (ver abajo).
- Los huecos sin campaña de pago se rellenan con cajas del grupo, etiquetadas «Contenido patrocinado» (`data/ads/grupo-*.json`, `type: grupo`):
  - MOVO valoración de licitaciones;
  - Ediciones a medida;
  - Anúnciate.
- Los enlaces externos llevan UTM automáticos.
- El panel muestra campañas en curso y programadas, importe contratado e inventario de huecos.
- Para el contenido patrocinado se rellena el campo «Contenido patrocinado por» de la pieza. Se señaliza y queda fuera de la selección automática de portada.
- Página pública: #anunciate (formatos, sin tarifas publicadas).

## Gestor de patrocinios (móvil) · desde el 8-11-2026

- Dirección: `app.moticias.com/gestor/` (Vercel; mientras no esté el dominio, la dirección de Vercel del proyecto `moticias-app`). Se entra con contraseña; la sesión dura 90 días en el móvil.
- Perfiles (una cuenta por persona, desde el 9-11-2026): superadministrador (todo, incluido el equipo), editor (cajas de las piezas), comercial (productos propios y publicidad) y oficina (cajas de las piezas). Alta en la pestaña «Equipo»: nombre, correo y perfil → enlace de invitación de un solo uso (7 días) para mandar por WhatsApp o correo; con él la persona crea su contraseña. Suspender en vez de borrar; «Enlace para cambiar la contraseña» si alguien la olvida. Los datos del equipo están en el repositorio privado `movo-es/moticias-equipo`.
- Suscriptores: pestaña con los totales de Ghost (gratuitos, de pago, cortesía), las últimas altas y el enlace para gestionarlos en Ghost. La redacción que escribe en Ghost se invita en Ghost (Settings → Staff).
- Acceso de emergencia: sin correo, con la contraseña común del superadministrador.
- Piezas: pendientes, falta en la web, con caja, posibles y todas. En cada pieza: publicar, retirar, editar el texto, elegir la posición (premium tras el primer párrafo · estándar entre el tercio y la mitad · referencia al final), añadir a mano otro producto (con su puntuación contra la pieza), ver cómo queda en el texto y republicar en la web.
- Productos: cómo entra cada uno (automático con umbral, con revisión, solo a mano, apagado), exclusiva o comparte, umbral, máximo por semana, textos, URL y contexto.
- Publicidad: campañas de `data/ads/`, activar o pausar.
- El correo diario de menciones lleva «Gestionar» en cada pieza: abre el gestor en esa pieza.
- Cada cambio queda en el repositorio (commit) y se sube la pieza a Ghost al momento; la caja muestra «En la web» o «Falta en la web», y la lista ofrece «Subir todo a la web ahora».

## Licitaciones y «Sucederá pronto»
- #licitaciones se divide en anuncios, publicaciones y resoluciones, y se filtra por sector:
  - autobús, ferrocarril, movilidad urbana, marítimo y puertos, aéreo, carreteras, logística.
- La fase y el sector se asignan automáticamente. Se pueden fijar a mano en la pieza o en la referencia de boletín.
- #pronto reúne la agenda (plazos, consultas, entradas en vigor, eventos) y los hitos futuros citados en las piezas. Se agrupa por hoy y mañana, esta semana, próximas semanas y más adelante.

## Logística
- #logistica: sección de mercancías con los modos tierra, mar y aire (campo «Modo» de la pieza).
- Primera tanda: 8 piezas verificadas (3 de tierra, 3 de mar, 2 de aire).

## Soluciones tecnológicas
- #tecnologia y fichas #sol-<id>: escaparate editorial con implantaciones verificables (en `data/soluciones/`).
- El editor decide el orden con flechas, destaca (abren la sección), oculta o publica.
- Una ficha patrocinada se marca y no altera el orden editorial.
- Primera tanda: 14 soluciones.
- Revisar antes de abrir al público:
  - Meep: la única fuente que la vincula a Alsa Mobi4U es un caso de estudio sin fecha.
  - ELECTRA de ETRALUX: no tiene página propia de producto.

## Imágenes
- Cada pieza tiene una foto propia, elegida por su sujeto concreto (operador, buque, estación o puerto citados), con crédito y licencia CC.
- El portal nunca repite una foto en la misma página: si coincide, usa una ilustración de sección.

## Navegación por facetas y buscador (cambio `navegacion-y-buscador`, 9-11-2026)
- Tres ejes por pieza, independientes: Modo (qué se mueve), Tema (qué tipo de hecho) y Territorio (comunidad o ámbito). `section` y `subsector` siguen para el portal y la hemeroteca.
- Una sola barra: menús Modo · Tema · Territorio (con mapa de comunidades), acceso a «Análisis» (con el autor de cada pieza) y lupa. Cada menú cuenta las piezas con los demás filtros puestos.
- Buscador con sinónimos del sector, topónimo como filtro, comunidades vecinas cuando no hay nada y corrección de erratas; sin resultado, «Pídela» (pieza bajo demanda).
- **Restaurar** (editor y editor jefe, 15-11-2026): versiones anteriores de piezas, publicidad y ediciones, y recuperación de fichas del CRM y de la base de prensa desde la copia interna de cada noche; siempre con aviso al editor jefe y deshacer (`docs/copia-de-seguridad.md § Restaurar desde el gestor`).
- Módulo fijo «Análisis» en la portada (columna derecha en escritorio; segunda tarjeta en móvil). Solo análisis firmados por el editor jefe (etiqueta interna `#analisis-editor-jefe`, campo `dir` del índice), nunca por tema: los análisis de la redacción salen como «Análisis» (cambio `tipos-de-contenido`, 15-11-2026). Cada tarjeta lleva su marca de tipo. En móvil, sin textos de presentación ni resúmenes: foto, modo · territorio y titular.
- Etiquetas de Ghost con slug fijo: `m-<submodo>`, `tema-<id>`, `t-<territorio>` (`ghost_publish.py --etiquetas` las crea; cada una con descripción, que sale en `llms.txt`).
- Maqueta navegable: `openspec/changes/navegacion-y-buscador/maqueta/`.

## Editor jefe, publicidad por niveles y CRM (9 de noviembre de 2026, cambio `editor-jefe-y-crm`)
- **Solo el editor jefe (superadministrador) publica.** Editor, comercial y oficina proponen (cajas y publicidad quedan «propuesta») y trabajan en el CRM; el servidor lo comprueba.
- **En moticias.com**, con la sesión del gestor abierta, cada noticia lleva un icono discreto ✎ (abajo a la derecha en la pieza; junto al titular en los listados): Editar, Otro enfoque con IA, Patrocinio y retoques, Retirar. `www.moticias.com/#editor` lleva a entrar y vuelve. Lo carga `<script src="https://app.moticias.com/sitio/m.js" defer></script>` en Ghost → Code injection → Site footer.
- **Editor**: campos de la pieza con vista previa al momento, firma (con el cupo del 10 %), corrección con nota al final. **Otro enfoque con IA**: seis enfoques o una indicación; la propuesta se ve junto al original; «Pasar al editor» y después «Publicar cambios». Las cifras o fechas nuevas se marcan y no se publican sin confirmarlas. **Retirar**: deja de verse, se conserva y se restaura.
- **Publicidad**: nueva caja con tipo (publicidad, patrocinio de un cliente, servicio del grupo; la etiqueta visible sale del tipo: «Publicidad», «Contenido patrocinado · <cliente>», «Contenido patrocinado» (grupo, sin decirlo), sin texto libre), anunciante, nivel (premium, estándar, básico, que marca sus huecos), titular, texto, enlace, fechas y peso; vista previa. Premium: bajo la cabecera y primera caja del lateral del artículo. Estándar: huecos de la portada y cierre del artículo. Básico: antes del pie (y boletín, reservado). Etiqueta siempre visible y `rel="sponsored"`.
- **CRM**: «Hoy y esta semana» (pasos), cuentas por tipo con buscador, ficha con personas, registrar (actividad, estado, siguiente paso), pasos, contratos (solo superadministrador y comercial), historial y archivo. «Importar las fuentes del repositorio» crea una cuenta por fuente de `portal/data/sources.json`. Regla de oro: cuenta en marcha = siguiente paso con fecha; «No contactar» es para siempre; nada se borra.
- **Suscriptores**: totales, filtros por estado y categoría, buscador y categoría de cada miembro (etiqueta `cat:` en Ghost).
- **Equipo**: en la base privada; perfiles «Editor jefe (superadministrador)», editor, comercial y oficina.

## Seguimiento, comprobador, empresas del grupo y nueva noticia (9 de noviembre de 2026, cambio `seguimiento-y-seo`)
- **Publicidad → Seguimiento**: por caja (y por producto del grupo, con sus cajas «Contenido patrocinado»), estado, publicada y retirada, posiciones, páginas donde se vio, vistas, clics y CTR en 7, 30 o 90 días; últimas comprobaciones del enlace y «Comprobar ahora». Vistas = la caja se vio al menos a medias; no cuentan robots, el comprobador ni el editor jefe.
- **Comprobador**: cron de Vercel, todos los días cada hora de 9 a 21 (Madrid), con azar; cada enlace activo se comprueba una vez al día a hora al azar (cambio `comprobador-diario`, 16-11-2026). El panel enseña «Comprobado hoy a las HH:MM · funciona / no funciona», el historial de 30 días se descarga en CSV para el anunciante y, si un enlace falla dos veces seguidas, llega un correo al editor jefe. Sus visitas no cuentan como clics ni mejoran el SEO de nadie: la cifra que ve el anunciante es solo de lectores.
- **Nueva noticia** (editor y editor jefe): pegar texto o enlace; 1) investiga y publica hoy; 2) además registra el dominio de la fuente (notas de prensa, información, no de confianza). Lo pedido por el editor o con fuente no de confianza queda para la aprobación del editor jefe. Lo atiende la rutina horaria de retoques (`/noticias-gestor`).
- **Empresas del grupo**: `/empresas-del-grupo/` (`src/ghost_grupo.py`), con la especialidad de cada marca y las piezas donde aparece su caja.

## Agenda de eventos (16 de noviembre de 2026, cambio `agenda-de-eventos`)

Respuesta corta: `moticias.com/agenda/` reúne las ferias, congresos y jornadas de transportes, movilidad y turismo en España de los próximos tres meses, con mapa, filtros y ficha por evento; los organizadores suben los suyos y los publica el editor jefe. No confundir con «Próximos plazos» y «Sucederá pronto» (los plazos de la edición, `data/agenda/`), que no cambian.

- **Página pública** (`src/ghost_agenda.py`, página de Ghost `agenda`): respuesta directa calculada (citas y ciudades del periodo), mapa con el contorno y la proyección de `portal/spain.js` (una marca por ciudad; color del tema; número si hay varias; blanca con aro discontinuo si mezcla temas; Canarias en su recuadro), pestañas de meses, «Por lugar», leyenda de temas, «Quitar filtros», «Ordenar la lista» (tema o fecha), lista con fechas, tema, formato, ciudad y sede, resumen, organiza, botón de inscripción y nota; temas sin citas; columna lateral (subir mi evento, calendario `.ics`, con fecha por confirmar, después del periodo); archivo; preguntas frecuentes; pie con la última comprobación. Datos estructurados `ItemList` + `FAQPage`, y `Event` en cada ficha. Los filtros los añade `app/public/sitio/agenda.js` (lo carga `m.js` solo en la agenda); todo el contenido ya está en el HTML. «Agenda» va en el menú principal (lo pone `m.js`), en `llms.txt` y en el índice del buscador.
- **Fichas** en `moticias.com/agenda/<evento>/`: entradas de Ghost con la etiqueta interna `#agenda`, fuera de la portada y del RSS, cuando Ghost tiene las rutas de `ghost/routes.yaml` (se suben una vez en Settings → Labs → Routes; la API no deja hacerlo con la clave de integración). Hasta entonces cada cita enlaza a su sitio en la página.
- **Subir mi evento** (`moticias.com/agenda/subir-mi-evento/`, o `/agenda-subir-mi-evento/` sin las rutas): cuatro bloques (el evento, quién organiza, persona responsable que no se publica, tres permisos separados); lo recibe `app.moticias.com/api/agenda` (`api/agenda.py`) con campo trampa, tiempo mínimo y límite por origen, y lo guarda en `agenda_envios`. Avisa al editor jefe con enlace a la cola y manda acuse al remitente; al publicarse, el enlace a su ficha.
- **Gestor, pestaña «Agenda»**: ver el punto del manual operativo. Con la sesión del editor jefe, cada cita de moticias.com lleva ✎ (editar) y ⊘ (retirar).
- **CRM**: publicar un evento crea o actualiza la cuenta de cada organizador (casada por dominio; por dominio y nombre en los dominios compartidos por muchos organismos), con etiqueta `organizador-eventos` y origen `agenda`, la persona responsable si se conoce, sus contactos en `crm_contactos` con nivel (`directo`, `prensa`, `general`, `centralita`), URL de fuente y fecha, una actividad «Evento en la agenda» y un siguiente paso 14 días antes (acreditación de prensa o propuesta de difusión), salvo «No contactar». Estados de la tabla: «Contacto directo», «Contacto general», «Contacto general · falta responsable», «Falta contacto».
- **Mantenimiento**: barrido de los lunes a las 09:41 (`/agenda-barrido`, `docs/tarea-agenda-barrido.md`); el cron `comprobar` visita cada día laborable los enlaces de inscripción y marca los caídos; el cron `ghost_al_dia` rehace la agenda cuando cambian los eventos o el día; lo terminado pasa a `pasado` y queda en el archivo. Calendario: `app.moticias.com/feed/agenda.ics`.
- **Eventos destacados de pago**: más adelante (decisión 6). Si llegan: «Contenido patrocinado · <cliente>», `rel="sponsored"` y sin alterar el orden editorial.

