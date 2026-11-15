# Cambio: cola-del-editor

Fecha: 16 de noviembre de 2026. Origen: punto 3 de la cola de Rainer del 15-11-2026. Prototipo publicado (`prototipo/index.html`), entrevista hecha: tres preguntas aceptadas tal como se recomendaron; desde la noche del 15-11 Rainer dio por aceptadas todas las recomendaciones. Estado: aplicado.

Respuesta corta: una pestaña «Cola» en el gestor (la primera para el editor jefe y los editores) con los temas nuevos, para filtrarlos, ordenarlos y decidir desde el móvil. Solo el editor jefe confirma y publica; «Confirmar» encarga la pieza a la redacción automática.

## Decisiones
1. **Edición de la mañana:** sigue automática. La cola recoge lo demás: temas que el barrido encontró y no entraron, avisos de batidas y sensores, propuestas de los editores.
2. **«Confirmar»:** encargo a la redacción horaria (`encargos_gestor` con `cola_tema`, que atiende /noticias-gestor). Investiga en fuente primaria y escribe con el estándar de siempre; rutinaria → publicada y aviso; crítica o con la firma del editor jefe → «Para aprobar» (Leer y publicar); sin fuente primaria → vuelve a la cola «Sin fuente primaria» con el motivo. Fin de semana y festivos: espera al lunes, salvo importancia 5, que lanza la batida de grandes noticias.
3. **Permisos:** editor jefe todo; editor ve, propone, corrige etiquetas y sección, y archiva o recupera solo lo suyo; comercial ve (sin la solución del grupo) y propone; oficina no entra. Solo cuentan para el aprendizaje las correcciones de importancia del editor jefe.

Y lo que ya venía decidido: filtros y orden por todas las etiquetas comunes y además estado, caducidad, agrupación de avisos sobre el mismo hecho, solución del grupo y quién lo propuso; selección individual o en bloque; confirmar, editar, subir y bajar importancia, cambiar de sección, archivar y borrar (papelera recuperable).

## Qué se ha hecho
- Base privada: migración 012 (`cola_temas`, `cola_correcciones`, `encargos_gestor.cola_tema`), aplicada el 16-11-2026.
- `src/cola.py`: permisos, caducidad (festivos nacionales y Viernes Santo calculado), agrupación por clave de hecho, `proponer`, `sql`, `ejemplos`, `aciertos`, `caducar`.
- `api/gestor.py`: `GET a=cola&pestana=…` (sincroniza con los encargos y archiva lo caducado) y `POST a=cola` (`proponer`, `confirmar`, `importancia`, `editar`, `seccion`, `archivar`, `papelera`, `recuperar`), con permisos comprobados en el servidor (403).
- Gestor: pestaña «Cola» con las pestañas Cola · Confirmados · Publicados · Archivo · Papelera, filtros, orden, selección en bloque, hojas de edición, importancia con motivo y sección.
- Rutinas: la edición diaria (7 octies) y la batida suben sus temas a la cola; /noticias-gestor respeta las etiquetas del tema confirmado; el asesor de los lunes informa una vez al mes de los aciertos del agente.
