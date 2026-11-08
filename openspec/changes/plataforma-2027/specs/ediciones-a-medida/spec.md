# Capacidad: ediciones a medida, revistas y widget (delta)

## ADDED Requisito: perfil de cliente
Cada edición a medida tiene un `perfil` (tipos de pieza, secciones, subsectores, etiquetas incluidas y excluidas, palabras clave, campañas, idioma, número máximo, periodo, cadencia, marca, destinatarios, revisores). El mismo perfil alimenta la página privada, el correo, el PDF y el widget. Se edita en la sala de redacción, no en código.

## ADDED Requisito: selector de contenidos
Módulo común (`app/lib/selector`) que, dado un perfil, devuelve piezas, boletines, plazos y señales ordenados por relevancia y fecha, leyendo `data/` y la Content API de Ghost. Lo usan ediciones a medida, widget, empaquetador, difusión de comunicados, radar y asesor.

## ADDED Requisito: contenido del cliente
El cliente puede aportar piezas propias; se maquetan igual y se marcan «Contenido de <cliente>». Nunca se mezclan sin marca con las de MOTICIAS ni entran en la web pública.

## ADDED Requisito: empaquetador con revisión previa
Según la cadencia del perfil, `/edicion-a-medida <perfil>` genera la selección, crea un documento colaborativo de Claude con selección y textos, lo comparte con los revisores y espera aprobación; aprobado, publica la página privada `app.moticias.com/ediciones/<cliente>`, el correo (plantilla Brevo con la cabecera del cliente) y el PDF (portada, sumario, piezas con fuentes, agenda de plazos), generado en Python en la propia tarea.

#### Escenario: revista mensual de una asociación
- CUANDO llega el día de cadencia de un perfil con revisores designados
- ENTONCES el documento de revisión se crea antes de las 08:00 y el envío solo se produce tras la aprobación en el documento o en la sala.

## ADDED Requisito: widget embebible
`app.moticias.com/widget.js` pinta en cualquier web una lista de titulares filtrada por atributos `data-*` (sector, etiquetas, número), leyendo la Content API pública de Ghost, con estilo neutro, enlace a cada pieza y marca «Powered by MOTICIAS» con enlace. Es gratuito y no requiere clave.

## ADDED Requisito: gratis y de pago
Gratis lo que trae enlaces y lectores (widget); de pago lo que requiere horas o exclusividad (revistas, ediciones privadas, informes). Las métricas que ve el cliente: lecturas, clics y altas atribuidas a su edición.
