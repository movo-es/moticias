/* MOTICIAS · Widget embebible (módulo 3). Sin dependencias. Licencia: uso libre con la marca visible.
 *
 * Uso mínimo (feed estático servido por app.moticias.com, generado por src/export_feed.py):
 *   <div class="moticias-widget" data-feed="https://app.moticias.com/feed/widget-portada.json"></div>
 *   <script async src="https://app.moticias.com/widget.js"></script>
 *
 * Con la Content API de Ghost (lectura pública; la clave de contenido no da acceso a nada privado):
 *   <div class="moticias-widget" data-ghost-url="https://moticias.com" data-ghost-key="…"
 *        data-tags="autobús,concesiones" data-limit="6"></div>
 *
 * Atributos: data-feed | data-ghost-url + data-ghost-key · data-tags (coma; en Ghost filtra por etiqueta;
 * en el feed filtra por subsector o etiqueta) · data-section (tierra|mar|aire|regulacion|licitaciones|analisis|logistica)
 * · data-limit (por defecto 6) · data-title (por defecto «Lo esencial · MOTICIAS») · data-agenda ("1" muestra plazos)
 * · data-theme (light|dark|auto) · data-accent (color) · data-utm (campaña; por defecto «widget»).
 * El widget pinta dentro de un shadow DOM: no toca el CSS de la página anfitriona ni se deja tocar por él.
 */
(function () {
  "use strict";
  var BRAND = "MOTICIAS", HOME = "https://moticias.com/", VERSION = "0.1";

  function utm(url, campaign) {
    try {
      var u = new URL(url);
      if (!u.searchParams.has("utm_source")) {
        u.searchParams.set("utm_source", "widget");
        u.searchParams.set("utm_medium", "referral");
        u.searchParams.set("utm_campaign", campaign || "widget");
        u.searchParams.set("utm_content", location.hostname || "local");
      }
      return u.toString();
    } catch (e) { return url; }
  }

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]; }); }

  function fecha(iso) {
    if (!iso) return "";
    var d = new Date(iso.length === 10 ? iso + "T12:00:00" : iso);
    if (isNaN(d)) return esc(iso);
    return d.toLocaleDateString("es-ES", { day: "numeric", month: "short" });
  }

  var CSS = [
    ":host{all:initial;display:block;font:14px/1.45 'IBM Plex Sans','Helvetica Neue',Arial,sans-serif;color:var(--ink);",
    "--ink:#0f1f33;--muted:#5f6877;--paper:#ffffff;--line:#d8d5cc;--accent:#e9b532;--accent-ink:#7a5a05;--head:#0f1f33;--on-head:#f3f2ee}",
    ":host([data-theme=dark]){--ink:#ebe8df;--muted:#98a1ae;--paper:#122136;--line:#26384f;--accent:#e9b532;--accent-ink:#f0c654;--head:#07101c;--on-head:#ebe8df}",
    ".w{background:var(--paper);border:1px solid var(--line);border-radius:10px;overflow:hidden;max-width:100%}",
    ".h{background:var(--head);color:var(--on-head);padding:10px 14px;display:flex;align-items:baseline;justify-content:space-between;gap:8px}",
    ".h b{font-family:'Newsreader',Georgia,serif;font-size:17px;letter-spacing:.2px}.h b i{font-style:normal;color:var(--accent)}",
    ".h span{font-size:11px;opacity:.75;text-transform:uppercase;letter-spacing:.08em}",
    "ol{list-style:none;margin:0;padding:0}li{padding:10px 14px;border-top:1px solid var(--line)}li:first-child{border-top:0}",
    ".k{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--accent-ink);font-weight:600}",
    ".k em{font-style:normal;color:var(--muted);font-weight:400;margin-left:6px;text-transform:none;letter-spacing:0}",
    "a.t{display:block;color:var(--ink);text-decoration:none;font-family:'Newsreader',Georgia,serif;font-size:16px;line-height:1.3;margin:2px 0}a.t:hover{text-decoration:underline}",
    ".s{color:var(--muted);font-size:13px;margin:0}",
    ".ag{border-top:2px solid var(--accent);padding:8px 14px}.ag h4{margin:0 0 4px;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}",
    ".ag div{font-size:13px;padding:3px 0}.ag time{font-variant-numeric:tabular-nums;color:var(--accent-ink);font-weight:600;margin-right:6px}",
    ".ag a{color:var(--ink);text-decoration:none}.ag a:hover{text-decoration:underline}",
    ".f{padding:8px 14px;border-top:1px solid var(--line);font-size:12px;color:var(--muted);display:flex;justify-content:space-between}",
    ".f a{color:var(--muted);text-decoration:none;font-weight:600}.f a:hover{color:var(--ink)}",
    ".e{padding:14px;color:var(--muted);font-size:13px}"
  ].join("");

  function render(host, data, opts) {
    var root = host.shadowRoot || host.attachShadow({ mode: "open" });
    if (opts.accent) host.style.setProperty("--accent", opts.accent);
    var items = (data.items || []).slice(0, opts.limit);
    var html = "<style>" + CSS + "</style><div class='w'><div class='h'><b><i>M</i>" + esc(BRAND.slice(1)) + "</b><span>" + esc(opts.title) + "</span></div>";
    if (!items.length) {
      html += "<div class='e'>Sin piezas para estos filtros.</div>";
    } else {
      html += "<ol>";
      items.forEach(function (it) {
        html += "<li><div class='k'>" + esc(it.kicker || it.section || "") + "<em>" + fecha(it.date) + "</em></div>" +
          "<a class='t' href='" + esc(utm(it.url, opts.utm)) + "' target='_blank' rel='noopener'>" + esc(it.title) + "</a>" +
          (it.subtitle ? "<p class='s'>" + esc(it.subtitle) + "</p>" : "") + "</li>";
      });
      html += "</ol>";
    }
    if (opts.agenda && data.agenda && data.agenda.length) {
      html += "<div class='ag'><h4>Próximos plazos</h4>";
      data.agenda.slice(0, 5).forEach(function (g) {
        var t = esc(g.title); if (g.url) t = "<a href='" + esc(utm(g.url, opts.utm)) + "' target='_blank' rel='noopener'>" + t + "</a>";
        html += "<div><time>" + fecha(g.date) + "</time>" + t + "</div>";
      });
      html += "</div>";
    }
    html += "<div class='f'><span>Noticias con M de Movilidad y Transportes</span><a href='" + esc(utm(HOME, opts.utm)) + "' target='_blank' rel='noopener'>Powered by MOTICIAS</a></div></div>";
    root.innerHTML = html;
  }

  function filtraFeed(data, opts) {
    var tags = opts.tags, sec = opts.section;
    var items = (data.items || []).filter(function (it) {
      if (sec && it.section !== sec) return false;
      if (tags.length) {
        var hay = [it.subsector, it.kicker, it.title].concat(it.tags || []).join(" ").toLowerCase();
        return tags.some(function (t) { return hay.indexOf(t) >= 0; });
      }
      return true;
    });
    return { items: items, agenda: data.agenda || [] };
  }

  function desdeGhost(opts) {
    var filtro = [];
    if (opts.tags.length) filtro.push("tags:[" + opts.tags.map(function (t) { return t.replace(/[^a-z0-9áéíóúñü\- ]/gi, ""); }).join(",") + "]");
    if (opts.section) filtro.push("tags:hash-" + opts.section);
    var q = "key=" + encodeURIComponent(opts.ghostKey) + "&limit=" + opts.limit + "&include=tags&fields=slug,title,custom_excerpt,published_at,url,primary_tag" +
      (filtro.length ? "&filter=" + encodeURIComponent(filtro.join("+")) : "");
    return fetch(opts.ghostUrl.replace(/\/$/, "") + "/ghost/api/content/posts/?" + q, { headers: { "Accept-Version": "v5.0" } })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        return { items: (j.posts || []).map(function (p) {
          return { title: p.title, subtitle: p.custom_excerpt, url: p.url, date: p.published_at,
                   kicker: p.primary_tag ? p.primary_tag.name : "", section: null };
        }), agenda: [] };
      });
  }

  function montar(host) {
    if (host.__moticias) return; host.__moticias = true;
    var d = host.dataset;
    var opts = {
      limit: Math.max(1, Math.min(20, parseInt(d.limit || "6", 10) || 6)),
      title: d.title || "Lo esencial", tags: (d.tags || "").toLowerCase().split(",").map(function (s) { return s.trim(); }).filter(Boolean),
      section: d.section || "", agenda: d.agenda === "1" || d.agenda === "true", utm: d.utm || "widget", accent: d.accent || "",
      ghostUrl: d.ghostUrl || "", ghostKey: d.ghostKey || "", feed: d.feed || ""
    };
    if (d.theme === "dark") host.setAttribute("data-theme", "dark");
    else if (d.theme !== "light" && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) host.setAttribute("data-theme", "dark");
    var p = opts.ghostUrl && opts.ghostKey ? desdeGhost(opts)
      : fetch(opts.feed || "https://app.moticias.com/feed/widget-portada.json", { cache: "no-cache" }).then(function (r) { return r.json(); }).then(function (j) { return filtraFeed(j, opts); });
    p.then(function (data) { render(host, data, opts); })
     .catch(function (e) { render(host, { items: [] }, opts); if (window.console) console.warn("MOTICIAS widget:", e); });
  }

  function init() { Array.prototype.forEach.call(document.querySelectorAll(".moticias-widget,[data-moticias-widget]"), montar); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
  window.MoticiasWidget = { init: init, version: VERSION };
})();
