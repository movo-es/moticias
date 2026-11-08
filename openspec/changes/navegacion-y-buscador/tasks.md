# Tareas · navegacion-y-buscador

- [x] `verticals/movilidad.json`: `taxonomia` (5 modos, 14 submodos, 7 temas, 22 territorios con alias y vecinos) y `busqueda.sinonimos` (29 grupos).
- [x] `src/taxonomia.py`: carga, alias, inferencia, `informe` / `aplicar` / `pieza`.
- [x] Clasificar las 74 piezas publicadas (`modo`, `submodo`, `temas`, `territorios`); informe revisado.
- [x] `src/buscador.py`: sinónimos, territorio como filtro, vecinas, erratas, `--territorio`, contexto en `--json`.
- [x] `src/export_search_index.py` → `app/public/buscador/index.json`; CORS y caché en `vercel.json`.
- [x] `src/ghost_publish.py`: etiquetas de los tres ejes con slug fijo, sin duplicar etiquetas libres; `--etiquetas` crea o corrige las 41 etiquetas en Ghost.
- [x] Maqueta navegable con datos reales (`maqueta/index.html`, `construir.py`), publicada como artefacto el 9-11-2026.
- [x] Docs y comandos: `CLAUDE.md`, `docs/manual-operativo.md`, `docs/tarea-edicion-diaria.md`, `docs/arquitectura.md`, `docs/gestores-portal.md`, `.claude/commands/edicion-diaria.md`, `.claude/commands/pieza-bajo-demanda.md`.
- [ ] Rainer: probar la maqueta en el móvil y decir qué cambia (color del módulo del director, orden de los menús, nombres de temas).
- [ ] Con claves de Ghost en el entorno (rutina de la mañana o Vercel): `python3 -I src/ghost_publish.py --etiquetas` y republicar las 74 piezas (`--all --status published`; las del director siguen en borrador) para que lleven las etiquetas de los ejes.
- [ ] Comprobar que `https://app.moticias.com/buscador/index.json` responde tras el despliegue de Vercel.
- [ ] Cuando `publicar-en-ghost-v1` versione el tema en `ghost/theme/`: llevar la barra, los menús, el mapa, el módulo del director, la portada móvil y `assets/buscador.js` desde la maqueta; `routes.yaml` con `/tierra/`, `/mar/`, `/aire/`, `/logistica/`, `/analisis/` y `/territorio/<id>/`; caída a la búsqueda nativa si el índice no carga.
- [ ] Formulario de pieza bajo demanda enlazado desde «Pídela» (depende del cambio `plataforma-2027 › buscador-bajo-demanda`).
- [ ] Partir el índice por años cuando pase de 2 MB (previsto para 2028).
- [ ] Archivar el cambio cuando el tema esté en producción con los menús y el buscador.
