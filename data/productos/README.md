# Gestor de productos propios (`data/productos/`)

Un JSON por producto o servicio del grupo que MOTICIAS puede mencionar al pie de una pieza cuando la noticia trata de un problema que ese producto resuelve. Lo lee `src/menciones.py`; lo edita Rainer (o la sala de redacción cuando exista) sin tocar código. La regla editorial está en `CLAUDE.md` y en `openspec/changes/plataforma-2027/specs/menciones-del-grupo/spec.md`: la mención nunca va dentro del texto de la pieza; va en un bloque señalizado «Nota de la casa» con su declaración, y el director recibe por correo cada mención publicada con enlace para editarla o retirarla.

## Campos

| Campo | Qué es |
|---|---|
| `id`, `name`, `url`, `owner` | Identificador (= nombre del fichero), nombre público, página de destino, sociedad titular. **Sin `url` no se menciona.** |
| `status` | `activo` (se menciona), `borrador` (no se menciona hasta aprobar), `pausado`, `retirado`. Nunca se borra un fichero. |
| `one_liner` | Una frase de qué hace. |
| `contexto` | **El contexto que queremos que le dé entrada a las noticias**, en prosa: cuándo sí y cuándo no. Es la instrucción para la persona y para el modelo cuando revisan una propuesta; el motor automático usa `disparadores` y `excluir`. |
| `disparadores.subsectores`, `.secciones` | Dónde encaja la pieza (`subsector`, `section` de la pieza). |
| `disparadores.palabras_clave` | Términos que suman 1 punto cada uno (una vez por término, sin acentos ni mayúsculas). |
| `disparadores.frases` | Expresiones que suman 3 puntos cada una. |
| `excluir` | Si alguno aparece en título, subtítulo o resumen, no se menciona (evita mencionar un producto en una pieza que ya habla del grupo o de su mercado propio). |
| `umbral` | Puntuación mínima para proponer la mención (10 por defecto). Además, la cabecera de la pieza (título, subtítulo, resumen) tiene que contener una frase disparadora o dos palabras clave: la pieza debe tratar del problema, no rozarlo. Cabecera puntúa doble. |
| `max_por_semana` | Tope de menciones publicadas del producto en siete días; alcanzado, se propone pero no se publica. |
| `textos.corto` | El texto del bloque (dos o tres frases, en tono informativo, sin adjetivos comerciales). |
| `textos.cta` | Texto del enlace. |
| `utm_campaign` | Para medir: el enlace lleva `utm_source=moticias&utm_medium=nota-de-la-casa&utm_campaign=<este>&utm_content=<id de la pieza>`. |

## Cómo se decide una mención

1. La rutina diaria (paso 7 quinquies) ejecuta `python3 -I src/menciones.py proponer --fecha AAAA-MM-DD --aplicar` sobre las piezas del día.
2. Para cada pieza se puntúan todos los productos `activo` con `url`; gana el de mayor puntuación si supera su `umbral`, no hay término de `excluir`, la pieza no es un análisis del director y el producto no ha agotado `max_por_semana`.
3. La mención se escribe en la pieza (`menciones: [{producto, texto, cta, url, estado, motivo, puntuacion, propuesta_en}]`) con `estado: publicada` (rutinaria) y el publicador la pinta en el bloque «Nota de la casa».
4. `python3 -I src/menciones.py informe --fecha AAAA-MM-DD` y `enviar` mandan a `ruphoff@avionline.es` el resumen con un enlace de edición por mención (editor de Ghost y fichero en GitHub). Solo se envía si hubo menciones.
5. Retirar una mención = poner `estado: retirada` en el JSON (nunca borrarla) y volver a publicar la pieza; el bloque desaparece y la historia queda.

## Lo que no hace

No reescribe la pieza, no cambia la firma ni los criterios de aprobación, no añade enlaces en el cuerpo del texto, no menciona un producto en una pieza que trate del propio grupo (esas son críticas y las firma el director). Una pieza lleva como mucho una mención.
