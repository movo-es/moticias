# Cambio: voz-desde-el-panel

Fecha: 16 de noviembre de 2026. Origen: petición de Rainer del 16-11-2026 a mediodía («quiero que la voz del editor ya exista y que en el panel tenga facilidad de ponerlo; crea uno con una visión nuestra de PMST, la dificultad de las pymes»). Estado: aplicado.

## Por qué
«La voz del editor» existía en el menú y en el gestor desde esa mañana, pero vacía: solo podía llenarse con las propuestas de los sábados y lo aprobado no salía hasta el lunes. El editor jefe no tenía cómo poner una columna cuando quisiera.

## Decisiones
1. **Tarjeta siempre visible** arriba de la «Cola» del editor jefe, con «+ Nueva columna» y enlace directo (`?vista=cola&voz=nueva`).
2. **Dos caminos**: «Encargar el borrador» (tema y enfoque → redacción horaria, sin tabla nueva: un encargo de `encargos_gestor` que empieza por «LA VOZ DEL EDITOR · columna de opinión») y «Escribirla yo» (la pieza pendiente se crea en el momento).
3. **Aprobar para ahora o para el lunes.** Sigue marcado el lunes a las 08:00, que es la regla; «Publicar ahora» es una elección expresa del editor jefe. Sin aprobación no se publica nada: no cambia.
4. **Temas del grupo por encargo.** La tarea de los sábados sigue sin elegirlos; si los encarga el editor jefe, se escriben con la relación declarada por su nombre en la nota de intereses, sin nombrar el servicio en el texto y sin cajas de contenido patrocinado (`src/menciones.py` excluye también `kind: opinion`).
5. **Imagen.** La candidata se ve en la tarjeta desde el repositorio aunque no esté en Ghost; al publicar, si el despliegue no lleva `portal/img/`, `src/ghost_publish.py` la baja del repositorio y la sube.
6. **Primera columna**: «El polígono no tiene plan» (`data/articles/el-poligono-no-tiene-plan-v7kd.json`), pendiente de la aprobación del editor jefe.

## Qué no cambia
La firma, la marca «Opinión · La voz del editor», el cupo (no cuenta), la tarea de los sábados, «Pedir otra versión» y que solo el editor jefe aprueba.

## Lo que queda para Rainer
- Leer y aprobar la primera columna en `https://app.moticias.com/gestor/?vista=cola`.
- Dos afirmaciones del texto dicen «no nos consta» (criterios del artículo 25 y cifra oficial de centros obligados): confirmarlas o corregirlas con lo que él sepa.
