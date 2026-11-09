# Diseño: sala-de-prensa-v1

**Unión con `prensa-y-medios` (9-11-2026, noche; decisión de Rainer: «lo unes tú sobre su base»).** No hay lista de contactos propia de la sala de prensa: los destinatarios son los medios y periodistas de la base de prensa (Supabase «moticias», migración 005, `src/prensa.py`); el plan de difusión es un envío en borrador de esa base y se aprueba y envía en la pestaña «Prensa» del gestor; las coberturas verificadas van a `prensa_coberturas`; los pedidos, a `prensa_notas` (migración 007). Donde este documento dice otra cosa, manda este párrafo.

Respuesta corta: la nota entra (formulario o buzón), el asesor la puntúa y recomienda un plan, se publica marcada en `/notas-de-prensa/` con los tres ejes, y si el cliente paga difusión sale a los contactos que pasan tres filtros de valor, con aprobación humana. Desde ese día, `/prensa-impacto` busca lo que se publica a raíz de ella y el cliente recibe un informe con cada impacto probado, su alcance con fuente y una estimación de impactos con método declarado.

## 1. Flujo

```
cliente ─► app.moticias.com/prensa/ (asesor en vivo, plan) ─► api/prensa.py ─► CRM (cuenta + persona) + prensa_notas (recibida)
buzón prensa@ ─► /prensa-buzon ──────────────────────────────────────────────┘
                         │ verificación del emisor (dominio corporativo o enlace)
                         ▼
          src/prensa_publicar.py ─► data/notas-de-prensa/<id>.json + Ghost /notas-de-prensa/ (tags notas-de-prensa, #comunicado, m-, tema-, t-)
                         │ (si el plan incluye difusión)
          src/prensa_difusion.py planificar ─► prensa_envios (borrador) + prensa_destinatarios con motivo ─► aviso
                         │ aprobación en la pestaña «Prensa» del gestor (editor jefe; oficina si es nota de cliente) ─► Brevo (src/prensa.py)
                         ▼
          /prensa-impacto (laborables) ─► candidatos ─► src/prensa_impacto.py ─► prensa_coberturas (verificados) ─► informe al día por enlace firmado
```

## 2. Dónde vive cada dato

| Dato | Dónde |
|---|---|
| Nota publicada (título, cuerpo, organización, ejes, fechas, huellas) | `data/notas-de-prensa/<id>.json` (público) |
| Pedido: cliente (cuenta y persona del CRM), plan, valoración del asesor, verificación, consentimientos, envío, candidatos y métricas del informe | `prensa_notas` (migración 007) |
| Medios, periodistas, redacciones, audiencias declaradas con fuente | base de prensa (`medios`, `periodistas`; migración 005) |
| Difusión: envío, destinatarios con su motivo, estados de Brevo | `prensa_envios`, `prensa_destinatarios` (005) |
| Impactos verificados | `prensa_coberturas` (005, ampliada en la 007 con tipo, estado, evidencia, contención y revisión) |

## 3. Bases legales

Las de la base de prensa (`prensa-y-medios`): solo datos profesionales publicados por el medio, por el periodista o en documentos públicos, cada uno con su fuente (art. 19 LOPDGDD); «No contactar» para siempre; baja firmada en cada envío; responsable Avionline S.L. La sala de prensa añade el filtro de relevancia y el tope semanal. Los lectores (B2C) solo reciben el resumen semanal del boletín de Ghost al que se suscribieron. Detalle y puntos para el abogado: `docs/prensa/legal-contactos.md`.

## 4. Filtro de valor (lo que hace que una nota de MOTICIAS se lea)

1. **Puerta de la nota.** Solo se difunde si el asesor da ≥ 60 (≥ 70 en Plus). Por debajo, el cliente recibe la lista de arreglos; se publica gratis igualmente si tiene hecho noticiable.
2. **Puerta del destinatario** (`src/prensa_valor.py`). Relevancia del medio = ámbito exacto del submodo 3 (o ámbito genérico del modo 2; en Plus, generalistas, económicos, regionales y agencias 2), tema 1, territorio: medio regional de la comunidad de la nota 2, nacional 1, internacional 1 o −2 ante una noticia autonómica, regional de otra comunidad −10. Se envía con relevancia ≥ 3 a sus periodistas con correo y a su buzón de notas: un periodista de ferrocarril no recibe una nota de autobús. Fuera los medios y periodistas «poco colaboradores» y quien está en «No contactar».
3. **Puerta de la frecuencia.** Máximo de notas por semana: 2 por periodista, 3 por buzón de redacción (`prensa.filtro_valor.max_envios_semana`, contadas en `prensa_destinatarios`). Quien recibe sin publicar ni responder pasa a «poco colaborador» con el recálculo de la base y sale solo.
4. **Formato.** Asunto `Nota de prensa · <modo> · <territorio>: <titular>`; arriba, la marca de comunicado y tres líneas «Por qué le llega» (qué, a quién afecta, dato clave; editables en el pedido), después la nota tal cual, contacto de prensa y enlace a la nota con UTM; pie y baja los de `src/prensa.py`. B2C nunca recibe una nota suelta: recibe el resumen semanal del boletín «Notas de prensa» de Ghost (un correo por modo a la etiqueta `np-<modo>`).
6. **Aprobación.** El editor jefe, o la oficina si la nota es de un cliente (decisión de Rainer, 9-11-2026; permiso `notas_clientes`); los envíos en nombre de MOTICIAS, solo el editor jefe.
5. **Horario.** Laborables de 08:30 a 11:30.

## 5. Asesor de comunicación

Determinista (siempre, sin coste, sin red): longitud del titular, entradilla (¿responde qué, quién, dónde y cuándo en ≤ 60 palabras?), longitud del cuerpo y de los párrafos, cita atribuida con nombre y cargo, cifras, fechas absolutas, bloque «Sobre …», contacto de prensa, palabras de humo, anglicismos, superlativos que hay que probar, densidad promocional (primera persona del plural, exclamaciones, mayúsculas), ejes detectados con `src/taxonomia.py`. Cada aviso cita la frase concreta.

Noticiabilidad (0–30): hay hecho fechado; hay cifra (importe, viajeros, plazas, kilómetros, flota, empleo); interviene una administración o hay contrato, concesión o norma; afecta a usuarios o al sector más allá de la empresa; es primero o único (si lo prueba); coincide con un tema con actividad reciente en MOTICIAS. Lo noticiable lo decide el hecho, no el adjetivo.

Con `ANTHROPIC_API_KEY`: segunda pasada que devuelve titular y entradilla alternativos, versión recortada y las tres preguntas que hará un periodista. Instrucción cerrada: no añadir hechos, cifras ni citas; marcar `[DATO]`.

Recomendador: cuenta destinatarios reales que pasan las puertas 2 y 3 por tipo, y medios del catálogo para esos ejes. Reglas, en este orden: (a) si la nota es promoción de producto sin hecho → contenido patrocinado o nada; (b) si puntuación < 60 → arreglos y Publicación; (c) si destinatarios < mínimo del plan → Publicación y decirlo con el número; (d) si ámbito local → Difusión solo si hay medios de ese territorio; (e) Plus solo si hay interés regional o estatal y ≥ 30 destinatarios. Publicidad solo si el objetivo declarado es presencia sostenida. Cada recomendación lleva su porqué en una frase.

## 6. Informe de repercusión

**Detección.** Huellas de la nota: título exacto, la cita entre comillas, cada cifra con su unidad, frases distintivas de seis palabras, nombre de la organización con sus alias. El agente busca con WebSearch (frases exactas entre comillas, nombre + cifra, nombre + tema), lee la portada o el RSS de los medios que recibieron la nota y las alertas que existan, y guarda cada candidato (URL, título, fecha, texto) en `work/prensa/impacto/<id>/`. El script clasifica:

- `reproduccion`: ≥ 50 % de las frases de seis palabras de la nota aparecen en la página.
- `adaptacion`: entre el 15 % y el 50 %, o la cita literal, más el nombre de la organización.
- `mencion`: nombre de la organización más una cifra o término propio de la nota, con contención < 15 %.
- `descartado`: sin nombre de la organización, o publicado antes que la nota (o del fin del embargo), o página de MOTICIAS o del propio emisor.

Las reproducciones y adaptaciones con fecha válida quedan `verificado` automáticamente; las menciones quedan `revisar` y solo entran en el informe cuando una persona las marca. Duplicados: misma URL canónica o mismo medio y título → uno. Sindicación (mismo texto en varios medios) se cuenta por medio y se señala.

**Alcance.** Por impacto: audiencia del medio solo si está declarada en su ficha de la base (`medios.audiencia` con `fuente`); si no lo está, «audiencia no declarada» y el impacto cuenta pero no suma alcance. **Impactos estimados**: horquilla = audiencia × coeficiente del tipo de medio (`prensa.impacto.coeficientes`, declarados en el propio informe). **Medidos**: aperturas, clics, respuestas, rebotes y bajas de los envíos (`prensa_destinatarios`, estados de Brevo), clics al enlace del cliente (UTM), impresiones de LinkedIn que Rainer anote.

**Lo que el informe nunca hace:** valor publicitario equivalente; sumar audiencias sin fuente; contar como impacto una página que no se ha leído; dar por buena una mención sin revisión.

## 7. LinkedIn

Lo que sí: (1) Rainer descarga su archivo de datos (Configuración → Privacidad de datos → Obtener una copia de tus datos → Contactos), que llega como `Connections.csv`; (2) `python3 -I src/prensa_valor.py linkedin Connections.csv` saca los periodistas de medios que ya están en la base, con rol y fuente («contacto de primer grado de Rainer Uphoff, exportación oficial»), en el formato de `src/prensa.py validar|sql`, y aparte cuenta los contactos de comunicación (clientes potenciales, que no entran en la base de prensa); (3) se cargan con el conector de Supabase como hace `/medios-actualizar`; (4) `/promo-social` prepara la publicación de cada nota difundida para su perfil y Rainer la publica. Lo que no: rastrear perfiles, automatizar mensajes o publicaciones con su sesión.

## 8. Precios

Tarifas de lanzamiento confirmadas por Rainer el 9-11-2026 (más IVA) en `verticals/movilidad.json → prensa.planes`: 0 / 190 / 390 € y bono de 1.900 €; `tarifas_publicas: true`. El cobro, como en `notas-de-prensa-v2` (enero), por MOVO; hasta entonces, factura de Avionline.
