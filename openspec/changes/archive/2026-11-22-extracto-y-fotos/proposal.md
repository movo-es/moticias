# Cambio: extracto-y-fotos

Fecha: 22 de noviembre de 2026. Origen: dos defectos vistos al comprobar «El polígono no tiene plan» en la web; visto bueno de Rainer («hazlo»). Estado: aplicado.

## Qué pasaba
1. **Entradilla cortada.** Ghost admite 300 caracteres y el código cortaba el resumen en el carácter 300, a media palabra («La solución está en el pl»). Los 116 resúmenes pasan de 300: pasaba en todas las piezas.
2. **Sin foto en la sección.** La foto de la columna no estaba en `portal/img/ghost-urls.json` y el índice de las secciones la daba sin imagen. Lo mismo en una pieza del 17-11.
3. **Fotos subidas una y otra vez.** El gestor en Vercel no lleva `portal/` (`.vercelignore`) y no veía esa lista: desde el 16-11 (cuando empezó a bajar las fotos del repositorio) subía cada foto de nuevo en cada republicación («…-6.jpg»). No se veía en la web, pero llenaba el almacén de Ghost.

## Decisiones
1. `extracto()`: corta al final de la última frase que cabe; si ninguna cabe, en palabra entera con «…».
2. `urls_fotos()` lee la lista del repositorio cuando el despliegue no la lleva; `_anotar_fotos()` apunta en el repositorio cada foto recién subida.
3. Se anotan las dos fotos que faltaban y se rehace el índice.
4. `FORMATO` pasa a 4: el cron `ghost_al_dia` republica todas las piezas (20 por pasada) y con ello sus entradillas.

## Qué no cambia
El texto de ninguna pieza: el `summary` aprobado se conserva entero; solo cambia por dónde se corta al mandarlo a Ghost.

## Pendiente
Las copias repetidas de fotos que ya hay en el almacén de Ghost no se borran aquí (nada se borra sin decisión del editor jefe).
