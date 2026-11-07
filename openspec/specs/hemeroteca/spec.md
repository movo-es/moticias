# Capacidad: hemeroteca

## Requisito: archivo diario
Tras cerrar y verificar la edición, la rutina añade sus piezas, boletines, plazos y edición a `hemeroteca/data/AAAA-MM.json` y actualiza `data/index.json` con `src/hemeroteca_build.py daily`, y publica solo los ficheros cambiados en el artefacto de la hemeroteca.

#### Escenario: fallo al publicar
- CUANDO la publicación de la hemeroteca falla
- ENTONCES se reintenta una sola vez y, si sigue fallando, se dice en el aviso; la edición del portal no se retrasa.

## Requisito: fidelidad
La hemeroteca conserva cada edición tal como quedó al cierre; una corrección posterior en el portal solo llega a la hemeroteca con una reconstrucción `full`.

## Requisito: tamaño
Cada fichero de mes queda por debajo de 16 MB.
