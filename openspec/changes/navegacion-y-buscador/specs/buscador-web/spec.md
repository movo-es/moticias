# Capacidad: buscador que entiende (web y agente)

Extiende `buscador-bajo-demanda` (cambio `plataforma-2027`). Código: `src/buscador.py` (agente), `src/export_search_index.py` (índice) y el JavaScript del tema de Ghost (hoy en `openspec/changes/navegacion-y-buscador/maqueta/index.html`).

## Requisito: un solo diccionario
Los sinónimos (`verticals/<vertical>.json → busqueda.sinonimos`) y la taxonomía son los mismos para el agente y para la web: ambos los leen del vertical o del índice generado a partir de él. Un término de la consulta acierta si él o cualquiera de sus equivalentes aparece en la pieza, por palabra completa con raíz común o por expresión.

#### Escenario: sinónimo
- CUANDO el lector busca «concesiones caducadas»
- ENTONCES encuentra piezas que dicen «vencidas», «prórroga» o «prolongación tácita», y la pieza de Cantabria del 6-11-2026 aparece la primera si no hay otro territorio en la consulta.

## Requisito: el topónimo es un filtro
Si la consulta nombra un territorio (por su nombre o por un alias), deja de ser palabra a buscar y pasa a ser filtro de `territorios`. El lector ve «Buscas … en <territorio>».

#### Escenario: territorio sin cobertura o con cobertura floja
- CUANDO el territorio pedido no tiene ninguna pieza que trate el asunto en su cabecera
- ENTONCES el buscador añade las piezas de las comunidades vecinas que sí lo tratan y lo dice: «Poco de Asturias; sí de Cantabria (vecina)». El veredicto para el agente es `parcial`, nunca `cubierto`.

## Requisito: erratas
Un término que no aparece en ninguna pieza se sustituye por la palabra más parecida del vocabulario de cabeceras (distancia de edición ≤ 1, o ≤ 2 si tiene seis letras o más) y se muestra «¿Quisiste decir …?». No se corrigen términos que sí existen.

## Requisito: índice estático
`src/export_search_index.py` genera `app/public/buscador/index.json` (taxonomía con alias y vecinos, sinónimos y una entrada por pieza con `status` publicable: id, cabecera, resumen recortado, fecha, tipo, autor, ejes, etiquetas, foto, URL, texto plano de búsqueda). Se regenera en cada edición (paso 7 ter) y lo sirve Vercel con CORS para `www.moticias.com` y caché de diez minutos. Al pasar de 2 MB se parte por años.

#### Escenario: índice inaccesible
- CUANDO el tema no puede cargar el índice
- ENTONCES usa la búsqueda nativa de Ghost y lo indica discretamente; nunca deja el cuadro sin respuesta.

## Requisito: sin resultado, encargo
Cuando una búsqueda devuelve cero piezas, o solo piezas de vecinas, el cuadro de lectura ofrece «Pídela: la investigamos y la escribimos», que abre el formulario de pieza bajo demanda con la consulta ya escrita.
