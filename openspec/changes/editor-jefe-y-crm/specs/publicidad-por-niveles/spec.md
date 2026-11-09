# Publicidad y patrocinios por niveles

## ADDED Requisito: niveles y huecos
`verticals/movilidad.json → publicidad`: premium (`cabecera`, `articulo-lateral`), estándar (`portada-medio`, `articulo-cierre`), básico (`pie`, `boletin`). Nunca dentro del texto de una pieza ni sobre la apertura.

## ADDED Requisito: caja
Etiqueta siempre visible (Publicidad, Patrocinio o Autopromoción, con el anunciante), titular, texto, enlace `https://` con UTM y `rel="sponsored"` si es pagada. Lo pagado va delante de la autopromoción; dentro, por nivel y peso; una caja no se repite en la misma página.

## ADDED Requisito: quién
Solo el editor jefe activa, pausa o termina. Los demás perfiles crean o retocan cajas en estado `propuesta`. El importe, el contacto y la factura van al CRM (`crm_contratos`), nunca al repositorio.
