# Capacidad: gestor de patrocinios y publicidad (nueva)

## ADDED Requisito: dónde vive y cómo se entra
Página `app/public/gestor/index.html` y API `api/gestor.py` (Python, biblioteca estándar) desplegadas en Vercel (`vercel.json` en la raíz; proyecto enlazado a `movo-es/moticias`, redespliega en cada push). Dominio previsto `app.moticias.com/gestor/`. Sin índice para buscadores (`noindex`). Entrada con contraseña; la sesión es una cookie firmada, `HttpOnly`, `Secure`, de 90 días, que se invalida al cambiar cualquiera de las contraseñas. Las peticiones de escritura exigen la cabecera `X-Gestor: 1` (CSRF).

## ADDED Requisito: perfiles
- **Superadministrador** (`GESTOR_CLAVE_SUPERADMIN`): todo.
- **Oficina** (`GESTOR_CLAVE_OFICINA`, opcional): publicar, dejar pendiente, retirar, editar el texto de una caja, añadir una caja a mano y republicar la pieza. Ve los productos y la publicidad, pero no los cambia.

## ADDED Requisito: qué se gestiona
- **Piezas** (últimos 30 días y cualquier pieza con pendientes): filtros «Pendientes», «Con caja», «Posibles» (puntúa algún producto y no tiene caja) y «Todas». Ficha de pieza: cajas con su estado y motivo; puntuación de cada producto contra la pieza (umbral, si lo supera); añadir a mano; ver cómo queda en el texto; republicar.
- **Productos**: modo, exclusividad, umbral, máximo por semana, textos, URL y contexto. Los cambios valen desde la siguiente propuesta; no reescriben menciones ya hechas.
- **Publicidad** (`data/ads/`): ver campañas y huecos; activar o pausar.

## ADDED Requisito: escritura y publicación
Cada cambio lee el fichero fresco de GitHub (`GITHUB_TOKEN`, permiso de contenidos en `movo-es/moticias`), lo modifica y lo guarda con un commit «Patrocinio: …» / «Producto …» / «Publicidad …». Cada acción sobre una mención añade una línea a su `historial` (`en`, `por` = perfil, `accion`). Después, si hay `GHOST_URL` y `GHOST_ADMIN_KEY`, actualiza el post en Ghost manteniendo su estado (`ghost_publish.republicar`); si el post aún no existe o faltan claves, lo dice y lo hará la rutina. El gestor nunca borra.

#### Escenario: no cabe otra caja
- CUANDO se publica o añade una caja y la pieza ya tiene `max_por_pieza` cajas o una exclusiva
- ENTONCES no se guarda nada y el gestor pide retirar otra antes.

#### Escenario: análisis del director
- CUANDO se intenta añadir una caja a una pieza `kind: analisis`
- ENTONCES se rechaza.
