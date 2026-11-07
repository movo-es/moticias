/* MOTICIAS — aplicación de portada, secciones, artículo y administración.
   Datos: base de datos del artefacto (colecciones articles, boletines, agenda, editions; documento settings/site).
   Sin dependencias externas. */
(function () {
  "use strict";

  // ---------- Utilidades ----------
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const SECTION_NAMES = { tierra: "Tierra", mar: "Mar", aire: "Aire", logistica: "Logística", regulacion: "Regulación", licitaciones: "Licitaciones", analisis: "Análisis", tecnologia: "Tecnología", transversal: "Transversal" };
  const MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  const MONTHS_S = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  const DAYS = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];

  function parseDate(s) {
    if (!s) return null;
    const m = String(s).match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!m) { const d = new Date(s); return isNaN(d) ? null : d; }
    return new Date(Date.UTC(+m[1], +m[2] - 1, +m[3], 12));
  }
  function fmtLong(s) { const d = parseDate(s); if (!d) return ""; return `${DAYS[d.getUTCDay()]}, ${d.getUTCDate()} de ${MONTHS[d.getUTCMonth()]} de ${d.getUTCFullYear()}`; }
  function fmtMid(s) { const d = parseDate(s); if (!d) return ""; return `${d.getUTCDate()} de ${MONTHS[d.getUTCMonth()]} de ${d.getUTCFullYear()}`; }
  function fmtShort(s) { const d = parseDate(s); if (!d) return ""; return `${d.getUTCDate()} ${MONTHS_S[d.getUTCMonth()]} ${d.getUTCFullYear()}`; }
  function fmtNum(s) { const d = parseDate(s); if (!d) return ""; return `${String(d.getUTCDate()).padStart(2, "0")}.${String(d.getUTCMonth() + 1).padStart(2, "0")}.${d.getUTCFullYear()}`; }
  function todayISO() { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; }
  function daysUntil(s) { const d = parseDate(s); if (!d) return null; const t = parseDate(todayISO()); return Math.round((d - t) / 86400000); }
  function slugify(s) {
    return String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 80) || ("pieza-" + Date.now().toString(36));
  }
  function readingTime(text) { const w = String(text || "").trim().split(/\s+/).length; return Math.max(1, Math.round(w / 210)); }
  function imgSrc(a) { const im = a && a.image; if (!im) return ""; if (im.src) return im.src; if (im.assetId) return "/_blob/" + im.assetId; return ""; }
  function creditText(im) { if (!im) return ""; const parts = []; if (im.credit) parts.push(im.credit); if (im.license) parts.push(im.license); return parts.join(" · "); }
  function safeUrl(u) { u = String(u || "").trim(); return /^https?:\/\//i.test(u) ? u : ""; }
  function host(u) { try { return new URL(u).hostname.replace(/^www\./, ""); } catch (e) { return ""; } }

  // Marcado ligero: escapa HTML y aplica un subconjunto de Markdown.
  function md(src) {
    const lines = String(src || "").replace(/\r/g, "").split("\n");
    let html = "", para = [], list = null, first = true;
    const inline = (t) => esc(t)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
      .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    const flushPara = () => { if (para.length) { const cls = first ? ' class="lede"' : ""; html += `<p${cls}>${inline(para.join(" "))}</p>`; para = []; first = false; } };
    const flushList = () => { if (list) { html += `<${list.type}>${list.items.map((i) => `<li>${inline(i)}</li>`).join("")}</${list.type}>`; list = null; } };
    for (const raw of lines) {
      const line = raw.trimEnd();
      if (!line.trim()) { flushPara(); flushList(); continue; }
      let m;
      if ((m = line.match(/^(#{1,3})\s+(.*)$/))) { flushPara(); flushList(); const lvl = m[1].length + 1; html += `<h${lvl}>${inline(m[2])}</h${lvl}>`; continue; }
      if (line.startsWith(">>")) { flushPara(); flushList(); html += `<div class="pull">${inline(line.slice(2).trim())}</div>`; continue; }
      if (line.startsWith(">")) { flushPara(); flushList(); html += `<blockquote>${inline(line.slice(1).trim())}</blockquote>`; continue; }
      if (/^(-{3,}|\*{3,})$/.test(line)) { flushPara(); flushList(); html += "<hr>"; continue; }
      if ((m = line.match(/^[-*]\s+(.*)$/))) { flushPara(); if (!list || list.type !== "ul") { flushList(); list = { type: "ul", items: [] }; } list.items.push(m[1]); continue; }
      if ((m = line.match(/^\d+[.)]\s+(.*)$/))) { flushPara(); if (!list || list.type !== "ol") { flushList(); list = { type: "ol", items: [] }; } list.items.push(m[1]); continue; }
      flushList(); para.push(line.trim());
    }
    flushPara(); flushList();
    return html;
  }

  // Ilustración de respaldo cuando una pieza no tiene foto.
  function artSvg(section, seed) {
    const col = { tierra: "#4f6f3a", mar: "#1c5d74", aire: "#2e63a8", regulacion: "#4a3f7a", licitaciones: "#b0621c", analisis: "#7a1f2b", logistica: "#7a6a2a", tecnologia: "#0e7c86" }[section] || "#0f1f33";
    let h = 0; for (const c of String(seed || "m")) h = (h * 31 + c.charCodeAt(0)) >>> 0;
    const lines = [];
    for (let i = 0; i < 14; i++) { const y = 20 + i * 22 + ((h >> (i % 7)) % 9); lines.push(`<path d="M-20 ${y} Q 300 ${y - 40 - (h % 30)} 620 ${y + 10}" stroke="rgba(255,255,255,.${(i % 3) + 1}5)" stroke-width="${1 + (i % 3)}" fill="none"/>`); }
    const letter = (SECTION_NAMES[section] || "M").charAt(0);
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400"><rect width="600" height="400" fill="${col}"/>${lines.join("")}<text x="40" y="360" font-family="Georgia,serif" font-size="260" fill="rgba(255,255,255,.14)" font-weight="700">${letter}</text></svg>`;
    return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
  }

  function toast(msg, err) { const t = $("#toast"); t.textContent = msg; t.className = "toast show" + (err ? " err" : ""); clearTimeout(toast._t); toast._t = setTimeout(() => (t.className = "toast"), 3200); }

  // ---------- Estado ----------
  const S = {
    db: null, user: null, assets: null, canEdit: false, isOwner: false,
    articles: [], boletines: [], agenda: [], edition: null, settings: null, sources: null, blogs: [], ads: [], solutions: [], pageImgs: new Set(),
    loaded: { articles: false, boletines: false, agenda: false, editions: false },
    offline: false, timer: null, unsubs: [], route: "portada", adminTab: "piezas", adminFilter: { q: "", kind: "", status: "", section: "" },
  };
  const published = () => S.articles.filter((a) => a.status !== "borrador" && a.kind !== "blog");
  const isLong = (a) => a.kind === "analisis" || a.kind === "reportaje";
  const bySection = (sec) => published().filter((a) => a.section === sec && !isLong(a));
  const analyses = () => published().filter((a) => isLong(a));
  const reportajes = () => published().filter((a) => a.kind === "reportaje");
  const news = () => published().filter((a) => !isLong(a));
  const sortByDate = (arr) => arr.slice().sort((a, b) => String(b.published_at || b.date || "").localeCompare(String(a.published_at || a.date || "")));
  const relRank = (a) => (a.featured === 1 ? 0 : a.featured === 2 ? 1 : a.relevance === "ALTA" ? 2 : 3);
  const sortByRank = (arr) => arr.slice().sort((a, b) => relRank(a) - relRank(b) || String(b.published_at || b.date || "").localeCompare(String(a.published_at || a.date || "")));

  // ---------- Arranque ----------
  async function init() {
    window.addEventListener("hashchange", route);
    setupReveal();
    setupAdminShell();
    route();
    try {
      const useCap = window.claude && typeof window.claude.use === "function" ? (n) => window.claude.use(n) : () => Promise.resolve(null);
      const [db, user] = await Promise.all([useCap("db"), useCap("user")]);
      S.db = db; S.user = user;
      if (user) {
        try { S.isOwner = !!(await user.isOwner()); } catch (e) { S.isOwner = false; }
        try { S.canEdit = !!(await user.canEdit()) || S.isOwner; } catch (e) { S.canEdit = S.isOwner; }
      }
      if (S.canEdit) { S.assets = await useCap("assets"); showAdminControls(); }
      if (!db) { await loadFallback("La base de datos no está disponible en esta vista; se muestra la última edición guardada."); return; }
      subscribeAll();
    } catch (e) {
      console.error(e);
      await loadFallback("No se pudo conectar con la base de datos; se muestra la última edición guardada.");
    }
  }

  // Contenido de fondo publicado con la página (data/fallback.json): se fusiona con la base
  // cuando su revisión (deep_rev) es más reciente que la del documento guardado.
  const DEEP_FIELDS = ["image", "body_md", "key_data", "timeline", "sources", "title", "subtitle", "summary", "actors", "relevance_for", "why", "next", "key_fact", "deep_rev", "revised_at", "published_at", "published_time"];
  function mergeDeep(a) {
    const f = S.deep && S.deep[a.id];
    if (!f || (f.deep_rev || 0) <= (a.deep_rev || 0)) return a;
    const out = Object.assign({}, a);
    DEEP_FIELDS.forEach((k) => { if (f[k] != null && f[k] !== "" && !(Array.isArray(f[k]) && !f[k].length)) out[k] = f[k]; });
    return out;
  }
  const SOL_DEEP = ["body_md", "deployments", "sources", "url", "tags", "provider_country", "verified_at", "summary", "deep_rev"];
  function mergeSol(x) {
    const f = S.deepSol && S.deepSol[x.id];
    if (!f || (f.deep_rev || 0) <= (x.deep_rev || 0)) return x;
    const out = Object.assign({}, x); SOL_DEEP.forEach((k) => { if (f[k] != null && f[k] !== "") out[k] = f[k]; }); return out;
  }
  function loadDeep() {
    return fetch("data/fallback.json", { cache: "no-store" }).then((r) => (r.ok ? r.json() : null)).then((d) => {
      S.deep = {}; ((d && d.articles) || []).forEach((a) => { if (a.deep_rev) S.deep[a.id] = a; });
      S.deepSol = {}; ((d && d.soluciones) || []).forEach((x) => { if (x.deep_rev) S.deepSol[x.id] = x; });
      if (S.rawArticles) { S.articles = S.rawArticles.map(mergeDeep); }
      if (S.rawSolutions) { S.solutions = S.rawSolutions.map(mergeSol); }
      render();
    }).catch(() => { S.deep = {}; });
  }
  function subscribeAll() {
    const db = S.db;
    loadDeep();
    S.timer = setTimeout(() => { if (!S.loaded.articles) { $("#main").innerHTML = `<div class="wrap" style="padding:60px 0"><div class="empty">La edición tarda en llegar. <b>Comprueba la conexión</b> o vuelve a abrir la página.</div></div>`; } }, 10000);
    const onErr = (where) => (e) => { console.error(where, e); if (!S.loaded.articles) loadFallback("Error al leer la base de datos; se muestra la última edición guardada."); };
    S.unsubs.push(db.collection("articles").orderBy("published_at", "desc").limit(500).onSnapshot((snap) => {
      S.rawArticles = snap.docs.map((d) => Object.assign({ id: d.id }, d.data()));
      S.articles = S.rawArticles.map(mergeDeep);
      S.loaded.articles = true; clearTimeout(S.timer); render();
    }, onErr("articles")));
    S.unsubs.push(db.collection("boletines").orderBy("fecha", "desc").limit(800).onSnapshot((snap) => {
      S.boletines = snap.docs.map((d) => Object.assign({ id: d.id }, d.data())); S.loaded.boletines = true; render();
    }, onErr("boletines")));
    S.unsubs.push(db.collection("agenda").orderBy("date", "asc").limit(400).onSnapshot((snap) => {
      S.agenda = snap.docs.map((d) => Object.assign({ id: d.id }, d.data())); S.loaded.agenda = true; render();
    }, onErr("agenda")));
    S.unsubs.push(db.collection("editions").orderBy("date", "desc").limit(1).onSnapshot((snap) => {
      S.edition = snap.docs.length ? Object.assign({ id: snap.docs[0].id }, snap.docs[0].data()) : null; S.loaded.editions = true; render();
    }, onErr("editions")));
    S.unsubs.push(db.collection("blogs").orderBy("name", "asc").limit(200).onSnapshot((snap) => { S.blogs = snap.docs.map((d) => Object.assign({ id: d.id }, d.data())); render(); }, (e) => console.error("blogs", e)));
    S.unsubs.push(db.collection("ads").orderBy("start", "desc").limit(300).onSnapshot((snap) => { S.ads = snap.docs.map((d) => Object.assign({ id: d.id }, d.data())); render(); }, (e) => console.error("ads", e)));
    S.unsubs.push(db.collection("soluciones").orderBy("priority", "asc").limit(300).onSnapshot((snap) => { S.rawSolutions = snap.docs.map((d) => Object.assign({ id: d.id }, d.data())); S.solutions = S.rawSolutions.map(mergeSol); render(); }, (e) => console.error("soluciones", e)));
    S.unsubs.push(db.doc("settings/site").onSnapshot((snap) => { S.settings = snap.exists ? snap.data() : null; render(); }, onErr("settings")));
  }

  async function loadFallback(msg) {
    try {
      const r = await fetch("data/fallback.json", { cache: "no-store" });
      if (!r.ok) throw new Error("sin copia local");
      const d = await r.json();
      S.articles = d.articles || []; S.boletines = d.boletines || []; S.agenda = d.agenda || []; S.edition = d.edition || null; S.settings = d.settings || null; S.blogs = d.blogs || []; S.ads = d.ads || []; S.solutions = d.soluciones || [];
      S.offline = msg; S.loaded.articles = true; render();
    } catch (e) {
      $("#main").innerHTML = `<div class="wrap" style="padding:60px 0"><div class="empty">Todavía no hay contenido publicado. <b>${esc(msg || "")}</b></div></div>`;
    }
  }

  // ---------- Enrutado ----------
  function route() {
    const h = (location.hash || "#portada").slice(1);
    S.route = /^[a-z0-9-]+$/i.test(h) ? h : "portada";
    setNav();
    window.scrollTo({ top: 0, behavior: "auto" });
    render();
  }
  function setNav() {
    let navSec = S.route;
    if (S.route.startsWith("a-")) { const art = S.articles.find((x) => x.id === S.route.slice(2)); navSec = art ? (art.kind === "blog" ? "blogs" : art.kind === "analisis" ? "analisis" : art.section) : "portada"; }
    else if (S.route.startsWith("blog-")) navSec = "blogs";
    else if (S.route.startsWith("sol-")) navSec = "tecnologia";
    $$("#nav a").forEach((a) => a.classList.toggle("active", a.dataset.sec === navSec));
  }

  function render() {
    if (!S.loaded.articles) return;
    renderChrome();
    const r = S.route;
    const main = $("#main");
    let html = "";
    S.pageImgs = new Set();
    if (r.startsWith("a-")) html = viewArticle(r.slice(2));
    else if (r === "tierra" || r === "mar" || r === "aire") html = viewMode(r);
    else if (r === "regulacion") html = viewRegulacion();
    else if (r === "licitaciones") html = viewLicitaciones();
    else if (r === "analisis") html = viewAnalisis();
    else if (r === "datos") html = viewDatos();
    else if (r === "fuentes") html = viewFuentes();
    else if (r === "blogs") html = viewBlogs();
    else if (r.startsWith("blog-")) html = viewBlog(r.slice(5));
    else if (r === "anunciate") html = viewAnunciate();
    else if (r === "logistica") html = viewLogistica();
    else if (r === "pronto") html = viewPronto();
    else if (r === "tecnologia") html = viewTecnologia();
    else if (r.startsWith("sol-")) html = viewSolucion(r.slice(4));
    else html = viewPortada();
    if (["tierra", "mar", "aire", "logistica", "regulacion", "licitaciones", "analisis", "tecnologia"].includes(r)) html += adSlot("seccion", { section: r, key: r }, "wide");
    const note = S.offline || (window.MOTICIAS_REVIEW && window.MOTICIAS_REVIEW.note) || "";
    main.innerHTML = (note ? `<div class="wrap"><div class="notice">${esc(note)}</div></div>` : "") + html;
    afterRender();
    const dr = $("#drawer");
    if (dr && dr.classList.contains("open") && !S.editing && !S.editingBlog && !S.editingAd && !S.editingBol && !S.editingAg && !S.editingSol && S.adminTab !== "edicion" && !(document.activeElement && document.activeElement.id === "f-q")) renderAdmin();
  }

  function renderChrome() {
    setNav();
    const ed = S.edition || {};
    const date = ed.date || todayISO();
    $("#top-date").textContent = fmtLong(date).replace(/^./, (c) => c.toUpperCase());
    $("#top-edition").textContent = ed.number ? `Edición nº ${ed.number}` : "";
    $("#top-close").textContent = ed.closed_at ? `Cierre de edición ${ed.closed_at} CET` : "";
    $("#footer-end").textContent = `FIN DE EDICIÓN · ${fmtMid(date)}${ed.closed_at ? ", " + ed.closed_at + " CET" : ""}`;
    // Teletipo: boletines de la fecha más reciente
    const tk = $("#ticker"), reel = $("#ticker-reel");
    let items = [], label = "Boletines";
    if (ed.ticker && ed.ticker.length) { items = ed.ticker; label = ed.ticker_label || "Boletines"; }
    else if (S.boletines.length) { items = S.boletines.slice(0, 14).map((b) => ({ ref: b.referencia, text: b.nota || b.titulo_corto || b.titulo, url: b.url })); label = `BOE ${fmtShort(S.boletines[0].fecha)}`; }
    if (items.length) {
      tk.hidden = false; $(".label", tk).textContent = label;
      const one = items.map((b) => `<span class="item"><b>${esc(b.ref || "")}</b><a href="${esc(safeUrl(b.url))}" target="_blank" rel="noopener">${esc(b.text || "")}</a></span>`).join("");
      reel.innerHTML = one + one;
    } else { tk.hidden = true; }
    // Créditos fotográficos del pie
    const credits = [];
    published().forEach((a) => { if (a.image && a.image.credit) credits.push(`${a.image.credit}${a.image.license ? " (" + a.image.license + ")" : ""}`); });
    $("#footer-credits").textContent = credits.length ? "Fotografías: " + Array.from(new Set(credits)).join(" · ") : "";
  }

  // ---------- Fragmentos ----------
  function kicker(a) { return `<div class="kicker ${esc(a.section || "")}">${esc(a.kicker || SECTION_NAMES[a.section] || "")}</div>`; }
  function srcBadges(a) {
    const kinds = new Set((a.sources || []).map((s) => s.kind));
    let out = "";
    if (kinds.has("oficial")) out += `<span class="badge src">Fuente oficial</span>`;
    if (kinds.has("medios")) out += `<span class="badge src">Medios</span>`;
    return out;
  }
  function metaLine(a, opts) {
    opts = opts || {};
    const parts = [];
    if (a.relevance) parts.push(`<span class="badge ${a.relevance === "ALTA" ? "alta" : "media"}">${esc(a.relevance)}</span>`);
    if (a.status === "borrador") parts.push(`<span class="badge borrador">Borrador</span>`);
    if (a.sponsored_by) parts.push(`<span class="badge sponsored">Patrocinado</span>`);
    parts.push(`<span class="num">${esc(fmtShort(a.date || a.published_at))}</span>`);
    if (a.event_date && a.event_date !== a.date) parts.push(`<span class="num" title="Fecha de los hechos">hechos: ${esc(fmtShort(a.event_date))}</span>`);
    if (!opts.noSrc) parts.push(srcBadges(a));
    if (opts.author && a.author) parts.push(`<span>${esc(a.author)}</span>`);
    return `<div class="meta">${parts.join("")}</div>`;
  }
  function imgFor(a) {
    const src = imgSrc(a);
    if (src && !S.pageImgs.has(src)) { S.pageImgs.add(src); return { src, real: true }; }
    return { src: artSvg(a.section, a.id), real: false };
  }
  function thumb(a, cls) {
    const im = imgFor(a), src = im.src;
    const cr = a.image && im.real ? creditText(a.image) : "";
    return `<div class="thumb ${cls || ""}"><img src="${esc(src)}" alt="${esc((a.image && a.image.alt) || a.title || "")}" loading="lazy">${cr ? `<span class="credit">${esc(cr)}</span>` : ""}</div>`;
  }
  function card(a, extra) {
    return `<article class="card ${extra || ""}">${thumb(a)}<div class="body">${kicker(a)}<h3><a href="#a-${esc(a.id)}">${esc(a.title)}</a></h3><p class="dek">${esc(a.subtitle || "")}</p>${a.relevance_for ? `<p class="for"><b>Para quién</b>${esc(a.relevance_for)}</p>` : ""}${metaLine(a)}</div></article>`;
  }
  function featureCard(a) {
    return `<article class="feature">${thumb(a)}<div class="body"><div class="kicker analisis">${esc(a.kicker || "Reportaje")}</div><h3><a href="#a-${esc(a.id)}">${esc(a.title)}</a></h3><p class="dek">${esc(a.subtitle || "")}</p><p class="drop">${esc(a.summary || "")}</p><div class="meta"><span>${esc(a.author || "Redacción")}</span><span class="sep">·</span><span>${readingTime(a.body_md)} min de lectura</span><span class="sep">·</span><span class="num">${esc(fmtShort(a.date))}</span></div></div></article>`;
  }
  function listItem(a, withMini) {
    return `<li>${withMini ? "" : ""}<div>${kicker(a)}<h3><a href="#a-${esc(a.id)}">${esc(a.title)}</a></h3>${metaLine(a, { noSrc: true })}</div>${withMini ? `<img class="mini" src="${esc(imgFor(a).src)}" alt="" loading="lazy">` : ""}</li>`;
  }
  function sectionHead(sec, title, more, sub) {
    const sp = sectionSponsor(sec);
    return `<div class="section-head ${esc(sec || "")}"><h2>${esc(title)}${sub ? `<small>${esc(sub)}</small>` : ""}</h2>${sp || more ? `<div class="sh-right">${sp}${more ? `<a class="more" href="#${esc(more)}">Ver sección →</a>` : ""}</div>` : ""}</div>`;
  }
  function emptyBox(txt) { return `<div class="empty">${txt}</div>`; }

  // ---------- Portada ----------
  function viewPortada() {
    const ed = S.edition || {};
    const all = news().filter((a) => !a.sponsored_by);
    const an = sortByDate(analyses());
    const lead = (ed.lead_id && all.find((a) => a.id === ed.lead_id)) || sortByRank(all)[0];
    const analysis = (ed.analysis_id && an.find((a) => a.id === ed.analysis_id)) || an.find((a) => a.kind === "analisis") || an[0];
    const used = new Set([lead && lead.id, analysis && analysis.id].filter(Boolean));
    const rest = sortByRank(all.filter((a) => !used.has(a.id)));
    const brief = rest.slice(0, 5); brief.forEach((a) => used.add(a.id));
    const essentials = rest.filter((a) => !used.has(a.id)).slice(0, 6); essentials.forEach((a) => used.add(a.id));
    if (!all.length && !an.length) return `<div class="wrap" style="padding:50px 0">${emptyBox("Todavía no hay piezas publicadas en esta edición." + (S.canEdit ? " Abre <b>Administrar</b> para crear la primera." : ""))}</div>`;

    let html = `<section class="cover"><div class="wrap"><div class="cover-grid">`;
    if (lead) {
      const lim = imgFor(lead), src = lim.src;
      html += `<article class="lead"><div class="photo"><img src="${esc(src)}" alt="${esc((lead.image && lead.image.alt) || "")}"></div><div class="shade"></div>${lim.real && lead.image && creditText(lead.image) ? `<span class="credit">${esc(creditText(lead.image))}</span>` : ""}<div class="text">${kicker(lead)}<h2>${esc(lead.title)}</h2><p class="dek">${esc(lead.subtitle || "")}</p>${metaLine(lead)}</div><a class="cover-link" href="#a-${esc(lead.id)}" aria-label="${esc(lead.title)}"></a></article>`;
    }
    html += `<div class="rail">`;
    if (analysis) {
      const initial = (analysis.author || "M").trim().charAt(0).toUpperCase();
      html += `<article class="analysis-card"><div class="kicker analisis">${esc(analysis.kicker || "Análisis del día")}</div><h3><a href="#a-${esc(analysis.id)}">${esc(analysis.title)}</a></h3><p class="dek">${esc(analysis.subtitle || "")}</p><div class="byline"><span class="avatar">${esc(initial)}</span><span><b>${esc(analysis.author || "Redacción")}</b><br>${esc(analysis.author_role || "")}${analysis.author_role ? " · " : ""}${readingTime(analysis.body_md)} min de lectura</span></div><p class="drop">${esc(analysis.summary || "")}</p><a class="readmore" href="#a-${esc(analysis.id)}">Leer el análisis completo →</a></article>`;
    }
    if (brief.length) {
      html += `<div class="brief"><h4>En cinco titulares</h4><ol>${brief.map((a) => `<li><div><a href="#a-${esc(a.id)}">${esc(a.title)}</a><div class="meta"><span class="kicker ${esc(a.section)}" style="font-size:10.5px">${esc(SECTION_NAMES[a.section] || "")}</span><span class="num">${esc(fmtShort(a.date))}</span>${a.relevance === "ALTA" ? `<span class="badge alta">Alta</span>` : ""}</div></div></li>`).join("")}</ol></div>`;
    }
    html += `</div></div></div></section>`;

    if (essentials.length) {
      html += `<section class="block"><div class="wrap">${sectionHead("", "Lo esencial hoy", "", "selección por impacto sectorial")}<div class="cards reveal">${essentials.map((a) => card(a)).join("")}</div></div></section>`;
    }
    html += adSlot("portada-medio", { key: "pm" }, "wide");
    // Reportajes
    const reps = sortByDate(reportajes()).slice(0, 3);
    if (reps.length) {
      html += `<section class="block"><div class="wrap">${sectionHead("analisis", "Reportajes", "analisis", "investigación propia: el sistema, el dinero y la regla")}<div class="features reveal">${reps.map((a) => featureCard(a)).join("")}</div></div></section>`;
    }
    if (reps.length) html += adSlot("portada-reportajes", { key: "pr" }, "wide");
    // Documento del día
    if (ed.document && ed.document.title) {
      html += `<section class="block"><div class="wrap"><div class="section-head regulacion"><h2>El documento del día<small>fuente primaria</small></h2></div><div class="card wide reveal" style="display:grid;grid-template-columns:1fr;max-width:none"><div class="body" style="padding:22px 26px"><div class="kicker regulacion">${esc(ed.document.kicker || "Documento")}</div><h3 style="font-size:26px"><a href="${esc(safeUrl(ed.document.url))}" target="_blank" rel="noopener">${esc(ed.document.title)}</a></h3><p class="dek">${esc(ed.document.summary || "")}</p><div class="meta"><span class="badge src">${esc(ed.document.source || "Fuente oficial")}</span><span class="num">${esc(fmtShort(ed.document.date))}</span>${ed.document.ref ? `<span class="num">${esc(ed.document.ref)}</span>` : ""}</div></div></div></div></section>`;
    }
    // Mapa
    html += mapSection();
    // Modos
    for (const sec of ["tierra", "mar", "aire"]) {
      const all2 = sortByRank(bySection(sec));
      if (!all2.length) continue;
      const fresh = all2.filter((a) => !used.has(a.id));
      const arr = fresh.concat(all2.filter((a) => used.has(a.id)));
      const l = arr[0], others = arr.slice(1, 5);
      used.add(l.id);
      html += `<section class="block"><div class="wrap">${sectionHead(sec, SECTION_NAMES[sec], sec, modeSub(sec))}<div class="mode-grid reveal"><article class="mode-lead">${thumb(l)}${kicker(l)}<h3><a href="#a-${esc(l.id)}">${esc(l.title)}</a></h3><p class="dek">${esc(l.subtitle || "")}</p>${metaLine(l)}</article><ul class="list">${others.map((a) => listItem(a, true)).join("")}</ul></div></div></section>`;
    }
    html += logisticaPortada(used);
    // Regulación
    const reg = sortByRank(bySection("regulacion"));
    if (reg.length) html += `<section class="block"><div class="wrap">${sectionHead("regulacion", "Regulación", "regulacion", "normas, expedientes y consultas")}<div class="cards reveal">${reg.slice(0, 3).map((a) => card(a)).join("")}</div></div></section>`;
    // Licitaciones y plazos
    const lic = sortByRank(bySection("licitaciones"));
    if (lic.length) {
      const li = licItems(), cf = {}; li.forEach((x) => (cf[x.fase] = (cf[x.fase] || 0) + 1));
      html += `<section class="block"><div class="wrap">${sectionHead("licitaciones", "Licitaciones", "licitaciones", "anuncios, publicaciones y resoluciones")}<div class="fase-strip">${Object.keys(LIC_FASES).map((k) => `<a href="#licitaciones" data-goto-fase="${k}"><b>${cf[k] || 0}</b><span>${esc(LIC_FASES[k])}</span></a>`).join("")}</div><div class="cards reveal">${lic.slice(0, 3).map((a) => card(a)).join("")}</div></div></section>`;
    }
    const soon = prontoItems().slice(0, 8);
    if (soon.length) html += `<section class="block"><div class="wrap">${sectionHead("licitaciones", "Sucederá pronto", "pronto", "plazos, consultas y fechas que vienen")}<ul class="pronto-list two reveal">${soon.map(prontoRow).join("")}</ul></div></section>`;
    // Boletines del día
    html += boletinesSection(true);
    html += tecnologiaPortada();
    // Datos
    html += `<section class="block"><div class="wrap">${sectionHead("", "Datos", "datos", "series propias a partir de fuentes primarias")}${dataGrid()}</div></section>`;
    html += adSlot("portada-pie", { key: "pp" }, "wide");
    // Método
    html += `<section class="block"><div class="wrap">${sectionHead("", "Cómo trabajamos", "fuentes")}${methodBox()}</div></section>`;
    return html;
  }
  function modeSub(sec) { return { tierra: "autobús, ferrocarril, carretera y movilidad urbana", mar: "pasaje marítimo, puertos y marina mercante", aire: "aerolíneas, aeropuertos y navegación aérea" }[sec] || ""; }

  // ---------- Secciones ----------
  function viewMode(sec) {
    const arr = sortByRank(bySection(sec));
    const an = sortByDate(analyses().filter((a) => a.scope === sec || a.section === sec));
    let html = `<section class="block"><div class="wrap">${sectionHead(sec, SECTION_NAMES[sec], "", modeSub(sec))}`;
    if (!arr.length) html += emptyBox("Sin piezas publicadas en esta sección todavía.");
    else {
      const l = arr[0];
      html += `<div class="mode-grid"><article class="mode-lead">${thumb(l)}${kicker(l)}<h3><a href="#a-${esc(l.id)}">${esc(l.title)}</a></h3><p class="dek">${esc(l.subtitle || "")}</p>${metaLine(l)}</article><ul class="list">${arr.slice(1, 7).map((a) => listItem(a, true)).join("")}</ul></div>`;
      if (arr.length > 7) html += `<hr class="rule"><div class="cards">${arr.slice(7).map((a) => card(a)).join("")}</div>`;
    }
    html += `</div></section>`;
    if (an.length) html += `<section class="block"><div class="wrap">${sectionHead("analisis", "Análisis y reportajes de " + SECTION_NAMES[sec].toLowerCase(), "analisis")}<div class="features">${an.map((a) => featureCard(a)).join("")}</div></div></section>`;
    const bol = S.boletines.filter((b) => (b.modos || []).includes(sec));
    if (bol.length) html += `<section class="block"><div class="wrap">${sectionHead("", "En los boletines oficiales", "", `${bol.length} referencias`)}${boletinesTable(bol.slice(0, 40))}</div></section>`;
    return html;
  }

  function viewRegulacion() {
    const arr = sortByRank(bySection("regulacion"));
    const disp = S.boletines.filter((b) => /^1|^3/.test(String(b.seccion_codigo || "")) || /ley|real decreto|orden|resolución|acuerdo/i.test(b.tipo || ""));
    let html = `<section class="block"><div class="wrap">${sectionHead("regulacion", "Regulación", "", "normas publicadas, expedientes europeos y consultas abiertas")}`;
    html += arr.length ? `<div class="cards">${arr.map((a) => card(a)).join("")}</div>` : emptyBox("Sin piezas de regulación publicadas todavía.");
    html += `</div></section>`;
    const cons = S.agenda.filter((d) => d.kind === "consulta" && (daysUntil(d.date) == null || daysUntil(d.date) >= -1));
    if (cons.length) html += `<section class="block"><div class="wrap">${sectionHead("regulacion", "Consultas y audiencias abiertas")}<div class="timeline">${cons.map(deadlineCard).join("")}</div></div></section>`;
    html += `<section class="block"><div class="wrap">${sectionHead("", "Disposiciones y resoluciones", "", "BOE, sección I y III")}${disp.length ? boletinesTable(disp) : emptyBox("Sin referencias.")}</div></section>`;
    return html;
  }

  function viewAnalisis() {
    const an = sortByDate(analyses());
    let html = `<section class="block"><div class="wrap">${sectionHead("analisis", "Análisis y reportajes", "", "un análisis de fondo cada día, en un ámbito distinto, y reportajes de investigación propia")}`;
    if (!an.length) html += emptyBox("Sin análisis publicados todavía.");
    else {
      const l = an.find((a) => a.kind === "analisis") || an[0];
      const rest = an.filter((a) => a.id !== l.id);
      html += `<article class="mode-lead" style="max-width:900px">${thumb(l)}<div class="kicker analisis">${esc(l.kicker || "Análisis")}</div><h3><a href="#a-${esc(l.id)}">${esc(l.title)}</a></h3><p class="dek">${esc(l.subtitle || "")}</p>${metaLine(l, { author: true })}</article>`;
      if (rest.length) html += `<hr class="rule"><div class="features">${rest.map((a) => featureCard(a)).join("")}</div>`;
    }
    const rot = (S.settings && S.settings.rotation) || [];
    if (rot.length) html += `<hr class="rule"><div class="admin-note" style="max-width:720px">Rotación de ámbitos del análisis diario: ${esc(rot.join(" · "))}.</div>`;
    html += `</div></section>`;
    return html;
  }

  function viewDatos() {
    return `<section class="block"><div class="wrap">${sectionHead("", "Datos", "", "series propias, construidas a partir de fuentes primarias")}${dataGrid(true)}</div></section>`;
  }

  function viewFuentes() {
    if (!S.sources) { fetch("data/sources.json", { cache: "no-store" }).then((r) => (r.ok ? r.json() : [])).then((j) => { S.sources = j; if (S.route === "fuentes") render(); }).catch(() => { S.sources = []; }); }
    let html = `<section class="block"><div class="wrap">${sectionHead("", "Cómo trabajamos", "", "método, fuentes y correcciones")}${methodBox(true)}</div></section>`;
    if (S.sources && S.sources.length) {
      const groups = {};
      S.sources.forEach((s) => { (groups[s.type] = groups[s.type] || []).push(s); });
      const order = ["boletín oficial", "licitaciones", "ministerio/regulador", "agencia/gestor", "operador público", "estadística", "jurisprudencia", "asociación", "think tank", "prensa especializada"];
      const keys = Object.keys(groups).sort((a, b) => (order.indexOf(a) + 1 || 99) - (order.indexOf(b) + 1 || 99));
      html += `<section class="block"><div class="wrap">${sectionHead("", "Fuentes que vigilamos", "", `${S.sources.length} fuentes verificadas`)}<div class="sources-grid">${keys.map((k) => `<div class="source-group"><h4>${esc(k)}</h4><ul>${groups[k].map((s) => `<li><a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener">${esc(s.name)}</a><span>${esc([s.mode, s.scope].filter(Boolean).join(" · "))}</span></li>`).join("")}</ul></div>`).join("")}</div></div></section>`;
    }
    return html;
  }

  function methodBox(full) {
    const ed = S.edition || {};
    return `<div class="method"><div><h3>Método</h3><p>${esc(ed.note_metodologica || "Cada pieza se construye sobre al menos una fuente primaria (boletines oficiales, organismos reguladores, operadores públicos) y se contrasta con prensa especializada. Las fechas de publicación y de consulta se indican en cada enlace. Los boletines se barren a diario con la API de datos abiertos del BOE.")}</p>${full ? `<h3 style="margin-top:18px">Estructura de cada noticia</h3><ul><li>De qué trata</li><li>Quiénes son los protagonistas</li><li>Para quién es relevante</li><li>Por qué es importante</li><li>Qué puede pasar ahora</li><li>Para saber más, con fuente oficial y medios</li></ul>` : ""}</div><div><h3>Independencia y correcciones</h3><p>Sin publicidad de proveedores. La dirección editorial declara su vinculación con el sector (Movenbus, plataforma de contratación de autobuses); las piezas que afecten a intereses propios se señalan o se omiten.</p><p style="margin-top:10px">Los errores se corrigen en la propia pieza, con nota fechada. Las observaciones se reciben en la dirección de contacto de la cabecera.</p>${full ? `<h3 style="margin-top:18px">Uso de herramientas</h3><p>La búsqueda, el barrido de boletines y los borradores se apoyan en herramientas de inteligencia artificial bajo supervisión editorial. Ninguna cifra se publica sin su fuente.</p>` : ""}</div></div>`;
  }

  // ---------- Boletines ----------
  function boletinesSection(portada) {
    if (!S.boletines.length) return "";
    const latest = S.boletines[0].fecha, oldest = S.boletines[S.boletines.length - 1].fecha;
    const shown = portada ? S.boletines.slice(0, 12) : S.boletines;
    const sub = latest === oldest ? `BOE ${fmtShort(latest)} · ${S.boletines.length} referencias seleccionadas` : `BOE del ${fmtShort(oldest)} al ${fmtShort(latest)} · ${S.boletines.length} referencias seleccionadas`;
    return `<section class="block"><div class="wrap">${sectionHead("", portada ? `Boletines oficiales` : "Boletines", portada ? "regulacion" : "", sub)}${boletinesTable(shown)}${portada && S.boletines.length > 12 ? `<p style="margin-top:10px;font-size:13px"><a href="#regulacion"><b>Ver todas las referencias →</b></a></p>` : ""}</div></section>`;
  }
  function boletinesTable(rows) {
    return `<div class="table-wrap"><table class="data"><thead><tr><th>Fecha</th><th>Referencia</th><th>Órgano</th><th>Título</th><th>Tipo</th><th>Modo</th></tr></thead><tbody>${rows.map((b) => `<tr><td class="date">${esc(fmtNum(b.fecha))}</td><td class="ref"><a href="${esc(safeUrl(b.url))}" target="_blank" rel="noopener">${esc(b.referencia || "")}</a></td><td style="font-size:12.5px;color:var(--muted)">${esc(b.organo || "")}</td><td class="t"><a href="${esc(safeUrl(b.url))}" target="_blank" rel="noopener">${esc(b.titulo || "")}</a>${b.nota ? `<div style="font-size:12.5px;color:var(--muted);margin-top:4px">${esc(b.nota)}</div>` : ""}</td><td style="font-size:12.5px">${esc(b.tipo || "")}</td><td>${(b.modos || []).map((m) => `<span class="tag ${esc(m)}">${esc(SECTION_NAMES[m] || m)}</span>`).join(" ")}</td></tr>`).join("")}</tbody></table></div>`;
  }

  // ---------- Agenda / plazos ----------
  function upcomingDeadlines(n) {
    return S.agenda.filter((d) => { const k = daysUntil(d.date); return k == null || k >= -1; }).slice(0, n);
  }
  function deadlineCard(d) {
    const k = daysUntil(d.date);
    const when = k == null ? "" : k < 0 ? "cerrado ayer" : k === 0 ? "hoy" : k === 1 ? "mañana" : `en ${k} días`;
    const kindName = { plazo: "Plazo", consulta: "Consulta", vigor: "Entrada en vigor", evento: "Evento" }[d.kind] || "Fecha";
    return `<div class="deadline ${esc(d.kind || "")}"><div class="when"><span>${esc(fmtNum(d.date))} · ${esc(kindName)}</span><b>${esc(when)}</b></div><div class="what">${d.url ? `<a href="${esc(safeUrl(d.url))}" target="_blank" rel="noopener">${esc(d.title)}</a>` : esc(d.title)}</div><div class="who">${esc(d.authority || "")}${d.amount ? ` · ${esc(d.amount)}` : ""}</div></div>`;
  }

  // ---------- Mapa ----------
  function mapSection() {
    const SP = window.SPAIN_PATHS;
    const pts = news().filter((a) => a.geo && typeof a.geo.lat === "number" && typeof a.geo.lon === "number");
    if (!SP || !pts.length) return "";
    const m = SP.meta;
    const proj = (lon, lat) => { let x = lon, y = lat; if (lat < 30 && lon < -12) { x += m.dlon; y += m.dlat; } return [(x - m.lon0) * m.k * m.cos0, -(y - m.lat0) * m.k]; };
    const [x0, y0, x1, y1] = SP.bbox; const pad = 24;
    const vb = `${x0 - pad} ${y0 - pad} ${x1 - x0 + 2 * pad} ${y1 - y0 + 2 * pad}`;
    const cb = SP.canariasBox;
    // Agrupar por lugar aproximado
    const groups = [];
    pts.forEach((a) => { const [x, y] = proj(a.geo.lon, a.geo.lat); const g = groups.find((q) => Math.hypot(q.x - x, q.y - y) < 14); if (g) g.items.push(a); else groups.push({ x, y, items: [a], place: a.geo.place || "" }); });
    const pins = groups.map((g, i) => { const a = g.items[0]; const dx = (i % 2 ? 1 : -1) * 0; return `<g class="pin ${esc(a.section)}" data-pin="${i}" transform="translate(${g.x.toFixed(1)} ${g.y.toFixed(1)})"><circle class="halo" r="6"/><circle class="core" r="${g.items.length > 1 ? 6.5 : 5}"/><text x="${9 + dx}" y="4">${esc(g.place)}${g.items.length > 1 ? ` (${g.items.length})` : ""}</text></g>`; }).join("");
    const svg = `<svg viewBox="${vb}" role="img" aria-label="Mapa de España con los lugares de las noticias de hoy"><g>${SP.provinces.map((p) => `<path class="prov" d="${p.d}"><title>${esc(p.name)}</title></path>`).join("")}<path class="ccaa" d="${SP.ccaa}"/><path class="border" d="${SP.border}"/><rect class="inset" x="${cb[0] - 14}" y="${cb[1] - 14}" width="${cb[2] - cb[0] + 28}" height="${cb[3] - cb[1] + 28}" rx="3"/></g>${pins}</svg>`;
    const list = groups.map((g, i) => g.items.map((a) => `<li data-pin="${i}"><div><div class="place">${esc(g.place)}</div>${kicker(a)}<h3><a href="#a-${esc(a.id)}">${esc(a.title)}</a></h3></div></li>`).join("")).join("");
    return `<section class="block"><div class="wrap">${sectionHead("", "El mapa del día", "", `${pts.length} noticias con lugar`)}<div class="map-grid reveal"><div class="map-card" id="map-card"><div class="title">Dónde pasa hoy</div>${svg}<div class="legend"><span><i style="background:#a4d37a"></i>Tierra</span><span><i style="background:#5fc3dd"></i>Mar</span><span><i style="background:#8fb5f0"></i>Aire</span><span><i style="background:#ffb86b"></i>Licitaciones</span></div></div><div class="map-list"><ul class="list" id="map-list">${list}</ul></div></div></div></section>`;
  }
  function wireMap() {
    const card = $("#map-card"); if (!card) return;
    const setActive = (i) => { $$("[data-pin]").forEach((el) => el.classList.toggle("active", el.dataset.pin === String(i))); };
    $$(".pin", card).forEach((p) => { p.addEventListener("mouseenter", () => setActive(p.dataset.pin)); p.addEventListener("click", () => { setActive(p.dataset.pin); const li = $(`#map-list li[data-pin="${p.dataset.pin}"]`); if (li) li.scrollIntoView({ block: "nearest", behavior: "smooth" }); }); });
    $$("#map-list li").forEach((li) => li.addEventListener("mouseenter", () => setActive(li.dataset.pin)));
  }

  // ---------- Datos ----------
  function dataGrid(full) {
    let by = {};
    if (S.edition && S.edition.boe_series && Object.keys(S.edition.boe_series).length) by = S.edition.boe_series;
    else S.boletines.forEach((b) => { const d = b.fecha; if (!d) return; by[d] = by[d] || { total: 0, lic: 0, disp: 0 }; by[d].total++; if (/^5/.test(String(b.seccion_codigo || "")) || /licitaci|formalizaci|concurso|anuncio/i.test(b.tipo || "")) by[d].lic++; else by[d].disp++; });
    const days = Object.keys(by).sort().slice(-12);
    const max = Math.max(1, ...days.map((d) => by[d].total));
    const W = 640, H = 220, padL = 30, padB = 34, bw = Math.min(40, (W - padL - 10) / Math.max(1, days.length) - 8);
    const sy = (v) => H - padB - (v / max) * (H - padB - 20);
    let bars = "";
    days.forEach((d, i) => {
      const x = padL + 6 + i * ((W - padL - 10) / Math.max(1, days.length));
      const g = by[d];
      const hD = sy(0) - sy(g.disp), hL = sy(0) - sy(g.lic);
      bars += `<rect class="bar" x="${x}" y="${sy(g.disp)}" width="${bw}" height="${hD}" style="animation-delay:${i * 50}ms"><title>${fmtShort(d)}: ${g.disp} disposiciones y resoluciones</title></rect>`;
      bars += `<rect class="bar lic" x="${x}" y="${sy(g.total)}" width="${bw}" height="${hL}" style="animation-delay:${i * 50 + 80}ms"><title>${fmtShort(d)}: ${g.lic} anuncios de contratación</title></rect>`;
      bars += `<text class="val" x="${x + bw / 2}" y="${sy(g.total) - 5}" text-anchor="middle">${g.total}</text>`;
      bars += `<text class="lbl" x="${x + bw / 2}" y="${H - padB + 16}" text-anchor="middle">${fmtNum(d).slice(0, 5)}</text>`;
    });
    const grid = [0, .5, 1].map((f) => `<line class="axis" x1="${padL}" x2="${W}" y1="${sy(max * f)}" y2="${sy(max * f)}" stroke-dasharray="${f ? "2 4" : "0"}"/><text class="lbl" x="${padL - 6}" y="${sy(max * f) + 4}" text-anchor="end">${Math.round(max * f)}</text>`).join("");
    const chart = `<div class="chart-card reveal"><h3>El BOE en transporte, día a día</h3><div class="sub">Referencias de transporte y movilidad de personas localizadas en cada sumario diario del BOE. Tinta: disposiciones, resoluciones y actos. Ámbar: anuncios de licitación y formalización.</div><svg viewBox="0 0 ${W} ${H}">${grid}${bars}</svg><div class="note">Fuente: elaboración propia a partir de la API de datos abiertos del BOE (boe.es/datosabiertos). Criterio: títulos que contienen términos del sector o emitidos por el Ministerio de Transportes y Movilidad Sostenible y sus entes.</div></div>`;
    const serVals = Object.values(by);
    const totalBol = serVals.length ? serVals.reduce((s, v) => s + (v.total || 0), 0) : S.boletines.length;
    const lic = serVals.length ? serVals.reduce((s, v) => s + (v.lic || 0), 0) : S.boletines.filter((b) => /^5/.test(String(b.seccion_codigo || ""))).length;
    const amounts = S.agenda.filter((d) => d.amount_eur).reduce((s, d) => s + (+d.amount_eur || 0), 0);
    const dl = upcomingDeadlines(100).length;
    const kpis = `<div class="ad-kpis"><div class="kpi"><div class="v num">${totalBol}</div><div class="l">referencias de transporte localizadas en el BOE en el periodo seguido</div></div><div class="kpi accent"><div class="v num">${lic}</div><div class="l">anuncios de licitación y formalización (sección V)</div></div><div class="kpi"><div class="v num">${dl}</div><div class="l">plazos y fechas en la agenda de los próximos días</div></div><div class="kpi"><div class="v num">${amounts ? (amounts / 1e6).toLocaleString("es-ES", { maximumFractionDigits: 1 }) + " M€" : "—"}</div><div class="l">valor estimado de las licitaciones con plazo en agenda</div></div></div>`;
    let more = "";
    if (full) {
      const sec = {}; S.boletines.forEach((b) => (b.modos || ["transversal"]).forEach((m) => (sec[m] = (sec[m] || 0) + 1)));
      more = `<div class="chart-card" style="margin-top:24px"><h3>Reparto por modo</h3><div class="sub">Una referencia puede afectar a más de un modo.</div><div class="kpis" style="grid-template-columns:repeat(4,1fr)">${Object.keys(sec).map((k) => `<div class="kpi"><div class="v num">${sec[k]}</div><div class="l">${esc(SECTION_NAMES[k] || k)}</div></div>`).join("")}</div></div>`;
    }
    return `<div class="data-grid">${chart}${kpis}</div>${more}`;
  }

  // ---------- Artículo ----------
  function fmtTl(s) {
    if (!s) return "";
    const m = String(s).match(/^(\d{4})-(\d{2})(?:-(\d{2}))?/);
    if (!m) return String(s);
    if (!m[3]) return `${MONTHS_S[+m[2] - 1]} ${m[1]}`;
    return fmtShort(s);
  }
  function viewArticle(id) {
    const a = S.articles.find((x) => x.id === id);
    if (!a) return `<div class="wrap" style="padding:50px 0">${emptyBox("No encontramos esa pieza. <a href='#portada'><b>Volver a la portada</b></a>")}</div>`;
    if (a.status === "borrador" && !S.canEdit) return `<div class="wrap" style="padding:50px 0">${emptyBox("Esta pieza todavía no está publicada.")}</div>`;
    const long = isLong(a);
    const src = imgSrc(a); if (src) S.pageImgs.add(src);
    const related = sortByRank(news().filter((x) => x.id !== a.id && (x.section === a.section || x.subsector === a.subsector))).slice(0, 4);
    const srcLi = (s) => `<li><span class="badge src">${esc(s.kind === "oficial" ? "Oficial" : "Medios")}</span><div><a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener">${esc(s.title || s.outlet || s.url)}</a><div class="meta"><span>${esc(s.outlet || host(s.url))}</span>${s.published ? `<span class="sep">·</span><span>Publicado ${esc(fmtNum(s.published))}</span>` : ""}${s.accessed ? `<span class="sep">·</span><span>Consultado ${esc(fmtNum(s.accessed))}</span>` : ""}</div><div class="url">${esc(s.url || "")}</div></div></li>`;
    const oficial = (a.sources || []).filter((s) => s.kind === "oficial"), medios = (a.sources || []).filter((s) => s.kind !== "oficial");
    const srcList = (oficial.length || medios.length) ? `<div class="sources"><h3>Para saber más</h3>${oficial.length ? `<h4>Documentos y fuentes oficiales</h4><ul>${oficial.map(srcLi).join("")}</ul>` : ""}${medios.length ? `<h4>Medios</h4><ul>${medios.map(srcLi).join("")}</ul>` : ""}</div>` : "";
    const quick = [["Quiénes son los protagonistas", a.actors], ["Para quién es relevante", a.relevance_for], ["Por qué es importante", a.why], ["Qué puede pasar ahora", a.next]].filter((b) => b[1]);
    let body = "";
    if (a.body_md) {
      body = `<div class="article-body">${md(a.body_md)}</div>`;
      const q2 = (a.summary ? [["De qué trata", a.summary]] : []).concat(quick);
      if (!long && q2.length) body += `<div class="quick"><h3>Guía rápida</h3><div class="quick-grid">${q2.map((b) => `<div class="blk"><h4>${esc(b[0])}</h4><p>${esc(b[1])}</p></div>`).join("")}</div></div>`;
    } else if (long) {
      body = `<div class="article-body">${md(a.summary || "")}</div>`;
    } else {
      const blocks = [["De qué trata", a.summary]].concat(quick).filter((b) => b[1]);
      body = `<div class="blocks">${a.key_fact ? `<div class="blk key"><h4>Dato clave</h4><p>${esc(a.key_fact)}</p></div>` : ""}${blocks.map((b) => `<div class="blk"><h4>${esc(b[0])}</h4><p>${esc(b[1])}</p></div>`).join("")}</div>`;
    }
    const kd = (a.key_data || []).filter((k) => k && k.value);
    const tl = (a.timeline || []).filter((t) => t && t.text).slice().sort((x, y) => String(x.date || "").localeCompare(String(y.date || "")));
    const today = todayISO();
    const ofs = (a.sources || []).filter((s) => s.kind === "oficial" && s.published).slice().sort((x, y) => String(x.published).localeCompare(String(y.published)));
    const lastOf = ofs.length ? ofs[ofs.length - 1] : null;
    const accessed = (a.sources || []).map((s) => s.accessed).filter(Boolean).sort().pop();
    const fmtTs = (iso) => { const m = String(iso || "").match(/^(\d{4}-\d{2}-\d{2})(?:T(\d{2}:\d{2}))?/); return m ? fmtShort(m[1]) + (m[2] ? ", " + m[2] + " CET" : "") : ""; };
    const age = a.event_date ? Math.round((parseDate(a.date || a.published_at) - parseDate(a.event_date)) / 864e5) : null;
    const trace = `<div class="box trace"><h4>Trazabilidad</h4><dl>${a.event_date ? `<div><dt>Fecha de los hechos</dt><dd>${esc(fmtShort(a.event_date))}${age != null && age > 7 ? ` <span class="badge media">seguimiento: hechos de hace ${age} días</span>` : ""}</dd></div>` : ""}${lastOf ? `<div><dt>Documento oficial más reciente</dt><dd>${esc(lastOf.outlet || host(lastOf.url))}, publicado el ${esc(fmtShort(lastOf.published))}</dd></div>` : `<div><dt>Documento oficial</dt><dd>sin fecha de publicación indicada</dd></div>`}${accessed ? `<div><dt>Fuentes consultadas</dt><dd>${esc(fmtShort(accessed))}</dd></div>` : ""}<div><dt>Redactado</dt><dd>${esc(fmtTs(a.published_at || a.date))}</dd></div>${a.revised_at ? `<div><dt>Ampliado o corregido</dt><dd>${esc(fmtTs(a.revised_at))}</dd></div>` : ""}</dl></div>`;
    const aside = `<aside class="aside">${trace}${a.key_fact && (a.body_md || long) ? `<div class="box key"><h4>Dato clave</h4><p>${esc(a.key_fact)}</p></div>` : ""}${kd.length ? `<div class="box"><h4>Cifras clave</h4><dl class="kd">${kd.map((k) => `<div><dt>${esc(k.label || "")}</dt><dd>${esc(k.value)}${k.source ? `<small>${esc(k.source)}</small>` : ""}</dd></div>`).join("")}</dl></div>` : ""}${tl.length ? `<div class="box"><h4>Cronología</h4><ol class="tl">${tl.map((t) => `<li class="${String(t.date || "") > today ? "next" : ""}"><span class="d">${esc(fmtTl(t.date))}</span><span>${esc(t.text)}</span></li>`).join("")}</ol></div>` : ""}${long ? `<div class="box"><h4>Autor</h4><p style="font-size:14px"><b>${esc(a.author || "Redacción")}</b>${a.author_role ? `<br><span style="color:var(--muted)">${esc(a.author_role)}</span>` : ""}</p>${a.author_note ? `<p style="font-size:12.5px;color:var(--muted);margin-top:8px">${esc(a.author_note)}</p>` : ""}</div>` : ""}${related.length ? `<div class="box"><h4>Relacionadas</h4><ul>${related.map((r) => `<li><a href="#a-${esc(r.id)}">${esc(r.title)}</a><div class="meta"><span class="kicker ${esc(r.section)}" style="font-size:10.5px">${esc(SECTION_NAMES[r.section] || "")}</span><span>${esc(fmtShort(r.date))}</span></div></li>`).join("")}</ul></div>` : ""}${(a.tags || []).length ? `<div class="box"><h4>Etiquetas</h4><p style="font-size:13px;color:var(--ink-2)">${a.tags.map((t) => esc(t)).join(" · ")}</p></div>` : ""}${a.sponsored_by ? "" : adSlot("articulo-lateral", { section: a.section, blog: a.blog_id, key: a.id }, "side")}</aside>`;
    const blog = a.kind === "blog" ? blogById(a.blog_id) : null;
    const backHref = blog ? "blog-" + blogSlug(blog) : a.kind === "analisis" ? "analisis" : (a.section || "portada");
    const backLabel = blog ? blog.name : a.kind === "analisis" ? "Análisis" : (SECTION_NAMES[a.section] || "Portada");
    const spNote = a.sponsored_by ? `<div class="sponsored-note">Contenido patrocinado por ${/^https?:/i.test(a.sponsor_url || "") ? `<a href="${esc(a.sponsor_url)}" target="_blank" rel="sponsored noopener">${esc(a.sponsored_by)}</a>` : `<b>${esc(a.sponsored_by)}</b>`}. Comunicación comercial identificada como tal; no forma parte de la selección editorial de MOTICIAS.</div>` : "";
    const endAd = a.sponsored_by ? "" : adsFor("articulo-cierre", { section: a.section, blog: a.blog_id }).length ? `<div class="ad-end">${adHtml(pickAd((function () { const l = adsFor("articulo-cierre", { section: a.section, blog: a.blog_id }); const p = l.filter((x) => x.type !== "autopromocion"); return p.length ? p : l; })(), "ac" + a.id), "articulo-cierre", "wide")}</div>` : "";
    const words = readingTime((a.body_md || "") + " " + (a.summary || "") + " " + (a.why || ""));
    return `<article class="article ${long ? "long" : ""}${blog ? " blogpost" : ""}"${blog && safeColor(blog.accent) ? ` style="--blog:${esc(safeColor(blog.accent))}"` : ""}><div class="wrap"><a class="back" href="#${esc(backHref)}">← ${esc(backLabel)}</a><div class="article-head">${kicker(a)}<h1>${esc(a.title)}</h1><p class="dek">${esc(a.subtitle || "")}</p><div class="meta">${a.relevance ? `<span class="badge ${a.relevance === "ALTA" ? "alta" : "media"}">${esc(a.relevance)}</span>` : ""}${a.status === "borrador" ? `<span class="badge borrador">Borrador</span>` : ""}<span><b style="color:var(--ink)">${esc(a.author || "Redacción")}</b>${a.author_role ? `, ${esc(a.author_role)}` : ""}</span><span class="sep">·</span><span>Publicado el ${esc(fmtMid(a.date || a.published_at))}${a.published_time ? `, ${esc(a.published_time)} CET` : ""}</span>${a.updated_at ? `<span class="sep">·</span><span>Actualizado ${esc(fmtNum(a.updated_at))}</span>` : ""}<span class="sep">·</span><span>${words} min de lectura</span>${srcBadges(a)}</div>${S.canEdit ? `<div class="share"><button type="button" data-edit="${esc(a.id)}">Editar esta pieza</button><button type="button" data-copy="${esc(a.id)}">Copiar enlace</button></div>` : `<div class="share"><button type="button" data-copy="${esc(a.id)}">Copiar enlace</button></div>`}</div>${src ? `<figure class="article-hero"><img src="${esc(src)}" alt="${esc((a.image && a.image.alt) || "")}"><figcaption><span>${esc((a.image && a.image.caption) || (a.image && a.image.alt) || "")}</span><span>${esc(creditText(a.image))}${a.image && a.image.source ? ` · <a href="${esc(safeUrl(a.image.source))}" target="_blank" rel="noopener">origen</a>` : ""}</span></figcaption></figure>` : ""}<div class="article-grid"><div>${spNote}${body}${srcList}${endAd}</div>${aside}</div></div></article>`;
  }

  // ---------- Blogs y ediciones a medida ----------
  const BLOG_TYPES = { blog: "Blog", asociacion: "Edición para asociación", empresa: "Edición para empresa", boletin: "Boletín temático" };
  const BLOG_LAYOUTS = { revista: "Revista (tarjetas con foto)", lista: "Lista compacta", boletin: "Boletín (columna única, sin fotos)" };
  const BLOG_MODULES = { posts: "Entradas propias", feed: "Selección automática de MOTICIAS", plazos: "Plazos y licitaciones", boletines: "Boletines oficiales", contacto: "Caja de contacto" };
  const lc = (s) => String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  const safeColor = (c) => (/^#[0-9a-f]{3,8}$/i.test(String(c || "").trim()) ? String(c).trim() : "");
  const blogById = (id) => S.blogs.find((b) => b.id === id);
  const blogSlug = (b) => b.slug || b.id;
  const blogPosts = (bid, all) => sortByDate(S.articles.filter((a) => a.kind === "blog" && a.blog_id === bid && (all || a.status !== "borrador")));
  const blogVisible = (b) => S.canEdit || (b.status !== "borrador" && b.visibility !== "oculto");
  function blogFeed(b) {
    const f = b.filters || {};
    const secs = f.sections || [], subs = (f.subsectors || []).map(lc), kws = (f.keywords || []).map(lc), kinds = f.kinds || [];
    if (!secs.length && !subs.length && !kws.length && !kinds.length) return [];
    return sortByDate(published().filter((a) => {
      if (kinds.length && !kinds.includes(a.kind || "noticia")) return false;
      if (secs.length && !secs.includes(a.section) && !secs.includes(a.scope)) return false;
      if (subs.length && !subs.some((s) => lc(a.subsector) === s || (a.tags || []).some((t) => lc(t) === s))) return false;
      if (kws.length) { const hay = lc([a.title, a.subtitle, a.summary, a.kicker, (a.tags || []).join(" "), a.subsector].join(" ")); if (!kws.some((k) => hay.includes(k))) return false; }
      return true;
    }));
  }
  function blogCover(b) { const im = b.cover; if (!im) return ""; return im.src || (im.assetId ? "/_blob/" + im.assetId : ""); }
  function blogLogo(b, cls) { const t = (b.logo_text || b.name || "M").trim(); const ini = t.length <= 3 ? t : t.split(/\s+/).filter((w) => w.length > 2).slice(0, 2).map((w) => w[0]).join("").toUpperCase() || t[0]; return `<span class="blog-logo ${cls || ""}">${esc(ini)}</span>`; }
  function blogCard(b) {
    const cover = blogCover(b);
    const n = blogPosts(b.id).length, feedN = (b.modules || {}).feed !== false ? blogFeed(b).length : 0;
    const flags = S.canEdit ? `${b.status === "borrador" ? `<span class="badge borrador">Borrador</span>` : ""}${b.visibility === "oculto" ? `<span class="badge media">Solo con enlace</span>` : ""}` : "";
    return `<article class="blog-card" style="--blog:${esc(safeColor(b.accent) || "#0b2545")}"><a class="blog-card-top" href="#blog-${esc(blogSlug(b))}">${cover ? `<img src="${esc(cover)}" alt="" loading="lazy">` : ""}<span class="shade"></span>${blogLogo(b)}</a><div class="body"><div class="kicker">${esc(BLOG_TYPES[b.type] || "Blog")}</div><h3><a href="#blog-${esc(blogSlug(b))}">${esc(b.name)}</a></h3><p class="dek">${esc(b.tagline || "")}</p>${b.description ? `<p class="for">${esc(b.description)}</p>` : ""}<div class="meta">${b.author ? `<span>${esc(b.author)}</span><span class="sep">·</span>` : ""}<span>${n} ${n === 1 ? "entrada" : "entradas"}</span>${feedN ? `<span class="sep">·</span><span>${feedN} piezas seleccionadas</span>` : ""}${flags}</div></div></article>`;
  }
  function viewBlogs() {
    const list = S.blogs.filter(blogVisible).slice().sort((a, b) => (a.order || 99) - (b.order || 99) || String(a.name).localeCompare(String(b.name)));
    const contact = (S.settings && S.settings.contact) || "";
    let html = `<section class="block"><div class="wrap">${sectionHead("", "Blogs y ediciones", "", "espacios con firma propia y versiones a medida")}`;
    html += list.length ? `<div class="blog-grid reveal">${list.map(blogCard).join("")}</div>` : emptyBox("Todavía no hay blogs publicados." + (S.canEdit ? " Créalos en <b>Administrar → Blogs</b>." : ""));
    html += `<div class="bespoke reveal"><div><div class="kicker">Ediciones a medida</div><h3>Una MOTICIAS para tu asociación, tu empresa o tu boletín</h3><p>Seleccionamos cada mañana las normas, contratos y plazos que afectan a tu actividad, con tu marca y tu enfoque: autobús, ferrocarril, puertos, aeropuertos o movilidad urbana. Se entrega como página propia, como boletín por correo o como bloque para tu web.</p></div><div class="bespoke-cta">${contact ? `<a class="btn" href="mailto:${esc(contact)}?subject=${encodeURIComponent("Edición a medida de MOTICIAS")}">Solicitar una edición</a>` : ""}<a class="btn secondary" href="#anunciate">Formatos y patrocinios</a></div></div>`;
    return html + `</div></section>`;
  }
  function postsBlock(arr, layout) {
    if (layout === "lista") return `<ul class="list blog-list">${arr.map((a) => listItem(a, true)).join("")}</ul>`;
    if (layout === "boletin") return `<div class="digest">${arr.map((a) => `<article>${kicker(a)}<h3><a href="#a-${esc(a.id)}">${esc(a.title)}</a></h3>${a.summary ? `<p>${esc(a.summary)}</p>` : `<p>${esc(a.subtitle || "")}</p>`}${metaLine(a)}</article>`).join("")}</div>`;
    return `<div class="cards">${arr.map((a) => card(a)).join("")}</div>`;
  }
  function viewBlog(slug) {
    const b = S.blogs.find((x) => blogSlug(x) === slug);
    if (!b || (!S.canEdit && b.status === "borrador")) return `<div class="wrap" style="padding:50px 0">${emptyBox("No encontramos ese blog. <a href='#blogs'><b>Ver todos los blogs</b></a>")}</div>`;
    const mods = Object.assign({ posts: true, feed: true, plazos: false, boletines: false, contacto: false }, b.modules || {});
    const layout = b.layout || "revista";
    const posts = mods.posts ? blogPosts(b.id, S.canEdit) : [];
    const pinned = b.pinned_id && posts.find((p) => p.id === b.pinned_id);
    const rest = posts.filter((p) => p !== pinned);
    const feed = mods.feed ? blogFeed(b).slice(0, b.feed_limit || 9) : [];
    const accent = safeColor(b.accent) || "#0b2545";
    const cover = blogCover(b); if (cover) S.pageImgs.add(cover);
    const sp = pickAd(adsFor("blog", { blog: b.id }).filter((ad) => ad.type === "patrocinio"), "blog-sp-" + b.id);
    const modos = (b.filters && b.filters.modos) || [];
    let html = `<div class="blog-page" style="--blog:${esc(accent)}"><section class="blog-head">${cover ? `<img class="bg" src="${esc(cover)}" alt="">` : ""}<div class="shade"></div><div class="wrap"><a class="back" href="#blogs">← Blogs y ediciones</a><div class="blog-id">${blogLogo(b, "big")}<div><div class="kicker">${esc(BLOG_TYPES[b.type] || "Blog")}${S.canEdit && b.visibility === "oculto" ? " · solo con enlace" : ""}${S.canEdit && b.status === "borrador" ? " · borrador" : ""}</div><h1>${esc(b.name)}</h1>${b.tagline ? `<p class="dek">${esc(b.tagline)}</p>` : ""}<div class="meta">${b.author ? `<span><b>${esc(b.author)}</b>${b.author_role ? ", " + esc(b.author_role) : ""}</span>` : ""}${sp ? `<span class="sep">·</span><span class="sponsor-inline">Con el patrocinio de ${sponsorLink(sp, "blog")}</span>` : ""}</div></div></div>${S.canEdit ? `<div class="share"><button type="button" data-blog-admin="${esc(b.id)}">Editar blog</button><button type="button" data-blog-post="${esc(b.id)}">+ Nueva entrada</button><button type="button" data-blog-mail="${esc(b.id)}">Copiar versión boletín (HTML)</button></div>` : ""}</div></section><div class="wrap">`;
    if (b.intro_md || b.cta_text) html += `<div class="blog-intro reveal">${b.intro_md ? `<div class="article-body">${md(b.intro_md)}</div>` : ""}${b.cta_text && b.cta_url ? `<a class="btn accent" href="${esc(/^(https?:|mailto:|#)/i.test(b.cta_url) ? b.cta_url : "")}" ${/^https?:/i.test(b.cta_url) ? 'target="_blank" rel="noopener"' : ""}>${esc(b.cta_text)}</a>` : ""}</div>`;
    if (pinned) html += `<section class="block"><div class="section-head"><h2>Destacado</h2></div><div class="features reveal">${featureCard(pinned)}</div></section>`;
    if (mods.posts && (rest.length || (!pinned && S.canEdit))) html += `<section class="block"><div class="section-head"><h2>${esc(b.posts_title || "Entradas")}</h2></div>${rest.length ? `<div class="reveal">${postsBlock(rest, layout)}</div>` : emptyBox("Todavía no hay entradas en este blog. Pulsa <b>+ Nueva entrada</b> para escribir la primera.")}</section>`;
    const ad = adSlot("blog", { blog: b.id, key: b.id, inline: true }, "wide");
    if (ad) html += ad;
    if (feed.length) html += `<section class="block"><div class="section-head"><h2>${esc(b.feed_title || "Seleccionado por MOTICIAS")}<small>${esc(feedRule(b))}</small></h2></div><div class="reveal">${postsBlock(feed, layout)}</div></section>`;
    if (mods.plazos) { const dl = upcomingDeadlines(40).filter((d) => !modos.length || modos.includes(d.mode)).slice(0, 8); if (dl.length) html += `<section class="block"><div class="section-head licitaciones"><h2>Plazos que vienen<small>agenda de licitaciones, consultas y fechas límite</small></h2></div><div class="timeline reveal">${dl.map(deadlineCard).join("")}</div></section>`; }
    if (mods.boletines) { const bo = S.boletines.filter((x) => !modos.length || (x.modos || []).some((m) => modos.includes(m))).slice(0, 10); if (bo.length) html += `<section class="block"><div class="section-head regulacion"><h2>En los boletines<small>referencias oficiales más recientes</small></h2></div><ul class="bol-mini reveal">${bo.map((x) => `<li><span class="num">${esc(x.referencia || "")}</span><a href="${esc(safeUrl(x.url))}" target="_blank" rel="noopener">${esc(x.titulo_corto || x.titulo || "")}</a><span class="meta"><span>${esc(x.boletin || "")}</span><span class="num">${esc(fmtShort(x.fecha))}</span></span></li>`).join("")}</ul></section>`; }
    if (mods.contacto) { const mail = b.contact_email || (S.settings && S.settings.contact) || ""; html += `<section class="block"><div class="bespoke"><div><div class="kicker">Contacto</div><h3>${esc(b.contact_title || "¿Quieres aparecer aquí o proponer un tema?")}</h3><p>${esc(b.contact_text || "Escríbenos con tu propuesta. Respondemos en el día laborable siguiente.")}</p></div><div class="bespoke-cta">${mail ? `<a class="btn accent" href="mailto:${esc(mail)}?subject=${encodeURIComponent(b.name)}">Escribir</a>` : ""}</div></div></section>`; }
    if (!posts.length && !feed.length && !b.intro_md) html += emptyBox("Este blog todavía no tiene contenido. Configura filtros de selección automática o añade entradas.");
    return html + `</div></div>`;
  }
  function feedRule(b) {
    const f = b.filters || {}, parts = [];
    if ((f.kinds || []).length) parts.push(f.kinds.map((k) => ({ noticia: "noticias", analisis: "análisis", reportaje: "reportajes" }[k] || k)).join(", "));
    if ((f.sections || []).length) parts.push(f.sections.map((s) => SECTION_NAMES[s] || s).join(", "));
    if ((f.subsectors || []).length) parts.push(f.subsectors.join(", "));
    if ((f.keywords || []).length) parts.push("«" + f.keywords.join("», «") + "»");
    return parts.join(" · ");
  }
  function blogNewsletterHtml(b) {
    const base = location.href.split("#")[0];
    const accent = safeColor(b.accent) || "#0b2545";
    const items = blogPosts(b.id).concat((b.modules || {}).feed !== false ? blogFeed(b) : []).slice(0, 10);
    const ed = S.edition || {};
    const row = (a) => `<tr><td style="padding:14px 0;border-bottom:1px solid #e3e1da"><div style="font:700 11px Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:${accent}">${esc(a.kicker || SECTION_NAMES[a.section] || "")}</div><a href="${esc(base + "#a-" + a.id)}" style="font:700 18px Georgia,serif;color:#111;text-decoration:none">${esc(a.title)}</a><div style="font:14px/1.5 Arial,sans-serif;color:#444;margin-top:4px">${esc(a.summary || a.subtitle || "")}</div></td></tr>`;
    return `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;margin:0 auto;background:#fff"><tr><td style="background:${accent};padding:22px 24px;color:#fff"><div style="font:700 12px Arial,sans-serif;letter-spacing:.1em;text-transform:uppercase;opacity:.85">MOTICIAS · ${esc(BLOG_TYPES[b.type] || "Blog")}</div><div style="font:700 26px Georgia,serif;margin-top:4px">${esc(b.name)}</div>${b.tagline ? `<div style="font:15px Arial,sans-serif;opacity:.9;margin-top:4px">${esc(b.tagline)}</div>` : ""}</td></tr><tr><td style="padding:6px 24px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">${items.map(row).join("")}</table></td></tr><tr><td style="padding:16px 24px;font:12px Arial,sans-serif;color:#777">FIN DE EDICIÓN · ${esc(fmtMid(ed.date || todayISO()))}${ed.closed_at ? ", " + esc(ed.closed_at) + " CET" : ""} · <a href="${esc(base + "#blog-" + blogSlug(b))}" style="color:${accent}">Ver en la web</a></td></tr></table>`;
  }
  async function copyBlogNewsletter(id) {
    const b = blogById(id); if (!b) return;
    const html = blogNewsletterHtml(b);
    try {
      if (window.ClipboardItem && navigator.clipboard && navigator.clipboard.write) await navigator.clipboard.write([new ClipboardItem({ "text/html": new Blob([html], { type: "text/html" }), "text/plain": new Blob([html], { type: "text/plain" }) })]);
      else await navigator.clipboard.writeText(html);
      toast("Versión boletín copiada: pégala en Brevo o en tu gestor de correo");
    } catch (e) { toast("No se pudo copiar al portapapeles", true); }
  }

  // ---------- Publicidad y patrocinios ----------
  const AD_TYPES = { banner: "Banner", patrocinio: "Patrocinio de sección o blog", contenido: "Contenido patrocinado", boletin: "Boletín por correo", autopromocion: "Autopromoción (casa)" };
  const AD_SLOTS = {
    "portada-medio": "Portada · tras «Lo esencial hoy»",
    "portada-reportajes": "Portada · tras «Reportajes»",
    "portada-pie": "Portada · antes de «Cómo trabajamos»",
    "seccion": "Secciones · cabecera patrocinada y banner",
    "articulo-lateral": "Artículo · columna lateral",
    "articulo-cierre": "Artículo · tras «Para saber más»",
    "blog": "Blogs y ediciones a medida",
    "newsletter": "Boletín por correo (reserva)",
  };
  const AD_STATES = { activo: "En curso", programado: "Programada", finalizado: "Finalizada", pausado: "Pausada", borrador: "Borrador" };
  function adState(ad, t) {
    t = t || todayISO();
    if (ad.status === "pausado") return "pausado";
    if (ad.status === "borrador") return "borrador";
    if (ad.start && ad.start > t) return "programado";
    if (ad.end && ad.end < t) return "finalizado";
    return "activo";
  }
  function adsFor(slot, ctx) {
    ctx = ctx || {}; const t = todayISO();
    return S.ads.filter((ad) => adState(ad, t) === "activo" && (ad.slots || []).includes(slot)
      && (!ctx.section || !(ad.sections || []).length || ad.sections.includes(ctx.section))
      && (!ctx.blog || !(ad.blog_ids || []).length || ad.blog_ids.includes(ctx.blog)));
  }
  function pickAd(list, key) {
    if (!list || !list.length) return null;
    const arr = list.slice().sort((a, b) => String(a.id).localeCompare(String(b.id)));
    let h = 0; for (const ch of String(key || "")) h = (h * 31 + ch.charCodeAt(0)) | 0;
    const total = arr.reduce((s, a) => s + Math.max(1, +a.weight || 1), 0);
    let r = Math.abs(Math.floor(Date.now() / 864e5) * 7 + h) % total;
    for (const a of arr) { r -= Math.max(1, +a.weight || 1); if (r < 0) return a; }
    return arr[0];
  }
  function adUrl(ad, slot) {
    const u = String(ad.url || "").trim();
    if (/^mailto:[^\s"'<>]+$/i.test(u) || /^#[a-z0-9-]*$/i.test(u)) return u;
    if (!/^https?:\/\//i.test(u)) return "";
    if (ad.utm === false) return u;
    try { const x = new URL(u); const p = { utm_source: "moticias", utm_medium: ad.type || "banner", utm_campaign: ad.utm_campaign || ad.id, utm_content: slot }; Object.keys(p).forEach((k) => { if (!x.searchParams.has(k)) x.searchParams.set(k, p[k]); }); return x.toString(); } catch (e) { return u; }
  }
  function adImg(ad) { const im = ad.image; if (!im) return ""; return im.src || (im.assetId ? "/_blob/" + im.assetId : ""); }
  function adLabel(ad) { return ad.label || ({ patrocinio: "Patrocinio", contenido: "Contenido patrocinado", autopromocion: "MOTICIAS" }[ad.type] || "Publicidad"); }
  function adHtml(ad, slot, variant) {
    if (!ad) return "";
    const href = adUrl(ad, slot), ext = /^https?:/i.test(href), img = adImg(ad);
    const open = href ? `<a class="ad-body" href="${esc(href)}"${ext ? ' target="_blank" rel="sponsored noopener"' : ""}>` : `<div class="ad-body">`;
    const close = href ? "</a>" : "</div>";
    return `<aside class="ad ad-${esc(variant || "wide")} ${img ? "has-img" : "text-only"}${ad.type === "autopromocion" ? " house" : ""}" style="--ad-accent:${esc(safeColor(ad.accent) || "#0b2545")}" aria-label="${esc(adLabel(ad))}"><div class="ad-label">${esc(adLabel(ad))}${ad.advertiser && ad.type !== "autopromocion" ? " · " + esc(ad.advertiser) : ""}</div>${open}${img ? `<img src="${esc(img)}" alt="${esc((ad.image && ad.image.alt) || ad.headline || ad.advertiser || "")}" loading="lazy">` : ""}<div class="ad-text">${ad.type === "autopromocion" && ad.advertiser && lc(ad.advertiser) !== lc(adLabel(ad)) ? `<span class="ad-brand">${esc(ad.advertiser)}</span>` : ""}${ad.headline ? `<b>${esc(ad.headline)}</b>` : ""}${ad.text ? `<p>${esc(ad.text)}</p>` : ""}${ad.cta ? `<span class="ad-cta">${esc(ad.cta)} →</span>` : ""}</div>${close}</aside>`;
  }
  function adSlot(slot, ctx, variant) {
    const list = adsFor(slot, ctx).filter((a) => a.type !== "patrocinio" || slot !== "seccion");
    const paid = list.filter((a) => a.type !== "autopromocion");
    const ad = pickAd(paid.length ? paid : list, slot + ((ctx && ctx.key) || ""));
    if (!ad) return "";
    const inner = adHtml(ad, slot, variant || "wide");
    return variant === "side" || (ctx && ctx.inline) ? inner : `<section class="block ad-block"><div class="wrap">${inner}</div></section>`;
  }
  function sponsorLink(ad, slot) { const href = adUrl(ad, slot); return href ? `<a href="${esc(href)}"${/^https?:/i.test(href) ? ' target="_blank" rel="sponsored noopener"' : ""}>${esc(ad.advertiser || ad.name)}</a>` : `<b>${esc(ad.advertiser || ad.name)}</b>`; }
  function sectionSponsor(sec) {
    if (!sec || !S.ads) return "";
    const ad = pickAd(adsFor("seccion", { section: sec }).filter((a) => a.type === "patrocinio" && (a.sections || []).includes(sec)), "sp-" + sec);
    return ad ? `<span class="sponsor">Sección patrocinada por ${sponsorLink(ad, "seccion")}</span>` : "";
  }
  function viewAnunciate() {
    const contact = (S.settings && S.settings.contact) || "";
    const mail = (subj) => contact ? `mailto:${contact}?subject=${encodeURIComponent(subj)}` : "";
    const formats = [
      ["Banner en portada", "Tres posiciones entre bloques editoriales, nunca por encima de la apertura ni dentro de una pieza. Imagen horizontal o texto con llamada a la acción."],
      ["Patrocinio de sección", "Tierra, Mar, Aire, Regulación o Licitaciones y plazos con la mención «Sección patrocinada por» en la cabecera y un banner propio en la sección."],
      ["Patrocinio de blog o edición a medida", "Presencia en un espacio temático o en la edición personalizada de una asociación o empresa, con mención en la cabecera y en la versión boletín."],
      ["Contenido patrocinado", "Piezas firmadas por la marca y señalizadas como tales en la tarjeta, en el titular y en el pie. No entran en la selección editorial del día."],
      ["Boletín por correo", "Un espacio por envío en el boletín de la mañana, separado del contenido y marcado como publicidad."],
    ];
    return `<section class="block"><div class="wrap">${sectionHead("", "Anúnciate y patrocina", "", "formatos para llegar a quien decide en transporte de viajeros")}<div class="ads-intro reveal"><p>MOTICIAS se lee por la mañana, antes de las reuniones: direcciones de operadores, áreas de contratación de administraciones, asociaciones, consultoras e ingenierías del transporte de viajeros por tierra, mar y aire. La publicidad se separa siempre del contenido editorial y se marca de forma visible.</p></div><div class="formats reveal">${formats.map((f) => `<div class="fmt"><h4>${esc(f[0])}</h4><p>${esc(f[1])}</p></div>`).join("")}</div><div class="method reveal" style="margin-top:28px"><div><h3>Reglas que no cambian</h3><p>Toda comunicación comercial se identifica como tal, de acuerdo con el artículo 20 de la Ley 34/2002 (LSSI). Los anunciantes no eligen ni revisan piezas informativas. Medimos con parámetros UTM en el enlace de destino, sin cookies de seguimiento de terceros. Las tarifas se facilitan bajo petición según formato, duración y exclusividad.</p></div><div><h3>Hablemos</h3><p>Cuéntanos qué quieres comunicar y a quién. Te proponemos formato, calendario y medición.</p><p style="margin-top:12px">${contact ? `<a class="btn" href="${esc(mail("Publicidad y patrocinios en MOTICIAS"))}">Pedir información</a> ` : ""}<a class="btn secondary" href="#blogs">Ediciones a medida</a></p></div></div></div></section>`;
  }

  // ---------- Licitaciones: fases y sectores ----------
  const LIC_FASES = { anuncio: "Anuncios de licitación", publicacion: "Publicaciones", resolucion: "Resoluciones" };
  const LIC_FASE_SHORT = { anuncio: "Anuncio", publicacion: "Publicación", resolucion: "Resolución" };
  const LIC_FASE_HELP = { anuncio: "convocatorias abiertas, con plazo para presentar ofertas", publicacion: "información pública, competencia de proyectos, consultas, pliegos y correcciones", resolucion: "adjudicaciones, formalizaciones y desistimientos" };
  const SECTORS = { autobus: "Autobús", ferrocarril: "Ferrocarril", urbano: "Movilidad urbana", maritimo: "Marítimo y puertos", aereo: "Aéreo y aeropuertos", carreteras: "Carreteras", logistica: "Logística", otros: "Otros" };
  function licFase(x) {
    if (x.fase && LIC_FASES[x.fase]) return x.fase;
    const t = lc([x.tipo, (x.tags || []).join(" "), x.title || x.titulo_corto || x.titulo, x.kicker].join(" "));
    if (/adjudic|formaliz|desisti|renuncia a la celebracion|desiert|fallid/.test(t)) return "resolucion";
    if (/correccion|corrige|informacion publica|competencia de proyectos|consulta|subasta|trazado|expropia/.test(t)) return "publicacion";
    if (/anuncio de licitacion|licita|concurso|convocatoria/.test(t)) return "anuncio";
    return "publicacion";
  }
  function sectorOf(x) {
    if (x.sector && SECTORS[x.sector]) return x.sector;
    const t = lc([x.subsector, (x.tags || []).join(" "), x.title || x.titulo_corto || x.titulo, x.organo, x.authority, x.kicker].join(" "));
    if (x.section === "logistica" || /mercanc|logistic|carga aerea|contenedor/.test(t)) return "logistica";
    if (/\bmetro\b|tranvia|\bemt\b|\btmb\b|dbus|autobus urbano|bus urbano|transporte urbano|bicicleta/.test(t)) return "urbano";
    if (/nautic|ferry|ferris|naviera|buque/.test(t)) return "maritimo";
    if (/ferrocarril|ferroviari|adif|renfe|cercanias|\btren|fgc|alta velocidad|estacion de viajeros|estaciones/.test(t)) return "ferrocarril";
    if (/aena|aeropuerto|aere|aeronave|vuelo|enaire|aerolinea/.test(t)) return "aereo";
    if (/autobus|autocar|viajeros por carretera|rutas a la demanda|demanda rural|concesion.*\bbus/.test(t)) return "autobus";
    if (/\bpuertos?\b|portuari|maritim|\bports\b|\bapb\b|\bapv\b/.test(t)) return "maritimo";
    if (/carretera|autovia|autopista|trazado/.test(t)) return "carreteras";
    const m = x.mode || (x.modos || [])[0];
    return m === "mar" ? "maritimo" : m === "aire" ? "aereo" : "otros";
  }
  function isLicBoletin(b) {
    const t = lc([b.tipo, b.titulo_corto, b.titulo].join(" "));
    return /^5A/.test(String(b.seccion_codigo || "")) || /licita|adjudic|formaliz|concurso|concesion|competencia de proyectos|subasta/.test(t);
  }
  function licItems() {
    const out = [];
    published().filter((a) => a.section === "licitaciones" || a.fase).forEach((a) => out.push({ t: "a", fase: licFase(a), sector: sectorOf(a), date: a.event_date || a.date, o: a }));
    S.boletines.filter(isLicBoletin).forEach((b) => out.push({ t: "b", fase: licFase(b), sector: sectorOf(b), date: b.fecha, o: b }));
    return out.sort((x, y) => String(y.date || "").localeCompare(String(x.date || "")));
  }
  function chips(attr, opts, cur, counts, allLabel) {
    return `<div class="chips" role="group">${[["", allLabel || "Todo"]].concat(Object.keys(opts).filter((k) => !counts || counts[k]).map((k) => [k, opts[k]])).map(([k, l]) => `<button type="button" class="chip ${cur === k ? "on" : ""}" ${attr}="${esc(k)}">${esc(l)}${counts && k && counts[k] ? ` <span>${counts[k]}</span>` : ""}</button>`).join("")}</div>`;
  }
  function licRow(it) {
    const o = it.o;
    const href = it.t === "a" ? "#a-" + o.id : safeUrl(o.url);
    const title = it.t === "a" ? o.title : o.titulo_corto || o.titulo;
    const who = it.t === "a" ? (o.kicker || "") : [o.organo, o.referencia].filter(Boolean).join(" · ");
    return `<li><span class="d num">${esc(fmtNum(it.date))}</span><span class="sec">${esc(SECTORS[it.sector] || "")}</span><div><a href="${esc(href)}"${it.t === "b" ? ' target="_blank" rel="noopener"' : ""}>${esc(title)}</a><div class="who">${it.t === "a" ? `<span class="badge src">Pieza MOTICIAS</span> ` : `<span class="badge src">${esc(o.boletin || "Boletín")}</span> `}${esc(who)}</div></div></li>`;
  }
  function viewLicitaciones() {
    const f = S.licFilter || (S.licFilter = { fase: "", sector: "" });
    const all = licItems();
    const bySec = all.filter((x) => !f.sector || x.sector === f.sector);
    const cF = {}, cS = {};
    all.forEach((x) => { cS[x.sector] = (cS[x.sector] || 0) + 1; });
    bySec.forEach((x) => { cF[x.fase] = (cF[x.fase] || 0) + 1; });
    let html = `<section class="block"><div class="wrap">${sectionHead("licitaciones", "Licitaciones", "", "anuncios, publicaciones y resoluciones por sector")}<div class="filters">${chips("data-lic-fase", LIC_FASES, f.fase, cF, "Todas las fases")}${chips("data-lic-sector", SECTORS, f.sector, cS, "Todos los sectores")}</div>`;
    const fases = f.fase ? [f.fase] : Object.keys(LIC_FASES);
    fases.forEach((fk) => {
      const items = bySec.filter((x) => x.fase === fk);
      const arts = items.filter((x) => x.t === "a").map((x) => x.o);
      html += `<div class="lic-block"><div class="lic-head"><h3>${esc(LIC_FASES[fk])} <span>${items.length}</span></h3><p>${esc(LIC_FASE_HELP[fk])}</p></div>`;
      if (!items.length) html += `<p class="lic-empty">Sin ${esc(LIC_FASES[fk].toLowerCase())}${f.sector ? " en " + esc(SECTORS[f.sector].toLowerCase()) : ""} en esta edición.</p>`;
      if (arts.length) html += `<div class="cards reveal">${sortByRank(arts).slice(0, f.fase ? 12 : 3).map((a) => card(a)).join("")}</div>`;
      const rows = items.filter((x) => x.t === "b" || (arts.length > (f.fase ? 12 : 3) && sortByRank(arts).slice(f.fase ? 12 : 3).includes(x.o)));
      if (rows.length) html += `<ul class="lic-list">${rows.map(licRow).join("")}</ul>`;
      html += `</div>`;
    });
    const soon = prontoItems().filter((x) => !f.sector || x.sector === f.sector).slice(0, 6);
    if (soon.length) html += `<div class="lic-block"><div class="lic-head"><h3>Sucederá pronto</h3><p>próximos plazos y fechas${f.sector ? " · " + esc(SECTORS[f.sector]) : ""} · <a href="#pronto"><b>ver el calendario completo →</b></a></p></div><ul class="pronto-list">${soon.map(prontoRow).join("")}</ul></div>`;
    return html + `</div></section>`;
  }

  // ---------- Sucederá pronto ----------
  const PRONTO_KINDS = { plazo: "Plazos", consulta: "Consultas", vigor: "Entradas en vigor", evento: "Eventos", hito: "Hitos anunciados" };
  const PRONTO_ONE = { plazo: "Plazo", consulta: "Consulta", vigor: "En vigor", evento: "Evento", hito: "Hito" };
  function prontoItems() {
    const t = todayISO(), out = [], seen = new Set();
    S.agenda.forEach((d) => { if (!d.date || d.date < t) return; out.push({ date: d.date, kind: d.kind || "plazo", title: d.title, who: [d.authority, d.amount].filter(Boolean).join(" · "), href: safeUrl(d.url), ext: true, sector: sectorOf(d) }); seen.add(lc(d.title).slice(0, 40)); });
    const words = (x) => new Set(lc(x).replace(/[^a-z0-9 ]/g, " ").split(/\s+/).filter((w) => w.length > 3));
    const similar = (x, y) => { const A = words(x), B = words(y); if (!A.size || !B.size) return false; let n = 0; A.forEach((w) => { if (B.has(w)) n++; }); return n / Math.min(A.size, B.size) >= 0.5; };
    published().forEach((a) => (a.timeline || []).forEach((tl) => {
      if (!tl || !tl.text || !/^\d{4}-\d{2}-\d{2}$/.test(String(tl.date || "")) || tl.date <= t) return;
      const key = lc(tl.text).slice(0, 40); if (seen.has(key)) return;
      if (out.some((o) => o.date === tl.date && similar(o.title, tl.text))) return;
      seen.add(key);
      out.push({ date: tl.date, kind: "hito", title: tl.text, who: "De la pieza: " + a.title, href: "#a-" + a.id, ext: false, sector: sectorOf(a) });
    }));
    return out.sort((x, y) => x.date.localeCompare(y.date));
  }
  function prontoRow(x) {
    const k = daysUntil(x.date), d = parseDate(x.date);
    const when = k === 0 ? "hoy" : k === 1 ? "mañana" : `en ${k} días`;
    return `<li class="${esc(x.kind)}"><div class="day"><b>${d ? d.getUTCDate() : ""}</b><span>${d ? MONTHS_S[d.getUTCMonth()] : ""}</span></div><div><div class="m"><span class="k">${esc(PRONTO_ONE[x.kind] || "Fecha")}</span><span>${esc(SECTORS[x.sector] || "")}</span><span class="when">${esc(when)}</span></div>${x.href ? `<a href="${esc(x.href)}"${x.ext ? ' target="_blank" rel="noopener"' : ""}>${esc(x.title)}</a>` : `<span class="t">${esc(x.title)}</span>`}${x.who ? `<div class="who">${esc(x.who)}</div>` : ""}</div></li>`;
  }
  function viewPronto() {
    const f = S.prontoFilter || (S.prontoFilter = { kind: "", sector: "" });
    const all = prontoItems();
    const cK = {}, cS = {};
    all.forEach((x) => { cS[x.sector] = (cS[x.sector] || 0) + 1; if (!f.sector || x.sector === f.sector) cK[x.kind] = (cK[x.kind] || 0) + 1; });
    const arr = all.filter((x) => (!f.kind || x.kind === f.kind) && (!f.sector || x.sector === f.sector));
    const groups = [["Hoy y mañana", (k) => k <= 1], ["Esta semana", (k) => k > 1 && k <= 7], ["Próximas semanas", (k) => k > 7 && k <= 31], ["Más adelante", (k) => k > 31]];
    let html = `<section class="block"><div class="wrap">${sectionHead("licitaciones", "Sucederá pronto", "", "plazos, consultas, entradas en vigor, eventos e hitos ya anunciados")}<div class="filters">${chips("data-pr-kind", PRONTO_KINDS, f.kind, cK, "Todo")}${chips("data-pr-sector", SECTORS, f.sector, cS, "Todos los sectores")}</div>`;
    let any = false;
    groups.forEach(([label, fn]) => { const g = arr.filter((x) => fn(daysUntil(x.date))); if (!g.length) return; any = true; html += `<div class="lic-block"><div class="lic-head"><h3>${esc(label)} <span>${g.length}</span></h3></div><ul class="pronto-list">${g.map(prontoRow).join("")}</ul></div>`; });
    if (!any) html += emptyBox("No hay fechas próximas con este filtro.");
    html += `<p class="fine">Las fechas proceden de la agenda de la redacción (boletines, convocatorias y organismos) y de los hitos futuros citados en las piezas publicadas, con enlace a su origen.</p>`;
    return html + `</div></section>`;
  }

  // ---------- Logística ----------
  const LOG_MODES = { tierra: "Tierra", mar: "Mar", aire: "Aire" };
  const LOG_SUB = { tierra: "carretera, ferrocarril de mercancías y plataformas", mar: "puertos, navieras y contenedores", aire: "carga aérea y aeropuertos" };
  const logPieces = (m) => sortByRank(published().filter((a) => a.section === "logistica" && (!m || a.mode === m)));
  function viewLogistica() {
    const f = S.logMode || "";
    const cnt = {}; logPieces().forEach((a) => (cnt[a.mode] = (cnt[a.mode] || 0) + 1));
    let html = `<section class="block"><div class="wrap">${sectionHead("logistica", "Logística", "", "transporte de mercancías por tierra, mar y aire")}<div class="filters">${chips("data-log-mode", LOG_MODES, f, cnt, "Los tres modos")}</div>`;
    const modes = f ? [f] : Object.keys(LOG_MODES);
    let any = false;
    modes.forEach((m) => {
      const arr = logPieces(m); if (!arr.length) return; any = true;
      html += `<div class="lic-block"><div class="section-head ${m}"><h2>${esc(LOG_MODES[m])}<small>${esc(LOG_SUB[m])}</small></h2></div><div class="cards reveal">${arr.map((a) => card(a)).join("")}</div></div>`;
    });
    if (!any) html += emptyBox("Sin piezas de logística publicadas todavía." + (S.canEdit ? " Crea una en <b>Administrar → Piezas</b> con la sección «Logística»." : ""));
    return html + `</div></section>`;
  }
  function logisticaPortada(used) {
    const cols = Object.keys(LOG_MODES).map((m) => [m, logPieces(m).filter((a) => !used.has(a.id))]).filter((c) => c[1].length);
    if (!cols.length) return "";
    return `<section class="block"><div class="wrap">${sectionHead("logistica", "Logística", "logistica", "mercancías por tierra, mar y aire")}<div class="log-cols reveal">${cols.map(([m, arr]) => { const l = arr[0]; return `<div class="log-col"><div class="kicker ${m}">${esc(LOG_MODES[m])}</div>${thumb(l)}<h3><a href="#a-${esc(l.id)}">${esc(l.title)}</a></h3><p class="dek">${esc(l.subtitle || "")}</p>${metaLine(l, { noSrc: true })}${arr.length > 1 ? `<ul class="list">${arr.slice(1, 3).map((a) => `<li><div><h3><a href="#a-${esc(a.id)}">${esc(a.title)}</a></h3>${metaLine(a, { noSrc: true })}</div></li>`).join("")}</ul>` : ""}</div>`; }).join("")}</div></div></section>`;
  }

  // ---------- Soluciones tecnológicas ----------
  const SOL_CATS = ["Billetaje y pago", "Operación y SAE", "Información al viajero", "Transporte a la demanda", "Datos y planificación", "Electrificación y energía", "Seguridad y mantenimiento", "Puertos y aeropuertos", "Logística y carga"];
  const SOL_MODES = { tierra: "Tierra", mar: "Mar", aire: "Aire", logistica: "Logística" };
  const solSort = (arr) => arr.slice().sort((a, b) => (b.featured ? 1 : 0) - (a.featured ? 1 : 0) || (+a.priority || 999) - (+b.priority || 999) || String(a.name).localeCompare(String(b.name)));
  const solVisible = () => solSort(S.solutions.filter((s) => s.status === "publicado" || (S.canEdit && s.status !== "oculto")));
  function solCard(s, big) {
    const dep = (s.deployments || [])[0];
    const flags = S.canEdit && s.status !== "publicado" ? `<span class="badge borrador">${esc(s.status || "borrador")}</span>` : "";
    return `<article class="sol ${big ? "big" : ""}">${s.sponsored_by ? `<div class="ad-label">Patrocinado · ${esc(s.sponsored_by)}</div>` : ""}<div class="kicker tecnologia">${esc(s.category || "Tecnología")}</div><h3><a href="#sol-${esc(s.id)}">${esc(s.name)}</a></h3><div class="prov">${esc(s.provider || "")}${s.provider_country ? ` · ${esc(s.provider_country)}` : ""}</div><p>${esc(s.summary || "")}</p>${dep ? `<div class="dep"><b>Implantación</b> ${esc([dep.client, dep.place, dep.year].filter(Boolean).join(" · "))}</div>` : ""}<div class="meta">${(s.modes || []).map((m) => `<span class="badge media">${esc(SOL_MODES[m] || m)}</span>`).join("")}${flags}${S.canEdit ? `<span class="num">prioridad ${esc(s.priority || "–")}</span>` : ""}</div></article>`;
  }
  function viewTecnologia() {
    const cat = S.solCat || "";
    const vis = solVisible();
    const cnt = {}; vis.forEach((s) => (cnt[s.category] = (cnt[s.category] || 0) + 1));
    const opts = {}; SOL_CATS.forEach((c) => (opts[c] = c));
    const arr = vis.filter((s) => !cat || s.category === cat);
    const feat = cat ? [] : arr.filter((s) => s.featured).slice(0, 3);
    const rest = arr.filter((s) => !feat.includes(s));
    let html = `<section class="block"><div class="wrap">${sectionHead("tecnologia", "Soluciones tecnológicas", "", "herramientas con implantaciones reales en transporte y logística")}${S.canEdit ? `<div class="admin-note">Tú decides el orden y lo que sale: <b>Administrar → Tecnología</b>. Las destacadas abren la sección.</div>` : ""}<div class="filters">${chips("data-sol-cat", opts, cat, cnt, "Todas las categorías")}</div>`;
    if (feat.length) html += `<div class="sol-grid feat reveal">${feat.map((s) => solCard(s, true)).join("")}</div>`;
    html += rest.length ? `<div class="sol-grid reveal">${rest.map((s) => solCard(s)).join("")}</div>` : feat.length ? "" : emptyBox("Sin soluciones publicadas en esta categoría.");
    html += `<p class="fine">Selección editorial: cada ficha recoge al menos una implantación verificable con su fuente. Una solución patrocinada se señala como tal y no altera el orden editorial.</p>`;
    return html + `</div></section>`;
  }
  function viewSolucion(id) {
    const s = S.solutions.find((x) => x.id === id);
    if (!s || (!S.canEdit && s.status !== "publicado")) return `<div class="wrap" style="padding:50px 0">${emptyBox("No encontramos esa ficha. <a href='#tecnologia'><b>Ver soluciones</b></a>")}</div>`;
    const srcLi = (x) => `<li><span class="badge src">${esc(x.kind === "oficial" ? "Oficial" : "Medios")}</span><div><a href="${esc(safeUrl(x.url))}" target="_blank" rel="noopener">${esc(x.title || x.outlet || x.url)}</a><div class="meta"><span>${esc(x.outlet || host(x.url))}</span>${x.published ? `<span class="sep">·</span><span>Publicado ${esc(fmtNum(x.published))}</span>` : ""}${x.accessed ? `<span class="sep">·</span><span>Consultado ${esc(fmtNum(x.accessed))}</span>` : ""}</div></div></li>`;
    const related = vis2(s);
    return `<article class="article"><div class="wrap"><a class="back" href="#tecnologia">← Soluciones tecnológicas</a><div class="article-head"><div class="kicker tecnologia">${esc(s.category || "")}</div><h1>${esc(s.name)}</h1><p class="dek">${esc(s.summary || "")}</p><div class="meta"><span><b style="color:var(--ink)">${esc(s.provider || "")}</b>${s.provider_country ? ", " + esc(s.provider_country) : ""}</span>${(s.modes || []).map((m) => `<span class="badge media">${esc(SOL_MODES[m] || m)}</span>`).join("")}${s.sponsored_by ? `<span class="badge sponsored">Patrocinado</span>` : ""}${s.verified_at ? `<span class="sep">·</span><span>Verificado el ${esc(fmtMid(s.verified_at))}</span>` : ""}</div>${S.canEdit ? `<div class="share"><button type="button" data-sol-admin="${esc(s.id)}">Editar esta ficha</button></div>` : ""}</div><div class="article-grid"><div>${s.sponsored_by ? `<div class="sponsored-note">Ficha patrocinada por <b>${esc(s.sponsored_by)}</b>. Comunicación comercial identificada como tal.</div>` : ""}<div class="article-body">${md(s.body_md || "")}</div>${(s.deployments || []).length ? `<div class="quick"><h3>Implantaciones verificadas</h3><div class="quick-grid">${s.deployments.map((d) => `<div class="blk"><h4>${esc([d.client, d.place].filter(Boolean).join(" · "))}${d.year ? ` <span class="num">(${esc(d.year)})</span>` : ""}</h4><p>${esc(d.what || "")}${safeUrl(d.source_url) ? ` <a href="${esc(safeUrl(d.source_url))}" target="_blank" rel="noopener">fuente</a>` : ""}</p></div>`).join("")}</div></div>` : ""}${(s.sources || []).length ? `<div class="sources"><h3>Para saber más</h3><ul>${s.sources.map(srcLi).join("")}</ul></div>` : ""}</div><aside class="aside">${safeUrl(s.url) ? `<div class="box"><h4>Web del producto</h4><p style="font-size:14px"><a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener">${esc(host(s.url))}</a></p></div>` : ""}${related.length ? `<div class="box"><h4>En la misma categoría</h4><ul>${related.map((r) => `<li><a href="#sol-${esc(r.id)}">${esc(r.name)}</a><div class="meta"><span>${esc(r.provider || "")}</span></div></li>`).join("")}</ul></div>` : ""}${(s.tags || []).length ? `<div class="box"><h4>Etiquetas</h4><p style="font-size:13px;color:var(--ink-2)">${s.tags.map(esc).join(" · ")}</p></div>` : ""}</aside></div></div></article>`;
  }
  function vis2(s) { return solVisible().filter((x) => x.id !== s.id && x.category === s.category).slice(0, 4); }
  function tecnologiaPortada() {
    const arr = solVisible().filter((s) => s.status === "publicado").slice(0, 4);
    if (!arr.length) return "";
    return `<section class="block"><div class="wrap">${sectionHead("tecnologia", "Soluciones tecnológicas", "tecnologia", "selección del editor")}<div class="sol-grid four reveal">${arr.map((s) => solCard(s)).join("")}</div></div></section>`;
  }
  function wireFilters() {
    const bind = (attr, fn) => $$(`[${attr}]`).forEach((b) => b.addEventListener("click", () => { fn(b.getAttribute(attr)); render(); }));
    bind("data-lic-fase", (v) => { S.licFilter.fase = v; });
    bind("data-lic-sector", (v) => { S.licFilter.sector = v; });
    bind("data-pr-kind", (v) => { S.prontoFilter.kind = v; });
    bind("data-pr-sector", (v) => { S.prontoFilter.sector = v; });
    bind("data-log-mode", (v) => { S.logMode = v; });
    bind("data-sol-cat", (v) => { S.solCat = v; });
    $$("[data-sol-admin]").forEach((b) => b.addEventListener("click", () => { S.editingSol = S.solutions.find((x) => x.id === b.dataset.solAdmin) || null; openAdmin("tecnologia"); }));
  }

  // ---------- Administración: tecnología ----------
  function listSolAdmin() {
    const arr = solSort(S.solutions);
    return `<div class="toolbar"><button type="button" class="btn" id="new-sol">+ Nueva solución</button><a class="btn secondary" href="#tecnologia" data-close-admin>Ver sección</a></div><div class="admin-note">Ordena con las flechas: lo de arriba sale primero en la sección y en portada (cuatro primeras publicadas). <b>Destacar</b> la abre a tamaño grande. <b>Ocultar</b> la retira sin borrarla.</div><div class="admin-list">${arr.map((s, i) => `<div class="admin-row sol-row"><div class="ord"><button type="button" class="btn small secondary" data-sol-up="${esc(s.id)}" ${i === 0 ? "disabled" : ""} title="Subir">↑</button><b>${i + 1}</b><button type="button" class="btn small secondary" data-sol-down="${esc(s.id)}" ${i === arr.length - 1 ? "disabled" : ""} title="Bajar">↓</button></div><div><div class="t">${esc(s.name)}${s.featured ? " ★" : ""}</div><div class="m"><span class="badge ${s.status === "publicado" ? "media" : "borrador"}">${esc(s.status || "borrador")}</span><span>${esc(s.category || "")}</span><span>·</span><span>${esc(s.provider || "")}</span>${s.sponsored_by ? `<span class="badge sponsored">Patrocinado</span>` : ""}</div></div><div class="actions"><button type="button" class="btn small secondary" data-sol-feat="${esc(s.id)}">${s.featured ? "Quitar destacado" : "Destacar"}</button><button type="button" class="btn small secondary" data-sol-vis="${esc(s.id)}">${s.status === "publicado" ? "Ocultar" : "Publicar"}</button><button type="button" class="btn small secondary" data-sol-edit="${esc(s.id)}">Editar</button><button type="button" class="btn small danger" data-sol-del="${esc(s.id)}">Borrar</button></div></div>`).join("") || `<div class="admin-note">Sin soluciones todavía.</div>`}</div>`;
  }
  function formSol(s) {
    const v = (k) => esc(s[k] == null ? "" : s[k]);
    return `<div class="toolbar"><button type="button" class="btn secondary" id="back-sol">← Volver</button><span style="font-weight:600">${s.id ? "Editar solución" : "Nueva solución"}</span></div>
    <form id="form-sol" class="form-grid">
      <label class="full">Nombre<input type="text" name="name" value="${v("name")}" required></label>
      <label>Proveedor<input type="text" name="provider" value="${v("provider")}"></label>
      <label>País del proveedor<input type="text" name="provider_country" value="${v("provider_country")}"></label>
      <label>Categoría<select name="category">${SOL_CATS.map((c) => `<option ${s.category === c ? "selected" : ""}>${esc(c)}</option>`).join("")}</select></label>
      <label>Estado<select name="status">${["publicado", "borrador", "oculto"].map((k) => `<option value="${k}" ${(s.status || "borrador") === k ? "selected" : ""}>${k}</option>`).join("")}</select></label>
      <label>Prioridad (1 = primero)<input type="number" name="priority" value="${v("priority") || 50}" min="1"></label>
      <label>Destacada<select name="featured"><option value="0" ${!s.featured ? "selected" : ""}>No</option><option value="1" ${s.featured ? "selected" : ""}>Sí</option></select></label>
      <div class="full"><label>Modos</label>${checks("modes", SOL_MODES, s.modes)}</div>
      <label class="full">Resumen (máx. 40 palabras)<textarea name="summary">${v("summary")}</textarea></label>
      <label class="full">Ficha (Markdown)<textarea name="body_md" class="tall">${v("body_md")}</textarea></label>
      <label class="full">Implantaciones (una por línea: cliente | lugar | año | qué | URL de la fuente)<textarea name="deployments">${esc((s.deployments || []).map((d) => [d.client, d.place, d.year, d.what, d.source_url].map((x) => x || "").join(" | ")).join("\n"))}</textarea></label>
      <label class="full">Fuentes (una por línea: oficial|medios | medio | título | URL | AAAA-MM-DD)<textarea name="sources">${esc((s.sources || []).map((x) => [x.kind, x.outlet, x.title, x.url, x.published].map((y) => y || "").join(" | ")).join("\n"))}</textarea></label>
      <label>Web del producto<input type="url" name="url" value="${v("url")}"></label>
      <label>Patrocinada por (vacío = editorial)<input type="text" name="sponsored_by" value="${v("sponsored_by")}"></label>
      <label>Etiquetas (comas)<input type="text" name="tags" value="${esc((s.tags || []).join(", "))}"></label>
      <label>Verificada el<input type="date" name="verified_at" value="${v("verified_at") || todayISO()}"></label>
      <input type="hidden" name="id" value="${v("id")}">
      <div class="full sticky-actions"><button type="button" class="btn secondary" id="back-sol-2">Cancelar</button><button type="submit" class="btn">Guardar</button></div>
    </form>`;
  }
  function wireSolAdmin(c) {
    const on = (sel, ev, fn) => { const el = $(sel, c); if (el) el.addEventListener(ev, fn); };
    on("#new-sol", "click", () => { S.editingSol = { status: "borrador", priority: (S.solutions.length || 0) + 1, category: SOL_CATS[0], modes: ["tierra"] }; renderAdmin(); });
    on("#back-sol", "click", () => { S.editingSol = null; renderAdmin(); });
    on("#back-sol-2", "click", () => { S.editingSol = null; renderAdmin(); });
    $$("[data-sol-edit]", c).forEach((b) => b.addEventListener("click", () => { S.editingSol = S.solutions.find((x) => x.id === b.dataset.solEdit); renderAdmin(); }));
    $$("[data-sol-del]", c).forEach((b) => b.addEventListener("click", () => confirmInline(b, async () => { await S.db.doc("soluciones/" + b.dataset.solDel).delete(); toast("Solución borrada"); })));
    $$("[data-sol-feat]", c).forEach((b) => b.addEventListener("click", async () => { const s = S.solutions.find((x) => x.id === b.dataset.solFeat); if (s) await writeDoc("soluciones/" + s.id, { featured: !s.featured }, true); }));
    $$("[data-sol-vis]", c).forEach((b) => b.addEventListener("click", async () => { const s = S.solutions.find((x) => x.id === b.dataset.solVis); if (s) await writeDoc("soluciones/" + s.id, { status: s.status === "publicado" ? "oculto" : "publicado" }, true); }));
    const move = async (id, dir) => {
      const arr = solSort(S.solutions); const i = arr.findIndex((x) => x.id === id), j = i + dir;
      if (i < 0 || j < 0 || j >= arr.length) return;
      if (!!arr[i].featured !== !!arr[j].featured) { toast("Las destacadas van siempre arriba: quita o pon el destacado para cruzar ese límite", true); return; }
      [arr[i], arr[j]] = [arr[j], arr[i]];
      for (let k = 0; k < arr.length; k++) if (+arr[k].priority !== k + 1) await writeDoc("soluciones/" + arr[k].id, { priority: k + 1 }, true);
    };
    $$("[data-sol-up]", c).forEach((b) => b.addEventListener("click", () => move(b.dataset.solUp, -1)));
    $$("[data-sol-down]", c).forEach((b) => b.addEventListener("click", () => move(b.dataset.solDown, 1)));
    on("#form-sol", "submit", async (e) => {
      e.preventDefault(); const f = e.target; const g = (n) => (f[n] ? f[n].value.trim() : "");
      const existing = g("id"); const id = existing || slugify(g("name")).slice(0, 50);
      if (!existing && S.solutions.find((x) => x.id === id)) { toast("Ya existe una solución con ese nombre", true); return; }
      const prev = existing ? S.solutions.find((x) => x.id === existing) || {} : {};
      const lines = (n) => g(n).split("\n").map((l) => l.trim()).filter(Boolean).map((l) => l.split("|").map((x) => x.trim()));
      const data = Object.assign({}, prev, { id, name: g("name"), provider: g("provider"), provider_country: g("provider_country"), category: g("category"), status: g("status"), priority: +g("priority") || 50, featured: g("featured") === "1", modes: checked(f, "modes"), summary: g("summary"), body_md: g("body_md"),
        deployments: lines("deployments").map((p) => ({ client: p[0] || "", place: p[1] || "", year: p[2] || "", what: p[3] || "", source_url: p[4] || "" })),
        sources: lines("sources").map((p) => ({ kind: p[0] === "oficial" ? "oficial" : "medios", outlet: p[1] || "", title: p[2] || "", url: p[3] || "", published: p[4] || "", accessed: todayISO() })).filter((x) => x.url),
        url: g("url"), sponsored_by: g("sponsored_by"), tags: csv(g("tags")), verified_at: g("verified_at"), updated_at: new Date().toISOString() });
      if (!data.name) { toast("Falta el nombre", true); return; }
      const ok = await writeDoc("soluciones/" + id, data, false); if (ok) { S.editingSol = null; renderAdmin(); }
    });
  }

  // ---------- Tras pintar ----------
  function afterRender() {
    wireMap();
    $$(".reveal").forEach((el) => S.io && S.io.observe(el));
    $$("[data-copy]").forEach((b) => b.addEventListener("click", async () => { const url = location.href.split("#")[0] + "#a-" + b.dataset.copy; try { await navigator.clipboard.writeText(url); toast("Enlace copiado"); } catch (e) { toast(url); } }));
    $$("[data-edit]").forEach((b) => b.addEventListener("click", () => openAdmin("piezas", b.dataset.edit)));
    $$("[data-blog-admin]").forEach((b) => b.addEventListener("click", () => { S.editingBlog = blogById(b.dataset.blogAdmin) || null; openAdmin("blogs"); }));
    $$("[data-blog-post]").forEach((b) => b.addEventListener("click", () => { openAdmin("piezas"); S.editing = newBlogPost(blogById(b.dataset.blogPost)); renderAdmin(); }));
    wireFilters();
    $$("[data-goto-fase]").forEach((b) => b.addEventListener("click", () => { S.licFilter = { fase: b.dataset.gotoFase, sector: "" }; }));
    $$("[data-blog-mail]").forEach((b) => b.addEventListener("click", () => copyBlogNewsletter(b.dataset.blogMail)));
    const onScroll = () => { const el = $("#progress"); if (!el) return; if (!S.route.startsWith("a-")) { el.style.width = "0"; return; } const h = document.documentElement; const p = h.scrollTop / Math.max(1, h.scrollHeight - h.clientHeight); el.style.width = Math.min(100, p * 100) + "%"; };
    window.removeEventListener("scroll", S._scroll); S._scroll = onScroll; window.addEventListener("scroll", onScroll, { passive: true }); onScroll();
  }
  function setupReveal() {
    if (!("IntersectionObserver" in window)) return;
    S.io = new IntersectionObserver((entries) => entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("in"); S.io.unobserve(en.target); } }), { rootMargin: "0px 0px -8% 0px" });
  }

  // ---------- Administración ----------
  function showAdminControls() { $("#admin-fab").classList.add("show"); $("#btn-admin-top").classList.remove("hidden"); $("#admin-who").textContent = S.isOwner ? "Superadministrador (propietario)" : "Editor"; }
  function setupAdminShell() {
    $("#admin-fab").addEventListener("click", () => openAdmin());
    $("#btn-admin-top").addEventListener("click", () => openAdmin());
    $("#drawer-close").addEventListener("click", closeAdmin);
    $("#drawer-scrim").addEventListener("click", closeAdmin);
    $$("#admin-tabs button").forEach((b) => b.addEventListener("click", () => { S.adminTab = b.dataset.tab; S.editing = null; S.editingBlog = null; S.editingAd = null; S.editingSol = null; renderAdmin(); }));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && $("#drawer").classList.contains("open")) closeAdmin(); });
  }
  function openAdmin(tab, editId) { if (!S.canEdit) return; if (tab) S.adminTab = tab; S.editing = editId ? S.articles.find((a) => a.id === editId) || null : null; $("#drawer").classList.add("open"); $("#drawer").setAttribute("aria-hidden", "false"); document.body.style.overflow = "hidden"; renderAdmin(); }
  function closeAdmin() { $("#drawer").classList.remove("open"); $("#drawer").setAttribute("aria-hidden", "true"); document.body.style.overflow = ""; }

  function renderAdmin() {
    $$("#admin-tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === S.adminTab));
    const c = $("#admin-content");
    if (!S.db) { c.innerHTML = `<div class="admin-note">La base de datos no está disponible en esta vista. Abre el portal desde claude.ai con tu cuenta para administrar.</div>`; return; }
    if (S.adminTab === "piezas") c.innerHTML = S.editing !== null && S.editing !== undefined ? formArticle(S.editing) : listArticlesAdmin();
    else if (S.adminTab === "edicion") c.innerHTML = formEdition();
    else if (S.adminTab === "boletines") c.innerHTML = S.editingBol ? formBoletin(S.editingBol) : listBoletinesAdmin();
    else if (S.adminTab === "agenda") c.innerHTML = S.editingAg ? formAgenda(S.editingAg) : listAgendaAdmin();
    else if (S.adminTab === "blogs") c.innerHTML = S.editingBlog ? formBlog(S.editingBlog) : listBlogsAdmin();
    else if (S.adminTab === "publicidad") c.innerHTML = S.editingAd ? formAd(S.editingAd) : listAdsAdmin();
    else if (S.adminTab === "tecnologia") c.innerHTML = S.editingSol ? formSol(S.editingSol) : listSolAdmin();
    wireAdmin();
  }

  function listArticlesAdmin() {
    const f = S.adminFilter;
    let arr = S.articles.filter((a) => (!f.q || (a.title + " " + a.subtitle + " " + a.kicker).toLowerCase().includes(f.q.toLowerCase())) && (!f.kind || a.kind === f.kind) && (!f.status || (a.status || "publicado") === f.status) && (!f.section || a.section === f.section));
    arr = sortByDate(arr);
    return `<div class="toolbar"><button type="button" class="btn" id="new-article">+ Nueva pieza</button><button type="button" class="btn secondary" id="new-analysis">+ Nuevo análisis</button><input type="search" id="f-q" placeholder="Buscar en títulos…" value="${esc(f.q)}" style="max-width:260px"><select id="f-section"><option value="">Todas las secciones</option>${Object.keys(SECTION_NAMES).map((k) => `<option value="${k}" ${f.section === k ? "selected" : ""}>${SECTION_NAMES[k]}</option>`).join("")}</select><select id="f-status"><option value="">Publicadas y borradores</option><option value="publicado" ${f.status === "publicado" ? "selected" : ""}>Publicadas</option><option value="borrador" ${f.status === "borrador" ? "selected" : ""}>Borradores</option></select></div><div class="admin-note">${arr.length} piezas. Destacar: <b>1</b> = apertura de portada, <b>2</b> = secundaria. Los cambios se publican al instante para quien tenga acceso a la página.</div><div class="admin-list">${arr.map((a) => `<div class="admin-row"><img src="${esc(imgSrc(a) || artSvg(a.section, a.id))}" alt=""><div><div class="t">${esc(a.title)}</div><div class="m"><span class="badge ${a.status === "borrador" ? "borrador" : "media"}">${esc(a.status || "publicado")}</span><span>${esc(a.kind === "analisis" ? "Análisis" : a.kind === "reportaje" ? "Reportaje" : a.kind === "blog" ? "Blog · " + ((blogById(a.blog_id) || {}).name || "sin blog") : "Noticia")}</span>${a.sponsored_by ? `<span class="badge sponsored">Patrocinado</span>` : ""}<span>·</span><span>${esc(SECTION_NAMES[a.section] || a.section || "")}</span><span>·</span><span>${esc(fmtShort(a.date))}</span>${a.featured ? `<span>· Destacada ${a.featured}</span>` : ""}</div></div><div class="actions"><button type="button" class="btn small secondary" data-a-edit="${esc(a.id)}">Editar</button><button type="button" class="btn small secondary" data-a-toggle="${esc(a.id)}">${a.status === "borrador" ? "Publicar" : "Retirar"}</button><button type="button" class="btn small danger" data-a-del="${esc(a.id)}">Borrar</button></div></div>`).join("")}</div>`;
  }

  function formArticle(a) {
    const isNew = !a.id;
    const v = (k) => esc(a[k] == null ? "" : a[k]);
    const srcRows = (a.sources && a.sources.length ? a.sources : [{ kind: "oficial" }, { kind: "medios" }]).map((s, i) => srcRow(s, i)).join("");
    const isAn = a.kind === "analisis";
    return `<div class="toolbar"><button type="button" class="btn secondary" id="back-list">← Volver a la lista</button><span style="font-weight:600">${isNew ? "Nueva pieza" : "Editar pieza"}</span></div>
    <form id="form-article" class="form-grid">
      <label>Tipo<select name="kind"><option value="noticia" ${!isAn && a.kind !== "reportaje" && a.kind !== "blog" ? "selected" : ""}>Noticia</option><option value="analisis" ${isAn ? "selected" : ""}>Análisis de fondo</option><option value="reportaje" ${a.kind === "reportaje" ? "selected" : ""}>Reportaje</option><option value="blog" ${a.kind === "blog" ? "selected" : ""}>Entrada de blog</option></select></label>
      <label>Blog (solo entradas de blog)<select name="blog_id"><option value="">—</option>${S.blogs.map((b) => `<option value="${esc(b.id)}" ${a.blog_id === b.id ? "selected" : ""}>${esc(b.name)}</option>`).join("")}</select></label>
      <label>Sección<select name="section">${["tierra", "mar", "aire", "logistica", "regulacion", "licitaciones", "tecnologia"].map((k) => `<option value="${k}" ${a.section === k ? "selected" : ""}>${SECTION_NAMES[k]}</option>`).join("")}</select></label>
      <label>Modo (solo logística)<select name="mode"><option value="">—</option>${Object.keys(LOG_MODES).map((k) => `<option value="${k}" ${a.mode === k ? "selected" : ""}>${LOG_MODES[k]}</option>`).join("")}</select></label>
      <label>Fase (licitaciones)<select name="fase"><option value="">Automática</option>${Object.keys(LIC_FASES).map((k) => `<option value="${k}" ${a.fase === k ? "selected" : ""}>${LIC_FASE_SHORT[k]}</option>`).join("")}</select></label>
      <label>Sector<select name="sector"><option value="">Automático</option>${Object.keys(SECTORS).map((k) => `<option value="${k}" ${a.sector === k ? "selected" : ""}>${SECTORS[k]}</option>`).join("")}</select></label>
      <label>Tema general y sector (antetítulo)<input type="text" name="kicker" value="${v("kicker")}" placeholder="Concesiones · Autobús interurbano"></label>
      <label>Subsector<input type="text" name="subsector" value="${v("subsector")}" placeholder="autobús, ferrocarril, aeropuertos…"></label>
      <label class="full">Título<input type="text" name="title" value="${v("title")}" required></label>
      <label class="full">Subtítulo<input type="text" name="subtitle" value="${v("subtitle")}"></label>
      <label>Fecha de edición<input type="date" name="date" value="${v("date") || todayISO()}"></label>
      <label>Fecha de los hechos<input type="date" name="event_date" value="${v("event_date")}"></label>
      <label>Relevancia<select name="relevance"><option value="ALTA" ${a.relevance === "ALTA" ? "selected" : ""}>ALTA</option><option value="MEDIA" ${a.relevance !== "ALTA" ? "selected" : ""}>MEDIA</option></select></label>
      <label>Estado<select name="status"><option value="publicado" ${a.status !== "borrador" ? "selected" : ""}>Publicado</option><option value="borrador" ${a.status === "borrador" ? "selected" : ""}>Borrador</option></select></label>
      <label>Destacar en portada<select name="featured"><option value="0" ${!a.featured ? "selected" : ""}>No</option><option value="1" ${a.featured === 1 ? "selected" : ""}>1 · Apertura</option><option value="2" ${a.featured === 2 ? "selected" : ""}>2 · Secundaria</option></select></label>
      <label>Autor<input type="text" name="author" value="${v("author")}" placeholder="Rainer"></label>
      <label>Cargo o firma<input type="text" name="author_role" value="${v("author_role")}" placeholder="Director de MOTICIAS"></label>
      <label>Contenido patrocinado por (vacío = editorial)<input type="text" name="sponsored_by" value="${v("sponsored_by")}" placeholder="Nombre del patrocinador"></label>
      <label>Web del patrocinador<input type="url" name="sponsor_url" value="${v("sponsor_url")}" placeholder="https://…"></label>
      <label class="full">Nota del autor (declaración de intereses)<input type="text" name="author_note" value="${v("author_note")}"></label>
      <label class="full">Dato clave<input type="text" name="key_fact" value="${v("key_fact")}" placeholder="Una cifra con su unidad"></label>
      <label class="full">De qué trata (resumen)<textarea name="summary">${v("summary")}</textarea></label>
      <label class="full">Quiénes son los protagonistas<textarea name="actors">${v("actors")}</textarea></label>
      <label class="full">Para quién es relevante<textarea name="relevance_for">${v("relevance_for")}</textarea></label>
      <label class="full">Por qué es importante<textarea name="why">${v("why")}</textarea></label>
      <label class="full">Qué puede pasar ahora<textarea name="next">${v("next")}</textarea></label>
      <label class="full">Cuerpo del artículo (Markdown; el reportaje de fondo)<span class="help">## Título de apartado · **negrita** · *cursiva* · &gt; cita · &gt;&gt; destacado · - lista · [texto](https://enlace)</span><textarea name="body_md" class="tall">${v("body_md")}</textarea></label>
      <label class="full">Cifras clave (una por línea: etiqueta | valor | fuente)<textarea name="key_data">${esc((a.key_data || []).map((k) => [k.label || "", k.value || "", k.source || ""].join(" | ")).join("\n"))}</textarea></label>
      <label class="full">Cronología (una por línea: AAAA-MM-DD | texto)<textarea name="timeline">${esc((a.timeline || []).map((t) => [t.date || "", t.text || ""].join(" | ")).join("\n"))}</textarea></label>
      <div class="full"><label>Imagen</label><div class="img-field" style="margin-top:6px"><div class="preview" id="img-preview">${imgSrc(a) ? `<img src="${esc(imgSrc(a))}" alt="">` : "Sin imagen"}</div><div class="controls"><input type="file" id="img-file" accept="image/*" ${S.assets ? "" : "disabled"}><span class="help" style="font-size:12px;color:var(--muted)">${S.assets ? "Sube una foto desde tu dispositivo (máx. 20 MB)." : "La subida de archivos no está disponible en esta vista; indica una URL o ruta."}</span><input type="text" name="image_src" placeholder="URL o ruta de la imagen" value="${esc((a.image && a.image.src) || "")}"><input type="hidden" name="image_assetId" value="${esc((a.image && a.image.assetId) || "")}"><input type="text" name="image_alt" placeholder="Texto alternativo / pie" value="${esc((a.image && a.image.alt) || "")}"><input type="text" name="image_credit" placeholder="Crédito (autor)" value="${esc((a.image && a.image.credit) || "")}"><input type="text" name="image_license" placeholder="Licencia (CC BY 2.0, propia…)" value="${esc((a.image && a.image.license) || "")}"><input type="text" name="image_source" placeholder="URL de origen de la foto" value="${esc((a.image && a.image.source) || "")}"><button type="button" class="btn small secondary" id="img-clear">Quitar imagen</button></div></div></div>
      <div class="full"><label>Lugar (para el mapa)</label><div class="form-grid three" style="margin-top:6px"><input type="text" name="geo_place" placeholder="Ciudad o región" value="${esc((a.geo && a.geo.place) || "")}"><input type="number" step="any" name="geo_lat" placeholder="Latitud" value="${esc(a.geo && a.geo.lat != null ? a.geo.lat : "")}"><input type="number" step="any" name="geo_lon" placeholder="Longitud" value="${esc(a.geo && a.geo.lon != null ? a.geo.lon : "")}"></div></div>
      <div class="full"><label>Para saber más (fuentes)</label><div id="src-rows" style="margin-top:6px">${srcRows}</div><button type="button" class="btn small secondary" id="src-add">+ Añadir fuente</button></div>
      <label class="full">Etiquetas (separadas por comas)<input type="text" name="tags" value="${esc((a.tags || []).join(", "))}"></label>
      <label class="full">Ámbito del análisis (solo análisis)<input type="text" name="scope" value="${v("scope")}" placeholder="tierra, mar, aire, regulacion, urbano, infraestructuras…"></label>
      <input type="hidden" name="id" value="${v("id")}">
      <div class="full sticky-actions"><button type="button" class="btn secondary" id="back-list-2">Cancelar</button><button type="submit" class="btn" id="save-article">Guardar</button></div>
    </form>`;
  }
  function srcRow(s, i) {
    return `<div class="src-row" data-i="${i}"><select name="s_kind"><option value="oficial" ${s.kind === "oficial" ? "selected" : ""}>Oficial</option><option value="medios" ${s.kind !== "oficial" ? "selected" : ""}>Medios</option></select><input type="text" name="s_outlet" placeholder="Organismo o medio" value="${esc(s.outlet || "")}"><input type="text" name="s_title" placeholder="Título de la página" value="${esc(s.title || "")}"><input type="url" name="s_url" placeholder="https://…" value="${esc(s.url || "")}"><input type="date" name="s_published" value="${esc(s.published || "")}" title="Fecha de publicación"><button type="button" class="src-del" title="Quitar">×</button></div>`;
  }

  function formEdition() {
    const e = S.edition || {}; const d = e.document || {};
    const an = sortByDate(analyses()), nw = sortByRank(news());
    return `<form id="form-edition" class="form-grid">
      <label>Fecha de la edición<input type="date" name="date" value="${esc(e.date || todayISO())}"></label>
      <label>Número<input type="number" name="number" value="${esc(e.number || 1)}"></label>
      <label>Hora de cierre (CET)<input type="text" name="closed_at" value="${esc(e.closed_at || "07:30")}" placeholder="07:30"></label>
      <label>Apertura de portada<select name="lead_id"><option value="">Automática (destacada 1 o la primera ALTA)</option>${nw.map((a) => `<option value="${esc(a.id)}" ${e.lead_id === a.id ? "selected" : ""}>${esc(a.title)}</option>`).join("")}</select></label>
      <label class="full">Análisis del día<select name="analysis_id"><option value="">Automático (el más reciente)</option>${an.map((a) => `<option value="${esc(a.id)}" ${e.analysis_id === a.id ? "selected" : ""}>${esc(a.title)}</option>`).join("")}</select></label>
      <label class="full">Nota metodológica (se muestra en “Cómo trabajamos”)<textarea name="note_metodologica">${esc(e.note_metodologica || "")}</textarea></label>
      <div class="full"><label>El documento del día</label><div class="form-grid" style="margin-top:6px"><input type="text" name="doc_kicker" placeholder="Antetítulo (p. ej. Licitación · Adif)" value="${esc(d.kicker || "")}"><input type="text" name="doc_ref" placeholder="Referencia (BOE-B-2026-…)" value="${esc(d.ref || "")}"><input type="text" name="doc_title" class="full" placeholder="Título del documento" value="${esc(d.title || "")}" style="grid-column:1/-1"><textarea name="doc_summary" placeholder="Qué es y por qué merece leerse" style="grid-column:1/-1">${esc(d.summary || "")}</textarea><input type="url" name="doc_url" placeholder="https://…" value="${esc(d.url || "")}"><input type="date" name="doc_date" value="${esc(d.date || "")}"><input type="text" name="doc_source" placeholder="Fuente (BOE, DOUE, Adif…)" value="${esc(d.source || "")}"></div></div>
      <div class="full sticky-actions"><button type="submit" class="btn">Guardar edición</button></div>
    </form>`;
  }

  function listBoletinesAdmin() {
    const rows = S.boletines.slice(0, 300);
    return `<div class="toolbar"><button type="button" class="btn" id="new-bol">+ Nueva referencia</button><span class="help" style="font-size:13px;color:var(--muted)">${S.boletines.length} referencias. El barrido diario las añade automáticamente.</span></div><div class="admin-list">${rows.map((b) => `<div class="admin-row" style="grid-template-columns:1fr auto"><div><div class="t" style="font-size:14px">${esc(b.titulo)}</div><div class="m"><span>${esc(fmtNum(b.fecha))}</span><span>·</span><span>${esc(b.referencia || "")}</span><span>·</span><span>${esc(b.tipo || "")}</span><span>·</span><span>${(b.modos || []).join(", ")}</span></div></div><div class="actions"><button type="button" class="btn small secondary" data-b-edit="${esc(b.id)}">Editar</button><button type="button" class="btn small danger" data-b-del="${esc(b.id)}">Borrar</button></div></div>`).join("")}</div>`;
  }
  function formBoletin(b) {
    const v = (k) => esc(b[k] == null ? "" : b[k]);
    return `<div class="toolbar"><button type="button" class="btn secondary" id="back-bol">← Volver</button></div><form id="form-bol" class="form-grid">
      <label>Fecha<input type="date" name="fecha" value="${v("fecha") || todayISO()}"></label>
      <label>Boletín<input type="text" name="boletin" value="${v("boletin") || "BOE"}"></label>
      <label>Referencia<input type="text" name="referencia" value="${v("referencia")}" placeholder="BOE-A-2026-…"></label>
      <label>Código de sección<input type="text" name="seccion_codigo" value="${v("seccion_codigo")}" placeholder="1, 3, 5A, 5B"></label>
      <label class="full">Órgano<input type="text" name="organo" value="${v("organo")}"></label>
      <label class="full">Título<textarea name="titulo">${v("titulo")}</textarea></label>
      <label class="full">Título corto (teletipo)<input type="text" name="titulo_corto" value="${v("titulo_corto")}"></label>
      <label>Tipo<input type="text" name="tipo" value="${v("tipo")}" placeholder="real decreto, resolución, anuncio de licitación…"></label>
      <label>Fase (licitaciones)<select name="fase"><option value="">Automática</option>${Object.keys(LIC_FASES).map((k) => `<option value="${k}" ${b.fase === k ? "selected" : ""}>${LIC_FASE_SHORT[k]}</option>`).join("")}</select></label>
      <label>Sector<select name="sector"><option value="">Automático</option>${Object.keys(SECTORS).map((k) => `<option value="${k}" ${b.sector === k ? "selected" : ""}>${SECTORS[k]}</option>`).join("")}</select></label>
      <label>Modos (coma)<input type="text" name="modos" value="${esc((b.modos || []).join(", "))}" placeholder="tierra, mar, aire"></label>
      <label class="full">URL<input type="url" name="url" value="${v("url")}"></label>
      <label class="full">Nota editorial<input type="text" name="nota" value="${v("nota")}"></label>
      <input type="hidden" name="id" value="${v("id")}">
      <div class="full sticky-actions"><button type="submit" class="btn">Guardar</button></div></form>`;
  }
  function listAgendaAdmin() {
    return `<div class="toolbar"><button type="button" class="btn" id="new-ag">+ Nueva fecha</button></div><div class="admin-list">${S.agenda.map((d) => `<div class="admin-row" style="grid-template-columns:1fr auto"><div><div class="t" style="font-size:14px">${esc(d.title)}</div><div class="m"><span>${esc(fmtNum(d.date))}</span><span>·</span><span>${esc(d.kind || "")}</span><span>·</span><span>${esc(d.authority || "")}</span></div></div><div class="actions"><button type="button" class="btn small secondary" data-g-edit="${esc(d.id)}">Editar</button><button type="button" class="btn small danger" data-g-del="${esc(d.id)}">Borrar</button></div></div>`).join("")}</div>`;
  }
  function formAgenda(d) {
    const v = (k) => esc(d[k] == null ? "" : d[k]);
    return `<div class="toolbar"><button type="button" class="btn secondary" id="back-ag">← Volver</button></div><form id="form-ag" class="form-grid">
      <label>Fecha<input type="date" name="date" value="${v("date") || todayISO()}"></label>
      <label>Tipo<select name="kind">${["plazo", "consulta", "vigor", "evento"].map((k) => `<option value="${k}" ${d.kind === k ? "selected" : ""}>${({ plazo: "Plazo de licitación", consulta: "Consulta / audiencia", vigor: "Entrada en vigor", evento: "Evento" })[k]}</option>`).join("")}</select></label>
      <label class="full">Título<input type="text" name="title" value="${v("title")}"></label>
      <label>Órgano<input type="text" name="authority" value="${v("authority")}"></label>
      <label>Importe (texto)<input type="text" name="amount" value="${v("amount")}" placeholder="51,5 M€"></label>
      <label>Importe en euros (número)<input type="number" name="amount_eur" value="${v("amount_eur")}"></label>
      <label>Modo<input type="text" name="mode" value="${v("mode")}" placeholder="tierra, mar, aire"></label>
      <label class="full">URL<input type="url" name="url" value="${v("url")}"></label>
      <input type="hidden" name="id" value="${v("id")}">
      <div class="full sticky-actions"><button type="submit" class="btn">Guardar</button></div></form>`;
  }

  function wireAdmin() {
    const c = $("#admin-content");
    const on = (sel, ev, fn) => { const el = $(sel, c); if (el) el.addEventListener(ev, fn); };
    on("#new-article", "click", () => { S.editing = { kind: "noticia", section: "tierra", status: "publicado", relevance: "MEDIA", author: "Redacción" }; renderAdmin(); });
    on("#new-analysis", "click", () => { S.editing = { kind: "analisis", section: "regulacion", status: "publicado", relevance: "ALTA", author: "Rainer", author_role: "Director de MOTICIAS", kicker: "Análisis" }; renderAdmin(); });
    on("#f-q", "input", (e) => { S.adminFilter.q = e.target.value; renderAdmin(); $("#f-q", c).focus(); const el = $("#f-q", c); el.setSelectionRange(el.value.length, el.value.length); });
    on("#f-section", "change", (e) => { S.adminFilter.section = e.target.value; renderAdmin(); });
    on("#f-status", "change", (e) => { S.adminFilter.status = e.target.value; renderAdmin(); });
    on("#back-list", "click", () => { S.editing = null; renderAdmin(); });
    on("#back-list-2", "click", () => { S.editing = null; renderAdmin(); });
    $$("[data-a-edit]", c).forEach((b) => b.addEventListener("click", () => { S.editing = S.articles.find((a) => a.id === b.dataset.aEdit); renderAdmin(); }));
    $$("[data-a-toggle]", c).forEach((b) => b.addEventListener("click", async () => { const a = S.articles.find((x) => x.id === b.dataset.aToggle); if (!a) return; await writeDoc("articles/" + a.id, { status: a.status === "borrador" ? "publicado" : "borrador", updated_at: todayISO() }, true); }));
    $$("[data-a-del]", c).forEach((b) => b.addEventListener("click", () => confirmInline(b, async () => { await S.db.doc("articles/" + b.dataset.aDel).delete(); toast("Pieza borrada"); })));
    on("#src-add", "click", () => { const rows = $("#src-rows", c); rows.insertAdjacentHTML("beforeend", srcRow({ kind: "medios" }, rows.children.length)); wireSrcDel(); });
    wireSrcDel();
    on("#img-clear", "click", () => { const f = $("#form-article", c); f.image_src.value = ""; f.image_assetId.value = ""; $("#img-preview", c).textContent = "Sin imagen"; });
    on("#img-file", "change", async (e) => {
      const file = e.target.files && e.target.files[0]; if (!file || !S.assets) return;
      try { toast("Subiendo imagen…"); const res = await S.assets.upload(file); const f = $("#form-article", c); f.image_assetId.value = res.id; f.image_src.value = res.url || ("/_blob/" + res.id); $("#img-preview", c).innerHTML = `<img src="${esc(f.image_src.value)}" alt="">`; toast("Imagen subida"); }
      catch (err) { console.error(err); toast("No se pudo subir la imagen: " + (err && err.message ? err.message : "error"), true); }
    });
    on("#form-article", "submit", async (e) => {
      e.preventDefault();
      const f = e.target; const g = (n) => (f[n] ? f[n].value.trim() : "");
      const existing = g("id");
      const id = existing || slugify(g("title")) + "-" + Date.now().toString(36).slice(-4);
      const prev = existing ? S.articles.find((a) => a.id === existing) || {} : {};
      const sources = $$(".src-row", f).map((r) => ({ kind: $("[name=s_kind]", r).value, outlet: $("[name=s_outlet]", r).value.trim(), title: $("[name=s_title]", r).value.trim(), url: $("[name=s_url]", r).value.trim(), published: $("[name=s_published]", r).value, accessed: todayISO() })).filter((s) => s.url || s.title);
      const lines = (n) => g(n).split("\n").map((l) => l.trim()).filter(Boolean);
      const key_data = lines("key_data").map((l) => { const p = l.split("|").map((x) => x.trim()); return { label: p[0] || "", value: p[1] || "", source: p[2] || "" }; }).filter((k) => k.value);
      const timeline = lines("timeline").map((l) => { const i = l.indexOf("|"); return i < 0 ? { date: "", text: l } : { date: l.slice(0, i).trim(), text: l.slice(i + 1).trim() }; }).filter((t) => t.text);
      const data = Object.assign({}, prev, {
        id, kind: g("kind"), section: g("section"), kicker: g("kicker"), subsector: g("subsector"), title: g("title"), subtitle: g("subtitle"), date: g("date") || todayISO(), event_date: g("event_date") || null,
        relevance: g("relevance"), status: g("status"), featured: +g("featured") || 0, author: g("author"), author_role: g("author_role"), author_note: g("author_note"), key_fact: g("key_fact"),
        sponsored_by: g("sponsored_by"), sponsor_url: g("sponsor_url"), mode: g("section") === "logistica" ? g("mode") || "tierra" : (prev.mode || null), fase: g("fase") || null, sector: g("sector") || null, blog_id: g("kind") === "blog" ? g("blog_id") || null : null,
        summary: g("summary"), actors: g("actors"), relevance_for: g("relevance_for"), why: g("why"), next: g("next"), body_md: g("body_md"), scope: g("scope"), key_data, timeline,
        tags: g("tags").split(",").map((t) => t.trim()).filter(Boolean), sources,
        image: g("image_src") || g("image_assetId") ? { src: g("image_src"), assetId: g("image_assetId"), alt: g("image_alt"), credit: g("image_credit"), license: g("image_license"), source: g("image_source") } : null,
        geo: g("geo_lat") && g("geo_lon") ? { place: g("geo_place"), lat: +g("geo_lat"), lon: +g("geo_lon") } : null,
        published_at: prev.published_at || (g("date") || todayISO()) + "T07:30:00+01:00", updated_at: existing ? todayISO() : null, created_by: "admin",
      });
      if (!data.title) { toast("Falta el título", true); return; }
      if (data.kind === "blog" && !data.blog_id) { toast("Elige el blog de esta entrada", true); return; }
      if (data.kind === "blog" && !data.kicker) data.kicker = (blogById(data.blog_id) || {}).name || "";
      if (data.featured === 1) { // sólo una apertura
        for (const a of S.articles) if (a.featured === 1 && a.id !== id) await writeDoc("articles/" + a.id, { featured: 0 }, true);
      }
      const ok = await writeDoc("articles/" + id, data, false);
      if (ok) { S.editing = null; renderAdmin(); if (!existing) location.hash = "#a-" + id; }
    });
    on("#form-edition", "submit", async (e) => {
      e.preventDefault(); const f = e.target; const g = (n) => (f[n] ? f[n].value.trim() : "");
      const date = g("date") || todayISO();
      const data = { date, number: +g("number") || 1, closed_at: g("closed_at"), lead_id: g("lead_id"), analysis_id: g("analysis_id"), note_metodologica: g("note_metodologica"), document: g("doc_title") ? { kicker: g("doc_kicker"), ref: g("doc_ref"), title: g("doc_title"), summary: g("doc_summary"), url: g("doc_url"), date: g("doc_date"), source: g("doc_source") } : null, updated_at: new Date().toISOString() };
      const ok = await writeDoc("editions/" + date, data, false); if (ok) toast("Edición guardada");
    });
    on("#new-bol", "click", () => { S.editingBol = { boletin: "BOE", fecha: todayISO() }; renderAdmin(); });
    on("#back-bol", "click", () => { S.editingBol = null; renderAdmin(); });
    $$("[data-b-edit]", c).forEach((b) => b.addEventListener("click", () => { S.editingBol = S.boletines.find((x) => x.id === b.dataset.bEdit); renderAdmin(); }));
    $$("[data-b-del]", c).forEach((b) => b.addEventListener("click", () => confirmInline(b, async () => { await S.db.doc("boletines/" + b.dataset.bDel).delete(); toast("Referencia borrada"); })));
    on("#form-bol", "submit", async (e) => {
      e.preventDefault(); const f = e.target; const g = (n) => (f[n] ? f[n].value.trim() : "");
      const id = g("id") || slugify(g("referencia") || g("titulo")).slice(0, 60) + "-" + Date.now().toString(36).slice(-4);
      const data = { id, fecha: g("fecha"), boletin: g("boletin"), referencia: g("referencia"), seccion_codigo: g("seccion_codigo"), organo: g("organo"), titulo: g("titulo"), titulo_corto: g("titulo_corto"), tipo: g("tipo"), modos: g("modos").split(",").map((t) => t.trim()).filter(Boolean), url: g("url"), nota: g("nota"), fase: g("fase") || null, sector: g("sector") || null };
      const ok = await writeDoc("boletines/" + id, data, false); if (ok) { S.editingBol = null; renderAdmin(); }
    });
    on("#new-ag", "click", () => { S.editingAg = { kind: "plazo", date: todayISO() }; renderAdmin(); });
    on("#back-ag", "click", () => { S.editingAg = null; renderAdmin(); });
    $$("[data-g-edit]", c).forEach((b) => b.addEventListener("click", () => { S.editingAg = S.agenda.find((x) => x.id === b.dataset.gEdit); renderAdmin(); }));
    $$("[data-g-del]", c).forEach((b) => b.addEventListener("click", () => confirmInline(b, async () => { await S.db.doc("agenda/" + b.dataset.gDel).delete(); toast("Fecha borrada"); })));
    on("#form-ag", "submit", async (e) => {
      e.preventDefault(); const f = e.target; const g = (n) => (f[n] ? f[n].value.trim() : "");
      const id = g("id") || slugify(g("title")).slice(0, 60) + "-" + Date.now().toString(36).slice(-4);
      const data = { id, date: g("date"), kind: g("kind"), title: g("title"), authority: g("authority"), amount: g("amount"), amount_eur: +g("amount_eur") || null, mode: g("mode"), url: g("url") };
      const ok = await writeDoc("agenda/" + id, data, false); if (ok) { S.editingAg = null; renderAdmin(); }
    });
    wireAdmin2(c);
    wireSolAdmin(c);
  }
  // ---------- Administración: blogs ----------
  const checks = (name, opts, sel) => `<div class="checks">${Object.keys(opts).map((k) => `<label class="chk"><input type="checkbox" name="${name}" value="${esc(k)}" ${(sel || []).includes(k) ? "checked" : ""}> ${esc(opts[k])}</label>`).join("")}</div>`;
  const imgField = (prefix, im, help) => `<div class="img-field" style="margin-top:6px"><div class="preview" id="${prefix}-preview">${im && (im.src || im.assetId) ? `<img src="${esc(im.src || "/_blob/" + im.assetId)}" alt="">` : "Sin imagen"}</div><div class="controls"><input type="file" accept="image/*" data-upload="${prefix}" ${S.assets ? "" : "disabled"}><span class="help" style="font-size:12px;color:var(--muted)">${esc(help || (S.assets ? "Sube una imagen desde tu dispositivo." : "Indica una URL o ruta."))}</span><input type="text" name="${prefix}_src" placeholder="URL o ruta de la imagen" value="${esc((im && im.src) || "")}"><input type="hidden" name="${prefix}_assetId" value="${esc((im && im.assetId) || "")}"><input type="text" name="${prefix}_alt" placeholder="Texto alternativo" value="${esc((im && im.alt) || "")}"><input type="text" name="${prefix}_credit" placeholder="Crédito" value="${esc((im && im.credit) || "")}"><button type="button" class="btn small secondary" data-img-clear="${prefix}">Quitar imagen</button></div></div>`;
  const readImg = (f, prefix) => { const src = f[prefix + "_src"].value.trim(), id = f[prefix + "_assetId"].value.trim(); return src || id ? { src, assetId: id, alt: f[prefix + "_alt"].value.trim(), credit: f[prefix + "_credit"].value.trim() } : null; };
  const checked = (f, name) => $$(`[name="${name}"]`, f).filter((x) => x.checked).map((x) => x.value);
  const csv = (s) => String(s || "").split(",").map((x) => x.trim()).filter(Boolean);
  const eur = (n) => (n == null || n === "" || isNaN(n) ? "" : Number(n).toLocaleString("es-ES", { maximumFractionDigits: 0 }) + " €");
  function newBlogPost(b) { return { kind: "blog", blog_id: b ? b.id : "", section: (b && b.filters && (b.filters.sections || [])[0]) || "tierra", status: "borrador", relevance: "MEDIA", author: (b && b.author) || "Rainer", author_role: (b && b.author_role) || "", kicker: b ? b.name : "" }; }

  function listBlogsAdmin() {
    const arr = S.blogs.slice().sort((a, b) => (a.order || 99) - (b.order || 99) || String(a.name).localeCompare(String(b.name)));
    return `<div class="toolbar"><button type="button" class="btn" id="new-blog">+ Nuevo blog o edición</button><a class="btn secondary" href="#blogs" id="see-blogs">Ver página pública</a></div><div class="admin-note">Cada blog tiene portada, color, logotipo, diseño y módulos propios. Puede llevar entradas escritas a mano y una <b>selección automática</b> de piezas de MOTICIAS según filtros (secciones, subsectores, palabras clave). Las ediciones <b>«solo con enlace»</b> no aparecen en el índice: sirven para versiones privadas de asociaciones o empresas.</div><div class="admin-list">${arr.length ? arr.map((b) => { const n = blogPosts(b.id, true).length; return `<div class="admin-row"><span class="swatch" style="background:${esc(safeColor(b.accent) || "#0b2545")}">${blogLogo(b)}</span><div><div class="t">${esc(b.name)}</div><div class="m"><span class="badge ${b.status === "borrador" ? "borrador" : "media"}">${esc(b.status || "publicado")}</span><span>${esc(BLOG_TYPES[b.type] || "Blog")}</span><span>·</span><span>${b.visibility === "oculto" ? "solo con enlace" : "en el índice"}</span><span>·</span><span>${n} entradas</span><span>·</span><span>${blogFeed(b).length} automáticas</span></div></div><div class="actions"><a class="btn small secondary" href="#blog-${esc(blogSlug(b))}" data-close-admin>Ver</a><button type="button" class="btn small secondary" data-bl-post="${esc(b.id)}">+ Entrada</button><button type="button" class="btn small secondary" data-bl-edit="${esc(b.id)}">Editar</button><button type="button" class="btn small danger" data-bl-del="${esc(b.id)}">Borrar</button></div></div>`; }).join("") : `<div class="admin-note">Todavía no hay blogs.</div>`}</div>`;
  }
  function formBlog(b) {
    const isNew = !b.id;
    const v = (k) => esc(b[k] == null ? "" : b[k]);
    const f = b.filters || {}, m = Object.assign({ posts: true, feed: true, plazos: false, boletines: false, contacto: false }, b.modules || {});
    const posts = b.id ? blogPosts(b.id, true) : [];
    return `<div class="toolbar"><button type="button" class="btn secondary" id="back-blogs">← Volver a blogs</button><span style="font-weight:600">${isNew ? "Nuevo blog o edición" : "Editar blog"}</span>${b.id ? `<button type="button" class="btn small secondary" data-bl-post="${esc(b.id)}">+ Nueva entrada</button>` : ""}</div>
    <form id="form-blog" class="form-grid">
      <label class="full">Nombre<input type="text" name="name" value="${v("name")}" required placeholder="Cuaderno del director"></label>
      <label>Dirección (slug)<input type="text" name="slug" value="${v("slug")}" placeholder="se genera desde el nombre" ${b.id ? "readonly" : ""}></label>
      <label>Tipo<select name="type">${Object.keys(BLOG_TYPES).map((k) => `<option value="${k}" ${b.type === k ? "selected" : ""}>${BLOG_TYPES[k]}</option>`).join("")}</select></label>
      <label>Estado<select name="status"><option value="publicado" ${b.status !== "borrador" ? "selected" : ""}>Publicado</option><option value="borrador" ${b.status === "borrador" ? "selected" : ""}>Borrador</option></select></label>
      <label>Visibilidad<select name="visibility"><option value="publico" ${b.visibility !== "oculto" ? "selected" : ""}>En el índice de blogs</option><option value="oculto" ${b.visibility === "oculto" ? "selected" : ""}>Solo con enlace (versión privada)</option></select></label>
      <label class="full">Lema<input type="text" name="tagline" value="${v("tagline")}" placeholder="Una frase que explique para qué existe"></label>
      <label class="full">Descripción para el índice<input type="text" name="description" value="${v("description")}"></label>
      <label>Autor o responsable<input type="text" name="author" value="${v("author")}"></label>
      <label>Cargo<input type="text" name="author_role" value="${v("author_role")}"></label>
      <label>Color de marca<input type="color" name="accent" value="${esc(safeColor(b.accent) || "#0b2545")}"></label>
      <label>Logotipo (iniciales o sigla)<input type="text" name="logo_text" value="${v("logo_text")}" maxlength="4" placeholder="CD"></label>
      <label>Diseño<select name="layout">${Object.keys(BLOG_LAYOUTS).map((k) => `<option value="${k}" ${(b.layout || "revista") === k ? "selected" : ""}>${BLOG_LAYOUTS[k]}</option>`).join("")}</select></label>
      <label>Orden en el índice<input type="number" name="order" value="${v("order") || 10}"></label>
      <div class="full"><label>Imagen de cabecera</label>${imgField("cover", b.cover)}</div>
      <label class="full">Presentación (Markdown)<span class="help">Texto propio de la cabecera: misión, a quién va dirigido, quién lo firma.</span><textarea name="intro_md">${v("intro_md")}</textarea></label>
      <label>Botón: texto<input type="text" name="cta_text" value="${v("cta_text")}" placeholder="Suscríbete"></label>
      <label>Botón: enlace<input type="text" name="cta_url" value="${v("cta_url")}" placeholder="https://… · mailto:… · #seccion"></label>
      <div class="full"><label>Módulos</label>${checks("modules", BLOG_MODULES, Object.keys(m).filter((k) => m[k]))}</div>
      <div class="full"><label>Selección automática · tipos de pieza</label>${checks("f_kinds", { noticia: "Noticias", analisis: "Análisis", reportaje: "Reportajes" }, f.kinds)}</div>
      <div class="full"><label>Selección automática · secciones</label>${checks("f_sections", { tierra: "Tierra", mar: "Mar", aire: "Aire", regulacion: "Regulación", licitaciones: "Licitaciones y plazos" }, f.sections)}</div>
      <label>Subsectores (comas)<input type="text" name="f_subsectors" value="${esc((f.subsectors || []).join(", "))}" placeholder="autobús, ferrocarril, puertos"></label>
      <label>Palabras clave (comas)<input type="text" name="f_keywords" value="${esc((f.keywords || []).join(", "))}" placeholder="concesión, OSP, Ley 9/2025"></label>
      <div class="full"><label>Plazos y boletines · modos</label>${checks("f_modos", { tierra: "Tierra", mar: "Mar", aire: "Aire" }, f.modos)}</div>
      <label>Título del bloque automático<input type="text" name="feed_title" value="${v("feed_title")}" placeholder="Seleccionado por MOTICIAS"></label>
      <label>Máximo de piezas automáticas<input type="number" name="feed_limit" value="${v("feed_limit") || 9}" min="1" max="40"></label>
      <label>Título del bloque de entradas<input type="text" name="posts_title" value="${v("posts_title")}" placeholder="Entradas"></label>
      <label>Entrada destacada<select name="pinned_id"><option value="">Ninguna</option>${posts.map((p) => `<option value="${esc(p.id)}" ${b.pinned_id === p.id ? "selected" : ""}>${esc(p.title)}</option>`).join("")}</select></label>
      <label>Contacto: título<input type="text" name="contact_title" value="${v("contact_title")}"></label>
      <label>Contacto: correo<input type="email" name="contact_email" value="${v("contact_email")}" placeholder="por defecto, el de la cabecera"></label>
      <label class="full">Contacto: texto<input type="text" name="contact_text" value="${v("contact_text")}"></label>
      <label class="full">Notas internas (cliente, condiciones, envío)<textarea name="notes">${v("notes")}</textarea></label>
      <input type="hidden" name="id" value="${v("id")}">
      <div class="full sticky-actions"><button type="button" class="btn secondary" id="back-blogs-2">Cancelar</button><button type="submit" class="btn">Guardar blog</button></div>
    </form>
    ${b.id ? `<div class="admin-note" style="margin-top:22px"><b>Entradas de este blog</b> (${posts.length})</div><div class="admin-list">${posts.map((a) => `<div class="admin-row"><img src="${esc(imgSrc(a) || artSvg(a.section, a.id))}" alt=""><div><div class="t">${esc(a.title)}</div><div class="m"><span class="badge ${a.status === "borrador" ? "borrador" : "media"}">${esc(a.status || "publicado")}</span><span>${esc(fmtShort(a.date))}</span></div></div><div class="actions"><button type="button" class="btn small secondary" data-a-edit="${esc(a.id)}" data-goto-piezas>Editar</button></div></div>`).join("") || `<div class="admin-note">Sin entradas todavía.</div>`}</div>` : ""}`;
  }

  // ---------- Administración: publicidad y patrocinios ----------
  function listAdsAdmin() {
    const t = todayISO(), y = t.slice(0, 4);
    const arr = S.ads.slice().sort((a, b) => String(b.start || "").localeCompare(String(a.start || "")));
    const paid = arr.filter((a) => a.type !== "autopromocion" && a.status !== "borrador");
    const cnt = (st) => arr.filter((a) => adState(a, t) === st).length;
    const yearSum = paid.filter((a) => String(a.start || a.end || "").startsWith(y)).reduce((s, a) => s + (+a.amount_eur || 0), 0);
    const live = paid.filter((a) => adState(a, t) === "activo").reduce((s, a) => s + (+a.amount_eur || 0), 0);
    const inv = Object.keys(AD_SLOTS).map((k) => { const occ = arr.filter((a) => adState(a, t) === "activo" && (a.slots || []).includes(k)); const p = occ.filter((a) => a.type !== "autopromocion"); return `<tr><td>${esc(AD_SLOTS[k])}</td><td>${p.length ? p.map((a) => esc(a.advertiser || a.name)).join(", ") : `<span style="color:var(--muted)">Libre${occ.length ? " · autopromoción" : ""}</span>`}</td></tr>`; }).join("");
    return `<div class="toolbar"><button type="button" class="btn" id="new-ad">+ Nueva campaña o patrocinio</button><a class="btn secondary" href="#anunciate" data-close-admin>Ver página «Anúnciate»</a></div>
    <div class="ad-kpis"><div><b>${cnt("activo")}</b><span>en curso</span></div><div><b>${cnt("programado")}</b><span>programadas</span></div><div><b>${eur(live) || "0 €"}</b><span>contratado en curso</span></div><div><b>${eur(yearSum) || "0 €"}</b><span>contratado en ${y}</span></div></div>
    <div class="admin-note">La publicidad se muestra solo en los huecos previstos, nunca sobre la apertura ni dentro del texto, y siempre con la etiqueta visible. Si un hueco no tiene campaña de pago, se rellena con <b>autopromoción</b>. Los enlaces externos llevan UTM automáticos para medir en la web del anunciante.</div>
    <table class="inv"><thead><tr><th>Hueco</th><th>Ocupado hoy por</th></tr></thead><tbody>${inv}</tbody></table>
    <div class="admin-list" style="margin-top:16px">${arr.map((a) => { const st = adState(a, t); return `<div class="admin-row"><span class="swatch" style="background:${esc(safeColor(a.accent) || "#0b2545")}">${adImg(a) ? `<img src="${esc(adImg(a))}" alt="">` : ""}</span><div><div class="t">${esc(a.name || a.headline || a.advertiser)}</div><div class="m"><span class="badge ${st === "activo" ? "alta" : st === "borrador" ? "borrador" : "media"}">${esc(AD_STATES[st])}</span><span>${esc(AD_TYPES[a.type] || a.type || "")}</span><span>·</span><span>${esc(a.advertiser || "")}</span><span>·</span><span>${esc(a.start ? fmtShort(a.start) : "sin inicio")} → ${esc(a.end ? fmtShort(a.end) : "sin fin")}</span>${a.amount_eur ? `<span>· ${esc(eur(a.amount_eur))}</span>` : ""}<span>· ${(a.slots || []).length} huecos</span></div></div><div class="actions"><button type="button" class="btn small secondary" data-ad-edit="${esc(a.id)}">Editar</button><button type="button" class="btn small secondary" data-ad-toggle="${esc(a.id)}">${a.status === "pausado" ? "Reanudar" : "Pausar"}</button><button type="button" class="btn small danger" data-ad-del="${esc(a.id)}">Borrar</button></div></div>`; }).join("") || `<div class="admin-note">Sin campañas todavía.</div>`}</div>`;
  }
  function formAd(a) {
    const isNew = !a.id;
    const v = (k) => esc(a[k] == null ? "" : a[k]);
    const blogs = {}; S.blogs.forEach((b) => (blogs[b.id] = b.name));
    return `<div class="toolbar"><button type="button" class="btn secondary" id="back-ads">← Volver a publicidad</button><span style="font-weight:600">${isNew ? "Nueva campaña o patrocinio" : "Editar campaña"}</span></div>
    <form id="form-ad" class="form-grid">
      <label class="full">Nombre interno<input type="text" name="name" value="${v("name")}" required placeholder="Patrocinio sección Tierra · T1 2027"></label>
      <label>Anunciante o marca<input type="text" name="advertiser" value="${v("advertiser")}"></label>
      <label>Tipo<select name="type">${Object.keys(AD_TYPES).map((k) => `<option value="${k}" ${(a.type || "banner") === k ? "selected" : ""}>${AD_TYPES[k]}</option>`).join("")}</select></label>
      <label>Estado<select name="status"><option value="activo" ${!a.status || a.status === "activo" ? "selected" : ""}>Activa (según fechas)</option><option value="pausado" ${a.status === "pausado" ? "selected" : ""}>Pausada</option><option value="borrador" ${a.status === "borrador" ? "selected" : ""}>Borrador</option></select></label>
      <label>Peso en la rotación<input type="number" name="weight" value="${v("weight") || 1}" min="1" max="10"></label>
      <label>Inicio<input type="date" name="start" value="${v("start") || todayISO()}"></label>
      <label>Fin<input type="date" name="end" value="${v("end")}"></label>
      <div class="full"><label>Huecos donde aparece</label>${checks("slots", AD_SLOTS, a.slots)}</div>
      <div class="full"><label>Limitar a secciones (vacío = todas)</label>${checks("sections", { tierra: "Tierra", mar: "Mar", aire: "Aire", regulacion: "Regulación", licitaciones: "Licitaciones y plazos", analisis: "Análisis" }, a.sections)}</div>
      ${Object.keys(blogs).length ? `<div class="full"><label>Limitar a blogs (vacío = todos)</label>${checks("blog_ids", blogs, a.blog_ids)}</div>` : ""}
      <label>Etiqueta visible<input type="text" name="label" value="${v("label")}" placeholder="Publicidad · Patrocinio · Contenido patrocinado"></label>
      <label>Color<input type="color" name="accent" value="${esc(safeColor(a.accent) || "#0b2545")}"></label>
      <label class="full">Titular del anuncio<input type="text" name="headline" value="${v("headline")}"></label>
      <label class="full">Texto<textarea name="text">${v("text")}</textarea></label>
      <label>Llamada a la acción<input type="text" name="cta" value="${v("cta")}" placeholder="Solicitar valoración"></label>
      <label>Enlace de destino<input type="text" name="url" value="${v("url")}" placeholder="https://… · mailto:… · #a-pieza"></label>
      <label>Campaña UTM<input type="text" name="utm_campaign" value="${v("utm_campaign")}" placeholder="por defecto, el identificador"></label>
      <label>Añadir UTM<select name="utm"><option value="1" ${a.utm !== false ? "selected" : ""}>Sí</option><option value="0" ${a.utm === false ? "selected" : ""}>No</option></select></label>
      <div class="full"><label>Creatividad (imagen opcional; sin imagen se muestra como anuncio de texto)</label>${imgField("adimg", a.image, "Horizontal 1200 × 300 para portada; 600 × 500 para lateral.")}</div>
      <div class="full"><label>Vista previa</label><div id="ad-preview" class="ad-preview"></div></div>
      <label>Importe contratado (€)<input type="number" name="amount_eur" value="${v("amount_eur")}" min="0" step="1"></label>
      <label>Modalidad<select name="pricing">${["tarifa plana", "por envío", "CPM", "intercambio", "gratuito / casa"].map((k) => `<option ${a.pricing === k ? "selected" : ""}>${k}</option>`).join("")}</select></label>
      <label>Persona de contacto<input type="text" name="contact" value="${v("contact")}"></label>
      <label>Referencia de factura o pedido<input type="text" name="invoice_ref" value="${v("invoice_ref")}"></label>
      <label class="full">Notas internas<textarea name="notes">${v("notes")}</textarea></label>
      <input type="hidden" name="id" value="${v("id")}">
      <div class="full sticky-actions"><button type="button" class="btn secondary" id="back-ads-2">Cancelar</button><button type="submit" class="btn">Guardar campaña</button></div>
    </form>`;
  }
  function readAdForm(f) {
    const g = (n) => (f[n] ? f[n].value.trim() : "");
    return { name: g("name"), advertiser: g("advertiser"), type: g("type"), status: g("status"), weight: +g("weight") || 1, start: g("start"), end: g("end"), slots: checked(f, "slots"), sections: checked(f, "sections"), blog_ids: checked(f, "blog_ids"), label: g("label"), accent: g("accent"), headline: g("headline"), text: g("text"), cta: g("cta"), url: g("url"), utm_campaign: g("utm_campaign"), utm: g("utm") !== "0", image: readImg(f, "adimg"), amount_eur: g("amount_eur") === "" ? null : +g("amount_eur"), pricing: g("pricing"), contact: g("contact"), invoice_ref: g("invoice_ref"), notes: g("notes") };
  }
  function wireAdmin2(c) {
    const on = (sel, ev, fn) => { const el = $(sel, c); if (el) el.addEventListener(ev, fn); };
    // Imágenes genéricas
    $$("[data-upload]", c).forEach((inp) => inp.addEventListener("change", async (e) => {
      const p = inp.dataset.upload, file = e.target.files && e.target.files[0], f = inp.closest("form"); if (!file || !S.assets || !f) return;
      try { toast("Subiendo imagen…"); const res = await S.assets.upload(file); f[p + "_assetId"].value = res.id; f[p + "_src"].value = res.url || ("/_blob/" + res.id); $("#" + p + "-preview", c).innerHTML = `<img src="${esc(f[p + "_src"].value)}" alt="">`; toast("Imagen subida"); f.dispatchEvent(new Event("input")); }
      catch (err) { console.error(err); toast("No se pudo subir la imagen", true); }
    }));
    $$("[data-img-clear]", c).forEach((btn) => btn.addEventListener("click", () => { const p = btn.dataset.imgClear, f = btn.closest("form"); f[p + "_src"].value = ""; f[p + "_assetId"].value = ""; $("#" + p + "-preview", c).textContent = "Sin imagen"; f.dispatchEvent(new Event("input")); }));
    $$("[data-close-admin]", c).forEach((a) => a.addEventListener("click", () => closeAdmin()));
    // Blogs
    on("#new-blog", "click", () => { S.editingBlog = { type: "blog", status: "borrador", visibility: "publico", layout: "revista", accent: "#0b2545", author: "Rainer", modules: { posts: true, feed: true } }; renderAdmin(); });
    on("#back-blogs", "click", () => { S.editingBlog = null; renderAdmin(); });
    on("#back-blogs-2", "click", () => { S.editingBlog = null; renderAdmin(); });
    $$("[data-bl-edit]", c).forEach((b) => b.addEventListener("click", () => { S.editingBlog = blogById(b.dataset.blEdit); renderAdmin(); }));
    $$("[data-bl-post]", c).forEach((b) => b.addEventListener("click", () => { S.adminTab = "piezas"; S.editing = newBlogPost(blogById(b.dataset.blPost)); renderAdmin(); }));
    $$("[data-goto-piezas]", c).forEach((b) => b.addEventListener("click", () => { S.adminTab = "piezas"; S.editing = S.articles.find((a) => a.id === b.dataset.aEdit); renderAdmin(); }));
    $$("[data-bl-del]", c).forEach((b) => b.addEventListener("click", () => confirmInline(b, async () => { await S.db.doc("blogs/" + b.dataset.blDel).delete(); toast("Blog borrado (sus entradas se conservan en Piezas)"); })));
    on("#form-blog", "submit", async (e) => {
      e.preventDefault(); const f = e.target; const g = (n) => (f[n] ? f[n].value.trim() : "");
      const existing = g("id");
      const id = existing || slugify(g("slug") || g("name")).slice(0, 50);
      if (!existing && blogById(id)) { toast("Ya existe un blog con esa dirección; cambia el nombre o el slug", true); return; }
      const prev = existing ? blogById(existing) || {} : {};
      const mods = {}; Object.keys(BLOG_MODULES).forEach((k) => (mods[k] = checked(f, "modules").includes(k)));
      const data = Object.assign({}, prev, {
        id, slug: id, name: g("name"), type: g("type"), status: g("status"), visibility: g("visibility"), tagline: g("tagline"), description: g("description"), author: g("author"), author_role: g("author_role"),
        accent: g("accent"), logo_text: g("logo_text"), layout: g("layout"), order: +g("order") || 10, cover: readImg(f, "cover"), intro_md: g("intro_md"), cta_text: g("cta_text"), cta_url: g("cta_url"), modules: mods,
        filters: { kinds: checked(f, "f_kinds"), sections: checked(f, "f_sections"), subsectors: csv(g("f_subsectors")), keywords: csv(g("f_keywords")), modos: checked(f, "f_modos") },
        feed_title: g("feed_title"), feed_limit: +g("feed_limit") || 9, posts_title: g("posts_title"), pinned_id: g("pinned_id") || null, contact_title: g("contact_title"), contact_email: g("contact_email"), contact_text: g("contact_text"), notes: g("notes"),
        updated_at: new Date().toISOString(), created_at: prev.created_at || new Date().toISOString(),
      });
      if (!data.name) { toast("Falta el nombre", true); return; }
      const ok = await writeDoc("blogs/" + id, data, false);
      if (ok) { S.editingBlog = null; renderAdmin(); }
    });
    // Publicidad
    on("#new-ad", "click", () => { S.editingAd = { type: "banner", status: "borrador", start: todayISO(), slots: ["portada-medio"], weight: 1, pricing: "tarifa plana" }; renderAdmin(); });
    on("#back-ads", "click", () => { S.editingAd = null; renderAdmin(); });
    on("#back-ads-2", "click", () => { S.editingAd = null; renderAdmin(); });
    $$("[data-ad-edit]", c).forEach((b) => b.addEventListener("click", () => { S.editingAd = S.ads.find((x) => x.id === b.dataset.adEdit); renderAdmin(); }));
    $$("[data-ad-toggle]", c).forEach((b) => b.addEventListener("click", async () => { const a = S.ads.find((x) => x.id === b.dataset.adToggle); if (!a) return; await writeDoc("ads/" + a.id, { status: a.status === "pausado" ? "activo" : "pausado", updated_at: new Date().toISOString() }, true); }));
    $$("[data-ad-del]", c).forEach((b) => b.addEventListener("click", () => confirmInline(b, async () => { await S.db.doc("ads/" + b.dataset.adDel).delete(); toast("Campaña borrada"); })));
    const fa = $("#form-ad", c);
    if (fa) {
      const prevw = () => { const d = readAdForm(fa); d.id = fa.id.value || "vista-previa"; $("#ad-preview", c).innerHTML = adHtml(d, (d.slots || [])[0] || "portada-medio", (d.slots || [])[0] === "articulo-lateral" ? "side" : "wide"); };
      fa.addEventListener("input", prevw); fa.addEventListener("change", prevw); prevw();
      fa.addEventListener("submit", async (e) => {
        e.preventDefault();
        const existing = fa.id.value.trim();
        const d = readAdForm(fa);
        if (!d.name) { toast("Falta el nombre interno", true); return; }
        if (!d.slots.length) { toast("Elige al menos un hueco", true); return; }
        if (d.end && d.start && d.end < d.start) { toast("La fecha de fin es anterior a la de inicio", true); return; }
        const id = existing || slugify(d.name).slice(0, 50) + "-" + Date.now().toString(36).slice(-4);
        const prev = existing ? S.ads.find((x) => x.id === existing) || {} : {};
        const ok = await writeDoc("ads/" + id, Object.assign({}, prev, d, { id, updated_at: new Date().toISOString(), created_at: prev.created_at || new Date().toISOString() }), false);
        if (ok) { S.editingAd = null; renderAdmin(); }
      });
    }
  }
  function wireSrcDel() { $$(".src-del").forEach((b) => { b.onclick = () => b.closest(".src-row").remove(); }); }
  function confirmInline(btn, fn) {
    if (btn.dataset.armed) { btn.dataset.armed = ""; fn().catch((e) => { console.error(e); toast("No se pudo borrar: " + (e && e.message ? e.message : ""), true); }); return; }
    btn.dataset.armed = "1"; const old = btn.textContent; btn.textContent = "¿Seguro? Pulsa otra vez"; setTimeout(() => { if (btn.isConnected) { btn.textContent = old; btn.dataset.armed = ""; } }, 3500);
  }
  async function writeDoc(path, data, merge) {
    try {
      const ref = S.db.doc(path);
      if (merge) { try { await ref.update(data); } catch (e) { if (e && e.code === "invalid_argument") { const snap = await ref.get(); await ref.set(Object.assign({}, snap.exists ? snap.data() : {}, data)); } else throw e; } }
      else await ref.set(Object.assign({}, data));
      toast("Guardado"); return true;
    } catch (e) {
      console.error(e);
      const msg = e && e.code === "quota_exceeded" ? "Límite de la base de datos alcanzado; borra piezas antiguas." : e && e.code === "invalid_argument" ? "No tienes permiso de escritura o el dato no es válido." : "No se pudo guardar.";
      toast(msg, true); return false;
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
