# Tareas · editor-jefe-y-crm

- [x] `src/firma.py` (informe · decidir), `editorial.firma_director`, nota de intereses sin nombre, autor de Ghost por firma; rutina diaria (paso FIRMA y análisis del día).
- [x] `src/redaccion.py`: editar, corrección, retirar/restaurar, aprobar, otro enfoque con IA con control de cifras nuevas.
- [x] `api/gestor.py`: permisos por perfil en el servidor; `redaccion`, `firma`, `anuncio` (crear, niveles, propuestas), `publicidad` (pública), `crm_*`, `crm`, `miembros`, `miembro`; equipo en la base; marca `moticias_jefe` y `yo` con CORS para www.moticias.com.
- [x] Gestor (`app/public/gestor/index.html`): editor con vista previa, IA con original y propuesta, retirar, firma con cupo; publicidad con niveles y vista previa; CRM (hoy, tipos, buscador, ficha, personas, estado, pasos, contratos, historial, archivo); suscriptores por categoría; equipo.
- [x] Script del sitio `app/public/sitio/m.js`: huecos de publicidad por nivel e icono del editor jefe.
- [x] Migración `003_gestor_crm.sql`.
- [x] Pruebas: recorrido completo en Chrome a 390 px contra un banco local (editor, IA, cifras, firma, retirar, publicidad, CRM, suscriptores, equipo, permisos de oficina) y el script del sitio sobre copias de las páginas reales.
- [x] Proyecto Supabase «moticias» (Frankfurt, `cjrntzaqmvhgscdgiehs`, creado el 9-11-2026 con el visto bueno de Rainer al coste), migraciones 003 y 004 aplicadas, huella de la llave guardada, y en Vercel `SUPABASE_URL`, `SUPABASE_ANON_KEY` y `MOTICIAS_BD_CLAVE` (esta última generada en el navegador: no la ha visto nadie). Comprobado: sin la llave no se lee ni se escribe nada.
- [x] Ghost → Code injection → Site footer: `<script src="https://app.moticias.com/sitio/m.js" defer></script>` añadido el 9-11-2026 (`ghost/inyeccion-pie.html`); comprobado en www.moticias.com sin errores.
- [ ] Desplegar en producción con las variables de la base (fusionar #11). Rainer: entrar en el gestor con su cuenta (o la contraseña común) y darse de alta como editor jefe en «Equipo»; probar la IA en una pieza.
