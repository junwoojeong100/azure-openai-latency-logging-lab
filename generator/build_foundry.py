# -*- coding: utf-8 -*-
# Foundry 에이전트 모니터링 실습 가이드(1 page HTML) 생성기. 사용: python3 build_foundry.py [출력 경로]
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from template import THEME_JS, CSS, JS
import foundry_a
import foundry_b
import foundry_c

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "foundry-agents-monitoring-lab.html")

EXTRA_CSS = """
.step h4 { margin: 18px 0 6px; font-size: 15px; }
table.cmp th:first-child, table.cmp td:first-child { width: 22%; }
table.cmp td:nth-child(3), table.cmp td:nth-child(4) { background: var(--cp-accent-soft); }
table.cmp th small { font-weight: 400; color: var(--cp-text-soft); }
sup { font-size: 0.75em; color: var(--cp-text-soft); }
.foot-note { font-size: 12.5px; color: var(--cp-text-muted); margin: 4px 0 12px; }
.two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.two ol { margin: 4px 0; padding-left: 22px; font-size: 14px; }
@media (max-width: 1000px) { .two { grid-template-columns: minmax(0, 1fr); } }
"""

m = foundry_a.measured()

TOC = [
    ("grp", "시작하기 전에"), ("start", "개요 · 비교 · 준비물"),
    ("grp", "A · 환경 만들기"), ("a1", "A1 도구 · 로그인"), ("a2", "A2 azd up"), ("a3", "A3 확인 · 도우미 함수"),
    ("grp", "B · 호출"), ("b1", "B1 azd 로 호출"), ("b2", "B2 클라이언트 스크립트"),
    ("grp", "C · 확인과 분석"), ("c1", "C1 트레이스 도착"), ("c2", "C2 에이전트 단위 지연"), ("c3", "C3 느린 곳 가리기"), ("c4", "C4 요청 한 건 따라가기"), ("c5", "C5 토큰 · 모델 메트릭"), ("c6", "C6 포털에서 보는 곳"),
    ("grp", "D · 알림 · 장애 재현"), ("d1", "D1 알림 만들기"), ("d2", "D2 장애 만들기"), ("d3", "D3 알림 확인 · 실패 원인"), ("d4", "D4 복구 · 알림 끄기"),
    ("grp", "E · 비교 정리와 삭제"), ("e1", "E1 R1~R8 은 어디로"), ("e2", "E2 삭제"),
    ("grp", "부록"), ("x1", "A 확인한 사실"), ("x2", "B 문제 해결"), ("x3", "C 운영 적용 · 개인정보"), ("x4", "D 리소스 · 줄 수 상세"),
]
toc = ""
for k, v in TOC:
    toc += f'<div class="grp">{v}</div>' if k == "grp" else f'<a href="#{k}">{v}</a>'

hero = f"""<header class="hero">
<div class="eyebrow">Microsoft Foundry · 프롬프트 에이전트 · MAF 호스티드 에이전트</div>
<h1>같은 모니터링, Foundry 에이전트로 만들면 얼마나 간단해질까</h1>
<p class="lead">AOAI 로그 수집 실습(R1~R8)이 만들던 요청 단위 모니터링을 <b>Foundry 프로젝트 · 프롬프트 에이전트 · MAF 호스티드 에이전트</b>로 다시 만들어, 새 리소스 그룹에서 실제로 실행한 결과를 비교합니다.
설정 코드는 <b>{foundry_a.OLD_TOTAL}줄 → {foundry_a.NEW_TOTAL}줄</b>, 에이전트 코드에는 텔레메트리 코드가 <b>0줄</b>, 환경은 <code>azd up</code> 한 번이면 만들어집니다.</p>
<div class="chips">
<span class="chip"><b>검증</b> 2026-10-24 · Korea Central · gpt-5.4-mini · azd 1.37.1</span>
<span class="chip"><b>소요</b> azd up 약 {(m['up_total_s'] + 59) // 60}분 · 전체 약 25분</span>
<span class="chip"><b>비용</b> 토큰 · 수집 소액 (호스티드는 컨테이너 사용 시간)</span>
<span class="chip"><b>형식</b> 한 페이지 · bash · 복사 버튼</span>
<a class="chip" href="#x1"><b>검증 기록</b> 보기 →</a>
<a class="chip" href="aoai-logging-hands-on-lab.html"><b>원본</b> AOAI + VM 가이드 →</a>
</div>
</header>"""

body = foundry_a.build() + foundry_b.build() + foundry_c.build()
foot = '<footer class="foot">이 문서의 명령 · 코드 · 쿼리는 저장소의 <code>foundry/</code> 폴더 파일과 같은 내용이며, 2026-10-24 실제 Azure 구독의 새 리소스 그룹에서 실행해 검증했습니다(부록 A). 수치는 한 환경에서 잰 값이니 운영 계획에는 본인 환경에서 다시 측정하세요.</footer>'

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Foundry 에이전트 모니터링 실습 가이드 — 프롬프트 에이전트 · MAF 호스티드 에이전트</title>
{THEME_JS}
<style>{CSS}{EXTRA_CSS}</style>
</head>
<body>
{hero}
<div class="layout">
<nav class="toc" aria-label="목차">{toc}</nav>
<main>{body}</main>
</div>
{foot}
{JS}
</body>
</html>
"""
open(OUT, "w", encoding="utf-8").write(html)
print("written", OUT, len(html), "bytes")
