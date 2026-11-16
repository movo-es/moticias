# Redacción del editor jefe

## ADDED Requisito: herramientas en moticias.com
Solo con sesión de superadministrador en el gestor. La marca `moticias_jefe` no da permisos; el sitio pregunta `GET /api/gestor?a=yo` con credenciales desde `https://www.moticias.com` y solo enseña el icono si contesta `jefe: true`.

## ADDED Requisito: editar
Lista cerrada de campos (`src/redaccion.py → CAMPOS`). Cada edición deja `revised_at` y una línea en `revisiones`; una corrección añade además `correcciones` (nota al final, con fecha). Se escribe por commit y se actualiza Ghost al momento.

#### Escenario: cifra nueva
- CUANDO el texto a publicar contiene una cifra o fecha que no está en la pieza ni en sus fuentes
- ENTONCES el servidor contesta 409 con la lista y solo publica si el editor jefe confirma expresamente que responde de ellas.

## ADDED Requisito: otro enfoque con IA
La IA (AI Gateway, `MODELO_IA`, por defecto `anthropic/claude-opus-5.5`) devuelve una propuesta que no se guarda. El editor jefe la ve junto al original, la pasa al editor y publica con «Publicar cambios». No puede añadir hechos; las cifras nuevas se marcan.

## ADDED Requisito: retirar
«Borrar» es retirar: `status: retirada` y borrador en Ghost; la pieza se conserva y se puede restaurar. Nunca se borra.

## ADDED Requisito: solo el editor jefe
Editar, IA, retirar, restaurar, aprobar, retoques, publicar cajas, activar publicidad, productos y equipo: permiso `redaccion`/`piezas`/`publicidad`/`productos`/`equipo`, que solo tiene `superadmin`. Los demás perfiles reciben 403 del servidor.

## ADDED Requisito: leer la pieza antes de aprobarla
En el gestor, la ficha de cada pieza enseña la pieza entera como la leerá el lector: antetítulo, titular, subtítulo, firma, foto con crédito, dato clave, cifras clave con su fuente, texto (con las cajas de contenido patrocinado marcadas), «Qué viene ahora», cronología, fuentes enlazadas con medio y fecha y nota de intereses (decisión de Rainer, 16-11-2026). Si la pieza espera aprobación, aparece abierta, con el motivo (`review_note`) arriba y los botones Aprobar y publicar · Editar · Otro enfoque con IA · Retirar repetidos al final; si ya está publicada, plegada. Una pieza pendiente está en borrador en Ghost, así que la ficha no ofrece «Ver en moticias.com».
