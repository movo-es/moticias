# Capacidad: menciones del grupo (delta sobre plataforma-2027)

## MODIFIED Requisito: la mención va en una caja «Contenido patrocinado» en medio del texto
Sustituye a «la mención va al pie, señalizada, una por pieza». Cada mención publicada se pinta como una caja `<aside class="contenido-patrocinado">` dentro de una tarjeta HTML de Ghost, insertada entre bloques del cuerpo, siempre después de un párrafo, una lista o una cita, nunca antes del primer bloque ni después del último: una caja hacia la mitad; dos cajas a un tercio y a dos tercios. La caja lleva la etiqueta `verticals/<id>.json → productos.label` («Contenido patrocinado»), el texto corto, el enlace con UTM y `rel="sponsored noopener"`, y la declaración `productos.declaracion` («<nombre> es un servicio de una empresa del grupo de MOTICIAS.»). Una pieza lleva como mucho `productos.max_por_pieza` cajas (2). El texto, el titular, el resumen y las fuentes no se tocan.

#### Escenario: pieza con una mención publicada
- CUANDO la pieza tiene una mención con `estado: publicada`
- ENTONCES el publicador pinta una caja hacia la mitad del cuerpo y nada al pie.

#### Escenario: mención exclusiva
- CUANDO la primera mención publicada tiene `exclusividad: exclusiva`
- ENTONCES solo se pinta esa caja, aunque haya otras publicadas.

## ADDED Requisito: posición de la caja (decisión de Rainer, 8-11-2026, 23:33)
Cada mención tiene `posicion`, editable en el gestor, y cada producto una posición por defecto: `premium` (tras el primer párrafo del cuerpo), `estandar` (entre el tercio y la mitad del texto: una caja hacia el 40 %, dos al tercio y a la mitad) y `referencia` (al final del texto, antes de las cifras clave). Sin campo, `estandar`. La caja lleva siempre enlace (si falta el texto del enlace, el nombre del producto), con `rel="sponsored noopener"`: es lo que Google pide para enlaces señalizados como patrocinados y protege a moticias.com de una penalización por esquema de enlaces.

## ADDED Requisito: cada cambio sube a la web al momento
Tras publicar una mención —de forma automática (rutina) o manual (gestor)— y tras cualquier cambio de texto, posición o estado, la pieza se actualiza en Ghost en el acto (`ghost_publish.republicar`, o `ghost_publish.py --ids`), lo que refresca su fecha de modificación y el sitemap. Si Ghost responde bien, la mención queda con `en_web: <fecha>`; si no, el gestor la muestra como «Falta en la web» y ofrece «Subir todo a la web ahora».

## ADDED Requisito: modo y exclusividad por producto
Cada producto tiene `modo` (`automatico` · `revision` · `manual` · `apagado`) y `exclusividad` (`exclusiva` · `compartida`). La propuesta automática (`src/menciones.py proponer`) solo considera productos en `automatico` o `revision` que superan su `umbral`; ordena por puntuación; si el primero es exclusivo, solo él; si no, añade los compartidos siguientes hasta `max_por_pieza`, saltando los exclusivos. `automatico` escribe `estado: publicada`; `revision` escribe `propuesta` (pendiente en el gestor). El tope semanal sigue convirtiendo en `propuesta`. Un producto sin `modo` toma `automatico` si está `activo` y `apagado` en otro caso.

#### Escenario: producto en revisión
- CUANDO un producto en `revision` supera el umbral en una pieza
- ENTONCES la mención queda `propuesta`, no se pinta y aparece en «Pendientes» del gestor y en el correo.

## MODIFIED Requisito: el director recibe cada mención con enlace al gestor
El correo diario de menciones lleva un botón «Abrir el gestor de patrocinios» y, por mención, «Gestionar» (`<gestor_url>?pieza=<id>`); GitHub y Ghost quedan como enlaces de respaldo.
