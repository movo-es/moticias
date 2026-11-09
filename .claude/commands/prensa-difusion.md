---
description: Sala de prensa — prepara como borrador de la base de prensa la difusión de las notas pagadas, con el filtro de valor, y avisa a quien la aprueba
---

Eres la difusión de la sala de prensa de MOTICIAS. Corres en laborables tras `/prensa-buzon`. Diseño: `openspec/changes/sala-de-prensa-v1/design.md § 4`. Los destinatarios son los medios y periodistas de la base de prensa (Supabase «moticias», `src/prensa.py`); no hay otra lista. Necesitas en el entorno las variables de `src/bd.py` (SUPABASE_URL, SUPABASE_ANON_KEY, MOTICIAS_BD_CLAVE) y BREVO_API_KEY; si faltan, termina con «sin acceso a la base de prensa» y nada más.

1. **Notas pendientes de difusión.** Con el conector de Supabase o `src/bd.py`: filas de `prensa_notas` con `plan` en (`difusion`, `difusion-plus`, `bono`), `estado = 'publicada'` y `envio_id` vacío.
2. **Planificar** cada una: `python3 -I src/prensa_difusion.py planificar <id>`. Crea el envío en borrador (`prensa_envios`, tipo `nota_de_prensa`, por cuenta del cliente) con los destinatarios que pasan las tres puertas y su motivo, y escribe al director (y a la oficina si la nota es de un cliente) con el enlace `app.moticias.com/gestor/?envio=<n>`.
3. **Si sale BLOQUEADO**, escribe al cliente (correo de la persona del pedido en el CRM) con el motivo en dos frases y, si es por puntuación, los tres avisos de prioridad alta del asesor (`python3 -I src/prensa_asesor.py <texto> --json`). No se cobra una difusión bloqueada: anótalo en el pedido (`motivo`).
4. **Nunca apruebes ni envíes.** Lo hacen el editor jefe o la oficina en la pestaña «Prensa» del gestor; el envío sale por Brevo, uno a uno, con baja firmada.
5. **Martes:** `python3 -I src/prensa_difusion.py resumen` (resumen semanal de los lectores por el boletín «Notas de prensa» de Ghost, un correo por modo a la etiqueta `np-<modo>`; necesita GHOST_ADMIN_KEY).
6. **Aviso** de una línea: borradores creados, bloqueados y por qué.

Prohibido: añadir destinatarios a mano que no pasan el filtro; escribir a quien está en «No contactar»; enviar nada.
