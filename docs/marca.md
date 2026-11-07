# MOTICIAS · Marca v1 (7 de noviembre de 2026)

Respuesta corta: MOTICIAS se presenta con un símbolo propio, la **Glorieta** —dos arcos de red, uno azul 286 y otro cielo, que bajan a un anillo de intercambio y dibujan una M—, el nombre **MOTICIAS** en mayúsculas y el tagline **«Noticias con M de Movilidad y Transportes»**. Comparte con el grupo el azul 286, las líneas de red y el redondeo, sin copiar ninguna marca del grupo. Este paquete trae los logos con el texto ya convertido a trazados, los favicons, la imagen para compartir, las piezas para Ghost y las fichas de diseño (`tokens/`).

## 1. Nombre y tagline

- **Nombre:** MOTICIAS, siempre en mayúsculas en el logotipo. En texto corrido, «MOTICIAS». Dominio: moticias.com.
- **Tagline oficial:** «Noticias con M de Movilidad y Transportes». La M va en Señal (naranja) y en peso 800; el resto, en tinta y peso 500. No se traduce ni se abrevia.
- **Alcance:** movilidad, transporte de viajeros y, más adelante, logística (tierra, mar y aire). El símbolo no representa ningún vehículo ni modo concreto, así que la logística entra como sección sin tocar la marca.

## 2. El símbolo: la Glorieta

Dos líneas de plano de red suben y bajan en arco, como un puente o la boca de un túnel, y sus tramos interiores bajan a un anillo, como dos vías que entran en una glorieta o en un intercambiador. Juntas se leen como M sin dibujar la V central (la que usa MUFMI).

Construcción, en una retícula de 120 unidades:

- Arco izquierdo: `M16 100 V46 A19 19 0 0 1 54 46 V68`, trazo 14, extremos redondeados, azul 286.
- Arco derecho: `M66 68 V46 A19 19 0 0 1 104 46 V100`, trazo 14, extremos redondeados, cielo.
- Anillo: centro (60, 84), radio 12,5, trazo 7, sin relleno, tinta.
- Caja exacta del símbolo: `viewBox="8 19 104 89"`.
- Favicon y tamaños pequeños: trazo 18, anillo de radio 13 y trazo 9, tramos interiores hasta y = 66, sobre azulejo azul 286 con esquinas de radio 23 %.

## 3. Versiones y ficheros

| Fichero | Uso |
|---|---|
| `svg/moticias-logo-horizontal.svg` | Versión principal con tagline: cabecera de la web en escritorio, documentos, presentaciones |
| `svg/moticias-logo-horizontal-sin-claim.svg` | Cabecera compacta, vídeo, firmas, tamaños medianos |
| `svg/moticias-logo-vertical.svg` | Carteles, portadas, formatos cuadrados |
| `svg/moticias-simbolo.svg` | Símbolo suelto, sellos, marcas de agua |
| `…-negativo.svg` | Sobre tinta (#0B1B3F) o azul 286: arcos en blanco y cielo claro, M del tagline en Señal clara |
| `…-mono.svg` / `…-mono-blanco.svg` | Una sola tinta: prensa, grabado, sellos, fondos fotográficos |
| `favicon/favicon.svg`, `favicon.ico`, `favicon-16.png`, `favicon-32.png` | Pestaña del navegador |
| `favicon/apple-touch-icon.png` (180), `icon-192.png`, `icon-512.png`, `site.webmanifest` | Iconos de móvil y de aplicación |
| `redes/og-image.png` (1200 × 630) | Imagen al compartir en LinkedIn, X, WhatsApp; `og:image` por defecto |
| `redes/avatar-400.png` | Foto de perfil de LinkedIn, X, YouTube |
| `ghost/logo-cabecera.png`, `logo-cabecera-negativo.png` | Logotipo de publicación en Ghost (160 px de alto) |
| `ghost/icono-publicacion.png` (512) | Icono de publicación en Ghost |
| `ghost/logo-boletin.png` (1200 de ancho) | Cabecera del boletín por correo |
| `tokens/tokens.json`, `tokens/moticias.css` | Colores, tipografías y radios como fichas y variables CSS |

Los SVG no dependen de ninguna fuente: el texto está convertido a trazados con Plus Jakarta Sans (licencia OFL).

## 4. Color

| Ficha | Hex | Uso | Contraste sobre blanco |
|---|---|---|---|
| Azul 286 | `#0033A1` | Arco izquierdo, enlaces, botones, color de acento en Ghost | 10,6:1 |
| Cielo | `#2E9BE6` | Arco derecho, gráficos. **No para texto sobre blanco** | 3,0:1 |
| Tinta | `#0B1B3F` | Anillo, nombre, texto, fondos oscuros | 16,9:1 |
| Señal | `#F26A1B` | La M del tagline, alertas y plazos. Poco y nunca en manchas grandes | 3,1:1 (solo texto grande o gráficos) |
| Niebla | `#F4F6FB` | Fondos de sección | — |
| Línea | `#C9D2E6` | Filetes, bordes, cápsulas | — |
| Cielo claro | `#8FD0FF` | Arco derecho en negativo | 6,4:1 sobre azul 286 |
| Señal clara | `#FFB27A` | M del tagline en negativo | 9,6:1 sobre tinta; 6,0:1 sobre azul 286 |

El azul 286 es el mismo que usa Movenbus; MOVO usa `#12329B`. Esto acerca a MOTICIAS al grupo sin confundirla con él.

## 5. Tipografía

- **Plus Jakarta Sans** 800 y 500: nombre, tagline, navegación, etiquetas, botones. Es la alternativa abierta a Aspira (la de Movenbus).
- **Newsreader** 400 y 600: titulares y texto de las piezas (la que ya usa el portal).
- **IBM Plex Mono** 400 y 500: fechas, cifras, referencias del BOE, datos.

Las tres están en Google Fonts.

## 6. Reglas de uso

- **Área de respeto:** alrededor del logotipo, como mínimo la altura de las mayúsculas de MOTICIAS.
- **Tamaños mínimos:** con tagline, 360 px de ancho (por debajo, el tagline baja de 13 px); sin tagline, 140 px; símbolo suelto, 24 px. Por debajo de 24 px se usa siempre el favicon.
- **Fondos:** blanco, niebla, tinta o azul 286. Sobre foto, solo la versión mono-blanco y con la foto oscurecida.
- **No se hace:** cambiar los colores de los arcos o intercambiarlos; rellenar el anillo; poner el naranja en el símbolo; deformar, girar o añadir sombras o degradados; reescribir el nombre en otra tipografía; separar el tagline del nombre en el logotipo horizontal; poner logos de MUFMI, Movenbus o MOVO junto al de MOTICIAS dentro de una pieza editorial.

## 7. Relación con el grupo

Lo que se repite educa la vista: los azules, las líneas de red con extremos redondeados, la cápsula en etiquetas y botones, la sans geométrica y el nombre en mayúsculas. Lo que cambia separa la marca: la M de arcos con anillo y el naranja Señal. La independencia editorial manda: ninguna pieza cita ni muestra soluciones del grupo; la conexión la hace la plataforma, siempre señalizada.

## 8. Implantación

**Ghost (Ajustes → Design & branding → Brand):**
- Accent color: `#0033A1`.
- Publication icon: `ghost/icono-publicacion.png`.
- Publication logo: `ghost/logo-cabecera.png` (en un tema oscuro, `logo-cabecera-negativo.png`).
- Cabecera del boletín (Ajustes → Newsletters → Header image): `ghost/logo-boletin.png`.
- `og:image` por defecto (Ajustes → General → Metadata / Social accounts): `redes/og-image.png`.

**Favicon SVG y manifiesto en el tema** (Ghost genera el favicon a partir del icono de publicación; para servir además el SVG, se copian los ficheros de `favicon/` en `assets/marca/` del tema y se añade en `default.hbs`):

```html
<link rel="icon" href="{{asset "marca/favicon.ico"}}" sizes="any">
<link rel="icon" href="{{asset "marca/favicon.svg"}}" type="image/svg+xml">
<link rel="apple-touch-icon" href="{{asset "marca/apple-touch-icon.png"}}">
<link rel="manifest" href="{{asset "marca/site.webmanifest"}}">
<meta name="theme-color" content="#0033A1">
```

Las rutas de iconos de `site.webmanifest` (`/icon-192.png`, `/icon-512.png`) se ajustan a donde queden servidas.

**Schema.org `Organization`:** `logo` → la URL pública de `favicon/icon-512.png` (cuadrado, PNG, más de 112 px, como recomienda Google), `name` → «MOTICIAS», `slogan` → el tagline, y `sameAs` con los perfiles sociales.

**CSS:** `tokens/moticias.css` define las variables `--mt-*`; el tema y la sala de redacción las usan en lugar de colores sueltos.

## 9. Dónde va en el repositorio

Propuesta, para cumplir la regla de que lo específico de cada vertical vive en su configuración:

- Ficheros: `verticals/movilidad/marca/` (este paquete tal cual).
- Documento: `docs/marca.md` (este README).
- Configuración: en `verticals/movilidad.json`, un bloque `brand` con `name`, `tagline`, `domain`, la ruta de la carpeta de marca y los colores de `tokens/tokens.json`, para que el segundo vertical (turismo) tenga el suyo sin tocar código.
