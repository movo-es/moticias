# Cambio: sala-de-prensa-v1

Fecha: 9 de noviembre de 2026 (mediodía). Origen: encargo de Rainer. Adelanta y amplía `notas-de-prensa-v1` (estrategia 2027, § 4.1, previsto para la semana 47), que queda absorbido por este cambio.

## Por qué

Rainer: «Crea una plataforma de difusión de noticias y notas de prensa. A un cliente de pago que quiera dar visibilidad a su lanzamiento o noticia le ofrecemos el broadcast automático de su nota de prensa a nuestros contactos en los medios, newsletters y redes sociales. Saldrá en nuestra lista de "Notas de prensa" segmentada por modo de transporte, tema y región. Opcionalmente podrá contratar presencia publicitaria o contenido patrocinado. Un sistema que ayude al cliente a afinar contenido, tono y longitud —un asesor de comunicación virtual— y a elegir con honestidad las mejores opciones para difundir, publicitar o patrocinar. Debe recibir un informe de lo que va saliendo a raíz de su nota en otros medios y newsletters, con la repercusión, el alcance y los impactos estimados, como cualquier informe de medios profesional. Esta parte nos hará ganar más dinero que las suscripciones. Crea desde ya una base de datos a la que se puedan enviar las notas, B2B y B2C, con la plataforma filtrando para que lo que llegue de MOTICIAS siempre se vea como valor, aunque lleve la etiqueta "nota de prensa". Puedes usar mi LinkedIn.»

## Qué cambia

**Unido a `prensa-y-medios` el 9-11-2026 (noche)**: la base de contactos, los envíos y las coberturas son los de la base de prensa de Supabase; la sala de prensa pone encima el asesor, el filtro de valor, la página de clientes, los pedidos (`prensa_notas`, migración 007) y el informe. Los puntos 4 y 5 quedan así.

1. **Lista pública «Notas de prensa»** en `moticias.com/notas-de-prensa/`, con los tres ejes de siempre (modo · tema · territorio, `verticals/movilidad.json → taxonomia`): cada nota lleva las etiquetas `m-`, `tema-` y `t-`, así que se filtra igual que las piezas. Marca visible «Nota de prensa · Comunicado de empresa · no es contenido editorial de MOTICIAS». Nunca en la portada editorial ni en el boletín diario (regla de siempre).
2. **Asesor de comunicación virtual** (`src/prensa_asesor.py`; página `app.moticias.com/prensa/`): puntúa la nota en cinco dimensiones (noticiabilidad, estructura, claridad, tono, datos y verificabilidad), señala cada problema con la frase concreta, propone titular y entradilla answer-first, y dice lo que falta. Con la API de Claude, además, reescritura sugerida que **no añade hechos** (los huecos se marcan `[DATO]`).
3. **Recomendador honesto** (mismo módulo): cruza la nota con la audiencia real que hay en la base de contactos para ese modo y territorio y recomienda un plan —o dice que no merece la pena pagar—: «con esta audiencia, Publicación gratuita basta», «esto no es una nota de prensa, es publicidad: le conviene contenido patrocinado», «falta el dato que lo hace noticia».
4. **Destinatarios**: los medios y periodistas de la base de prensa (`prensa-y-medios`), filtrados por `src/prensa_valor.py`; lectores B2C, solo por el boletín «Notas de prensa» de Ghost.
5. **LinkedIn**: de la exportación oficial (`Connections.csv`) salen los periodistas de medios que ya están en la base, con su fuente, para cargarlos con `src/prensa.py sql`. Sin rastreo automático ni mensajes automáticos: lo prohíben las condiciones de LinkedIn y pondría en riesgo la cuenta de Rainer.
6. **Difusión con filtro de valor** (`src/prensa_difusion.py`): tres puertas, borrador en `prensa_envios` con el motivo de cada destinatario y «Por qué le llega», aviso a quien aprueba (editor jefe; la oficina en notas pagadas de clientes) y envío desde la pestaña «Prensa» del gestor; resumen semanal B2C por Ghost.
7. **Informe de repercusión** (`src/prensa_impacto.py`, comando `/prensa-impacto`): detección por huellas del texto, cita, cifras y nombre; cada impacto con URL, fecha, medio, tipo (reproducción, adaptación, mención) y evidencia; alcance potencial solo con audiencia declarada y su fuente; impactos estimados como horquilla con método declarado; métricas propias medidas (Ghost, Brevo, clics). Sin AVE. Lo dudoso no entra en el informe sin revisión humana: **cero falsos positivos** es el compromiso; la exhaustividad se declara como «detectado por estos métodos».
8. **Oferta comercial** en `verticals/movilidad.json → prensa` (planes y visibilidad, tarifas de lanzamiento como hipótesis) y texto público en `docs/prensa/oferta.md`.

## Qué no cambia

Un comunicado nunca es noticia sin verificación independiente; si tiene un hecho con valor, entra como candidata y la redacción lo trata con sus propias fuentes. El cortafuegos editorial-comercial se mantiene: pagar compra difusión y visibilidad, nunca cobertura editorial. Nada se borra: retirar es `retirada`.

## Qué verás tú

- `app.moticias.com/prensa/`: pegas una nota, el asesor la puntúa al momento y te dice qué plan conviene y por qué.
- En la pestaña «Prensa» del gestor: el borrador de cada difusión con sus destinatarios y el motivo de cada uno, para aprobar desde el móvil.
- Un informe de repercusión de ejemplo generado sobre una nota ficticia de prueba (`openspec/changes/sala-de-prensa-v1/ejemplo/`).
