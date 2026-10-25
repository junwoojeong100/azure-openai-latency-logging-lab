# -*- coding: utf-8 -*-
# Foundry 에이전트 모니터링 실습 가이드(1 page HTML) 생성기. 사용: python3 build_foundry.py [출력 경로]
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from template import THEME_JS, CSS, JS
from common import toc_html
import foundry_a
import foundry_b
import foundry_c

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "foundry-agents-monitoring-lab.html")

m = foundry_a.measured()

TOC = [
    ("grp", "처음 읽는 분께"), ("start", "이 가이드가 하는 일"), ("terms", "용어 사전"), ("howto", "읽는 법 · 전체 단계"), ("prep", "준비물 · 안전 수칙"),
    ("grp", "A · 환경 만들기"), ("a1", "A1 도구 · 로그인"), ("a2", "A2 azd up"), ("a3", "A3 확인 · 도우미 함수"),
    ("grp", "B · 호출"), ("b1", "B1 azd 로 호출"), ("b2", "B2 클라이언트 스크립트"), ("b3", "B3 기존 앱 전환 공수"),
    ("grp", "C · 확인과 분석"), ("c1", "C1 트레이스 도착"), ("c2", "C2 에이전트 단위 지연"), ("c3", "C3 느린 곳 찾기"), ("c4", "C4 요청 한 건 따라가기"), ("c5", "C5 토큰 · 모델 메트릭"), ("c6", "C6 포털에서 보는 곳"), ("c7", "C7 앱에서 본 시간 · 앱 최소 기록"),
    ("grp", "D · 알림 · 장애 재현"), ("d1", "D1 알림 만들기"), ("d2", "D2 장애 만들기"), ("d3", "D3 알림 확인 · 실패 원인"), ("d4", "D4 복구 · 알림 끄기"),
    ("grp", "E · 판단 기준 · 정리와 삭제"), ("e1", "E1 내 앱에는 어느 방법? · 대응표"), ("e2", "E2 삭제"),
    ("grp", "부록"), ("x1", "A 확인한 사실"), ("x2", "B 문제 해결"), ("x3", "C 운영 적용 · 개인정보"), ("x4", "D 리소스 · 줄 수 상세"),
]

hero = f"""<header class="hero">
<div class="eyebrow">Microsoft Foundry · 프롬프트 에이전트 · MAF 호스티드 에이전트</div>
<h1>같은 모니터링, Foundry 에이전트로 만들면 얼마나 간단해질까</h1>
<p class="lead">Azure OpenAI 모델을 부르는 앱이 <b>가끔 느릴 때</b>, 그 시간이 어디서 쓰였는지 <b>요청 한 건씩</b> 보려면 보통 로그 · 트레이스 설정을 직접 해야 합니다(짝 가이드인 가이드 1 이 그 방법을 다룹니다).
이 가이드는 모델 호출을 <b>Foundry 에이전트</b>(프롬프트 에이전트 · MAF 호스티드 에이전트)를 거치게 바꾸면 <b>서버 쪽 모니터링이 얼마나 단순해지는지</b>를 직접 해 보며 확인합니다.
새 리소스 그룹에서 <code>azd up</code> 한 번으로 환경을 만들고, 에이전트를 호출해 <b>코드 없이 쌓이는 트레이스</b>를 보고, 알림까지 만들어 봅니다.
서버 쪽(에이전트 ↔ 모델) 모니터링 설정은 <b>{foundry_a.OLD_TOTAL}줄 → {foundry_a.NEW_TOTAL}줄</b>로 줄지만, <b>앱 ↔ 에이전트 구간은 앱이 따로 기록해야 한다</b>는 점도 함께 정리합니다.
명령은 복사해서 그대로 실행할 수 있고, 코드는 <b>한 덩어리마다 무슨 일을 하는지 바로 아래에 해설</b>이 붙어 있습니다.</p>
<div class="chips">
<span class="chip"><b>검증</b> 2026-10-24 · Korea Central · gpt-5.4-mini · azd 1.37.1</span>
<span class="chip"><b>소요</b> 실행 약 25분 + 해설 읽기(B3 · C7 등) 약 10분 (azd up 약 {(m['up_total_s'] + 59) // 60}분 포함)</span>
<span class="chip"><b>비용</b> 토큰 · 수집 소액 (호스티드는 컨테이너 사용 시간)</span>
<span class="chip"><b>필요한 것</b> Azure 구독 · 터미널(bash) · azd</span>
<a class="chip" href="#x1"><b>검증 기록</b> 보기 →</a>
<a class="chip" href="aoai-logging-hands-on-lab.html"><b>가이드 1</b> AOAI + VM 로그 수집 →</a>
</div>
</header>"""

body = foundry_a.build_front() + foundry_a.build() + foundry_b.build() + foundry_c.build()
foot = '<footer class="foot">이 문서의 명령 · 코드 · 쿼리는 저장소의 <code>foundry/</code> 폴더 파일과 같은 내용이며, 2026-10-24 실제 Azure 구독의 새 리소스 그룹에서 실행해 검증했습니다(부록 A). B3 · C7 의 표는 2026-10-24 추가 시험 결과이고, 수치는 한 환경에서 잰 값이니 운영 계획에는 본인 환경에서 다시 측정하세요.</footer>'

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Foundry 에이전트 모니터링 실습 가이드 — 프롬프트 에이전트 · MAF 호스티드 에이전트</title>
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
