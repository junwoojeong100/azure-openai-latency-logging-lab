# -*- coding: utf-8 -*-
# HTML 템플릿(CSS·JS) — 테마 변수만 사용 (하드코딩 색 없음)
THEME_JS = """<script>
  (() => {
    const param = new URLSearchParams(window.location.search).get("scoutTheme");
    const theme =
      param || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
  })();
</script>"""

CSS = r"""
:root {
  color-scheme: light;
  --cp-bg: #f7f4ef;
  --cp-bg-elevated: #fcfbf8;
  --cp-surface: #ffffff;
  --cp-surface-soft: #f5f5f5;
  --cp-border: #dedede;
  --cp-border-strong: #919191;
  --cp-text: #242424;
  --cp-text-muted: #5c5c5c;
  --cp-text-soft: #6f6f6f;
  --cp-accent: #b11f4b;
  --cp-accent-hover: #9a1a41;
  --cp-accent-soft: rgba(177, 31, 75, 0.08);
  --cp-accent-fg: #ffffff;
  --cp-success: #16a34a;
  --cp-danger: #dc2626;
  --cp-warning: #f59e0b;
  --cp-link: #0078d4;
  --cp-shadow: 0 18px 48px rgba(0, 0, 0, 0.12);
  --cp-overlay: rgba(255, 255, 255, 0.8);
  --cp-panel: rgba(255, 255, 255, 0.86);
  --cp-panel-strong: rgba(255, 255, 255, 0.96);
  --cp-sheen: rgba(255, 255, 255, 0.55);
  --cp-highlight: rgba(177, 31, 75, 0.12);
}
html[data-theme="dark"] {
  color-scheme: dark;
  --cp-bg: #3d3b3a;
  --cp-bg-elevated: #343231;
  --cp-surface: #292929;
  --cp-surface-soft: #2e2e2e;
  --cp-border: #474747;
  --cp-border-strong: #5f5f5f;
  --cp-text: #dedede;
  --cp-text-muted: #919191;
  --cp-text-soft: #b0b0b0;
  --cp-accent: #fd8ea1;
  --cp-accent-hover: #fb7b91;
  --cp-accent-soft: rgba(253, 142, 161, 0.14);
  --cp-accent-fg: #1a1a1a;
  --cp-success: #4ade80;
  --cp-danger: #f87171;
  --cp-warning: #fbbf24;
  --cp-link: #4da6ff;
  --cp-shadow: 0 18px 48px rgba(0, 0, 0, 0.32);
  --cp-overlay: rgba(41, 41, 41, 0.88);
  --cp-panel: rgba(41, 41, 41, 0.72);
  --cp-panel-strong: rgba(41, 41, 41, 0.96);
  --cp-sheen: rgba(255, 255, 255, 0.04);
  --cp-highlight: rgba(253, 142, 161, 0.12);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 16px; }
body {
  margin: 0; background: var(--cp-bg); color: var(--cp-text);
  font-family: "Segoe UI", Aptos, Calibri, -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 15px; line-height: 1.65;
}
a { color: var(--cp-link); }
code, pre, kbd { font-family: Consolas, "Courier New", Courier, monospace; }
:not(pre) > code {
  background: var(--cp-surface-soft); border: 1px solid var(--cp-border); border-radius: 6px;
  padding: 1px 6px; font-size: 0.9em; word-break: break-word;
}
.hero { max-width: 1240px; margin: 0 auto; padding: 36px 28px 8px; }
.eyebrow { color: var(--cp-accent); font-weight: 700; letter-spacing: 0.08em; font-size: 12px; text-transform: uppercase; }
.hero h1 { margin: 6px 0 10px; font-size: 32px; line-height: 1.25; letter-spacing: -0.01em; }
.hero p.lead { margin: 0 0 16px; color: var(--cp-text-muted); font-size: 16px; max-width: 860px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 8px; }
.chip {
  display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 999px;
  background: var(--cp-surface); border: 1px solid var(--cp-border); font-size: 13px; color: var(--cp-text-muted);
}
.chip b { color: var(--cp-text); font-weight: 600; }
.layout { max-width: 1240px; margin: 0 auto; padding: 8px 28px 56px; display: grid; grid-template-columns: 250px minmax(0, 1fr); gap: 32px; }
nav.toc { position: sticky; top: 16px; align-self: start; max-height: calc(100vh - 32px); overflow: auto; padding: 14px 4px 14px 0; font-size: 13.5px; }
nav.toc .grp { margin: 14px 0 4px; font-size: 11.5px; font-weight: 700; letter-spacing: 0.06em; color: var(--cp-text-soft); text-transform: uppercase; }
nav.toc a { display: block; padding: 4px 10px; border-left: 2px solid var(--cp-border); color: var(--cp-text-muted); text-decoration: none; }
nav.toc a:hover { color: var(--cp-text); border-left-color: var(--cp-border-strong); }
nav.toc a.on { color: var(--cp-accent); border-left-color: var(--cp-accent); background: var(--cp-accent-soft); font-weight: 600; }
main { min-width: 0; }
main section { margin: 0 0 44px; }
main h2 {
  font-size: 22px; margin: 0 0 14px; padding-bottom: 8px; border-bottom: 2px solid var(--cp-accent);
  display: flex; align-items: baseline; gap: 10px;
}
main h2 small { font-size: 13px; font-weight: 500; color: var(--cp-text-soft); }
.step {
  background: var(--cp-surface); border: 1px solid var(--cp-border); border-radius: 16px; padding: 18px 20px 14px; margin: 0 0 18px;
  box-shadow: 0 0 2px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.14);
}
.step > h3 { margin: 0 0 4px; font-size: 17.5px; display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.badge {
  display: inline-block; font-size: 11.5px; font-weight: 700; letter-spacing: 0.04em; padding: 2px 9px; border-radius: 999px;
  color: var(--cp-accent); background: var(--cp-accent-soft); border: 1px solid var(--cp-highlight);
}
.badge.opt { color: var(--cp-text-muted); background: var(--cp-surface-soft); border-color: var(--cp-border); }
.meta { color: var(--cp-text-soft); font-size: 13px; margin: 0 0 10px; }
.step p { margin: 8px 0; }
.step ul, .step ol { margin: 8px 0; padding-left: 22px; }
.step li { margin: 3px 0; }
.codewrap { position: relative; margin: 10px 0; }
.codewrap .cap { font-size: 12.5px; font-weight: 600; color: var(--cp-text-muted); margin: 0 0 4px; display: flex; justify-content: space-between; }
pre.code {
  margin: 0; padding: 12px 14px; overflow: auto; background: var(--cp-surface-soft); border: 1px solid var(--cp-border);
  border-radius: 10px; font-size: 12.8px; line-height: 1.55; tab-size: 2; max-height: 560px;
}
pre.code code { white-space: pre; }
.c { color: var(--cp-text-soft); }
button.copy {
  position: absolute; top: 26px; right: 8px; font: inherit; font-size: 12px; padding: 2px 10px; border-radius: 8px; cursor: pointer;
  color: var(--cp-accent); background: var(--cp-surface); border: 1px solid var(--cp-highlight); opacity: 0.92;
}
.codewrap.nocap button.copy { top: 8px; }
button.copy:hover { background: var(--cp-accent-soft); }
button.copy.ok { color: var(--cp-accent-fg); background: var(--cp-success); border-color: var(--cp-success); }
details { margin: 10px 0; border: 1px solid var(--cp-border); border-radius: 10px; background: var(--cp-bg-elevated); }
details > summary { cursor: pointer; padding: 8px 14px; font-weight: 600; font-size: 14px; color: var(--cp-text-muted); }
details[open] > summary { border-bottom: 1px solid var(--cp-border); color: var(--cp-text); }
details > .inner { padding: 2px 14px 10px; }
.expect, .callout {
  margin: 10px 0; padding: 9px 14px; border-radius: 10px; border: 1px solid var(--cp-border); background: var(--cp-bg-elevated);
  border-left: 4px solid var(--cp-success); font-size: 14px;
}
.expect > .lbl, .callout > .lbl { font-weight: 700; font-size: 12.5px; margin-bottom: 4px; color: var(--cp-success); letter-spacing: 0.02em; }
.expect pre { margin: 6px 0 2px; padding: 8px 10px; background: var(--cp-surface); border: 1px solid var(--cp-border); border-radius: 8px; font-size: 12.3px; overflow: auto; line-height: 1.5; }
.callout { border-left-color: var(--cp-accent); }
.callout > .lbl { color: var(--cp-accent); }
.callout.warn { border-left-color: var(--cp-warning); }
.callout.warn > .lbl { color: var(--cp-warning); }
.callout.danger { border-left-color: var(--cp-danger); }
.callout.danger > .lbl { color: var(--cp-danger); }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 14px; background: var(--cp-surface); border: 1px solid var(--cp-border); border-radius: 10px; overflow: hidden; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--cp-border); vertical-align: top; }
th { background: var(--cp-surface-soft); font-size: 12.5px; color: var(--cp-text-muted); letter-spacing: 0.02em; }
tr:last-child td { border-bottom: 0; }
table.nw td:first-child { white-space: nowrap; }
a.chip { text-decoration: none; }
a.chip:hover { border-color: var(--cp-accent); color: var(--cp-accent); }
th.res { white-space: nowrap; }
td.ok { color: var(--cp-success); font-weight: 700; white-space: nowrap; }
td.part { color: var(--cp-warning); font-weight: 700; white-space: nowrap; }
td.no { color: var(--cp-danger); font-weight: 700; white-space: nowrap; }
.diagram { background: var(--cp-surface); border: 1px solid var(--cp-border); border-radius: 16px; padding: 10px; margin: 12px 0; }
.diagram svg { width: 100%; height: auto; display: block; }
.diagram .box { fill: var(--cp-surface-soft); stroke: var(--cp-border-strong); stroke-width: 1.2; }
.diagram .boxa { fill: var(--cp-accent-soft); stroke: var(--cp-accent); stroke-width: 1.4; }
.diagram .lbl { fill: var(--cp-text); font-size: 13px; font-family: "Segoe UI", Aptos, Calibri, sans-serif; }
.diagram .sub { fill: var(--cp-text-muted); font-size: 11px; font-family: "Segoe UI", Aptos, Calibri, sans-serif; }
.diagram .ttl { fill: var(--cp-accent); font-size: 12px; font-weight: 700; font-family: "Segoe UI", Aptos, Calibri, sans-serif; letter-spacing: 0.04em; }
.diagram .arr { stroke: var(--cp-text-soft); stroke-width: 1.4; fill: none; }
.diagram .arrh { fill: var(--cp-text-soft); }
footer.foot { max-width: 1240px; margin: 0 auto; padding: 0 28px 40px; color: var(--cp-text-soft); font-size: 13px; }
@media (max-width: 1000px) {
  .layout { grid-template-columns: minmax(0, 1fr); gap: 12px; }
  .hero, .layout, footer.foot { padding-left: 16px; padding-right: 16px; }
  .hero h1 { font-size: 24px; }
  table { display: block; overflow-x: auto; }
  nav.toc { position: static; max-height: none; border-bottom: 1px solid var(--cp-border); padding-bottom: 12px; }
}
@media print {
  nav.toc, button.copy { display: none !important; }
  .layout { display: block; padding: 0 12px; }
  .step { break-inside: avoid; box-shadow: none; }
  pre.code { max-height: none; overflow: visible; white-space: pre-wrap; }
  details { display: block; }
}
"""

JS = r"""<script>
(function () {
  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    var ok = false; try { ok = document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(ta); return ok;
  }
  document.querySelectorAll("button.copy").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var code = btn.parentElement.querySelector("pre.code code");
      var text = code ? code.textContent : "";
      function done(ok) {
        var old = btn.textContent; btn.textContent = ok ? "복사됨" : "선택 후 Ctrl+C"; if (ok) btn.classList.add("ok");
        setTimeout(function () { btn.textContent = "복사"; btn.classList.remove("ok"); }, 1400);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(fallbackCopy(text)); });
      } else { done(fallbackCopy(text)); }
    });
  });
  var links = Array.prototype.slice.call(document.querySelectorAll("nav.toc a"));
  var map = {}; links.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
  var targets = Object.keys(map).map(function (id) { return document.getElementById(id); }).filter(Boolean);
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { links.forEach(function (a) { a.classList.remove("on"); }); var a = map[e.target.id]; if (a) a.classList.add("on"); }
      });
    }, { rootMargin: "-10% 0px -80% 0px" });
    targets.forEach(function (t) { io.observe(t); });
  }
})();
</script>"""
