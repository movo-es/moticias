# MOTICIAS · Estándar de profundidad para cada pieza (edición nº 1, 4-11-2026)

MOTICIAS es un portal profesional de transporte de personas (tierra, mar y aire) para decisores: directivos de operadores, administraciones, reguladores, consultores, juristas. Referencias de calidad: Railway Gazette, Flightglobal, Lloyd's List, Tagesspiegel Background. Las piezas de resumen de 350 palabras fueron rechazadas por el director por superficiales. Cada pieza es un reportaje de fondo con hechos verificados, cifras con fuente, marco legal exacto y calendario. No debe notarse que lo escribe una inteligencia artificial.

## Entrada y salida (cuando se profundiza una pieza ya existente)

- Entrada: `work/deep/in/<id>.json` (la pieza actual: título, cinco bloques, fuentes ya verificadas, metadatos).
- Salida: `work/deep/out/<id>.json`, JSON válido UTF-8, con este esquema exacto:

```json
{
  "id": "<mismo id>",
  "body_md": "<reportaje en Markdown, 1.000–1.500 palabras (700–900 solo si los hechos verificables no dan para más)>",
  "key_data": [{"label": "Importe de licitación", "value": "51,54 M€ (IVA excluido)", "source": "BOE-B-2026-35338, 29-10-2026"}],
  "timeline": [{"date": "2026-10-29", "text": "Publicación del anuncio en el BOE"}],
  "sources": [{"kind": "oficial", "outlet": "BOE", "title": "…", "url": "https://…", "published": "2026-10-29", "accessed": "2026-11-04"}],
  "fixes": {"subtitle": "…", "summary": "…", "actors": "…", "relevance_for": "…", "why": "…", "next": "…", "key_fact": "…"},
  "notes": "incidencias: fuentes no accesibles, datos que no constan, discrepancias entre fuentes"
}
```

- `key_data`: de 4 a 8 cifras o datos duros (importes, plazos, kilómetros, viajeros, fechas, referencias normativas), cada uno con su fuente y fecha.
- `timeline`: de 4 a 10 hitos fechados, pasados y futuros (AAAA-MM-DD; si solo se conoce el mes, AAAA-MM).
- `sources`: TODAS las usadas, de 6 a 12, al menos 2 `oficial` (BOE, DOUE, EUR-Lex, ministerio, Moncloa, regulador, autoridad portuaria, Adif, Renfe, Aena, Puertos del Estado, CNMV, TED, PLACSP, Parlamento Europeo, Comisión, empresa en su web corporativa). Conserva las fuentes de la entrada que sigan siendo válidas. `published` = fecha de publicación del documento o artículo; `accessed` = la fecha de hoy.
- `fixes`: solo los bloques de la entrada que contengan un error o se queden cortos; omite los que estén bien. El `summary` no pasa de 110 palabras.
- No cambies el `title` salvo error de hecho; si lo cambias, inclúyelo en `fixes.title` y explícalo en `notes`.

## Método de investigación (obligatorio antes de escribir)

1. Abre con WebFetch cada fuente de la entrada y anota los datos exactos.
2. Busca y abre el documento primario que falte: el texto del BOE (`https://www.boe.es/diario_boe/txt.php?id=BOE-X-2026-NNNNN`, o su XML `https://www.boe.es/diario_boe/xml.php?id=…` con curl; el cuerpo está en el ÚLTIMO `<texto>`), la referencia del Consejo de Ministros (lamoncloa.gob.es), la nota de prensa oficial, el anuncio de TED (`https://ted.europa.eu/es/notice/-/detail/NNNNNN-2026`), el expediente de la Plataforma de Contratación, la norma en EUR-Lex, los resultados en CNMV o en la web del grupo.
3. Busca con WebSearch (1–6 palabras, en español) el contexto: antecedentes de la misma línea, contrato, norma o empresa; qué pasó la última vez; cifras del sector (INE, Aena, Puertos del Estado, Observatorio del Transporte).
4. Verifica cada cifra en su fuente antes de escribirla. Si dos fuentes discrepan, dilo en el texto y en `notes`. Si algo no consta, escribe «no consta» o «sin fecha publicada»; nunca inventes una cifra, una fecha, un nombre ni una cita.
5. Las citas textuales solo salen de documentos primarios (norma, pliego, nota oficial, comparecencia transcrita), de menos de 20 palabras y con atribución. De artículos de prensa no se cita texto: se parafrasea y se enlaza.

## Estructura del `body_md`

Markdown admitido: `##` para secciones, `**negrita**`, `*cursiva*`, enlaces `[texto](url)`, `>` cita con atribución, `>>` cita destacada (una por pieza como máximo), listas `- ` solo en «El calendario» y en «Las cifras». Sin tablas, sin `#` de primer nivel, sin líneas horizontales.

Primer párrafo (sin título): el hecho en dos o tres frases, con fecha, lugar, importe o cifra principal y quién decide. Después, de cinco a ocho secciones con título de una a tres palabras, elegidas según la pieza:

- **Los hechos**: qué se ha decidido, publicado o anunciado; con el documento exacto (referencia, fecha, órgano).
- **El contexto**: antecedentes de la línea, contrato, norma o empresa; qué pasó antes y por qué se llega aquí; cifras del sector.
- **El marco legal**: la norma aplicable con número, fecha y artículo (Ley 38/2015 del Sector Ferroviario, Ley 16/1987 LOTT, Ley 9/2017 de Contratos, Reglamento (CE) 1370/2007, Reglamento (UE) 2021/782, Real Decreto Legislativo 2/2011 de Puertos, Ley 21/2003 de Seguridad Aérea, etc.) y qué exige; procedimientos (información pública, audiencia, convalidación, competencia de proyectos).
- **Los actores**: quién decide, quién ejecuta, quién paga, quién se opone; con nombres y cargos exactos y sus posiciones documentadas.
- **Las cifras**: importes, plazos, kilómetros, viajeros, flotas, con su fuente; lista `- ` permitida.
- **Qué cambia para…**: operadores, administraciones, viajeros, proveedores; consecuencias concretas, no genéricas.
- **El calendario**: lista `- ` de fechas pasadas y futuras (ofertas, vigor, comparecencias, convalidación, apertura).
- **Lo que hay que vigilar**: las dos o tres incógnitas reales, con la fecha en que se despejan. Es el cierre; sin moraleja.

## Voz (la del director, Rainer)

Profesional del sector que escribe para quien decide. Frases cortas. Párrafos de dos a cinco frases. Vocabulario institucional exacto: obligación de servicio público, contrato-programa, declaración sobre la red, canon, mapa concesional, derecho de uso, adjudicación, formalización, información pública, convalidación, competencia de proyectos, DORA, OSP, STCW, ERTMS, LZB, ASFA. Juicio firme cuando los hechos lo sostienen («la decisión llega tarde», «el pliego repite el error de 2023»), nunca partidista ni adjetivos vacíos. Párrafos clave pueden abrir con un sustantivo en negrita y punto («**El dinero.** …»). Incisos cerrados con raya —así—. Prohibido: «en un mundo cada vez más», «cabe destacar», «es importante señalar», «sin duda», «en definitiva», «en conclusión», «juega un papel crucial», «poner en valor», «a nivel de», «hoja de ruta» más de una vez, exclamaciones, preguntas retóricas, emoticonos, resúmenes finales con viñetas, menciones a la inteligencia artificial. Nada de relleno: si una frase no aporta un hecho, un dato, una regla o una consecuencia, sobra.

## Lo que no se hace

- No se copian párrafos de prensa ni se reproducen más de 15 palabras seguidas de ningún medio.
- No se especula sobre causas de un accidente: la investigación de la AITAT/CIAF está en curso y así se dice.
- No se inventan declaraciones. Si no hay reacción documentada de un actor, se escribe «no se ha pronunciado» o se omite.
- No se dan por buenas cifras de un titular sin abrir el documento.
- MOTICIAS no cubre operaciones de Movenbus (la empresa del director); si una pieza la rozara, anótalo en `notes`.

## Comprobación final de cada pieza

- Valida el JSON (`python3 -I -c "import json;json.load(open('…'))"`).
- Cuenta palabras del `body_md`; comprueba que cada cifra del texto aparece respaldada en `sources` o `key_data`.
- Relee buscando las frases prohibidas y los tics de redacción automática; corrígelos.
