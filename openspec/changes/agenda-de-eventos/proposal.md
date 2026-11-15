# Cambio: agenda-de-eventos

Fecha: 15 de noviembre de 2026. Origen: encargo de Rainer del mismo día, sobre la maqueta que vio y aprobó (agenda pública con mapa, «Subir mi evento» y la tabla de organizadores y responsables del CRM). Estado: **propuesta, pendiente del «sí» de Rainer y de sus decisiones** (al final).

Respuesta corta: una sección nueva de moticias.com, **«Agenda»** (`moticias.com/agenda/`), con las ferias, congresos y jornadas de transportes, movilidad y turismo en España de los próximos tres meses, con un mapa como el de la portada, filtros por mes, ciudad y tema, una ficha por evento y un formulario para que los organizadores suban el suyo. Detrás, una pestaña «Agenda» en el gestor (cola de revisión, publicados, organizadores y responsables), fichas del CRM que se crean solas al publicar, un bloque «Agenda» en el panel de actividades y un barrido semanal en la nube que busca eventos nuevos y vuelve a comprobar los publicados.

## Por qué

Los decisores del sector planifican su año por ferias y congresos, y no hay en España una agenda profesional fiable de transportes, movilidad y turismo juntos. Para MOTICIAS es servicio al lector (credibilidad), es una vía de entrada de organizadores (leads: acreditaciones, difusión, patrocinio) y es contenido propio que buscadores y modelos de lenguaje citan.

## Lo comprobado en el código (15-11-2026, sobre `main` en `0e57163`)

La lista «Lo comprobado» del encargo se hizo sobre `92c869a`. Desde entonces solo ha entrado `0e57163` (etiqueta de las cajas del grupo), que no toca nada de esto. Todo lo demás se confirma, con estos matices:

- `data/agenda/` tiene 74 documentos (38 `plazo`, 23 `evento`, 7 `consulta`, 6 `vigor`): son los plazos de la edición diaria. **No se tocan.**
- `crm_cuentas` **no** guarda correo ni teléfono generales de la entidad (solo `web`, `dominio`, `subtipo`, `etiquetas`, `origen`). Hay que añadirlos, con su nivel y su fuente (punto 6).
- `crm_actividades.tipo` lleva la lista de tipos fija en la base (una restricción). Para el tipo nuevo `evento_agenda` la migración tiene que ampliarla, además de `verticals/movilidad.json → crm.actividades`.
- La cuenta del CRM es única por **tipo y dominio**, no solo por dominio. Casar por dominio, sin mirar el tipo, es lo correcto aquí (IFEMA organiza GENERA y FITUR: una sola cuenta). Excepción: dominios compartidos por muchos organismos (`gobiernodecanarias.org`, `juntadeandalucia.es`…). Ahí se casa por dominio **y** nombre, para no fundir una dirección general con todo el Gobierno.
- **Migración 012, no 011.** La sesión del cambio `restaurar-copia` está aplicando ahora `011_restauracion.sql`. Su copia diaria de la base incluirá también las tablas nuevas de la agenda, sin hacer nada más.
- El territorio «valencia» de la semilla es `comunidad-valenciana` en la taxonomía.
- `ghost_al_dia` hoy solo publica ediciones y el índice del buscador. Hay que enseñarle a rehacer la agenda cuando cambie `data/eventos/`.
- El tema de Ghost sigue sin versionar (`ghost/theme/` no existe). Esto condiciona la dirección de las fichas (decisión 3).

## Qué cambia

1. **Datos.** Colección nueva `data/eventos/<inicio>-<slug>.json`, separada de `data/agenda/`, con los campos del encargo. Los temas de la agenda (10, con su color en el mapa), los formatos, las modalidades y los estados van en `verticals/movilidad.json → agenda`, nunca en el código. Módulo `src/eventos.py` con `validar · listar · alta · pasar-a-pasado`. Sin fuente con fecha, sin fecha, sin tema válido o sin territorio de la taxonomía, el evento no pasa.
2. **Página pública `moticias.com/agenda/`** (`src/ghost_agenda.py`, patrón de `src/ghost_grupo.py`):
   - de arriba abajo, como en la maqueta: título y respuesta directa calculada (citas y ciudades del periodo); mapa con pestañas de meses, «Por lugar» y leyenda-filtro por tema; «Quitar filtros»; «Ordenar la lista» (tema por defecto, o fecha); la lista;
   - una línea con los temas sin citas;
   - columna lateral: «¿Organizas una jornada del sector?» → «Subir mi evento», calendario `.ics`, «Con fecha por confirmar», «Después de…»;
   - pie con la última comprobación y el aviso de confirmar en la web oficial;
   - todo el contenido va en el HTML que sirve Ghost (también la lista y «Por lugar»); el script del pie solo añade los filtros;
   - datos estructurados `ItemList` + `FAQPage` en la página y `Event` en cada ficha;
   - «Agenda» en el menú principal, en `llms.txt` y en el índice del buscador. Calendario en `app.moticias.com/feed/agenda.ics`, junto a los feeds del widget.
   - Periodo: de hoy a tres meses. Lo anterior pasa al archivo, `moticias.com/agenda/archivo/`.
3. **Mapa** con el contorno y la proyección de `portal/spain.js`, sin librerías de mapas: una marca por ciudad, el color es el tema, el número cuando hay varias citas, blanca con aro discontinuo si mezcla temas, Canarias en su recuadro. Mes, ciudad y tema se combinan y los contadores se recalculan. El color nunca es la única pista. Botones de verdad, utilizables con teclado, de 44 px. En el móvil, «Por lugar» baja debajo del mapa.
4. **«Subir mi evento»** (`moticias.com/agenda/subir-mi-evento/`): el formulario de cuatro bloques de la maqueta, con los tres permisos separados. Responsable del tratamiento: Avionline S.L. El envío va a `app.moticias.com/api/agenda` (Vercel) y de ahí a la base privada (tabla `agenda_envios`, migración 012), con campo trampa, tiempo mínimo de rellenado y límite por origen. Avisa al editor jefe con enlace a la cola; el remitente recibe acuse y, al publicarse, el enlace a su ficha. Nada de lo que sube un tercero se publica solo.
5. **Gestor, pestaña «Agenda»** (móvil):
   - «Por revisar», con vista previa, comprobación del enlace y aviso de posible duplicado;
   - acciones sueltas o en bloque: publicar, editar, pedir datos, fecha por confirmar, aplazado, cancelado, retirar y restaurar. Publicar y retirar, solo el editor jefe (403 en el servidor);
   - «Publicados», con filtros y la última comprobación;
   - «Organizadores y responsables», con los seis contadores, y la ficha del CRM al pulsar;
   - alta manual por la redacción;
   - el ✎ de `m.js` también en cada cita de la web.
6. **CRM.** Publicar un evento crea o actualiza la cuenta de cada entidad organizadora (`origen: agenda`, etiqueta `organizador-eventos`), la persona responsable si está identificada, una actividad `evento_agenda` y un siguiente paso con fecha («Evento dentro de 14 días: acreditación de prensa o propuesta de difusión»). Respeta «No contactar».
   - **Regla del contacto más cercano:** tabla nueva `crm_contactos` (cuenta, persona opcional, canal, valor, nivel `directo · prensa · general · centralita`, URL de fuente y fecha). Si no hay ninguno, la ficha queda «por localizar».
   - Estados en la tabla: «Contacto general», «Contacto general · falta responsable», «Falta contacto».
   - Los permisos del formulario se guardan tal como se marcaron, con fecha y texto (`permiso_correo_at`, `permiso_correo_como`).
7. **Panel de actividades: bloque «Agenda»** (dónde, decisión 2): citas de los próximos 14 días, pendientes de revisar, eventos sin responsable, entidades sin contacto, enlaces de inscripción caídos, cambios de fecha o sede detectados y el último barrido. Cada cifra abre su lista.
8. **Mantenimiento en la nube:**
   - comando `/agenda-barrido` y su tarea semanal (Opus). Busca eventos nuevos, vuelve a comprobar fecha, sede y enlace de los publicados y completa contactos. Lo nuevo entra como `propuesto` y los cambios como aviso. Escribe `data/` por el buzón y los contactos, directos a la base privada;
   - el cron `comprobar` visita también, cada día laborable, los enlaces de inscripción;
   - al pasar la fecha de fin, el evento sale de la página. Además, el barrido lo marca `pasado` y queda en el archivo, sin borrarse.
9. **Documentación** en el mismo cambio: `CLAUDE.md`, `docs/gestores-portal.md`, `docs/arquitectura.md`, `docs/manual-operativo.md`, `docs/puesta-en-marcha.md`, la spec `openspec/specs/agenda-de-eventos/` y una nota en `openspec/specs/boe-y-agenda/` sobre plazos frente a eventos.

## Semilla

- **12 eventos en el periodo, 3 con fecha por confirmar y 3 justo después.** Se vuelven a comprobar en la web de cada organizador antes de publicar; cuatro empiezan el 17-19 de noviembre. Lo que no se pueda comprobar se dice («sede por anunciar», «hora sin publicar»).
- **Los 15 contactos del CRM**, con nombres, correos y teléfonos, van **solo** a Supabase. Ni en el repositorio, ni en esta propuesta, ni en las pruebas. Una prueba automática busca en el repositorio cada nombre, correo y teléfono de la semilla y tiene que dar cero.

## Qué no cambia

- `data/agenda/`, «Próximos plazos» y «Sucederá pronto» siguen como están.
- Ninguna fecha, sede o enlace se publica sin comprobarlo en la fuente del organizador.
- Nada se borra.
- Un contacto público no es permiso comercial, y «No contactar» es para siempre.
- Subdirectorio, nunca subdominio (salvo `app.moticias.com` para el formulario, como ya es la regla).
- Firma, aprobación y tipos de contenido no cambian. Si algún día hay eventos destacados de pago, llevan «Contenido patrocinado · <cliente>» y `rel="sponsored"`, y no alteran el orden.

## Decisiones de Rainer

1. **El nombre.** Recomendado: `data/agenda/` se queda como está, con «Próximos plazos» y «Sucederá pronto» como nombres visibles, y los eventos van en `data/eventos/`. No se renombra nada de lo que ya funciona.
2. **Qué pantalla es el «panel de actividades».** En el gestor no existe ninguna con ese nombre. Dos opciones:
   - **A.** Un bloque «Agenda» dentro de «Hoy y esta semana» del CRM.
   - **B.** Una pantalla de inicio nueva del gestor, «Inicio», con la actividad de todas las áreas: el bloque «Agenda» completo y, de las demás, las cifras que el gestor ya calcula (piezas pendientes, retoques abiertos, enlaces de publicidad caídos, envíos de prensa por aprobar, pasos de hoy del CRM).
   - **Recomendado: B.** Es lo que se entiende por «panel». Lo de las otras áreas solo se enseña, no se reprograma.
3. **La dirección de cada ficha.** Ghost, sin tema propio, no admite páginas dentro de otra (`/agenda/ibtm-world-2026/`) salvo con su fichero de rutas (`routes.yaml`). Dos opciones:
   - **A. Rutas de Ghost.** Las fichas quedan en `moticias.com/agenda/<evento>/` y la agenda en `moticias.com/agenda/`. Cada ficha es una entrada de Ghost con etiqueta interna `#agenda`, fuera de la portada, del RSS y de los boletines. Para eso hay que añadir unas líneas al fichero de rutas de Ghost; antes se descarga el actual para no perder nada. Lo intento por la API; si Ghost no deja subirlo con la clave de integración, te doy el fichero y tres toques en Ajustes → Labs → Rutas, una sola vez.
   - **B. Sin tocar rutas.** Una página de Ghost por ficha con dirección `moticias.com/agenda-<evento>/`, fuera de `/agenda/`. Si más adelante se pasa a A, hay que redirigir todas las direcciones, y eso resta en buscadores.
   - **Recomendado: A.** La dirección no cambia nunca, que es lo que pide el SEO.
4. **El barrido.** Recomendado: **lunes a las 09:41**, después de la edición diaria y fuera de la hora punta de las tareas. Fuentes de arranque (en `verticals/movilidad.json → agenda.fuentes`, ampliables):
   - el calendario de ferias de la AFE (Asociación de Ferias Españolas);
   - los recintos: IFEMA, Fira Barcelona, FYCMA, Feria Valencia, Feria de Zaragoza, BEC, Palacio de Congresos de Canarias, FIBES;
   - las asociaciones: Asociación Española de la Carretera, ANFAC, ITS España, Railway Innovation Hub, Fundación Conama, AVIA, Confebus, APETAM/FEDINTRA, ATUC, Mafex, AEDIVE, Spain Convention Bureau;
   - la agenda de los ministerios de Transportes y de Turismo.
5. **Ferias de público general.** Recomendado: **solo profesionales**, más las grandes del sector con jornadas profesionales (como FITUR), marcadas «Abierta al público». Las de consumo puro (salones de caravanas, ferias de viajes para particulares) no entran.
6. **Eventos destacados de pago.** Recomendado: **más adelante**. Ahora solo se deja el campo `destacado` preparado, sin uso, para que añadirlo luego no obligue a rehacer nada.
7. **Clics simulados en las cajas de contenido patrocinado** (lo pediste en el mismo encargo; va en un cambio aparte, `comprobador-diario`).
   - **a) Mejorar el SEO de los anunciantes: no lo voy a hacer.** Por tres razones:
     - Google no ve esas visitas: no les sube ni un puesto.
     - Si se contaran como clics, la cifra que ve el anunciante sería falsa. Eso es fraude publicitario y pone en riesgo la credibilidad de MOTICIAS, que es lo que vende.
     - Contradice tu propia regla del 9-11 (`seguimiento-y-seo`): ni robots ni comprobador cuentan como lectores.
   - **b) Que el panel de publicidad demuestre que los enlaces funcionan: sí, y ya existe a medias.**
     - Hoy el comprobador visita cada enlace una vez al día laborable, a una hora al azar entre las 8 y las 20, y lo apunta aparte de los clics de lectores.
     - Propongo que lo haga **también sábados y domingos**, siempre a una hora al azar entre las 9 y las 21 (hora de Madrid).
     - El panel enseñará en cada caja «Comprobado hoy a las HH:MM · funciona / no funciona», con un historial de 30 días que se puede descargar para el anunciante.
     - Si un enlace falla dos veces seguidas, te llega un correo.
   - **Recomendado: b, en ese cambio aparte**, que aplico en cuanto me digas «sí».
