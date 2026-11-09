# Método del informe de repercusión de MOTICIAS

Respuesta corta: contamos como impacto solo lo que podemos probar que procede de su nota (con enlace, fecha y el fragmento de texto que coincide), damos el alcance solo con la audiencia que el propio medio declara, estimamos impactos como una horquilla con coeficientes que publicamos aquí, y no calculamos valor publicitario equivalente. Lo que no hemos podido leer no está en el informe, y el informe lo dice.

## 1. Cómo detectamos

Desde el día de publicación, en los días 1, 2, 3, 5, 7, 10, 14, 21 y 30 (`verticals/movilidad.json → prensa.impacto.calendario_dias`):

1. Búsquedas exactas en buscadores: el titular entre comillas, tres frases distintivas de ocho palabras de la nota, el comienzo de la cita del portavoz, y el nombre de la organización junto a cada cifra de la nota.
2. Lectura de la portada o el RSS de los medios de la base de prensa que recibieron la nota.
3. Alertas que el cliente o MOTICIAS tengan configuradas para el nombre de la organización.
4. Lo que el cliente nos envíe (recortes, enlaces): se verifica igual que lo demás.

No llegamos a: contenido tras muro de pago que no podamos leer, prensa en papel, radio, televisión, boletines por correo que no recibamos, y redes sociales cerradas. Por eso hablamos de impactos **detectados**.

## 2. Cómo verificamos

Cada página candidata se compara con la nota frase a frase (secuencias de seis palabras, sin tildes ni mayúsculas):

| Tipo | Regla | Entra en el informe |
|---|---|---|
| Reproducción | Al menos el 50 % de las secuencias de la nota aparecen en la página, con el nombre de la organización y fecha igual o posterior a la publicación (o al fin del embargo) | Sí, automáticamente |
| Adaptación | Entre el 15 % y el 50 %, o la cita literal del portavoz, con nombre y fecha válida | Sí, automáticamente |
| Mención | Nombre de la organización más una cifra o un término propio de la nota, sin texto de la nota | Solo cuando una persona la ha revisado |
| Descartada | Sin el nombre de la organización; anterior a la nota; páginas de MOTICIAS o del propio emisor | No |

Una misma pieza con dos direcciones (con y sin parámetros de seguimiento, o la misma pieza del mismo medio con otra URL) cuenta una vez. Si el mismo texto aparece en varios medios (sindicación), cuenta en cada medio y se señala.

## 3. Alcance potencial

Es la suma de la audiencia que cada medio con impacto **declara** (kit de medios, OJD/PGD, página de publicidad), con su fuente y fecha en la ficha del medio de la base de prensa (`medios.audiencia`). Cada medio cuenta una vez aunque publique dos piezas. Un medio sin audiencia declarada aparece en el informe pero no suma.

## 4. Impactos estimados

Es una horquilla, no una medición. Se calcula por impacto, multiplicando la audiencia declarada por un coeficiente según el tipo de medio:

- **Web**: entre el 0,2 % y el 1 % de los usuarios únicos mensuales del medio ve una pieza concreta de su sección de noticias (hipótesis prudente para medios sectoriales).
- **Boletín por correo**: suscriptores × tasa de apertura (25–45 %, la habitual en boletines B2B sectoriales; si el medio declara la suya, se usa la suya).
- **Redes sociales**: las impresiones reales que da la plataforma; sin ese dato, no se estima.
- **Agencias**: no tienen audiencia propia; cuentan las reproducciones detectadas en sus clientes.

Los coeficientes son hipótesis de método, declaradas al cliente en cada informe, y se revisan con los datos propios de MOTICIAS (Brevo y Ghost) cuando haya serie suficiente.

## 5. Métricas medidas

Las de MOTICIAS se miden, no se estiman: envíos, entregas, aperturas, clics, respuestas, rebotes y bajas de la difusión (estados de Brevo en `prensa_destinatarios`); impresiones de las publicaciones en LinkedIn (las anota el director con su fuente y fecha); clics al enlace del cliente (parámetros UTM, si el cliente nos da acceso a su analítica o nos pasa la cifra).

## 6. Lo que no hacemos

- **Valor publicitario equivalente (AVE).** Los Principios de Barcelona 3.0 de AMEC (2020) establecen que el AVE no es el valor de la comunicación.
- Sumar audiencias que el medio no declara, ni multiplicar por factores de «credibilidad».
- Contar como impacto una página que no hemos leído.
- Dar por buena una mención sin revisión humana.

## 7. Código

`src/prensa_impacto.py` (consultas, clasificación, alcance, informe) y el comando `/prensa-impacto`. Los impactos verificados se guardan en `prensa_coberturas` de la base de prensa, donde además cuentan para la colaboración y la probabilidad de publicación de cada medio. Umbrales y coeficientes en `verticals/movilidad.json → prensa.impacto`.
