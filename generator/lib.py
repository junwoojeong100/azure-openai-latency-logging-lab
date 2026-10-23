# -*- coding: utf-8 -*-
# 생성기 공용 도우미: 스니펫 읽기(마커 제거) · 코드/예상결과/콜아웃/스텝 HTML 조각
import html, os, re

HERE = os.path.dirname(os.path.abspath(__file__))

SN = os.path.join(HERE, "..", "snippets") + os.sep
VMF = os.path.join(HERE, "vmfiles") + os.sep


def esc(s):
    return html.escape(s, quote=False)


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


def out(text, label="예상 결과"):
    """실제 환경에서 얻은 출력 예시 (실행 대상 아님)"""
    return f'<div class="expect"><div class="lbl">{esc(label)}</div><pre>{esc(text.strip(chr(10)))}</pre></div>'


def note(body_html, label="예상 결과"):
    return f'<div class="expect"><div class="lbl">{esc(label)}</div>{body_html}</div>'


def call(kind, label, body_html):
    cls = {"info": "callout", "warn": "callout warn", "danger": "callout danger"}[kind]
    return f'<div class="{cls}"><div class="lbl">{esc(label)}</div>{body_html}</div>'


def details(summary, inner_html, open_=False):
    return f'<details{" open" if open_ else ""}><summary>{esc(summary)}</summary><div class="inner">{inner_html}</div></details>'


def step(sid, title, badge=None, meta=None, body="", opt=False):
    b = ""
    if badge:
        b = f'<span class="badge{" opt" if opt else ""}">{esc(badge)}</span>'
    m = f'<p class="meta">{meta}</p>' if meta else ""
    return f'<div class="step" id="{sid}"><h3>{b}<span>{esc(title)}</span></h3>{m}{body}</div>'


def section(sid, title, small, inner):
    sm = f"<small>{esc(small)}</small>" if small else ""
    return f'<section id="{sid}"><h2>{esc(title)}{sm}</h2>{inner}</section>'
