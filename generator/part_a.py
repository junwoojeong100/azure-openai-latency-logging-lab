# -*- coding: utf-8 -*-
# 처음 읽는 분께(개요 · 용어 · 읽는 법 · 준비물) / A · 실습 환경 만들기
from lib import *
from common import *

# 요청 한 건이 지나가는 시간 — 이 가이드 전체의 ‘기본 그림’
SVG_TIMELINE = """<svg viewBox="0 0 960 350" role="img" aria-label="요청 한 건이 지나가는 시간: 앱 안(호출 전), 앱과 AOAI 사이의 연결, AOAI 처리, 응답 도착. 앱 호출 로그의 total_ms 는 연결부터 응답 도착까지의 SDK 호출 구간이고, AOAI 가 잰 시간은 AOAI 처리 구간입니다. 둘의 차이가 AOAI 바깥에서 쓴 시간입니다">
<text class="ttl" x="20" y="26">요청 한 건이 지나가는 시간 (왼쪽 → 오른쪽)</text>
<path class="brka" d="M170,100 L170,88 L920,88 L920,100"/>
<text class="lblb" x="545" y="76" text-anchor="middle">앱 호출 로그(R3)의 total_ms — with call_log 블록 안, 즉 SDK 호출 구간</text>
<rect class="boxw" x="40" y="108" width="130" height="62" rx="10"/>
<text class="lblb" x="52" y="132">① 호출 전</text><text class="sub" x="52" y="150">앱 안 대기 · 준비</text>
<rect class="box" x="170" y="108" width="170" height="62" rx="10"/>
<text class="lblb" x="182" y="132">② 연결</text><text class="sub" x="182" y="150">DNS · TCP · TLS · 방화벽</text>
<rect class="boxa" x="340" y="108" width="420" height="62" rx="10"/>
<text class="lblb" x="352" y="132">③ AOAI 서비스가 답을 만드는 시간</text><text class="sub" x="352" y="150">출력 토큰이 길수록 · 서비스가 바쁠수록 길어집니다</text>
<rect class="box" x="760" y="108" width="160" height="62" rx="10"/>
<text class="lblb" x="772" y="132">④ 응답 도착</text><text class="sub" x="772" y="150">수신 · SDK 가 응답 처리</text>
<path class="brkg" d="M340,182 L340,194 L760,194 L760,182"/>
<text class="lblb" x="550" y="214" text-anchor="middle">AOAI 가 잰 시간(DurationMs) — AOAI 진단 로그 R1 · 메트릭 R2</text>
<path class="brkw" d="M40,182 L40,194 L340,194 L340,182"/>
<text class="lbl" x="190" y="214" text-anchor="middle">probe 가 구간별로 잰 시간 R7</text>
<text class="sub" x="190" y="232" text-anchor="middle">네트워크 경로 R6 · VM 상태 R5 · 동시 호출 수 R3</text>
<rect class="box" x="40" y="252" width="880" height="84" rx="12"/>
<text class="ttl" x="56" y="274">두 시간을 같은 요청끼리 빼 보면 (C 단계에서 계산)</text>
<text class="lbl" x="56" y="298">앱이 잰 시간 − AOAI 가 잰 시간 = SDK 호출 구간에서 AOAI 바깥(연결 · 네트워크 · SDK)이 쓴 시간</text>
<text class="lbl" x="56" y="320">실습에서는 보통 70~130ms 였고, 갑자기 커지면 원인은 AOAI 가 아닙니다. ①(호출 전 대기)은 total_ms 에 들어가지 않습니다.</text>
</svg>"""

# 실습 환경 구성도 (기존)
SVG = """<svg viewBox="0 0 960 330" role="img" aria-label="실습 환경 구성도: VM의 앱·probe·에이전트와 Azure OpenAI, Application Insights, Connection Monitor가 하나의 Log Analytics 워크스페이스로 로그를 보냅니다">
<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="arrh"/></marker></defs>
<rect class="box" x="16" y="28" width="340" height="276" rx="14"/>
<text class="ttl" x="32" y="50">VM · RHEL 9 (인바운드 포트 없음)</text>
<rect class="boxa" x="32" y="62" width="308" height="66" rx="10"/>
<text class="lbl" x="46" y="86">데모 앱 report-agent</text><text class="sub" x="46" y="106">R3 호출 로그(JSON) + R4 OpenTelemetry</text>
<rect class="box" x="32" y="140" width="308" height="52" rx="10"/>
<text class="lbl" x="46" y="162">합성 probe (1분 타이머)</text><text class="sub" x="46" y="180">R7 · syslog local5 + 지연 순간 스냅샷</text>
<rect class="box" x="32" y="204" width="308" height="52" rx="10"/>
<text class="lbl" x="46" y="226">Azure Monitor Agent</text><text class="sub" x="46" y="244">R5 · 성능 카운터 12개 + cron·local5 syslog</text>
<rect class="boxa" x="470" y="28" width="262" height="86" rx="12"/>
<text class="ttl" x="486" y="50">AZURE OPENAI</text><text class="lbl" x="486" y="72">gpt-4.1-mini (Global Standard)</text><text class="sub" x="486" y="92">R1 진단 설정 · R2 메트릭</text>
<rect class="box" x="470" y="130" width="262" height="62" rx="12"/>
<text class="lbl" x="486" y="156">Application Insights</text><text class="sub" x="486" y="176">R4 · AppDependencies · AppTraces</text>
<rect class="box" x="470" y="208" width="262" height="62" rx="12"/>
<text class="lbl" x="486" y="234">Connection Monitor</text><text class="sub" x="486" y="254">R6 · VM → AOAI:443 · 30초 간격</text>
<rect class="boxa" x="800" y="28" width="148" height="276" rx="14"/>
<text class="ttl" x="814" y="52">LOG ANALYTICS</text>
<text class="sub" x="814" y="82">AzureDiagnostics</text><text class="sub" x="814" y="102">AzureMetrics</text><text class="sub" x="814" y="122">AppDependencies</text>
<text class="sub" x="814" y="142">AppTraces</text><text class="sub" x="814" y="162">Perf</text><text class="sub" x="814" y="182">Syslog</text>
<text class="sub" x="814" y="202">Heartbeat</text><text class="sub" x="814" y="222">NWConnectionMonitor…</text>
<text class="lbl" x="814" y="274">한 곳에서 시간으로</text><text class="lbl" x="814" y="292">맞춰 봅니다</text>
<path class="arr" d="M340,92 L470,64" marker-end="url(#ah)"/>
<path class="arr" d="M340,160 L470,100" marker-end="url(#ah)"/>
<path class="arr" d="M340,112 L470,158" marker-end="url(#ah)"/>
<path class="arr" d="M340,236 L420,236 L420,300 L874,300 L874,304" marker-end="url(#ah)"/>
<path class="arr" d="M732,70 L800,70" marker-end="url(#ah)"/>
<path class="arr" d="M732,162 L800,162" marker-end="url(#ah)"/>
<path class="arr" d="M732,240 L800,240" marker-end="url(#ah)"/>
<text class="sub" x="372" y="62">호출</text>
</svg>"""


def build_front():
    """시작하기 전에 · 용어 사전 · 읽는 법 · 준비물 — 네 개의 섹션"""
    # ───────── 1. 이 가이드가 하는 일
    segments = table(
        ["구간", "시간이 걸리는 이유(예)", "이 구간을 보는 기록 (R번호는 아래 표)"],
        [
            ["① 호출 전 · 앱 안", "요청이 앱 안에서 기다림(작업 큐 · 동시 호출 · CPU · 메모리 부족 · 정각에 도는 배치 작업)", "동시 호출 수(R3 `inflight`) · VM 성능과 cron(R5) · probe(R7). 앱 자체의 작업 큐는 앱에서 따로 계측"],
            ["② 앱 ↔ AOAI 사이", "DNS 조회 · 연결(TCP/TLS) 지연 · 방화벽/NAT · 재시도", "앱 시간 − AOAI 시간(C2) · probe(R7) · 네트워크 경로 로그(R6)"],
            ["③ AOAI 서비스", "모델이 답을 만드는 시간(출력이 길수록 ↑) · 서비스 혼잡 · 한도 초과(429)", "AOAI 진단 로그(R1) · AOAI 메트릭(R2)"],
        ],
        cls="nw",
    )
    judge = table(
        ["이런 패턴이 보이면", "의심할 곳"],
        [
            ["앱만 길고 AOAI 처리 시간은 정상(차이가 큼)", "AOAI 바깥 — SDK 호출 구간의 연결 · 네트워크 (호출 전 앱 대기는 별도 계측)"],
            ["앱 지연이 정각 · 30분 cron · CPU 상승과 겹침", "VM 자원 · 스케줄 작업 경합"],
            ["앱 · probe(VM 안)만 느리고 probe(VM 밖)는 정상", "VM → AOAI 경로(방화벽 · DNS · SNAT)"],
            ["앱 · AOAI · probe 모두 느림", "AOAI 서비스 · 공유 용량"],
            ["AOAI 에 499, 처리 시간이 앱 timeout 과 비슷", "앱 timeout 이 먼저 끊음(긴 출력 · 큰 입력)"],
        ],
    )
    sec_start = section(
        "start",
        "이 가이드가 하는 일",
        "문제 · 방법 · 전체 그림",
        md(
            """
            AOAI(Azure OpenAI)를 호출하는 앱의 응답이 **가끔 느릴 때**, ‘느리다’는 사실만으로는 원인을 알 수 없습니다. 시간이 쓰일 수 있는 곳이 **세 군데**이기 때문입니다. (아래 R1~R8 은 이 가이드가 로그 수집 항목에 붙인 번호입니다: R1 AOAI 진단 로그 · R2 AOAI 메트릭 · R3 앱 호출 로그 · R4 Application Insights · R5 VM 모니터링 에이전트 · R6 네트워크 경로 · R7 합성 probe · R8 알림. 자세한 표는 아래에 있습니다.)
            """
        )
        + segments
        + md(
            """
            각 구간의 시간을 **따로 잰 기록이 없으면** ‘어디서’ 느린지 구분할 수 없습니다. 이 가이드는 구간마다 기록을 남기는 8가지 설정(R1~R8)을 **새 리소스 그룹에 처음부터 만들어 가며** 하나씩 켜 보고, 마지막에 **앱과 AOAI 는 요청 ID 로 한 건씩, VM 과 네트워크는 시각으로** 맞춰 보는 방법까지 해 봅니다.
            """
        )
        + diagram(SVG_TIMELINE)
        + call(
            "tip",
            "이 가이드를 끝내면 할 수 있는 것",
            """
            - 요청 한 건마다 **앱이 잰 시간과 AOAI 가 잰 시간을 비교**해, 느린 시간이 **AOAI 안인지 바깥(연결 · 네트워크)인지** 구분한다.
            - 느린 시각이 **정각 · 30분에 도는 배치 작업(cron)** 이나 VM 부하와 겹치는지 **확인하는 방법**을 익힌다(이 실습 데이터는 1시간 남짓이라 실제 패턴은 나오지 않습니다).
            - 느림 · 실패가 생기면 **이메일 알림**을 받고, 그 순간의 VM 상태 스냅샷을 남긴다.
            """,
        )
        + md("#### 이 가이드가 도와주는 판단 — 미리보기")
        + judge
        + md("각 패턴을 실제 데이터로 확인하는 방법과 해석은 [C5](#c5)에 있습니다.")
        + md("**실습 환경은 이렇게 구성됩니다.** VM 위에서 데모 앱 · probe · 모니터링 에이전트가 돌고, 모든 로그가 하나의 Log Analytics 워크스페이스로 모입니다.")
        + diagram(SVG)
        + md("#### 어디에 무엇을 켜나요 — R1 ~ R8 한눈에")
        + table(
            ["R", "모으는 것", "설정하는 곳", "쌓이는 테이블", "앱 코드 수정?", "단계"],
            [
                ["R1", "AOAI 서비스가 잰 **요청별 처리 시간 · 상태 코드 · 토큰 수**", "AOAI 리소스(진단 설정)", "`AzureDiagnostics`", "없음", "[B1](#b1)"],
                ["R2", "AOAI 메트릭(분당 요청 수 · 상태 코드별 · 응답 완료 시간)", "AOAI 리소스(이미 쌓이고 있음, 조회만)", "`AzureMetrics`(+ 메트릭 저장소)", "없음", "[B5](#b5)"],
                ["R3", "앱이 잰 호출별 **지연 · 결과 · 요청 ID · 토큰 수 · 동시 호출 수**(JSON 한 줄)", "앱 코드", "`AppTraces`", "**호출부를 `with` 블록으로 감싸기**(몇 줄)", "[B3](#b3)"],
                ["R4", "앱의 외부 호출 · 로그를 Application Insights 로", "앱 시작 코드 + 환경변수", "`AppDependencies` · `AppTraces`", "**시작 코드 2줄**", "[B3](#b3)"],
                ["R5", "VM 의 CPU · 메모리 · 디스크 · 네트워크 + cron/syslog", "VM(모니터링 에이전트 + 수집 규칙)", "`Perf` · `Syslog` · `Heartbeat`", "없음", "[B2](#b2)"],
                ["R6", "VM → AOAI 경로의 연결 시간 · 실패율 · 방화벽 로그", "네트워크 리소스", "`NWConnectionMonitorTestResult` · `AZFW*`", "없음", "[B7](#b7)"],
                ["R7", "1분마다 AOAI · 앱 URL 에 보내는 **합성 호출의 구간별 시간** + 지연 순간의 VM 스냅샷", "VM(스크립트 + 타이머)", "`Syslog`(local5)", "없음(스크립트 설치)", "[B4](#b4)"],
                ["R8", "지연 · 실패를 알려 주는 알림 4종", "Azure Monitor", "(알림 규칙)", "없음", "[B6](#b6)"],
            ],
            cls="map",
        ),
    )

    # ───────── 2. 용어 사전
    sec_terms = section(
        "terms",
        "먼저 알아 둘 말",
        "용어 사전 — 모르는 말이 나오면 여기로 돌아오세요",
        md("처음 보는 말이 많아도 괜찮습니다. 아래는 이 가이드에 나오는 말을 **쉽게 풀어 쓴 것**입니다. 본문에서도 처음 나올 때 한 번 더 풀어 씁니다.")
        + md("#### Azure OpenAI 와 호출")
        + gloss_group(["aoai", "region", "deployment", "sdk", "sku", "tpm", "token", "status", "timeout", "apiver", "p95", "reasoning"])
        + md("#### 로그 · 모니터링")
        + gloss_group(["law", "kql", "appi", "diag", "metric", "otel", "sampling", "reqid", "alert", "ingest", "utc", "avail", "support"])
        + md("#### VM · 네트워크 · 권한")
        + gloss_group(["ama", "facility", "mi", "entra_a", "rbac", "systemd", "syslog", "probe", "dns", "nat", "net", "rtt", "fqdn", "snat", "nva", "rg"])
        + md("#### 이 가이드의 말")
        + gloss_group(["rnum"]),
    )

    # ───────── 3. 읽는 법 · 전체 단계
    LAB = Raw('<span class="scope">실습 준비</span>')
    APPLY = Raw('<span class="scope apply">그대로 적용</span>')
    CHECK = Raw('<span class="scope check">확인</span>')
    steps_map = table(
        ["단계", "하는 일", "시간", "이름표", "끝나면"],
        [
            ["[A1](#a1)", "구독 선택 · 변수 · 도우미 함수 만들기", "2분", LAB, "`lablog.env` 파일 · `vmrun` · `kq` 함수"],
            ["[A2](#a2)", "리소스 그룹 · 워크스페이스 · Application Insights · 네트워크", "2분", LAB, "리소스 5개"],
            ["[A3](#a3)", "Azure OpenAI 와 모델 배포", "2분", LAB, "호출할 수 있는 모델 배포"],
            ["[A4](#a4)", "RHEL 9 VM 과 관리 ID 권한", "3분", LAB, "앱이 돌 VM"],
            ["[A5](#a5)", "VM 에 Python 3.12 · 패키지 설치", "3분", LAB, "앱을 돌릴 준비 완료"],
            ["[B1](#b1)", "R1 · AOAI 진단 설정", "1분", APPLY, "AOAI 요청 로그가 워크스페이스로(20~26분 뒤 도착)"],
            ["[B2](#b2)", "R5 · 모니터링 에이전트 + 수집 규칙", "3분", APPLY, "VM 성능 · syslog 수집"],
            ["[B3](#b3)", "R3 · R4 · 데모 앱(호출 로그 + Application Insights)", "3분", APPLY, "호출마다 JSON 로그 · 앱 추적"],
            ["[B4](#b4)", "R7 · 합성 probe", "2분", APPLY, "1분마다 구간별 시간 기록"],
            ["[B5](#b5)", "R2 · AOAI 메트릭 확인", "1분", CHECK, "상태 코드 값 확인"],
            ["[B6](#b6)", "R8 · 알림 4종", "2분", APPLY, "느림 · 실패 알림"],
            ["[B7](#b7)", "R6 · 네트워크 경로 로그 (경로가 의심될 때만)", "5분", Raw('<span class="scope check">선택</span>'), "연결 시간 · 실패율"],
            ["[C1~C5](#c1)", "도착 확인 · 요청 한 건 대조 · 시간 패턴 · VM 쪽 · 체크리스트", "10분", CHECK, "느린 구간을 구분하는 법"],
            ["[D](#d1)", "비용 중지 또는 전체 삭제", "5분", Raw('<span class="scope">정리</span>'), "리소스 정리"],
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
        + terminal_rules("cd ~/aoai-lab && source lablog.env", extra=[
            "**값을 넣어야 하는 코드**(예: `export SUB=\"<구독 ID>\"`)는 ‘전체 복사’ 를 터미널에 바로 붙이지 말고, 메모장에 먼저 붙여 꺾쇠째 실제 값으로 바꾼 뒤 다시 복사해 실행하세요.",
            "**번호 구간은 한 명령(스크립트)을 설명하려고 자른 조각**입니다. 중간만 복사하면 `<<'EOF'` 나 `'` 가 닫히지 않아 터미널이 입력을 기다립니다(멈추면 `Ctrl+C`). 항상 코드 상자 위의 **‘전체 복사’** 로 한 번에 붙이세요. `<<'EOF' … EOF`(heredoc)는 그 사이의 줄들을 그대로 입력으로 넘기는 셸 문법이고, `export` 는 변수를 이후 명령에서도 쓰게 하는 지정입니다.",
            "VM **안**에서 실행하는 명령(`systemctl` · `journalctl` · `cat /etc/redhat-release` 등)은 내 컴퓨터가 아니라 VM 안에서 실행합니다. `vmrun <<'X'` 다음 줄에 명령을 쓰고 `X` 로 닫으면 됩니다(A1 에서 만드는 도우미 함수).",
        ])
        + md("#### 전체 단계 한눈에")
        + md(
            """
            **A** 는 실습을 위해 새로 만드는 환경이라 **내 환경에서는 보통 건너뜁니다**(이미 AOAI · 앱 · VM 이 있으므로). 내 환경에는 **B 의 설정**이 해당 리소스(AOAI · VM · 앱)에 그대로 적용됩니다. 내 환경에 쓰려면 먼저 [부록 B](#x2) 의 변수표와 단계별 표를 보세요. B3 · B4 처럼 데모 파일이 섞인 단계는 **구간마다 ‘실습 전용’ · ‘내 환경에도’ 이름표**가 붙어 있어 무엇을 가져가면 되는지 알 수 있습니다.
            """
        )
        + steps_map
        + call(
            "tip",
            "시간 계획 — 로그가 쌓이는 동안 다른 단계를 합니다",
            """
            **A 약 12~15분 → B 약 17분**(B1 을 가장 먼저 켜고, 로그가 쌓이는 동안 나머지를 진행) **→ 남은 대기 약 10분 → C 약 10분 → D 약 5분 = 약 1시간**입니다. 시간표로 보면 **T+0 B1 설정 → T+20~26분 AOAI 로그 도착 시작 → T+30분 이후 C1 확인**입니다. 처음 해 본다면 **2~3시간 여유**를 두세요.
            """,
        ),
    )

    # ───────── 4. 준비물
    prereq_tbl = table(
        ["항목", "요구 사항", "비고"],
        [
            ["Azure CLI", "2.60 이상 (이 가이드는 2.86 으로 검증)", "`az version` · 없다면 [설치 안내](https://learn.microsoft.com/cli/azure/install-azure-cli)"],
            ["셸", "bash (macOS · Linux · WSL · Azure Cloud Shell)", "Windows 는 WSL 또는 Cloud Shell 에서 실행하세요(PowerShell 명령은 제공하지 않습니다) · Cloud Shell 이면 설치가 필요 없습니다"],
            ["구독 권한", "실습용 구독의 **Owner**, 또는 **Contributor + User Access Administrator**(역할 부여가 필요)", "관리 ID 에 AOAI 호출 역할을 부여합니다"],
            ["AOAI 쿼터", "koreacentral · Global Standard · gpt-4.1-mini 20K TPM 이상", "아래 확인 명령"],
            ["비용(예상)", "3시간 기준 약 $2 안팎(예: VM(B2s · RHEL) 약 $0.1/시간 + AOAI 토큰 소액 + Log Analytics 수집). Log Analytics 는 시간당 약 1MB 를 수집했고 **청구 계정당 월 5GB 무료**(종량제 기준)에 포함되는 수준이었습니다", "금액은 **예시**입니다. 리전 · 라이선스 · 알림 · Connection Monitor 에 따라 달라지니 [Azure 가격 계산기](https://azure.microsoft.com/pricing/calculator/)로 확인하세요. Azure Firewall(선택)은 시간당 과금 — 쓰면 바로 삭제"],
        ],
        cls="nw",
    )
    workdir = code(
        "mkdir -p ~/aoai-lab && cd ~/aoai-lab",
        cap="① 작업 폴더 만들기 — 이 가이드가 만드는 파일(lablog.env · 임시 SSH 키 · 수집 규칙 JSON)이 이 폴더에 생깁니다",
    )
    quota = walk(
        """az cognitiveservices usage list -l koreacentral --query "[?name.value=='OpenAI.GlobalStandard.gpt4.1-mini'].{used:currentValue,limit:limit}" -o table""",
        [
            (
                "az cognitiveservices usage list",
                "이 구독의 koreacentral 모델 쿼터를 조회해 gpt-4.1-mini 한 줄만 보여 줍니다",
                """
                * `az cognitiveservices usage list -l koreacentral` — 이 구독이 koreacentral 리전에서 쓸 수 있는 **모델별 쿼터(한도)와 현재 사용량** 전체를 가져옵니다.
                * `--query "[?name.value=='OpenAI.GlobalStandard.gpt4.1-mini'] …"` — 결과(목록)에서 이름이 `OpenAI.GlobalStandard.gpt4.1-mini`(Global Standard 방식의 gpt-4.1-mini)인 항목만 고릅니다. 이런 필터 문법을 JMESPath 라고 합니다.
                * `.{used:currentValue,limit:limit}` — 고른 항목에서 **현재 사용량(used)** 과 **한도(limit)** 두 칸만 남깁니다.
                * `-o table` — 결과를 표로 출력합니다.

                단위는 **1K TPM**(분당 1,000 토큰)입니다. 이 실습은 배포 용량 20(= 분당 2만 토큰)을 쓰므로 `limit − used` 가 20 이상이어야 합니다.
                """,
            )
        ],
        cap="② 쿼터 확인 명령 (로그인이 되어 있어야 합니다 — 아직이라면 A1 의 로그인 뒤에 실행해도 됩니다)",
    )
    sec_prep = section(
        "prep",
        "준비물 · 안전 수칙",
        "시작 전에 확인할 것",
        prereq_tbl
        + workdir
        + quota
        + out(
            """Used    Limit
------  -------
0.0     5000.0""",
            read="""
            - `Limit` 에서 `Used` 를 뺀 값이 20 이상이면 이 실습을 진행할 수 있습니다(위 예: 5000 − 0).
            - **아무것도 나오지 않으면** 그 모델이 이 리전에 없다는 뜻입니다. 다른 리전을 쓰려면 A1 의 `LOC` 와 이 명령의 `-l` 을 함께 바꾸세요. 한도가 부족하면 Foundry 포털의 할당량(Quotas) 화면이나 Azure 지원 요청으로 쿼터 증설을 요청하세요(경로는 포털 버전에 따라 다를 수 있습니다).
            """,
        )
        + call(
            "warn",
            "안전 수칙",
            """
            - **실습용 구독**에서 실행하세요. 마지막 단계(D)에서 리소스 그룹을 통째로 삭제합니다.
            - VM 에는 **인터넷에서 들어오는 접속을 허용하는 규칙이 없습니다.** 모든 VM 작업은 `az vm run-command` 로 수행하므로 SSH 가 필요 없습니다.
            - 데모 앱은 AOAI **키**를 씁니다. 이 실습에서 키는 내 터미널 → Azure Run Command 파라미터(보호되지 않는 일반 파라미터) → VM 의 `/etc/report-agent/app.env`(권한 600) 순서로 전달됩니다. **실습이 끝나면 리소스 그룹을 지우거나 키를 재생성**하세요. 운영에서는 키 대신 관리 ID 를 쓰세요(probe 는 이미 관리 ID 를 사용).
            - 수집하는 것은 시간 · 상태 · 토큰 수 같은 **메타데이터뿐**이며 프롬프트 · 응답 본문은 기록하지 않습니다.
            """,
        ),
    )
    return sec_start + sec_terms + sec_howto + sec_prep


def build():
    # ───────────────── A. 실습 환경
    a1_login = walk(
        """az login                                        # 이미 로그인되어 있으면 생략 (Cloud Shell 은 불필요)
export SUB="<구독 ID>"                          # ← 실습용 구독 ID 로 바꿉니다 (az account list -o table)
az account set -s "$SUB"
for e in application-insights log-analytics scheduled-query monitor-control-service; do az extension add -n $e -y 2>/dev/null; done
for p in Microsoft.CognitiveServices Microsoft.Insights Microsoft.OperationalInsights Microsoft.Compute Microsoft.Network Microsoft.Storage Microsoft.AlertsManagement; do az provider register -n $p >/dev/null; done""",
        [
            ("az login", "Azure 에 로그인", "브라우저가 열리고 계정을 고르면 터미널이 Azure 에 로그인된 상태가 됩니다. 이미 로그인했다면 건너뛰어도 됩니다(Azure Cloud Shell 은 처음부터 로그인되어 있습니다)."),
            (
                "export SUB=",
                "실습할 구독을 고정",
                """
                `SUB` 에 **구독 ID** 를 넣고(`<구독 ID>` 를 직접 바꿔 넣는 자리), `az account set` 으로 **이후 모든 `az` 명령이 이 구독만 대상으로 하게** 합니다. 구독이 여러 개인 계정에서 엉뚱한 구독에 리소스가 만들어지는 실수를 막아 줍니다. 구독 ID 는 `az account list -o table` 결과의 **`SubscriptionId` 열**(GUID)에서 볼 수 있습니다. **값을 넣는 순서**: 이 상자의 ‘전체 복사’ 를 터미널에 바로 붙이지 말고, 메모장에 먼저 붙여 `<구독 ID>` 를 꺾쇠째 실제 값으로 바꾼 뒤 다시 복사해 실행하세요.
                """,
            ),
            (
                "for e in application-insights",
                "az 확장 4개 설치",
                """
                `az` 의 일부 기능(Application Insights · Log Analytics · 로그 알림 · 수집 규칙)은 **확장(extension)** 으로 따로 설치해야 합니다. 4개를 한 번에 설치합니다.

                * `-y` — 설치 여부를 묻는 질문에 자동으로 ‘예’
                * `2>/dev/null` — **모든 오류 출력**(이미 설치되어 있다는 안내 포함)을 숨김. 설치가 실패해도 보이지 않으니, 뒤에서 ‘확장이 없다’는 오류가 나면 이 줄을 `2>/dev/null` 없이 다시 실행해 보세요
                """,
            ),
            (
                "for p in Microsoft.CognitiveServices",
                "리소스 공급자 7개 등록",
                """
                Azure 는 서비스 종류(= **리소스 공급자**)마다 구독에서 **한 번 등록**해야 그 리소스를 만들 수 있습니다. 이 실습에 쓰는 7개(AOAI · 모니터링 · Log Analytics · VM · 네트워크 · 저장소 · 알림)를 등록합니다.
                이미 등록되어 있으면 아무 일도 일어나지 않습니다. **처음 등록하는 구독이면 등록이 끝나기까지 몇 분 걸리고**(명령은 기다리지 않고 바로 끝납니다), 끝나기 전에 A2 로 넘어가면 리소스 생성이 실패할 수 있습니다. **이 상자 아래의 ‘(확인)’ 명령으로 7개가 모두 `Registered` 인지 확인한 뒤** 넘어가세요.
                """,
            ),
        ],
        cap="① 구독과 확장 설치",
        run="A1",
    )
    a1_vars = walk(
        """export LOC=koreacentral
export SFX=$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c5)      # 이름 충돌을 피하는 5자리 접미사
export RG=rg-lablog-$SFX LAW_NAME=law-lablog-$SFX APPI=appi-lablog-$SFX AOAI=oai-lablog-$SFX ST=stlablog$SFX
export DEP=gpt41mini VNET=vnet-lablog SNET=snet-vm NSG=nsg-lablog-vm PIP=pip-lablog-vm VM=vm-lablog-rhel
export MAIL="<알림 받을 이메일>"                                      # ← 본인 메일 (B6 알림 수신)
# 뒤 단계의 명령이 그대로 쓰는 값 (리소스 ID · 호스트 이름 · 꼬리표)
export LAW=/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.OperationalInsights/workspaces/$LAW_NAME
export VM_RG=$RG AOAI_HOST=$AOAI.openai.azure.com
export TAGS="purpose=aoai-logging-lab created=$(date +%F)"
# 새 터미널에서도 이어서 쓰도록 파일로 저장합니다 (다시 열 때: source lablog.env)
cat > lablog.env <<EOF
export SUB="$SUB" LOC=$LOC SFX=$SFX RG=$RG LAW_NAME=$LAW_NAME APPI=$APPI AOAI=$AOAI ST=$ST
export DEP=$DEP VNET=$VNET SNET=$SNET NSG=$NSG PIP=$PIP VM=$VM MAIL="$MAIL"
export LAW=$LAW VM_RG=$VM_RG AOAI_HOST=$AOAI_HOST TAGS="$TAGS"
EOF
cat >> lablog.env <<'EOF'
# VM 에서 스크립트 실행 (SSH 없이 az vm run-command 사용). 사용: vmrun [KEY=값 ...] <<'X' ... X
vmrun() { local s; s="$(cat)"; if [ $# -gt 0 ]; then az vm run-command invoke -g "$RG" -n "$VM" --command-id RunShellScript --scripts "$s" --parameters "$@" --query "value[0].message" -o tsv; else az vm run-command invoke -g "$RG" -n "$VM" --command-id RunShellScript --scripts "$s" --query "value[0].message" -o tsv; fi; }
# Log Analytics 쿼리 실행 (사용: kq '<KQL>')
kq() { : "${WSID:=$(az monitor log-analytics workspace show -g "$RG" -n "$LAW_NAME" --query customerId -o tsv)}"; az monitor log-analytics query -w "$WSID" --analytics-query "$1" -o table; }
EOF
source lablog.env
echo "RG=$RG  AOAI=$AOAI  VM=$VM" """,
        [
            (
                "export LOC=",
                "리전과 이름 접미사",
                """
                * `LOC=koreacentral` — 모든 리소스를 만들 **리전(위치)**. 한국 중부로 정했습니다. 다른 리전을 쓰려면 이 값과 함께 **준비물의 쿼터 확인 명령**, **B7 의 `-l koreacentral` 두 곳**도 바꿉니다.
                * `SFX=$(…)` — **무작위 5글자**(소문자 · 숫자)를 만들어 이름 뒤에 붙입니다. `tr -dc 'a-z0-9' </dev/urandom` 이 무작위 바이트에서 소문자 · 숫자만 남기고, `head -c5` 가 앞 5글자를 고릅니다. AOAI · 저장소 이름은 **전 세계에서 유일**해야 해서, 다시 실습해도 이름이 겹치지 않게 하려는 것입니다.
                """,
            ),
            (
                "export RG=",
                "리소스 이름 정하기 (1)",
                """
                `RG`(리소스 그룹) · `LAW_NAME`(워크스페이스) · `APPI`(Application Insights) · `AOAI`(Azure OpenAI) · `ST`(저장소 계정) 이름을 **`종류-lablog-접미사`** 형태로 정합니다. 이름 규칙은 리소스마다 달라서(저장소 계정은 소문자·숫자만 3~24자) `ST` 만 하이픈이 없습니다.
                """,
            ),
            (
                "export DEP=",
                "리소스 이름 정하기 (2)",
                """
                `DEP` = 모델 **배포 이름**(앱이 이 이름으로 호출), `VNET` · `SNET` · `NSG` · `PIP` = 가상 네트워크 · 서브넷 · 네트워크 보안 그룹 · 공용 IP, `VM` = 가상 머신 이름입니다. 이 이름들은 고정값이라 접미사가 없습니다(같은 리소스 그룹 안에서만 유일하면 됩니다).
                """,
            ),
            (
                "export MAIL=",
                "알림 받을 이메일",
                "B6 에서 만드는 알림이 이 주소로 메일을 보냅니다. `<알림 받을 이메일>` 을 본인 메일로 바꿔 넣으세요(꺾쇠는 지웁니다). 위 구독 ID 와 같은 방법으로, 메모장에서 바꾼 뒤 복사하세요.",
            ),
            (
                "# 뒤 단계의 명령이",
                "뒤 단계에서 쓰는 변수들",
                """
                뒤 단계(B · C)의 명령들이 `LAW` · `VM_RG` · `AOAI_HOST` 같은 변수를 쓰므로 미리 만들어 둡니다. **이름을 이대로 두면 뒤 단계의 명령을 그대로 붙여 넣을 수 있습니다.**

                * `LAW` — 워크스페이스의 **리소스 ID**(`/subscriptions/…/workspaces/이름`). 여러 명령이 이름이 아니라 ID 를 요구합니다.
                * `VM_RG` — VM 이 있는 리소스 그룹(여기서는 `RG` 와 같음)
                * `AOAI_HOST` — AOAI 호출 주소의 호스트 부분(`<AOAI 이름>.openai.azure.com`)
                * `TAGS` — 모든 리소스에 붙일 **꼬리표**(목적 · 생성일). 나중에 실습 리소스를 찾아 지울 때 편합니다.
                """,
            ),
            (
                "# 새 터미널에서도",
                "변수를 파일로 저장 — lablog.env",
                """
                지금까지 정한 값을 `lablog.env` 파일에 **구체적인 값으로** 적어 둡니다. 새 터미널에서 `source lablog.env` 한 줄이면 변수가 모두 되살아납니다.

                `<<EOF` 처럼 **따옴표 없는 EOF** 는 `$RG` 같은 변수를 **지금 값으로 바꿔서** 파일에 씁니다(그래서 파일 안에는 `RG=rg-lablog-x7k2q` 처럼 실제 값이 적힙니다).
                """,
            ),
            (
                "cat >> lablog.env",
                "도우미 함수 ① vmrun — VM 안에서 명령 실행",
                """
                `>>` 는 파일 **끝에 덧붙이기**, `<<'EOF'`(따옴표 있는 EOF)는 변수를 **바꾸지 않고 글자 그대로** 쓰라는 뜻입니다. 함수 안의 `$RG` · `$VM` 은 **함수를 부를 때** 그때의 값으로 해석되어야 하기 때문입니다.

                `vmrun` 은 **VM 안에서 스크립트를 실행**하는 함수입니다. 사용법은 `vmrun <<'X'` 아래에 실행할 스크립트를 적고 `X` 로 끝내는 것입니다.
                * `local s; s="$(cat)"` — `local` 은 ‘이 함수 안에서만 쓰는 변수’이고, `$(cat)` 은 표준입력(heredoc)으로 들어온 스크립트를 읽어 `s` 에 담습니다.
                * `az vm run-command invoke … --command-id RunShellScript --scripts "$s"` — Azure 가 VM 에 설치된 에이전트(Azure VM 에이전트, `waagent`)를 통해 스크립트를 **VM 안에서 root 권한으로** 실행합니다(그래서 뒤의 `dnf` 를 `sudo` 없이 씁니다). **SSH 접속이 필요 없고** VM 에 인바운드 포트를 열 필요도 없습니다.
                * `--parameters "$@"` — `$@` 는 함수에 넘긴 **인자 전체**입니다. `vmrun AOAI_HOST=값 DEP=값` 처럼 넘긴 `이름=값` 들을 VM 안 스크립트가 `$이름` 으로 쓸 수 있게 전달합니다. 인자가 하나도 없으면(`$#` 가 0) 이 부분을 뺍니다 — 앞의 `if [ $# -gt 0 ]` 가 그 판단입니다.
                * `--query "value[0].message" -o tsv` — 실행 결과(표준출력)만 글자 그대로 출력합니다.

                **heredoc 이 두 구간에 걸쳐 있습니다.** 이 구간의 `cat >> lablog.env <<'EOF'` 로 시작한 입력은 **다음 구간의 `kq()` 정의 바로 뒤 `EOF` 줄에서 끝납니다.** 그 사이의 모든 줄이 파일에 덧붙여집니다.
                """,
            ),
            (
                "kq()",
                "도우미 함수 ② kq — 로그 조회",
                """
                `kq '<KQL 질의>'` 한 줄로 Log Analytics 를 조회해 표로 보여 주는 함수입니다.
                * `: "${WSID:=$(…)}"` — `WSID` 가 비어 있으면 워크스페이스의 **고유 ID(customerId)** 를 조회해 담습니다. `:` 는 ‘아무것도 안 하는 명령’이라 이 줄은 **값을 한 번만 가져와 저장(캐시)** 하는 역할만 합니다. 두 번째 호출부터는 이 조회를 건너뜁니다.
                * `az monitor log-analytics query -w "$WSID" --analytics-query "$1" -o table` — 첫 번째 인자(`$1` = 작은따옴표로 감싼 KQL)를 실행해 **표**로 출력합니다.
                """,
            ),
            (
                "source lablog.env",
                "파일을 읽어 적용하고 확인",
                "`source lablog.env` 는 방금 만든 파일을 **현재 터미널에 적용**합니다(변수와 함수 2개가 이 터미널에서 쓸 수 있게 됨). 마지막 `echo` 로 값이 들어갔는지 확인합니다.",
            ),
        ],
        cap="② 변수 · 파일 저장 · 도우미 함수 (vmrun, kq)",
        run="A1",
    )
    a1 = step(
        "a1",
        "구독 선택 · 변수 · 도우미 함수",
        "A1",
        "소요 약 2분",
        brief(
            what="실습용 구독을 고르고, 이후 모든 단계가 쓰는 **변수(이름 · 위치)** 와 도우미 함수 2개(`vmrun` · `kq`)를 만듭니다.",
            why="리소스 이름을 매번 치지 않고 `$RG` 처럼 부르기 위해서, 그리고 ‘VM 안에서 명령 실행’(`vmrun`)과 ‘로그 조회’(`kq`)를 한 줄로 줄이기 위해서입니다.",
            result="`lablog.env` 파일(변수 + 함수)이 생깁니다. 새 터미널에서도 `source lablog.env` 한 줄로 되살립니다.",
            apply="내 환경에서는 **새로 만들지 않고 이미 있는 리소스의 이름**을 같은 변수에 넣어 쓰면 됩니다(예: `AOAI` · `RG` · `LAW` · `VM`).",
        )
        + a1_login
        + code(
            'for p in Microsoft.CognitiveServices Microsoft.Insights Microsoft.OperationalInsights Microsoft.Compute Microsoft.Network Microsoft.Storage Microsoft.AlertsManagement; do printf "%-36s" "$p"; az provider show -n $p --query registrationState -o tsv; done',
            cap="(확인) 리소스 공급자 7개가 모두 Registered 인지 — 확인용 명령 · 실행 블록 아님",
        )
        + md("일곱 줄이 모두 `Registered` 이면 다음으로 넘어갑니다. `Registering` 이 있으면 **1~2분 뒤 이 확인 명령을 다시** 실행하세요(등록은 구독에서 한 번만 하면 됩니다).")
        + a1_vars
        + out("RG=rg-lablog-x7k2q  AOAI=oai-lablog-x7k2q  VM=vm-lablog-rhel", read="`x7k2q` 부분은 실행할 때마다 다른 무작위 값입니다. 세 값이 모두 비어 있지 않으면 성공입니다.")
        + code(
            'echo "SUB=$SUB  MAIL=$MAIL"; az account show --query "{subscription:name, account:user.name}" -o table',
            cap="(확인) 내가 직접 넣은 구독 ID 와 메일이 맞게 들어갔는지 — 실행 블록이 아닌 확인용 명령",
        )
        + call(
            "info",
            "표의 열 순서가 다를 수 있습니다",
            "`az` 는 표의 열을 **알파벳순**으로 보여 주고, 버전에 따라 맨 앞에 `TableName`(항상 `PrimaryResult`) 열을 하나 더 붙이기도 합니다. 그래서 이 문서의 ‘예상 결과’와 열 순서가 다를 수 있지만 내용은 같습니다. VM 에 값을 넘길 때 `;` 처럼 셸 특수문자가 들어간 값(예: 연결 문자열)은 base64 로 바꿔 넘깁니다(B3 참고).",
        ),
        scope="lab",
    )

    a2 = step(
        "a2",
        "리소스 그룹 · Log Analytics · Application Insights · 네트워크",
        "A2",
        "소요 약 2분",
        brief(
            what="모든 로그가 모이는 **Log Analytics 워크스페이스**와 거기에 연결된 **Application Insights**, 그리고 VM 이 놓일 **가상 네트워크**를 만듭니다.",
            why="앱 · AOAI · VM 의 로그를 **한 워크스페이스에서 시간으로 맞춰 보려면** 같은 곳에 모여야 합니다.",
            result="리소스 그룹 하나 안에 리소스 5개(워크스페이스 · Application Insights · NSG · VNet · 공용 IP)가 생깁니다.",
            apply="내 환경에는 보통 **이미 있으므로 새로 만들지 마세요.** 기존 워크스페이스의 **리소스 ID** 를 `LAW` 에 넣고, 앱 · AOAI · VM 로그를 **같은 워크스페이스로 통일**하는 것을 권장합니다(부록 D).",
        )
        + walk(
            """az group create -n $RG -l $LOC --tags $TAGS -o none
az monitor log-analytics workspace create -g $RG -n $LAW_NAME -l $LOC --sku PerGB2018 --retention-time 30 --tags $TAGS -o none
az monitor app-insights component create -a $APPI -g $RG -l $LOC --kind web --application-type web --workspace "$LAW" --tags $TAGS -o none
az network nsg create -g $RG -n $NSG -l $LOC --tags $TAGS -o none
az network vnet create -g $RG -n $VNET -l $LOC --address-prefixes 10.20.0.0/16 --subnet-name $SNET --subnet-prefixes 10.20.1.0/24 --nsg $NSG --tags $TAGS -o none
az network public-ip create -g $RG -n $PIP -l $LOC --sku Standard --allocation-method Static --tags $TAGS -o none""",
            [
                (
                    "az group create",
                    "리소스 그룹 만들기",
                    """
                    리소스 그룹은 **리소스를 담는 폴더**입니다. 실습이 끝나면 이 그룹을 지워 모든 리소스를 한 번에 정리합니다.
                    * `-n $RG` — 그룹 이름
                    * `-l $LOC` — 위치(리전)
                    * `--tags $TAGS` — 나중에 찾기 쉽게 붙이는 꼬리표
                    * `-o none` — 성공 시 출력(JSON)을 생략합니다. 이후 모든 `az` 명령에서도 같은 뜻입니다.
                    """,
                ),
                (
                    "az monitor log-analytics workspace create",
                    "Log Analytics 워크스페이스 만들기",
                    """
                    모든 로그가 모일 **저장소**입니다.
                    * `--sku PerGB2018` — 저장한 데이터 양(GB)만큼 내는 요금 방식. 현재 표준입니다.
                    * `--retention-time 30` — 로그를 **30일** 보관합니다.
                    """,
                ),
                (
                    "az monitor app-insights component create",
                    "Application Insights 만들기 (워크스페이스 기반)",
                    """
                    앱의 호출 기록을 받을 서비스입니다.
                    * `--workspace "$LAW"` — **위 워크스페이스에 연결**합니다. 이렇게 ‘워크스페이스 기반’으로 만들면 앱 데이터가 별도 저장소가 아니라 **같은 워크스페이스**(`AppDependencies` · `AppTraces` 테이블)에 쌓여 AOAI · VM 로그와 한 번에 조회됩니다.
                    * `--kind web --application-type web` — 일반 웹/서비스 앱용 종류
                    """,
                ),
                (
                    "az network nsg create",
                    "네트워크 보안 그룹(NSG) 만들기",
                    "**방화벽 규칙 묶음**입니다. 인터넷에서 **들어오는(인바운드) 접속을 허용하는 규칙을 하나도 추가하지 않으므로** 인터넷에서 VM 으로 들어오는 접속은 차단됩니다(NSG 의 기본 규칙은 같은 VNet 안과 Azure 로드 밸런서의 트래픽만 허용합니다). 이 실습은 SSH 로 접속하지 않습니다.",
                ),
                (
                    "az network vnet create",
                    "가상 네트워크(VNet) 만들기",
                    """
                    * `--address-prefixes 10.20.0.0/16` — 네트워크 전체 주소 범위(사설 주소)
                    * `--subnet-name $SNET --subnet-prefixes 10.20.1.0/24` — 그 안의 작은 구역(서브넷) 하나. VM 이 여기에 놓입니다.
                    * `--nsg $NSG` — 위 보안 그룹을 이 서브넷에 연결
                    """,
                ),
                (
                    "az network public-ip create",
                    "공용 IP 만들기",
                    "VM 이 인터넷으로 **나가는** 데 쓰는 고정 공용 주소입니다(아래 알림 상자 참고). `--sku Standard` 는 기본 규칙이 ‘들어오는 접속 차단’인 SKU 라서 안전합니다.",
                ),
            ],
            cap="리소스 만들기 (명령 6줄 — 리소스 그룹 1개 + 리소스 5개)",
            run="A2",
        )
        + call(
            "info",
            "공용 IP 는 왜 만드나요",
            "새 가상 네트워크의 VM 은 **기본 아웃바운드 접속이 없습니다.** Standard 공용 IP 를 붙이면 **나가는 접속만** 열리고(인터넷에서 들어오는 접속은 NSG 에 허용 규칙이 없어 차단), VM 이 AOAI · Azure Monitor · 패키지 저장소에 나갈 수 있습니다.",
        )
        + walk(
            "az resource list -g $RG -o table",
            [("az resource list", "만들어진 리소스 확인", "`az resource list -g $RG` 는 리소스 그룹 안의 리소스를 모두 나열합니다. `-o table` 로 이름 · 종류만 표로 봅니다.")],
            cap="확인",
            run="A2",
        )
        + out(
            """Name              ResourceGroup     Location      Type
----------------  ----------------  ------------  ---------------------------------------
law-lablog-…       rg-lablog-…        koreacentral  Microsoft.OperationalInsights/workspaces
appi-lablog-…      rg-lablog-…        koreacentral  Microsoft.Insights/components
nsg-lablog-vm      rg-lablog-…        koreacentral  Microsoft.Network/networkSecurityGroups
vnet-lablog        rg-lablog-…        koreacentral  Microsoft.Network/virtualNetworks
pip-lablog-vm      rg-lablog-…        koreacentral  Microsoft.Network/publicIPAddresses""",
            read="`Type` 열에 워크스페이스 · Application Insights · NSG · VNet · 공용 IP 5가지가 모두 있으면 성공입니다.",
        ),
        scope="lab",
    )

    a3 = step(
        "a3",
        "Azure OpenAI 리소스와 모델 배포",
        "A3",
        "소요 약 2분",
        brief(
            what="일반적인 Azure OpenAI 와 같은 종류(`kind=OpenAI`)의 AOAI 리소스를 만들고, 모델 **gpt-4.1-mini** 를 `gpt41mini` 라는 **배포 이름**으로 배포합니다(Global Standard 방식).",
            why="앱과 probe 가 호출할 **대상**이 있어야 하고, R1/R2 에서 이 리소스의 로그 · 메트릭을 켭니다.",
            result="배포 상태가 `Succeeded`. 호출 주소는 `https://<AOAI 이름>.openai.azure.com` 입니다.",
            apply="내 환경은 **이미 있는 AOAI 를 그대로** 씁니다. 이 단계는 건너뛰고, 기존 리소스의 이름을 `AOAI` · 배포 이름을 `DEP` 에 넣으세요.",
            caution="이 실습의 코드는 `max_tokens` 를 씁니다. gpt-5 계열 같은 **추론 모델**은 `max_completion_tokens` 를 요구하므로 그 모델로 실습하려면 R3 호출부와 R7 probe 요청 본문(`\"max_tokens\":1`)을 바꿔야 합니다.",
        )
        + walk(
            """az cognitiveservices account create -g $RG -n $AOAI -l $LOC --kind OpenAI --sku S0 --custom-domain $AOAI --tags $TAGS --yes -o none
az cognitiveservices account deployment create -g $RG -n $AOAI --deployment-name $DEP \\
  --model-name gpt-4.1-mini --model-version 2025-04-14 --model-format OpenAI --sku-name GlobalStandard --sku-capacity 20 -o none
az cognitiveservices account deployment show -g $RG -n $AOAI --deployment-name $DEP --query properties.provisioningState -o tsv""",
            [
                (
                    "az cognitiveservices account create",
                    "AOAI 리소스 만들기",
                    """
                    * `--kind OpenAI` — Azure OpenAI 종류의 Cognitive Services 계정
                    * `--sku S0` — 표준 요금 등급
                    * `--custom-domain $AOAI` — **사용자 지정 도메인**. 호출 주소가 `https://$AOAI.openai.azure.com` 이 되며, 키 없이 **관리 ID(Entra) 로 호출하려면 반드시 필요**합니다(probe 가 이 방식을 씁니다).
                    * `--yes` — 약관 동의 질문에 자동으로 ‘예’
                    """,
                ),
                (
                    "az cognitiveservices account deployment create",
                    "모델 배포 만들기",
                    """
                    * `--deployment-name $DEP` — 앱이 호출할 **배포 이름**(`gpt41mini`)
                    * `--model-name gpt-4.1-mini --model-version 2025-04-14 --model-format OpenAI` — 어떤 모델의 어떤 버전인지
                    * `--sku-name GlobalStandard` — **Global Standard** 방식(여러 리전 용량을 쓰는 종량제). 요금은 쓴 토큰만큼입니다.
                    * `--sku-capacity 20` — 처리 한도 **20K TPM**(분당 2만 토큰)
                    """,
                ),
                (
                    "az cognitiveservices account deployment show",
                    "배포가 끝났는지 확인",
                    "`--query properties.provisioningState -o tsv` 로 **배포 상태 글자 하나**만 출력합니다. `Succeeded` 면 호출할 수 있습니다.",
                ),
            ],
            cap="AOAI 리소스 → 모델 배포 → 상태 확인",
            run="A3",
        )
        + out("Succeeded", read="`Succeeded` 가 나오면 끝입니다. `Creating` 이면 잠시 뒤 마지막 명령만 다시 실행하세요."),
        scope="lab",
    )

    a4 = step(
        "a4",
        "RHEL 9 VM 과 관리 ID 권한",
        "A4",
        "소요 약 3분",
        brief(
            what="앱 · probe · 에이전트가 돌 **VM** 을 만들고, VM 에 **시스템 할당 관리 ID** 를 켠 뒤 이 ID 에 AOAI 호출 역할(`Cognitive Services OpenAI User`)을 줍니다.",
            why="probe 가 **API 키 없이** VM 의 신원(관리 ID)으로 AOAI 를 호출하게 하려는 것이고, Azure Monitor Agent(B2)도 이 ID 를 씁니다.",
            result="`Succeeded` 상태의 VM 과 `SystemAssigned` 관리 ID.",
            apply="내 환경은 **이미 있는 VM** 이므로 VM 을 새로 만들지 마세요. **관리 ID 켜기(`az vm identity assign` — B2 에도 포함)** 와 이 단계의 **`az role assignment create`(AOAI 호출 역할 부여)** 만 하면 됩니다. 이 역할이 없으면 B4 의 probe 가 401/403 으로 실패합니다(역할이 반영되기까지 몇 분 걸릴 수 있음).",
        )
        + walk(
            """ssh-keygen -t rsa -b 3072 -N "" -f ./id_lab -C lablog-temp -q        # VM 생성에만 필요한 임시 키 (실습 후 삭제 — SSH 는 쓰지 않습니다)
az vm create -g $RG -n $VM -l $LOC --image RedHat:RHEL:9-lvm-gen2:latest --size Standard_B2s \\
  --admin-username azureuser --ssh-key-values ./id_lab.pub --vnet-name $VNET --subnet $SNET \\
  --public-ip-address $PIP --nsg "" --assign-identity '[system]' --os-disk-size-gb 64 --storage-sku StandardSSD_LRS --tags $TAGS -o none
VM_MI=$(az vm show -g $RG -n $VM --query identity.principalId -o tsv)
AOAI_ID=$(az cognitiveservices account show -g $RG -n $AOAI --query id -o tsv)
az role assignment create --assignee-object-id $VM_MI --assignee-principal-type ServicePrincipal \\
  --role "Cognitive Services OpenAI User" --scope $AOAI_ID -o none
echo "export AOAI_ID=$AOAI_ID" >> lablog.env
az vm show -g $RG -n $VM --query "{state:provisioningState, identity:identity.type}" -o table""",
            [
                (
                    "ssh-keygen",
                    "임시 SSH 키 만들기",
                    """
                    Linux VM 은 만들 때 **로그인 수단(SSH 키 또는 비밀번호)** 을 꼭 지정해야 해서 임시 키 한 쌍(`id_lab`, `id_lab.pub`)을 만듭니다. **이 실습은 SSH 로 접속하지 않습니다**(VM 에 인바운드 포트가 없고 모든 작업은 `vmrun` 으로 수행). 실습이 끝나면 D 단계에서 지웁니다.
                    * `-N ""` — 키에 암호를 걸지 않음
                    * `-f ./id_lab` — 키 파일 위치(공개 키는 `id_lab.pub`)
                    * `-C lablog-temp` — 키에 붙이는 이름표
                    * `-q` — 조용히
                    """,
                ),
                (
                    "az vm create",
                    "VM 만들기",
                    """
                    * `--image RedHat:RHEL:9-lvm-gen2:latest` — **RHEL 9**(이 가이드의 설치 명령은 RHEL 계열 Linux 기준)
                    * `--size Standard_B2s` — 2 vCPU · 4GB 의 저렴한 크기(시간당 약 $0.1)
                    * `--admin-username azureuser --ssh-key-values ./id_lab.pub` — 관리자 이름과 위 임시 키
                    * `--vnet-name $VNET --subnet $SNET --public-ip-address $PIP` — A2 에서 만든 네트워크와 공용 IP 에 연결
                    * `--nsg ""` — VM 의 네트워크 카드에 **별도 NSG 를 만들지 않음**(서브넷에 이미 NSG 가 연결되어 있음)
                    * `--assign-identity '[system]'` — **시스템 할당 관리 ID** 켜기(VM 이 자기 신원을 갖게 됩니다)
                    * `--os-disk-size-gb 64 --storage-sku StandardSSD_LRS` — 디스크 64GB, 표준 SSD
                    """,
                ),
                (
                    "VM_MI=",
                    "역할을 줄 대상과 범위를 알아내기",
                    """
                    * `VM_MI` — VM 관리 ID 의 **주체 ID(principalId)**. ‘누구에게 줄지’입니다.
                    * `AOAI_ID` — AOAI 리소스의 **리소스 ID**. ‘어디에 대한 권한인지’(범위)입니다.
                    """,
                ),
                (
                    "az role assignment create",
                    "AOAI 호출 역할 부여",
                    """
                    **관리 ID 에 AOAI 를 호출할 권한**을 줍니다. 역할 `Cognitive Services OpenAI User` 는 모델 호출(추론)만 허용하고 설정 변경은 못 합니다 — 필요한 만큼만 주는 **최소 권한**입니다.
                    * `--assignee-object-id $VM_MI --assignee-principal-type ServicePrincipal` — 대상은 VM 의 관리 ID
                    * `--scope $AOAI_ID` — **이 AOAI 리소스에만** 적용
                    """,
                ),
                (
                    "echo \"export AOAI_ID=",
                    "AOAI_ID 를 변수 파일에 저장",
                    "방금 얻은 `AOAI_ID` 를 `lablog.env` 에 덧붙입니다. 이후 단계(B1 진단 설정 · B5 메트릭 · B6 알림)가 이 값을 씁니다.",
                ),
                (
                    "az vm show -g $RG -n $VM --query",
                    "VM 상태 확인",
                    "VM 이 `Succeeded` 이고 관리 ID 종류가 `SystemAssigned` 인지 표로 확인합니다.",
                ),
            ],
            cap="임시 키 → VM → 관리 ID 역할 → 확인",
            run="A4",
        )
        + out(
            """State      Identity
---------  --------------
Succeeded  SystemAssigned""",
            read="`State` 가 `Succeeded`, `Identity` 가 `SystemAssigned` 이면 성공입니다.",
        ),
        scope="lab",
    )

    a5 = step(
        "a5",
        "VM 준비 — Python 3.12 · 패키지",
        "A5",
        "소요 약 3분 · 첫 `vmrun` 은 30~60초 걸립니다",
        brief(
            what="VM 에 **Python 3.12** 와 전용 가상환경을 만들고, 앱이 쓸 패키지(`openai` · `azure-monitor-opentelemetry`)를 설치합니다. 마지막으로 VM 이 AOAI 주소에 **닿는지** 확인합니다. (이 실습의 데모 앱 이름은 `report-agent` 로, 보고서 작성 앱을 흉내 낸 작은 프로그램입니다.)",
            why="RHEL 9 의 기본 `python3` 는 **3.9** 인데, R4(Application Insights 계측) 패키지 `azure-monitor-opentelemetry` 의 검증 버전(1.8.11)은 **Python 3.10 이상**이 필요합니다. `initscripts` 는 Azure Monitor Agent(R5) 문서가 요구하는 패키지입니다.",
            result="`Python 3.12.x` 와 패키지 목록, 그리고 AOAI 주소 확인 결과 `401`(키 없이 호출했으므로 정상).",
            apply="내 앱이 이미 Python 3.10+ 이면 설치는 필요 없습니다. 3.9 라면 3.10 이상으로 올리는 것을 권장합니다(3.9 에서 낮은 버전 패키지가 동작하는지는 검증하지 않았습니다).",
        )
        + walk(
            """vmrun AOAI_HOST=$AOAI_HOST DEP=$DEP <<'VMEOF'
set -e
dnf install -y python3.12 python3.12-pip initscripts >/tmp/dnf.log 2>&1 || { tail -20 /tmp/dnf.log; exit 1; }
python3.12 --version
install -d -m 0755 /opt/report-agent
python3.12 -m venv /opt/report-agent/venv
/opt/report-agent/venv/bin/pip install --quiet --upgrade pip
/opt/report-agent/venv/bin/pip install --quiet "openai>=3.0.0" "azure-monitor-opentelemetry>=1.8.10"
/opt/report-agent/venv/bin/pip list 2>/dev/null | grep -i -E "^(openai|azure-monitor-opentelemetry|opentelemetry-sdk|httpx2?) "
echo "== AOAI 엔드포인트 도달 확인 (키 없이 호출하므로 401 이 정상)"
curl -s -o /dev/null -w "%{http_code} dns=%{time_namelookup}s tcp=%{time_connect}s tls=%{time_appconnect}s\\n" --max-time 15 "https://$AOAI_HOST/openai/deployments/$DEP/chat/completions?api-version=2024-10-21" -X POST -H "Content-Type: application/json" -d '{}'
VMEOF""",
            [
                (
                    "vmrun AOAI_HOST",
                    "VM 안에서 실행하는 스크립트 열기",
                    """
                    `vmrun` 이 `<<'VMEOF'` 와 마지막 `VMEOF` **사이의 모든 줄을 VM 안에서** 실행합니다(A1 에서 만든 함수). `AOAI_HOST=… DEP=…` 는 이 두 값을 VM 안 스크립트에 넘기는 것이라, 아래 줄들에서 `$AOAI_HOST` · `$DEP` 로 쓸 수 있습니다.
                    따옴표가 있는 `'VMEOF'` 라서 **내 컴퓨터의 셸이 `$변수` 를 미리 바꾸지 않고**, 글자 그대로 VM 으로 보냅니다.
                    """,
                ),
                (
                    "set -e",
                    "오류가 나면 즉시 중단",
                    "`set -e` 는 **처리되지 않은 명령 실패에서 스크립트를 멈추게** 합니다(파이프라인 앞쪽 명령의 실패 등 모든 경우를 잡지는 못합니다). 앞 단계가 실패했는데 뒤 단계가 계속 진행되는 것을 대부분 막아 줍니다.",
                ),
                (
                    "dnf install",
                    "Python 3.12 · 보조 패키지 설치",
                    """
                    * `dnf install -y python3.12 python3.12-pip initscripts` — RHEL 의 패키지 관리자(`dnf`)로 Python 3.12, pip, `initscripts` 를 설치합니다.
                    * `>/tmp/dnf.log 2>&1` — 설치 출력은 로그 파일에 저장(화면을 길게 채우지 않음)
                    * `|| { tail -20 /tmp/dnf.log; exit 1; }` — **실패하면** 로그의 마지막 20줄을 보여 주고 중단
                    """,
                ),
                ("python3.12 --version", "설치 확인", "Python 3.12 가 설치되었는지 버전을 출력합니다."),
                (
                    "install -d -m 0755",
                    "앱 폴더와 가상환경 만들기",
                    """
                    * `install -d -m 0755 /opt/report-agent` — 앱을 둘 폴더를 **권한 755**(누구나 읽기 가능)로 만듭니다.
                    * `python3.12 -m venv /opt/report-agent/venv` — **가상환경**(앱 전용 Python 환경)을 만듭니다. 시스템 Python 을 건드리지 않고 앱에 필요한 패키지만 따로 설치하려는 것입니다.
                    """,
                ),
                (
                    "/opt/report-agent/venv/bin/pip install --quiet --upgrade pip",
                    "패키지 설치",
                    """
                    가상환경의 `pip` 으로 설치합니다(`--quiet` 는 진행 출력 생략).
                    * `pip` 자체를 최신으로 올립니다.
                    * `openai>=3.0.0` — AOAI 를 호출하는 SDK
                    * `azure-monitor-opentelemetry>=1.8.10` — R4. 앱의 외부 호출과 로그를 Application Insights 로 보내는 계측 패키지
                    """,
                ),
                ("/opt/report-agent/venv/bin/pip list", "설치된 버전 확인", "설치한 패키지의 버전만 골라 출력합니다(`grep`)."),
                (
                    "echo \"== AOAI",
                    "AOAI 주소에 닿는지 확인",
                    """
                    **키 없이** AOAI 주소로 빈 요청을 보내 봅니다. 키가 없으니 `401`(인증 필요)이 나오는 것이 정상이며, 이것은 **VM 이 AOAI 까지 네트워크로 닿는다**는 뜻입니다.
                    * `-s -o /dev/null` — 진행 표시 없이, 응답 본문은 버림
                    * `--max-time 15` — 최대 15초만 기다림
                    * `-X POST -H "Content-Type: application/json" -d '{}'` — **빈 JSON(`{}`)을 POST 로** 보냅니다. 인증 정보가 없어서 서버가 내용을 보기 전에 거절합니다.
                    * 주소의 구조 `https://<AOAI 이름>.openai.azure.com` / `openai/deployments/<배포 이름>` / `chat/completions` / `?api-version=2024-10-21` — **어느 배포의 채팅 API 를 어느 API 버전으로** 부르는지입니다.
                    * `-w "%{http_code} dns=… tcp=… tls=…"` — 응답 코드와 **DNS · TCP 연결 · TLS 핸드셰이크에 걸린 시간**을 출력(R7 probe 가 같은 방식으로 시간을 잽니다)

                    결과 해석: **`401`** 은 정상(서버에 닿았고 인증이 없어 거절됨), `000` 은 연결 자체가 안 됨(DNS · 방화벽 · 네트워크 확인), `404` 는 배포 이름이 없음, `403` 은 접근이 차단됨(네트워크 규칙 가능성)입니다.
                    """,
                ),
            ],
            cap="VM 에 Python 환경 만들기 + 패키지 설치 + AOAI 도달 확인",
            run="A5",
        )
        + out(
            """Python 3.12.x
azure-monitor-opentelemetry  1.8.11
httpx2                       2.x
openai                       3.x
opentelemetry-sdk            1.4x
== AOAI 엔드포인트 도달 확인 (키 없이 호출하므로 401 이 정상)
401 dns=0.019s tcp=0.021s tls=0.048s""",
            read="""
            - 앞쪽 `Python 3.12.x` 와 패키지 4줄은 설치 성공의 증거입니다(버전 숫자는 달라질 수 있음).
            - 마지막 줄의 **`401`** 이 정상입니다. `dns` · `tcp` · `tls` 는 각각 **초 단위 시간**이며 같은 리전에서는 0.0x 초 수준입니다.
            """,
        )
        + call("info", "run-command 한 번에 약 30초", "Azure VM 에이전트(`waagent`)가 스크립트를 받아 실행하는 시간입니다. 오래 걸리는 설치는 **한 번에 묶어서** 실행하세요."),
        scope="lab",
    )

    return section("a", "A · 실습 환경 만들기", "리소스 그룹부터 VM 까지 약 12~15분 — 내 환경에서는 보통 건너뜁니다", a1 + a2 + a3 + a4 + a5)
