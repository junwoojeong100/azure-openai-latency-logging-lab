# -*- coding: utf-8 -*-
# 두 가이드가 함께 쓰는 HTML 템플릿(CSS · JS). 색은 모두 테마 변수(--cp-*)만 사용합니다 (하드코딩 색 없음).
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
  font-size: 16px; line-height: 1.75; word-break: keep-all; overflow-wrap: break-word;
}
a { color: var(--cp-link); }
code, pre, kbd { font-family: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, "Cascadia Mono", "Liberation Mono", "Noto Sans Mono CJK KR", D2Coding, monospace; }
:not(pre) > code {
  background: var(--cp-surface-soft); border: 1px solid var(--cp-border); border-radius: 6px;
  padding: 1px 6px; font-size: 0.88em; word-break: break-word; overflow-wrap: anywhere;
}

/* ───────── 머리말 */
.hero { max-width: 1280px; margin: 0 auto; padding: 36px 28px 8px; }
.eyebrow { color: var(--cp-accent); font-weight: 700; letter-spacing: 0.08em; font-size: 12px; text-transform: uppercase; }
.hero h1 { margin: 6px 0 12px; font-size: 32px; line-height: 1.3; letter-spacing: -0.01em; }
.hero p.lead { margin: 0 0 16px; color: var(--cp-text-muted); font-size: 17px; max-width: 900px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 8px; }
.chip {
  display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 999px;
  background: var(--cp-surface); border: 1px solid var(--cp-border); font-size: 13px; color: var(--cp-text-muted);
}
.chip b { color: var(--cp-text); font-weight: 600; }
a.chip { text-decoration: none; }
a.chip:hover { border-color: var(--cp-accent); color: var(--cp-accent); }

/* ───────── 레이아웃 · 목차 */
.layout { max-width: 1280px; margin: 0 auto; padding: 8px 28px 56px; display: grid; grid-template-columns: 252px minmax(0, 1fr); gap: 34px; }
nav.toc { position: sticky; top: 16px; align-self: start; max-height: calc(100vh - 32px); overflow: auto; padding: 14px 4px 14px 0; font-size: 13.5px; }
nav.toc .grp { margin: 14px 0 4px; font-size: 11.5px; font-weight: 700; letter-spacing: 0.06em; color: var(--cp-text-soft); text-transform: uppercase; }
nav.toc a { display: block; padding: 4px 10px; border-left: 2px solid var(--cp-border); color: var(--cp-text-muted); text-decoration: none; line-height: 1.5; }
nav.toc a:hover { color: var(--cp-text); border-left-color: var(--cp-border-strong); }
nav.toc a.on { color: var(--cp-accent); border-left-color: var(--cp-accent); background: var(--cp-accent-soft); font-weight: 600; }
nav.toc a.done::after { content: " ✓"; color: var(--cp-success); font-weight: 700; }
.tools { margin: 0 0 10px; padding: 10px 12px; border: 1px solid var(--cp-border); border-radius: 12px; background: var(--cp-surface); }
.tools .prog { font-size: 12.5px; color: var(--cp-text-muted); margin-bottom: 6px; }
.tools .prog b { color: var(--cp-text); }
.tools .bar { height: 6px; border-radius: 999px; background: var(--cp-surface-soft); border: 1px solid var(--cp-border); overflow: hidden; margin-bottom: 8px; }
.tools .bar > i { display: block; height: 100%; width: 0; background: var(--cp-success); transition: width 0.25s; }
.tools button {
  font: inherit; font-size: 12px; padding: 3px 9px; margin: 0 4px 4px 0; border-radius: 8px; cursor: pointer;
  color: var(--cp-text-muted); background: var(--cp-surface); border: 1px solid var(--cp-border);
}
.tools button:hover { border-color: var(--cp-accent); color: var(--cp-accent); }
.tools button[aria-pressed="true"] { color: var(--cp-accent); background: var(--cp-accent-soft); border-color: var(--cp-highlight); }
main { min-width: 0; }
main section { margin: 0 0 48px; }
main h2 {
  font-size: 23px; margin: 0 0 14px; padding-bottom: 8px; border-bottom: 2px solid var(--cp-accent);
  display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 12px; line-height: 1.4;
}
main h2 small { font-size: 13.5px; font-weight: 500; color: var(--cp-text-soft); }
main h4 { margin: 20px 0 6px; font-size: 16px; }
main p { margin: 10px 0; }
main > section > p, main .lede { max-width: 920px; }

/* ───────── 단계 카드 */
.step {
  background: var(--cp-surface); border: 1px solid var(--cp-border); border-radius: 16px; padding: 20px 22px 14px; margin: 0 0 22px;
  box-shadow: 0 0 2px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.14);
}
.step > h3 { margin: 0 0 4px; font-size: 19px; line-height: 1.4; display: flex; flex-wrap: wrap; align-items: center; gap: 6px 10px; }
.badge {
  display: inline-block; font-size: 12px; font-weight: 700; letter-spacing: 0.04em; padding: 2px 10px; border-radius: 999px;
  color: var(--cp-accent); background: var(--cp-accent-soft); border: 1px solid var(--cp-highlight);
}
.badge.opt { color: var(--cp-text-muted); background: var(--cp-surface-soft); border-color: var(--cp-border); }
.scope { font-size: 11.5px; font-weight: 600; padding: 2px 9px; border-radius: 999px; border: 1px solid var(--cp-border); color: var(--cp-text-muted); background: var(--cp-surface-soft); white-space: nowrap; }
.scope.apply { color: var(--cp-accent); border-color: var(--cp-highlight); background: var(--cp-accent-soft); }
.scope.check { color: var(--cp-success); border-color: var(--cp-success); background: var(--cp-surface); }
.meta { color: var(--cp-text-soft); font-size: 13.5px; margin: 0 0 10px; }
.step p { margin: 10px 0; }
.step ul, .step ol { margin: 8px 0; padding-left: 22px; }
.step li { margin: 4px 0; }
.step h4 { margin: 22px 0 6px; font-size: 16px; padding-left: 10px; border-left: 3px solid var(--cp-accent); line-height: 1.4; }

/* 이 단계 한눈에 */
.brief {
  margin: 12px 0 14px; padding: 4px 16px; border: 1px solid var(--cp-border); border-radius: 12px; background: var(--cp-bg-elevated);
}
.brief .row { display: grid; grid-template-columns: 112px minmax(0, 1fr); gap: 4px 14px; padding: 7px 0; border-bottom: 1px dashed var(--cp-border); }
.brief .row:last-child { border-bottom: 0; }
.brief .row > b { font-size: 13px; color: var(--cp-accent); letter-spacing: 0.01em; padding-top: 1px; }
.brief .row.apply > b { color: var(--cp-success); }
.brief .row.warn > b { color: var(--cp-warning); }
.brief .row > div > :first-child { margin-top: 0; }
.brief .row > div > :last-child { margin-bottom: 0; }
.brief p { margin: 4px 0; font-size: 15px; }
.brief ul { margin: 4px 0; padding-left: 20px; font-size: 15px; }

/* ───────── 코드 */
.codewrap { position: relative; margin: 12px 0; }
.codewrap .cap { font-size: 12.5px; font-weight: 600; color: var(--cp-text-muted); margin: 0 0 4px; display: flex; justify-content: space-between; gap: 12px; padding-right: 64px; }
pre.code {
  margin: 0; padding: 12px 14px; overflow: auto; background: var(--cp-surface-soft); border: 1px solid var(--cp-border);
  border-radius: 10px; font-size: 13.5px; line-height: 1.6; tab-size: 2; max-height: 620px;
}
pre.code code { white-space: pre; }
pre.code::-webkit-scrollbar, .expect pre::-webkit-scrollbar { height: 11px; width: 11px; }
pre.code::-webkit-scrollbar-track, .expect pre::-webkit-scrollbar-track { background: transparent; }
pre.code::-webkit-scrollbar-thumb, .expect pre::-webkit-scrollbar-thumb { background: var(--cp-text-soft); opacity: 0.6; border-radius: 6px; border: 2px solid transparent; background-clip: content-box; }
@supports not selector(::-webkit-scrollbar) { pre.code, .expect pre { scrollbar-width: thin; scrollbar-color: var(--cp-text-soft) transparent; } }
pre.code.more, .expect pre.more { box-shadow: inset -22px 0 14px -14px rgba(0, 0, 0, 0.30); }
.c { color: var(--cp-text-soft); }
button.copy {
  position: absolute; top: 24px; right: 8px; font: inherit; font-size: 12px; padding: 2px 10px; border-radius: 8px; cursor: pointer;
  color: var(--cp-accent); background: var(--cp-surface); border: 1px solid var(--cp-highlight); opacity: 0.95;
}
.codewrap.nocap button.copy { top: 8px; }
button.copy:hover { background: var(--cp-accent-soft); }
button.copy.ok { color: var(--cp-accent-fg); background: var(--cp-success); border-color: var(--cp-success); }

/* 코드 한 덩어리씩 읽기 (코드 → 해설) */
.walk { margin: 14px 0; border: 1px solid var(--cp-border-strong); border-radius: 12px; background: var(--cp-surface); overflow: hidden; }
.walk-cap {
  display: flex; align-items: center; gap: 10px 14px; flex-wrap: wrap; padding: 7px 12px 7px 14px;
  background: var(--cp-surface-soft); border-bottom: 1px solid var(--cp-border-strong);
}
.walk-cap .fn { font-size: 13px; font-weight: 700; color: var(--cp-text); }
.walk-cap .wm { font-size: 12px; color: var(--cp-text-soft); flex: 1 1 auto; }
.walk-cap button.copy { position: static; flex: none; }
.walk .seg + .seg { border-top: 1px solid var(--cp-border); }
.walk .segcode { position: relative; }
.walk .segcode .no {
  position: absolute; left: 11px; top: 11px; width: 24px; height: 24px; border-radius: 50%; display: grid; place-items: center;
  background: var(--cp-accent); color: var(--cp-accent-fg); font-size: 12px; font-weight: 700; font-family: "Segoe UI", Aptos, Calibri, sans-serif;
}
.walk pre.code { border: 0; border-radius: 0; max-height: none; padding: 12px 14px 12px 46px; background: var(--cp-surface-soft); }
.walk .note { padding: 10px 18px 12px 46px; background: var(--cp-bg-elevated); border-top: 1px dashed var(--cp-border); font-size: 15px; }
.walk .note .nt { font-weight: 700; font-size: 15px; margin: 0 0 4px; color: var(--cp-text); }
.walk .note .nt i { font-style: normal; color: var(--cp-accent); margin-right: 6px; }
.walk .note .nt .tg { display: inline-block; font-size: 11px; font-weight: 700; padding: 0 8px; margin-right: 7px; border-radius: 999px; border: 1px solid var(--cp-border); color: var(--cp-text-muted); background: var(--cp-surface-soft); vertical-align: 1px; }
.walk .note .nt .tg.apply { color: var(--cp-accent); border-color: var(--cp-highlight); background: var(--cp-accent-soft); }
.walk .note p { margin: 5px 0; }
.walk .note ul, .walk .note ol { margin: 5px 0; padding-left: 20px; }
.walk .note li { margin: 3px 0; }
body.hide-notes .walk .note { display: none; }
dl.flags { display: grid; grid-template-columns: fit-content(34%) minmax(0, 1fr); gap: 6px 16px; margin: 8px 0; font-size: 14.5px; align-items: start; }
dl.flags dt { margin: 0; min-width: 0; overflow-wrap: anywhere; }
dl.flags dd { margin: 0; min-width: 0; color: var(--cp-text); }
dl.flags dt code { white-space: normal; overflow-wrap: anywhere; word-break: break-word; }
dl.flags dt.long { grid-column: 1 / -1; margin-top: 4px; }
dl.flags dd.long { grid-column: 1 / -1; margin: 0 0 6px 10px; padding-left: 12px; border-left: 3px solid var(--cp-border-strong); }

/* 접이식 */
details { margin: 12px 0; border: 1px solid var(--cp-border); border-radius: 10px; background: var(--cp-bg-elevated); }
details > summary { cursor: pointer; padding: 9px 14px; font-weight: 600; font-size: 14.5px; color: var(--cp-text-muted); }
details[open] > summary { border-bottom: 1px solid var(--cp-border); color: var(--cp-text); }
details > .inner { padding: 4px 14px 12px; }

/* 예상 결과 · 알림 상자 */
.expect, .callout {
  margin: 12px 0; padding: 10px 16px; border-radius: 10px; border: 1px solid var(--cp-border); background: var(--cp-bg-elevated);
  border-left: 4px solid var(--cp-success); font-size: 15px;
}
.expect > .lbl, .callout > .lbl { font-weight: 700; font-size: 12.5px; margin-bottom: 4px; color: var(--cp-success); letter-spacing: 0.02em; }
.expect pre { margin: 6px 0 2px; padding: 9px 12px; background: var(--cp-surface); border: 1px solid var(--cp-border); border-radius: 8px; font-size: 12.8px; overflow: auto; line-height: 1.55; }
.expect .how { margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--cp-border); }
.expect .how > b { display: block; font-size: 12.5px; color: var(--cp-accent); margin-bottom: 2px; }
.expect .how p, .expect .how ul { margin: 4px 0; font-size: 14.5px; }
.expect .how ul { padding-left: 20px; }
.callout { border-left-color: var(--cp-accent); }
.callout > .lbl { color: var(--cp-accent); }
.callout.tip { border-left-color: var(--cp-success); }
.callout.tip > .lbl { color: var(--cp-success); }
.callout.warn { border-left-color: var(--cp-warning); }
.callout.warn > .lbl { color: var(--cp-warning); }
.callout.danger { border-left-color: var(--cp-danger); }
.callout.danger > .lbl { color: var(--cp-danger); }
.callout p { margin: 5px 0; }
.callout ul, .callout ol { margin: 5px 0; padding-left: 20px; }
.callout li { margin: 3px 0; }

/* 표 */
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 14.5px; background: var(--cp-surface); border: 1px solid var(--cp-border); border-radius: 10px; overflow: hidden; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--cp-border); vertical-align: top; line-height: 1.6; }
th { background: var(--cp-surface-soft); font-size: 12.5px; color: var(--cp-text-muted); letter-spacing: 0.02em; }
tr:last-child td { border-bottom: 0; }
table.nw td:first-child { white-space: nowrap; }
th.res { white-space: nowrap; }
td.ok { color: var(--cp-success); font-weight: 700; white-space: nowrap; }
td.part { color: var(--cp-warning); font-weight: 700; white-space: nowrap; }
td.no { color: var(--cp-danger); font-weight: 700; white-space: nowrap; }
table.cmp th:first-child, table.cmp td:first-child { width: 22%; }
table.cmp td:nth-child(3), table.cmp td:nth-child(4) { background: var(--cp-accent-soft); }
table.cmp th small { font-weight: 400; color: var(--cp-text-soft); }
table.map td:first-child { white-space: nowrap; font-weight: 700; }
table.map td.sc { white-space: nowrap; font-size: 13px; }
table.map a { text-decoration: none; }
table.map a:hover { text-decoration: underline; }
sup { font-size: 0.75em; color: var(--cp-text-soft); }
.foot-note { font-size: 13px; color: var(--cp-text-muted); margin: 4px 0 12px; }

/* 용어 사전 · 읽는 법 */
dl.gloss { display: grid; grid-template-columns: minmax(150px, 210px) minmax(0, 1fr); gap: 0; margin: 10px 0; border: 1px solid var(--cp-border); border-radius: 10px; overflow: hidden; background: var(--cp-surface); }
dl.gloss dt, dl.gloss dd { margin: 0; padding: 8px 14px; border-bottom: 1px solid var(--cp-border); font-size: 14.5px; line-height: 1.65; }
dl.gloss dt { font-weight: 700; background: var(--cp-surface-soft); }
dl.gloss dt small { display: block; font-weight: 500; font-size: 12px; color: var(--cp-text-soft); }
dl.gloss dd p { margin: 3px 0; }
dl.gloss > :nth-last-child(-n+2) { border-bottom: 0; }
.legend { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; margin: 12px 0; }
.legend > div { border: 1px solid var(--cp-border); border-radius: 12px; padding: 10px 14px; background: var(--cp-surface); font-size: 14.5px; }
.legend > div > b { display: block; font-size: 13px; color: var(--cp-accent); margin-bottom: 3px; }
.legend p { margin: 4px 0; }
.mini { display: inline-block; font-size: 11.5px; font-weight: 700; padding: 1px 8px; border-radius: 999px; border: 1px solid var(--cp-highlight); color: var(--cp-accent); background: var(--cp-accent-soft); }
.two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.two ol { margin: 4px 0; padding-left: 22px; font-size: 14.5px; }

/* 완료 체크 */
.donebox { display: flex; align-items: center; gap: 8px; margin: 14px 0 6px; padding-top: 10px; border-top: 1px dashed var(--cp-border); font-size: 13.5px; color: var(--cp-text-muted); cursor: pointer; }
.donebox input { width: 17px; height: 17px; accent-color: var(--cp-success); cursor: pointer; }

/* 그림 */
.diagram { background: var(--cp-surface); border: 1px solid var(--cp-border); border-radius: 16px; padding: 10px; margin: 14px 0; }
.diagram svg { width: 100%; height: auto; display: block; }
.diagram .box { fill: var(--cp-surface-soft); stroke: var(--cp-border-strong); stroke-width: 1.2; }
.diagram .boxa { fill: var(--cp-accent-soft); stroke: var(--cp-accent); stroke-width: 1.4; }
.diagram .boxg { fill: var(--cp-surface); stroke: var(--cp-success); stroke-width: 1.4; }
.diagram .boxw { fill: var(--cp-surface); stroke: var(--cp-warning); stroke-width: 1.4; stroke-dasharray: 5 3; }
.diagram .lbl { fill: var(--cp-text); font-size: 14px; font-family: "Segoe UI", Aptos, Calibri, sans-serif; }
.diagram .lblb { fill: var(--cp-text); font-size: 14px; font-weight: 700; font-family: "Segoe UI", Aptos, Calibri, sans-serif; }
.diagram .sub { fill: var(--cp-text-muted); font-size: 12px; font-family: "Segoe UI", Aptos, Calibri, sans-serif; }
.diagram .ttl { fill: var(--cp-accent); font-size: 13px; font-weight: 700; font-family: "Segoe UI", Aptos, Calibri, sans-serif; letter-spacing: 0.04em; }
.diagram .ok { fill: var(--cp-success); font-size: 12px; font-weight: 700; font-family: "Segoe UI", Aptos, Calibri, sans-serif; }
.diagram .arr { stroke: var(--cp-text-soft); stroke-width: 1.4; fill: none; }
.diagram .arrh { fill: var(--cp-text-soft); }
.diagram .brk { stroke: var(--cp-text-soft); stroke-width: 1.3; fill: none; }
.diagram .brka { stroke: var(--cp-accent); stroke-width: 1.6; fill: none; }
.diagram .brkg { stroke: var(--cp-success); stroke-width: 1.6; fill: none; }
.diagram .brkw { stroke: var(--cp-warning); stroke-width: 1.6; fill: none; }

footer.foot { max-width: 1280px; margin: 0 auto; padding: 0 28px 40px; color: var(--cp-text-soft); font-size: 13px; }

@media (max-width: 1000px) {
  .layout { grid-template-columns: minmax(0, 1fr); gap: 12px; }
  .hero, .layout, footer.foot { padding-left: 16px; padding-right: 16px; }
  .hero h1 { font-size: 25px; }
  table { display: block; overflow-x: auto; }
  nav.toc { position: static; max-height: none; border-bottom: 1px solid var(--cp-border); padding-bottom: 12px; }
  .brief .row { grid-template-columns: minmax(0, 1fr); }
  .two { grid-template-columns: minmax(0, 1fr); }
  dl.gloss { grid-template-columns: minmax(0, 1fr); }
  dl.gloss dt { border-bottom: 0; padding-bottom: 2px; }
  dl.flags { grid-template-columns: minmax(0, 1fr); gap: 0; }
  dl.flags dd { margin: 0 0 8px; }
  .walk pre.code { padding-left: 14px; padding-top: 34px; }
  .walk .note { padding-left: 14px; }
  .walk .segcode .no { top: 8px; }
}
@media (max-width: 720px) {
  table { display: block; overflow: visible; border: 0; background: transparent; margin: 10px 0; }
  table thead { display: none; }
  table tbody { display: block; }
  table tr { display: block; margin: 0 0 12px; border: 1px solid var(--cp-border); border-radius: 10px; background: var(--cp-surface); overflow: hidden; }
  table tr:last-child td { border-bottom: 1px solid var(--cp-border); }
  table td { display: block; padding: 7px 12px; white-space: normal; }
  table tr td:last-child { border-bottom: 0; }
  table td::before { content: attr(data-label); display: block; font-size: 11.5px; font-weight: 700; color: var(--cp-text-soft); margin-bottom: 2px; letter-spacing: 0.02em; }
  table td[data-label=""]::before, table td:not([data-label])::before { display: none; }
  table tr > td:first-child { background: var(--cp-surface-soft); }
  table.nw td:first-child, table.map td:first-child, table.map td.sc, td.ok, td.part, td.no { white-space: normal; }
  table.cmp th:first-child, table.cmp td:first-child { width: auto; }
  .diagram { overflow-x: auto; }
  .diagram svg { min-width: 620px; }
}
@media print {
  nav.toc, button.copy, .tools, .donebox { display: none !important; }
  .layout { display: block; padding: 0 12px; }
  .step { break-inside: avoid-page; box-shadow: none; }
  pre.code { max-height: none; overflow: visible; white-space: pre-wrap; }
  details { display: block; }
  body.hide-notes .walk .note { display: block; }
}
"""

JS = r"""<script>
(function () {
  var PAGE = location.pathname.split("/").pop() || "index";
  function store(get, key, val) {
    try { if (get) { return localStorage.getItem(key); } localStorage.setItem(key, val); } catch (e) {}
    return null;
  }
  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    var ok = false; try { ok = document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(ta); return ok;
  }
  document.querySelectorAll("button.copy").forEach(function (btn) {
    var label = btn.textContent;
    btn.addEventListener("click", function () {
      var scope = btn.closest(".walk") || btn.parentElement;
      var text = Array.prototype.map.call(scope.querySelectorAll("pre.code code"), function (c) { return c.textContent; }).join("\n");
      function done(ok) {
        btn.textContent = ok ? "복사됨" : "선택 후 Ctrl+C"; if (ok) btn.classList.add("ok");
        setTimeout(function () { btn.textContent = label; btn.classList.remove("ok"); }, 1400);
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

  var KEY = "lab-done:" + PAGE;
  var boxes = Array.prototype.slice.call(document.querySelectorAll("input[data-done]"));
  var saved = {};
  try { saved = JSON.parse(store(true, KEY) || "{}") || {}; } catch (e) { saved = {}; }
  var progText = document.querySelector(".tools .prog b");
  var progBar = document.querySelector(".tools .bar > i");
  function refresh() {
    var n = 0;
    boxes.forEach(function (b) {
      var id = b.getAttribute("data-done"), a = map[id];
      if (b.checked) { n++; if (a) a.classList.add("done"); } else if (a) { a.classList.remove("done"); }
    });
    if (progText) progText.textContent = n + " / " + boxes.length;
    if (progBar) progBar.style.width = (boxes.length ? Math.round(100 * n / boxes.length) : 0) + "%";
  }
  boxes.forEach(function (b) {
    b.checked = !!saved[b.getAttribute("data-done")];
    b.addEventListener("change", function () {
      saved[b.getAttribute("data-done")] = b.checked; store(false, KEY, JSON.stringify(saved)); refresh();
    });
  });
  refresh();

  function markMore(p) { p.classList.toggle("more", p.scrollWidth > p.clientWidth + 2 && p.scrollLeft + p.clientWidth < p.scrollWidth - 2); }
  function markAll() { Array.prototype.forEach.call(document.querySelectorAll("pre.code, .expect pre"), markMore); }
  markAll(); window.addEventListener("resize", markAll); window.addEventListener("load", markAll);
  document.addEventListener("scroll", function (e) { var t = e.target; if (t && t.matches && t.matches("pre.code, .expect pre")) markMore(t); }, true);

  Array.prototype.forEach.call(document.querySelectorAll("main table"), function (t) {
    var heads = Array.prototype.map.call(t.querySelectorAll("thead th"), function (th) {
      var c = th.cloneNode(true);
      Array.prototype.forEach.call(c.querySelectorAll("br"), function (b) { b.parentNode.replaceChild(document.createTextNode(" "), b); });
      return c.textContent.replace(/\s+/g, " ").trim();
    });
    if (!heads.length) return;
    Array.prototype.forEach.call(t.querySelectorAll("tbody tr"), function (tr) {
      Array.prototype.forEach.call(tr.children, function (td, i) { td.setAttribute("data-label", heads[i] && heads[i] !== "#" ? heads[i] : ""); });
    });
  });

  var btnNotes = document.getElementById("t-notes");
  if (btnNotes) btnNotes.addEventListener("click", function () {
    var on = document.body.classList.toggle("hide-notes");
    btnNotes.setAttribute("aria-pressed", on ? "true" : "false");
    btnNotes.textContent = on ? "코드 해설 보이기" : "코드 해설 숨기기";
  });
  var btnOpen = document.getElementById("t-open");
  if (btnOpen) btnOpen.addEventListener("click", function () {
    var all = Array.prototype.slice.call(document.querySelectorAll("main details"));
    var open = all.some(function (d) { return !d.open; });
    all.forEach(function (d) { d.open = open; });
    btnOpen.textContent = open ? "접이식 모두 접기" : "접이식 모두 펼치기";
  });
  var btnReset = document.getElementById("t-reset");
  if (btnReset) btnReset.addEventListener("click", function () {
    boxes.forEach(function (b) { b.checked = false; }); saved = {}; store(false, KEY, "{}"); refresh();
  });
})();
</script>"""
