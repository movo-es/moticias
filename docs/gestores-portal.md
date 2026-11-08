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
- Perfiles: superadministrador (todo) y oficina (cajas de las piezas, sin tocar productos ni publicidad).
- Piezas: pendientes, con caja, posibles y todas. En cada pieza: publicar, retirar, editar el texto, añadir a mano otro producto (con su puntuación contra la pieza), ver cómo queda en el texto y republicar en la web.
- Productos: cómo entra cada uno (automático con umbral, con revisión, solo a mano, apagado), exclusiva o comparte, umbral, máximo por semana, textos, URL y contexto.
- Publicidad: campañas de `data/ads/`, activar o pausar.
- El correo diario de menciones lleva «Gestionar» en cada pieza: abre el gestor en esa pieza.
- Cada cambio queda en el repositorio (commit) y se republica la pieza en Ghost al momento.

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
