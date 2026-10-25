# -*- coding: utf-8 -*-
# AOAI + VM 로그 수집 실습 가이드(1 page HTML) 생성기. 사용: python3 build.py [출력 경로]
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from template import THEME_JS, CSS, JS
from common import toc_html
import part_a
import part_b
import part_c

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "aoai-logging-hands-on-lab.html")

TOC = [
    ("grp", "처음 읽는 분께"), ("start", "이 가이드가 하는 일"), ("terms", "용어 사전"), ("howto", "읽는 법 · 전체 단계"), ("prep", "준비물 · 안전 수칙"),
    ("grp", "A · 실습 환경 만들기"), ("a1", "A1 변수 · 도우미 함수"), ("a2", "A2 RG · 워크스페이스 · 네트워크"), ("a3", "A3 Azure OpenAI 배포"), ("a4", "A4 RHEL VM · 관리 ID"), ("a5", "A5 VM 준비"),
    ("grp", "B · 로그 켜기"), ("b1", "B1 · R1 AOAI 진단 설정"), ("b2", "B2 · R5 모니터링 에이전트 · 수집 규칙"), ("b3", "B3 · R3·R4 데모 앱"), ("b4", "B4 · R7 합성 probe"), ("b5", "B5 · R2 메트릭"), ("b6", "B6 · R8 알림"), ("b7", "B7 · R6 네트워크"),
    ("grp", "C · 확인과 분석"), ("c1", "C1 데이터 도착 · 지연"), ("c2", "C2 요청 단위 대조"), ("c3", "C3 시간 패턴"), ("c4", "C4 VM · probe · cron"), ("c5", "C5 체크리스트 · 읽는 법"),
    ("grp", "D · 정리"), ("d1", "D 삭제 · 중지"),
    ("grp", "부록"), ("x1", "A 확인한 사실"), ("x2", "B 내 환경에 적용하기"), ("x3", "C 문제 해결"), ("x4", "D 운영 적용 시 차이"), ("x5", "E 분석 쿼리 모음"),
]

hero = """<header class="hero">
<div class="eyebrow">Azure OpenAI · 응답 지연 · 로그 수집</div>
<h1>Azure OpenAI 응답이 느릴 때 원인을 찾는 로그 수집 실습 가이드</h1>
<p class="lead">‘가끔 AOAI 응답이 느리다’는 말만으로는 원인을 알 수 없습니다. 느린 시간이 <b>앱 안 · 앱과 AOAI 사이 · AOAI 서비스</b> 중 어디서 생겼는지 구분하려면, 같은 요청의 기록을 세 곳에서 남겨 시각과 요청 ID 로 맞춰 봐야 합니다.
이 가이드는 그 로그를 모으는 방법을 <b>새 리소스 그룹에서 처음부터 직접 만들어 보며</b> 설명합니다. 모든 명령은 복사해서 그대로 실행할 수 있고, 코드는 <b>한 덩어리마다 무슨 일을 하는지 바로 아래에 해설</b>이 붙어 있습니다.</p>
<div class="chips">
<span class="chip"><b>검증</b> 2026-10-23 · Korea Central · RHEL 9.8 · gpt-4.1-mini</span>
<span class="chip"><b>소요</b> 약 1시간 (명령 · 로그 대기, 읽는 시간은 별도)</span>
<span class="chip"><b>비용</b> 약 $2 안팎 (예상 · 변동)</span>
<span class="chip"><b>필요한 것</b> Azure 구독 · 터미널(bash)</span>
<a class="chip" href="#x1"><b>검증 기록</b> 보기 →</a>
<a class="chip" href="foundry-agents-monitoring-lab.html"><b>비교</b> Foundry 에이전트 가이드 →</a>
</div>
</header>"""

body = part_a.build_front() + part_a.build() + part_b.build() + part_c.build()
foot = '<footer class="foot">이 문서의 명령 · 코드 · 쿼리는 이 저장소의 <code>snippets/</code> 와 <code>generator/</code> 파일과 같은 내용이며, 2026-10-23 실제 Azure 구독의 새 리소스 그룹에서 실행해 검증했습니다(부록 A). 데모 앱 · probe 는 실습용이며 운영 적용 전에 부록 D 를 확인하세요. 수치는 한 환경에서 잰 값입니다.</footer>'

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
<nav class="toc" aria-label="목차">{toc_html(TOC)}</nav>
<main>{body}</main>
</div>
{foot}
{JS}
</body>
</html>
"""
open(OUT, "w", encoding="utf-8").write(html)
print("written", OUT, len(html), "chars")
