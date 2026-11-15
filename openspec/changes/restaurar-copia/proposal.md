# Cambio: restaurar-copia

Fecha: 15 de noviembre de 2026. Origen: encargo de Rainer del mismo día («un proceso de restaurar de copia de seguridad que pueda cualquiera con perfil de editor»). Estado: **propuesta, pendiente del «sí» de Rainer y de sus decisiones**. Se apoya en `copia-de-seguridad-mac`.

Respuesta corta: «Restaurar» pasa a ser una pantalla del gestor, desde el móvil y sin el Mac, para dos casos: devolver una pieza, un anuncio, un producto o una edición a una versión anterior (desde el historial del repositorio) y recuperar registros de la base privada (CRM, base de prensa, equipo, seguimiento) desde una copia diaria que la propia Supabase guarda en un esquema aparte. Nunca se restaura encima: siempre se enseña qué cambia, se restaura con un registro y se puede deshacer. El desastre total (perder el proyecto de Supabase, Ghost o GitHub) sigue siendo cosa del editor jefe con la copia cifrada del Mac (`docs/copia-de-seguridad.md`).

## Por qué (lo comprobado el 15-11-2026)

- **Contenido.** Todo lo que publica MOTICIAS está en `data/`, y el repositorio guarda cada versión de cada fichero (cada edición, cada retoque, cada cambio del gestor es un commit). Hoy volver a una versión anterior exige saber usar git.
- **Base privada.** El proyecto está en el plan Pro de Supabase, que guarda copias diarias propias, pero restaurarlas devuelve **todo el proyecto** a ese día y borra lo posterior: no sirve para recuperar una ficha del CRM mal editada. La copia cifrada del Mac solo puede abrirse en el Mac con la frase de cifrado.
- **Permisos.** El perfil editor hoy solo propone, trabaja en el CRM, ve suscriptores y lanza el barrido (`src/equipo.py`). Restaurar una pieza publicada es publicar, y eso hoy solo lo hace el editor jefe.

## Qué cambia

1. **Pestaña «Restaurar» del gestor** (editor y editor jefe), con dos apartados y el mismo método: elegir → ver qué cambia → restaurar → aviso al director → «Deshacer».
2. **Contenido** (`data/articles`, `data/ads`, `data/productos`, `data/editions`, `data/agenda`, `data/boletines`):
   - buscar el documento; ver sus versiones (fecha, quién, motivo del commit) y la diferencia campo a campo con la actual;
   - «Restaurar esta versión» escribe un commit nuevo con el contenido antiguo (no reescribe la historia ni borra nada), añade a la pieza una línea en `revisiones` y `revised_at`, y la republica en Ghost con su estado de siempre (una pieza del director pendiente sigue en borrador);
   - las reglas de siempre se comprueban también aquí: tipo de contenido y tres ejes válidos (`src/tipos.py`, `src/taxonomia.py`); si la versión antigua no los tiene, se completan antes de publicar;
   - «Deshacer» restaura la versión que había justo antes.
3. **Base privada:**
   - **copia interna diaria en Supabase:** un trabajo programado de la propia base (`pg_cron`, 03:40) copia cada noche todas las tablas de `public` a un esquema privado `copia` (`copia.<tabla>_AAAAMMDD`), conserva 14 días y no se publica en la API. Los datos no salen de Supabase, que es donde ya están;
   - el gestor compara una tabla de hoy con la del día elegido y enseña solo lo que falta o lo que cambió (por ficha: cuenta del CRM, medio, periodista…);
   - «Recuperar» vuelve a insertar la fila que falta o devuelve los campos elegidos a su valor de ese día, con una línea en `gestor_registro`. Nunca borra una fila de hoy. Las reglas de la base se mantienen: «No contactar» es para siempre y los estados son de solo añadir (una restauración no puede quitar un «No contactar»).
4. **Aviso:** cada restauración manda un correo al director con qué, de qué fecha, quién y el enlace para deshacerla.
5. **Lo que no entra:** restaurar Ghost (miembros, ajustes, tema), el equipo y sus contraseñas, o el proyecto entero. Eso sigue en manos del editor jefe con la copia del Mac (`docs/copia-de-seguridad.md § Restaurar de verdad`).

## Qué no cambia

Nadie borra nada; la historia del repositorio no se reescribe; la firma, la aprobación y el cupo del director siguen igual; los datos personales nunca van al repositorio; la copia del Mac sigue siendo el respaldo fuera de la nube.

## Decisiones que le tocan a Rainer

1. **¿Restaura el editor directamente el contenido publicado, o lo propone y tú lo apruebas con un toque?** Propuesta: **directamente**, como excepción acotada a «solo el editor jefe publica»: solo puede devolver una versión que ya estuvo publicada, queda registrado, te llega el aviso y se deshace en un toque. Las piezas firmadas por ti quedan fuera: esas solo las restauras tú.
2. **Copia interna diaria de la base privada en Supabase** (esquema `copia`, 14 días): propuesta **sí**. Es lo que permite recuperar un dato desde el móvil sin el Mac. Los datos no salen de Supabase, pero sí hay una segunda copia de los datos personales dentro de Supabase durante 14 días.
3. **¿Puede el editor recuperar también fichas del equipo y del seguimiento, o solo CRM y base de prensa?** Propuesta: **solo CRM y base de prensa**; equipo y seguimiento, solo el editor jefe.
