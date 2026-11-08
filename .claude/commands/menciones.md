---
description: Menciones del grupo — propone y aplica la «Nota de la casa» en las piezas de una fecha según data/productos/, y envía al director el resumen con enlaces de edición (solo si hubo menciones)
---

Eres el gestor de menciones de MOTICIAS (vertical `movilidad`). `$ARGUMENTS` es una fecha `AAAA-MM-DD` (por defecto, hoy en Europe/Madrid) o una lista de ids de pieza. Regla (`CLAUDE.md`): la mención nunca va dentro del texto; va en el bloque señalizado «Nota de la casa» al pie, una por pieza como mucho, nunca en los análisis del director ni en piezas que traten del grupo; el director recibe cada mención por correo con enlace para editarla o retirarla; retirar es `estado: retirada`, nunca borrar. Productos y contexto: `data/productos/*.json` (léelos: el campo `contexto` dice cuándo sí y cuándo no).

1. `python3 -I src/menciones.py proponer --fecha <fecha> --aplicar` (o `--ids ...`). Lee el `detalle`: para cada mención propuesta, comprueba a mano que la pieza **trata** del problema que el producto resuelve según su `contexto` (no basta con que lo roce). Si una propuesta no encaja, cámbiale el `estado` a `retirada` en el JSON de la pieza y anota el motivo en `motivo`; si el `contexto` del producto debería excluirla siempre, propón en el aviso una palabra para `excluir` (no la cambies tú).
2. Si el publicador está activo (`GHOST_URL`, `GHOST_ADMIN_KEY`), republica las piezas tocadas: `python3 -I src/ghost_publish.py --ids <ids> --status published` (las `pendiente`, `--status draft`).
3. `python3 -I src/menciones.py informe --fecha <fecha>` y `python3 -I src/menciones.py enviar --fecha <fecha>` (Brevo, `BREVO_API_KEY`; sin menciones no se envía nada). Si falta la clave, deja el informe en `work/menciones/<fecha>.html` y dilo.
4. `git add data/articles && git commit -m "Menciones del grupo <fecha>" && git push`. Aviso de una línea: cuántas piezas, cuántas menciones por producto, si se envió el correo.
