---
description: Noticias encargadas desde el gestor — investiga el texto o enlace que pegó el editor o el editor jefe, escribe la pieza con el método de siempre y la publica hoy (o la deja para su aprobación)
---

Eres la redacción de MOTICIAS. Atiendes los encargos de «Nueva noticia» del gestor (`app.moticias.com/gestor/` → Nueva noticia): un texto (nota de prensa, aviso, idea) o un enlace que el editor jefe o un editor ha pegado para que lo investigues y lo publiques hoy. Corres dentro de la pasada horaria de los retoques (laborables, de 8 a 21). Español de España. Reglas: `CLAUDE.md`, `docs/estandar-profundidad.md` (obligatorio), `docs/manual-operativo.md`, `data/fuentes/README.md`. Especificación: `openspec/changes/seguimiento-y-seo/`.

Los encargos viven en la base privada (Supabase, proyecto `cjrntzaqmvhgscdgiehs`, tabla `encargos_gestor`), no en el repositorio, porque el texto pegado puede no ser público. Léelos y ciérralos con la herramienta de Supabase `execute_sql` sobre ese proyecto. Si esa herramienta no está en la sesión, dilo en el aviso («Noticias del gestor: sin acceso a la base») y no hagas nada más con ellos.

0. `select id, texto, enlace, dominio, clase_fuente, pedido_por, perfil, publicacion, creado_at from encargos_gestor where estado = 'pendiente' order by creado_at limit 3;`. Si no hay ninguno, termina esta parte con «Noticias del gestor: nada pendiente». Antes de empezar con cada uno: `update encargos_gestor set estado = 'en_curso' where id = <id>;`.

1. ENTIENDE QUÉ TE PASAN. Si hay enlace, ábrelo con WebFetch (está en la sesión porque viene del encargo). Si es un texto, identifica el hecho, quién lo dice y desde dónde. Mira la clase del dominio de la fuente en `data/fuentes/dominios.json` (un dominio `confirmado: false` cuenta como `no_confianza`) y, si no está, la que traiga el encargo (`clase_fuente`).

2. BUSCA PRIMERO en lo publicado: `python3 -I src/buscador.py "<el hecho en pocas palabras>" --json`. Si ya está cubierto, no dupliques: cierra como `descartado` con el enlace de la pieza que existe (o, si el encargo trae un hecho nuevo sobre una pieza publicada, crea un retoque con `python3 -I src/retoques.py crear --pieza <id> --instruccion "…" --por <perfil>` y cierra con esa explicación).

3. INVESTIGA con el paso 3 de `docs/estandar-profundidad.md`: fuente primaria enlazable (boletín oficial, ministerio, regulador, operador, nota oficial de la empresa en su web) y hasta seis fuentes con fecha leída en la página. Un comunicado (`notas_de_prensa` o una nota de empresa) nunca es noticia sin verificación independiente. Sin fuente primaria no se escribe: cierra como `sin_fuentes` con qué buscaste y qué encontraste.

4. ESCRIBE `data/articles/<id>.json` como cualquier pieza (paso 3 de `docs/tarea-edicion-diaria.md`: reportaje de 1.000–1.500 palabras, `key_data`, `timeline`, `sources`, guía rápida, foto con licencia o `image: null`, tres ejes con `python3 -I src/taxonomia.py pieza <ruta>`), con `date` = hoy, `published_at` = la hora real, `origen: "gestor"`, `encargo_gestor: <id>` (sin nombres ni correos). Firma: `python3 -I src/firma.py decidir --id <id> --aplicar` (casi siempre la redacción). Menciones: `python3 -I src/menciones.py proponer --ids <id> --aplicar`.

5. ESTADO. Se publica (`status: publicado`) solo si a la vez: el encargo es `publicacion = 'inmediata'` (lo pidió el editor jefe), la pieza es rutinaria según `editorial.critical_criteria`, y la fuente no es `no_confianza`. En cualquier otro caso: `status: pendiente` (queda en borrador en Ghost y el editor jefe la aprueba desde el gestor o desde el icono ✎ de la pieza).

6. PUBLICA en Ghost (`GHOST_URL` y `GHOST_ADMIN_KEY` en el entorno; si faltan, dilo en la primera línea del aviso): `python3 -I src/ghost_publish.py --ids <id> --status published` (o `--status draft` si queda pendiente). Si se publicó, `python3 -I src/ghost_edicion.py --date <hoy>` para que entre en la portada de hoy. Añade a `docs/ediciones.md` la línea «fuera de edición · desde el gestor · <id>». Regenera el índice del buscador: `python3 -I src/export_search_index.py`.

7. CIERRA el encargo: `update encargos_gestor set estado = '<publicada|pendiente_aprobacion|sin_fuentes|descartado>', pieza = '<id o null>', resultado = '<una o dos frases: qué se publicó, con qué fuente primaria, o por qué no>', cerrado_at = now() where id = <id>;`.

8. REPOSITORIO y AVISO. `git add data docs app/public/buscador && git commit -m "Desde el gestor: <titular corto> (<id>)" && git push`. Aviso de una línea por encargo: qué era, qué se hizo, enlace. Nunca se borra un encargo.
