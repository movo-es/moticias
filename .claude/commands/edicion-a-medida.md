---
description: Edición a medida — genera para un perfil la selección, el documento de revisión y, tras la aprobación, la página, el correo y el PDF
---

Eres el empaquetador de ediciones a medida de MOTICIAS. `$ARGUMENTS` = `<perfil> [preparar|emitir] [--hasta AAAA-MM-DD]`; el perfil es `data/perfiles/<perfil>.json`. Especificación: `openspec/changes/plataforma-2027/specs/ediciones-a-medida/spec.md`; contexto: `docs/estrategia-2027.md § 4.6`. Herramientas: `src/selector.py` (módulo 1) y `src/empaquetador.py` (módulo 2).

**preparar** (por defecto; corre según la cadencia del perfil, antes de las 08:00):
1. `python3 -I src/empaquetador.py --perfil data/perfiles/<perfil>.json --sin-pdf` → `work/ediciones/<perfil>/<fecha>/` con `seleccion.json`, `revision.md`, `pagina.html` y `correo.html`.
2. Lee `revision.md` y la selección con ojo de redactor: quita duplicados de un mismo hecho, comprueba que ninguna pieza del cliente aparece sin marca, que ninguna pieza de MOTICIAS cita soluciones del grupo, y que la cabecera, el color y el nombre son los del perfil. Si falta una pieza evidente del periodo (mira `data/articles/` del rango), añádela a `seleccion.json`.
3. Si `review.required` es `true`: crea el documento de revisión colaborativo con las herramientas de Claude Docs (título «Revisión · <nombre del perfil> · <fecha>», contenido de `revision.md` más un enlace a `pagina.html` publicada como vista previa si es posible) y compártelo con `review.reviewers`; deja el enlace en `work/ediciones/<perfil>/<fecha>/revision.url` y avisa en una línea. No emitas.
4. Si `review.required` es `false`, pasa a **emitir**.

**emitir** (a mano, cuando el documento de revisión está aprobado, o automático si no hay revisión):
1. Aplica a `seleccion.json` lo marcado en el documento de revisión (piezas quitadas, añadidas, orden).
2. `python3 -I src/empaquetador.py --perfil data/perfiles/<perfil>.json --seleccion work/ediciones/<perfil>/<fecha>/seleccion.json` → página, correo y `edicion.pdf`.
3. Página privada: si la aplicación está desplegada, publica `pagina.html` en `app.moticias.com/ediciones/<perfil>/<fecha>`; si no, publícala como artefacto de Claude privado y guarda la URL.
4. Correo: con las herramientas de Brevo, confirma la cuenta (`accounts_get_account`), crea la campaña en borrador con `correo.html`, la lista del perfil (`brand.brevo_list_id`) y el remitente verificado; envía una prueba a la dirección de `review.test_email` si existe. El envío real lo confirma una persona, salvo que el perfil diga `outputs.email_auto: true`.
5. PDF: adjunta `edicion.pdf` a la página privada y guárdalo en `data/ediciones-a-medida/<perfil>/<fecha>.pdf` solo si el perfil pide archivo (`outputs.archive: true`); si no, queda en `work/`.
6. Registro: añade una línea a `docs/ediciones-a-medida.md` (fecha, perfil, piezas, boletines, plazos, revisor, estado) y haz commit y push.

Reglas: el contenido del cliente siempre marcado; nunca se mezcla con el de MOTICIAS sin marca; cada pieza enlaza a su original; el pie lleva «Powered by MOTICIAS» y la declaración de intereses del vertical; si el selector devuelve menos de tres piezas, no se emite: se avisa y se propone ampliar `filters.days` o las palabras clave. Nada inventado: si una pieza no existe en `data/`, no entra.
