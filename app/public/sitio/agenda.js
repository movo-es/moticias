/* MOTICIAS · Agenda de moticias.com (cambio OpenSpec agenda-de-eventos, 16-11-2026).
   Lo carga m.js solo en las páginas con .m-agenda. Todo el contenido ya está en el HTML que sirve Ghost; esto solo:
   1. filtra por mes, ciudad y tema a la vez (mapa, «Por lugar», leyenda y lista) y recalcula los contadores;
   2. ordena la lista por tema (por defecto) o por fecha;
   3. envía el formulario «Subir mi evento» a app.moticias.com/api/agenda (con tiempo mínimo y campo trampa);
   4. con la sesión del editor jefe, pone el icono ✎ en cada cita (editar o retirar en el gestor).
   Sin dependencias; si algo falla, la página sigue entera y legible. */
(function () {
  "use strict";
  var API = "https://app.moticias.com";
  var d = document;
  var raiz = d.querySelector(".m-agenda");
  if (!raiz) return;
  var $$ = function (s, el) { return [].slice.call((el || raiz).querySelectorAll(s)); };

  // ---------- 1 y 2. Filtros y orden ----------
  var lista = raiz.querySelector(".ma-lista");
  if (lista) {
    var citas = $$(".ma-cita", lista);
    var F = {mes: "", ciudad: "", tema: ""};
    var cumple = function (c, sin) {
      return (sin === "mes" || !F.mes || (" " + c.dataset.meses + " ").indexOf(" " + F.mes + " ") >= 0) &&
             (sin === "ciudad" || !F.ciudad || c.dataset.ciudad === F.ciudad) &&
             (sin === "tema" || !F.tema || c.dataset.tema === F.tema);
    };
    var pulsado = function (b, si) { b.setAttribute("aria-pressed", si ? "true" : "false"); };
    var colores = {};
    $$(".ma-tema-b").forEach(function (b) { var i = b.querySelector("i"); colores[b.dataset.tema] = i ? i.style.background : ""; });
    function pintar() {
      var vis = 0;
      citas.forEach(function (c) { var ok = cumple(c); c.hidden = !ok; if (ok) vis++; });
      // Meses: cuántas citas quedarían en cada mes con los otros dos filtros
      $$(".ma-mes").forEach(function (b) {
        var m = b.dataset.mes, n = citas.filter(function (c) { return cumple(c, "mes") && (!m || (" " + c.dataset.meses + " ").indexOf(" " + m + " ") >= 0); }).length;
        b.querySelector("b").textContent = n; pulsado(b, m === F.mes);
      });
      $$(".ma-tema-b").forEach(function (b) {
        var n = citas.filter(function (c) { return cumple(c, "tema") && c.dataset.tema === b.dataset.tema; }).length;
        b.querySelector("b").textContent = n; b.disabled = !n && F.tema !== b.dataset.tema; pulsado(b, b.dataset.tema === F.tema);
      });
      // Ciudades: marca del mapa y fila de «Por lugar»
      $$(".ma-pin").forEach(function (p) {
        var cs = citas.filter(function (c) { return cumple(c, "ciudad") && c.dataset.ciudad === p.dataset.ciudad; });
        var temas = {}; cs.forEach(function (c) { temas[c.dataset.tema] = 1; });
        var ts = Object.keys(temas), mixto = ts.length > 1, n = cs.length;
        if (!n) { p.setAttribute("hidden", ""); return; }
        p.removeAttribute("hidden");
        var marca = p.querySelector(".ma-pin-marca"), r = n === 1 ? 9 : 12 + Math.min(n, 6);
        marca.setAttribute("r", r); marca.setAttribute("fill", mixto ? "#FFFFFF" : (colores[ts[0]] || "#fff"));
        var aro = p.querySelector(".ma-pin-aro");
        if (mixto && !aro) { aro = d.createElementNS("http://www.w3.org/2000/svg", "circle"); aro.setAttribute("class", "ma-pin-aro"); p.insertBefore(aro, marca); }
        if (aro) { if (mixto) aro.setAttribute("r", r + 4); else aro.remove(); }
        p.querySelector(".ma-pin-n").textContent = n > 1 ? n : "";
        var nombre = p.getAttribute("aria-label").split(":")[0];
        p.setAttribute("aria-label", nombre + ": " + n + (n === 1 ? " cita" : " citas"));
        p.classList.toggle("ma-activo", F.ciudad === p.dataset.ciudad);
      });
      $$(".ma-lugares li").forEach(function (li) {
        var cs = citas.filter(function (c) { return cumple(c, "ciudad") && c.dataset.ciudad === li.dataset.ciudad; });
        li.hidden = !cs.length && F.ciudad !== li.dataset.ciudad;
        var b = li.querySelector("button"); b.querySelector("b").textContent = cs.length; pulsado(b, F.ciudad === li.dataset.ciudad);
        li.querySelector(".ma-lugar-titulos").textContent = cs.map(function (c) { return c.dataset.corto || c.querySelector("h3").textContent; }).join(" · ");
      });
      var vacio = raiz.querySelector(".ma-vacio"); if (vacio) vacio.hidden = vis > 0;
      var cuenta = raiz.querySelector(".ma-cuenta");
      if (cuenta) cuenta.textContent = (F.mes || F.ciudad || F.tema) ? vis + (vis === 1 ? " cita" : " citas") + " con estos filtros" : "";
    }
    var alterna = function (k, val) { F[k] = F[k] === val ? "" : val; pintar(); };
    $$(".ma-mes").forEach(function (b) { b.addEventListener("click", function () { F.mes = b.dataset.mes; pintar(); }); });
    $$(".ma-tema-b").forEach(function (b) { b.addEventListener("click", function () { alterna("tema", b.dataset.tema); }); });
    $$(".ma-lugar").forEach(function (b) { b.addEventListener("click", function () { alterna("ciudad", b.dataset.ciudad); }); });
    $$(".ma-pin").forEach(function (p) {
      var ir = function () { alterna("ciudad", p.dataset.ciudad); if (F.ciudad) { var li = raiz.querySelector('.ma-lugares li[data-ciudad="' + p.dataset.ciudad + '"]'); if (li) li.scrollIntoView({block: "nearest"}); } };
      p.addEventListener("click", ir);
      p.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); ir(); } });
    });
    $$(".ma-quitar").forEach(function (b) { b.addEventListener("click", function () { F.mes = F.ciudad = F.tema = ""; pintar(); }); });
    $$(".ma-orden button").forEach(function (b) {
      b.addEventListener("click", function () {
        var porFecha = b.dataset.orden === "fecha";
        citas.slice().sort(function (x, y) {
          return porFecha ? (x.dataset.inicio < y.dataset.inicio ? -1 : x.dataset.inicio > y.dataset.inicio ? 1 : 0) : (+x.dataset.ordenTema) - (+y.dataset.ordenTema);
        }).forEach(function (c) { lista.appendChild(c); });
        $$(".ma-orden button").forEach(function (o) { pulsado(o, o === b); });
      });
    });
    // Enlace directo a una cita (#id): se ve resaltada
    if (location.hash && raiz.querySelector(location.hash.replace(/[^#\w-]/g, ""))) raiz.querySelector(location.hash.replace(/[^#\w-]/g, "")).style.background = "#fff8d6";
    pintar();
  }

  // ---------- 3. «Subir mi evento» ----------
  var form = raiz.querySelector("form[data-agenda-form]");
  if (form) {
    var t0 = Date.now();
    var res = form.querySelector(".ma-resultado");
    var resumen = form.querySelector("#f-resumen");
    if (resumen) resumen.addEventListener("input", function () {
      var n = (resumen.value.match(/\S+/g) || []).length, s = resumen.parentNode.querySelector("small");
      if (s) s.textContent = "Hasta 60 palabras: de qué trata y para quién. Llevas " + n + ".";
      resumen.setCustomValidity(n > 60 ? "Pasa de 60 palabras" : "");
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); res.textContent = "Revisa los campos marcados con asterisco y el permiso de tratamiento."; return; }
      var datos = {};
      [].forEach.call(form.elements, function (el) { if (!el.name) return; datos[el.name] = el.type === "checkbox" ? el.checked : el.value.trim(); });
      datos.t = Math.round((Date.now() - t0) / 1000);
      var btn = form.querySelector("button[type=submit]"); btn.disabled = true; res.textContent = "Enviando…";
      fetch(API + "/api/agenda?a=enviar", {method: "POST", headers: {"Content-Type": "text/plain"}, body: JSON.stringify(datos)})
        .then(function (r) { return r.json().then(function (j) { return [r.ok, j]; }); })
        .then(function (x) {
          if (x[0]) { form.innerHTML = '<p class="respuesta-directa"><strong>Recibido.</strong> ' + String(x[1].mensaje || "").replace(/</g, "&lt;") + "</p>"; return; }
          btn.disabled = false; res.textContent = x[1].error || "No se pudo enviar. Prueba más tarde.";
        })
        .catch(function () { btn.disabled = false; res.textContent = "No se pudo enviar. Prueba más tarde o escribe a redaccion@moticias.com."; });
    });
  }

  // ---------- 4. Icono ✎ del editor jefe en cada cita ----------
  if (/(?:^|;\s*)moticias_jefe=1/.test(d.cookie)) {
    fetch(API + "/api/gestor?a=yo", {credentials: "include"}).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
      if (!j || !j.jefe) return;
      $$(".ma-cita").forEach(function (c) {
        var h = c.querySelector("h3"); if (!h || h.querySelector(".mtx-ed")) return;
        [["✎", "editar", "Editar esta cita"], ["⊘", "retirar", "Retirar esta cita"]].forEach(function (x) {
          var a = d.createElement("a");
          a.className = "mtx-ed"; a.textContent = " " + x[0]; a.title = x[2]; a.setAttribute("aria-label", x[2]);
          a.href = API + "/gestor/?vista=agenda&evento=" + encodeURIComponent(c.id) + "&accion=" + x[1];
          a.style.cssText = "font-size:.8em;text-decoration:none;margin-left:6px";
          h.appendChild(a);
        });
      });
    }).catch(function () {});
  }
})();
