/* MOTICIAS · tema de Ghost. Mejoras en el navegador; el contenido ya llega completo desde el servidor. */
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };
  function todayISO() { var d = new Date(); return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); }
  function days(iso) { var a = Date.parse(String(iso).slice(0, 10) + "T00:00:00Z"), b = Date.parse(todayISO() + "T00:00:00Z"); return isNaN(a) ? null : Math.round((a - b) / 864e5); }

  // Teletipo: la lista del BOE de la página de la edición sube bajo la cabecera.
  var src = $(".m-ticker"), tk = $("#ticker");
  if (src && tk) {
    var items = $$("li", src).map(function (li) { return '<span class="item">' + li.innerHTML + "</span>"; }).join("");
    $(".label", tk).textContent = ($(".m-ticker-label", src) || {}).textContent || "BOE";
    $(".reel", tk).innerHTML = items + items;
    tk.hidden = false;
  }

  // Plazos: «hoy», «mañana», «en N días» según la fecha del lector.
  $$(".m-deadline[data-date]").forEach(function (el) {
    var k = days(el.getAttribute("data-date")), b = $(".m-countdown", el);
    if (!b || k == null) return;
    b.textContent = k < 0 ? "cerrado" : k === 0 ? "hoy" : k === 1 ? "mañana" : "en " + k + " días";
    if (k < 0 && $$(".m-deadline[data-date]").length > 4) el.hidden = true;
  });

  // Cronología: marca como «por venir» lo que aún no ha pasado hoy.
  var t = todayISO();
  $$(".m-tl li[data-date]").forEach(function (li) { li.classList.toggle("next", li.getAttribute("data-date") > t); });

  // Mapa de la edición: dibuja España (assets/js/spain.js) y sitúa las piezas con lugar.
  var box = $(".m-map[data-map]");
  if (box) {
    var s = document.createElement("script");
    s.src = (document.querySelector('link[href*="/assets/css/moticias.css"]') || { href: "/assets/css/moticias.css" }).href.replace(/css\/moticias\.css.*/, "js/spain.js");
    s.onload = function () { drawMap(box); };
    document.body.appendChild(s);
  }
  function drawMap(box) {
    var SP = window.SPAIN_PATHS; if (!SP) return;
    var m = SP.meta;
    var proj = function (lon, lat) { var x = lon, y = lat; if (lat < 30 && lon < -12) { x += m.dlon; y += m.dlat; } return [(x - m.lon0) * m.k * m.cos0, -(y - m.lat0) * m.k]; };
    var bb = SP.bbox, pad = 24, cb = SP.canariasBox;
    var lis = $$(".m-map-list li[data-lat]");
    var groups = [];
    lis.forEach(function (li, i) {
      var p = proj(parseFloat(li.getAttribute("data-lon")), parseFloat(li.getAttribute("data-lat")));
      var g = groups.filter(function (q) { return Math.hypot(q.x - p[0], q.y - p[1]) < 14; })[0];
      if (g) g.items.push(li); else groups.push({ x: p[0], y: p[1], items: [li], sec: li.getAttribute("data-sec"), place: ($(".m-place", li) || {}).textContent || "" });
    });
    groups.forEach(function (g, i) { g.items.forEach(function (li) { li.setAttribute("data-pin", i); }); });
    var pins = groups.map(function (g, i) {
      return '<g class="pin ' + esc(g.sec) + '" data-pin="' + i + '" transform="translate(' + g.x.toFixed(1) + " " + g.y.toFixed(1) + ')"><circle class="halo" r="6"/><circle class="core" r="' + (g.items.length > 1 ? 6.5 : 5) + '"/><text x="9" y="4">' + esc(g.place.split(",")[0].slice(0, 28)) + (g.items.length > 1 ? " (" + g.items.length + ")" : "") + "</text></g>";
    }).join("");
    box.innerHTML = '<svg viewBox="' + (bb[0] - pad) + " " + (bb[1] - pad) + " " + (bb[2] - bb[0] + 2 * pad) + " " + (bb[3] - bb[1] + 2 * pad) + '" role="img" aria-label="Mapa de España con los lugares de las piezas de la edición"><g>' +
      SP.provinces.map(function (p) { return '<path class="prov" d="' + p.d + '"><title>' + esc(p.name) + "</title></path>"; }).join("") +
      '<path class="ccaa" d="' + SP.ccaa + '"/><path class="border" d="' + SP.border + '"/><rect class="inset" x="' + (cb[0] - 14) + '" y="' + (cb[1] - 14) + '" width="' + (cb[2] - cb[0] + 28) + '" height="' + (cb[3] - cb[1] + 28) + '" rx="3"/></g>' + pins + "</svg>";
    var setActive = function (i) { $$("[data-pin]").forEach(function (el) { el.classList.toggle("active", el.getAttribute("data-pin") === String(i)); }); };
    $$(".pin", box).forEach(function (p) {
      p.addEventListener("mouseenter", function () { setActive(p.getAttribute("data-pin")); });
      p.addEventListener("click", function () { setActive(p.getAttribute("data-pin")); var li = $('.m-map-list li[data-pin="' + p.getAttribute("data-pin") + '"]'); if (li) li.scrollIntoView({ block: "nearest", behavior: "smooth" }); });
    });
    lis.forEach(function (li) { li.addEventListener("mouseenter", function () { setActive(li.getAttribute("data-pin")); }); });
  }
})();
