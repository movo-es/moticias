/* MOTICIAS · script del sitio (www.moticias.com). Lo carga la inyección de código del pie de Ghost:
   <script src="https://app.moticias.com/sitio/m.js" defer></script>
   Dos cosas, nada más (cambio OpenSpec editor-jefe-y-crm, decisiones de Rainer del 9-11-2026):
   1. Publicidad y patrocinios: rellena los huecos con las cajas activas del gestor (app.moticias.com/api/gestor?a=publicidad),
      por niveles (premium: cabecera y lateral del artículo; estándar: portada y cierre del artículo; básico: antes del pie).
      Etiqueta siempre visible (art. 20 LSSI) y enlace rel="sponsored" en TODAS las cajas, también en las del grupo. Nunca
      dentro del texto de una pieza. Si no hay caja pagada para un hueco, va la del grupo («Contenido patrocinado · servicio
      del grupo») o se queda la que pinta el tema.
   2. Editor jefe: si este navegador tiene la marca «moticias_jefe» (la pone el gestor al entrar el superadministrador), pregunta
      al gestor si de verdad lo es (con su sesión) y, solo entonces, enseña un icono discreto en cada noticia con Editar, Otro
      enfoque con IA, Patrocinio y retoques, y Retirar. La marca no da ningún permiso: todo se comprueba en el servidor.
   3. Seguimiento: cuenta una visualización cuando una caja (publicidad, patrocinio o «Contenido patrocinado» del texto) se ve
      al menos a medias, y un clic cuando se pulsa su enlace (POST /api/gestor?a=evento). No cuenta las visitas del editor jefe
      ni de navegadores automatizados.
   4. Tipo de contenido (cambio tipos-de-contenido, 15-11-2026): en los listados, una marca pequeña junto a cada titular
      («Análisis», «Reportaje», «Noticia», «Nota de prensa · Comunicado de …»), leída de
      app.moticias.com/buscador/tipos.json (lo genera src/export_search_index.py). Dentro de cada pieza la marca ya va
      en el cuerpo del post (src/ghost_publish.py), así que no depende de este script ni del tema.
   6. Pinta las páginas de sección con sus piezas (la plantilla del tema salía vacía).
      En /la-voz-del-editor/, la última columna entera y las anteriores en una columna estrecha a la derecha (17-11-2026).
   1 ter. Nunca dos cajas de publicidad o patrocinio una encima de otra sin contenido entre ellas, en ninguna página (17-11-2026).
   5. Oculta la marca «Powered by Ghost» de la ventana de entrada y suscripción de Ghost.
   7. Menú con submenús (cambio menu-y-voz-del-editor, 16-11-2026): Portada · La voz del editor (destacado fijo) · Tierra ▾ ·
      Mar ▾ · Aire ▾ · Logística ▾ · Temas ▾ · Regiones ▾ · Análisis. Datos y recuentos de tipos.json → menu. En el móvil la
      barra sigue en su sitio (no se pega arriba ni tapa los titulares) y los submenús se abren como hoja inferior.
   Sin dependencias; si algo falla, el sitio sigue igual. */
(function () {
  "use strict";
  var API = "https://app.moticias.com";
  var d = document;
  var E = function (s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]; }); };
  var _tipos = null;
  var tiposJSON = function () { return _tipos || (_tipos = fetch(API + "/buscador/tipos.json").then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })); };
  var css = d.createElement("style");
  css.textContent =
    ".mtx-hueco{margin:14px auto}.mtx-hueco.mtx-cab{max-width:1180px;padding:0 16px}.mtx-hueco .ad{margin:0}" +
    ".ad .ad-img{display:block;width:100%;height:auto;border-radius:6px;margin:0 0 8px}" +
    ".mtx-ed{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;margin-left:6px;border-radius:50%;" +
    "font:13px/1 system-ui,sans-serif;color:#111;background:#f1efe8;border:1px solid #d9d6cc;text-decoration:none;vertical-align:middle;opacity:.45;transition:opacity .15s}" +
    ".mtx-ed:hover,.mtx-ed:focus{opacity:1}@media(hover:none){.mtx-ed{opacity:.7}}" +
    ".mtx-fab{position:fixed;right:14px;bottom:calc(14px + env(safe-area-inset-bottom));z-index:9999;font:14px/1.3 system-ui,sans-serif}" +
    ".mtx-fab>button{width:42px;height:42px;border-radius:50%;border:1px solid #333;background:#111;color:#fff;font-size:18px;opacity:.55;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.2)}" +
    ".mtx-fab>button:hover,.mtx-fab.on>button{opacity:1}" +
    ".mtx-fab ul{display:none;position:absolute;right:0;bottom:50px;margin:0;padding:6px;list-style:none;background:#fff;border:1px solid #ddd;border-radius:12px;box-shadow:0 6px 24px rgba(0,0,0,.18);min-width:230px}" +
    ".mtx-fab.on ul{display:block}.mtx-fab li a{display:block;padding:10px 12px;border-radius:8px;color:#111;text-decoration:none}.mtx-fab li a:hover{background:#f3f3f1}" +
    ".mtx-fab li.t{padding:6px 12px 4px;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#888}.mtx-fab li a.r{color:#a12b2b}";
  d.head.appendChild(css);

  // ---------- 0 bis. Favicon ----------
  // El favicon de MOTICIAS (decisión de Rainer, 15-11-2026; fuente: ghost/marca/). El tema, sin versionar, declara su propio
  // favicon.svg y la clave de integración no puede cambiar el icono del sitio en Ghost: aquí se retiran los que haya y se
  // pone el nuestro. Lo definitivo es subirlo en Ghost (Settings → Design & branding → Publication icon) y al tema.
  (function () {
    var ICONO = "https://storage.ghost.io/c/09/7e/097ec773-4043-4062-afef-953ef8d3b4ed/content/images/2026/11/favicon-512.png", APPLE = "https://storage.ghost.io/c/09/7e/097ec773-4043-4062-afef-953ef8d3b4ed/content/images/2026/11/apple-touch-icon-180.png";
    [].forEach.call(d.querySelectorAll('link[rel~="icon"], link[rel="apple-touch-icon"]'), function (l) { l.parentNode.removeChild(l); });
    var i = d.createElement("link"); i.rel = "icon"; i.type = "image/png"; i.sizes = "512x512"; i.href = ICONO; d.head.appendChild(i);
    var t = d.createElement("link"); t.rel = "apple-touch-icon"; t.sizes = "180x180"; t.href = APPLE; d.head.appendChild(t);
  })();

  // ---------- 0. La marca no se traduce ----------
  // Los traductores automáticos del navegador tienden a convertir «MOTICIAS» en «noticias»/«news»: la marca se marca como no
  // traducible donde aparece como marca (cabecera, logo, pie).
  [].forEach.call(d.querySelectorAll(".brand, .logo, header.masthead a[aria-label], footer.site .brand, footer.site .wrap > :first-child"), function (el) { el.setAttribute("translate", "no"); el.classList.add("notranslate"); });

  // ---------- 1. Publicidad ----------
  var seccion = (function () {
    var a = d.querySelector("article.article");
    if (a) return a.className.replace(/\barticle\b/, "").trim().split(/\s+/)[0] || "";
    return (location.pathname.match(/^\/([a-z-]+)\/?$/) || [])[1] || "";  // páginas de sección: /la-voz-del-editor/, /tierra/… (17-11-2026)
  })();
  function elegir(lista, usadas) {
    var c = (lista || []).filter(function (x) { return !usadas[x.id] && (!x.secciones.length || x.secciones.indexOf(seccion) >= 0); });
    var pagadas = c.filter(function (x) { return x.tipo !== "grupo"; });
    if (pagadas.length) c = pagadas;
    // Una caja pensada para esta sección va delante de las genéricas del mismo rango (decisión de Rainer, 17-11-2026).
    var propias = c.filter(function (x) { return x.secciones.length; });
    if (propias.length) c = propias;
    if (!c.length) return null;
    var nivel = c[0].nivel; c = c.filter(function (x) { return x.nivel === nivel; });
    var total = c.reduce(function (s, x) { return s + (x.peso || 1); }, 0), r = Math.random() * total;
    for (var i = 0; i < c.length; i++) { r -= (c[i].peso || 1); if (r <= 0) { usadas[c[i].id] = 1; return c[i]; } }
    usadas[c[0].id] = 1; return c[0];
  }
  function utm(u, x, hueco) {
    try { var url = new URL(u); if (!/^https?:$/.test(url.protocol)) return u; if (!url.searchParams.get("utm_source")) { url.searchParams.set("utm_source", "moticias"); url.searchParams.set("utm_medium", x.tipo); url.searchParams.set("utm_campaign", x.campana); url.searchParams.set("utm_content", hueco); } return url.toString(); } catch (e) { return u; }
  }
  function caja(x, hueco, ancha) {
    var rel = "sponsored noopener";  // sin excepción: también las cajas del grupo
    return '<aside class="ad ' + (ancha ? "ad-wide" : "ad-side") + (x.tipo === "grupo" ? " house" : "") + '" aria-label="' + E(x.etiqueta) + '" data-mtx="' + E(x.id) + '" data-mtx-h="' + E(hueco) + '">' +
      '<span class="ad-label">' + E(x.etiqueta) + "</span>" +
      '<a class="ad-body" href="' + E(utm(x.url, x, hueco)) + '" rel="' + rel + '" target="_blank">' +
      (x.imagen ? '<img class="ad-img" src="' + E(x.imagen) + '" alt="" loading="lazy">' : "") +
      '<span class="ad-text">' + (x.anunciante ? '<span class="ad-brand">' + E(x.anunciante) + "</span>" : "") + "<b>" + E(x.titular) + "</b>" +
      (x.texto ? '<span class="ad-p">' + E(x.texto) + "</span>" : "") + '<span class="ad-cta">' + E(x.cta || "Más información") + " →</span></span></a></aside>";
  }
  function publicidad(datos) {
    var H = (datos && datos.huecos) || {}, usadas = {}, x;
    // Como mucho tres huecos de pago por página (16-11-2026); las cajas del grupo no cuentan.
    var tope = (datos && datos.tope_pago) || 3, pagadas = 0, elegir0 = elegir;
    elegir = function (lista, us) {
      var l = pagadas >= tope ? (lista || []).filter(function (c) { return c.tipo === "grupo"; }) : lista;
      var c = elegir0(l, us); if (c && c.tipo !== "grupo") pagadas++; return c;
    };
    // El hueco «cabecera» (banda bajo la cabecera) ya no se pinta: quedaba encima de la apertura (decisión de Rainer, 15-11-2026).
    // Premium · portada: un escalón por debajo de la apertura, a la derecha; en el móvil, franja bajo los titulares visuales.
    var cover = d.querySelector("section.cover");
    if (cover && (x = elegir(H["portada-premium"], usadas))) premium(x, cover, datos);
    // Premium · lateral del artículo
    var lat = d.querySelector("aside.m-aside");
    if (lat && (x = elegir(H["articulo-lateral"], usadas))) { var l = d.createElement("div"); l.className = "m-box mtx-hueco"; l.innerHTML = caja(x, "articulo-lateral", false); lat.insertBefore(l, lat.firstChild); }
    // Estándar · cierre del artículo (sustituye a la caja que pinta el tema solo si hay caja)
    var fin = d.querySelector(".ad-end");
    if (fin && (x = elegir(H["articulo-cierre"], usadas))) fin.innerHTML = caja(x, "articulo-cierre", false);
    // Estándar · huecos de la portada
    [].forEach.call(d.querySelectorAll(".ad-block .ad.ad-wide"), function (n) { var y = elegir(H["portada-medio"], usadas); if (y) n.outerHTML = caja(y, "portada-medio", true); });
    // Básico · antes del pie
    var pie = d.querySelector("footer.site");
    if (pie && (x = elegir(H.pie, usadas))) { var p = d.createElement("div"); p.className = "mtx-hueco mtx-cab"; p.innerHTML = caja(x, "pie", true); pie.parentNode.insertBefore(p, pie); }
    sinApilar();
  }
  // ---------- 1 ter. Nunca dos cajas una encima de otra (decisión de Rainer, 17-11-2026) ----------
  // En ninguna página quedan dos cajas de publicidad, patrocinio o «Contenido patrocinado» seguidas en vertical sin contenido
  // entre ellas (texto visible, imagen o vídeo; los comentarios, que suelen estar vacíos, no separan). Si pasa, se queda la de más rango (contenido patrocinado del texto >
  // pagada > del grupo o del tema) y, a igualdad, la de arriba; la otra se quita con su hueco. Las que van una al lado de otra
  // (lateral del artículo) no cuentan. Se comprueba al poner la publicidad y cada vez que se pinta una sección.
  var SEL_AD = "aside.ad, aside.mtx-ban, aside.contenido-patrocinado";
  function visible(el) { var r = el.getBoundingClientRect(); return r.width > 2 && r.height > 2; }
  function rango(el) {
    if (el.matches("aside.contenido-patrocinado")) return 3;
    return el.hasAttribute("data-mtx") && !el.classList.contains("house") ? 2 : 1;
  }
  function separadas(a, b) {
    var w = d.createTreeWalker(d.body, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT), n;
    w.currentNode = a;
    while ((n = w.nextNode()) && n !== b) {
      if (a.contains(n)) continue;
      if (n.nodeType === 3) {
        var pe = n.parentElement;
        if (n.nodeValue.trim() && pe && !/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(pe.tagName) && visible(pe)) return true;
      } else if (/^(IMG|PICTURE|VIDEO|CANVAS|svg)$/.test(n.tagName) && n.getBoundingClientRect().height > 24) return true;
    }
    return false;
  }
  function quitarCaja(el) {
    var c = el.closest(".mtx-hueco, section.ad-block, .ad-end, section.mtx-premium");
    if (c && c.querySelectorAll(SEL_AD).length === 1) c.remove(); else el.remove();
  }
  function sinApilar() {
    for (var vuelta = 0; vuelta < 10; vuelta++) {
      var ads = [].filter.call(d.querySelectorAll(SEL_AD), function (el) { return visible(el) && !el.parentElement.closest(SEL_AD); }), quitada = false;
      for (var i = 0; i + 1 < ads.length && !quitada; i++) {
        var a = ads[i], b = ads[i + 1], ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
        if (ra.left >= rb.right || rb.left >= ra.right) continue;  // una al lado de otra
        if (separadas(a, b)) continue;
        quitarCaja(rango(b) > rango(a) ? a : b); quitada = true;
      }
      if (!quitada) return;
    }
  }
  // ---------- 1 bis. Banner premium (cambio banner-premium, 16-11-2026) ----------
  css.textContent +=
    ".mtx-premium{margin:28px 0 0}.mtx-esc{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:28px;align-items:start}" +
    ".mtx-mas h3{font:700 12px/1.4 system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#5d6b82;margin:0 0 6px;border-top:3px solid #0b2545;padding-top:10px}" +
    ".mtx-mas a{display:block;padding:10px 0;border-bottom:1px solid #dfe4ec;color:#0b2545;text-decoration:none;font:500 16px/1.3 Newsreader,Georgia,serif}.mtx-mas a:hover{text-decoration:underline}" +
    ".mtx-mas small{display:block;font:600 10.5px/1.4 system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:#7a1f2b;margin-bottom:2px}" +
    ".mtx-ban{position:relative;border-radius:12px;overflow:hidden;border:1px solid #d8dde6;background:#fff;margin:0}" +
    ".mtx-ban-lab{position:absolute;top:0;left:0;z-index:3;background:#fff;color:#4a5568;font:700 10px/1 system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;padding:6px 9px;border-bottom-right-radius:8px;border-right:1px solid #d8dde6;border-bottom:1px solid #d8dde6}" +
    ".mtx-ban img{display:block;width:100%;height:100%;object-fit:cover}.mtx-ban a.mtx-ban-a{position:absolute;inset:0;z-index:1}" +
    ".mtx-ban-t{position:relative;height:100%;padding:30px 22px 18px;display:flex;flex-direction:column;justify-content:center;gap:8px}" +
    ".mtx-ban-t .m{font:700 11px/1.3 system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;opacity:.85}.mtx-ban-t b{font:600 22px/1.15 Newsreader,Georgia,serif}" +
    ".mtx-ban-t .p{font:500 14px/1.4 system-ui,sans-serif;opacity:.92}" +
    ".mtx-ban-t .cta{position:relative;z-index:2;align-self:flex-start;margin-top:4px;font:700 13px/1 system-ui,sans-serif;padding:10px 14px;border-radius:999px;border:0;cursor:pointer;text-decoration:none}" +
    ".mtx-ban.bajo .mtx-ban-t{flex-direction:row;align-items:center;gap:18px;padding:24px 22px 14px}.mtx-ban.bajo .mtx-ban-t .cta{align-self:center;margin:0}.mtx-ban.bajo .mtx-ban-t .p{display:none}.mtx-ban.bajo .mtx-ban-t b{font-size:19px;flex:1}" +
    "@media(max-width:760px){.mtx-esc{grid-template-columns:1fr;gap:0}.mtx-mas{display:none}.mtx-ban{height:auto!important;aspect-ratio:358/120;grid-column:auto!important}" +
    ".mtx-ban-t{padding:28px 14px 10px;gap:10px;flex-direction:row;align-items:center}.mtx-ban-t .m,.mtx-ban-t .p{display:none}" +
    ".mtx-ban-t b,.mtx-ban.bajo .mtx-ban-t b{font-size:16px;line-height:1.2;flex:1;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.mtx-ban-t .cta{font-size:12px;padding:8px 10px;align-self:center;margin:0}}" +
    ".mtx-fv{position:fixed;inset:0;background:rgba(11,37,69,.45);z-index:9998}.mtx-fm{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:9999;width:min(520px,calc(100% - 32px));max-height:88vh;overflow:auto;background:#fff;color:#14213d;border-radius:14px;padding:18px;font:15px/1.45 system-ui,sans-serif}" +
    ".mtx-fm h3{font:600 22px/1.2 Newsreader,Georgia,serif;margin:0 0 4px}.mtx-fm .g{display:grid;grid-template-columns:1fr 1fr;gap:0 12px}.mtx-fm .w{grid-column:1/-1}" +
    ".mtx-fm label{display:block;font-size:13px;color:#5d6b82;margin:10px 0 4px}.mtx-fm input{width:100%;font:inherit;padding:9px 10px;border:1px solid #d8dde6;border-radius:9px;box-sizing:border-box}" +
    ".mtx-fm .lg{font-size:12px;color:#5d6b82;background:#f4f6fa;border-radius:8px;padding:10px;margin:12px 0}.mtx-fm .ck{display:flex;gap:8px;font-size:13px}.mtx-fm .ck input{width:auto}" +
    ".mtx-fm .pie{display:flex;gap:8px;margin-top:12px}.mtx-fm .pie button{flex:1;font:700 14px system-ui,sans-serif;padding:11px;border-radius:10px;border:1px solid #d8dde6;background:#fff;cursor:pointer}.mtx-fm .pie .p{background:#0b2545;color:#fff;border-color:#0b2545}";
  function premium(x, cover, datos) {
    var R = (datos && datos.rejilla) || {}, gap = R.separacion || 28;
    var f = x.formato || (x.modo === "imagen" ? "2x2" : "4x1"), cr = f.split("x"), c = +cr[0] || 4, r = +cr[1] || 1;
    var sec = d.createElement("section"); sec.className = "block mtx-premium";
    var wrap = d.createElement("div"); wrap.className = "wrap"; sec.appendChild(wrap);
    var url = utm(x.url, x, "portada-premium"), col = x.colores || {};
    var cuerpo = x.modo === "imagen" && x.imagen
      ? '<a class="mtx-ban-a" href="' + E(url) + '" rel="sponsored noopener" target="_blank" aria-label="' + E(x.titular || x.anunciante || "Publicidad") + '"></a>' +
        "<picture>" + (x.imagen_movil ? '<source media="(max-width:760px)" srcset="' + E(x.imagen_movil) + '">' : "") + '<img src="' + E(x.imagen) + '" alt="' + E(x.alt) + '" loading="lazy"></picture>'
      : '<div class="mtx-ban-t" style="background:' + E(col.fondo || "#0b2545") + ";color:" + E(col.texto || "#fff") + '">' +
        '<a class="mtx-ban-a" href="' + E(url) + '" rel="sponsored noopener" target="_blank" aria-label="' + E(x.titular) + '"></a>' +
        (x.anunciante ? '<span class="m">' + E(x.anunciante) + "</span>" : "") + "<b>" + E(x.titular) + "</b>" + (x.texto ? '<span class="p">' + E(x.texto) + "</span>" : "") +
        (x.cta_tipo === "web" ? '<a class="cta" data-cta href="' + E(url) + '" rel="sponsored noopener" target="_blank" style="background:' + E(col.boton) + ";color:" + E(col.boton_texto) + '">' + E(x.cta_texto || "Ir a la web") + "</a>" : "") +
        (x.cta_tipo === "info" ? '<button type="button" class="cta" data-form style="background:' + E(col.boton) + ";color:" + E(col.boton_texto) + '">' + E(x.cta_texto || "Pide más información") + "</button>" : "") + "</div>";
    var ban = '<aside class="mtx-ban' + (r === 1 ? " bajo" : "") + (x.tipo === "grupo" ? " house" : "") + '" data-mtx="' + E(x.id) + '" data-mtx-h="portada-premium" aria-label="' + E(x.etiqueta) +
      '" style="grid-column:' + (5 - c) + " / span " + c + '"><span class="mtx-ban-lab">' + E(x.etiqueta) + "</span>" + cuerpo + "</aside>";
    wrap.innerHTML = '<div class="mtx-esc">' + (c < 4 ? '<div class="mtx-mas" style="grid-column:1 / span ' + (4 - c) + '"><h3>Más noticias</h3></div>' : "") + ban + "</div>";
    cover.insertAdjacentElement("afterend", sec);
    var el = wrap.querySelector(".mtx-ban");
    function alto() {  // alto real según la rejilla: fila = media columna
      if (window.matchMedia("(max-width:760px)").matches) { el.style.height = ""; return; }
      var w = wrap.querySelector(".mtx-esc").getBoundingClientRect().width, cw = (w - 3 * gap) / 4;
      el.style.height = Math.round(r * (cw / 2) + (r - 1) * gap) + "px";
    }
    alto(); window.addEventListener("resize", alto);
    tiposJSON().then(function (j) {  // a la izquierda, los últimos titulares que no estén ya en la apertura
      var mas = wrap.querySelector(".mtx-mas"); if (!mas || !j || !j.menu) return;
      var ya = {}; [].forEach.call(cover.querySelectorAll("a[href]"), function (a) { ya[a.href.replace(/[?#].*$/, "")] = 1; });
      var n = Math.max(2, r * 2 + (c === 2 ? 1 : 0));
      (j.menu.ultimas || []).filter(function (p) { return !ya[p.url]; }).slice(0, n).forEach(function (p) {
        var a = d.createElement("a"); a.href = p.url; a.innerHTML = (p.mc ? "<small>" + E(p.mc) + "</small>" : "") + E(p.t); mas.appendChild(a);
      });
    });
    var b = el.querySelector("[data-form]");
    if (b) b.addEventListener("click", function (e) { e.preventDefault(); contar(x.id, "portada-premium", "fa"); formulario(x, datos); });
    var w2 = el.querySelector("a[data-cta]");
    if (w2) w2.addEventListener("click", function () { contar(x.id, "portada-premium", "cta"); });
  }
  function formulario(x, datos) {
    var F = (datos && datos.formulario_textos) || {};
    var v = d.createElement("div"); v.className = "mtx-fv";
    var m = d.createElement("div"); m.className = "mtx-fm"; m.setAttribute("role", "dialog"); m.setAttribute("aria-modal", "true"); m.setAttribute("aria-label", "Pide más información");
    var anun = E(x.anunciante || "el anunciante");
    var campo = function (id, txt, ob, tipo, ac, w) { return '<div' + (w ? ' class="w"' : "") + '><label for="mf-' + id + '">' + txt + (ob ? " *" : "") + '</label><input id="mf-' + id + '" type="' + (tipo || "text") + '" autocomplete="' + ac + '"' + (ob ? " required" : "") + "></div>"; };
    m.innerHTML = "<h3>Pide más información</h3><p style=\"margin:0;color:#5d6b82\">A " + anun + ", anunciante en MOTICIAS.</p><form><div class=\"g\">" +
      campo("nombre", "Nombre", 1, "text", "name") + campo("empresa", "Empresa", 0, "text", "organization") + campo("email", "Correo electrónico", 1, "email", "email") +
      campo("telefono", "Teléfono", 0, "tel", "tel") + campo("direccion", "Dirección", 0, "text", "street-address", 1) + campo("cp", "Código postal", 1, "text", "postal-code") +
      campo("ciudad", "Ciudad", 0, "text", "address-level2") + campo("pais", "País", 1, "text", "country-name", 1) + "</div>" +
      '<div class="lg">' + String(F.aviso || "").replace(/\{anunciante\}/g, anun) + "</div>" +
      '<label class="ck"><input type="checkbox" id="mf-ok"> ' + E(String(F.consentimiento || "").replace(/\{anunciante\}/g, x.anunciante || "el anunciante")) + "</label>" +
      '<div class="pie"><button type="button" class="n">Cancelar</button><button class="p">Enviar</button></div><p class="msg" style="font-size:13px;color:#a12b2b"></p></form>';
    d.body.appendChild(v); d.body.appendChild(m);
    var pais = m.querySelector("#mf-pais"); pais.value = "España";
    function cerrar() { v.remove(); m.remove(); }
    v.onclick = cerrar; m.querySelector(".n").onclick = cerrar;
    m.querySelector("form").onsubmit = function (e) {
      e.preventDefault();
      var cuerpo = {anuncio: x.id, hueco: "portada-premium", seccion: SEC, dispositivo: DISP, procedencia: PROC, pagina: location.pathname, texto_legal: F.version || "",
                    consentimiento: m.querySelector("#mf-ok").checked};
      ["nombre", "empresa", "email", "telefono", "direccion", "cp", "ciudad", "pais"].forEach(function (k) { cuerpo[k] = m.querySelector("#mf-" + k).value.trim(); });
      if (!cuerpo.consentimiento) { m.querySelector(".msg").textContent = "Marca la casilla para que podamos entregar tus datos al anunciante."; return; }
      fetch(API + "/api/gestor?a=formulario", {method: "POST", body: JSON.stringify(cuerpo), headers: {"Content-Type": "text/plain"}})
        .then(function (r) { return r.json().then(function (j) { return [r.ok, j]; }); })
        .then(function (t) { if (t[0]) { m.innerHTML = "<h3>Enviado</h3><p>" + E(t[1].mensaje || "Gracias.") + '</p><div class="pie"><button type="button" class="p">Cerrar</button></div>'; m.querySelector("button").onclick = cerrar; }
          else m.querySelector(".msg").textContent = t[1].error || "No se pudo enviar."; })
        .catch(function () { m.querySelector(".msg").textContent = "No se pudo enviar. Prueba más tarde."; });
    };
  }
  // «Lo esencial» de la portada: el tema deja las columnas vacías; se rellenan con las piezas de cada sección (16-11-2026).
  (function () {
    var cols = d.querySelectorAll(".essentials .ess-col");
    if (!cols.length) return;
    tiposJSON().then(function (j) {
      var es = j && j.menu && j.menu.esencial; if (!es) return;
      var usadas = {};  // una pieza sale en una sola columna
      [].forEach.call(cols, function (c) {
        var k = (c.className.match(/ess-col\s+([a-z-]+)/) || [])[1], ul = c.querySelector("ul.list");
        if (!k || !ul || ul.children.length || !es[k]) return;
        ul.innerHTML = es[k].filter(function (p) { return !usadas[p.url]; }).slice(0, 3).map(function (p) { usadas[p.url] = 1; return '<li><a href="' + E(p.url) + '">' + E(p.t) + "</a></li>"; }).join("");
      });
    });
  })();

  // ---------- 3. Seguimiento ----------
  var JEFE = /(?:^|;\s*)moticias_jefe=1/.test(d.cookie);
  // Medición ampliada (banner premium, 16-11-2026): sección, dispositivo y procedencia (dominio de origen o utm_source).
  var SEC = (location.pathname.match(/^\/([a-z0-9-]+)\//) || [])[1] || "portada";
  if (d.querySelector("article.article")) SEC = "articulo";
  var DISP = /Mobi|Android|iPhone/i.test(navigator.userAgent) ? "movil" : /iPad|Tablet/i.test(navigator.userAgent) ? "tableta" : "escritorio";
  var PROC = (function () {
    try { var u = new URL(location.href).searchParams.get("utm_source"); if (u) return u.toLowerCase().slice(0, 60); } catch (e) {}
    try { var r = d.referrer ? new URL(d.referrer).hostname.replace(/^www\./, "") : ""; return !r ? "directo" : (r === location.hostname.replace(/^www\./, "") ? "interno" : r); } catch (e) { return "directo"; }
  })();
  function contar(id, h, t) {
    if (JEFE || navigator.webdriver || !id) return;
    var cuerpo = JSON.stringify({a: id, h: h || "?", p: location.pathname, t: t, s: SEC, dv: DISP, pr: PROC});
    try { if (navigator.sendBeacon && navigator.sendBeacon(API + "/api/gestor?a=evento", new Blob([cuerpo], {type: "text/plain"}))) return; } catch (e) {}
    try { fetch(API + "/api/gestor?a=evento", {method: "POST", body: cuerpo, keepalive: true, mode: "no-cors"}); } catch (e) {}
  }
  function datos(el) {
    if (el.hasAttribute("data-mtx")) return [el.getAttribute("data-mtx"), el.getAttribute("data-mtx-h")];
    return ["caja:" + el.getAttribute("data-producto"), "texto-" + (el.getAttribute("data-posicion") || "estandar")];
  }
  var vistos = typeof WeakSet === "function" ? new WeakSet() : null;
  var mirador = "IntersectionObserver" in window ? new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (e.isIntersecting && vistos && !vistos.has(e.target)) { vistos.add(e.target); var x = datos(e.target); contar(x[0], x[1], "i"); mirador.unobserve(e.target); }
    });
  }, {threshold: 0.5}) : null;
  function vigilarCajas() {
    if (!mirador) return;
    [].forEach.call(d.querySelectorAll("[data-mtx], aside.contenido-patrocinado[data-producto]"), function (el) { mirador.observe(el); });
  }
  d.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest("a[href]");
    var c = a && a.closest("[data-mtx], aside.contenido-patrocinado[data-producto]");
    if (c) { var x = datos(c); contar(x[0], x[1], "c"); }
  }, true);

  function cuandoEste(sel, fn, n) { if (d.querySelector(sel) || (n || 0) > 20) return fn(); setTimeout(function () { cuandoEste(sel, fn, (n || 0) + 1); }, 150); }
  fetch(API + "/api/gestor?a=publicidad").then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
    if (!j) return;
    if (d.body.classList.contains("post-template")) cuandoEste("aside.m-aside", function () { publicidad(j); cajasDelTema(); vigilarCajas(); }); else { publicidad(j); cajasDelTema(); vigilarCajas(); }
  }).catch(function () { vigilarCajas(); });

  // ---------- 6. Secciones ----------
  // Las páginas de sección (/tierra/, /mar/, /aire/, /logistica/, /regulacion/, /licitaciones/, /analisis/) usan la
  // plantilla «custom-seccion» del tema, que no está en el repositorio y salía vacía (15-11-2026). Hasta que el tema se
  // versione (publicar-en-ghost-v1), este script pinta cada sección con las piezas publicadas, leídas del índice del
  // buscador (app.moticias.com/buscador/index.json) y filtradas por los tres ejes (modo, tema) o por el tipo de contenido.
  var SECCIONES = {
    tierra: function (p) { return p.m === "tierra"; },
    mar: function (p) { return p.m === "mar"; },
    aire: function (p) { return p.m === "aire"; },
    logistica: function (p) { return p.m === "logistica"; },
    regulacion: function (p) { return (p.te || []).indexOf("regulacion") >= 0; },
    licitaciones: function (p) { return (p.te || []).indexOf("concesiones") >= 0; },
    analisis: function (p) { return p.tc === "editorial"; }
  };
  SECCIONES["la-voz-del-editor"] = function (p) { return p.kind === "opinion"; };
  var secActual = (location.pathname.match(/^\/([a-z-]+)\/?$/) || [])[1];
  if (secActual && SECCIONES[secActual] && d.querySelector("main#main")) {
    css.textContent += ".mtx-sec{list-style:none;margin:0;padding:0;display:grid;gap:22px}" +
      ".mtx-sec li{display:grid;grid-template-columns:200px 1fr;gap:18px;align-items:start;padding-bottom:22px;border-bottom:1px solid #e5e7eb}" +
      ".mtx-sec img{width:200px;height:130px;object-fit:cover;border-radius:6px;background:#eef0f2}" +
      ".mtx-sec .sf{display:flex;align-items:center;justify-content:center;width:200px;height:130px;border-radius:6px;background:#0b2545;color:#fff;font:700 13px system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;text-decoration:none}" +
      ".mtx-sec .k{font:600 11px/1.4 system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:#6b7280;margin:0 0 6px}" +
      ".mtx-sec .k b{color:#7a1f2b;font-weight:700}" +
      ".mtx-sec h2{font-size:21px;line-height:1.25;margin:0 0 6px}.mtx-sec h2 a{color:inherit;text-decoration:none}" +
      ".mtx-sec p.r{margin:0;color:#374151;font-size:15px;line-height:1.45}" +
      ".mtx-mas{margin:22px 0 0;padding:10px 18px;border:1px solid #d1d5db;border-radius:20px;background:#fff;font:600 14px system-ui,sans-serif;cursor:pointer}" +
      "@media(max-width:640px){.mtx-sec li{grid-template-columns:1fr}.mtx-sec img,.mtx-sec .sf{width:100%;height:190px}}";
    var MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
    var fecha = function (iso) { var x = String(iso || "").split("-"); return x.length === 3 ? (+x[2]) + " " + MES[+x[1] - 1] + " " + x[0] : ""; };
    fetch(API + "/buscador/index.json").then(function (r) { return r.ok ? r.json() : null; }).then(function (ix) {
      if (!ix || !ix.piezas) return;
      var subs = {};
      (ix.taxonomia.modos || []).forEach(function (m) { (m.submodos || []).forEach(function (s) { subs[s.id] = s.nombre; }); });
      var regla = (ix.secciones || {})[secActual];  // reglas del vertical (secciones_web); si no vienen, las de aquí
      var merc = ix.mercancias || [];
      // Reglas de secciones_web (16-11-2026): medio (con el eje antiguo como reserva), mercancías, tema, tipo y clase de pieza.
      var filtro = regla ? function (p) { return (!regla.modo || p.m === regla.modo) && (!regla.medio || (p.md || p.m) === regla.medio) &&
        (!regla.mercancias || p.m === "logistica" || (p.mo || []).some(function (x) { return merc.indexOf(x) >= 0; })) &&
        (!regla.tema || (p.te || []).indexOf(regla.tema) >= 0) && (!regla.tipo || p.tc === regla.tipo) && (!regla.kind || p.kind === regla.kind); } : SECCIONES[secActual];
      var lista = ix.piezas.filter(filtro).sort(function (a, b) { return a.d < b.d ? 1 : a.d > b.d ? -1 : 0; });
      var main = d.querySelector("main#main"), vacio = main.querySelector("p.empty");
      var caja = vacio ? vacio.parentNode : null;
      if (!caja) { var sec0 = d.createElement("section"); sec0.className = "block"; caja = d.createElement("div"); caja.className = "wrap"; sec0.appendChild(caja); main.insertBefore(sec0, main.firstChild); }
      if (vacio) vacio.remove();
      if (!lista.length) { caja.insertAdjacentHTML("beforeend", '<p class="empty">' + (secActual === "la-voz-del-editor" ? "La primera columna se publicará un lunes, en cuanto el editor jefe apruebe la primera propuesta." : "Todavía no hay piezas en esta sección.") + "</p>"); return; }
      if (secActual === "la-voz-del-editor") { vozDesplegada(lista, caja); sinApilar(); return; }
      var ul = d.createElement("ul"); ul.className = "mtx-sec"; caja.appendChild(ul);
      var n = 0;
      function mas() {
        lista.slice(n, n + 20).forEach(function (p) {
          var li = d.createElement("li");
          li.innerHTML = (p.gi ? '<a href="' + E(p.url) + '"><img src="' + E(p.gi) + '" alt="' + E(p.alt) + '" loading="lazy"></a>' : '<a class="sf" href="' + E(p.url) + '" aria-hidden="true">' + E(subs[p.sm] || "MOTICIAS") + "</a>") +
            '<div><p class="k"><b>' + E(p.mc || "") + "</b> · " + E(subs[p.sm] || "") + " · " + E(fecha(p.d)) + "</p>" +
            '<h2><a href="' + E(p.url) + '">' + E(p.t) + "</a></h2>" + (p.r ? '<p class="r">' + E(p.r) + "</p>" : "") + "</div>";
          ul.appendChild(li);
        });
        n += 20;
        var b = caja.querySelector(".mtx-mas");
        if (n < lista.length && !b) { b = d.createElement("button"); b.className = "mtx-mas"; b.textContent = "Ver más"; b.onclick = mas; caja.appendChild(b); }
        else if (n >= lista.length && b) b.remove();
      }
      mas();
      sinApilar();
    }).catch(function () {});
  }

  // ---------- 6 bis. «La voz del editor» desplegada (cambio voz-desplegada-y-sin-banners-apilados, 17-11-2026) ----------
  // En /la-voz-del-editor/ la última columna se lee entera, con su foto y su crédito, y a la derecha, en una columna estrecha
  // que no compite con ella, las anteriores (fecha, tema y titular). El texto se toma tal cual de la página de la columna
  // (mismo dominio): no se reescribe nada. Si no se puede leer, queda el resumen con «Leer la columna completa». En el móvil
  // las anteriores van debajo.
  function vozDesplegada(lista, caja) {
    css.textContent += ".mtx-vz{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:56px;align-items:start}" +
      ".mtx-vz-ult{min-width:0;max-width:760px}.mtx-vz-ult .k{font:600 11px/1.4 system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:#6b7280;margin:0 0 8px}" +
      ".mtx-vz-ult .k b{color:#7a1f2b;font-weight:700}.mtx-vz-ult h2{font-size:clamp(28px,4vw,40px);line-height:1.12;margin:0 0 10px}.mtx-vz-ult h2 a{color:inherit;text-decoration:none}" +
      ".mtx-vz-ult .dek{font-size:19px;line-height:1.45;color:#374151;margin:0 0 12px}.mtx-vz-ult .by{font:500 14px/1.4 system-ui,sans-serif;color:#4b5563;margin:0 0 18px}" +
      ".mtx-vz-ult figure{margin:0 0 22px}.mtx-vz-ult figure img{display:block;width:100%;height:auto;border-radius:6px}.mtx-vz-ult figcaption{font:12px/1.4 system-ui,sans-serif;color:#6b7280;margin-top:6px}" +
      ".mtx-vz-ult .article-main{max-width:none;margin:0;padding:0;font-size:18px;line-height:1.6}.mtx-vz-ult .article-main p,.mtx-vz-ult .article-main ul{margin:0 0 1em}" +
      ".mtx-vz-ult .article-main h2{font-size:26px;line-height:1.2;margin:1.6em 0 .5em}.mtx-vz-ult .article-main li{margin:0 0 .4em}.mtx-vz-ult .article-main a{color:#1d4ed8;text-decoration:underline}.mtx-vz-ult .ir{display:inline-block;margin-top:18px;font:600 14px system-ui,sans-serif;color:#1d4ed8}" +
      ".mtx-vz-ant{position:sticky;top:20px;border-left:1px solid #e5e7eb;padding-left:22px;font-family:system-ui,sans-serif}" +
      ".mtx-vz-ant h3{font:700 11px/1.4 system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#5d6b82;margin:0 0 6px}" +
      ".mtx-vz-ant ul{list-style:none;margin:0;padding:0}.mtx-vz-ant li{padding:12px 0;border-bottom:1px solid #eef0f3}" +
      ".mtx-vz-ant small{display:block;font:600 10.5px/1.4 system-ui,sans-serif;letter-spacing:.05em;text-transform:uppercase;color:#7a8597;margin-bottom:3px}" +
      ".mtx-vz-ant a{color:#0b2545;text-decoration:none;font:500 16px/1.3 Newsreader,Georgia,serif}.mtx-vz-ant a:hover{text-decoration:underline}" +
      ".mtx-vz-ant p.v{font-size:13px;line-height:1.45;color:#6b7280;margin:8px 0 0}" +
      "@media(max-width:900px){.mtx-vz{grid-template-columns:1fr;gap:32px}.mtx-vz-ant{position:static;border-left:0;padding-left:0;border-top:3px solid #0b2545;padding-top:12px}}";
    var ult = lista[0], ant = lista.slice(1);
    var tema = function (p) { return String(p.k || "").replace(/^La voz del editor\s*·\s*/i, ""); };
    var g = d.createElement("div"); g.className = "mtx-vz";
    g.innerHTML = '<article class="mtx-vz-ult"><p class="k"><b>' + E(ult.mc || "Opinión · La voz del editor") + "</b>" + (tema(ult) ? " · " + E(tema(ult)) : "") + " · " + E(fecha(ult.d)) + "</p>" +
      '<h2><a href="' + E(ult.url) + '">' + E(ult.t) + "</a></h2>" + (ult.s ? '<p class="dek">' + E(ult.s) + "</p>" : "") +
      '<p class="by">Por ' + E(ult.au || "Rainer Uphoff") + "</p>" +
      '<div class="mtx-vz-cuerpo">' + (ult.r ? "<p>" + E(ult.r) + "</p>" : "") + '<a class="ir" href="' + E(ult.url) + '">Leer la columna completa →</a></div></article>' +
      '<aside class="mtx-vz-ant" aria-label="Columnas anteriores"><h3>Columnas anteriores</h3>' +
      (ant.length ? "<ul>" + ant.map(function (p) { return '<li><small>' + E(fecha(p.d)) + (tema(p) ? " · " + E(tema(p)) : "") + '</small><a href="' + E(p.url) + '">' + E(p.t) + "</a></li>"; }).join("") + "</ul>"
        : '<p class="v">Esta es la primera columna. Las siguientes dejarán aquí las anteriores.</p>') + "</aside>";
    caja.appendChild(g);
    var ruta; try { ruta = new URL(ult.url).pathname; } catch (e) { return; }
    fetch(ruta, {credentials: "same-origin"}).then(function (r) { return r.ok ? r.text() : null; }).then(function (h) {
      if (!h) return;
      var doc = new DOMParser().parseFromString(h, "text/html");
      var cuerpo = doc.querySelector(".article-main.gh-content") || doc.querySelector(".gh-content");
      if (!cuerpo || cuerpo.textContent.trim().length < 200) return;
      [].forEach.call(cuerpo.querySelectorAll(".m-tipo, script, aside.contenido-patrocinado"), function (x) { x.remove(); });  // la marca ya va arriba
      var foto = doc.querySelector("figure.article-hero"), t = doc.querySelector(".article-head time");
      var dest = g.querySelector(".mtx-vz-cuerpo"); dest.innerHTML = "";
      if (foto) dest.appendChild(d.importNode(foto, true));
      var c = d.importNode(cuerpo, true); dest.appendChild(c);
      dest.insertAdjacentHTML("beforeend", '<a class="ir" href="' + E(ult.url) + '">Abrir en su página (para compartir o comentar) →</a>');
      if (t) g.querySelector(".by").insertAdjacentHTML("beforeend", " · " + E(t.textContent.trim()));
      sinApilar();
    }).catch(function () {});
  }

  // ---------- 5. Sin «Powered by Ghost» ----------
  // La ventana de entrada y suscripción de Ghost (Portal) pinta siempre la marca «Powered by Ghost» y no tiene ajuste para
  // quitarla. Esa ventana va en marcos de la misma página (mismo origen), así que se le añade una regla que la oculta
  // (decisión de Rainer, 15-11-2026). Si Ghost cambia el nombre de la clase, la marca vuelve a verse y nada más se rompe.
  function sinMarcaGhost(f) {
    try {
      var doc = f.contentDocument;
      if (!doc || !doc.head || doc.getElementById("mtx-sin-marca")) return;
      var st = doc.createElement("style"); st.id = "mtx-sin-marca";
      st.textContent = ".gh-portal-powered{display:none!important}";
      doc.head.appendChild(st);
    } catch (e) {}
  }
  function vigilarPortal() {
    [].forEach.call(d.querySelectorAll('iframe[title^="portal-"]'), function (f) {
      sinMarcaGhost(f);
      if (!f.__mtx) { f.__mtx = 1; f.addEventListener("load", function () { sinMarcaGhost(f); }); }
    });
  }
  if ("MutationObserver" in window) new MutationObserver(vigilarPortal).observe(d.documentElement, {childList: true, subtree: true});
  vigilarPortal();

  // ---------- 4. Tipo de contenido ----------
  // Marca por tipo en los listados (portada, secciones, etiquetas, búsqueda). En la propia pieza ya va en el cuerpo.
  var SLUG_TC = /^\/([a-z0-9]+(?:-[a-z0-9]+)*)\/?$/;
  css.textContent += ".mtx-tc{display:inline-block;margin:0 0 4px;font:600 10.5px/1.4 system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:#6b7280}" +
    ".mtx-tc.t-editorial{color:#7a1f2b}.mtx-tc.t-nota_de_prensa{color:#6b7280;border:1px solid #e5e7eb;border-radius:4px;padding:0 5px}";
  function marcas(tc) {
    [].forEach.call(d.querySelectorAll("main h1 a[href], main h2 a[href], main h3 a[href], .lead h2 a, .second h3 a, .m-map-list a[href]"), function (a) {
      try { var u = new URL(a.href, location.href); } catch (e) { return; }
      var mm = u.host === location.host && u.pathname.match(SLUG_TC), x = mm && tc[mm[1]];
      if (!x || (u.pathname === location.pathname) || a.parentNode.querySelector(".mtx-tc") || a.closest(".mtx-sec, .mtx-vz")) return;
      var s = d.createElement("span");
      s.className = "mtx-tc t-" + x[0]; s.textContent = x[1];
      s.style.display = "block"; a.insertAdjacentElement("beforebegin", s);
    });
  }
  // Las cajas que pinta el tema por su cuenta (huecos sin caja del gestor) también llevan rel="sponsored". Las del grupo
  // (clase «house» del tema, que no está versionado) llevan además la etiqueta «Contenido patrocinado», y su enlace,
  // utm_medium=grupo. Cuando el tema se versione (publicar-en-ghost-v1), esto pasa al tema.
  var GRUPO = "Contenido patrocinado";  // sin decir «del grupo» en las cajas por niveles (decisión de Rainer, 15-11-2026, noche)
  function cajasDelTema() {
    [].forEach.call(d.querySelectorAll("aside.ad.house:not([data-mtx])"), function (c) {
      c.setAttribute("aria-label", GRUPO);
      var l = c.querySelector(".ad-label"); if (l) l.textContent = GRUPO;
      [].forEach.call(c.querySelectorAll("a[href]"), function (a) {
        try { var u = new URL(a.href); if (u.searchParams.get("utm_medium")) { u.searchParams.set("utm_medium", "grupo"); a.href = u.toString(); } } catch (e) {}
      });
    });
    [].forEach.call(d.querySelectorAll(".ad a[href], .ad-end a[href], aside.contenido-patrocinado a[href]"), function (a) { a.setAttribute("rel", "sponsored noopener"); });
  }
  cajasDelTema();
  if (!d.body.classList.contains("post-template")) {
    tiposJSON().then(function (j) { if (j && j.piezas) marcas(j.piezas); }).catch(function () {});
  }

  // ---------- 2. Editor jefe ----------
  var SLUG = /^\/([a-z0-9]+(?:-[a-z0-9]+)*-[a-z0-9]{4})\/?$/;
  function enlace(slug, accion) {
    return API + "/gestor/?" + new URLSearchParams({pieza: slug, accion: accion || "", volver: location.href}).toString();
  }
  function herramientas() {
    var m = location.pathname.match(SLUG), pieza = d.body.classList.contains("post-template") && m;
    // «Iniciar barrido de noticias ahora» (decisión de Rainer, 9-11-2026): en todas las páginas; lo lanza el gestor.
    var barrido = API + "/gestor/?" + new URLSearchParams({barrido: "1", volver: location.href}).toString();
    var f = d.createElement("div");
    f.className = "mtx-fab";
    f.innerHTML = '<button type="button" aria-label="Herramientas del editor jefe" title="Editor jefe">✎</button><ul>' +
      '<li class="t">Editor jefe</li>' +
      (pieza ? '<li><a href="' + E(enlace(m[1], "editar")) + '">Editar</a></li>' +
        '<li><a href="' + E(enlace(m[1], "ia")) + '">Otro enfoque con IA</a></li>' +
        '<li><a href="' + E(enlace(m[1], "")) + '">Patrocinio y retoques</a></li>' +
        '<li><a class="r" href="' + E(enlace(m[1], "retirar")) + '">Retirar</a></li>' : '') +
      '<li><a href="' + E(barrido) + '">Iniciar barrido de noticias ahora</a></li></ul>';
    f.querySelector("button").onclick = function () { f.classList.toggle("on"); };
    d.addEventListener("click", function (ev) { if (!f.contains(ev.target)) f.classList.remove("on"); });
    d.body.appendChild(f);
    // En listados: un icono pequeño junto a cada titular que lleva a una pieza.
    [].forEach.call(d.querySelectorAll("main h1 a[href], main h2 a[href], main h3 a[href], .lead h2 a, .second h3 a"), function (a) {
      try { var u = new URL(a.href, location.href); } catch (e) { return; }
      var mm = u.host === location.host && u.pathname.match(SLUG);
      if (!mm || a.parentNode.querySelector(".mtx-ed")) return;
      var i = d.createElement("a");
      i.className = "mtx-ed"; i.href = enlace(mm[1], "editar"); i.title = "Editar (editor jefe)"; i.setAttribute("aria-label", "Editar esta pieza"); i.textContent = "✎";
      a.insertAdjacentElement("afterend", i);
    });
  }
  if (location.hash === "#editor") { location.href = API + "/gestor/?" + new URLSearchParams({volver: location.href.replace(/#editor$/, "")}).toString(); return; }
  if (/(?:^|;\s*)moticias_jefe=1/.test(d.cookie)) {
    fetch(API + "/api/gestor?a=yo", {credentials: "include"}).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) { if (j && j.jefe) herramientas(); }).catch(function () {});
  }

  // ---------- 7. Menú con submenús y «La voz del editor» ----------
  (function () {
    var nav = d.querySelector("header.masthead nav.nav");
    if (!nav) return;
    css.textContent +=
      "nav.nav{position:relative}nav.nav .mtx-v{display:inline-flex;align-items:center;gap:6px}" +
      "nav.nav .mtx-voz{border:1.5px solid #f26b1d;color:#b8470b!important;border-radius:999px}nav.nav .mtx-voz:hover{background:#fff4ec}" +
      "nav.nav .mtx-voz::before{content:'';width:7px;height:7px;border-radius:50%;background:#f26b1d;display:inline-block;margin-right:6px;vertical-align:1px}" +
      "nav.nav a.mtx-sub{display:inline-flex;align-items:center}" +
      "nav.nav a.mtx-sub::after{content:'';width:5px;height:5px;border-right:1.6px solid currentColor;border-bottom:1.6px solid currentColor;transform:rotate(45deg);opacity:.55;margin:-3px 0 0 7px}" +
      "nav.nav a.mtx-sub[aria-expanded=true]::after{transform:rotate(-135deg);margin-top:3px}" +
      ".mtx-panel{position:absolute;z-index:60;background:#fff;border:1px solid #e3e6ea;border-radius:12px;box-shadow:0 12px 32px rgba(11,37,69,.14);padding:16px 18px;display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:4px 18px}" +
      ".mtx-panel h4{grid-column:1/-1;margin:0 0 6px;font:700 11px/1.4 system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#6b7280}" +
      ".mtx-panel a{display:flex;justify-content:space-between;gap:10px;padding:8px 10px;border-radius:8px;color:#0b2545;text-decoration:none;font:500 15px/1.3 system-ui,sans-serif;text-transform:none;letter-spacing:0}" +
      ".mtx-panel a:hover,.mtx-panel a:focus{background:#f1f4f8}.mtx-panel a small{color:#8a94a3;font-variant-numeric:tabular-nums}" +
      ".mtx-panel a.mtx-todo{font-weight:700}.mtx-panel .mtx-sep{grid-column:1/-1;height:1px;background:#eef0f3;margin:6px 0}" +
      ".mtx-velo{position:fixed;inset:0;background:rgba(11,37,69,.35);z-index:59}" +
      "@media(max-width:760px){.mtx-panel{position:fixed;left:0;right:0;bottom:0;top:auto;max-height:72vh;overflow:auto;border-radius:16px 16px 0 0;grid-template-columns:1fr 1fr;padding:18px 16px calc(18px + env(safe-area-inset-bottom))}" +
      ".mtx-panel a{font-size:15px;padding:10px}}";
    var abierto = null, velo = null;
    function cerrar() {
      if (abierto) { abierto.btn.setAttribute("aria-expanded", "false"); abierto.panel.remove(); abierto = null; }
      if (velo) { velo.remove(); velo = null; }
    }
    function enlace(x, todo) {
      return '<a href="' + E(x.url) + '"' + (todo ? ' class="mtx-todo"' : "") + "><span>" + E(x.nombre) + "</span>" + (x.n != null ? "<small>" + x.n + "</small>" : "") + "</a>";
    }
    function abrir(btn, html) {
      if (abierto && abierto.btn === btn) return cerrar();
      cerrar();
      var p = d.createElement("div"); p.className = "mtx-panel"; p.setAttribute("role", "menu"); p.innerHTML = html;
      if (window.matchMedia("(max-width:760px)").matches) { velo = d.createElement("div"); velo.className = "mtx-velo"; velo.onclick = cerrar; d.body.appendChild(velo); d.body.appendChild(p); }
      else {  // la barra recorta lo que sobresale (desplazamiento horizontal): el panel va en el cuerpo, bajo la barra
        var r = nav.getBoundingClientRect();
        p.style.top = (r.bottom + window.scrollY + 6) + "px"; p.style.left = (r.left + window.scrollX) + "px"; p.style.width = r.width + "px";
        d.body.appendChild(p);
      }
      btn.setAttribute("aria-expanded", "true"); abierto = {btn: btn, panel: p};
      var a = p.querySelector("a"); if (a) a.focus({preventScroll: true});
    }
    d.addEventListener("keydown", function (e) { if (e.key === "Escape") cerrar(); });
    d.addEventListener("click", function (e) { if (abierto && !abierto.panel.contains(e.target) && e.target !== abierto.btn) cerrar(); });
    function boton(texto, html, antes, url) {
      // Enlace (el tema le da el mismo estilo que a los demás; sin JavaScript lleva a la página) que abre el submenú.
      var b = d.createElement("a"); b.href = url || "#"; b.className = "mtx-sub"; b.textContent = texto; b.setAttribute("role", "button");
      b.setAttribute("aria-haspopup", "true"); b.setAttribute("aria-expanded", "false");
      b.addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); abrir(b, html()); });
      nav.insertBefore(b, antes || null);
      return b;
    }
    tiposJSON().then(function (j) {
      var m = j && j.menu;
      if (!m) return;
      var portada = nav.querySelector(".nav-portada"), analisis = nav.querySelector(".nav-analisis");
      // «La voz del editor»: destacado fijo, justo después de Portada (en el móvil se ve sin desplazar la barra).
      var voz = d.createElement("a"); voz.href = m.voz.url; voz.className = "mtx-voz"; voz.textContent = m.voz.nombre;
      if (location.pathname.indexOf("/la-voz-del-editor") === 0) voz.setAttribute("aria-current", "page");
      nav.insertBefore(voz, portada ? portada.nextSibling : nav.firstChild);
      // Tierra, Mar y Aire: el enlace de siempre abre el submenú; dentro, «Todo …» y cada modo.
      (m.medios || []).forEach(function (md) {
        var a = nav.querySelector(".nav-" + md.id);
        var html = function () { return "<h4>" + E(md.nombre) + "</h4>" + enlace({nombre: "Todo " + md.nombre.toLowerCase(), url: md.url, n: md.n}, true) +
          md.modos.map(function (x) { return enlace(x); }).join(""); };
        var b = boton(md.nombre, html, a, md.url);
        if (a) { b.className += " " + a.className; a.remove(); }
      });
      // Logística (modos de mercancías de cualquier medio), Temas (con Regulación y Licitaciones) y Regiones.
      var ref = nav.querySelector(".nav-regulacion") || analisis;
      if (m.logistica && m.logistica.modos.length) boton(m.logistica.nombre, function () { return "<h4>Logística</h4>" + enlace({nombre: "Toda la logística", url: m.logistica.url}, true) + m.logistica.modos.map(function (x) { return enlace(x); }).join(""); }, ref, m.logistica.url);
      boton("Temas", function () { return "<h4>Temas</h4>" + m.secciones.map(function (x) { return enlace(x, true); }).join("") + '<div class="mtx-sep"></div>' + m.temas.map(function (x) { return enlace(x); }).join(""); }, ref);
      boton("Regiones", function () {
        var sup = m.regiones.filter(function (x) { return x.tipo !== "ccaa"; }), cc = m.regiones.filter(function (x) { return x.tipo === "ccaa"; });
        return "<h4>Regiones</h4>" + sup.map(function (x) { return enlace(x, true); }).join("") + '<div class="mtx-sep"></div>' + cc.map(function (x) { return enlace(x); }).join("");
      }, ref);
      [].forEach.call(nav.querySelectorAll(".nav-regulacion, .nav-licitaciones"), function (a) { a.remove(); });
    }).catch(function () {});
  })();
  // ---------- 8. Agenda (cambio agenda-de-eventos, 16-11-2026) ----------
  // «Agenda» en el menú principal, antes de Análisis; y en las páginas de la agenda, sus filtros y su formulario.
  (function () {
    var nav = d.querySelector("header.masthead nav.nav");
    if (nav && !nav.querySelector(".mtx-agenda")) {
      var a = d.createElement("a"); a.href = "/agenda/"; a.className = "mtx-agenda nav-agenda"; a.textContent = "Agenda";
      if (location.pathname.indexOf("/agenda") === 0) a.setAttribute("aria-current", "page");
      nav.insertBefore(a, nav.querySelector(".nav-analisis"));
    }
    if (d.querySelector(".m-agenda")) { var s = d.createElement("script"); s.src = API + "/sitio/agenda.js"; s.defer = true; d.body.appendChild(s); }
  })();
})();
