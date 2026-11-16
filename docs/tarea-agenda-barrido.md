# Tarea · barrido de la agenda de eventos (lunes 09:41)

Cambio OpenSpec `agenda-de-eventos` (16-11-2026). Lo ejecuta la tarea programada «MOTICIAS · agenda de eventos» con `/agenda-barrido` (Opus 5.5). Corre en la nube: no puede hacer `push`, así que lo que cambia en `data/eventos/` llega a `main` por el buzón del repositorio, y los contactos van directos a la base privada.

Respuesta corta: cada lunes, la agenda se pone al día sola. Lo nuevo queda en la cola «Por revisar» del gestor para que lo publique el editor jefe; los cambios de lo ya publicado (fecha, sede, enlace, cancelación) quedan como aviso en «Inicio»; los organizadores y sus contactos se completan en el CRM.

## Pasos

1. **Arranque.** `git pull` si se puede; `python3 -I src/eventos.py validar` (debe dar 0 errores) y `python3 -I src/eventos.py listar`. En la base: `select count(*) from agenda_envios where estado = 'recibido'` (si la tabla no existe, avisa: «falta aplicar la migración 015»).
2. **Lo que ya pasó.** `python3 -I src/eventos.py pasar-a-pasado`: lo terminado pasa a `pasado` y queda en el archivo (no se borra).
3. **Volver a comprobar lo publicado** (`estado` publicado, aplazado o cancelado, y los `fecha_por_confirmar`). Para cada uno abre su `url_oficial` o `url_inscripcion` (WebFetch) y compara fecha, sede, ciudad, precio y estado:
   - si todo coincide, pon `comprobado_at` = hoy y añade la fuente con la fecha de hoy (sin duplicar la URL: actualiza su `fecha`);
   - si algo cambió, **no publiques el cambio tú**: corrige el fichero solo si el organizador lo dice claramente (fecha nueva, «aplazado», «cancelado»), añade `revisiones` y `revised_at`, y deja además un aviso en la base: `insert into agenda_avisos (evento_id, tipo, detalle, fuente_url, origen) values (…, 'cambio_fecha' | 'cambio_sede' | 'cambio_enlace' | 'cancelado' | 'aplazado', '<qué cambió, de qué a qué>', '<url>', 'barrido');`
   - si un «por confirmar» ya tiene fecha publicada por el organizador, pon `inicio`/`fin`, deja `estado: propuesto` y avisa (`tipo` 'nuevo'): lo publica el editor jefe;
   - si la web no responde, no cambies nada; anótalo en el resumen.
4. **Buscar eventos nuevos** de los próximos cuatro meses en las fuentes de `verticals/movilidad.json → agenda.barrido.fuentes` (calendario de la AFE mes a mes, recintos y asociaciones), y con WebSearch por tema («congreso movilidad 2027», «jornada transporte público», «feria logística»…). Solo profesionales, más las grandes del sector con días profesionales (`publico: general`, marcadas «Abierta al público»); nada de consumo puro. Antes de dar de alta, busca duplicados (`listar` y misma ciudad y fecha). Cada nuevo: fichero JSON con todos los campos (ver `src/eventos.py`, `CAMPOS`), `estado: propuesto`, `origen: barrido`, `fuentes` con URL y fecha de hoy (la del organizador primero), coordenadas de la ciudad (`agenda.ciudades` del vertical) y `python3 -I src/eventos.py alta --json <fichero>`. Tope: 15 por pasada.
5. **Organizadores y contactos** (solo base privada; nada al repositorio). Para los eventos publicados sin cuenta en `agenda_organizadores` o con «Falta contacto» en el gestor:
   - la cuenta se casa por dominio (y por nombre en dominios compartidos como `gobiernodecanarias.org`); si no existe, créala con `origen = 'agenda'` y `etiquetas = '{organizador-eventos}'`;
   - el responsable (nombre y cargo) solo si lo publica el organizador o una nota de prensa identificable;
   - contactos en `crm_contactos` con `canal`, `valor`, `nivel` (`directo` si es de la persona; si no, el más cercano: `prensa` del evento, secretaría o correo `general`, `centralita`), `fuente_url` y `fuente_fecha`. Nada deducido: no se construyen correos a partir del nombre. Sin ninguno, la ficha queda «por localizar»;
   - respeta «No contactar» (`crm_cuentas_hoy.estado = 'no_contactar'` o `crm_personas.no_contactar_at`): esas no se tocan.
6. **Subir.** `python3 -I src/eventos.py validar` sin errores; `git add data/eventos` y commit `Agenda: barrido AAAA-MM-DD`; `push` si se puede; si no, `python3 -I src/buzon.py preparar --origen agenda-barrido` y cada `work/buzon/*.sql` con `execute_sql`. El cron `ghost_al_dia` rehace `moticias.com/agenda/` en cuanto el cambio llega a `main`.
7. **Registro.** `insert into agenda_barridos (ok, resumen, resultado) values (true|false, '<resumen en una línea>', '{"nuevos": n, "cambios": n, "revisados": n, "contactos": n, "errores": [...]}'::jsonb);`
8. **Aviso** (corto, para el móvil): nuevos en la cola (con enlace `https://app.moticias.com/gestor/?vista=agenda`), cambios detectados, fichas completadas y lo que no se pudo comprobar.
