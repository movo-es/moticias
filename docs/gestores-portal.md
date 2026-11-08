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
  - Cuaderno del director: análisis y reportajes.
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
- Los huecos sin campaña de pago se rellenan con autopromoción (en `data/ads/`):
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
- Una sola barra: menús Modo · Tema · Territorio (con mapa de comunidades), botón «Análisis del director» y lupa. Cada menú cuenta las piezas con los demás filtros puestos.
- Buscador con sinónimos del sector, topónimo como filtro, comunidades vecinas cuando no hay nada y corrección de erratas; sin resultado, «Pídela» (pieza bajo demanda).
- Módulo fijo «Análisis del director» en la portada (columna derecha en escritorio; segunda tarjeta en móvil). En móvil, sin textos de presentación ni resúmenes: foto, modo · territorio y titular.
- Etiquetas de Ghost con slug fijo: `m-<submodo>`, `tema-<id>`, `t-<territorio>` (`ghost_publish.py --etiquetas` las crea; cada una con descripción, que sale en `llms.txt`).
- Maqueta navegable: `openspec/changes/navegacion-y-buscador/maqueta/`.
