# Cambio: comprobador-diario

Fecha: 16 de noviembre de 2026. Origen: encargo de Rainer del 15-11 (dentro del de la agenda): «horarios aleatorios en horario diurno de España para simular clics en todas las cajas de contenidos patrocinados una vez al día, a) para mejorar el SEO de los clientes publicitarios, b) para que en el panel de publicidad sea auditable que los enlaces funcionan». Estado: **aplicado y archivado el 16-11-2026** (decisión 7 b de `agenda-de-eventos`, «sí a todo»).

Respuesta corta: el comprobador que ya existía (`seguimiento-y-seo`) pasa de laborables a todos los días, una vez por enlace y día a hora al azar entre las 9 y las 21 de Madrid, y el panel lo demuestra: «Comprobado hoy a las HH:MM · funciona / no funciona», historial de 30 días descargable en CSV para el anunciante y correo al editor jefe si un enlace falla dos veces seguidas.

## Lo que no se hace, y por qué (a)

Las visitas del comprobador no se cuentan como clics ni se presentan como mejora de SEO:
- Google no ve una visita de servidor: no sube a nadie ni un puesto.
- Contarlas como clics haría falsa la cifra que ve el anunciante. Eso es fraude publicitario y pone en riesgo la credibilidad de MOTICIAS.
- Contradice la regla de `seguimiento-y-seo` (9-11-2026): ni robots, ni comprobador, ni editor jefe cuentan como lectores.

## Qué cambia (b)

1. Cron `comprobar` de Vercel: `23 8-19 * * *` (UTC; de 9 a 21 en Madrid), todos los días. La comprobación de los enlaces de inscripción de la agenda sigue solo en laborables.
2. `src/seguimiento.py → comprobar`: una vez al día por enlace; probabilidad 0,25 por pasada, 0,9 desde las 18 h y segura en la última pasada (20 h) si aún no se comprobó.
3. Correo al editor jefe cuando un enlace falla dos comprobaciones seguidas (una vez por racha).
4. Panel de seguimiento: «Comprobado hoy a las HH:MM · funciona / no funciona» y «Descargar 30 días (CSV)» (`/api/gestor?a=comprobaciones_csv&anuncio=…&dias=30`).
5. Pruebas sin red: `tests/test_comprobador.py`.
