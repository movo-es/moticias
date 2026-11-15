## ADDED Requirements

### Requisito: etiquetas comunes en toda pieza
Toda pieza lleva `medio`, `modos` (salvo «varios medios»), `temas`, `territorios`, `importancia` (1–5) y `fiabilidad` (`primaria`, `secundaria`, `sin_confirmar`); `event_date` es la fecha del hecho y `fecha_limite` es opcional. Sin ellas no se publica (`src/taxonomia.py validar`).

#### Escenario: logística dentro de su medio
- DADO una pieza sobre la terminal ferroviaria de mercancías de Bilbao
- CUANDO se etiqueta
- ENTONCES `medio` es `tierra` y `modos` es `["tren-mercancias"]`, y sale en /logistica/

#### Escenario: medio apagado
- DADO que «espacio» tiene `activo: false`
- CUANDO se etiqueta una pieza
- ENTONCES nunca se propone `espacio` ni sus modos; al ponerlo a `true` se proponen sin tocar código

### Requisito: importancia propuesta y corregida
El agente propone `importancia_agente` con la escala del vertical; la que manda es `importancia`, que corrige el editor jefe. Cada corrección se guarda para que el agente aprenda. La firma del editor jefe exige importancia 4 o más.

### Requisito: fiabilidad de la fuente
Primaria se puede confirmar; secundaria reputada solo con dos fuentes que coinciden y queda marcada «buscar primaria»; sin confirmar no se puede confirmar ni publicar. El lector no ve esta etiqueta.

### Requisito: caducidad
Una noticia o un aviso caduca al pasar su `fecha_limite` o, si no la tiene, a los 3 días laborables de su fecha del hecho. Lo editorial, «La voz del editor» y lo de referencia no caducan nunca.

### Requisito: orden para el lector
Con filtros: encaje, después importancia, después fecha; lo que no caduca no pierde peso con los días. Sin filtros: por fecha, con la apertura del editor jefe.
