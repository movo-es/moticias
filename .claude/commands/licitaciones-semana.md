---
description: Licitaciones de la semana (viernes) — organismo, objeto, importe, plazo y concesiones que vencen, por sector y comunidad
---

Eres la redacción de MOTICIAS (vertical $ARGUMENTS, por defecto `movilidad`). Produce **Licitaciones de la semana**: una pieza `kind: "noticia"`, `section: "licitaciones"`, `kicker: "Licitaciones · Semana N"`, según `docs/estandar-profundidad.md` y las reglas de `docs/tarea-edicion-diaria.md`.

Fuentes: `src/boe_sweep.py --desde <lunes> --hasta <hoy>` (sección V-A y V-B: licitaciones, formalizaciones, concesiones, competencia de proyectos); TED (API v3, CPV de `verticals/<vertical>.json`, país ESP, últimos 7 días); PLACSP (Atom de perfiles de contratante, filtrando por CPV y palabras de transporte de viajeros); `data/agenda/` y `data/boletines/` para no repetir.

Estructura: apertura con los tres contratos de mayor importe o impacto; tabla en texto (sin tabla Markdown: lista `- ` con organismo · objeto · importe · plazo · enlace) por sector (autobús, ferrocarril, movilidad urbana, marítimo y puertos, aéreo, carreteras, logística) y, dentro, por comunidad; «Concesiones que vencen» (próximos 12 meses, con fuente); «Adjudicaciones y formalizaciones» de la semana (quién ganó y por cuánto frente al precio base); «Lo que hay que vigilar». Cada licitación relevante va además a `data/agenda/` (`kind: plazo`, `amount`, `amount_eur`, `edicion: hoy`) y a `data/boletines/` si viene del BOE. Marca en la pieza, como dato y no como texto, `relaciones_solucion` = `MOVO` (valoración de licitaciones) para que la plataforma muestre el servicio señalizado. Guarda, registra en `docs/ediciones.md`, commit y push. Aviso corto.
