# Capacidad: fotos

## Requisito: licencia y crédito
Cada pieza lleva una foto con licencia libre (CC BY, CC BY-SA, CC0, dominio público) y crédito visible (`image.credit`, `license`, `source`), o `image: null` si no existe ninguna pertinente.

## Requisito: pertinencia
La foto muestra el sujeto concreto de la pieza (el tren, el buque de esa naviera, la estación, la sede), ≥ 1000 px de ancho, sin rostros reconocibles, sin menores, sin fotos de prensa ni de agencias. Se mira antes de elegir.

## Requisito: no repetir
Una misma foto no aparece dos veces en la misma página del portal; si coincide, el portal usa una ilustración de sección.

## Requisito: almacenamiento
Se redimensiona a 1600 px (JPEG 82), se sube al artefacto (`/_blob/<assetId>`) y se guarda copia en `portal/img/b-<assetId>.jpg` con su crédito en `portal/img/credits.json`.
