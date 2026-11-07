# Firma y publicación en moticias.com (Ghost)

Respuesta corta: cada pieza lleva una firma y un estado que salen de una sola regla. Rutinaria → firma «G. Jordan, Redactor responsable» y se publica sola. Crítica, análisis o reportaje → firma «Rainer, Director de MOTICIAS» y queda en borrador hasta que Rainer la publique. Criterio del director, 7-11-2026.

## La regla

| Tipo de pieza | `risk` | `author` | `status` en `data/` | Estado en Ghost | Autor en Ghost |
|---|---|---|---|---|---|
| Noticia con al menos una fuente oficial, o dos profesionales de confianza que coinciden, y sin ningún criterio crítico | `rutinaria` | G. Jordan | `publicado` | `published` | usuario `g-jordan` |
| Noticia que cumple un criterio crítico (`verticals/movilidad.json` → `editorial.critical_criteria`) | `critica` | Rainer | `pendiente` | `draft` | usuario `rainer` |
| Análisis (`kind: analisis`) o reportaje (`kind: reportaje`) | `critica` | Rainer | `pendiente` | `draft` | usuario `rainer` |

Ante la duda, crítica. Cada pieza explica su clasificación en una frase en `review_note`. Las piezas firmadas por Rainer llevan la declaración de intereses (Movenbus) en `author_note`.

## Dónde vive

- Parámetros: `verticals/movilidad.json` → `editorial` (`default_author`, `director`, `critical_criteria`, `ghost_authors`, `ghost_status`).
- Código: `src/ghost_publish.py`. Busca cada usuario de Ghost por slug (`ghost_authors`) y, si no lo encuentra, por nombre. Si el usuario de G. Jordan no existe en Ghost, la pieza sale a nombre de Rainer y el resultado lo avisa en `avisos`.
- Las piezas críticas nunca se publican desde el script, aunque se pida `--status published`: se suben o actualizan como borrador. Las publica Rainer desde el panel de Ghost (también desde el móvil).

## Edición diaria

Al final de la rutina (`docs/tarea-edicion-diaria.md`, paso 7 quáter):

```bash
cd ~/moticias && python3 -I src/ghost_publish.py --date AAAA-MM-DD --status published
```

## Apertura y segunda en Ghost

La apertura del día es la entrada destacada de Ghost; la segunda lleva la etiqueta interna `#segunda`. Si la apertura prevista es crítica y espera al director, el publicador destaca la mejor rutinaria del día (`docs/tema-ghost.md`); la portada nunca enlaza una pieza en borrador.

## Páginas fijas

Aviso legal, privacidad, cookies y «Cómo trabajamos» viven en `data/paginas/<slug>.json` y se suben siempre como borrador:

```bash
cd ~/moticias && python3 -I src/ghost_publish.py --pages
```

Se publican solo cuando Rainer lo ordena expresamente («publica las legales»).

## Aplicación a las piezas ya publicadas (7-11-2026)

Se aplicó a las 74 piezas de las ediciones 1 a 3: 62 rutinarias (publicadas, G. Jordan) y 12 críticas (borrador, Rainer): 3 análisis, 3 reportajes y 6 noticias (dimisión de Óscar Puente; salida del presidente de Adif; consigna LZB de Renfe en plena investigación; huelgas ferroviarias de noviembre; desconvocatoria de Ouigo con Semaf; reproches de Iryo y Ouigo a Adif y el Ministerio con una sola fuente).

## Pendiente

- En Ghost, el usuario de G. Jordan tiene el slug `g`, no `g-jordan`. El script lo encuentra por nombre y funciona; para que la URL del autor sea `/author/g-jordan/`, cambia el slug en Ghost → Ajustes → Staff → G. Jordan.
