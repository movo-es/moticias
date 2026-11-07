---
description: Radar regulatorio semanal (lunes) — expedientes, consultas públicas, transposiciones y plazos con fecha límite
---

Eres la redacción de MOTICIAS (vertical $ARGUMENTS, por defecto `movilidad`). Produce el **Radar regulatorio** de la semana: una pieza `kind: "noticia"`, `section: "regulacion"`, `kicker: "Radar regulatorio · Semana N"`, según `docs/estandar-profundidad.md` y las reglas de `docs/tarea-edicion-diaria.md` (fuentes primarias con fecha, nada inventado, lectura web sin aprobaciones).

Fuentes, en este orden: `src/boe_sweep.py --desde <lunes anterior> --hasta <hoy>` (disposiciones y anuncios, no licitaciones); el buscador de participación pública del Ministerio de Transportes (consulta previa, audiencia e información pública, con fechas de inicio y fin); DOUE/EUR-Lex (serie L) y «Have your say» de la Comisión (TRANSPORT); CNMC (consultas y resoluciones ferroviarias y aeroportuarias); boletines autonómicos listados en `docs/fuentes.md` cuando su RSS responda; `data/agenda/` para los plazos ya conocidos.

Estructura del cuerpo: apertura con los tres expedientes que más afectan al sector esta semana; después secciones «Estatal», «Autonómico», «Europa», «Consultas abiertas» (lista con fecha límite), «Transposiciones pendientes», «Lo que hay que vigilar». Cada expediente: qué es, a quién afecta, fecha límite, enlace primario. Añade a `data/agenda/` todo plazo nuevo (`kind: consulta | vigor | plazo`, `edicion: hoy`). Guarda la pieza en `data/articles/` y, si el portal está disponible, en su base; registra en `docs/ediciones.md` una línea «Radar regulatorio»; commit y push. Aviso corto al terminar.
