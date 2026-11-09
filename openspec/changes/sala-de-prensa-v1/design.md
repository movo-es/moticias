# Diseño: sala-de-prensa-v1

Respuesta corta: la nota entra (formulario o buzón), el asesor la puntúa y recomienda un plan, se publica marcada en `/notas-de-prensa/` con los tres ejes, y si el cliente paga difusión sale a los contactos que pasan tres filtros de valor, con aprobación humana. Desde ese día, `/prensa-impacto` busca lo que se publica a raíz de ella y el cliente recibe un informe con cada impacto probado, su alcance con fuente y una estimación de impactos con método declarado.

## 1. Flujo

```
cliente ─► app.moticias.com/prensa/ (asesor en vivo, plan) ─► api/prensa.py ─► moticias-equipo/prensa/entrantes/<id>.json
buzón prensa@ ─► /prensa-buzon ─────────────────────────────────────────────┘
                         │ verificación del emisor (dominio corporativo o enlace)
                         ▼
          data/notas-de-prensa/<id>.json (público: lo que se publica)  +  moticias-equipo/prensa/pedidos/<id>.json (privado: plan, contacto, pago, valoración)
                         │
       src/prensa_publicar.py ─► Ghost /notas-de-prensa/<slug>/ (tags notas-de-prensa, #comunicado, m-, tema-, t-)
                         │ (si el plan incluye difusión)
       src/prensa_difusion.py planificar ─► plan con destinatarios y motivos ─► aprobación (director u oficina) ─► enviar (Brevo, etiqueta np-<id>)
                         │
       /prensa-impacto (laborables) ─► consultas ─► candidatos ─► src/prensa_impacto.py clasificar ─► revisión de dudosos ─► informe HTML ─► cliente
```

## 2. Dónde vive cada dato

| Dato | Dónde | Por qué |
|---|---|---|
| Nota publicada (título, cuerpo, organización, ejes, fecha, huellas) | `data/notas-de-prensa/<id>.json` | Es público por naturaleza; el repositorio es la fuente de verdad |
| Catálogo de medios y newsletters (nombre, web, tipo, ejes, audiencia declarada con fuente, página de contacto) | `data/medios/<id>.json` | Datos de organizaciones, públicos |
| Contactos con nombre, correo, cargo, consentimiento | `movo-es/moticias-equipo/prensa/contactos.json` | Datos personales: el repositorio público no los admite (regla de siempre) |
| Pedido (plan, contacto del cliente, valoración del asesor, plan de difusión, aprobación, envíos) | `moticias-equipo/prensa/pedidos/<id>.json` | La valoración se entrega solo al emisor |
| Impactos detectados y revisados, informe | `moticias-equipo/prensa/impacto/<id>.json` y `informes/<id>-<fecha>.html` | Es del cliente |
| Más adelante | Supabase, migración `003_sala_de_prensa.sql` (borrador incluido) | Cuando exista el proyecto `moticias` (semana 48) |

Los scripts reciben la carpeta privada con `--privado <ruta>` (por defecto `work/privado/prensa`, que una tarea programada rellena clonando `movo-es/moticias-equipo`). Si la carpeta no existe, los scripts lo dicen y no inventan contactos.

## 3. Bases legales (borrador para revisión por un abogado; Rainer no es abogado ni lo es Claude)

| Tipo de contacto | Ejemplos | Base | Qué recibe | Cómo se da de baja |
|---|---|---|---|---|
| `redaccion` | redaccion@medio.es publicada en su web | Interés legítimo: envío de información profesional a la dirección que el medio publica para recibirla | Notas de su modo y territorio | Enlace en cada correo; la baja es inmediata y por sector o total |
| `periodista` | Redactor de un medio del sector | Interés legítimo documentado (RGPD art. 6.1.f; evaluación en `docs/prensa/legal-contactos.md`); información del art. 14 en el primer envío | Notas de su especialidad, máximo 2 por semana | Ídem |
| `newsletter` | Editor de un boletín sectorial | Ídem que periodista | Ídem | Ídem |
| `decisor-b2b` | Director de operaciones de un operador, técnico de movilidad de un ayuntamiento | **Consentimiento** (alta en MOTICIAS con la casilla «Recibir notas de prensa de mi sector») | Una por semana como máximo | Centro de preferencias de Ghost |
| `profesional` | Lector profesional suscrito | Consentimiento | Resumen semanal | Ídem |
| `particular` | Lector B2C | Consentimiento (newsletter «Notas de prensa» de Ghost con etiquetas de sector) | Resumen semanal | Ídem |

Contactos importados de LinkedIn: los que son periodistas o redacciones entran como tales (interés legítimo, con información en el primer envío); los demás entran como `pendiente-opt-in` y **no reciben notas** hasta que se den de alta ellos mismos. A esos se les invita una sola vez, desde el perfil de Rainer (mensaje o publicación en LinkedIn con el enlace de alta), no por correo masivo: la LSSI (art. 21) exige consentimiento previo para comunicaciones comerciales por correo.

## 4. Filtro de valor (lo que hace que una nota de MOTICIAS se lea)

1. **Puerta de la nota.** Solo se difunde si el asesor da ≥ 60 (≥ 70 en Plus). Por debajo, el cliente recibe la lista de arreglos; se publica gratis igualmente si tiene hecho noticiable.
2. **Puerta del destinatario.** Relevancia = coincidencias entre los ejes de la nota y los intereses del contacto (submodo 3, medio de todo el transporte 2, solo el modo 1, territorio 2, ámbito estatal 1, tema 1; un medio internacional resta 2 ante una noticia autonómica). Se envía con relevancia ≥ 3: un periodista de ferrocarril no recibe una nota de autobús. Los intereses salen de lo que el contacto declaró, del medio en el que trabaja o, si son inferidos del cargo, se marcan como inferidos y pesan la mitad.
3. **Puerta de la frecuencia.** Máximo de envíos por semana por tipo (`prensa.filtro_valor.max_envios_semana`); quien no abre en 6 envíos seguidos queda en pausa (no se le borra).
4. **Formato.** Asunto `Nota de prensa · <modo> · <territorio>: <titular>`; arriba, tres líneas «Por qué le llega» redactadas por MOTICIAS (qué, a quién afecta, dato clave), después la nota tal cual, contacto de prensa, adjuntos enlazados (nunca adjuntos pesados), baja por sector. B2C nunca recibe una nota suelta: recibe el resumen semanal.
5. **Horario.** Laborables de 08:30 a 11:30.

## 5. Asesor de comunicación

Determinista (siempre, sin coste, sin red): longitud del titular, entradilla (¿responde qué, quién, dónde y cuándo en ≤ 60 palabras?), longitud del cuerpo y de los párrafos, cita atribuida con nombre y cargo, cifras, fechas absolutas, bloque «Sobre …», contacto de prensa, palabras de humo, anglicismos, superlativos que hay que probar, densidad promocional (primera persona del plural, exclamaciones, mayúsculas), ejes detectados con `src/taxonomia.py`. Cada aviso cita la frase concreta.

Noticiabilidad (0–30): hay hecho fechado; hay cifra (importe, viajeros, plazas, kilómetros, flota, empleo); interviene una administración o hay contrato, concesión o norma; afecta a usuarios o al sector más allá de la empresa; es primero o único (si lo prueba); coincide con un tema con actividad reciente en MOTICIAS. Lo noticiable lo decide el hecho, no el adjetivo.

Con `ANTHROPIC_API_KEY`: segunda pasada que devuelve titular y entradilla alternativos, versión recortada y las tres preguntas que hará un periodista. Instrucción cerrada: no añadir hechos, cifras ni citas; marcar `[DATO]`.

Recomendador: cuenta destinatarios reales que pasan las puertas 2 y 3 por tipo, y medios del catálogo para esos ejes. Reglas, en este orden: (a) si la nota es promoción de producto sin hecho → contenido patrocinado o nada; (b) si puntuación < 60 → arreglos y Publicación; (c) si destinatarios < mínimo del plan → Publicación y decirlo con el número; (d) si ámbito local → Difusión solo si hay medios de ese territorio; (e) Plus solo si hay interés regional o estatal y ≥ 30 destinatarios. Publicidad solo si el objetivo declarado es presencia sostenida. Cada recomendación lleva su porqué en una frase.

## 6. Informe de repercusión

**Detección.** Huellas de la nota: título exacto, la cita entre comillas, cada cifra con su unidad, frases distintivas de seis palabras, nombre de la organización con sus alias. El agente busca con WebSearch (frases exactas entre comillas, nombre + cifra, nombre + tema), lee los RSS de `data/medios/` y las alertas que existan, y guarda cada candidato (URL, título, fecha, texto) en `work/prensa/impacto/<id>/`. El script clasifica:

- `reproduccion`: ≥ 50 % de las frases de seis palabras de la nota aparecen en la página.
- `adaptacion`: entre el 15 % y el 50 %, o la cita literal, más el nombre de la organización.
- `mencion`: nombre de la organización más una cifra o término propio de la nota, con contención < 15 %.
- `descartado`: sin nombre de la organización, o publicado antes que la nota (o del fin del embargo), o página de MOTICIAS o del propio emisor.

Las reproducciones y adaptaciones con fecha válida quedan `verificado` automáticamente; las menciones quedan `revisar` y solo entran en el informe cuando una persona las marca. Duplicados: misma URL canónica o mismo medio y título → uno. Sindicación (mismo texto en varios medios) se cuenta por medio y se señala.

**Alcance.** Por impacto: audiencia del medio solo si está declarada (fuente y fecha en `data/medios/`); si no lo está, «audiencia no declarada» y el impacto cuenta pero no suma alcance. **Impactos estimados**: horquilla = audiencia × coeficiente del tipo de medio (`prensa.impacto.coeficientes`, declarados en el propio informe). **Medidos**: visitas a la nota en MOTICIAS, aperturas y clics de los envíos (Brevo, etiqueta `np-<id>`), clics al enlace del cliente (UTM), impresiones de LinkedIn que Rainer anote.

**Lo que el informe nunca hace:** valor publicitario equivalente; sumar audiencias sin fuente; contar como impacto una página que no se ha leído; dar por buena una mención sin revisión.

## 7. LinkedIn

Lo que sí: (1) Rainer descarga su archivo de datos (Configuración → Privacidad de datos → Obtener una copia de tus datos → Contactos), que llega como `Connections.csv` (nombre, apellidos, URL, correo solo si el contacto lo permite, empresa, cargo, fecha de conexión); (2) `src/contactos.py importar-linkedin` lo clasifica; (3) `/promo-social` prepara la publicación de cada nota difundida para su perfil y para la página de MOTICIAS, y Rainer la publica. Lo que no: rastrear perfiles, automatizar mensajes o publicaciones con su sesión.

## 8. Precios

Hipótesis de lanzamiento en `verticals/movilidad.json → prensa.planes` (0 / 190 / 390 € y bono de 1.900 €), dentro de las horquillas de la estrategia 2027. No se publican como tarifa hasta que Rainer las confirme. El cobro, como en `notas-de-prensa-v2` (enero), por MOVO; hasta entonces, factura de Avionline.
