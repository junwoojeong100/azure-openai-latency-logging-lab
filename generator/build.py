# -*- coding: utf-8 -*-
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from template import THEME_JS, CSS, JS
import part_a, part_b, part_c

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "aoai-logging-hands-on-lab.html")

TOC = [
    ("grp", "시작하기 전에"), ("start", "개요 · 구성 · 준비물"),
    ("grp", "A · 실습 환경 만들기"), ("a1", "A1 변수 · 도우미 함수"), ("a2", "A2 RG · 워크스페이스 · 네트워크"), ("a3", "A3 Azure OpenAI 배포"), ("a4", "A4 RHEL VM · 관리 ID"), ("a5", "A5 VM 준비"),
    ("grp", "B · 로그 켜기"), ("b1", "B1 · R1 AOAI 진단 설정"), ("b2", "B2 · R5 에이전트 · 수집 규칙"), ("b3", "B3 · R3·R4 데모 앱"), ("b4", "B4 · R7 합성 probe"), ("b5", "B5 · R2 메트릭"), ("b6", "B6 · R8 알림"), ("b7", "B7 · R6 네트워크"),
    ("grp", "C · 확인과 분석"), ("c1", "C1 데이터 도착 · 지연"), ("c2", "C2 요청 단위 대조"), ("c3", "C3 시간 패턴"), ("c4", "C4 VM · probe · cron"), ("c5", "C5 체크리스트 · 읽는 법"),
    ("grp", "D · 정리"), ("d1", "D 삭제 · 중지"),
    ("grp", "부록"), ("x1", "A 확인한 사실"), ("x2", "B 가이드 수정 내역"), ("x3", "C 문제 해결"), ("x4", "D 운영 적용 시 차이"),
]
toc = ""
for k, v in TOC:
    toc += f'<div class="grp">{v}</div>' if k == "grp" else f'<a href="#{k}">{v}</a>'

hero = """<header class="hero">
<div class="eyebrow">Azure OpenAI · 응답 지연 · 로그 수집</div>
<h1>로그 수집 실습 가이드 — 리소스 그룹부터 새로 만들어 끝까지</h1>
<p class="lead">앱 · VM · Azure OpenAI 세 구간에서 요청 단위 로그를 모으는 22장 가이드(R1~R8)를, 새 리소스 그룹에 실습 환경을 만들어 직접 적용하고 결과를 확인합니다. 모든 코드 블록은 복사해서 그대로 실행할 수 있습니다.</p>
<div class="chips">
<span class="chip"><b>검증</b> 2026-10-23 · Korea Central · RHEL 9.8 · gpt-4.1-mini</span>
<span class="chip"><b>소요</b> 약 1시간 (로그 대기 포함)</span>
<span class="chip"><b>비용</b> 약 $2 이내 (예상)</span>
<span class="chip"><b>형식</b> 한 페이지 · bash · 복사 버튼</span>
<a class="chip" href="#x1"><b>검증 기록</b> 보기 →</a>
<a class="chip" href="foundry-agents-monitoring-lab.html"><b>비교</b> Foundry 에이전트 가이드 →</a>
</div>
</header>"""

body = part_a.build() + part_b.build() + part_c.build()
foot = '<footer class="foot">이 문서의 명령·코드·쿼리는 22장 가이드의 스니펫과 같은 내용이며, 2026-10-23 실제 Azure 구독의 새 리소스 그룹에서 실행해 검증했습니다. 데모 앱·probe 는 실습용이며 운영 적용 전에 부록 D 를 확인하세요.</footer>'

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Azure OpenAI 응답 지연 — 로그 수집 실습 가이드</title>
{THEME_JS}
<style>{CSS}</style>
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
