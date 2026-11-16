# Cambio: subidas-que-no-llegan

Fecha: 16 de noviembre de 2026 (noche). Origen: aviso de Rainer («aparece como publicada pero no está en la web»). Estado: aplicado.

## Qué pasó
A las 15:41 aprobó «El polígono no tiene plan» con «Publicar ahora». El gestor guardó la pieza como publicada y la subida a Ghost falló (registro: `redaccion_publicar`, `ghost: false`). La causa más probable es la fecha de publicación sin segundos que escribía «Publicar ahora» (cambio `voz-desde-el-panel`); a las 15:50 otra sesión hizo que la fecha salga siempre completa hacia Ghost y que «Volver a subir a la web» cree la pieza que falta. Nadie volvió a subirla y la tarjeta la enseñaba como publicada, con un enlace que daba 404.

## Decisiones
1. «Publicar ahora» guarda la fecha con segundos (se arregla en origen, además de al enviar).
2. El gestor sabe por su registro qué subidas fallaron (`subidas_fallidas`) y la tarjeta lo dice, con «Subir a la web ahora».
3. Cron `web_reintentos`, cada 20 minutos y todos los días: reintenta hasta 12 veces por pieza y lo apunta.

## Qué no cambia
Quién aprueba, la firma y las reglas de publicación. Solo se reintenta lo que ya estaba aprobado y sigue `publicado`.
