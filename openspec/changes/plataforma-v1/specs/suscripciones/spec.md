# Capacidad: suscripciones (delta)

## ADDED Requisito: niveles
Cuatro niveles: `lector` (gratis: boletín, portada y primer tercio de cada reportaje), `profesional` (de pago: todo el contenido, radar regulatorio, licitaciones de la semana, calendario ICS, archivo), `corporativa` (de pago, para organizaciones: varios usuarios, alertas por comunidad y modo, edición a medida, datos descargables, informe semanal ejecutivo), `anunciante` (acceso a sus campañas y métricas). Precios en `verticals/<id>.json` cuando se fijen.

## ADDED Requisito: alta y perfilado progresivo
El alta pide correo, nombre, organización, cargo y tipo de entidad. Después, por centro de preferencias y segundo correo, modos, comunidades, tamaño, si licita, CIF y teléfono opcionales. Doble confirmación obligatoria.

## ADDED Requisito: consentimientos separados
Casilla 1 (obligatoria): boletines del vertical. Casilla 2 (opcional, separada): ofertas de las empresas del grupo, nombradas (MOVO, Movenbus, MUFMI y la nueva línea). Sin la casilla 2 no se usa el contacto para vender. Responsable del tratamiento en la política de privacidad.

#### Escenario: contacto sin casilla 2
- CUANDO un contacto no marcó la casilla 2
- ENTONCES aparece en el CRM con `consent_group_offers = false` y queda excluido de cualquier campaña comercial.
