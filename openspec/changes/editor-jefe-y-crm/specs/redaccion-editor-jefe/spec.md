# Redacción del editor jefe

## ADDED Requisito: herramientas en moticias.com
Solo con sesión de superadministrador en el gestor. La marca `moticias_jefe` no da permisos; el sitio pregunta `GET /api/gestor?a=yo` con credenciales desde `https://www.moticias.com` y solo enseña el icono si contesta `jefe: true`.

## ADDED Requisito: editar
Lista cerrada de campos (`src/redaccion.py → CAMPOS`). Cada edición deja `revised_at` y una línea en `revisiones`; una corrección añade además `correcciones` (nota al final, con fecha). Se escribe por commit y se actualiza Ghost al momento.

#### Escenario: cifra nueva
- CUANDO el texto a publicar contiene una cifra o fecha que no está en la pieza ni en sus fuentes
- ENTONCES el servidor contesta 409 con la lista y solo publica si el director confirma expresamente que responde de ellas.

## ADDED Requisito: otro enfoque con IA
La IA (AI Gateway, `MODELO_IA`, por defecto `anthropic/claude-opus-5.5`) devuelve una propuesta que no se guarda. El director la ve junto al original, la pasa al editor y publica con «Publicar cambios». No puede añadir hechos; las cifras nuevas se marcan.

## ADDED Requisito: retirar
«Borrar» es retirar: `status: retirada` y borrador en Ghost; la pieza se conserva y se puede restaurar. Nunca se borra.

## ADDED Requisito: solo el editor jefe
Editar, IA, retirar, restaurar, aprobar, retoques, publicar cajas, activar publicidad, productos y equipo: permiso `redaccion`/`piezas`/`publicidad`/`productos`/`equipo`, que solo tiene `superadmin`. Los demás perfiles reciben 403 del servidor.
