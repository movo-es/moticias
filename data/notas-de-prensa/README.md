# Notas de prensa publicadas

Una nota por fichero, `AAAA-MM-DD-<slug>.json`, con el texto tal como se publica en `moticias.com/notas-de-prensa/` y sus tres ejes. Solo lo público: los datos del cliente, el plan, la valoración del asesor y la difusión viven en la base privada (`prensa_notas`, migración 007). Las crea `src/prensa_publicar.py` (`desde-pedido` o `nueva`); nunca se borran: retirar es `status: retirada`.
