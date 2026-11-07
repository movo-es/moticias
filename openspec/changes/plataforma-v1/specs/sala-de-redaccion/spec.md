# Capacidad: sala de redacción (delta)

## ADDED Requisito: aprobación desde el móvil solo para lo crítico
Las piezas rutinarias se publican sin pasar por la sala. La sala muestra las piezas `pendiente` (críticas y análisis del director) con vista previa completa y el motivo (`review_note`), y permite Publicar, Retirar y cambiar el orden y el destacado con controles usables con el pulgar.

## ADDED Requisito: corrección rápida
En el visor del editor, cada pieza publicada tiene a un toque «Editar» y «Retirar» (retirar = `status: retirado`, desaparece de la web y del boletín siguiente; nunca se borra del repositorio).

#### Escenario: aprobar una pieza
- CUANDO el superadministrador pulsa Publicar en una pieza pendiente
- ENTONCES la pieza pasa a `publicado`, se publica en Ghost y queda registrado quién y cuándo.

## ADDED Requisito: edición de una pieza
Se pueden editar título, subtítulo, bloques, cuerpo, foto, estado, destacado, relación con soluciones y relación con segmentos; cada cambio en una pieza publicada añade `revised_at` y nota de corrección.

## ADDED Requisito: roles
superadmin (todo), editor (piezas y ediciones), comercial (CRM, anunciantes, campañas), anunciante (solo sus campañas y métricas). Todo acceso con autenticación y RLS por `vertical_id` y rol.
