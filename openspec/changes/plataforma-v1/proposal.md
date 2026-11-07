# Cambio: plataforma-v1 — sala de redacción, suscripciones, CRM, promoción, sensores y verticales

Estado: propuesto (7-11-2026). Origen: reflexiones del director en `docs/estrategia.md`.

## Por qué

MOTICIAS produce ya contenido de referencia (74 piezas en tres ediciones), pero no tiene todavía la capa que convierte ese contenido en credibilidad medible, suscriptores con perfil, leads cualificados para MUFMI, MOVENBUS, MOVO y la nueva línea de planes de movilidad, ni canales señalizados para promocionar soluciones. Tampoco tiene gestión editorial desde el móvil, ni un asesor que proponga mejoras, ni sensores reutilizables por Amarantia. Hay que construir esa capa una sola vez, modular, para que el vertical de turismo («viajar en grupo») sea configuración y no un segundo desarrollo.

## Qué cambia

1. **Sala de redacción** (`app/`, aplicación web): cola de aprobación y repriorización desde el móvil, edición de piezas, campañas y ediciones a medida, publicidad y patrocinios, CRM, panel del asesor. Stack: Next.js (App Router) + Supabase (Postgres, Auth, RLS) + Vercel: el mismo que MOVO, para no mantener dos formas de hacer lo mismo y reutilizar lo aprendido allí (seguridad, despliegue, auditoría semanal).
2. **Publicación en moticias.com** con Ghost(Pro) por Admin API (`src/ghost_publish.py`): web pública, miembros y boletines; el repositorio sigue siendo la fuente de verdad del contenido.
3. **Suscripciones** en tres niveles más anunciante, con perfilado progresivo y consentimientos separados.
4. **CRM y leads** en Supabase: contactos, organizaciones, intereses, señales de comportamiento, puntuación por segmento y por solución del grupo, anunciantes y campañas.
5. **Promoción discreta y publicidad**: huecos señalizados (ya definidos en `docs/gestores-portal.md`), fichas de soluciones, casos, ediciones a medida, botón «Valorar con MOVO»; nunca en el texto editorial.
5 bis. **Campañas temáticas**: gestor de campañas con tema, fecha gancho, plan editorial, peso en los barridos, solución asociada, monetización (sin publicidad, patrocinada, banner o mixta) y KPI, para trabajar a fondo un tema cuando se acerca un plazo y medir los leads que trae. Primera: «Movilidad al trabajo: la cuenta atrás de los PMST» (MOVO a los rezagados).
6. **Sensores compartidos**: toda búsqueda de los agentes produce señales estructuradas en una tabla común (`senales`) que leen MOTICIAS, Amarantia y el hub Inteligencia de MOVO.
7. **Asesor de visibilidad y credibilidad**: comando `/consejo-visibilidad` y tarea semanal (lunes 09:17) que entrega a editores y superadmins ideas e instrucciones priorizadas.
8. **Verticales**: `verticals/<id>.json` con todo lo específico; el código lee la configuración.

## Fuera de alcance (por ahora)

Pasarela de pago propia (la lleva Ghost para suscripciones y MOVO/Stripe para servicios); app móvil nativa (la sala de redacción es web responsive); generación de vídeo.

## Riesgos

- Construir demasiado antes de tener suscriptores: por eso el orden de `tasks.md` empieza por lo que ya produce valor (Ghost, aprobación, asesor, sensores) y deja CRM avanzado y publicidad para cuando haya tráfico.
- Mezclar editorial y comercial: la spec de publicidad-promoción prohíbe promoción en el texto y exige señalización.
- Datos personales: RGPD y LSSI desde el diseño (consentimientos separados, responsable del tratamiento por decidir).
