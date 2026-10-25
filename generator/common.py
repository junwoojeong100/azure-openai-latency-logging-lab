# -*- coding: utf-8 -*-
# 두 가이드가 함께 쓰는 조각: 목차(진행 표시 포함) · 읽는 법 · 용어 사전 정의
from lib import *


def toc_html(entries):
    """entries = [("grp", 제목) | (id, 제목), …]  →  진행 표시 + 목차"""
    tools = (
        '<div class="tools"><div class="prog">진행 <b>0 / 0</b></div><div class="bar"><i></i></div>'
        '<button id="t-notes" type="button" aria-pressed="false">코드 해설 숨기기</button>'
        '<button id="t-open" type="button">접이식 모두 펼치기</button>'
        '<button id="t-reset" type="button">진행 초기화</button></div>'
    )
    body = ""
    for k, v in entries:
        body += f'<div class="grp">{esc(v)}</div>' if k == "grp" else f'<a href="#{k}">{esc(v)}</a>'
    return tools + body


def legend_html():
    """‘이 문서 읽는 법’ 카드 — 두 가이드 공통"""
    return (
        '<div class="legend">'
        '<div><b>코드 상자 (회색)</b><p>터미널에 <b>붙여 넣어 실행</b>하는 명령입니다. 오른쪽 위의 <span class="mini">복사</span> 버튼을 누르면 그대로 복사됩니다.</p></div>'
        '<div><b>코드 해설 (번호 + 아래 설명)</b><p>긴 코드는 <b>번호가 붙은 구간</b>으로 나뉘고, 구간 바로 아래에 <b>무슨 일을 하는지 · 왜 하는지 · 옵션의 뜻</b>이 있습니다. '
        '위쪽의 <span class="mini">전체 복사</span> 는 구간을 이어 붙인 <b>스크립트 전체</b>를 복사합니다.</p></div>'
        '<div><b>예상 결과 (초록 줄)</b><p>실제 환경에서 실행했을 때 나온 출력의 <b>예</b>입니다. 시각 · ID 같은 값은 다를 수 있고, <b>읽는 법</b>이 바로 아래에 붙어 있습니다.</p></div>'
        '<div><b>알림 상자</b><p><b>참고·팁</b>(초록/분홍), <b>주의</b>(주황), <b>위험</b>(빨강)으로 구분합니다. 주황·빨강은 읽고 넘어가세요.</p></div>'
        '<div><b>단계 이름표</b><p><span class="scope">실습 환경 준비</span> 실습에서만 필요한 준비 · '
        '<span class="scope apply">내 환경에도 그대로 적용</span> 운영 환경에 그대로 쓰는 설정 · <span class="scope check">확인 · 분석</span> 결과를 보는 단계 · <span class="scope check">선택 · 조건부 적용</span> 조건이 맞을 때만 하는 단계 · <span class="scope">정리 · 실습 리소스 전용</span> 끝난 뒤 지우는 단계</p></div>'
        '<div><b>줄 수 표기</b><p>코드 상자 머리의 ‘N줄’은 <b>빈 줄과 주석을 포함한</b> 줄 수이고, 본문의 ‘16줄 · 35줄’ 같은 숫자는 <b>빈 줄 · 주석을 뺀</b> 줄 수입니다.</p></div>'
        '<div><b>왼쪽 목차 위 도구</b><p>단계 끝의 <b>‘끝냈어요’ 체크</b>가 진행률로 표시됩니다(이 브라우저에만 저장). <b>코드 해설 숨기기</b>를 누르면 코드만 이어서 볼 수 있고, <b>접이식 모두 펼치기</b>로 숨은 설명을 한 번에 엽니다.</p></div>'
        "</div>"
    )


def terminal_rules(reload_cmd, extra=None):
    extras = [extra] if isinstance(extra, str) else (extra or [])
    ex = "".join(f"\n        {5 + i}. {t}" for i, t in enumerate(extras))
    return call(
        "tip",
        "터미널 사용 규칙 — 처음이라면 이 규칙만 기억하세요",
        f"""
        1. **한 터미널 창에서 위에서 아래로 차례로** 실행합니다. 앞 단계에서 정한 변수를 뒤 단계가 그대로 씁니다.
        2. 창을 닫았거나 새로 열었다면, 작업 폴더로 이동해서 변수를 다시 불러옵니다: `{reload_cmd}`
        3. `<구독 ID>`, `<알림 받을 이메일>` 처럼 **꺾쇠로 감싼 곳은 직접 값을 넣는 자리**입니다. 꺾쇠(`<` `>`)까지 지우고 값만 넣으세요. (단, 해설에 ‘코드가 대신 바꿉니다’ 라고 적힌 자리 — 예: `<LAW_ID>` · `<trace_id>` — 는 그대로 둡니다.)
        4. 줄 끝의 `\\` 는 ‘다음 줄에 이어서 한 명령’이라는 뜻입니다. 복사 버튼으로 붙여 넣으면 줄바꿈까지 그대로 들어가므로 신경 쓰지 않아도 됩니다.{ex}
        """,
    )


# 용어 사전 — (용어, 작은 글씨, 설명). 가이드마다 필요한 묶음만 골라 씁니다.
G = {
    "aoai": ("Azure OpenAI (AOAI)", None, "Azure 에서 OpenAI 모델(GPT 등)을 **API 로 호출**해 쓰는 서비스입니다. 앱은 `https://<이름>.openai.azure.com` 주소로 요청을 보냅니다."),
    "deployment": ("배포 (deployment)", "모델 배포", "모델(예: gpt-4.1-mini)을 **호출할 수 있는 이름**으로 만들어 둔 것입니다. 앱은 모델 이름이 아니라 ‘배포 이름’으로 호출하고, 배포마다 처리 한도(TPM)가 있습니다."),
    "tpm": ("TPM · 쿼터", "tokens per minute", "배포가 **1분에 처리할 수 있는 토큰 수의 한도**입니다(이 가이드의 단위는 1K = 1,000). 한도를 넘으면 429(너무 많은 요청) 오류가 납니다."),
    "token": ("토큰", None, "모델이 글자를 처리하는 단위입니다(한글 한 글자는 대략 1~2토큰). **처리 시간과 요금이 토큰 수에 비례**하므로 응답이 길수록 오래 걸립니다."),
    "status": ("HTTP 상태 코드", None, "**200** 성공 · **404** 대상 없음(배포 이름 오타 등) · **429** 한도 초과 · **499** 서버가 응답하는 도중 클라이언트(앱)가 연결을 끊음(AOAI 로그에서 쓰는 값) · **5xx** 서버 오류."),
    "timeout": ("timeout", "시간 제한", "앱(SDK)이 응답을 **기다려 주는 시간 제한**입니다. 연결 · 요청 전송 · 응답 읽기 단계마다 따로 정하며, 넘으면 앱이 스스로 포기합니다(이 가이드의 기록에서는 `client_timeout`)."),
    "p95": ("지연 · p95", "latency", "요청이 걸린 시간이 **지연**입니다. p95 는 ‘가장 느린 5% 를 뺀 나머지 중 최댓값’으로, 평균에 묻히는 **느린 쪽**을 보려고 씁니다."),
    "law": ("Log Analytics 워크스페이스", "workspace", "Azure 의 **로그 저장소**입니다. 여러 곳의 로그를 한곳에 모아 두고 KQL 로 조회합니다."),
    "kql": ("KQL", "Kusto Query Language", "Log Analytics 워크스페이스 · Application Insights 를 조회하는 **질의 언어**입니다. `테이블 | 단계 | 단계` 처럼 **파이프(`|`)로 단계를 이어서** 위에서 아래로 읽습니다. 자주 쓰는 단계: **`where`** 거르기 · **`extend`** 계산한 열 추가 · **`project`** 열 고르기 · **`summarize … by`** 묶어서 집계 · **`join`** 키로 두 표 잇기 · **`union`** 표 합치기 · **`top`** 상위 N건. **p50 · p95** 는 ‘절반 · 95% 의 호출이 이 시간 이하’라는 뜻이라, p95 는 느린 쪽 5% 의 경계입니다."),
    "appi": ("Application Insights", "앱 모니터링", "앱의 **외부 호출 기록과 로그**를 모아 주는 서비스입니다. ‘워크스페이스 기반’으로 만들면 데이터가 위 워크스페이스의 `AppDependencies`(외부 호출) · `AppTraces`(앱 로그) 같은 테이블에 저장됩니다."),
    "diag": ("진단 설정", "Diagnostic settings", "Azure 리소스(예: AOAI)가 **스스로 만드는 로그 · 메트릭을 워크스페이스로 보내도록 켜는 설정**입니다. 앱 코드는 바뀌지 않습니다."),
    "metric": ("메트릭 vs 로그", None, "**메트릭**은 1분 단위로 집계된 숫자(가볍고 알림에 빠름), **로그**는 요청 한 건마다의 상세 기록입니다. 이 가이드는 둘 다 모읍니다."),
    "otel": ("OpenTelemetry (OTel)", None, "앱의 외부 호출과 로그를 **표준 방식으로 수집하는 오픈소스 계측 도구**입니다. `azure-monitor-opentelemetry` 가 이를 Application Insights 로 보냅니다."),
    "ama": ("Azure Monitor Agent (AMA) · 수집 규칙 (DCR)", "Data Collection Rule", "**VM 안에 설치되어** 성능 카운터 · syslog 를 Azure 로 보내는 프로그램(AMA)과, ‘무엇을 어디로 보낼지’ 적어 둔 규칙(DCR)입니다."),
    "mi": ("관리 ID", "Managed Identity", "VM 같은 Azure 리소스에 **자동으로 붙는 신원**입니다. 키나 비밀번호 없이 ‘역할’을 받아 다른 서비스를 호출합니다."),
    "rbac": ("역할 (RBAC)", "Role-based access control", "**누가 무엇을 할 수 있는지** 정하는 Azure 권한입니다. 예: `Cognitive Services OpenAI User` = AOAI 를 호출할 수 있음."),
    "systemd": ("systemd · journald", None, "Linux 에서 **서비스와 타이머를 관리**하는 프로그램이 systemd 입니다(서비스 파일의 `[Unit]` · `[Service]` · `[Install]` 은 구역 이름). 서비스가 출력한 로그를 모아 두는 곳이 journald 이고 `journalctl -u 서비스이름` 으로 봅니다. 타이머(`.timer`)는 같은 이름의 `.service` 를 정해진 시각에 실행합니다."),
    "syslog": ("syslog · cron", None, "**syslog** 는 Linux 가 로그를 남기는 표준 통로(채널 이름 = facility)이고, **cron** 은 정해진 시각에 작업을 실행하는 도구입니다. 이 가이드는 cron 의 실행 기록과 probe 의 기록(`local5`)을 syslog 로 수집합니다."),
    "dns": ("DNS · TCP · TLS", None, "**DNS** 는 이름(`xxx.openai.azure.com`)을 IP 주소로 바꾸는 조회, **TCP** 는 두 컴퓨터가 연결을 맺는 단계, **TLS** 는 그 연결을 암호화하는 협상입니다. 요청 한 건은 보통 DNS → TCP 연결 → TLS 협상 → 요청 전송 → 서버 처리 → 응답 순서로 진행되어, 느린 구간을 이 단계별로 나눠 볼 수 있습니다."),
    "nat": ("NAT · 방화벽 · 프록시", None, "**방화벽**은 허용된 접속만 통과시키는 장치, **프록시**는 접속을 대신 전달해 주는 중간 서버, **NAT** 는 사설 IP 의 VM 이 인터넷으로 나갈 때 공용 IP 로 주소를 바꿔 주는 것입니다. 이런 장치가 VM 과 AOAI 사이에 있으면 지연이 생길 수 있어 B7 에서 따로 봅니다."),
    "sdk": ("SDK · 스트리밍", None, "**SDK** 는 앱이 AOAI 를 부르게 해 주는 라이브러리(이 가이드는 Python `openai` 패키지)입니다. **스트리밍**은 응답을 다 만든 뒤 한 번에 받는 대신 **생성되는 대로 조각으로** 받는 방식입니다. 이 실습은 한 번에 받는 방식이며, 스트리밍이면 `total_ms` 의 의미가 달라집니다."),
    "probe": ("합성 probe", "synthetic probe", "사용자 요청과 상관없이 **1분마다 같은 작은 호출**을 보내 구간별 시간을 재는 점검 스크립트입니다. 평소 기준선이 생겨 ‘지금이 느린 건지’ 판단할 수 있습니다."),
    "net": ("Connection Monitor · flow log", "Network Watcher", "VM 에서 목적지(AOAI 443 포트)까지 **연결 시간 · 실패율을 주기적으로 재는 기능**, 그리고 VNet 안 **트래픽 흐름을 기록하는 기능**입니다."),
    "reqid": ("요청 ID", "apim-request-id", "요청 **한 건을 가리키는 값**입니다. AOAI 응답 헤더 `apim-request-id` 는 AOAI 진단 로그의 `CorrelationId` 와 **같아서**, 앱 기록과 AOAI 기록을 한 건씩 짝지을 수 있습니다."),
    "alert": ("알림 규칙 · 액션 그룹", None, "조건(예: 499 가 1건 이상)을 **계속 감시하다가** 충족하면 알려 주는 규칙과, 알릴 곳(이메일 등)을 모아 둔 **수신 그룹(= 액션 그룹)** 입니다."),
    "ingest": ("수집 지연", "ingestion latency", "로그가 생긴 뒤 워크스페이스에서 **조회되기까지 걸리는 시간**입니다. 실측: 앱 약 10초 · VM 약 2분(수집 규칙을 연결한 뒤 처음 나타나기까지는 5~10분) · AOAI 로그 평균 약 2분(처음 켠 뒤 20~26분은 비어 있음) · 메트릭 7~10분."),
    "rg": ("구독 · 리소스 그룹", "subscription · resource group", "**구독**은 요금과 권한의 기본 단위, **리소스 그룹**은 리소스를 담는 폴더입니다. 그룹을 지우면 안의 리소스가 모두 지워져 정리가 쉽습니다."),
    "rnum": ("R1 ~ R8", None, "이 가이드가 따르는 **로그 수집 항목 번호**입니다: R1 AOAI 진단 로그 · R2 AOAI 메트릭 · R3 앱 호출 로그 · R4 Application Insights · R5 모니터링 에이전트(AMA) · R6 네트워크 경로 · R7 합성 probe · R8 알림."),
    # Foundry 가이드
    "foundry": ("Microsoft Foundry", None, "AI 앱 · **에이전트 · 모델 배포를 한곳에서 만들고 운영하는 Azure 서비스**입니다. 모델을 직접 호출하는 대신 ‘에이전트’를 통해 호출할 수 있습니다."),
    "project": ("Foundry 프로젝트", "project", "Foundry 안에서 **에이전트 · 모델 배포 · 연결(예: Application Insights)을 묶어 두는 작업 공간**입니다. 호출 주소(엔드포인트)도 프로젝트마다 하나입니다."),
    "model": ("Foundry Models · 모델 배포", None, "Foundry 에서 모델(여기서는 gpt-5.4-mini)을 배포한 것입니다. 기존 AOAI 의 ‘배포’와 같은 개념이며, 호출 한도(쿼터)도 배포 단위입니다."),
    "agent": ("에이전트", "agent", "**모델 + 지시문(+ 도구)을 하나로 묶어 이름을 붙인 것**입니다. 앱은 에이전트 이름으로 호출하고, 에이전트가 모델을 부릅니다. 이 가이드는 ‘코드가 없는’ **프롬프트 에이전트**와 ‘코드로 만든’ **호스티드 에이전트** 두 가지를 씁니다."),
    "hosted": ("호스티드 에이전트 · MAF", "Hosted agent · Microsoft Agent Framework", "내가 쓴 Python 코드(MAF = Microsoft Agent Framework)를 **Foundry 가 컨테이너로 실행**해 주는 에이전트입니다. 코드로 도구·흐름을 직접 짤 수 있는 대신, 새 대화마다 컨테이너를 띄우는 **cold start** 가 있습니다."),
    "coldstart": ("cold start · warm", None, "컨테이너를 **새로 띄우느라 첫 호출이 느린 것**이 cold start, 이미 떠 있어 빠른 호출이 warm 입니다. 호스티드 에이전트는 **새 대화(세션)마다** cold start 가 일어납니다. 이번 실측: 시작 지연이 약 7초이고, 그 호출의 총 응답 시간은 약 8~12초였습니다."),
    "azd": ("azd (Azure Developer CLI)", None, "`azure.yaml` 한 파일에 적은 대로 **프로젝트 · 모델 · 에이전트를 만들고(`azd up`) 지우는(`azd down`)** 명령줄 도구입니다. `az` 와 로그인이 따로입니다."),
    "trace": ("트레이스 · 스팬", "trace · span", "요청 한 건이 지나간 **전체 경로가 트레이스**, 그 경로의 **한 구간(예: 에이전트 실행, 모델 호출)이 스팬**입니다. 구간마다 시작 시각과 걸린 시간이 기록됩니다."),
    "appi_f": ("Application Insights · Log Analytics", "트레이스 저장소", "**Application Insights** 는 앱 · 에이전트가 남긴 기록을 보여 주는 **모니터링 서비스**이고, **Log Analytics 워크스페이스**는 그 기록이 실제로 **저장되는 곳**입니다(A2 의 스크립트가 둘을 만들어 연결합니다). 기록은 `requests`(받은 요청) · `dependencies`(다른 곳에 시킨 일) · `traces`(로그) · `exceptions`(예외) 테이블에 쌓이고 KQL 로 조회합니다. 프로젝트에 연결만 되어 있으면 두 에이전트의 서버 쪽 트레이스가 코드 없이 쌓입니다."),
    "status_f": ("HTTP 상태 코드", None, "**200** 성공 · **400** 잘못된 요청(요청 옵션이 허용되지 않을 때 등) · **404** 대상 없음(배포 이름 오타 등) · **429** 한도 초과 · **5xx** 서버 오류. 이 가이드의 에이전트 응답은 **HTTP 200 이어도 `status` 가 `failed`** 일 수 있습니다(D2)."),
    "timeout_f": ("timeout", "시간 제한", "앱(SDK)이 응답을 **기다려 주는 시간 제한**입니다. 넘으면 앱이 스스로 포기하고 예외가 납니다 — 앱 최소 기록(C7)에서 잡아야 하는 경우입니다."),
    "ingest_f": ("수집 지연", "ingestion latency", "트레이스가 생긴 뒤 **조회되기까지 걸리는 시간**입니다. 이 가이드 실측: 마지막 호출이 약 11초 뒤에 보였고, 텔레메트리 799건 중 중앙값 약 6초 · 96% 가 1분 안 · 최대 약 2분 40초입니다(C1)."),
    "alert_f": ("알림 규칙 · 액션 그룹", None, "조건(예: 실패한 실행이 1건 이상)을 **주기적으로 확인하다가** 충족되면 알려 주는 규칙과, 알릴 곳(이메일 등)을 모아 둔 수신 그룹(액션 그룹)입니다(D1)."),
    "appmin": ("앱 최소 기록", None, "앱이 에이전트를 **부를 때마다 직접 남기는 로그 한 줄**(trace_id · 클라이언트가 잰 시간 · 상태/오류 · 재시도)입니다. 서버 트레이스에 없는 구간(앱 ↔ Foundry)을 메웁니다. 코드는 약 10~15줄로 예상합니다(이번에 검증하지 않음). C7 에서 설명합니다."),
    "side": ("서버 쪽 · 앱 쪽", None, "이 가이드에서 **‘서버 쪽’은 Foundry(에이전트 + 모델)**, **‘앱 쪽’은 내 코드와 그 코드가 도는 컴퓨터(VM 등)** 입니다. ‘서버 트레이스’는 Foundry 가 남기는 기록을 뜻합니다."),
    "reqdep": ("requests · dependencies · traces · exceptions", None, "Application Insights 의 네 테이블입니다. **requests = 서비스가 받은 일**, **dependencies = 서비스가 다른 곳에 시킨 일**(외부 호출), **traces = 로그 메시지**, **exceptions = 예외**. 같은 에이전트 실행이 두 테이블에 함께 남기도 합니다(C2)."),
    "respapi": ("Responses API · Chat Completions API", None, "OpenAI 모델을 부르는 두 가지 **호출 규격**입니다. 기존 AOAI 앱은 보통 Chat Completions(`chat.completions.create`)를, 에이전트는 Responses(`responses.create`)를 씁니다."),
    "otel_f": ("OpenTelemetry (OTel)", None, "서비스의 호출과 로그를 **표준 방식으로 수집하는 오픈소스 계측 규격 · 도구**입니다. **trace · span · `traceparent`**(요청 한 건의 이름표를 헤더로 전달) · **`gen_ai.*`**(AI 호출의 속성 이름) 같은 이름이 이 규격에서 나왔습니다. 호스티드 에이전트 컨테이너는 시작할 때 이것을 스스로 설정해 트레이스를 Application Insights 로 보냅니다."),
    "telemetry": ("텔레메트리", "telemetry", "서비스나 앱이 **스스로 남기는 측정 기록**(요청 · 걸린 시간 · 오류 · 로그)의 총칭입니다. 이 가이드에서 ‘텔레메트리 코드’는 그런 기록을 남기려고 **앱이나 에이전트에 넣는 코드**를 말합니다."),
    "prov": ("프로비저닝 · 배포", "provision · deploy", "**프로비저닝**은 Azure 리소스를 실제로 만드는 일, **배포**는 그 위에 에이전트를 올리는 일입니다. `azd up` = 프로비저닝 + 배포를 한 번에 합니다."),
    "rnum_f": ("R1 ~ R8", None, "짝 가이드(가이드 1)가 따르는 **로그 수집 항목 번호**입니다: R1 AOAI 진단 로그 · R2 메트릭 · R3 앱 호출 로그 · R4 Application Insights · R5 모니터링 에이전트(AMA) · R6 네트워크 경로 · R7 합성 probe · R8 알림. 이 가이드와의 대응은 E1 표에 있습니다."),
    "rolename": ("역할 이름 vs 역할", None, "**역할 이름(`cloud_RoleName`)** 은 기록을 보낸 쪽의 이름표입니다(예: `responsesapi`). **역할(RBAC)** 은 권한입니다(예: Foundry User). 말은 비슷하지만 전혀 다른 것입니다."),
    "utc": ("UTC · KST", None, "로그의 시각은 **UTC**(협정 세계시)로 저장 · 표시됩니다. 한국 시각(KST) = UTC + 9시간이라 **분은 같고 시(時)만 9시간 차이**입니다(예: UTC 13:26 = KST 22:26)."),
    "sampling": ("샘플링", "sampling", "호출을 **전부 기록하지 않고 일부만 기록**하는 것입니다. 호출이 많을 때 비용을 줄이는 기능인데, 진단 기간에는 빠지는 호출이 없도록 끕니다(R4 의 `always_on`)."),
    "sku": ("SKU · Global Standard", None, "**SKU** 는 리소스의 ‘등급 · 요금 방식’입니다. 모델 배포의 **Global Standard** 는 여러 리전의 용량을 함께 쓰는 **종량제**(쓴 토큰만큼 과금) 방식입니다."),
    "apiver": ("api-version", None, "AOAI 호출 주소 끝에 붙이는 **API 버전**(예: `api-version=2024-10-21`)입니다. 앱 · probe 가 같은 버전으로 호출해야 같은 동작을 합니다."),
    "entra_a": ("Microsoft Entra ID", None, "Azure 의 **계정 · 신원 서비스**(예전 이름 Azure AD)입니다. 키 대신 ‘관리 ID’ 같은 신원으로 인증하는 방식이 여기에 해당합니다."),
    "facility": ("syslog facility", None, "syslog 로그가 속한 **채널 이름**입니다(예: `cron` = cron 작업, `local0`~`local7` = 사용자 정의용). 이 가이드는 probe 의 기록에 `local5` 를 쓰고, 수집 규칙이 `cron` 과 `local5` 만 가져옵니다."),
    "rtt": ("RTT", "round-trip time", "신호가 **갔다가 돌아오는 왕복 시간**입니다. 같은 리전의 TCP 연결은 보통 몇 ms 입니다."),
    "fqdn": ("FQDN", "fully qualified domain name", "**전체 도메인 이름**(예: `<이름>.openai.azure.com`)입니다. 방화벽 규칙이 IP 대신 이 이름으로 허용 · 차단합니다."),
    "snat": ("SNAT 포트", None, "사설 IP 의 VM 이 인터넷으로 나갈 때 **공용 IP 의 포트를 빌려 쓰는 것**(주소 변환)입니다. 빌려 쓸 포트가 **고갈되면 새 연결이 느려지거나 실패**합니다."),
    "nva": ("NVA · UDR", None, "**NVA** 는 가상 네트워크 안의 **타사 네트워크 장비**(방화벽 가상 어플라이언스 등), **UDR** 은 트래픽을 그 장비로 보내도록 정하는 **사용자 정의 경로**입니다."),
    "support": ("Support Case", None, "Azure 지원팀에 보내는 **지원 요청**입니다(포털 → 도움말 + 지원). AOAI 쪽 문제가 의심될 때 이 가이드가 모은 **요청 ID · 시각 · 메트릭**을 첨부합니다."),
    "reasoning": ("추론 모델", "reasoning model", "답을 내기 전에 **내부 추론 과정을 거치는 모델**(예: gpt-5 계열)입니다. `max_tokens` 대신 `max_completion_tokens` 를 요구하는 등 호출 옵션이 다릅니다(A3 의 경고)."),
    "avail": ("가용성 테스트", "availability test", "Application Insights 가 **외부에서 주기적으로 URL 을 호출해 살아 있는지 보는 기능**입니다. 내 환경에 이미 있을 수 있습니다(부록 E 의 `avail_tests`)."),
    "region": ("리전 · 엔드포인트", None, "**리전**은 리소스가 있는 Azure 의 위치(예: koreacentral = 한국 중부)이고, **엔드포인트**는 호출 주소(`https://<이름>.openai.azure.com`)입니다."),
    "traceid": ("trace_id · traceparent · operation_Id", None, "**trace_id** 는 요청 한 건의 이름표입니다. 앱이 `traceparent` 라는 **요청 헤더**에 trace_id 를 실어 보내면, Application Insights 에서는 `operation_Id` 로 조회됩니다. 앱 기록과 서버 기록을 **같은 값으로** 짝지을 수 있습니다."),
    "spans": ("invoke_agent · chat 스팬", None, "플랫폼이 남기는 두 가지 스팬입니다. **invoke_agent** = 에이전트 실행 전체, **chat** = 그 안의 모델 호출. `invoke_agent − chat` 이 에이전트 런타임이 쓴 시간(오버헤드)입니다."),
    "entra": ("Entra ID · Foundry User 역할", None, "이 가이드는 API 키 없이 `az login` 한 **내 계정(Entra ID)** 으로 호출합니다. 호출하려면 프로젝트에 **Foundry User** 역할이 필요합니다(`azd up` 중에 자동으로 부여)."),
}


def gloss_group(keys):
    return gloss([G[k] for k in keys])
