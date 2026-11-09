# Base de contactos de la sala de prensa: bases legales y límites

**Borrador para revisión por un abogado antes del primer envío a periodistas.** Ni Rainer ni Claude son abogados; este documento ordena las decisiones y deja escrita la evaluación de interés legítimo que exige el RGPD, pero no sustituye a un asesoramiento profesional.

Respuesta corta: a redacciones y periodistas del sector se les escribe por interés legítimo, solo con notas de su especialidad y con baja en un clic; a todos los demás (decisores, profesionales, lectores), solo con su consentimiento. Los contactos importados de LinkedIn que no son prensa no reciben nada hasta que se dan de alta ellos mismos.

## 1. Responsable y dónde están los datos

Responsable: Avionline S.L. (titular de MOTICIAS). Los destinatarios son los de la base de prensa (Supabase «moticias», cambio `prensa-y-medios`): solo datos profesionales publicados por el propio medio, por el periodista o en documentos públicos, cada uno con su fuente (art. 19 LOPDGDD), «No contactar» para siempre y baja firmada en cada envío. Los clientes que envían notas quedan en el CRM (cuenta y persona) y su pedido en `prensa_notas`. Nada de esto está en el repositorio público.

## 2. Bases por tipo de destinatario

| Destinatario | Base | Notas |
|---|---|---|
| Buzón de redacción o de notas publicado por el medio | Interés legítimo (RGPD 6.1.f) | Dirección publicada para recibir información |
| Periodista, editor de boletín | Interés legítimo (RGPD 6.1.f) | Solo notas de su especialidad (filtro de relevancia ≥ 3), máximo 2 por semana, baja en cada correo, «No contactar» para siempre |
| Lector profesional o particular | Consentimiento | Boletín «Notas de prensa» de Ghost con sus sectores; solo resumen semanal |
| Cliente que envía una nota | Ejecución del encargo y, para comunicaciones de MOTICIAS, su casilla aparte | Queda en el CRM como empresa |

## 3. Evaluación de interés legítimo (periodistas y redacciones)

1. **Interés.** Hacer llegar a profesionales de la información comunicados del sector que cubren, que es parte de su trabajo y del de MOTICIAS como sala de prensa.
2. **Necesidad.** El envío individual a su dirección profesional es el medio habitual y menos intrusivo; no hay una alternativa menos invasiva con el mismo efecto.
3. **Ponderación.** Datos solo profesionales (nombre, cargo, medio, correo de trabajo); expectativa razonable: un periodista sectorial espera recibir comunicados de su sector; salvaguardas: filtro de relevancia (un periodista de ferrocarril no recibe notas de autobús), tope semanal, pausa automática a quien no abre 6 envíos seguidos, baja inmediata total o por sector, información clara en cada correo.

## 4. LSSI (art. 21)

Las comunicaciones comerciales por correo exigen consentimiento previo. Una nota de prensa enviada a un periodista es información para su trabajo, no una oferta comercial a él; aun así, por prudencia, **ningún contacto que no sea de prensa recibe nada sin consentimiento**, y los correos de MOTICIAS a clientes potenciales (por ejemplo, a directores de comunicación que aparezcan en la base) no se envían desde esta herramienta.

## 5. LinkedIn

Solo se usa la exportación oficial de los contactos de Rainer (`Connections.csv`), y de ella solo los periodistas de medios que ya están en la base, con la fuente «contacto de primer grado de Rainer Uphoff» (el correo, solo si el propio contacto lo comparte en LinkedIn). Los demás contactos no entran en la base de prensa: los directores de comunicación son clientes potenciales y se tratan, si acaso, en el CRM con su propia base legal. No se rastrean perfiles ni se automatizan mensajes: lo prohíben las condiciones de LinkedIn.

## 6. Pendiente de revisar con el abogado

- Texto de información del art. 14 en el primer envío a periodistas.
- Plazo de conservación de bajas y de registros de envío (propuesto: 24 meses para envíos; bajas, indefinido como lista de exclusión).
- Encaje del resumen semanal B2C con la política de privacidad de `docs/legal/privacidad.md`.
