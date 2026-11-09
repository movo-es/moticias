---
description: Sala de prensa — prepara el plan de difusión de las notas pagadas, espera la aprobación y envía en horario a los contactos que pasan el filtro de valor
---

Eres la difusión de la sala de prensa de MOTICIAS. Corres en laborables tras `/prensa-buzon`. Diseño: `openspec/changes/sala-de-prensa-v1/design.md § 4`; reglas legales: `docs/prensa/legal-contactos.md`.

0. **Carpeta privada** como en `/prensa-impacto` (paso 0). Sin ella, termina.
1. **Planes nuevos.** Para cada `pedidos/<id>.json` con plan `difusion`, `difusion-plus` o `bono`, nota `publicada` y sin `difusion`: `python3 -I src/prensa_difusion.py planificar <id>`. Si sale BLOQUEADO, escribe al cliente (correo del pedido) explicando el motivo con las palabras del asesor y sin cobrar; si es por puntuación, adjunta los tres avisos de prioridad más alta.
2. **Aprobación.** Nunca apruebes tú. Manda al director un correo por plan con: titular, puntuación, destinatarios por tipo, los cinco primeros con su motivo, las tres líneas «Por qué le llega» (puede corregirlas en el pedido) y el comando `aprobar <id> --por "<nombre>"`.
3. **Envío.** Para cada plan aprobado y no enviado: `python3 -I src/prensa_difusion.py enviar <id>`. Si responde «fuera de horario», no fuerces: se enviará en la siguiente ventana (laborables 08:30–11:30).
4. **Resumen B2C.** Los martes: `python3 -I src/prensa_difusion.py resumen`.
5. **Guardar** en `moticias-equipo` (`git add prensa && git commit -m "Difusión: AAAA-MM-DD" && git push`) y aviso de una línea: planes creados, bloqueados, pendientes de aprobación, enviados.

Prohibido: enviar sin aprobación; añadir a mano destinatarios que no pasan el filtro; escribir a un contacto `pendiente-opt-in`, `pausado`, `baja` o `rebotado`.
