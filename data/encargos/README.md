# Encargos de piezas bajo demanda (`data/encargos/`)

Cola de consultas de clientes que el buscador no pudo resolver con lo publicado. Las atiende `/pieza-bajo-demanda` (tarea programada «MOTICIAS · piezas bajo demanda», laborables cada dos horas de 8 a 20, y a mano cuando Rainer pasa una consulta). Especificación: `openspec/changes/plataforma-2027/specs/buscador-bajo-demanda/spec.md`.

**El repositorio es público: aquí no entra ningún dato personal.** Un encargo guarda la consulta y el identificador de miembro de Ghost (`miembro_id`, opaco); el correo del solicitante se consulta en la Admin API de Ghost en el momento de avisarle y no se escribe en ningún fichero. Cuando exista Supabase (`sala-de-redaccion-v1`), la cola se muda a la tabla `encargos` y esta carpeta queda como histórico.

## Formato (`<AAAA-MM-DD>-<slug-de-la-consulta>.json`)

```json
{
 "id": "2026-11-09-concesiones-autobus-aragon-vencen",
 "consulta": "¿Qué concesiones de autobús de Aragón vencen en 2027 y quién las licita?",
 "creado_en": "2026-11-09T10:12:00+01:00",
 "origen": "buscador" | "manual" | "correo",
 "solicitante": {"miembro_id": "<uuid de Ghost o null>", "nivel": "lector" | "profesional" | "corporativa" | "casa"},
 "estado": "pendiente" | "respondido" | "publicada" | "pendiente_aprobacion" | "sin_fuentes" | "descartado",
 "respuesta": {"tipo": "existente" | "nueva" | "sin_fuentes", "piezas": ["<id>"], "urls": ["https://www.moticias.com/<id>/"], "texto": "una o dos frases"},
 "cerrado_en": null,
 "notas": ""
}
```

Nunca se borra un encargo: descartar es `estado: descartado` con el motivo en `notas`. Cuota por nivel en `verticals/movilidad.json → encargos.cuota`.
