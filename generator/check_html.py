#!/usr/bin/env python3
# 생성된 HTML 가이드의 정적 점검 (Azure 연결 · 비용 없음).
# 사용: python3 generator/check_html.py [HTML 파일 ...]   (생략하면 저장소 루트의 두 가이드를 점검)
#
# 점검 항목
#  1. id 중복 없음 · 모든 #앵커 링크와 목차 링크가 실제 id 를 가리킴 · ‘끝냈어요’ 체크의 id 가 단계 id 와 일치
#  2. 코드 해설(walk): 구간 수 = 해설 수, 실행 블록의 data-part 가 1..n 으로 이어지고 같은 단계 · 같은 skip 값
#  3. 실행 단계(data-run) 목록 출력 — 러너(run_html.py · run_foundry_html.py)가 실행할 단계 수 확인
#  4. 테마: 인라인 style 없음 · 테마 변수 정의 밖에 하드코딩 색(#hex · rgb · hsl) 없음 · 테마 감지 스크립트가 <style> 앞에 있음
#  5. 본문에 마크다운 찌꺼기(**, `)나 이스케이프되지 않은 꺾쇠 자리 표시자가 보이지 않음
import html as htmllib
import os
import re
import sys
from collections import Counter
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))


class WalkParser(HTMLParser):
    """<div class="walk"> 안의 구간(.seg) · 해설(.note) · 실행 코드(<pre data-run>)를 모은다"""

    def __init__(self):
        super().__init__()
        self.walks, self.cur, self.depth, self.start = [], None, 0, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div":
            self.depth += 1
            cls = a.get("class", "")
            if cls == "walk":
                self.cur, self.start = {"segs": 0, "notes": 0, "pres": []}, self.depth
            elif self.cur is not None and cls == "seg":
                self.cur["segs"] += 1
            elif self.cur is not None and cls == "note":
                self.cur["notes"] += 1
        elif tag == "pre" and self.cur is not None and "data-run" in a:
            self.cur["pres"].append(a)

    def handle_endtag(self, tag):
        if tag == "div":
            if self.cur is not None and self.depth == self.start:
                self.walks.append(self.cur)
                self.cur = None
            self.depth -= 1


def check(path):
    src = open(path, encoding="utf-8").read()
    errs, notes = [], []

    # 1. id · 앵커
    ids = re.findall(r'\bid="([^"]+)"', src)
    dup = [k for k, v in Counter(ids).items() if v > 1]
    if dup:
        errs.append(f"중복 id: {dup}")
    idset = set(ids)
    for a in sorted(set(re.findall(r'href="#([^"]+)"', src))):
        if a not in idset:
            errs.append(f"끊어진 앵커 링크: #{a}")
    steps = set(re.findall(r'<div class="step" id="([^"]+)"', src))
    for d in re.findall(r'data-done="([^"]+)"', src):
        if d not in steps:
            errs.append(f"data-done 가 단계 id 가 아님: {d}")
    toc = re.search(r'<nav class="toc".*?</nav>', src, re.S)
    toc_ids = re.findall(r'href="#([^"]+)"', toc.group(0)) if toc else []
    notoc = sorted(steps - set(toc_ids) - {"x1", "x2", "x3", "x4"})
    if notoc:
        notes.append(f"목차에 없는 단계(체크는 되지만 목차 표시 없음): {notoc}")

    # 2. walk (코드 해설)
    parser = WalkParser()
    parser.feed(src)
    if not parser.walks:
        errs.append("코드 해설(walk)이 하나도 없음")
    for w in parser.walks:
        if w["segs"] != w["notes"] or w["segs"] == 0:
            errs.append(f"walk 의 구간 수({w['segs']}) != 해설 수({w['notes']})")
        pres = w["pres"]
        if not pres:
            continue
        if len(pres) != w["segs"]:
            errs.append(f"walk 의 구간({w['segs']})마다 실행 블록이 하나씩 있어야 하는데 {len(pres)}개: data-run={pres[0].get('data-run')}")
            continue
        runs = {p.get("data-run") for p in pres}
        skips = {p.get("data-skip") for p in pres}
        parts = [p.get("data-part") for p in pres]
        if len(runs) != 1 or len(skips) != 1:
            errs.append(f"walk 안에서 data-run/skip 이 섞임: {runs} {skips}")
        if parts != [str(i) for i in range(1, len(pres) + 1)]:
            errs.append(f"walk 의 data-part 가 1..n 이 아님: {parts}")
    n_walk = len(parser.walks)
    notes.append(f"코드 해설 {n_walk}개 · 구간 {sum(w['segs'] for w in parser.walks)}개")

    # 3. 실행 단계
    pre_pat = re.compile(r'<pre class="code" data-run="([^"]+)"(?: data-part="(\d+)")?( data-skip="1")?>')
    runs_all = pre_pat.findall(src)
    stages = []
    for sid, part, skip in runs_all:
        if part and int(part) > 1:
            continue
        stages.append((sid, bool(skip)))
    notes.append(f"실행 블록 {len(stages)}개(건너뜀 {sum(1 for _, s in stages if s)}개), 단계: {sorted({s for s, _ in stages})}")

    # 4. 테마
    if 'style="' in src:
        errs.append(f"인라인 style 속성 {src.count('style=' + chr(34))}개")
    css = re.search(r"<style>(.*?)</style>", src, re.S)
    css_txt = css.group(1) if css else ""
    css_nodef = re.sub(r":root\s*\{.*?\}", "", css_txt, flags=re.S)
    css_nodef = re.sub(r'html\[data-theme="dark"\]\s*\{.*?\}', "", css_nodef, flags=re.S)
    bad = re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", css_nodef)
    # 변수(--cp-*) 정의 줄이 아닌 곳의 box-shadow rgba 는 그림자 색이라 허용 목록에 둔다
    bad = [b for b in bad if b not in ("rgba(",)]
    if bad:
        errs.append(f"테마 변수 밖의 하드코딩 색: {sorted(set(bad))[:5]}")
    if "scoutTheme" not in src.split("<style>")[0]:
        errs.append("테마 감지 스크립트가 <style> 앞에 없음")

    # 5. 본문 찌꺼기
    body = re.sub(r"<style.*?</style>|<script.*?</script>|<pre.*?</pre>", " ", src, flags=re.S)
    body = re.sub(r"<code>.*?</code>", " ", body, flags=re.S)
    text = htmllib.unescape(re.sub(r"<[^>]+>", " ", body))
    for pat, what in ((r"\*\*", "마크다운 굵게(**)"), (r"`", "백틱(`)")):
        if re.search(pat, text):
            m = re.search(r".{25}" + pat + r".{25}", text, re.S)
            errs.append(f"본문에 {what} 가 남아 있음: …{m.group(0).strip() if m else ''}…")
    return errs, notes


def main():
    targets = sys.argv[1:] or [os.path.join(ROOT, "aoai-logging-hands-on-lab.html"), os.path.join(ROOT, "foundry-agents-monitoring-lab.html")]
    rc = 0
    for p in targets:
        errs, notes = check(p)
        print(f"== {os.path.relpath(p, ROOT)}  ({os.path.getsize(p):,} bytes)")
        for n in notes:
            print("  · " + n)
        for e in errs:
            print("  ✘ " + e)
        if not errs:
            print("  ✔ 모든 점검 통과")
        rc |= 1 if errs else 0
    sys.exit(rc)


if __name__ == "__main__":
    main()
