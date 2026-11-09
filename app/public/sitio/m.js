/* MOTICIAS · script del sitio (www.moticias.com). Lo carga la inyección de código del pie de Ghost:
   <script src="https://app.moticias.com/sitio/m.js" defer></script>
   Dos cosas, nada más (cambio OpenSpec editor-jefe-y-crm, decisiones de Rainer del 9-11-2026):
   1. Publicidad y patrocinios: rellena los huecos con las cajas activas del gestor (app.moticias.com/api/gestor?a=publicidad),
      por niveles (premium: cabecera y lateral del artículo; estándar: portada y cierre del artículo; básico: antes del pie).
      Etiqueta siempre visible (art. 20 LSSI) y enlace rel="sponsored". Nunca dentro del texto de una pieza. Si no hay caja
      pagada para un hueco, se queda la autopromoción que pinta el tema.
   2. Editor jefe: si este navegador tiene la marca «moticias_jefe» (la pone el gestor al entrar el superadministrador), pregunta
      al gestor si de verdad lo es (con su sesión) y, solo entonces, enseña un icono discreto en cada noticia con Editar, Otro
      enfoque con IA, Patrocinio y retoques, y Retirar. La marca no da ningún permiso: todo se comprueba en el servidor.
   3. Seguimiento: cuenta una visualización cuando una caja (publicidad, patrocinio o «Contenido patrocinado» del texto) se ve
      al menos a medias, y un clic cuando se pulsa su enlace (POST /api/gestor?a=evento). No cuenta las visitas del editor jefe
      ni de navegadores automatizados.
   Sin dependencias; si algo falla, el sitio sigue igual. */
(function () {
  "use strict";
  var API = "https://app.moticias.com";
  var d = document;
  var E = function (s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]; }); };
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

  // ---------- 0. La marca no se traduce ----------
  // Los traductores automáticos del navegador tienden a convertir «MOTICIAS» en «noticias»/«news»: la marca se marca como no
  // traducible donde aparece como marca (cabecera, logo, pie).
  [].forEach.call(d.querySelectorAll(".brand, .logo, header.masthead a[aria-label], footer.site .brand, footer.site .wrap > :first-child"), function (el) { el.setAttribute("translate", "no"); el.classList.add("notranslate"); });

  // ---------- 1. Publicidad ----------
  var seccion = (function () {
    var a = d.querySelector("article.article");
    return a ? (a.className.replace(/\barticle\b/, "").trim().split(/\s+/)[0] || "") : "";
  })();
  function elegir(lista, usadas) {
    var c = (lista || []).filter(function (x) { return !usadas[x.id] && (!x.secciones.length || x.secciones.indexOf(seccion) >= 0); });
    var pagadas = c.filter(function (x) { return x.tipo !== "autopromocion"; });
    if (pagadas.length) c = pagadas;
    if (!c.length) return null;
    var nivel = c[0].nivel; c = c.filter(function (x) { return x.nivel === nivel; });
    var total = c.reduce(function (s, x) { return s + (x.peso || 1); }, 0), r = Math.random() * total;
    for (var i = 0; i < c.length; i++) { r -= (c[i].peso || 1); if (r <= 0) { usadas[c[i].id] = 1; return c[i]; } }
    usadas[c[0].id] = 1; return c[0];
  }
  function utm(u, x, hueco) {
    try { var url = new URL(u); if (!url.searchParams.get("utm_source")) { url.searchParams.set("utm_source", "moticias"); url.searchParams.set("utm_medium", x.tipo); url.searchParams.set("utm_campaign", x.campana); url.searchParams.set("utm_content", hueco); } return url.toString(); } catch (e) { return u; }
  }
  function caja(x, hueco, ancha) {
    var rel = x.tipo === "autopromocion" ? "noopener" : "sponsored noopener";
    return '<aside class="ad ' + (ancha ? "ad-wide" : "ad-side") + (x.tipo === "autopromocion" ? " house" : "") + '" aria-label="' + E(x.etiqueta) + '" data-mtx="' + E(x.id) + '" data-mtx-h="' + E(hueco) + '">' +
      '<span class="ad-label">' + E(x.etiqueta) + (x.anunciante ? " · " + E(x.anunciante) : "") + "</span>" +
      '<a class="ad-body" href="' + E(utm(x.url, x, hueco)) + '" rel="' + rel + '" target="_blank">' +
      (x.imagen ? '<img class="ad-img" src="' + E(x.imagen) + '" alt="" loading="lazy">' : "") +
      '<span class="ad-text">' + (x.anunciante ? '<span class="ad-brand">' + E(x.anunciante) + "</span>" : "") + "<b>" + E(x.titular) + "</b>" +
      (x.texto ? '<span class="ad-p">' + E(x.texto) + "</span>" : "") + '<span class="ad-cta">' + E(x.cta || "Más información") + " →</span></span></a></aside>";
  }
  function publicidad(datos) {
    var H = (datos && datos.huecos) || {}, usadas = {}, x;
    // Premium · cabecera (todas las páginas)
    var mh = d.querySelector("header.masthead");
    if (mh && (x = elegir(H.cabecera, usadas))) { var w = d.createElement("div"); w.className = "mtx-hueco mtx-cab"; w.innerHTML = caja(x, "cabecera", true); (d.querySelector(".ticker") || mh).insertAdjacentElement("afterend", w); }
    // Premium · lateral del artículo
    var lat = d.querySelector("aside.m-aside");
    if (lat && (x = elegir(H["articulo-lateral"], usadas))) { var l = d.createElement("div"); l.className = "m-box mtx-hueco"; l.innerHTML = caja(x, "articulo-lateral", false); lat.insertBefore(l, lat.firstChild); }
    // Estándar · cierre del artículo (sustituye a la autopromoción del tema solo si hay caja)
    var fin = d.querySelector(".ad-end");
    if (fin && (x = elegir(H["articulo-cierre"], usadas))) fin.innerHTML = caja(x, "articulo-cierre", false);
    // Estándar · huecos de la portada
    [].forEach.call(d.querySelectorAll(".ad-block .ad.ad-wide"), function (n) { var y = elegir(H["portada-medio"], usadas); if (y) n.outerHTML = caja(y, "portada-medio", true); });
    // Básico · antes del pie
    var pie = d.querySelector("footer.site");
    if (pie && (x = elegir(H.pie, usadas))) { var p = d.createElement("div"); p.className = "mtx-hueco mtx-cab"; p.innerHTML = caja(x, "pie", true); pie.parentNode.insertBefore(p, pie); }
  }
  // ---------- 3. Seguimiento ----------
  var JEFE = /(?:^|;\s*)moticias_jefe=1/.test(d.cookie);
  function contar(id, h, t) {
    if (JEFE || navigator.webdriver || !id) return;
    var cuerpo = JSON.stringify({a: id, h: h || "?", p: location.pathname, t: t});
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
    if (d.body.classList.contains("post-template")) cuandoEste("aside.m-aside", function () { publicidad(j); vigilarCajas(); }); else { publicidad(j); vigilarCajas(); }
  }).catch(function () { vigilarCajas(); });

  // ---------- 2. Editor jefe ----------
  var SLUG = /^\/([a-z0-9]+(?:-[a-z0-9]+)*-[a-z0-9]{4})\/?$/;
  function enlace(slug, accion) {
    return API + "/gestor/?" + new URLSearchParams({pieza: slug, accion: accion || "", volver: location.href}).toString();
  }
  function herramientas() {
    var m = location.pathname.match(SLUG);
    if (d.body.classList.contains("post-template") && m) {
      var s = m[1], f = d.createElement("div");
      f.className = "mtx-fab";
      f.innerHTML = '<button type="button" aria-label="Herramientas del editor jefe" title="Editor jefe">✎</button><ul>' +
        '<li class="t">Editor jefe</li>' +
        '<li><a href="' + E(enlace(s, "editar")) + '">Editar</a></li>' +
        '<li><a href="' + E(enlace(s, "ia")) + '">Otro enfoque con IA</a></li>' +
        '<li><a href="' + E(enlace(s, "")) + '">Patrocinio y retoques</a></li>' +
        '<li><a class="r" href="' + E(enlace(s, "retirar")) + '">Retirar</a></li></ul>';
      f.querySelector("button").onclick = function () { f.classList.toggle("on"); };
      d.addEventListener("click", function (ev) { if (!f.contains(ev.target)) f.classList.remove("on"); });
      d.body.appendChild(f);
    }
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
})();
