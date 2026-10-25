# -*- coding: utf-8 -*-
# 생성기 공용 도우미: 스니펫 읽기(마커 제거) · 간단 마크다운 · 코드/예상결과/콜아웃/스텝 HTML 조각
import html
import os
import re
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))

SN = os.path.join(HERE, "..", "snippets") + os.sep
VMF = os.path.join(HERE, "vmfiles") + os.sep
FD = os.path.join(HERE, "..", "foundry") + os.sep
EXPECTED = os.path.join(HERE, "foundry_expected") + os.sep


class Raw(str):
    """이미 HTML 인 문자열 — 표 셀 등에서 마크다운 변환 없이 그대로 넣을 때 사용"""


def esc(s):
    return html.escape(s, quote=False)


# ───────────────── 스니펫 · 쿼리 · 파일 읽기
def read_clean(path):
    """snippets 파일 전체에서 '>>> slide:' / '<<< slide:' 마커 줄을 뺀 내용"""
    lines = open(path, encoding="utf-8").read().rstrip("\n").split("\n")
    return "\n".join(l for l in lines if not re.search(r"(>>>|<<<) slide:", l))


def snip(file, name):
    lines = open(SN + file, encoding="utf-8").read().split("\n")
    a = next(i for i, l in enumerate(lines) if ">>> slide:" + name in l)
    b = next(i for i, l in enumerate(lines) if "<<< slide:" + name in l)
    return "\n".join(lines[a + 1 : b])


def snipfile(file):
    return read_clean(SN + file)


def kql(name, vm="vm-lablog-rhel"):
    txt = open(SN + "queries.kql", encoding="utf-8").read()
    blocks = txt.split("\n//## ")
    for b in blocks:
        head = b.split("\n")[0]
        if head.split("|")[0].replace("//## ", "").strip() == name:
            body = "\n".join(l for l in b.split("\n")[1:] if not l.strip().startswith("//")).strip()
            return body.replace("contoso-vm-prod-agent-rhel", vm)
    raise KeyError(name)


def kq(name_or_text, vm="vm-lablog-rhel", is_name=True):
    q = kql(name_or_text, vm) if is_name else name_or_text
    assert "'" not in q, "KQL 에 작은따옴표가 있어 kq '...' 형태로 쓸 수 없습니다: " + q[:60]
    return "kq '\n" + q + "\n'"


def fd(path):
    """foundry/ 폴더의 파일 내용 (끝의 빈 줄 제거)"""
    return open(FD + path, encoding="utf-8").read().rstrip("\n")


def fkql(name):
    """foundry/queries.kql 에서 '//## 이름 | 설명' 블록의 쿼리 본문(주석 제외)"""
    txt = open(FD + "queries.kql", encoding="utf-8").read()
    for b in txt.split("\n//## "):
        head = b.split("\n")[0]
        if head.split("|")[0].replace("//## ", "").strip() == name:
            return "\n".join(l for l in b.split("\n")[1:] if not l.strip().startswith("//")).strip()
    raise KeyError(name)


def expected(name):
    """실제 실행에서 얻은 출력(foundry_expected/<name>.txt). 없으면 None"""
    p = EXPECTED + name + ".txt"
    return open(p, encoding="utf-8").read().rstrip("\n") if os.path.exists(p) else None


# ───────────────── 아주 작은 마크다운 (문단 · - 목록 · 1. 목록 · * 옵션 목록 · `코드` · **굵게** · [링크](#앵커))
_ALLOWED = re.compile(r"&lt;(/?)(br|sup|small|kbd|b|i|em|strong)&gt;")


def inline(s):
    codes = []

    def stash(m):
        codes.append("<code>" + esc(m.group(1)) + "</code>")
        return "\x00%d\x00" % (len(codes) - 1)

    s = re.sub(r"`([^`]+)`", stash, s)
    e = esc(s)
    e = _ALLOWED.sub(r"<\1\2>", e)
    e = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", e)
    e = re.sub(r"\[([^\]]+)\]\((#[\w\-]+|https?://[^)\s]+|[\w\-./]+\.html(?:#[\w\-]+)?)\)", r'<a href="\2">\1</a>', e)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], e)


def md(s):
    s = textwrap.dedent(s).strip("\n")
    out = []
    state = None  # p | ul | ol | dl
    buf = []

    def flush():
        nonlocal state, buf
        if not state:
            return
        if state == "p":
            out.append("<p>" + inline(" ".join(buf)) + "</p>")
        elif state == "ul":
            out.append("<ul>" + "".join("<li>" + inline(x) + "</li>" for x in buf) + "</ul>")
        elif state == "ol":
            out.append("<ol>" + "".join("<li>" + inline(x) + "</li>" for x in buf) + "</ol>")
        elif state == "dl":
            # ' — ' 가 있는 항목은 옵션 표(dl), 없는 항목은 일반 목록(ul)으로 — 연속된 같은 종류끼리 묶어 순서를 지킨다
            runs = []
            for x in buf:
                kind = "dl" if " — " in x else "ul"
                if runs and runs[-1][0] == kind:
                    runs[-1][1].append(x)
                else:
                    runs.append((kind, [x]))
            for kind, xs in runs:
                if kind == "ul":
                    out.append("<ul>" + "".join("<li>" + inline(x) + "</li>" for x in xs) + "</ul>")
                else:
                    items = []
                    for x in xs:
                        term, _, desc = x.partition(" — ")
                        items.append("<dt>" + inline(term) + "</dt><dd>" + inline(desc) + "</dd>")
                    out.append('<dl class="flags">' + "".join(items) + "</dl>")
        state, buf = None, []

    for raw in s.split("\n"):
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        st = line.lstrip()
        kind = None
        if st.startswith("#### "):
            flush()
            out.append("<h4>" + inline(st[5:]) + "</h4>")
            continue
        if st.startswith("- "):
            kind, text = "ul", st[2:]
        elif st.startswith("* "):
            kind, text = "dl", st[2:]
        elif re.match(r"\d+\. ", st):
            kind, text = "ol", re.sub(r"^\d+\. ", "", st)
        if kind:
            if state != kind:
                flush()
                state = kind
            buf.append(text.strip())
        elif state in ("ul", "ol", "dl") and raw.startswith("  "):
            buf[-1] += " " + st
        else:
            if state != "p":
                flush()
                state = "p"
            buf.append(st)
    flush()
    return "".join(out)


# ───────────────── 코드
def _hl(text, lang):
    out = []
    for line in text.split("\n"):
        s = line.lstrip()
        e = esc(line)
        if lang in ("bash", "python", "ini", "yaml") and s.startswith("#"):
            e = '<span class="c">' + e + "</span>"
        elif lang == "kql" and s.startswith("//"):
            e = '<span class="c">' + e + "</span>"
        out.append(e)
    return "\n".join(out)


def code(text, cap=None, run=None, skip=False, lang="bash", nocopy=False):
    """한 덩어리 코드 상자 (복사 버튼 포함). 긴 코드는 walk() 로 구간별 해설을 붙입니다."""
    text = text.strip("\n")
    attrs = ' class="code"'
    if run:
        attrs += f' data-run="{run}"'
    if skip:
        attrs += ' data-skip="1"'
    capdiv = f'<div class="cap"><span>{esc(cap)}</span><span></span></div>' if cap else ""
    btn = "" if nocopy else '<button class="copy" type="button">복사</button>'
    cls = "codewrap" + ("" if cap else " nocap")
    return f'<div class="{cls}">{capdiv}{btn}<pre{attrs}><code>{_hl(text, lang)}</code></pre></div>'


def walk(text, segs, cap=None, run=None, skip=False, lang="bash", nocopy=False, tags=None):
    """코드를 구간으로 나누고 구간마다 해설을 붙입니다 (코드 → 해설 → 코드 → 해설 …).

    text : 복사 · 실행되는 코드 전체 (그대로)
    segs : [(시작 줄 앵커, 제목, 해설 마크다운), …]
           앵커 = 그 구간의 첫 줄이 시작하는 문자열(앞 공백 무시), '=' 로 시작하면 그 줄 전체가 같은 줄. 첫 구간의 앵커는 비워 두거나 첫 줄과 같아야 합니다.
           구간은 앞 구간 뒤에서 처음 만나는 앵커 줄부터 다음 앵커 직전까지입니다 (코드는 빠짐없이 나뉨).
    tags : {구간 번호(1부터): "lab" | "apply"} — 구간 해설 제목 앞에 ‘실습 전용’ / ‘내 환경에도’ 이름표를 붙입니다.
    """
    lines = text.strip("\n").split("\n")
    n = len(lines)
    starts, prev = [], -1
    for i, seg in enumerate(segs):
        anchor = seg[0]
        if i == 0:
            assert not anchor or lines[0].lstrip().startswith(anchor), f"첫 구간 앵커가 첫 줄과 다릅니다: {anchor!r} / {lines[0]!r}"
            idx = 0
        else:
            if anchor.startswith("="):
                idx = next((j for j in range(prev + 1, n) if lines[j].strip() == anchor[1:]), None)
            else:
                idx = next((j for j in range(prev + 1, n) if lines[j].lstrip().startswith(anchor)), None)
            assert idx is not None, f"앵커를 찾지 못했습니다: {anchor!r}  (cap={cap})"
        starts.append(idx)
        prev = idx
    starts.append(n)

    segs_html = []
    TAGS = {"lab": ("실습 전용", "tg lab"), "apply": ("내 환경에도", "tg apply")}
    for i, seg in enumerate(segs):
        title, note = seg[1], seg[2]
        tag = seg[3] if len(seg) > 3 else (tags or {}).get(i + 1)
        tg = f'<span class="{TAGS[tag][1]}">{TAGS[tag][0]}</span>' if tag else ""
        chunk = "\n".join(lines[starts[i] : starts[i + 1]])
        attrs = ' class="code"'
        if run:
            attrs += f' data-run="{run}" data-part="{i + 1}"'
        if skip:
            attrs += ' data-skip="1"'
        segs_html.append(
            '<div class="seg"><div class="segcode">'
            f'<span class="no" aria-hidden="true">{i + 1}</span><pre{attrs}><code>{_hl(chunk, lang)}</code></pre></div>'
            f'<div class="note"><div class="nt"><i>{i + 1}</i>{tg}{inline(title)}</div>{md(note)}</div></div>'
        )
    btn = "" if nocopy else '<button class="copy" type="button">전체 복사</button>'
    capspan = f'<span class="fn">{esc(cap)}</span>' if cap else ""
    return (
        '<div class="walk">'
        f'<div class="walk-cap">{capspan}<span class="wm">{n}줄 · {len(segs)}개 구간 — 구간마다 아래에 해설이 있습니다 · ‘전체 복사’ 는 구간을 이어 붙인 전체를 복사합니다</span>{btn}</div>'
        + "".join(segs_html)
        + "</div>"
    )


# ───────────────── 상자 · 표 · 단계
def out(text, label="예상 결과", read=None):
    """실제 환경에서 얻은 출력 예시 (실행 대상 아님). read = 읽는 법(마크다운)"""
    how = f'<div class="how"><b>읽는 법</b>{md(read)}</div>' if read else ""
    return f'<div class="expect"><div class="lbl">{esc(label)}</div><pre>{esc(text.strip(chr(10)))}</pre>{how}</div>'


def call(kind, label, body):
    """알림 상자. kind = info · tip · warn · danger, body = 마크다운"""
    cls = {"info": "callout", "tip": "callout tip", "warn": "callout warn", "danger": "callout danger"}[kind]
    return f'<div class="{cls}"><div class="lbl">{esc(label)}</div>{md(body)}</div>'


def details(summary, inner_html, open_=False):
    return f'<details{" open" if open_ else ""}><summary>{esc(summary)}</summary><div class="inner">{inner_html}</div></details>'


def table(headers, rows, cls=None, th_cls=None):
    """headers = [제목…], rows = [[셀…]…]. 셀은 마크다운(인라인) 문자열 또는 Raw(HTML)"""

    def cell(c):
        return c if isinstance(c, Raw) else inline(str(c))

    th_cls = th_cls or {}
    head = "".join(f'<th{(" class=" + chr(34) + th_cls[i] + chr(34)) if i in th_cls else ""}>{cell(h)}</th>' for i, h in enumerate(headers))
    body = "".join("<tr>" + "".join(f"<td>{cell(c)}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table{(" class=" + chr(34) + cls + chr(34)) if cls else ""}><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


def gloss(items):
    """items = [(용어, 작은 글씨(영문 등) 또는 None, 설명 마크다운), …]"""
    parts = []
    for term, small, desc in items:
        sm = f"<small>{inline(small)}</small>" if small else ""
        parts.append(f"<dt>{inline(term)}{sm}</dt><dd>{md(desc)}</dd>")
    return '<dl class="gloss">' + "".join(parts) + "</dl>"


def brief(what=None, why=None, result=None, apply=None, caution=None):
    """단계 맨 위의 ‘한눈에’ 상자 (모두 마크다운)"""
    rows = []
    for key, label, cls in (("what", "무엇을 하나요", ""), ("why", "왜 필요한가요", ""), ("result", "끝나면", ""), ("apply", "내 환경에서는", " apply"), ("caution", "주의", " warn")):
        v = {"what": what, "why": why, "result": result, "apply": apply, "caution": caution}[key]
        if v:
            rows.append(f'<div class="row{cls}"><b>{label}</b><div>{md(v)}</div></div>')
    return '<div class="brief">' + "".join(rows) + "</div>"


SCOPES = {
    "lab": ("실습 환경 준비", "scope"),
    "apply": ("내 환경에도 그대로 적용", "scope apply"),
    "check": ("확인 · 분석", "scope check"),
    "read": ("읽는 단계 (실행 없음)", "scope check"),
    "opt": ("선택 · 조건부 적용", "scope check"),
    "clean": ("정리 · 실습 리소스 전용", "scope"),
}


def donebox(sid):
    return f'<label class="donebox"><input type="checkbox" data-done="{sid}"> 이 단계를 끝냈어요 (체크는 이 브라우저에만 저장됩니다)</label>'


def step(sid, title, badge=None, meta=None, body="", opt=False, scope=None, done=True):
    b = ""
    if badge:
        b = f'<span class="badge{" opt" if opt else ""}">{esc(badge)}</span>'
    sc = ""
    if scope:
        label, cls = SCOPES[scope]
        sc = f'<span class="{cls}">{label}</span>'
    m = f'<p class="meta">{inline(meta)}</p>' if meta else ""
    d = donebox(sid) if done else ""
    return f'<div class="step" id="{sid}"><h3>{b}<span>{esc(title)}</span>{sc}</h3>{m}{body}{d}</div>'


def section(sid, title, small, inner):
    sm = f"<small>{esc(small)}</small>" if small else ""
    return f'<section id="{sid}"><h2>{esc(title)}{sm}</h2>{inner}</section>'


def diagram(svg):
    return f'<div class="diagram">{svg}</div>'
