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
      («Análisis del director», «Análisis», «Reportaje», «Noticia», «Nota de prensa · Comunicado de …»), leída de
      app.moticias.com/buscador/tipos.json (lo genera src/export_search_index.py). Dentro de cada pieza la marca ya va
      en el cuerpo del post (src/ghost_publish.py), así que no depende de este script ni del tema.
   6. Pinta las páginas de sección con sus piezas (la plantilla del tema salía vacía).
   5. Oculta la marca «Powered by Ghost» de la ventana de entrada y suscripción de Ghost.
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
    var pagadas = c.filter(function (x) { return x.tipo !== "grupo"; });
    if (pagadas.length) c = pagadas;
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
    // Premium · cabecera (todas las páginas)
    var mh = d.querySelector("header.masthead");
    if (mh && (x = elegir(H.cabecera, usadas))) { var w = d.createElement("div"); w.className = "mtx-hueco mtx-cab"; w.innerHTML = caja(x, "cabecera", true); (d.querySelector(".ticker") || mh).insertAdjacentElement("afterend", w); }
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
  var secActual = (location.pathname.match(/^\/([a-z]+)\/?$/) || [])[1];
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
      var lista = ix.piezas.filter(SECCIONES[secActual]).sort(function (a, b) { return a.d < b.d ? 1 : a.d > b.d ? -1 : 0; });
      var main = d.querySelector("main#main"), vacio = main.querySelector("p.empty");
      var caja = vacio ? vacio.parentNode : null;
      if (!caja) { var sec0 = d.createElement("section"); sec0.className = "block"; caja = d.createElement("div"); caja.className = "wrap"; sec0.appendChild(caja); main.insertBefore(sec0, main.firstChild); }
      if (vacio) vacio.remove();
      if (!lista.length) { caja.insertAdjacentHTML("beforeend", '<p class="empty">Todavía no hay piezas en esta sección.</p>'); return; }
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
      if (!x || (u.pathname === location.pathname) || a.parentNode.querySelector(".mtx-tc") || a.closest(".mtx-sec")) return;
      var s = d.createElement("span");
      s.className = "mtx-tc t-" + x[0]; s.textContent = x[1];
      s.style.display = "block"; a.insertAdjacentElement("beforebegin", s);
    });
  }
  // Las cajas que pinta el tema por su cuenta (huecos sin caja del gestor) también llevan rel="sponsored". Las del grupo
  // (clase «house» del tema, que no está versionado) llevan además la etiqueta única «Contenido patrocinado · servicio del
  // grupo», y su enlace, utm_medium=grupo. Cuando el tema se versione (publicar-en-ghost-v1), esto pasa al tema.
  var GRUPO = "Contenido patrocinado · servicio del grupo";
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
    fetch(API + "/buscador/tipos.json").then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { if (j && j.piezas) marcas(j.piezas); }).catch(function () {});
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
})();
