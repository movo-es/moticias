# Cambio: etiquetas-comunes

Fecha: 15 de noviembre de 2026. Origen: encargo de Rainer del mismo día (punto 2 de su cola). Entrevista hecha el 15-11-2026, seis preguntas, todas aceptadas tal como se recomendaron, más una precisión suya sobre lo que no caduca. Estado: aplicado y archivado el 15-11-2026.

Respuesta corta: una sola taxonomía para la cola del editor, el menú, la publicidad y el panel SEO, ampliando la que ya había en `verticals/movilidad.json → taxonomia` (no se crea otra). Se deja de usar la palabra «ámbito».

## Decisiones de la entrevista
1. **Nombres:** Medio (tierra, mar, aire; «espacio» creado y apagado), Modo (tren, autobús…), Tema (los siete de siempre), Región (comunidades, Estatal, UE, Internacional), Importancia (1–5), Fiabilidad de la fuente, Fecha del hecho.
2. **Logística dentro de cada medio:** modos de mercancías (por carretera, tren de mercancías, carga marítima, carga aérea) que forman /logistica/; «Transversal» pasa a «Varios medios». Lista de modos en `taxonomia.modos_transporte`.
3. **Importancia 1–5** con la escala escrita en el vertical; lo publicado se convierte (ALTA→4, MEDIA→3, BAJA→2, con motivo de importancia→5); la firma del editor jefe pasa a importancia 4–5; el agente aprende de las correcciones (guardadas desde la cola, cambio siguiente).
4. **Fiabilidad:** primaria → se confirma; secundaria reputada → solo con dos que coinciden y queda «buscar primaria»; sin confirmar → aviso en la cola, «Confirmar» bloqueado, si caduca va al archivo. El lector no la ve.
5. **Fechas:** Fecha del hecho (`event_date`, ya existía en las 95 piezas) y Fecha límite opcional (`fecha_limite`, solo si la agenda la enlaza a una fuente de la pieza: 47 de 95). Caducidad en la cola: la fecha límite o 3 días laborables.
   Precisión de Rainer: lo editorial, «La voz del editor», los análisis en profundidad y los textos académicos o de referencia **no caducan nunca**: bajan por fecha en su sección, pero con filtros del lector pueden salir los primeros, y si son lo único sobre un tema salen siempre.
6. **Lo que ve el lector:** medio, modo, tema y región como etiquetas pulsables, y la fecha del hecho si difiere de la de publicación; no ve importancia, fiabilidad ni quién lo propuso. Con filtros: encaje → importancia → fecha (las noticias pierden peso, lo que no caduca no). Sin filtros: por fecha, con la apertura del editor jefe.

## Qué se ha hecho
- Vertical: `nombres`, `medios`, `modos_transporte`, `importancia`, `fiabilidad`, `fechas`, `orden_lector`; `nombre_corto` Estatal/UE/Internacional.
- `src/taxonomia.py`: `etiquetas` (informe o `--aplicar`), `validar`, y `pieza` propone también las etiquetas comunes. Las 95 piezas etiquetadas; todas pasan.
- `src/firma.py`: la firma del editor jefe exige importancia 4 o más (antes, relevancia ALTA).
- Índice del buscador con medio, modos, importancia, fechas y «no caduca», listo para el menú y la cola.
- Tarea diaria: `etiquetas --aplicar` y `validar` tras los tipos de contenido.
- Gestor, pestaña Prensa: el filtro «ámbitos» de la base de prensa pasa a llamarse «cobertura» (es otra cosa: lo que cubre cada medio de comunicación).

## Lo que no cambia por dentro
`modo`/`submodo` (eje antiguo) se conservan: los usan la base de prensa (Supabase), las etiquetas `m-` de Ghost y el mapa. El tipo interno `ambito` de los territorios y la columna `ambitos` de la base de prensa tampoco cambian de nombre.
