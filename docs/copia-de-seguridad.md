# MOTICIAS · Copia de seguridad en el Mac

Cambio OpenSpec `copia-de-seguridad-mac` (decisión y «sí» de Rainer, 15-11-2026). Respuesta corta: todo vive en la nube; el MacBook recibe cada día una copia, solo como respaldo. Nada en producción ni ninguna tarea programada depende del Mac: si no copia, lo único que pasa es que llega un correo.

## Qué se copia, dónde y cuándo

| Qué | Cómo | Dónde | Cifrado |
|---|---|---|---|
| El repositorio `movo-es/moticias`, todas las ramas e historial | `git bundle` | `~/Copias/MOTICIAS/AAAA-MM-DD/repo.bundle` | No (ya es público) |
| La base privada de Supabase «moticias» (CRM, equipo, base de prensa, seguimiento, encargos, buzón) | `pg_dump` con un usuario de **solo lectura** (`copia_lectura`) | dentro de `privado.sparseimage` | **Sí**, AES-256 (imagen de disco de macOS) |
| Lo que solo está en Ghost: miembros, ajustes, boletines, planes, etiquetas, páginas y posts | Admin API (`scripts/copia-mac/ghost_exportar.py`) | dentro de `privado.sparseimage` | **Sí** |
| El tema de Ghost | a mano, una vez al mes (el Mac lo recuerda con un aviso) | `~/Copias/MOTICIAS/tema/*.zip` | No |

- **Cuándo:** cada día a las 13:30. Si el Mac está dormido, al despertar; si estaba apagado, al iniciar sesión. Si ese día ya hay copia, no repite.
- **Cuántas se guardan:** las 7 últimas diarias, 4 semanales y 12 mensuales. El guion solo borra copias viejas de `~/Copias/MOTICIAS/`.
- **Prueba de restauración:** el primer lunes de cada mes (o si la última correcta tiene más de 35 días), automática.
- **Claves:** en el llavero de macOS, servicio «moticias-copia» (cuentas `supabase-url`, `ghost-admin-key`, `cifrado`, `token-registro`). Ninguna en ficheros ni en el repositorio. La **frase de cifrado** está además donde Rainer la guardó al instalar (gestor de contraseñas o papel): sin ella, las copias cifradas no se abren.
- **Registro:** cada copia y cada prueba mandan al gestor solo fecha, tamaños, huellas y recuentos (tabla `copias_registro`, migración 010). Se ve en `app.moticias.com/gestor/` → Equipo → «Copias de seguridad». El cron diario `copias_vigilar` (09:05) manda un correo si pasan **más de 3 días** sin copia correcta, si falla la última o si no hay prueba correcta en 35 días.
- **Espejo en la nube (solo el repositorio):** `movo-es/moticias-respaldo`, privado, actualizado por GitHub (`.github/workflows/espejo.yml`) tras cada subida a `main` y cada noche. La base privada y los miembros de Ghost nunca salen del Mac.

## Instalar (una vez, en el Terminal del Mac)

```bash
cd ~ && curl -fsSL https://raw.githubusercontent.com/movo-es/moticias/main/scripts/copia-mac/instalar.sh -o /tmp/moticias-instalar.sh && bash /tmp/moticias-instalar.sh
```

El instalador explica cada paso. Antes conviene tener Postgres.app (https://postgresapp.com/downloads.html; abrirlo una vez, «Initialize» y marcar que se inicie al arrancar). Durante la instalación pide la clave de una integración de Ghost («Copia de seguridad Mac») y abre el editor SQL de Supabase con dos líneas en el portapapeles: se pegan y se pulsa «Run».

## Comprobar que funciona

1. Gestor → Equipo → «Copias de seguridad»: «Última copia» de hoy y «Última copia probada».
2. En el Mac:

```bash
cd ~ && tail -n 30 ~/Copias/MOTICIAS/registro.log
```

3. Hacer una copia ahora, o una prueba de restauración ahora:

```bash
cd ~ && bash ~/Copias/MOTICIAS/.programa/copia.sh --forzar
```

```bash
cd ~ && bash ~/Copias/MOTICIAS/.programa/restaurar-prueba.sh
```

## Restaurar desde el gestor (editor y editor jefe; cambio `restaurar-copia`, 15-11-2026)

Para el día a día no hace falta el Mac. Gestor → pestaña **Restaurar**:

- **Piezas y publicidad.** Busca el documento, elige una versión anterior, mira qué cambia y pulsa «Restaurar esta versión». Se escribe una versión nueva (nada se borra), la pieza se republica con su estado de hoy, el editor jefe recibe un correo y aparece el botón «Deshacer». El editor no puede restaurar piezas firmadas por el editor jefe, piezas que no estén publicadas hoy, versiones que no llegaron a publicarse ni productos: eso lo hace el editor jefe.
- **CRM y prensa.** Supabase guarda cada noche (03:40) una copia de la base privada durante 14 días (esquema `copia`, migración 011). Elige qué y de qué día, compara con hoy y recupera la ficha que falta o los campos que cambiaron. Nunca borra una ficha de hoy y nunca quita un «No contactar». El editor recupera CRM y base de prensa; el editor jefe, además, contratos, seguimiento de la publicidad y encargos. El equipo no se recupera desde aquí.

## Restaurar de verdad (si algo se pierde)

Solo con una sesión de Claude Code o con ayuda técnica; nunca se borra nada en producción para restaurar: se restaura en limpio y se compara.

- **Repositorio:** `git clone ~/Copias/MOTICIAS/AAAA-MM-DD/repo.bundle moticias-restaurado`, o desde el espejo `movo-es/moticias-respaldo`.
- **Base privada:** abrir la imagen (doble clic en `privado.sparseimage` y la frase de cifrado) y restaurar `base.dump` en un proyecto de Supabase nuevo: primero la estructura de `supabase/migrations/` (001 a la última), después los datos con `pg_restore --data-only --disable-triggers` sobre esa estructura. `manifiesto.json` dice cuántas filas debe tener cada tabla.
- **Ghost:** los JSON de la carpeta `ghost/` de la imagen. Los miembros se importan por CSV desde el panel (Members → Import) a partir de `members.json`; posts y páginas se rehacen desde `data/articles/` con `src/ghost_publish.py`, que es la fuente de verdad; los ajustes, a mano a partir de `settings.json`. El tema, desde el `.zip` de `tema/` (o desde `ghost/theme/` cuando esté versionado).

## Lo que no hace

No copia los secretos de Vercel, Ghost, Brevo ni Supabase (se recrean en cada servicio). No guarda nada en el repositorio. No sustituye a las copias propias de Supabase y Ghost(Pro).
