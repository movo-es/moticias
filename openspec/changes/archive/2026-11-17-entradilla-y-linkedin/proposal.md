# Cambio: entradilla-y-linkedin

Fecha: 17 de noviembre de 2026. Origen: petición de Rainer del 17-11-2026 por la noche, con una captura de la página «Autobús y autocar» de moticias.com («Abajo se corta el texto de la entradilla abruptamente. Ten cuidado con eso, no generes entradillas que no quepan en el resumen. Crea en el gestor del editor un botón compartir en LinkedIn (con la imagen y la entradilla y un enlace "suscríbete gratis para seguir leyendo: moticias.com - noticias con M de movilidad y transportes")»). Estado: aplicado.

## Por qué
La tarjeta de la captura acababa en «—ferrocarr». No era un caso suelto: Ghost guarda como mucho 300 caracteres en el resumen de un post (`custom_excerpt`) y `src/ghost_publish.py` mandaba los 300 primeros caracteres del bloque «De qué trata» (`summary`, que tiene 60–110 palabras). Las 103 piezas tenían un `summary` de más de 300 caracteres (entre 305 y 836): todas las tarjetas de moticias.com terminaban a media frase y muchas a media palabra.

## Decisiones
1. **Campo propio.** Cada pieza lleva `entradilla`: el texto de las tarjetas, de los listados, del resumen de Ghost y de lo que se comparte. Frases completas, un párrafo, como mucho 280 caracteres (20 de margen sobre los 300 de Ghost), acabada en punto, sin puntos suspensivos y solo con hechos que están en la pieza. El `summary` no cambia: sigue abriendo la pieza.
2. **Se escribe para caber, no se recorta.** La redacción la escribe con la pieza (`docs/tarea-edicion-diaria.md` y los comandos que escriben piezas); `src/entradilla.py validar` para la rutina si falta, no cabe o no acaba en frase.
3. **Red de seguridad.** Ningún texto se corta ya a media palabra en ningún sitio: si una pieza llegara sin entradilla válida, se usan las frases completas de su `summary` que quepan y, solo si ni la primera cabe, un corte por palabra con «…». Lo mismo en la descripción para buscadores, en las fichas de la agenda y en las notas de prensa, que cortaban igual.
4. **Las 103 piezas, arregladas.** 76 con las primeras frases completas de su `summary`; 27, cuya primera frase no cabía, escritas a mano con los mismos hechos (comprobado: ninguna cifra que no esté en la pieza). No es una corrección de contenido: no añade `revised_at`.
5. **Ghost al día sin republicar.** El cron `web_reintentos` (cada 20 minutos) compara la entradilla de cada pieza con el resumen que tiene Ghost y cambia solo el resumen de los que no coinciden; lee la pieza fresca del repositorio antes de escribir.
6. **En el editor del gestor.** Campo «Entradilla» con contador; el servidor no guarda la que no cabe. «Otro enfoque con IA» propone también la entradilla y, si la de la IA no vale, se sustituye por frases completas.
7. **Compartir en LinkedIn.** Tarjeta en la ficha de cada pieza publicada del gestor y entrada en el menú ✎ de moticias.com. Texto: entradilla + «Suscríbete gratis para seguir leyendo: <enlace a la pieza>» + «moticias.com - Noticias con M de Movilidad y Transportes», editable antes de compartir. El enlace va a la pieza (con `utm_source=linkedin`), no a la portada: es lo que hace que LinkedIn ponga la tarjeta con la foto y el titular, y lo que deja al lector donde puede seguir leyendo y suscribirse.
8. **La imagen la pone LinkedIn.** Un enlace de compartir no admite una imagen: sale en la tarjeta del enlace, con la foto de la pieza. Subir la foto como imagen suelta exigiría publicar por la API de LinkedIn con una aplicación autorizada; queda fuera (y la regla de la casa es que en LinkedIn nada se publica solo).
9. **Cómo se abre.** El redactor de LinkedIn con el texto ya escrito solo funciona en el ordenador y LinkedIn no lo documenta; por eso el botón copia siempre el texto antes de abrir, y en el móvil usa el menú de compartir del teléfono.

## Qué no cambia
El `summary` y los cinco bloques, la firma, la aprobación, quién publica. La regla de LinkedIn de la sala de prensa (nada de rastreo ni mensajes automáticos).

## Lo que queda para Rainer
- Probar el botón con una pieza: `https://app.moticias.com/gestor/?vista=piezas` → abrir una → «Compartir en LinkedIn».
- Si prefiere otro texto fijo o que el enlace lleve a la portada, se cambia en `verticals/movilidad.json → redes.linkedin` sin tocar código.
