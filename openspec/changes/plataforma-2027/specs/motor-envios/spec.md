# Capacidad: motor de envíos (delta)

## ADDED Requisito: canales y adaptadores
Correo y SMS por Brevo; WhatsApp Business y voz por Twilio; newsletters editoriales siguen en Ghost. Cada canal es un adaptador con la misma interfaz (enviar, estado, acuse, baja). Remitentes por cliente configurables.

## ADDED Requisito: plantillas y segmentos
Plantillas con variables y, en WhatsApp, aprobadas por Meta antes de usarse. Segmentos definidos sobre `contacts`, `interests`, `cargos` y audiencias de PLUS. Ningún envío sin plantilla ni sin segmento.

## ADDED Requisito: estado por destinatario y acuses
`envios` (id, ejecucion_id, destinatario, canal, plantilla, estado: enviado | entregado | leído | acusado | fallido | baja, intentos, at). Acuse: enlace en correo y SMS, botón en WhatsApp, tecla en voz. Reintentos por canal y, si falla, siguiente canal del paso si lo hay.

## ADDED Requisito: secuencias durables
Una secuencia es una lista ordenada de pasos (segmento, canales, plantilla, condición de avance: tiempo, porcentaje de acuses, aprobación humana). Se ejecuta en Vercel Workflow: cada paso sobrevive a reinicios y puede pararse en cualquier momento.

#### Escenario: paso con acuse
- CUANDO un paso exige el 80 % de acuses o 20 minutos
- ENTONCES el siguiente paso no empieza hasta cumplirse una de las dos condiciones, y el panel muestra en tiempo real quién ha acusado.

## ADDED Requisito: horario, bajas y registro
Nada no urgente entre 22:00 y 8:00; toda baja se respeta en todos los canales; registro completo con retención de 24 meses.

## ADDED Requisito: usuarios del motor
PLUS, difusión de comunicados, alertas de licitaciones y de señales, boletines de ediciones a medida. Ningún producto envía por su cuenta.
