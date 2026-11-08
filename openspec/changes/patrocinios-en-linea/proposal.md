# Cambio: patrocinios-en-linea

Fecha: 8 de noviembre de 2026 (noche). Origen: decisión de Rainer al recibir el primer correo de menciones del grupo.

## Por qué

Rainer quiere gestionar las menciones de los productos del grupo como contenido patrocinado, desde el móvil y sobre la marcha, y decidir por producto: si entra solo o no, con qué umbral de puntuación, y si es exclusivo o comparte la pieza con otros. Quiere entrar al gestor directamente desde el correo.

Sus palabras: «gestionar la inclusión o no, automática con umbral de puntuación o no, exclusiva o dispuesta a compartir con otros similares en un gestor de espacios patrocinados y publicidad dentro de la web como superadmin u con perfil oficina. De momento pon todas las menciones de nuestro producto en línea con el contenido que propones en una caja en medio del texto con una etiqueta muy discreta que diga "contenido patrocinado". De los correos quiero entrar directamente a ese gestor que debe funcionar en móvil».

## Qué cambia

1. **Dónde va la mención.** Deja de ser el bloque «Nota de la casa» al pie: pasa a ser una caja «Contenido patrocinado» en medio del texto (tras un párrafo, hacia la mitad; con dos cajas, a un tercio y a dos tercios). La caja está separada de los párrafos, con fondo propio, etiqueta pequeña pero siempre visible (art. 20 LSSI) y una línea que dice que el servicio es de una empresa del grupo. El texto de la pieza no se toca. Las seis menciones ya escritas pasan a este formato.
2. **Ajustes por producto** (`data/productos/<id>.json`): `modo` = `automatico` (entra solo si supera el `umbral`), `revision` (queda pendiente para aprobar en el gestor), `manual` (solo se pone a mano) o `apagado`; `exclusividad` = `exclusiva` (si entra, la pieza no lleva otra caja) o `compartida` (hasta `max_por_pieza` cajas, hoy 2).
3. **Gestor de patrocinios y publicidad** en `app.moticias.com/gestor/` (Vercel, proyecto `moticias-app` del equipo MOVO; la excepción ya aceptada a «subdirectorios, nunca subdominios»): pensado para móvil; dos perfiles, superadministrador y oficina; escribe en el repositorio (la fuente de verdad sigue siendo GitHub) y republica la pieza en Ghost al momento.
4. **Correo.** Cada mención del correo lleva el botón «Gestionar», que abre el gestor en esa pieza.

## Qué no cambia

La caja no cambia el texto, la firma ni la aprobación de la pieza. Los análisis del director y las piezas que tratan del grupo no llevan cajas. Retirar es `estado: retirada`, nunca borrar. Los huecos de publicidad fuera del texto (`data/ads/`) siguen como estaban; el gestor solo permite activarlos y pausarlos.

## Riesgo editorial y cómo se cubre

Poner una caja comercial dentro del cuerpo acerca la promoción al texto. Se compensa con: etiqueta siempre visible, caja visualmente separada, `rel="sponsored"` en el enlace, declaración de grupo, máximo dos cajas por pieza, ninguna en análisis y tope semanal por producto. El asesor semanal vigila clics y quejas.
