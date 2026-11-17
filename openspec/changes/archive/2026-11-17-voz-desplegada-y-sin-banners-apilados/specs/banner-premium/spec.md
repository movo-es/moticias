### Requisito: nunca dos cajas una encima de otra (cambio `voz-desplegada-y-sin-banners-apilados`, 17-11-2026)
En ninguna página quedan dos cajas de publicidad, patrocinio o «Contenido patrocinado» seguidas en vertical sin contenido entre ellas (texto visible, imagen o vídeo). Se queda la de más rango (contenido patrocinado del texto > pagada > del grupo o de la plantilla) y, a igualdad, la de arriba; la otra se quita con su hueco. Las que van una al lado de otra no cuentan.

#### Escenario: pie de una sección
- DADO una sección cuyo último bloque es una caja y un hueco básico «antes del pie» con otra
- CUANDO se pinta la página
- ENTONCES solo queda una caja al pie

### Requisito: la caja de una sección va delante (17-11-2026)
En las páginas de sección la publicidad sabe en qué sección está, como en los artículos. Entre cajas del mismo rango, la que está pensada para esa sección (`sections`) va delante de las genéricas.

#### Escenario: MOVO bajo «La voz del editor»
- DADO la caja `grupo-movo-pmst-a-tiempo` activa para `la-voz-del-editor` en el hueco estándar
- CUANDO un lector abre `/la-voz-del-editor/` antes del 6-12-2026
- ENTONCES bajo la columna ve esa caja, con «Contenido patrocinado», y ninguna otra encima o debajo de ella
