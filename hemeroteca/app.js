/* Hemeroteca MOTICIAS: máquina del tiempo y búsqueda sobre todas las ediciones del portal. */
(function () {
  "use strict";
  var PORTAL_URL = "https://claude.ai/artifact/6r3hgcemzjFR7LcweAXgEZ";
  var FONTS = "https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300..800;1,6..72,300..800&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return ESC[c]; }); }

  /* ---------- Fechas ---------- */
  var DAYS = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];
  var MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  var MON = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  function pd(s) { var m = /^(\d{4})-(\d{2})(?:-(\d{2}))?/.exec(String(s || "")); return m ? new Date(Date.UTC(+m[1], +m[2] - 1, +(m[3] || 1), 12)) : null; }
  function fLong(s) { var d = pd(s); return d ? DAYS[d.getUTCDay()] + ", " + d.getUTCDate() + " de " + MONTHS[d.getUTCMonth()] + " de " + d.getUTCFullYear() : ""; }
  function fMid(s) { var d = pd(s); return d ? d.getUTCDate() + " de " + MONTHS[d.getUTCMonth()] + " de " + d.getUTCFullYear() : ""; }
  function fShort(s) { var d = pd(s); if (!d) return ""; return /^\d{4}-\d{2}$/.test(String(s)) ? MON[d.getUTCMonth()] + " " + d.getUTCFullYear() : d.getUTCDate() + " " + MON[d.getUTCMonth()] + " " + d.getUTCFullYear(); }
  function fDay(s) { var d = pd(s); if (!d) return ""; return /^\d{4}-\d{2}$/.test(String(s)) ? MON[d.getUTCMonth()] + " " + d.getUTCFullYear() : d.getUTCDate() + " " + MON[d.getUTCMonth()]; }
  function fNum(s) { var d = pd(s); return d ? String(d.getUTCDate()).padStart(2, "0") + "-" + String(d.getUTCMonth() + 1).padStart(2, "0") + "-" + d.getUTCFullYear() : ""; }
  function diff(a, b) { return Math.round((pd(b) - pd(a)) / 864e5); }
  function rel(from, to) { var n = diff(from, to); if (!isFinite(n)) return ""; if (n === 0) return "ese día"; if (n > 0) return n === 1 ? "al día siguiente" : "a " + n + " días"; return n === -1 ? "la víspera" : "hace " + (-n) + " días"; }
  function hhmm(iso) { var m = /T(\d{2}:\d{2})/.exec(String(iso || "")); return m ? m[1] : ""; }
  function words(t) { var s = String(t || "").trim(); return s ? s.split(/\s+/).length : 0; }
  function nf(n) { return Number(n || 0).toLocaleString("es-ES"); }
  function safeUrl(u) { u = String(u || "").trim(); return /^https?:\/\//i.test(u) ? u : ""; }
  function plural(n, a, b) { return nf(n) + " " + (n === 1 ? a : b); }

  /* ---------- Secciones ---------- */
  var SEC = { tierra: "Tierra", mar: "Mar", aire: "Aire", regulacion: "Regulación", licitaciones: "Licitaciones", logistica: "Logística", tecnologia: "Tecnología", analisis: "Análisis" };
  var SEC_ORDER = ["tierra", "mar", "aire", "regulacion", "licitaciones", "logistica", "tecnologia"];
  var KIND = { noticia: "Noticia", analisis: "Análisis", reportaje: "Reportaje" };
  var AGK = { plazo: "Plazo", consulta: "Consulta", vigor: "En vigor", evento: "Evento" };
  var SEC_HEX = { tierra: "#4f6f3a", mar: "#1c5d74", aire: "#2e63a8", regulacion: "#4a3f7a", licitaciones: "#b0621c", analisis: "#7a1f2b", logistica: "#7a6a2a", tecnologia: "#0e7c86" };
  function secOf(a) { return a.kind === "analisis" ? "analisis" : a.section; }
  function secVar(s) { return "var(--s-" + (SEC[s] ? s : "otros") + ")"; }

  function artSvg(section, seed) {
    var col = SEC_HEX[section] || "#0f1f33", h = 0, i, lines = "";
    String(seed || "m").split("").forEach(function (c) { h = (h * 31 + c.charCodeAt(0)) >>> 0; });
    for (i = 0; i < 14; i++) { var y = 20 + i * 22 + ((h >> (i % 7)) % 9); lines += '<path d="M-20 ' + y + " Q 300 " + (y - 40 - (h % 30)) + " 620 " + (y + 10) + '" stroke="rgba(255,255,255,.' + ((i % 3) + 1) + '5)" stroke-width="' + (1 + (i % 3)) + '" fill="none"/>'; }
    var letter = (SEC[section] || "M").charAt(0);
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400"><rect width="600" height="400" fill="' + col + '"/>' + lines + '<text x="40" y="360" font-family="Georgia,serif" font-size="260" fill="rgba(255,255,255,.14)" font-weight="700">' + letter + "</text></svg>";
    return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
  }

  /* ---------- Marcado ligero (mismo subconjunto que el portal) ---------- */
  function inline(t) {
    return esc(t)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
      .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      .replace(/\[([^\]]+)\]\((#a-[a-z0-9-]+)\)/g, '<a href="$2">$1</a>');
  }
  function md(src) {
    var lines = String(src || "").replace(/\r/g, "").split("\n"), html = "", para = [], list = null, first = true;
    function fp() { if (para.length) { html += "<p" + (first ? ' class="lede"' : "") + ">" + inline(para.join(" ")) + "</p>"; para = []; first = false; } }
    function fl() { if (list) { html += "<" + list.t + ">" + list.i.map(function (x) { return "<li>" + inline(x) + "</li>"; }).join("") + "</" + list.t + ">"; list = null; } }
    lines.forEach(function (raw) {
      var line = raw.replace(/\s+$/, ""), m;
      if (!line.trim()) { fp(); fl(); return; }
      if ((m = /^(#{1,3})\s+(.*)$/.exec(line))) { fp(); fl(); var l = m[1].length < 3 ? 2 : 3; html += "<h" + l + ">" + inline(m[2]) + "</h" + l + ">"; return; }
      if (line.indexOf(">>") === 0) { fp(); fl(); html += '<p class="pull">' + inline(line.slice(2).trim()) + "</p>"; return; }
      if (line.indexOf(">") === 0) { fp(); fl(); html += "<blockquote><p>" + inline(line.slice(1).trim()) + "</p></blockquote>"; return; }
      if (/^(-{3,}|\*{3,})$/.test(line)) { fp(); fl(); return; }
      if ((m = /^[-*]\s+(.*)$/.exec(line))) { fp(); if (!list || list.t !== "ul") { fl(); list = { t: "ul", i: [] }; } list.i.push(m[1]); return; }
      if ((m = /^\d+[.)]\s+(.*)$/.exec(line))) { fp(); if (!list || list.t !== "ol") { fl(); list = { t: "ol", i: [] }; } list.i.push(m[1]); return; }
      fl(); para.push(line.trim());
    });
    fp(); fl();
    return html;
  }
  function plain(s) { return String(s || "").replace(/\[([^\]]+)\]\([^)]*\)/g, "$1").replace(/^#{1,3}\s+/gm, "").replace(/^>>?\s?/gm, "").replace(/\*\*|\*/g, "").replace(/^[-*]\s+/gm, "").replace(/\s+/g, " ").trim(); }

  /* ---------- Búsqueda ---------- */
  function norm(s) { return String(s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase(); }
  var ACC = { a: "aáàâä", e: "eéèêë", i: "iíìîï", o: "oóòôö", u: "uúùûü", n: "nñ", c: "cç" };
  function termSrc(t) { return t.split("").map(function (ch) { return ACC[ch] ? "[" + ACC[ch] + "]" : ch.replace(/[.*+?^${}()|[\]\\\/]/g, "\\$&"); }).join(""); }
  function hlRe(terms) {
    var t = terms.filter(function (x) { return x.length > 1 || terms.length === 1; }).sort(function (a, b) { return b.length - a.length; });
    return t.length ? new RegExp(t.map(termSrc).join("|"), "gi") : null;
  }
  function hl(text, re) {
    text = String(text == null ? "" : text);
    if (!re) return esc(text);
    var out = "", last = 0, m;
    re.lastIndex = 0;
    while ((m = re.exec(text))) {
      if (!m[0]) { re.lastIndex++; continue; }
      out += esc(text.slice(last, m.index)) + "<mark>" + esc(m[0]) + "</mark>";
      last = m.index + m[0].length;
    }
    return out + esc(text.slice(last));
  }
  function snippet(text, re, len) {
    text = String(text || "").replace(/\s+/g, " ").trim(); len = len || 230;
    if (!re) return esc(text.slice(0, len)) + (text.length > len ? "…" : "");
    re.lastIndex = 0;
    var m = re.exec(text);
    if (!m) return null;
    var s = Math.max(0, m.index - 80), e;
    if (s > 0) { var sp = text.indexOf(" ", s); if (sp > -1 && sp < m.index) s = sp + 1; }
    e = Math.min(text.length, s + len);
    if (e < text.length) { var sp2 = text.lastIndexOf(" ", e); if (sp2 > m.index) e = sp2; }
    return (s > 0 ? "…" : "") + hl(text.slice(s, e), re) + (e < text.length ? "…" : "");
  }
  var STOP = {};
  "a al con de del e el en la las lo los o para por que se su sus un una y".split(" ").forEach(function (w) { STOP[w] = 1; });
  function parseQ(q) {
    var terms = [], neg = [], re = /(-?)"([^"]+)"|(\S+)/g, m;
    while ((m = re.exec(q))) {
      var raw = m[2] != null ? m[2] : m[3], isNeg = m[1] === "-";
      if (m[2] == null && raw.length > 1 && raw.charAt(0) === "-") { isNeg = true; raw = raw.slice(1); }
      var t = norm(raw).replace(/^[^a-z0-9]+|[^a-z0-9]+$/g, "");
      if (t) (isNeg ? neg : terms).push(t);
    }
    var core = terms.filter(function (t) { return !STOP[t]; });
    return { terms: core.length ? core : terms, neg: neg };
  }
  function cnt(hay, t) { if (!hay) return 0; var n = 0, i = hay.indexOf(t); while (i > -1 && n < 12) { n++; i = hay.indexOf(t, i + t.length); } return n; }
  var W = { t: 12, k: 6, s: 4, m: 2, b: 1, r: 2 };
  var REG_T = /real decreto|ley|orden|resoluci|disposici|acuerdo|convenio|informaci/i, LIC_T = /licitaci|formalizaci|concesi|adjudicaci/i;
  function inAmbito(it, amb) {
    if (!amb) return true;
    var x = it.ref, terr = amb === "tierra" || amb === "mar" || amb === "aire";
    if (it.type === "boletin") { if (terr) return (x.modos || []).indexOf(amb) > -1; if (amb === "licitaciones") return LIC_T.test(x.tipo || ""); if (amb === "regulacion") return REG_T.test(x.tipo || "") && !LIC_T.test(x.tipo || ""); return false; }
    if (it.type === "plazo") { if (terr) return x.mode === amb; if (amb === "licitaciones") return x.kind === "plazo"; if (amb === "regulacion") return x.kind === "consulta" || x.kind === "vigor"; return false; }
    if (amb === "analisis") return x.kind === "analisis";
    return x.section === amb;
  }
  function typeRank(it) { return it.type === "boletin" ? 1 : it.type === "plazo" ? 2 : 0; }

  /* ---------- Estado ---------- */
  var S = { raw: null, idx: null, eds: [], ed: {}, arts: [], art: {}, bols: [], ags: [], items: [], tags: [],
    cur: null, view: "", q: "", f: { type: "todo", amb: "", from: "", to: "", sort: "rel" }, shown: 30,
    fromSearch: false, dl: null, standalone: false };

  function ingest(raw) {
    S.raw = raw; S.idx = raw.index || {};
    (raw.chunks || []).forEach(function (ch) {
      S.eds = S.eds.concat(ch.editions || []); S.arts = S.arts.concat(ch.articles || []);
      S.bols = S.bols.concat(ch.boletines || []); S.ags = S.ags.concat(ch.agenda || []);
    });
    S.eds.sort(function (a, b) { return a.date < b.date ? -1 : 1; });
    S.eds.forEach(function (e, i) { e._i = i; S.ed[e.date] = e; });
    var sums = {}; (S.idx.editions || []).forEach(function (s) { sums[s.date] = s; });
    S.eds.forEach(function (e) { e._sum = sums[e.date] || {}; });
    S.arts.forEach(function (a) { S.art[a.id] = a; a._plain = plain(a.body_md); a._words = words(a._plain); });
    var tagc = {};
    S.arts.forEach(function (a) {
      (a.tags || []).forEach(function (t) { var k = norm(t); if (!tagc[k]) tagc[k] = { t: t, n: 0 }; tagc[k].n++; });
      S.items.push({ type: a.kind === "analisis" ? "analisis" : a.kind === "reportaje" ? "reportaje" : "noticia", date: a.date, ref: a,
        f: { t: norm(a.title), k: norm([a.kicker, a.subtitle].join(" ")), s: norm([a.summary, a.key_fact, (a.tags || []).join(" ")].join(" ")),
          m: norm([a.actors, a.relevance_for, a.why, a.next, a.author].join(" ")), b: norm(a._plain),
          r: norm([(a.sources || []).map(function (s) { return s.outlet + " " + s.title; }).join(" "), a.doc_ref, a.authority].join(" ")) } });
    });
    S.bols.forEach(function (b) { S.items.push({ type: "boletin", date: b.edicion || b.fecha, ref: b, f: { t: norm(b.titulo_corto || b.titulo), s: norm([b.titulo, b.nota].join(" ")), r: norm([b.referencia, b.organo, b.tipo].join(" ")) } }); });
    S.ags.forEach(function (g) { S.items.push({ type: "plazo", date: g.edicion || g.date, ref: g, f: { t: norm(g.title), r: norm([g.authority, g.amount, AGK[g.kind] || g.kind].join(" ")) } }); });
    S.tags = Object.keys(tagc).map(function (k) { return tagc[k]; }).filter(function (x) { return x.n > 1; }).sort(function (a, b) { return b.n - a.n || a.t.localeCompare(b.t); }).slice(0, 14);
  }
  function latest() { return S.eds.length ? S.eds[S.eds.length - 1].date : null; }
  function edOrder(d) {
    var e = S.ed[d], arts = S.arts.filter(function (a) { return a.date === d; });
    var lead = (e && S.art[e.lead_id] && S.art[e.lead_id].date === d && S.art[e.lead_id]) || arts.filter(function (a) { return a.featured === 1; })[0] || arts[0];
    var second = arts.filter(function (a) { return a.featured === 2 && a !== lead; })[0];
    var ana = (e && S.art[e.analysis_id] && S.art[e.analysis_id].date === d && S.art[e.analysis_id]) || arts.filter(function (a) { return a.kind === "analisis"; })[0];
    var rest = arts.filter(function (a) { return a !== lead && a !== second && a !== ana; });
    rest.sort(function (a, b) { return (a.relevance === "ALTA" ? 0 : 1) - (b.relevance === "ALTA" ? 0 : 1) || String(b.published_at || "").localeCompare(String(a.published_at || "")); });
    var groups = [];
    SEC_ORDER.forEach(function (s) { var g = rest.filter(function (a) { return a.kind === "noticia" && a.section === s; }); if (g.length) groups.push({ key: s, name: SEC[s], items: g }); });
    var other = rest.filter(function (a) { return a.kind === "noticia" && SEC_ORDER.indexOf(a.section) < 0; });
    if (other.length) groups.push({ key: "otros", name: "Otras piezas", items: other });
    var rep = rest.filter(function (a) { return a.kind === "reportaje"; });
    if (rep.length) groups.push({ key: "otros", name: "Reportajes", items: rep });
    var anas = rest.filter(function (a) { return a.kind === "analisis"; });
    if (anas.length) groups.push({ key: "analisis", name: "Análisis", items: anas });
    var flat = [lead, second, ana].filter(Boolean);
    groups.forEach(function (g) { flat = flat.concat(g.items); });
    return { lead: lead, second: second, ana: ana, groups: groups, flat: flat, arts: arts };
  }

  /* ---------- Piezas de interfaz ---------- */
  function imgTag(a, cls) {
    var im = a.image, sec = secOf(a);
    if (im && im.src) {
      return '<figure class="ph ' + (cls || "") + '"><img src="' + esc(im.src) + '" alt="' + esc(im.alt || "") + '" loading="lazy" data-sec="' + esc(sec) + '" data-seed="' + esc(a.id) + '"></figure>';
    }
    return '<figure class="ph ' + (cls || "") + '"><img src="' + artSvg(sec, a.id) + '" alt=""></figure>';
  }
  function credit(im) {
    if (!im) return "";
    var p = [im.credit, im.license].filter(Boolean).map(esc).join(" · ");
    var src = safeUrl(im.source);
    return p ? '<p class="credit">Foto: ' + p + (src ? ' · <a href="' + esc(src) + '" target="_blank" rel="noopener">origen</a>' : "") + "</p>" : "";
  }
  function edTag(d) { var e = S.ed[d]; return e ? '<a class="edl" href="#e-' + esc(d) + '">Edición nº ' + esc(e.number) + "</a>" : ""; }
  function linkOrText(text, url, re) { var u = safeUrl(url); var t = re ? hl(text, re) : esc(text); return u ? '<a href="' + esc(u) + '" target="_blank" rel="noopener">' + t + "</a>" : t; }

  /* ---------- Cabecera y pie ---------- */
  function shell() {
    var app = $("#app");
    app.innerHTML =
      '<header class="top"><div class="wrap top-in">' +
        '<a class="brand" href="#maquina" aria-label="Hemeroteca MOTICIAS, inicio"><span class="wm"><span class="m">M</span>OTICIAS</span><span class="brand-sub">Hemeroteca</span></a>' +
        '<nav class="tabs" aria-label="Vistas"><a href="#maquina" data-v="maquina"><span class="long">Máquina del tiempo</span><span class="short">Ediciones</span></a><a href="#buscar" data-v="buscar">Buscar</a></nav>' +
        '<details class="dl" id="dl" hidden><summary>Descargar</summary><div class="dl-menu">' +
          '<button type="button" data-dl="html"><b>Hemeroteca en un archivo (.html)</b><small>Todas las ediciones, con búsqueda y máquina del tiempo. Se abre sin conexión; las fotos no viajan en el archivo.</small></button>' +
          '<button type="button" data-dl="json"><b>Datos (.json)</b><small>Ediciones, piezas, boletines y plazos tal como los guarda el portal.</small></button>' +
        "</div></details>" +
        '<form class="qform" role="search" id="qform"><label for="q" class="vh">Buscar en todas las ediciones</label><span class="ico" aria-hidden="true"></span>' +
          '<input id="q" type="search" autocomplete="off" spellcheck="false" placeholder="Buscar en todas las ediciones: Adif, «tope de precios», BOE-A-2026…"><kbd aria-hidden="true">/</kbd></form>' +
      "</div></header>" +
      (S.standalone ? '<div class="offline"><div class="wrap">Copia en un solo archivo generada el ' + esc(fMid((S.idx.generated_at || "").slice(0, 10))) + ". Las fotos no se incluyen; se muestra una ilustración en su lugar.</div></div>" : "") +
      '<main id="main" tabindex="-1"></main>' +
      '<footer class="foot"><div class="wrap"><div><b>Hemeroteca MOTICIAS</b> · ' + plural(S.eds.length, "edición", "ediciones") + " · " + plural(S.arts.length, "pieza", "piezas") + " · " + plural(S.bols.length, "boletín", "boletines") + " · " + plural(S.ags.length, "plazo", "plazos") +
      "<br>Cada edición se muestra como quedó al cierre; si una pieza se corrigió después, consta la fecha de revisión.</div>" +
      "<div>Actualizada el " + esc(fMid((S.idx.generated_at || "").slice(0, 10))) + (hhmm(S.idx.generated_at) ? " a las " + esc(hhmm(S.idx.generated_at)) : "") + ' · <a href="' + PORTAL_URL + '" target="_blank" rel="noopener">Abrir el portal</a></div></div></footer>' +
      '<div class="toast" id="toast" role="status" aria-live="polite"></div>';
    var q = $("#q"), t = null;
    q.addEventListener("input", function () {
      clearTimeout(t);
      t = setTimeout(function () {
        S.q = q.value; S.shown = 30;
        if (S.view !== "buscar") { location.hash = "buscar"; } else { renderResults(); }
      }, 140);
    });
    $("#qform").addEventListener("submit", function (e) { e.preventDefault(); S.q = q.value; if (S.view !== "buscar") location.hash = "buscar"; else renderResults(); });
    $$("[data-dl]").forEach(function (b) { b.addEventListener("click", function () { doDownload(b.getAttribute("data-dl")); }); });
  }
  function toast(msg) { var el = $("#toast"); if (!el) return; el.textContent = msg; el.className = "toast show"; clearTimeout(toast.t); toast.t = setTimeout(function () { el.className = "toast"; }, 3400); }
  function setTabs() { $$(".tabs a").forEach(function (a) { var on = a.getAttribute("data-v") === (S.view === "lector" ? "" : S.view); if (on) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); }); }

  /* ---------- Máquina del tiempo ---------- */
  function seriesSvg(series, cur) {
    var ks = Object.keys(series || {}).sort();
    if (!ks.length) return "";
    var Wd = 320, H = 136, pl = 26, pr = 6, pt = 14, pb = 22, n = ks.length, bw = (Wd - pl - pr) / n;
    var max = 1; ks.forEach(function (k) { max = Math.max(max, +((series[k] || {}).total) || 0); });
    var p = Math.pow(10, Math.floor(Math.log10(max))), mm = max / p, top = (mm <= 1 ? 1 : mm <= 2 ? 2 : mm <= 5 ? 5 : 10) * p;
    function y(v) { return pt + (H - pt - pb) * (1 - v / top); }
    var g = "";
    [0, top / 2, top].forEach(function (v) { g += '<line class="grid" x1="' + pl + '" x2="' + (Wd - pr) + '" y1="' + y(v).toFixed(1) + '" y2="' + y(v).toFixed(1) + '"/><text class="ax" x="' + (pl - 5) + '" y="' + (y(v) + 3).toFixed(1) + '" text-anchor="end">' + Math.round(v) + "</text>"; });
    ks.forEach(function (k, i) {
      var v = series[k] || {}, tot = +v.total || 0, lic = Math.min(tot, +v.lic || 0), disp = Math.max(0, tot - lic);
      var x = pl + i * bw + bw * 0.16, w = bw * 0.68;
      g += '<g class="' + (k === cur ? "is-cur" : "") + '"><title>' + esc(fDay(k)) + ": " + tot + " referencias (" + lic + " licitaciones y formalizaciones, " + disp + " disposiciones y resoluciones)</title>" +
        '<rect class="b-lic" x="' + x.toFixed(1) + '" y="' + y(lic).toFixed(1) + '" width="' + w.toFixed(1) + '" height="' + (y(0) - y(lic)).toFixed(1) + '"/>' +
        '<rect class="b-disp" x="' + x.toFixed(1) + '" y="' + y(tot).toFixed(1) + '" width="' + w.toFixed(1) + '" height="' + (y(lic) - y(tot)).toFixed(1) + '"/>' +
        '<text class="ax" x="' + (x + w / 2).toFixed(1) + '" y="' + (H - 8) + '" text-anchor="middle">' + pd(k).getUTCDate() + "</text>" +
        (k === cur || i === n - 1 ? '<text class="val" x="' + (x + w / 2).toFixed(1) + '" y="' + (y(tot) - 4).toFixed(1) + '" text-anchor="middle">' + tot + "</text>" : "") + "</g>";
    });
    return '<svg viewBox="0 0 ' + Wd + " " + H + '" role="img" aria-label="Referencias de transporte en el BOE por día, del ' + esc(fDay(ks[0])) + " al " + esc(fDay(ks[n - 1])) + '">' + g + "</svg>";
  }
  function itemLi(a) {
    return '<li class="it"><a href="#a-' + esc(a.id) + '"><span class="k">' + esc(a.kicker || KIND[a.kind] || "") + '</span><span class="t">' + esc(a.title) + "</span>" + (a.subtitle ? '<span class="s">' + esc(a.subtitle) + "</span>" : "") + "</a></li>";
  }
  function renderMachine(d, dir) {
    var e = S.ed[d]; if (!e) return;
    S.cur = d;
    var i = e._i, prev = S.eds[i - 1], next = S.eds[i + 1], prev2 = S.eds[i - 2], last = latest();
    var o = edOrder(d), sum = e._sum.counts || {};
    var bols = S.bols.filter(function (b) { return b.edicion === d; }).sort(function (a, b) { return String(b.fecha).localeCompare(String(a.fecha)) || String(a.referencia).localeCompare(String(b.referencia)); });
    var open = S.ags.filter(function (g) { return String(g.edicion || "") <= d && String(g.date) >= d; }).sort(function (a, b) { return String(a.date).localeCompare(String(b.date)); });
    var nWords = o.arts.reduce(function (s, a) { return s + a._words; }, 0), nSrc = o.arts.reduce(function (s, a) { return s + (a.sources || []).length; }, 0);
    var months = {}, rail = S.eds.map(function (x) {
      var m = x.date.slice(0, 7), first = !months[m]; months[m] = 1;
      return '<li><a class="st" href="#e-' + esc(x.date) + '"' + (x.date === d ? ' aria-current="true"' : "") + ' title="Edición nº ' + esc(x.number) + " · " + esc(fLong(x.date)) + '">' + (first ? '<span class="mon">' + esc(MONTHS[pd(x.date).getUTCMonth()] + " " + x.date.slice(0, 4)) + "</span>" : "") + '<span class="dot"></span><span class="lbl">' + esc(fDay(x.date)) + '</span><span class="n">nº ' + esc(x.number) + "</span></a></li>";
    }).join("");
    var lead = o.lead, html = "";
    html += '<section class="tm wrap" aria-label="Máquina del tiempo">' +
      '<div class="tm-head">' +
        '<a class="navbtn" href="' + (prev ? "#e-" + esc(prev.date) : "#maquina") + '"' + (prev ? "" : ' aria-disabled="true" tabindex="-1"') + ' data-key="prev"><span class="arr" aria-hidden="true">◀</span><span class="txt">' + (prev ? esc(fDay(prev.date)) : "Anterior") + "</span></a>" +
        '<div class="tm-date"><div class="eyebrow">Edición nº ' + esc(e.number) + (e.closed_at ? " · cierre " + esc(e.closed_at) + " CET" : "") + "</div><h1>" + esc(fLong(d)) + "</h1></div>" +
        '<a class="navbtn" href="' + (next ? "#e-" + esc(next.date) : "#maquina") + '"' + (next ? "" : ' aria-disabled="true" tabindex="-1"') + ' data-key="next"><span class="txt">' + (next ? esc(fDay(next.date)) : "Siguiente") + '</span><span class="arr" aria-hidden="true">▶</span></a>' +
      "</div>" +
      '<div class="tm-now">' + (d === last ? '<span class="pill live">Última edición</span>' : '<span>Estás viendo una edición de hace ' + plural(diff(d, last), "día", "días") + '.</span> <a href="#e-' + esc(last) + '">Ir a la última (' + esc(fDay(last)) + ")</a>") + '<span class="pill">← → para recorrer las ediciones</span></div>' +
      '<div class="rail-wrap" id="railwrap"><ol class="rail" aria-label="Ediciones publicadas">' + rail + "</ol></div>" +
      '<div class="stack">' +
        (prev2 ? '<button type="button" class="ghost g2" data-go="' + esc(prev2.date) + '"><span>◀ ' + esc(fShort(prev2.date)) + " · nº " + esc(prev2.number) + "</span><span>" + plural((prev2._sum.counts || {}).piezas || 0, "pieza", "piezas") + "</span></button>" : "") +
        (prev ? '<button type="button" class="ghost g1" data-go="' + esc(prev.date) + '"><span>◀ ' + esc(fShort(prev.date)) + " · nº " + esc(prev.number) + "</span><span>" + plural((prev._sum.counts || {}).piezas || 0, "pieza", "piezas") + "</span></button>" : "") +
        '<article class="front' + (dir < 0 ? " in-back" : dir > 0 ? " in-fwd" : "") + '" id="front" aria-label="Portada del ' + esc(fMid(d)) + '">' +
          '<header class="fp-mast"><span class="wm"><span class="m">M</span>OTICIAS</span><span class="ed">Edición nº ' + esc(e.number) + " · " + esc(fLong(d)) + "</span></header>" +
          '<div class="fp-stats"><span><b>' + nf(o.arts.length) + "</b> piezas</span><span><b>" + nf(nWords) + "</b> palabras</span><span><b>" + nf(nSrc) + "</b> fuentes enlazadas</span><span><b>" + nf(bols.length) + "</b> boletines</span><span><b>" + nf(open.length) + "</b> plazos abiertos</span></div>" +
          '<div class="fp-grid"><div class="fp-main">';
    if (lead) {
      html += '<div class="lead"><div><a href="#a-' + esc(lead.id) + '" tabindex="-1" aria-hidden="true">' + imgTag(lead) + "</a>" + credit(lead.image) + "</div>" +
        '<div><div class="kicker" style="--sec:' + secVar(secOf(lead)) + '">Apertura · ' + esc(lead.kicker || "") + '</div><h2><a href="#a-' + esc(lead.id) + '">' + esc(lead.title) + "</a></h2>" +
        (lead.subtitle ? '<p class="dek">' + esc(lead.subtitle) + "</p>" : "") + '<p class="sum">' + esc(lead.summary || "") + "</p>" +
        '<div class="meta"><span>' + esc(lead.author || "Redacción") + "</span>" + (lead.published_time ? "<span>" + esc(lead.published_time) + "</span>" : "") + (lead._words ? "<span>" + Math.max(1, Math.round(lead._words / 210)) + " min de lectura</span>" : "") + "</div></div></div>";
    } else {
      html += '<p class="empty">Esta edición no tiene piezas archivadas.</p>';
    }
    if (o.second || o.ana) {
      html += '<div class="duo">';
      if (o.second) html += '<div class="card"><div class="kicker" style="--sec:' + secVar(secOf(o.second)) + '">' + esc(o.second.kicker || "") + '</div><h3><a href="#a-' + esc(o.second.id) + '">' + esc(o.second.title) + "</a></h3>" + (o.second.subtitle ? '<p class="dek">' + esc(o.second.subtitle) + "</p>" : "") + "</div>";
      if (o.ana) html += '<div class="card ana"><div class="kicker" style="--sec:var(--s-analisis)">Análisis · ' + esc(o.ana.scope || o.ana.kicker || "") + '</div><h3><a href="#a-' + esc(o.ana.id) + '">' + esc(o.ana.title) + "</a></h3><p class=\"sum\">" + esc(o.ana.summary || o.ana.subtitle || "") + '</p><div class="byline"><b>' + esc(o.ana.author || "Redacción") + "</b><span>" + esc(o.ana.author_role || "") + "</span></div></div>";
      html += "</div>";
    }
    if (o.groups.length) {
      html += '<div class="secs">' + o.groups.map(function (g) {
        return '<section style="--sec:' + secVar(g.key) + '"><div class="sec-h"><h3>' + esc(g.name) + "</h3><span>" + plural(g.items.length, "pieza", "piezas") + '</span></div><ul class="its">' + g.items.map(itemLi).join("") + "</ul></section>";
      }).join("") + "</div>";
    }
    html += '</div><aside class="side" aria-label="Documentos, boletines y plazos de la edición">';
    var doc = e.document;
    if (doc && doc.title) {
      var du = safeUrl(doc.url);
      html += '<div class="box"><h4>Documento del día</h4><div class="doc"><div class="ref">' + esc([doc.kicker, doc.ref].filter(Boolean).join(" · ")) + "</div><h5>" + (du ? '<a href="' + esc(du) + '" target="_blank" rel="noopener">' + esc(doc.title) + "</a>" : esc(doc.title)) + "</h5>" + (doc.summary ? "<p>" + esc(doc.summary) + "</p>" : "") + '<p class="credit">' + esc([doc.source, doc.date ? fNum(doc.date) : ""].filter(Boolean).join(" · ")) + "</p></div></div>";
    }
    var tick = (e.ticker || []);
    if (tick.length) {
      html += '<div class="box"><h4>' + esc(e.ticker_label || "Boletines") + ' del día</h4><ul class="tick">' + tick.map(function (t) { return '<li><span class="ref">' + esc(t.ref || "") + "</span>" + linkOrText(t.text, t.url) + "</li>"; }).join("") + "</ul>" +
        (bols.length > tick.length ? '<p class="more-l"><a href="#buscar" data-bols="' + esc(d) + '">Ver los ' + nf(bols.length) + " boletines de esta edición</a></p>" : "") + "</div>";
    } else if (bols.length) {
      html += '<div class="box"><h4>Boletines del día</h4><ul class="tick">' + bols.slice(0, 10).map(function (b) { return '<li><span class="ref">' + esc(b.referencia) + "</span>" + linkOrText(b.titulo_corto || b.titulo, b.url) + "</li>"; }).join("") + "</ul></div>";
    }
    if (open.length) {
      html += '<div class="box"><h4>Plazos abiertos ese día</h4><ul class="ags">' + open.slice(0, 12).map(function (g) {
        return '<li class="ag"><span class="ag-d"><b>' + esc(fDay(g.date)) + "</b><small>" + esc(rel(d, g.date)) + '</small></span><span class="ag-t"><span class="ag-k k-' + esc(g.kind) + '">' + esc(AGK[g.kind] || g.kind || "") + "</span>" + linkOrText(g.title, g.url) + "<small>" + esc([g.authority, g.amount].filter(Boolean).join(" · ")) + "</small></span></li>";
      }).join("") + "</ul>" + (open.length > 12 ? '<p class="more-l">Y ' + plural(open.length - 12, "plazo más", "plazos más") + ' hasta el ' + esc(fMid(open[open.length - 1].date)) + ".</p>" : "") + "</div>";
    }
    var ser = seriesSvg(e.boe_series, d);
    if (ser) {
      html += '<div class="box chart"><h4>El BOE, día a día</h4>' + ser + '<div class="legend"><span><i style="background:var(--bar-lic)"></i>Licitaciones y formalizaciones</span><span><i style="background:var(--bar-disp)"></i>Disposiciones y resoluciones</span></div>' +
        (e.boe_range ? '<p class="credit">Referencias de transporte de viajeros barridas en la edición · ' + esc(fNum(e.boe_range[0])) + " a " + esc(fNum(e.boe_range[1])) + "</p>" : "") + "</div>";
    }
    html += "</aside></div>";
    if (e.note_metodologica) html += '<details class="fp-note"><summary>Nota metodológica</summary><p>' + esc(e.note_metodologica) + "</p></details>";
    html += '<div class="fp-end"><span>Fin de edición · ' + esc(fLong(d)) + (e.closed_at ? " · " + esc(e.closed_at) + " CET" : "") + "</span><span>" + (prev ? '<a href="#e-' + esc(prev.date) + '">◀ Edición anterior</a>' : "Primera edición archivada") + "</span></div>";
    html += "</article></div></section>";
    $("#main").innerHTML = html;
    var cur = $(".st[aria-current]"), rw = $("#railwrap");
    if (cur && rw && rw.scrollWidth > rw.clientWidth) rw.scrollLeft = cur.offsetLeft - rw.clientWidth / 2 + cur.offsetWidth / 2;
    $$(".ghost").forEach(function (b) { b.addEventListener("click", function () { location.hash = "e-" + b.getAttribute("data-go"); }); });
    $$("[data-bols]").forEach(function (a) { a.addEventListener("click", function () { S.q = ""; $("#q").value = ""; S.f = { type: "boletines", amb: "", from: d, to: d, sort: "rel" }; S.shown = 60; }); });
  }

  /* ---------- Lector ---------- */
  function markIn(root, re) {
    if (!root || !re) return 0;
    var tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null), nodes = [], n, found = 0;
    while ((n = tw.nextNode())) { if (n.parentNode && !/^(MARK|SCRIPT|STYLE)$/.test(n.parentNode.nodeName)) nodes.push(n); }
    nodes.forEach(function (node) {
      var text = node.nodeValue; re.lastIndex = 0;
      if (!re.test(text)) return;
      var span = document.createElement("span"); span.innerHTML = hl(text, re);
      found += span.querySelectorAll("mark").length;
      var frag = document.createDocumentFragment(); while (span.firstChild) frag.appendChild(span.firstChild);
      node.parentNode.replaceChild(frag, node);
    });
    return found;
  }
  function renderReader(id) {
    var a = S.art[id]; if (!a) return;
    var e = S.ed[a.date], o = edOrder(a.date), pos = o.flat.indexOf(a), pv = o.flat[pos - 1], nx = o.flat[pos + 1];
    var sec = secOf(a), isAna = a.kind === "analisis";
    var P = S.fromSearch && S.q ? parseQ(S.q) : null, re = P ? hlRe(P.terms) : null;
    var html = '<article class="reader wrap" style="--sec:' + secVar(sec) + '">';
    html += '<nav class="crumbs" aria-label="Navegación">' + (e ? '<a href="#e-' + esc(a.date) + '">◀ Edición nº ' + esc(e.number) + " · " + esc(fShort(a.date)) + "</a>" : "") + (S.fromSearch ? '<a href="#buscar">◀ Volver a los resultados</a>' : "") + '<span id="hits" class="mono" hidden></span></nav>';
    html += '<header class="r-head"><div class="kicker">' + esc(a.kicker || KIND[a.kind] || "") + "</div><h1>" + esc(a.title) + "</h1>" + (a.subtitle ? '<p class="dek">' + esc(a.subtitle) + "</p>" : "") +
      '<div class="meta"><span>' + esc(a.author || "Redacción") + (a.author_role ? ", " + esc(a.author_role) : "") + "</span><span>" + esc(fLong(a.date)) + (a.published_time ? " · " + esc(a.published_time) : "") + "</span>" + (a._words ? "<span>" + nf(a._words) + " palabras · " + Math.max(1, Math.round(a._words / 210)) + " min</span>" : "") + (SEC[sec] ? "<span>" + esc(SEC[sec]) + "</span>" : "") + "</div></header>";
    html += '<div class="r-fig">' + imgTag(a) + credit(a.image) + "</div>";
    html += '<div class="r-grid"><div class="r-body" id="rbody">' + (a.body_md ? md(a.body_md) : '<p class="lede">' + esc(a.summary || "") + "</p>");
    if (!isAna) {
      var Q = [["De qué trata", a.summary], ["Protagonistas", a.actors], ["Para quién es relevante", a.relevance_for], ["Por qué importa", a.why], ["Qué puede pasar ahora", a.next]].filter(function (x) { return x[1]; });
      if (Q.length) html += '<section class="quick"><h2>Guía rápida</h2><div class="q-grid">' + Q.map(function (x) { return "<div><h3>" + x[0] + "</h3><p>" + esc(x[1]) + "</p></div>"; }).join("") + "</div></section>";
    }
    var srcs = (a.sources || []).slice().sort(function (x, y) { return (x.kind === "oficial" ? 0 : 1) - (y.kind === "oficial" ? 0 : 1); });
    if (srcs.length) {
      html += '<section class="srcs"><h2>Para saber más · ' + plural(srcs.length, "fuente", "fuentes") + "</h2><ol>" + srcs.map(function (s) {
        var u = safeUrl(s.url);
        return '<li><span class="kd-badge' + (s.kind === "oficial" ? " of" : "") + '">' + (s.kind === "oficial" ? "Oficial" : "Medios") + "</span><span><b>" + esc(s.outlet || "") + "</b> · " + (u ? '<a href="' + esc(u) + '" target="_blank" rel="noopener">' + esc(s.title || u) + "</a>" : esc(s.title || "")) + '</span><span class="dt">' + (s.published ? "Publicada " + esc(fNum(s.published) || s.published) : "Sin fecha publicada") + (s.accessed ? " · consultada " + esc(fNum(s.accessed)) : "") + "</span></li>";
      }).join("") + "</ol></section>";
    }
    html += "</div>";
    html += '<aside class="r-aside">';
    html += '<div class="box trace"><h4>Trazabilidad</h4><dl>' +
      (a.event_date ? "<div><dt>Fecha de los hechos</dt><dd>" + esc(fMid(a.event_date)) + "</dd></div>" : "") +
      "<div><dt>Publicada</dt><dd>" + esc(fMid(a.date)) + (a.published_time ? ", " + esc(a.published_time) : "") + "</dd></div>" +
      (a.revised_at ? "<div><dt>Revisada</dt><dd>" + esc(fMid(a.revised_at)) + (hhmm(a.revised_at) ? ", " + esc(hhmm(a.revised_at)) : "") + "</dd></div>" : "") +
      (e ? "<div><dt>Edición</dt><dd>nº " + esc(e.number) + (e.closed_at ? ", cierre " + esc(e.closed_at) + " CET" : "") + "</dd></div>" : "") +
      (a.doc_ref ? "<div><dt>Referencia</dt><dd class=\"mono\">" + esc(a.doc_ref) + "</dd></div>" : "") +
      (a.authority ? "<div><dt>Órgano</dt><dd>" + esc(a.authority) + "</dd></div>" : "") +
      "</dl></div>";
    if (isAna && a.author_note) html += '<div class="author"><b>' + esc(a.author || "") + "</b>" + esc(a.author_role || "") + '<p style="margin:6px 0 0">' + esc(a.author_note) + "</p></div>";
    if (a.key_fact) html += '<div class="box"><h4>Dato clave</h4><div class="keyfact">' + esc(a.key_fact) + "</div></div>";
    if ((a.key_data || []).length) html += '<div class="box"><h4>Cifras clave</h4><dl class="kd">' + a.key_data.map(function (k) { return "<div><dt>" + esc(k.label) + "</dt><dd><b>" + esc(k.value) + "</b>" + (k.source ? "<small>" + esc(k.source) + "</small>" : "") + "</dd></div>"; }).join("") + "</dl></div>";
    if ((a.timeline || []).length) {
      var tl = a.timeline.slice().sort(function (x, y) { return String(x.date).localeCompare(String(y.date)); });
      html += '<div class="box"><h4>Cronología</h4><ol class="tl">' + tl.map(function (t) { var fut = String(t.date) > a.date; return '<li class="' + (fut ? "fut" : "") + '"><time datetime="' + esc(t.date) + '">' + esc(/^\d{4}-\d{2}$/.test(t.date) ? fShort(t.date) : fMid(t.date)) + (fut ? " · previsto" : "") + "</time>" + esc(t.text) + "</li>"; }).join("") + "</ol></div>";
    }
    if ((a.tags || []).length) html += '<div class="box"><h4>Etiquetas</h4><div class="tags">' + a.tags.map(function (t) { return '<button type="button" class="tag" data-tag="' + esc(t) + '">' + esc(t) + "</button>"; }).join("") + "</div></div>";
    html += "</aside></div>";
    if (pv || nx) html += '<nav class="r-pn" aria-label="Piezas de la misma edición">' + (pv ? '<a href="#a-' + esc(pv.id) + '"><small>◀ Anterior en la edición</small><span>' + esc(pv.title) + "</span></a>" : "<span></span>") + (nx ? '<a href="#a-' + esc(nx.id) + '"><small>Siguiente en la edición ▶</small><span>' + esc(nx.title) + "</span></a>" : "<span></span>") + "</nav>";
    html += "</article>";
    $("#main").innerHTML = html;
    if (re) {
      var nHits = markIn($("#rbody"), re) + markIn($(".r-head"), re);
      var hb = $("#hits");
      if (nHits && hb) { hb.hidden = false; hb.innerHTML = plural(nHits, "coincidencia", "coincidencias") + ' · <button type="button" class="linkbtn" id="gohit">Ir a la primera</button>'; $("#gohit").addEventListener("click", function () { var mk = $("#main mark"); if (mk) mk.scrollIntoView({ block: "center" }); }); }
    }
    $$(".tag").forEach(function (b) { b.addEventListener("click", function () { var t = b.getAttribute("data-tag"); S.q = /\s/.test(t) ? '"' + t + '"' : t; $("#q").value = S.q; S.f.type = "todo"; S.shown = 30; location.hash = "buscar"; }); });
  }

  /* ---------- Búsqueda ---------- */
  function runSearch() {
    var P = parseQ(S.q), f = S.f, res = [];
    S.items.forEach(function (it) {
      if (f.type === "noticias" && !(it.type === "noticia" || it.type === "reportaje")) return;
      if (f.type === "analisis" && it.type !== "analisis") return;
      if (f.type === "boletines" && it.type !== "boletin") return;
      if (f.type === "plazos" && it.type !== "plazo") return;
      if (!inAmbito(it, f.amb)) return;
      if (f.from && it.date < f.from) return;
      if (f.to && it.date > f.to) return;
      var score = 0, k, ok = true;
      for (var i = 0; i < P.terms.length && ok; i++) {
        var s = 0; for (k in it.f) s += cnt(it.f[k], P.terms[i]) * (W[k] || 1);
        if (!s) ok = false; else score += s;
      }
      if (!ok) return;
      for (var j = 0; j < P.neg.length; j++) { for (k in it.f) { if (it.f[k].indexOf(P.neg[j]) > -1) return; } }
      res.push({ it: it, score: score });
    });
    var byRel = f.sort !== "fecha" && P.terms.length;
    res.sort(function (a, b) {
      return (byRel ? b.score - a.score : 0) || String(b.it.date).localeCompare(String(a.it.date)) || typeRank(a.it) - typeRank(b.it) ||
        String(b.it.ref.published_at || b.it.ref.fecha || "").localeCompare(String(a.it.ref.published_at || a.it.ref.fecha || ""));
    });
    return { res: res, P: P };
  }
  function resItem(r, re) {
    var it = r.it, x = it.ref;
    if (it.type === "boletin") {
      return '<li class="res"><div class="res-meta"><span class="badge b-bol">BOE</span><span>' + esc(x.referencia || "") + "</span><span>" + esc(fShort(x.fecha)) + "</span>" + edTag(it.date) + "</div><h3>" + linkOrText(x.titulo_corto || x.titulo, x.url, re) + "</h3>" + (x.nota ? '<p class="snip">' + hl(x.nota, re) + "</p>" : "") + '<p class="kick">' + esc([x.organo, x.tipo].filter(Boolean).join(" · ")) + "</p></li>";
    }
    if (it.type === "plazo") {
      return '<li class="res"><div class="res-meta"><span class="badge b-pla">' + esc(AGK[x.kind] || "Plazo") + "</span><span>" + esc(fLong(x.date)) + "</span>" + (x.edicion ? "<span>anotado en la</span>" + edTag(x.edicion) : "") + "</div><h3>" + linkOrText(x.title, x.url, re) + "</h3>" + '<p class="kick">' + esc([x.authority, x.amount].filter(Boolean).join(" · ")) + "</p></li>";
    }
    var sn = re ? (snippet(x._plain, re) || snippet(x.summary, re) || esc(x.summary || "")) : esc(x.summary || "");
    var sec = secOf(x);
    return '<li class="res" style="--sec:' + secVar(sec) + '"><div class="res-meta"><span class="badge">' + esc(KIND[x.kind] || "Noticia") + "</span>" + (SEC[x.section] && x.kind !== "analisis" ? '<span class="sec">' + esc(SEC[x.section]) + "</span>" : "") + "<span>" + esc(fShort(x.date)) + "</span>" + edTag(x.date) + "</div>" +
      '<h3><a href="#a-' + esc(x.id) + '" data-fs="1">' + hl(x.title, re) + "</a></h3>" + (x.kicker ? '<p class="kick">' + hl(x.kicker, re) + "</p>" : "") + '<p class="snip">' + sn + "</p></li>";
  }
  function renderSearch() {
    var eds = S.eds.slice().reverse();
    var opt = function (sel) { return '<option value="">Todas</option>' + eds.map(function (e) { return '<option value="' + esc(e.date) + '"' + (sel === e.date ? " selected" : "") + ">" + esc(fShort(e.date)) + " · nº " + esc(e.number) + "</option>"; }).join(""); };
    var types = [["todo", "Todo"], ["noticias", "Noticias"], ["analisis", "Análisis"], ["boletines", "Boletines BOE"], ["plazos", "Plazos"]];
    var ambs = [["", "Todos"], ["tierra", "Tierra"], ["mar", "Mar"], ["aire", "Aire"], ["regulacion", "Regulación"], ["licitaciones", "Licitaciones"], ["logistica", "Logística"], ["analisis", "Análisis"]];
    var html = '<section class="search wrap" aria-label="Búsqueda"><div class="s-head"><h1>Buscar en la hemeroteca</h1><p class="s-sum" id="ssum"></p></div>' +
      '<form class="s-filters" id="sf"><fieldset class="seg"><legend class="vh">Tipo</legend>' + types.map(function (t) { return '<label><input type="radio" name="type" id="ft-' + t[0] + '" value="' + t[0] + '"' + (S.f.type === t[0] ? " checked" : "") + "><span>" + t[1] + "</span></label>"; }).join("") + "</fieldset>" +
      '<label class="fld" for="f-amb">Ámbito<select id="f-amb">' + ambs.map(function (a) { return '<option value="' + a[0] + '"' + (S.f.amb === a[0] ? " selected" : "") + ">" + a[1] + "</option>"; }).join("") + "</select></label>" +
      '<label class="fld" for="f-from">Desde<select id="f-from">' + opt(S.f.from) + "</select></label>" +
      '<label class="fld" for="f-to">Hasta<select id="f-to">' + opt(S.f.to) + "</select></label>" +
      '<label class="fld" for="f-sort">Orden<select id="f-sort"><option value="rel"' + (S.f.sort === "rel" ? " selected" : "") + '>Relevancia</option><option value="fecha"' + (S.f.sort === "fecha" ? " selected" : "") + ">Más reciente</option></select></label>" +
      '<button type="button" class="linkbtn" id="f-clear">Limpiar filtros</button></form>' +
      (S.tags.length ? '<div class="s-tags"><span>Etiquetas frecuentes:</span>' + S.tags.map(function (t) { return '<button type="button" class="tag" data-tag="' + esc(t.t) + '">' + esc(t.t) + "</button>"; }).join("") + "</div>" : "") +
      '<ol class="results" id="results"></ol><div class="more" id="more"></div></section>';
    $("#main").innerHTML = html;
    var sf = $("#sf");
    sf.addEventListener("change", function () {
      var r = sf.querySelector("input[name=type]:checked");
      S.f = { type: r ? r.value : "todo", amb: $("#f-amb").value, from: $("#f-from").value, to: $("#f-to").value, sort: $("#f-sort").value };
      S.shown = 30; renderResults();
    });
    $("#f-clear").addEventListener("click", function () { S.f = { type: "todo", amb: "", from: "", to: "", sort: "rel" }; S.shown = 30; renderSearch(); });
    $$(".s-tags .tag").forEach(function (b) { b.addEventListener("click", function () { var t = b.getAttribute("data-tag"); S.q = /\s/.test(t) ? '"' + t + '"' : t; $("#q").value = S.q; S.shown = 30; renderResults(); }); });
    renderResults();
  }
  function renderResults() {
    var box = $("#results"); if (!box) return;
    var out = runSearch(), res = out.res, P = out.P, re = hlRe(P.terms);
    var c = { pieza: 0, boletin: 0, plazo: 0 };
    res.forEach(function (r) { c[r.it.type === "boletin" ? "boletin" : r.it.type === "plazo" ? "plazo" : "pieza"]++; });
    var q = S.q.trim();
    $("#ssum").innerHTML = (q ? "<b>" + plural(res.length, "resultado", "resultados") + "</b> para «" + esc(q) + "»" : "<b>" + plural(res.length, "elemento", "elementos") + "</b> archivados") +
      (res.length ? " · " + [c.pieza ? plural(c.pieza, "pieza", "piezas") : "", c.boletin ? plural(c.boletin, "boletín", "boletines") : "", c.plazo ? plural(c.plazo, "plazo", "plazos") : ""].filter(Boolean).join(" · ") : "");
    if (!res.length) {
      box.innerHTML = '<li class="empty">' + (q ? "Ninguna pieza, boletín o plazo contiene <b>" + esc(q) + "</b> con estos filtros. Prueba sin acentos, con menos palabras o con <b>Limpiar filtros</b>." : "No hay elementos con estos filtros.") + "</li>";
      $("#more").innerHTML = ""; return;
    }
    box.innerHTML = res.slice(0, S.shown).map(function (r) { return resItem(r, re); }).join("");
    $$("[data-fs]", box).forEach(function (a) { a.addEventListener("click", function () { S.fromSearch = true; }); });
    var left = res.length - S.shown;
    $("#more").innerHTML = left > 0 ? '<button type="button" class="btn" id="morebtn">Mostrar ' + nf(Math.min(30, left)) + " más (quedan " + nf(left) + ")</button>" : "";
    var mb = $("#morebtn"); if (mb) mb.addEventListener("click", function () { S.shown += 30; renderResults(); });
  }

  /* ---------- Descargas ---------- */
  function buildHtml() {
    var get = function (u) { return fetch(u, { cache: "no-store" }).then(function (r) { if (!r.ok) throw new Error(u); return r.text(); }); };
    return Promise.all([get("app.css"), get("app.js")]).then(function (p) {
      var data = JSON.stringify(S.raw).replace(/</g, "\\u003c").replace(/\u2028/g, "\\u2028").replace(/\u2029/g, "\\u2029");
      return "<!doctype html>\n<html lang=\"es\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\"><title>Hemeroteca MOTICIAS</title>" +
        '<link rel="stylesheet" href="' + FONTS.replace(/&/g, "&amp;") + '"><style>' + p[0] + '</style></head><body><div id="app"></div><script>window.__HEMEROTECA__=' + data + ";<\/script><script>" + p[1].replace(/<\/script/gi, "<\\/script") + "<\/script></body></html>\n";
    });
  }
  function doDownload(kind) {
    var det = $("#dl"); if (det) det.open = false;
    if (!S.dl) { toast("La descarga no está disponible en esta vista."); return; }
    var last = latest() || "";
    var job = kind === "json" ? Promise.resolve({ filename: "moticias-hemeroteca-datos-" + last + ".json", data: new Blob([JSON.stringify(S.raw)], { type: "application/json" }) })
      : buildHtml().then(function (html) { return { filename: "moticias-hemeroteca-" + last + ".html", data: new Blob([html], { type: "text/html" }) }; });
    job.then(function (req) { return S.dl.save(req); }).then(function () { toast("Archivo entregado al navegador."); }).catch(function (err) {
      var code = err && err.code;
      if (code === "declined") toast("Descarga cancelada.");
      else if (code === "rate_limited") toast("Ya hay una descarga pendiente de confirmar.");
      else if (code === "unavailable" || code === "not_granted" || code === "capability_disabled" || code === "capability_removed") { toast("La descarga no está disponible en esta vista."); if (det) det.hidden = true; }
      else toast("No se pudo preparar el archivo" + (err && err.message ? ": " + err.message : "."));
    });
  }
  function setupDownloads() {
    if (S.standalone || !window.claude || typeof window.claude.use !== "function") return;
    window.claude.use("downloads").then(function (d) { S.dl = d; var det = $("#dl"); if (d && det) det.hidden = false; }).catch(function () { S.dl = null; });
  }

  /* ---------- Rutas y teclado ---------- */
  function route() {
    var h = decodeURIComponent(location.hash.replace(/^#/, "")), prevView = S.view, prevCur = S.cur;
    if (h.indexOf("a-") === 0 && S.art[h.slice(2)]) {
      S.view = "lector"; renderReader(h.slice(2)); window.scrollTo(0, 0);
    } else if (h === "buscar") {
      if (prevView !== "buscar") { S.view = "buscar"; renderSearch(); window.scrollTo(0, 0); } else renderResults();
      S.fromSearch = false;
    } else {
      var d = h.indexOf("e-") === 0 && S.ed[h.slice(2)] ? h.slice(2) : latest();
      var dir = prevView === "maquina" && prevCur && S.ed[prevCur] && S.ed[d] ? Math.sign(S.ed[d]._i - S.ed[prevCur]._i) : 0;
      S.view = "maquina"; S.fromSearch = false; renderMachine(d, dir);
      if (prevView !== "maquina") window.scrollTo(0, 0);
    }
    setTabs();
  }
  function onKey(e) {
    var tag = (e.target && e.target.tagName) || "";
    var typing = /INPUT|SELECT|TEXTAREA/.test(tag) || (e.target && e.target.isContentEditable);
    if (e.key === "/" && !typing) { e.preventDefault(); var q = $("#q"); q.focus(); q.select(); return; }
    if (e.key === "Escape" && tag === "INPUT" && e.target.id === "q") { e.target.value = ""; S.q = ""; if (S.view === "buscar") renderResults(); return; }
    if (typing || e.metaKey || e.ctrlKey || e.altKey || S.view !== "maquina") return;
    var e0 = S.ed[S.cur]; if (!e0) return;
    if (e.key === "ArrowLeft" && S.eds[e0._i - 1]) { e.preventDefault(); location.hash = "e-" + S.eds[e0._i - 1].date; }
    if (e.key === "ArrowRight" && S.eds[e0._i + 1]) { e.preventDefault(); location.hash = "e-" + S.eds[e0._i + 1].date; }
  }

  /* ---------- Arranque ---------- */
  function fail(msg) { var app = $("#app"); if (app) app.innerHTML = '<div class="boot"><div class="boot-wm"><span class="m">M</span>OTICIAS</div><div class="boot-sub">Hemeroteca</div><p class="boot-msg">' + esc(msg) + "</p></div>"; }
  function start(raw) {
    ingest(raw);
    if (!S.eds.length) { fail("Todavía no hay ediciones archivadas."); return; }
    shell();
    document.addEventListener("error", function (ev) {
      var t = ev.target;
      if (t && t.tagName === "IMG" && !t.getAttribute("data-fb")) { t.setAttribute("data-fb", "1"); t.src = artSvg(t.getAttribute("data-sec"), t.getAttribute("data-seed")); }
    }, true);
    window.addEventListener("hashchange", route);
    document.addEventListener("keydown", onKey);
    route();
    setupDownloads();
  }
  function boot() {
    if (window.__HEMEROTECA__) { S.standalone = true; start(window.__HEMEROTECA__); return; }
    fetch("data/index.json", { cache: "no-store" }).then(function (r) { if (!r.ok) throw new Error("índice"); return r.json(); }).then(function (idx) {
      return Promise.all((idx.chunks || []).map(function (c) { return fetch(c, { cache: "no-store" }).then(function (r) { if (!r.ok) throw new Error(c); return r.json(); }); })).then(function (chunks) { start({ index: idx, chunks: chunks }); });
    }).catch(function (err) { fail("No se pudieron cargar las ediciones (" + (err && err.message ? err.message : "error") + "). Vuelve a abrir la página."); });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
