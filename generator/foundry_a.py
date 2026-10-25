# -*- coding: utf-8 -*-
# 처음 읽는 분께(개요 · 용어 · 읽는 법 · 준비물) / A · 환경 만들기 (Foundry 에이전트 모니터링 가이드)
import json
import os
import re

from lib import *
from common import *

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))


def measured():
    """실제 Azure 실행에서 잰 값 (foundry_expected/measured.json)"""
    return json.load(open(os.path.join(EXPECTED, "measured.json"), encoding="utf-8"))


def loc(*paths):
    """빈 줄 · 주석 · 슬라이드 마커를 뺀 줄 수"""
    n = 0
    for p in paths:
        for line in open(os.path.join(ROOT, p), encoding="utf-8").read().split("\n"):
            s = line.strip()
            if not s or s.startswith(("#", "//")) or re.search(r"(>>>|<<<) slide:", line):
                continue
            n += 1
    return n


OLD = {
    "R1": loc("snippets/R1_aoai_diagnostic_settings.sh"),
    "R3": loc("snippets/R3_aoai_call_log.py", "snippets/R3_usage_example.py"),
    "R4": loc("snippets/R4_appinsights_otel.py", "snippets/R4_telemetry.env.sample", "snippets/R4_systemd.sh"),
    "R5": loc("snippets/R5_vm_ama_dcr.sh", "snippets/R5_dcr_linux.json"),
    "R6": loc("snippets/R6_network_logs.sh"),
    "R7": loc(
        "snippets/R7_aoai_probe.sh", "snippets/R7_aoai_snapshot.sh", "snippets/R7_install.sh",
        "snippets/R7_aoai-probe.service", "snippets/R7_aoai-probe.timer", "snippets/R7_aoai-probe.env.sample",
    ),
    "R8": loc("snippets/R8_alerts.sh"),
}
OLD_TOTAL = sum(OLD.values())
NEW = {"connect": loc("foundry/scripts/connect-appinsights.sh"), "alerts": loc("foundry/scripts/alerts.sh")}
NEW_TOTAL = sum(NEW.values())
AGENT_LINES = loc("foundry/src/report-maf-agent/main.py")
CLIENT_LINES = loc("foundry/invoke_agents.py")
YAML_LINES = loc("foundry/azure.yaml")


def _hook_lines():
    """azure.yaml 의 hooks 블록 줄 수(빈 줄 · 주석 제외)"""
    n, inside = 0, False
    for line in open(os.path.join(ROOT, "foundry/azure.yaml"), encoding="utf-8").read().split("\n"):
        if line.startswith("hooks:"):
            inside = True
        elif inside and line and not line.startswith((" ", "#")):
            break
        if inside and line.strip() and not line.strip().startswith("#"):
            n += 1
    return n


HOOK_LINES = _hook_lines()
PCT = round(100 * (1 - NEW_TOTAL / OLD_TOTAL))

OLD_RESOURCES = [
    "Log Analytics 워크스페이스", "Application Insights", "진단 설정(AOAI → 워크스페이스)", "데이터 수집 규칙(DCR)", "DCR 연결",
    "Azure Monitor Agent 확장", "Network Watcher 확장", "Connection Monitor", "flow log 용 저장소 계정", "VNet flow log",
    "알림 수신 그룹", "메트릭 알림 규칙", "로그 알림 규칙",
]
NEW_RESOURCES = [
    "Log Analytics 워크스페이스", "Application Insights", "Foundry 프로젝트 ↔ Application Insights 연결", "역할 할당(호출자 · 프로젝트 관리 ID)",
    "알림 수신 그룹", "로그 알림 규칙",
]

# 이 가이드의 ‘기본 그림’: 요청 한 건의 시간 — 서버 트레이스에 보이는 구간과 안 보이는 구간
SVG_TIMELINE = """<svg viewBox="0 0 960 380" role="img" aria-label="요청 한 건의 시간: 앱 · SDK · 인증, 네트워크, Foundry 서버의 invoke_agent(안에 모델 호출 chat), 응답 도착. 서버 트레이스는 invoke_agent 와 chat 구간만 보여 주고 나머지는 앱이 직접 기록해야 합니다">
<text class="ttl" x="20" y="26">요청 한 건의 시간 — 서버 트레이스에 보이는 구간 / 안 보이는 구간</text>
<path class="brka" d="M40,100 L40,88 L920,88 L920,100"/>
<text class="lblb" x="480" y="76" text-anchor="middle">클라이언트(앱)가 잰 시간(client_ms) — 앱 최소 기록 (B3 · C7)</text>
<rect class="boxw" x="40" y="108" width="170" height="62" rx="10"/>
<text class="lblb" x="52" y="132">① 앱 · SDK · 인증</text><text class="sub" x="52" y="150">재시도 대기 포함</text>
<rect class="boxw" x="210" y="108" width="110" height="62" rx="10"/>
<text class="lblb" x="222" y="132">② 네트워크</text><text class="sub" x="222" y="150">앱 → Foundry</text>
<rect class="boxa" x="320" y="108" width="440" height="62" rx="10"/>
<text class="lblb" x="332" y="132">③ Foundry 서버 — 에이전트 실행(invoke_agent)</text>
<rect class="boxg" x="332" y="140" width="120" height="24" rx="6"/><text class="sub" x="342" y="157">런타임</text>
<rect class="boxg" x="452" y="140" width="190" height="24" rx="6"/><text class="sub" x="462" y="157">모델 호출(chat)</text>
<rect class="boxg" x="642" y="140" width="106" height="24" rx="6"/><text class="sub" x="652" y="157">런타임</text>
<rect class="boxw" x="760" y="108" width="160" height="62" rx="10"/>
<text class="lblb" x="772" y="132">④ 응답 도착</text><text class="sub" x="772" y="150">수신 · 앱의 후처리</text>
<path class="brkg" d="M320,182 L320,194 L760,194 L760,182"/>
<text class="lblb" x="540" y="214" text-anchor="middle">invoke_agent 스팬 — 서버 트레이스 (C2 · C3)</text>
<path class="brkg" d="M452,224 L452,236 L642,236 L642,224"/>
<text class="lbl" x="547" y="256" text-anchor="middle">chat 스팬 — 모델 호출 · 토큰 (C3 · C5)</text>
<path class="brkw" d="M40,182 L40,194 L320,194 L320,182"/>
<text class="lbl" x="180" y="214" text-anchor="middle">서버 트레이스에 없음</text>
<text class="sub" x="180" y="232" text-anchor="middle">① ② ≈ client_ms − invoke_agent</text>
<rect class="box" x="40" y="280" width="880" height="84" rx="12"/>
<text class="ttl" x="56" y="302">실측으로 확인한 것 (노트북 → Korea Central, 2026-10-24)</text>
<text class="lbl" x="56" y="326">같은 호출을 클라이언트와 서버가 잰 시간의 차이: 7건은 328~488ms, 새 클라이언트의 첫 호출은 1,882ms.</text>
<text class="lbl" x="56" y="348">429(한도 초과) 뒤 SDK 재시도 대기 약 4.6초는 서버 트레이스에 없고, 시작 전에 거절된 호출(없는 모델 배포 404)은 서버 흔적이 없었습니다.</text>
</svg>"""

# 구성도
SVG = """<svg viewBox="0 0 960 330" role="img" aria-label="구성도: 클라이언트가 Foundry 프로젝트의 프롬프트 에이전트와 호스티드 에이전트를 호출하면 플랫폼과 컨테이너가 Application Insights 로 트레이스를 보냅니다">
<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="arrh"/></marker></defs>
<rect class="box" x="16" y="52" width="196" height="150" rx="14"/>
<text class="ttl" x="32" y="76">클라이언트</text>
<text class="lbl" x="32" y="104">invoke_agents.py</text><text class="sub" x="32" y="124">Foundry SDK · 39줄</text>
<text class="sub" x="32" y="150">traceparent 헤더로</text><text class="sub" x="32" y="168">trace_id 를 직접 지정</text>
<rect class="box" x="268" y="28" width="360" height="274" rx="14"/>
<text class="ttl" x="284" y="52">FOUNDRY 프로젝트 · Korea Central</text>
<rect class="boxa" x="284" y="66" width="328" height="64" rx="10"/>
<text class="lbl" x="298" y="92">프롬프트 에이전트</text><text class="sub" x="298" y="112">코드 없음 · 모델 + 지시문 (azure.yaml)</text>
<rect class="boxa" x="284" y="142" width="328" height="64" rx="10"/>
<text class="lbl" x="298" y="168">MAF 호스티드 에이전트</text><text class="sub" x="298" y="188">main.py 16줄 · 세션마다 격리된 컨테이너</text>
<rect class="box" x="284" y="220" width="328" height="64" rx="10"/>
<text class="lbl" x="298" y="246">모델 배포 gpt-5.4-mini</text><text class="sub" x="298" y="266">Foundry Models · 메트릭은 설정 없이 자동</text>
<rect class="boxa" x="692" y="28" width="252" height="274" rx="14"/>
<text class="ttl" x="708" y="52">APPLICATION INSIGHTS</text>
<text class="sub" x="708" y="82">requests</text><text class="sub" x="708" y="102">dependencies (invoke_agent · chat)</text><text class="sub" x="708" y="122">traces (컨테이너 로그)</text>
<text class="sub" x="708" y="142">exceptions</text>
<text class="lbl" x="708" y="184">플랫폼 스팬 + 컨테이너 스팬</text><text class="sub" x="708" y="204">코드 없이 자동 수집</text>
<text class="lbl" x="708" y="248">로그 알림 2개</text><text class="sub" x="708" y="268">느린 실행 · 실패한 실행</text>
<path class="arr" d="M212,127 L268,127" marker-end="url(#ah)"/>
<path class="arr" d="M612,98 L692,98" marker-end="url(#ah)"/>
<path class="arr" d="M612,174 L692,150" marker-end="url(#ah)"/>
<path class="arr" d="M448,206 L448,220" marker-end="url(#ah)"/>
<text class="sub" x="222" y="118">호출</text>
<text class="sub" x="624" y="90">트레이스</text>
</svg>"""


def _row(cells, cls=None):
    tds = "".join(f"<td>{c}</td>" for c in cells)
    return f"<tr{(' class=' + chr(34) + cls + chr(34)) if cls else ''}>{tds}</tr>"


def compare_table():
    m = measured()
    rows = [
        ("모니터링 설정 코드·명령 줄 수<sup>①</sup>", f"<b>{OLD_TOTAL}줄</b> (R1·R3~R8)", f"<b>{NEW_TOTAL}줄</b>", f"<b>{NEW_TOTAL}줄</b> (같은 스크립트)"),
        ("코드 안의 텔레메트리 코드", f"<b>{OLD['R3'] + OLD['R4']}줄</b> (앱 코드에 R3 {OLD['R3']} + R4 {OLD['R4']})", f"에이전트의 텔레메트리 코드 <b>0줄</b> · 앱 최소 기록 약 10~15줄(추정)<sup>⑤</sup>", f"에이전트의 텔레메트리 코드 <b>0줄</b> (main.py 전체가 {AGENT_LINES}줄) · 앱 최소 기록 약 10~15줄(추정)<sup>⑤</sup>"),
        ("직접 만드는 모니터링용 Azure 리소스 종류<sup>②</sup>", f"<b>{len(OLD_RESOURCES)}종</b>", f"<b>{len(NEW_RESOURCES)}종</b>", f"<b>{len(NEW_RESOURCES)}종</b>"),
        ("관리하는 서버", "VM 1대 + Azure Monitor Agent + probe", "에이전트 쪽은 없음 (앱이 VM 에 있다면 그 VM 은 그대로)", "에이전트 쪽은 없음 (컨테이너는 Foundry 가 운영 · 앱 VM 은 그대로)"),
        ("설정에 걸린 시간", f"환경 약 15분 + 로그 켜기 약 16분<sup>③</sup>", f"<b>azd up {m['up_total_s'] // 60}분 {m['up_total_s'] % 60}초</b> (환경 + 에이전트 + 연결) + 알림 {m['alerts_s']}초", "같은 azd up 한 번"),
        ("첫 요청 로그가 조회되기까지", "AOAI 진단 로그 <b>20~26분</b> (설정 후 활성화 지연)", f"약 <b>{m['first_visible_s']}초</b><sup>④</sup>", f"약 <b>{m['first_visible_s']}초</b><sup>④</sup>"),
        ("요청 한 건을 잇는 키", "apim-request-id ↔ CorrelationId (앱이 응답 헤더를 로그에 남겨야 함)", "클라이언트가 보낸 <code>traceparent</code> 의 trace_id = <code>operation_Id</code>", "같음 (컨테이너 로그까지 같은 trace_id)"),
        ("지연을 구분하는 기준", "앱이 잰 시간 vs AOAI 서버 시간", "실행 시간 − 모델 호출 시간 (런타임 오버헤드)", "실행 시간 − 모델 호출 시간 + <b>cold start 단계별 분해</b>(시작 지연 3단계 + 컨테이너 응답)"),
        ("앱 ↔ 서비스 구간의 시간", "앱 호출 로그(R3)에서 AOAI 서버 시간을 빼서 계산", "<b>서버 트레이스에 없음</b> — 앱 최소 기록의 client_ms 에서 서버 시간을 빼서 계산(C7)", "같음"),
        ("새로 생기는 주의점", "—", f"호출 방식 변경 · 요청별 설정 제한(B3) · 드물게 실행이 모델 호출보다 약 {m['prompt_outlier_s']}초 길어짐 (이번 검증 {m['prompt_runs']}건 중 {m['prompt_outliers']}건 · 원인은 에이전트 런타임)", f"호출 방식 변경 · 요청별 설정 제한(B3) · 새 세션마다 cold start 약 {m['cold_startup_s']}초 · 컨테이너 시간 과금"),
    ]
    body = "".join(_row(r) for r in rows)
    return (
        '<table class="cmp"><thead><tr><th>항목</th><th>AOAI + VM 앱<br><small>가이드 1</small></th><th>Foundry<br><small>프롬프트 에이전트</small></th><th>Foundry<br><small>호스티드 에이전트 (MAF)</small></th></tr></thead><tbody>'
        + body
        + "</tbody></table>"
    )


def build_front():
    m = measured()
    # ───────── 1. 이 가이드가 하는 일
    visibility = table(
        ["구분", "내용", "확인 · 대응"],
        [
            ["**보임** (서버 쪽)", "에이전트 실행 시간 · 모델 호출 시간 · 토큰 수 · 호스티드 에이전트의 cold start 단계 · 실패 원인", "[C2](#c2)~[C5](#c5) · [D3](#d3)"],
            ["**안 보임**", "**앱 ↔ Foundry 구간** — 앱 자신의 시간 · SDK · 네트워크 · 재시도 대기", "**앱 최소 기록** → [C7](#c7)"],
            ["**안 보임**", "에이전트를 거치지 않고 **모델을 직접 호출**한 요청 (0건)", "에이전트를 지정해 호출 → [B3](#b3)"],
            ["**안 보임**", "실행이 시작되기 전에 **거절된 호출**(예: 없는 모델 배포로 만든 프롬프트 에이전트)", "앱 최소 기록 → [C7](#c7)"],
            ["**안 보임**", "**앱이 도는 VM 자체**(CPU · 디스크 · 네트워크)", "앱 VM 에 성능 카운터 수집 · probe 를 따로 설치(가이드 1 의 R5~R7 방식) → [E1](#e1)"],
            ["**함정**", "호스티드 에이전트의 실행 중 실패는 `requests` 에서 **성공(success=true)** 으로 남음", "`dependencies` · `exceptions` 로 감시 → [D3](#d3)"],
            ["**주의**", "프롬프트 · 응답 **본문이 트레이스에 기록**됨", "접근 제어 → [부록 C](#x3)"],
        ],
    )
    compare_html = (
        md("**설정량이 얼마나 줄었는지** 보여 주는 요약입니다. 가이드 1 을 읽은 분을 위한 표이며, 읽지 않았다면 건너뛰어도 됩니다.")
        + md(
            f"설정 코드는 **{OLD_TOTAL}줄 → {NEW_TOTAL}줄**(−{PCT}%), 직접 만드는 모니터링 리소스는 **{len(OLD_RESOURCES)}종 → {len(NEW_RESOURCES)}종**입니다. 단, 이 숫자는 **서버 쪽 모니터링 설정**만 센 것이고 앱 최소 기록은 포함하지 않았습니다."
        )
        + compare_table()
        + f'<p class="foot-note"><sup>①</sup> 빈 줄 · 주석을 뺀 줄 수. 가이드 1 은 <code>snippets/</code> 의 R1 {OLD["R1"]} · R3 {OLD["R3"]} · R4 {OLD["R4"]} · R5 {OLD["R5"]} · R6 {OLD["R6"]} · R7 {OLD["R7"]} · R8 {OLD["R8"]} 줄, '
        f'이 가이드는 <code>connect-appinsights.sh</code> {NEW["connect"]} + <code>alerts.sh</code> {NEW["alerts"]} 줄 (줄 수는 빌드할 때 파일에서 직접 센 값이며, <a href="#x4">부록 D</a>에 상세). <code>azure.yaml</code> 의 <code>hooks</code> 블록 {HOOK_LINES}줄(스크립트를 연결하는 부분)은 에이전트 정의 파일의 일부라 세지 않았습니다 — 포함하면 {NEW_TOTAL + HOOK_LINES}줄입니다. '
        f'<sup>②</sup> 목록은 <a href="#x4">부록 D</a>. <sup>③</sup> 가이드 1 의 B1~B7 단계 표기(1+3+3+2+2+5분 등)를 더한 값이며, 위 줄 수는 VM · 네트워크 구간 로그를 포함합니다. '
        "<sup>④</sup> 호출이 끝난 뒤 마지막 호출이 조회되기까지의 시간입니다. 연결을 만든 지 2분 이상 지나서 호출한 값이라, 연결 직후 곧바로 호출했을 때의 활성화 지연은 확인하지 못했습니다. "
        "<sup>⑤</sup> ‘약 10~15줄’은 <b>기존 호출 코드 위에 추가되는 줄</b>의 추정이며(C7 의 스케치는 호출 코드까지 합쳐 약 20줄), 실제 Foundry 호출로 검증하지 않았습니다. 같은 역할을 하는 기록 한 줄은 <code>invoke_agents.py</code> 의 출력(B2)입니다.</p>"
    )
    sec_start = section(
        "start",
        "이 가이드가 하는 일",
        "문제 · 방법 · 무엇이 보이고 안 보이나 · 전체 그림",
        md(
            """
            AOAI 를 부르는 앱의 응답이 **가끔 느릴 때**, 그 시간이 **어디서 쓰였는지 요청 한 건씩** 보고 싶다 — 이 가이드는 거기서 출발합니다.
            이 가이드는 **앱이 모델을 직접 부르는 대신 Foundry ‘에이전트’를 거쳐 부르게 바꾸는 방식**을 새 리소스 그룹에서 직접 만들어 시험합니다. 에이전트를 거쳐 호출하면 Foundry 가 **요청별 기록(트레이스)을 코드 없이** Application Insights 에 남겨 줍니다. `azd up` 한 번으로 환경을 만들고, 에이전트를 호출하고, 트레이스를 조회하고, 알림까지 확인합니다.
            """
        )
        + call(
            "tip",
            "핵심 결과 한눈에",
            f"""
            - 서버 쪽 모니터링 설정: **{OLD_TOTAL}줄 → {NEW_TOTAL}줄**(스크립트 기준) · 에이전트 코드 안의 텔레메트리 코드 **0줄**
            - 호스티드 에이전트: 새 대화마다 **cold start 약 {m['cold_startup_s']}초**(총 응답 약 8~12초)
            - 방금 한 호출의 트레이스가 **약 {m['first_visible_s']}초 뒤**(최대 약 2분 40초)에 조회됨
            - **앱 ↔ 에이전트 구간은 서버 트레이스에 없어** 앱이 따로 기록해야 함(C7)
            - 프롬프트 · 응답 **본문이 트레이스에 기록**됨(부록 C)
            """,
        )
        + call(
            "info",
            "가이드 1 을 읽지 않은 분께",
            """
            짝 가이드인 **가이드 1** 은 ‘VM 의 앱이 AOAI 를 **직접** 부를 때’ 요청별 로그를 **앱 쪽에서 직접 모으는** 방법입니다(번호 **R1~R8** 로 부릅니다). ① 앱이 호출마다 남기는 로그 ② Azure 서비스의 로그를 저장소로 보내는 스위치(**진단 설정**) ③ VM 에 까는 수집 프로그램(Azure Monitor Agent, **AMA**) ④ 주기적으로 호출해 보는 점검 스크립트(**probe**) ⑤ 알림 — 을 하나씩 설정합니다. 이 가이드는 같은 목적을 **‘호출을 에이전트로 바꿔서’** 풉니다. 이 문서에서 ‘에이전트’는 **Foundry 에이전트**만 뜻하고, 수집 프로그램은 AMA 로만 부릅니다. **가이드 1 없이 끝까지 따라 할 수 있고**, 두 방법의 대응은 [E1](#e1)에 정리되어 있습니다. 모르는 말이 나오면 바로 아래 [용어 사전](#terms)을 보세요.
            """,
        )
        + call(
            "tip",
            "이 가이드를 끝내면 할 수 있는 것",
            """
            - `azd up` 한 번으로 **Foundry 프로젝트 · 모델 · 에이전트 2개 · Application Insights 연결**을 만든다.
            - 에이전트 호출 한 건이 어떤 스팬(에이전트 실행 · 모델 호출 · cold start)으로 나뉘는지 보고, **느린 곳이 모델인지 에이전트 런타임인지** 구분한다.
            - 느린 실행 · 실패한 실행 **알림**을 만들고, 일부러 만든 장애에서 실제로 울리는지 확인한다.
            - 기존 앱의 호출을 에이전트로 바꿀 때 **무엇이 바뀌고(B3), 무엇이 서버 트레이스에 안 보이는지(C7)** 안다.
            """,
        )
        + md("#### 무엇이 보이고, 무엇이 안 보이나 — 한눈에")
        + md("이 가이드에서 **‘서버 쪽’은 Foundry(에이전트 + 모델)**, **‘앱 쪽’은 내 코드와 그 코드가 도는 컴퓨터**입니다. **에이전트 호출의 서버 쪽만 코드 없이 보이고**, 나머지는 따로 챙겨야 합니다.")
        + visibility
        + md("**실습 환경은 이렇게 구성됩니다.** 클라이언트가 Foundry 프로젝트의 두 에이전트를 호출하면, Foundry 플랫폼과 호스티드 에이전트 컨테이너가 Application Insights 로 트레이스를 보냅니다.")
        + diagram(SVG)
        + md("**요청 한 건의 시간**을 구간으로 나누면 아래와 같습니다. 초록색 구간은 서버 트레이스로 보이고, 점선(주황) 구간은 앱에서 따로 기록해야 보입니다. 이 그림이 이 가이드의 핵심입니다.")
        + diagram(SVG_TIMELINE)
        + md("그림을 글로 옮기면 아래 표와 같습니다.")
        + table(
            ["구간", "서버 트레이스에 보임?", "어디서 확인하나"],
            [
                ["① 앱 · SDK · 인증 (재시도 대기 포함)", "✘ 안 보임", "앱 최소 기록 — C7"],
                ["② 네트워크 (앱 → Foundry)", "✘ 안 보임", "앱 최소 기록 — C7"],
                ["③ Foundry 서버의 에이전트 실행 `invoke_agent` (안에 모델 호출 `chat`)", "✔ 보임", "C2 · C3 · C4"],
                ["③ 안의 호스티드 에이전트 cold start(시작 지연)", "✔ 보임(요청 스팬의 속성)", "C2 · C3"],
                ["④ 응답 도착 · 앱의 후처리", "✘ 안 보임", "앱 최소 기록 — C7"],
            ],
        )
        + call(
            "warn",
            "읽을 때 주의",
            f"""
            - 이 가이드는 **앱의 모델 호출 부분을 에이전트로 옮길 수 있을 때**의 이야기입니다. 옮기지 못하는 앱은 가이드 1 의 방식(VM 앱에 진단 설정 · 에이전트 · 앱 코드 · probe · 알림을 더함)이 그대로 필요합니다. **엔드포인트만** AOAI → Foundry 로 바꿔서는 에이전트 트레이스가 생기지 않습니다([B3](#b3)).
            - 수치는 **2026-10-24 Korea Central 한 환경에서 잰 값**입니다. 호스티드 에이전트는 **세션마다 cold start**(시작 지연 실측 약 {m['cold_startup_s']}초)가 있어 응답 시간 자체는 오히려 늘어날 수 있습니다 — 모니터링이 쉬워지는 것과 응답이 빨라지는 것은 별개입니다.
            - 프롬프트 · 응답 **본문이 트레이스에 기록**됩니다. 접근 제어는 [부록 C](#x3) 참고. 시범(PoC)에는 실제 업무 데이터나 개인정보를 넣지 마세요.
            """,
        )
        + details("가이드 1(AOAI + VM)과 비교 — 가이드 1 을 읽은 분용", compare_html),
    )

    # ───────── 2. 용어 사전
    sec_terms = section(
        "terms",
        "먼저 알아 둘 말",
        "용어 사전 — 모르는 말이 나오면 여기로 돌아오세요",
        md("처음 보는 말이 많아도 괜찮습니다. 아래는 이 가이드에 나오는 말을 **쉽게 풀어 쓴 것**입니다. 본문에서도 처음 나올 때 한 번 더 풀어 씁니다.")
        + md("#### Foundry 와 에이전트")
        + gloss_group(["aoai", "foundry", "project", "model", "agent", "hosted", "coldstart", "respapi", "entra"])
        + md("#### 트레이스 · 로그")
        + gloss_group(["telemetry", "side", "trace", "traceid", "spans", "appi_f", "reqdep", "rolename", "otel_f", "kql", "utc", "ingest_f", "alert_f", "appmin"])
        + md("#### 도구 · 기본 개념")
        + gloss_group(["azd", "prov", "rg", "tpm", "status_f", "timeout_f", "rnum_f"]),
    )

    # ───────── 3. 읽는 법 · 전체 단계
    steps_map = table(
        ["단계", "하는 일", "시간", "끝나면"],
        [
            ["[A1](#a1)", "도구 버전 확인 · 로그인 · 확장 설치", "1분", "`az` · `azd` 로그인, Foundry 확장 설치"],
            ["[A2](#a2)", "저장소 받기 → **`azd up`**(프로젝트 · 모델 · 연결 · 에이전트 2개)", f"약 {(m['up_total_s'] + 59) // 60}분", "에이전트 2개가 배포됨 · Application Insights 연결"],
            ["[A3](#a3)", "환경 값 저장 · `kq` 도우미 함수 · 확인", "1분", "만들어진 것 확인"],
            ["[B1](#b1)", "`azd` 로 에이전트 한 번씩 호출", "30초", "호스티드 응답에 단계별 시간이 나옴"],
            ["[B2](#b2)", "클라이언트 스크립트로 호출 16번", "2분", "`calls.jsonl`(호출마다 JSON 한 줄)"],
            ["[B3](#b3)", "기존 앱의 호출을 에이전트로 바꾸면 — 전환 공수(읽기)", "5분", "바뀌는 것 · 요청별 설정 가능/불가"],
            ["[C1](#c1)~[C6](#c6)", "트레이스 도착 · 에이전트 단위 지연 · 느린 곳 · 요청 한 건 · 토큰 · 포털", "약 5분", "느린 곳이 모델인지 런타임인지 구분함"],
            ["[C7](#c7)", "앱에서 본 시간 vs 서버에서 본 시간 — 앱 최소 기록(읽기)", "5분", "서버 트레이스에 없는 시간과 대응"],
            ["[D1](#d1)~[D4](#d4)", "알림 2개 · 장애 재현 · 알림 확인 · 복구", "약 10분", "알림이 실제로 울림"],
            ["[E1](#e1) · [E2](#e2)", "내 앱에는 어느 방법? · 가이드 1 대응표(읽기) · 삭제", "3분", "판단 기준 · 리소스 삭제"],
        ],
        cls="map",
    )
    sec_howto = section(
        "howto",
        "이 문서 읽는 법 · 전체 단계",
        "상자 · 이름표 · 터미널 규칙",
        md("이 문서는 **위에서 아래로 따라 하면** 되도록 순서대로 쓰였습니다. 각 단계는 같은 모양입니다.")
        + md("**① 한눈에**(무엇을 · 왜 · 끝나면 · 내 환경에서는) → **② 코드**(구간별 해설 포함) → **③ 예상 결과와 읽는 법**")
        + legend_html()
        + terminal_rules("cd ~/foundry-lab/azure-openai-latency-logging-lab/foundry && set -a; . ./foundry.env; set +a", extra=[
            "**값을 넣어야 하는 코드**(예: `export SUB=\"<구독 ID>\"`)는 ‘전체 복사’ 를 터미널에 바로 붙이지 말고, 메모장에 먼저 붙여 꺾쇠째 실제 값으로 바꾼 뒤 다시 복사해 실행하세요.",
            "**번호 구간은 한 명령(스크립트)을 설명하려고 자른 조각**입니다. 중간만 복사하면 `<<'EOF'` 나 `'` 가 닫히지 않아 터미널이 입력을 기다립니다(멈추면 `Ctrl+C`). 항상 코드 상자 위의 **‘전체 복사’** 로 한 번에 붙이세요. `<<'EOF' … EOF`(heredoc)는 그 사이의 줄들을 그대로 입력으로 넘기는 셸 문법이고, `export` 는 변수를 이후 명령에서도 쓰게 하는 지정입니다.",
            "B2 이후에 새 터미널을 열었다면 **가상환경도 다시 켭니다**(같은 폴더에서 `. .venv/bin/activate`). 호출 기록 파일 `calls.jsonl` 도 이 폴더에 있습니다.",
        ])
        + md("#### 전체 단계 한눈에")
        + md("**실행하는 단계**(A · B1~B2 · C1~C6 · D · E2)와 **읽는 단계**(B3 · C7 · E1)가 있습니다. 읽는 단계는 명령을 실행하지 않고, 앞 단계에서 얻은 실측 결과를 해석합니다.")
        + steps_map,
    )

    # ───────── 4. 준비물
    prereq = table(
        ["항목", "요구 사항", "비고"],
        [
            ["Azure CLI", "2.60 이상 (2.86 으로 검증)", "`az version` · 설치: [Azure CLI 설치 문서](https://learn.microsoft.com/cli/azure/install-azure-cli)"],
            ["Azure Developer CLI(azd)", "**1.37.1** 이상 + `microsoft.foundry` 확장 (azure.ai.agents 1.0.0-beta.22)", "확장은 아직 **베타**라 버전이 자주 바뀝니다 · 설치: [azd 설치 문서](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)"],
            ["Python", "3.10 이상 (클라이언트 스크립트용 · 3.14 로 검증)", "호스티드 에이전트는 Foundry 가 Python 3.13 으로 실행"],
            ["셸", "bash (macOS · Linux · WSL · Cloud Shell)", "git · curl 필요 · Windows 는 WSL 또는 Azure Cloud Shell(bash)에서 실행하세요(PowerShell 명령은 제공하지 않습니다) · Cloud Shell 은 azd 가 1.37.1 이상인지 `azd version` 으로 확인하세요"],
            ["구독 권한", "실습용 구독의 Owner (또는 Contributor + 역할 할당 권한)", "호출자에게 Foundry User 역할을 부여합니다 · 확인: 포털 → 구독 → 액세스 제어(IAM) → ‘내 액세스 보기’"],
            ["모델 쿼터", "koreacentral · Global Standard · gpt-5.4-mini 10 이상 (보통 단위 1K TPM)", "아래 확인 명령"],
            ["비용(예상)", "토큰 비용 소액 + Application Insights 수집 소액. 호스티드 에이전트는 **컨테이너 컴퓨트를 쓴 시간만큼** 과금(공식 가격 페이지), 프롬프트 에이전트는 추가 요금 없음", "실습은 모두 합쳐 수십 분 규모"],
        ],
        cls="nw",
    )
    quota = walk(
        """az cognitiveservices usage list -l koreacentral --query "[?name.value=='OpenAI.GlobalStandard.gpt-5.4-mini'].{used:currentValue,limit:limit}" -o table""",
        [
            (
                "az cognitiveservices usage list",
                "이 구독의 koreacentral 모델 쿼터를 조회해 gpt-5.4-mini 한 줄만 보여 줍니다",
                """
                * `az cognitiveservices usage list -l koreacentral` — 이 구독이 koreacentral 리전에서 쓸 수 있는 **모델별 쿼터(한도)와 현재 사용량** 전체
                * `--query "[?name.value=='OpenAI.GlobalStandard.gpt-5.4-mini'] …"` — 그중 이름이 `OpenAI.GlobalStandard.gpt-5.4-mini`(Global Standard 방식의 gpt-5.4-mini)인 항목만 고릅니다(JMESPath 필터 문법).
                * `.{used:currentValue,limit:limit}` — **현재 사용량(used)** 과 **한도(limit)** 두 칸만 남김
                * `-o table` — 표로 출력

                단위는 보통 **1K TPM**(분당 1,000 토큰)입니다. 이 실습은 배포 용량 **10** 을 쓰므로 `limit − used` 가 10 이상이어야 합니다.
                """,
            )
        ],
        cap="쿼터 확인 명령",
        run="A0",
    )
    sec_prep = section(
        "prep",
        "준비물 · 안전 수칙",
        "시작 전에 확인할 것",
        prereq
        + quota
        + out(
            expected("A0") or "Used    Limit\n------  -------\n0.0     1000.0",
            read="`Limit` 에서 `Used` 를 뺀 값이 10 이상이면 진행할 수 있습니다. 부족하면 다른 리전을 쓰거나 쿼터 증설을 요청하세요. **출력이 비어 있으면** 아직 `az login` 을 하지 않았거나(로그인은 A1 에서 합니다 — 그 뒤에 이 확인을 해도 됩니다), 구독이 다르거나, 쿼터 이름이 환경마다 달라 한 줄도 안 나온 것입니다. 구독이 여러 개라면 이 명령은 **지금 선택된 구독**을 조회하므로, A1 의 `az account set` 으로 실습 구독을 먼저 고른 뒤 실행하세요.",
        )
        + md("**작업 폴더 만들기** — 이 가이드에서 생기는 파일(받은 저장소 · `foundry.env` · `calls.jsonl` …)을 한곳에 모으려고 폴더를 하나 만들고 들어갑니다. **새 터미널을 열 때마다 이 폴더로 돌아와야** 합니다(터미널 규칙 참고).")
        + code("mkdir -p ~/foundry-lab && cd ~/foundry-lab", cap="작업 폴더 만들기 — A1 전에 한 번 직접 실행하세요 (이 폴더에서 A2 이후를 진행합니다)")
        + call(
            "warn",
            "안전 수칙",
            """
            - **실습용 구독**에서 실행하세요. 마지막 단계(E2)에서 `azd down` 으로 리소스 그룹을 통째로 삭제합니다.
            - 이 가이드의 모든 명령은 **새 리소스 그룹**(`rg-<azd 환경 이름>`)만 만들고 기존 리소스는 건드리지 않습니다.
            - **모델 · 에이전트 호출에는 API 키를 쓰지 않습니다** — 호출은 Entra ID(`az login`), 호스티드 에이전트는 Foundry 가 발급한 에이전트 ID 로 모델을 호출합니다. 트레이스 전송에는 Application Insights **연결 문자열**을 쓰며 `connect-appinsights.sh` 가 프로젝트의 연결에 저장합니다.
            - 회사 구독에서 `azd up` 이 **Azure Policy**(예: `RequestDisallowedByPolicy`)나 리소스 공급자 미등록 오류로 실패하면 구독 관리자에게 정책 예외 · 공급자 등록을 요청하세요. 이 가이드는 정책이 없는 개인 실습 구독에서 검증했습니다.
            """,
        ),
    )
    return sec_start + sec_terms + sec_howto + sec_prep


def build():
    m = measured()

    a1 = step(
        "a1",
        "도구 · 로그인",
        "A1",
        "소요 약 1분",
        brief(
            what="`az`(Azure CLI)와 `azd`(Azure Developer CLI) 버전을 확인하고, 로그인하고, **Foundry 확장**을 설치하고, 실습할 구독을 고정합니다.",
            why="`azd` 는 `az` 와 **로그인이 따로**입니다. 서로 다른 계정으로 로그인되어 있으면 azd 가 구독을 찾지 못합니다(부록 B 의 두 번째 항목).",
            result="`az` · `azd` 가 같은 계정으로 로그인되어 있고, Foundry 확장(에이전트 · 프로젝트 · 연결)이 설치됩니다.",
            apply="이미 `azd` 와 Foundry 확장이 있으면 버전만 확인하세요(azd 1.37.1 이상, `azure.ai.agents` 1.0.0-beta.22 이상).",
        )
        + walk(
            """az version --query '"azure-cli"' -o tsv; azd version | head -1       # azd 1.37.1 이상
az login                                                              # 이미 로그인되어 있으면 생략 (Cloud Shell 은 불필요)
azd auth login                                                        # az 와 같은 계정을 쓰려면 대신: azd config set auth.useAzCliAuth true
azd extension install microsoft.foundry                               # Foundry 확장 묶음 (이미 있으면 건너뜀)
for e in application-insights log-analytics scheduled-query; do az extension add -n $e -y 2>/dev/null; done   # az monitor 확장 (설치 물음 방지)
export SUB="<구독 ID>"                                                # ← 실습용 구독 ID (az account list -o table)
az account set -s "$SUB\"""",
            [
                (
                    "az version",
                    "도구 버전 확인",
                    """
                    * `az version --query '"azure-cli"' -o tsv` — Azure CLI 의 **버전 번호만** 출력합니다.
                    * `azd version | head -1` — azd 의 버전 정보 **첫 줄**만 출력합니다. **1.37.1 이상**이어야 합니다.
                    """,
                ),
                ("az login", "az 로그인", "브라우저가 열리고 계정을 고르면 `az` 가 로그인된 상태가 됩니다. 이미 로그인했다면 건너뛰어도 됩니다. 브라우저를 열 수 없는 환경이면 `az login --use-device-code` 로 표시된 코드를 다른 기기의 브라우저에 입력하세요."),
                (
                    "azd auth login",
                    "azd 로그인 (az 와는 별도)",
                    "`azd` 는 `az` 와 **로그인 정보를 따로** 가집니다. 같은 계정으로 로그인하세요(코드 줄 끝의 `# …` 는 설명 주석이라 입력하지 않아도 됩니다). 번거로우면 대신 `azd config set auth.useAzCliAuth true` 로 **az 의 로그인을 azd 가 그대로 쓰게** 할 수 있습니다. 브라우저를 못 여는 환경은 `azd auth login --use-device-code` 입니다.",
                ),
                (
                    "azd extension install microsoft.foundry",
                    "Foundry 확장 설치",
                    "`azd` 에 Foundry 기능(에이전트 · 프로젝트 · 연결)을 더하는 **확장 묶음**을 설치합니다. 이 한 줄이 필요한 확장(`azure.ai.agents` 등)을 함께 설치하며, 이미 있으면 건너뜁니다.",
                ),
                (
                    "for e in application-insights",
                    "az 확장 3개 설치",
                    "`az monitor app-insights query`(트레이스 조회) · `az monitor scheduled-query`(알림) · `az monitor log-analytics`(워크스페이스 만들기 — A2 의 연결 스크립트가 씀)에 쓰는 `az` 확장 3개를 설치합니다. `-y` 는 설치 질문에 자동 ‘예’, `2>/dev/null` 은 **모든 오류 출력**(이미 설치되었다는 안내 포함)을 숨깁니다. 설치가 실패해도 보이지 않으니, 뒤에서 ‘확장이 없다’는 오류가 나면 이 줄을 `2>/dev/null` 없이 다시 실행해 보세요.",
                ),
                (
                    "export SUB=",
                    "실습할 구독 고정",
                    "`SUB` 에 **구독 ID** 를 넣고(`<구독 ID>` 를 직접 바꿔 넣는 자리) `az account set` 으로 이후 `az` 명령이 이 구독만 대상으로 하게 합니다. 구독 ID 는 `az account list -o table` 로 볼 수 있습니다.",
                ),
            ],
            cap="① 버전 확인 · 로그인 · 확장 설치",
            run="A1",
        )
        + out(
            expected("A1") or "azure-cli  2.86.0\nazd version 1.37.1 (commit …) (stable)",
            read="첫 줄은 Azure CLI 버전, 둘째 줄은 azd 버전입니다. azd 가 `1.37.1` 이상이면 됩니다.",
        )
        + code(
            'az account show --query "{subscription:name, account:user.name}" -o table      # az 로그인 상태\nazd auth login --check-status                                      # azd 로그인 상태',
            cap="(확인) 두 도구가 같은 계정으로 로그인됐는지 — 확인용 명령 · 실행 블록 아님",
        )
        + md("**읽는 법**: `az account show` 가 보여 주는 **계정(account)** 과 `azd auth login --check-status` 가 보여 주는 로그인 계정이 **같은 이메일**이면 정상입니다. 다르거나 ‘not logged in’ 이면 해당 로그인 명령을 다시 하세요. 확장 설치는 `az extension list --query \"[].name\" -o tsv` 에 `application-insights` · `log-analytics` · `scheduled-query` 세 개가 보이면 정상입니다."),
        scope="lab",
    )

    # ── A2 에서 쓰는 파일 해설 (azure.yaml · connect-appinsights.sh · main.py · requirements.txt)
    yaml_walk = walk(
        fd("azure.yaml"),
        [
            (
                "# yaml-language-server",
                "프로젝트 이름",
                """
                * 맨 첫 줄 `# yaml-language-server: $schema=…` 은 편집기(VS Code 등)가 이 파일의 **문법을 검사하고 자동 완성**해 주도록 알려 주는 주석입니다. 동작에는 영향이 없습니다.
                * `name: foundry-agents-monitoring` — azd **프로젝트의 이름**입니다(리소스 그룹 이름과는 별개. 그것은 `azd env new` 로 만드는 ‘환경 이름’을 따릅니다).
                """,
            ),
            (
                "requiredVersions:",
                "필요한 도구 버전을 못 박기",
                "`azd` 가 **1.37.1 이상**, 확장 `azure.ai.agents` 가 **1.0.0-beta.22 이상**이 아니면 azd 가 실행을 막습니다. **최소 버전 요구**일 뿐 그 이후 버전을 막지는 않으므로, 이 가이드는 검증한 버전(azd 1.37.1 · beta.22)에서 확인했다는 점을 기억하세요. 베타 확장은 명령과 스키마가 자주 바뀝니다.",
            ),
            (
                "infra:",
                "인프라는 Foundry 전용 프로비저너에게 맡김",
                """
                `provider: microsoft.foundry` — 리소스를 만드는 일(**프로비저닝**)을 **Foundry 전용 프로비저너**가 합니다. 아래 `services` 에 적은 대로 Foundry 리소스 · 프로젝트 · 모델 배포를 만들며, Bicep 같은 인프라 코드 파일을 따로 쓰지 않습니다.
                이 프로비저너는 **Application Insights 를 만들지 않습니다.** 그래서 바로 아래 훅(hook)이 필요합니다.
                """,
            ),
            (
                "hooks:",
                "훅 — 프로비저닝 직후 Application Insights 를 연결",
                """
                **훅**은 azd 의 특정 시점에 끼워 넣는 스크립트입니다. `postprovision` 은 ‘**프로비저닝이 끝난 직후**’(= 프로젝트와 모델이 만들어진 직후)입니다.
                * `shell: sh` — `sh` 로 실행
                * `run: scripts/connect-appinsights.sh` — 실행할 스크립트
                * 이 한 블록(과 이 블록이 실행하는 스크립트)이 **이 가이드의 ‘모니터링 설정’ 전부**입니다. 스크립트가 Application Insights 를 만들어 프로젝트에 연결하면, 이후 두 에이전트의 트레이스가 코드 없이 쌓입니다(스크립트는 아래 파일 B 에서 한 줄씩 설명).
                """,
            ),
            (
                "services:",
                "서비스 ① ai-project — Foundry 리소스 · 프로젝트 · 모델 배포",
                """
                `services` 에 이 프로젝트를 이루는 구성 요소를 적습니다. `ai-project`(`host: azure.ai.project`)는 **Foundry 리소스와 프로젝트**이고, 거기에 올릴 **모델 배포**를 `deployments` 에 적습니다.
                * `name: gpt-5.4-mini` — **배포 이름**(에이전트가 이 이름으로 모델을 부릅니다)
                * `model` — 어떤 모델인지: `format: OpenAI` · `name: gpt-5.4-mini` · `version: "2026-03-17"`
                * `sku: GlobalStandard` · `capacity: 10` — 기존 AOAI 배포와 같은 **Global Standard 방식**(쓴 토큰만큼 과금), 처리 한도 **10 단위**(TPM 단위 — 정확한 환산은 본인 구독의 쿼터 화면 기준).
                """,
            ),
            (
                "# 프롬프트 에이전트",
                "서비스 ② 프롬프트 에이전트 — 코드 없이 모델 + 지시문만",
                """
                `kind: prompt` 에이전트는 **코드가 없습니다.** 모델과 지시문을 선언하면 끝입니다.
                * `host: azure.ai.agent` — 에이전트 서비스
                * `name` — 에이전트 이름(**호출할 때 쓰는 이름**)
                * `description` — 설명
                * `instructions` — **지시문**(시스템 프롬프트): “보고서 쓰는 법을 설명해 주고 한국어로 답하라”
                * `model: gpt-5.4-mini` — 위에서 만든 **배포 이름**
                * `project` — azd 서비스의 **소스 폴더** 항목입니다. 프롬프트 에이전트는 올릴 코드가 없어 **이 값이 쓰이지 않으니 예시 그대로 두세요**(`report-prompt-agent` 폴더가 없어도 `azd up` 은 정상 동작했습니다).
                * `uses: - ai-project` — 이 에이전트가 **위 `ai-project`(Foundry 프로젝트)에 의존한다**는 선언입니다. 배포 순서(프로젝트 먼저)와, 배포 전에 프로젝트 주소(`FOUNDRY_PROJECT_ENDPOINT`)가 있는지 확인하는 데 쓰입니다.
                """,
            ),
            (
                "# 호스티드 에이전트",
                "서비스 ③ 호스티드 에이전트(1) — 코드를 Foundry 가 실행",
                """
                `kind: hosted` 에이전트는 **내가 쓴 코드**(Microsoft Agent Framework, MAF)를 Foundry 가 실행해 줍니다.
                * `language: python` · `project: src/report-maf-agent` — 코드가 있는 **폴더**(아래 파일 C 의 `main.py`). 이 폴더가 압축되어 올라갑니다.
                * `codeConfiguration` — **코드 배포 방식**: 컨테이너 이미지를 직접 만들지 않고 **소스 ZIP 을 올리면** Foundry 가 실행합니다. `runtime: python_3_13` = **Python 3.13** 환경, `entryPoint: main.py` = **시작 파일**
                """,
            ),
            (
                "protocols:",
                "호스티드 에이전트(2) — 어떤 규약으로 호출받나",
                "`protocols` 는 이 에이전트가 **어떤 API 규약으로 요청을 받는지**입니다(선택지: `responses` · `invocations` · `a2a` 등). `responses` 2.0.0 = **Responses API**. 그래서 클라이언트가 프롬프트 에이전트와 같은 방식(`client.responses.create`)으로 부를 수 있습니다.",
            ),
            (
                "env:",
                "호스티드 에이전트(3) — 환경변수 · 컨테이너 크기 · 연결",
                """
                * `env` — 컨테이너에 넘기는 **환경변수**. `PYTHONNOUSERSITE: "1"` 은 사용자 영역의 Python 패키지를 무시해 **환경을 격리**합니다. `AZURE_AI_MODEL_DEPLOYMENT_NAME: ${AZURE_AI_MODEL_DEPLOYMENT_NAME}` 의 `${…}` 는 **azd 환경 값**(없으면 내 컴퓨터의 환경변수)으로 채워지며, 프로비저닝이 이 값을 정해 둡니다. 코드(`main.py`)가 이 값을 읽고, D2 에서 이 값을 일부러 오타로 바꿔 장애를 만듭니다.
                * `container.resources` — 컨테이너 자원: CPU `0.5` · 메모리 `1Gi`(기본값이며 선택지는 0.5/1Gi · 1/2Gi · 2/4Gi)
                * `uses: - ai-project` — 이 에이전트도 같은 Foundry 프로젝트에 의존
                """,
            ),
        ],
        cap="foundry/azure.yaml — 프로젝트 · 모델 · 에이전트 2개를 정의하는 파일",
        lang="yaml",
    )
    connect_walk = walk(
        fd("scripts/connect-appinsights.sh"),
        [
            (
                "#!/bin/sh",
                "스크립트 시작 — 오류 시 중단",
                "`set -eu`: 처리되지 않은 명령 실패에서 **즉시 중단**(`-e`, 모든 경우를 잡지는 못함), 정의하지 않은 변수를 쓰면 **오류**(`-u`)입니다. 위 주석이 이 스크립트의 목적(‘연결만 되어 있으면 서버 쪽 트레이스가 코드 변경 없이 쌓인다’)입니다.",
            ),
            (
                "RG=",
                "이름과 프로젝트 ID 만들기",
                """
                `AZURE_RESOURCE_GROUP` · `AZURE_LOCATION` · `AZURE_ENV_NAME` · `AZURE_SUBSCRIPTION_ID` · `AZURE_AI_ACCOUNT_NAME` · `AZURE_AI_PROJECT_NAME` 은 **azd 가 훅을 실행할 때 자동으로 넣어 주는 환경 값**입니다(`azd env get-values` 로 볼 수 있음).
                * `LAW` · `APPI` — 만들 워크스페이스 · Application Insights 이름(`law-<환경 이름>` · `appi-<환경 이름>`)
                * `PROJECT_ID` — Foundry **프로젝트의 리소스 ID**(구독 → 리소스 그룹 → Foundry 계정 → 프로젝트 경로). 아래에서 연결과 역할을 이 프로젝트에 건다는 뜻입니다.
                """,
            ),
            (
                "az monitor log-analytics workspace create",
                "Log Analytics 워크스페이스 만들기",
                "트레이스가 최종 저장되는 **로그 저장소**를 만듭니다(`-o none` 은 출력 생략).",
            ),
            (
                "az monitor app-insights component create",
                "Application Insights 만들기 (워크스페이스 기반)",
                "`--workspace "
                "\"$(…)\"` 로 방금 만든 워크스페이스에 **연결된** Application Insights 를 만듭니다. 이렇게 하면 데이터가 **워크스페이스에 저장**되고, `--kind web --application-type web` 은 일반 서비스용 종류입니다. `$(az monitor log-analytics workspace show … --query id -o tsv)` 는 워크스페이스의 리소스 ID 를 조회해 끼워 넣는 부분입니다.",
            ),
            (
                "APPI_ID=",
                "리소스 ID 와 연결 문자열 가져오기",
                "`APPI_ID` — Application Insights 의 **리소스 ID**, `CS` — **연결 문자열**(데이터를 어디로 보낼지 담은 값). 둘 다 아래 연결 요청에 쓰입니다.",
            ),
            (
                "az rest --method put",
                "★ 프로젝트에 Application Insights ‘연결’ 만들기 (이 스크립트의 핵심)",
                """
                `az rest` 로 Azure 리소스 관리 REST API 를 직접 호출해, Foundry **프로젝트에 ‘연결(connection)’ 하나를 만듭니다**(PUT = 만들기/덮어쓰기).
                * `…/connections/$APPI?api-version=2025-04-01-preview` — 프로젝트 안의 연결 리소스 주소
                * `category: "AppInsights"` — **연결의 종류**: Application Insights
                * `target: $APPI_ID` — 어떤 리소스에 연결하는지
                * `credentials.key: $CS` — **연결 문자열**을 자격 증명으로 저장(`authType: ApiKey`)
                * `isSharedToAll: true` — **프로젝트의 모든 사용자 · 에이전트가 공유**
                * `metadata` — 대상 리소스 정보
                * `--body "{\\"properties\\": …}"` — JSON 전체를 큰따옴표로 감쌌기 때문에 안쪽 큰따옴표를 `\\"` 로 적었습니다. `$APPI_ID` · `$CS` 같은 셸 변수가 그 자리에 값으로 들어갑니다.
                * `api-version=2025-04-01-preview` — **미리보기 API 버전**이라 바뀔 수 있습니다(이 가이드는 이 버전으로 검증했습니다).
                이 연결이 있으면 Foundry 플랫폼과 에이전트 컨테이너가 **트레이스를 이 Application Insights 로 보냅니다.** 에이전트 코드는 아무것도 바꾸지 않습니다.
                """,
            ),
            (
                "# 호출자에게",
                "역할 부여 — 호출자 · 프로젝트 관리 ID",
                """
                두 개의 역할 할당입니다(역할 이름 대신 **역할 ID(GUID)** 로 적었습니다).
                * **호출자 → Foundry User**(`53ca6127-…`, 예전 이름 Azure AI User) — `az ad signed-in-user show` 가 알려 주는 **지금 로그인한 나**에게, **프로젝트 범위**로 줍니다. 이 역할이 있어야 에이전트를 호출할 수 있습니다.
                * **프로젝트 관리 ID → Log Analytics Reader**(`73c42c96-…`) — 프로젝트의 **관리 ID**(`identity.principalId`)에게 Application Insights 범위로 줍니다. 프로젝트가 트레이스를 읽는 기능(평가 등)용으로 함께 줍니다. 이 두 번째 역할이 꼭 필요한지는 이 가이드에서 따로 검증하지 않았습니다.
                """,
            ),
            ('echo "Application Insights connected', "완료 메시지", "스크립트의 마지막 줄로, 연결이 끝났다는 메시지를 출력합니다. (`set -e` 덕분에 앞 단계가 하나라도 실패했다면 이 줄에 도달하기 전에 훅이 실패로 끝납니다.)"),
        ],
        cap="foundry/scripts/connect-appinsights.sh — postprovision 훅이 실행하는 스크립트 (모니터링 설정 전부)",
    )
    main_walk = walk(
        fd("src/report-maf-agent/main.py"),
        [
            (
                "import os",
                "필요한 도구 가져오기",
                """
                * `agent_framework.Agent` — **Microsoft Agent Framework(MAF)** 의 에이전트 클래스
                * `FoundryChatClient` — Foundry 의 모델을 부르는 클라이언트
                * `ResponsesHostServer` — 에이전트를 **Responses API 서버**로 띄워 주는 도구(호스팅)
                * `DefaultAzureCredential` — 실행 환경의 **신원**(Foundry 가 컨테이너에 부여한 에이전트 ID)으로 인증
                """,
            ),
            (
                "agent = Agent(",
                "에이전트 정의 — 모델 · 지시문 · 옵션",
                """
                * `project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"]` — Foundry 프로젝트 주소. **Foundry 가 컨테이너에 환경변수로 넣어 줍니다.**
                * `model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]` — 부를 **모델 배포 이름**. `azure.yaml` 의 `env` 에서 넘어온 값이라, 오타를 내면 모델 호출이 실패합니다(D2 장애 재현).
                * `credential=DefaultAzureCredential()` — **키 없이** 에이전트 ID 로 인증
                * `instructions` — 지시문(프롬프트 에이전트와 같은 내용)
                * `default_options={"store": False}` — 모델 호출의 기본 옵션: Responses API 의 `store` 를 끕니다. 생성한 응답을 API 로 **나중에 다시 조회**할 수 있게 저장하는 기능을 끄는 옵션이며, 트레이스 기록이나 서비스의 보존 정책에는 따로 적용되지 않습니다(트레이스에는 본문이 기록됩니다 — 부록 C).
                """,
            ),
            (
                "if __name__",
                "서버로 실행",
                "`ResponsesHostServer(agent).run()` — 에이전트를 **요청을 받는 서버로** 띄웁니다. Foundry 가 컨테이너 안에서 이 파일(`main.py`)을 시작하면 서버가 **Responses API 요청을 받아 `agent` 에게 전달**합니다.",
            ),
        ],
        cap="foundry/src/report-maf-agent/main.py — 호스티드 에이전트 전체 (텔레메트리 코드 없음)",
        lang="python",
    )
    a2 = step(
        "a2",
        "저장소 받기 → azd up (프로젝트 · 모델 · Application Insights 연결 · 에이전트 2개)",
        "A2",
        f"소요 약 {m['up_total_s'] // 60}~{m['up_total_s'] // 60 + 1}분 (azd 가 만드는 동안 기다리는 시간) · 가이드 1 을 읽었다면: 이 한 단계가 가이드 1 의 A · B1~B3 에 해당",
        brief(
            what="이 저장소의 `foundry/` 폴더(= azd 프로젝트)를 받아 **`azd up` 한 번**으로 Foundry 프로젝트 · 모델 배포 · 에이전트 2개를 만들고, 프로젝트에 Application Insights 를 연결합니다.",
            why="**프로젝트에 Application Insights 가 연결만 되어 있으면** 두 에이전트의 서버 쪽 트레이스가 코드 없이 쌓입니다. 그래서 환경을 만드는 이 한 단계가 곧 ‘모니터링 설정’입니다. (가이드 1 을 읽었다면: 가이드 1 에서 따로 하던 R1 · R4 · R5 · R7 을 이 한 단계가 대신합니다.)",
            result=f"에이전트 `report-prompt-agent` · `report-maf-agent` 가 배포되고, `azd up` 이 약 {m['up_total_s'] // 60}분 {m['up_total_s'] % 60}초(프로비저닝+훅 {m['provision_s']}초, 배포 {m['deploy_s']}초) 만에 끝납니다.",
            apply="내 환경에서는 **새 프로젝트를 만들 때** `azure.yaml` 과 `connect-appinsights.sh` 를 그대로 가져가 쓰거나, 이미 있는 프로젝트라면 **연결 요청(파일 B 의 구간 6)과 역할 부여(구간 7)만** 적용하되, 그 전에 구간 2 · 5 의 값을 내 것으로 준비하세요: `PROJECT_ID` = Foundry 프로젝트의 리소스 ID(포털의 프로젝트 속성), `APPI_ID` = `az monitor app-insights component show -a <이름> -g <그룹> --query id -o tsv`, `CS` = 같은 명령의 `--query connectionString -o tsv`. Application Insights 가 없다면 구간 2~7 을 모두 적용합니다.",
            caution="새 환경 3번 중 1번은 첫 시도가 일시적 오류로 실패했습니다. **같은 `azd up` 을 다시 실행하면 성공**합니다(아래 알림 상자).",
        )
        + walk(
            """git clone --depth 1 https://github.com/junwoojeong100/azure-openai-latency-logging-lab.git
cd azure-openai-latency-logging-lab/foundry
azd env new fdmon-$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c5) --subscription "$SUB" --location koreacentral
azd up""",
            [
                (
                    "git clone",
                    "저장소 받기",
                    "`git clone --depth 1 …` 으로 이 저장소의 **최신 상태만 얕게** 받고, `cd …/foundry` 로 **azd 프로젝트 폴더**(`azure.yaml` 이 있는 곳)로 들어갑니다. 이후 모든 명령은 이 폴더에서 실행합니다.",
                ),
                (
                    "azd env new",
                    "azd 환경 만들기 — 리소스 그룹 이름이 여기서 정해짐",
                    """
                    **azd 환경**은 한 번의 배포 설정(이름 · 구독 · 리전)입니다. 환경 이름이 **리소스 그룹 이름 `rg-<환경 이름>`** 이 됩니다.
                    * `fdmon-$(…)` — `fdmon-` 뒤에 **무작위 5글자**(소문자 · 숫자)를 붙여 이름이 겹치지 않게 합니다. `$(…)` 안은 ‘`/dev/urandom`(무작위 바이트)에서 `tr -dc 'a-z0-9'` 로 소문자 · 숫자만 남기고, `head -c5` 로 앞 5글자만’ 자르는 명령입니다(`LC_ALL=C` 는 macOS 에서 `tr` 가 오류 없이 동작하게 하는 설정).
                    * `--subscription "$SUB" --location koreacentral` — 구독과 리전
                    * 만든 환경은 `azd env list` 로 볼 수 있습니다. 중간에 터미널을 닫았다면 이 목록의 이름으로 다시 이어서 작업합니다(`azd env select <이름>`).
                    """,
                ),
                (
                    "azd up",
                    "azd up — 만들고 배포하고 연결하기",
                    """
                    **`azd up` 은 세 가지를 순서대로 합니다.**
                    1. **프로비저닝**: `azure.yaml` 대로 Foundry 리소스 · 프로젝트 · 모델 배포 생성
                    2. **훅(postprovision)**: `connect-appinsights.sh` 실행 → Application Insights 만들고 연결
                    3. **배포**: 에이전트 2개 만들기(프롬프트 에이전트 정의 등록, 호스티드 에이전트 코드 업로드 · 빌드 · 실행)
                    약 4분이 걸리며, 진행 상황이 터미널에 출력됩니다.
                    """,
                ),
            ],
            cap="한 번에: 저장소 → 환경 만들기 → azd up (환경 이름이 리소스 그룹 이름 rg-<환경 이름> 이 됩니다)",
            run="A2",
        )
        + out(
            expected("A2")
            or f"SUCCESS: Your application was provisioned and deployed to Azure in {m['up_total_s'] // 60} minutes {m['up_total_s'] % 60} seconds.\n  Provisioning: …\n  Deploying:    …",
            read="`SUCCESS: … provisioned and deployed to Azure in 3 minutes 42 seconds` 가 마지막에 나오면 성공입니다. `Provisioning`(프로비저닝 + 연결 훅)과 `Deploying`(에이전트 배포) 시간이 따로 나옵니다. 중간에 오류가 나면 아래 알림 상자를 보세요. `azd` 가 중간에 선택을 묻는 질문을 하면 안내대로 답하세요 — 이 가이드는 `azd env new` 로 구독 · 리전을 미리 정해 두어 **질문 없이 끝나도록** 검증했습니다.",
        )
        + call(
            "warn",
            "가끔 첫 시도가 실패합니다",
            "검증 중 새 환경 3번 중 1번은 프로젝트 생성 단계에서 `FailedIdentityOperation … Conflict … pending delete operation` 으로 약 45초 만에 실패했고, **같은 `azd up` 을 다시 실행하면 성공**했습니다(azd 는 이어서 진행합니다).",
        )
        + md("#### azd up 이 읽는 파일 A · azure.yaml — 무엇을 만들지 적은 파일")
        + md("**모니터링과 관련된 부분은 `hooks` 한 블록뿐**입니다. 나머지는 프로젝트 · 모델 · 에이전트를 정의합니다.")
        + yaml_walk
        + md("#### azd up 이 읽는 파일 B · connect-appinsights.sh — Application Insights 를 만들어 연결")
        + md(f"**이 스크립트({NEW['connect']}줄)가 ‘트레이스를 쌓는’ 모니터링 설정 전부**이고, D1 의 알림 스크립트({NEW['alerts']}줄)를 더한 **{NEW_TOTAL}줄**이 이 가이드의 모니터링 설정 전체입니다(주석 · 빈 줄 제외).")
        + connect_walk
        + md("#### azd up 이 읽는 파일 C · main.py — 호스티드 에이전트 코드 전체")
        + md(f"""에이전트 코드 **전체가 {AGENT_LINES}줄**이고 그중 **텔레메트리 코드는 0줄**입니다. 그런데도 트레이스가 쌓이는 이유는 세 단계입니다.
        1. **연결** — 위 파일 B(`connect-appinsights.sh`)가 프로젝트에 Application Insights 를 연결합니다.
        2. **(문서 기준)** 플랫폼이 호스티드 컨테이너에 연결 문자열을 **환경변수**(`APPLICATIONINSIGHTS_CONNECTION_STRING`)로 넣어 줍니다.
        3. **(실측)** 컨테이너가 시작하면서 스스로 Azure Monitor 를 설정하고(컨테이너 로그에 “Azure Monitor configured via azure-monitor-opentelemetry package” 가 남습니다), 요청 · 모델 호출을 **OpenTelemetry**(표준 trace · span 규격)로 자동 전송합니다.
        그래서 `main.py` 에는 로깅 · 계측 코드가 필요 없습니다.""")
        + main_walk
        + call(
            "info",
            "④ requirements.txt 를 쓰는 이유",
            """
            호스티드 에이전트의 코드 배포(`codeConfiguration`)는 Foundry 가 **원격에서 의존성을 설치**합니다. 그 목록이 `src/report-maf-agent/requirements.txt`(`agent-framework-foundry` · `agent-framework-foundry-hosting`)입니다.
            `pyproject.toml` 만 두면 `[tool.poetry] section not found` 로 실패해서(부록 B) `requirements.txt` 를 썼습니다. `uv.lock` 을 함께 두는 방법도 있습니다.
            """,
        ),
        scope="apply",
    )

    kq_walk = walk(
        """azd env get-values > foundry.env
cat >> foundry.env <<'EOF'
# Application Insights 에 KQL 을 보내 표로 출력 (사용: kq '<KQL>')
kq() { az monitor app-insights query --app "appi-$AZURE_ENV_NAME" -g "$AZURE_RESOURCE_GROUP" --analytics-query "$1" -o json | python3 -c '
import json, sys
t = json.load(sys.stdin)["tables"][0]; cols = [c["name"] for c in t["columns"]]
rows = [["" if v is None else str(v)[:70] for v in r] for r in t["rows"]]
w = [max([len(c)] + [len(r[i]) for r in rows]) for i, c in enumerate(cols)]
print("  ".join(c.ljust(w[i]) for i, c in enumerate(cols))); print("  ".join("-" * x for x in w))
for r in rows: print("  ".join(r[i].ljust(w[i]) for i in range(len(cols))))'; }
EOF
set -a; . ./foundry.env; set +a
az resource list -g "$AZURE_RESOURCE_GROUP" --query "[].{name:name, type:type}" -o table
azd ai agent show report-prompt-agent | head -5
azd ai agent show report-maf-agent | head -5""",
        [
            (
                "azd env get-values",
                "azd 환경 값을 파일로 저장",
                "`azd env get-values` 는 이 환경의 값(`AZURE_ENV_NAME` · `AZURE_RESOURCE_GROUP` · `AZURE_AI_PROJECT_NAME` · `FOUNDRY_PROJECT_ENDPOINT` …)을 `이름=값` 줄로 출력합니다. `> foundry.env` 로 **파일에 저장**해 두면 새 터미널에서도 다시 불러올 수 있습니다.",
            ),
            (
                "cat >> foundry.env",
                "kq 도우미 함수 — App Insights 에 KQL 을 보내 표로 보기",
                """
                `kq` 는 **Application Insights 에 KQL 을 보내 결과를 표로 찍어 주는 도우미 함수**입니다. 사용법: `kq '<KQL>'` (포털에서는 Application Insights → Logs 에 같은 KQL 을 붙여 넣어도 됩니다.)
                * `>>` 로 파일 **끝에 덧붙이고**, `<<'EOF'`(따옴표 있는 EOF)라서 `$1` · `$AZURE_ENV_NAME` 같은 변수는 **저장할 때가 아니라 함수를 부를 때** 해석됩니다.
                * `az monitor app-insights query --app "appi-$AZURE_ENV_NAME" -g … --analytics-query "$1" -o json` — Application Insights 에 **KQL(첫 번째 인자 `$1`)을 보내고 JSON 으로 받습니다.**
                * `| python3 -c '…'` — 그 JSON 을 표 모양으로 바꿔 찍는 짧은 Python 입니다(열 · 행 꺼내기, 각 값을 70자로 자르기, 칸 맞추기). **표 모양만 맞추는 코드라 이해하지 않아도 되고 복사해서 쓰면 됩니다.** 값은 **70자까지만** 보이니 전체가 필요하면 포털 Logs 에서 보세요. `kq` 가 `JSONDecodeError` 로 끝나면 `az` 가 JSON 대신 오류 문장을 돌려준 것이므로 [부록 B](#x2) 를 보세요.
                * **주의: 기본 조회 범위는 최근 1시간입니다.** `az monitor app-insights query` 는 `--offset` 을 주지 않으면 1시간만 봅니다. 호출한 지 1시간이 넘었다면 결과가 비어 보이니 조회 기간을 늘리세요: `sed -i.bak 's/ -o json | python3/ --offset 3d -o json | python3/' foundry.env` 를 실행한 뒤 위의 `set -a; . ./foundry.env; set +a` 를 다시 실행합니다(최대 3일).
                """,
            ),
            (
                "set -a;",
                "파일을 읽어 현재 터미널에 적용",
                "`set -a` 는 ‘이후 정의하는 변수를 자동으로 **환경변수로 내보내기(export)**’, `. ./foundry.env` 는 파일을 읽어 적용, `set +a` 는 자동 내보내기 해제입니다. 새 터미널에서는 이 줄만 다시 실행하면 됩니다.",
            ),
            (
                "az resource list",
                "만들어진 리소스 확인",
                "`az resource list -g \"$AZURE_RESOURCE_GROUP\"` 로 리소스 그룹 안의 리소스 이름을 나열합니다. Foundry 계정 · 그 아래 프로젝트 · Log Analytics 워크스페이스 · Application Insights 가 보여야 합니다.",
            ),
            (
                "azd ai agent show report-prompt-agent",
                "에이전트 상태 확인",
                "`azd ai agent show <이름>` 으로 배포된 에이전트의 정보(이름 · 종류 · 버전 · 상태)를 봅니다. `| head -5` 는 처음 5줄만 보여 주므로, 호스티드 에이전트는 `Status` 줄이 5줄 밖이라 **보이지 않을 수 있습니다**(전체는 `head` 없이 실행).",
            ),
        ],
        cap="환경 값 저장 · kq 함수 · 리소스 확인 · 에이전트 상태",
        run="A3",
    )
    a3 = step(
        "a3",
        "확인 — 환경 값 · 도우미 함수 · 만들어진 것",
        "A3",
        "소요 약 1분",
        brief(
            what="`azd` 가 만든 환경 값을 파일로 저장하고, 트레이스를 조회하는 **`kq` 도우미 함수**를 만든 뒤, 리소스와 에이전트 상태를 확인합니다.",
            why="이후 모든 단계가 이 환경 값(`$AZURE_RESOURCE_GROUP` 등)과 `kq` 함수를 씁니다.",
            result="`foundry.env`(변수 + `kq` 함수)가 생기고, 리소스 목록과 에이전트 정보가 출력됩니다.",
            apply="`kq` 대신 포털의 Application Insights → Logs 에 KQL 을 붙여 넣어도 됩니다.",
        )
        + kq_walk
        + out(
            expected("A3") or "Name  Type\n----  ----",
            read="""
            - 처음 4줄이 리소스 이름입니다: Foundry 계정(`cog-…`), 그 아래 **프로젝트**(`cog-…/fdmon-…`), Log Analytics 워크스페이스(`law-…`), Application Insights(`appi-…`).
            - 그 아래는 두 에이전트의 정보입니다: 프롬프트 에이전트는 `Kind: prompt` · `Status: active`, 호스티드 에이전트는 `ID: report-maf-agent:1`(이름:버전)처럼 **버전 1 로 등록**되었다는 뜻입니다.
            """,
        ),
        scope="check",
    )

    return section("a", "A · 환경 만들기", "azd up 한 번으로 프로젝트 · 모델 · 연결 · 에이전트", a1 + a2 + a3)
