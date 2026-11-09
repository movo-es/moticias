# Base de contactos de la sala de prensa: bases legales y límites

**Borrador para revisión por un abogado antes del primer envío a periodistas.** Ni Rainer ni Claude son abogados; este documento ordena las decisiones y deja escrita la evaluación de interés legítimo que exige el RGPD, pero no sustituye a un asesoramiento profesional.

Respuesta corta: a redacciones y periodistas del sector se les escribe por interés legítimo, solo con notas de su especialidad y con baja en un clic; a todos los demás (decisores, profesionales, lectores), solo con su consentimiento. Los contactos importados de LinkedIn que no son prensa no reciben nada hasta que se dan de alta ellos mismos.

## 1. Responsable y dónde están los datos

Responsable: Avionline S.L. (titular de MOTICIAS). Los contactos viven en el repositorio privado `movo-es/moticias-equipo` (`prensa/contactos.json`), nunca en el repositorio público; después, en Supabase (migración `003_sala_de_prensa.sql`) con acceso restringido. Se registra para cada contacto: origen, base legal, consentimiento (fecha y texto), envíos y bajas. Las bajas no se borran: se conservan para no volver a escribir.

## 2. Bases por tipo

| Tipo | Base | Notas |
|---|---|---|
| Redacción (dirección que el medio publica para recibir información) | Interés legítimo (RGPD 6.1.f) | Es una dirección profesional publicada para este fin |
| Periodista, editor de boletín | Interés legítimo (RGPD 6.1.f) | Solo notas de su especialidad (filtro de relevancia), máximo 2 por semana, baja en cada correo; información del art. 14 en el primer envío |
| Decisor B2B, profesional | Consentimiento | Casilla «Recibir notas de prensa de mi sector» en MOTICIAS (Ghost) o en el formulario de la sala de prensa |
| Particular (B2C) | Consentimiento | Newsletter «Notas de prensa» de Ghost con etiquetas de sector; solo resumen semanal |

## 3. Evaluación de interés legítimo (periodistas y redacciones)

1. **Interés.** Hacer llegar a profesionales de la información comunicados del sector que cubren, que es parte de su trabajo y del de MOTICIAS como sala de prensa.
2. **Necesidad.** El envío individual a su dirección profesional es el medio habitual y menos intrusivo; no hay una alternativa menos invasiva con el mismo efecto.
3. **Ponderación.** Datos solo profesionales (nombre, cargo, medio, correo de trabajo); expectativa razonable: un periodista sectorial espera recibir comunicados de su sector; salvaguardas: filtro de relevancia (un periodista de ferrocarril no recibe notas de autobús), tope semanal, pausa automática a quien no abre 6 envíos seguidos, baja inmediata total o por sector, información clara en cada correo.

## 4. LSSI (art. 21)

Las comunicaciones comerciales por correo exigen consentimiento previo. Una nota de prensa enviada a un periodista es información para su trabajo, no una oferta comercial a él; aun así, por prudencia, **ningún contacto que no sea de prensa recibe nada sin consentimiento**, y los correos de MOTICIAS a clientes potenciales (por ejemplo, a directores de comunicación que aparezcan en la base) no se envían desde esta herramienta.

## 5. LinkedIn

Solo se usa la exportación oficial de los contactos de Rainer (`Connections.csv`). No se rastrean perfiles ni se automatizan mensajes: lo prohíben las condiciones de LinkedIn. Los contactos que son prensa entran por interés legítimo; los demás quedan `pendiente-opt-in` y se les invita una vez, desde el perfil de Rainer (mensaje o publicación con el enlace de alta), no por correo masivo.

## 6. Pendiente de revisar con el abogado

- Texto de información del art. 14 en el primer envío a periodistas.
- Plazo de conservación de bajas y de registros de envío (propuesto: 24 meses para envíos; bajas, indefinido como lista de exclusión).
- Encaje del resumen semanal B2C con la política de privacidad de `docs/legal/privacidad.md`.
