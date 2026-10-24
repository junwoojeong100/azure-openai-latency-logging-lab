# -*- coding: utf-8 -*-
# 시작하기 전에 / A · 환경 만들기 (Foundry 에이전트 모니터링 가이드)
import json
import os
import re

from lib import *

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

SVG = """<div class="diagram"><svg viewBox="0 0 960 330" role="img" aria-label="구성도: 클라이언트가 Foundry 프로젝트의 프롬프트 에이전트와 호스티드 에이전트를 호출하면 플랫폼과 컨테이너가 Application Insights 로 트레이스를 보냅니다">
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
</svg></div>"""


def _row(cells, cls=None):
    tds = "".join(f"<td>{c}</td>" for c in cells)
    return f"<tr{(' class=' + chr(34) + cls + chr(34)) if cls else ''}>{tds}</tr>"


def compare_table():
    m = measured()
    rows = [
        ("모니터링 설정 코드·명령 줄 수<sup>①</sup>", f"<b>{OLD_TOTAL}줄</b> (R1·R3~R8)", f"<b>{NEW_TOTAL}줄</b>", f"<b>{NEW_TOTAL}줄</b> (같은 스크립트)"),
        ("앱 · 에이전트 코드 안의 텔레메트리 코드", f"<b>{OLD['R3'] + OLD['R4']}줄</b> (R3 {OLD['R3']} + R4 {OLD['R4']})", "<b>0줄</b> (코드가 없음)", f"<b>0줄</b> (main.py 전체가 {AGENT_LINES}줄)"),
        ("직접 만드는 모니터링용 Azure 리소스 종류<sup>②</sup>", f"<b>{len(OLD_RESOURCES)}종</b>", f"<b>{len(NEW_RESOURCES)}종</b>", f"<b>{len(NEW_RESOURCES)}종</b>"),
        ("관리하는 서버", "VM 1대 + Azure Monitor Agent + probe", "없음", "없음 (컨테이너는 Foundry 가 운영)"),
        ("설정에 걸린 시간", f"환경 약 15분 + 로그 켜기 약 16분<sup>③</sup>", f"<b>azd up {m['up_total_s'] // 60}분 {m['up_total_s'] % 60}초</b> (환경 + 에이전트 + 연결) + 알림 {m['alerts_s']}초", "같은 azd up 한 번"),
        ("첫 요청 로그가 조회되기까지", "AOAI 진단 로그 <b>20~26분</b> (설정 후 활성화 지연)", f"약 <b>{m['first_visible_s']}초</b><sup>④</sup>", f"약 <b>{m['first_visible_s']}초</b><sup>④</sup>"),
        ("요청 한 건을 잇는 키", "apim-request-id ↔ CorrelationId (앱이 응답 헤더를 로그에 남겨야 함)", "클라이언트가 보낸 <code>traceparent</code> 의 trace_id = <code>operation_Id</code>", "같음 (컨테이너 로그까지 같은 trace_id)"),
        ("지연을 가르는 기준", "앱이 잰 시간 vs AOAI 서버 시간", "실행 시간 − 모델 호출 시간 (런타임 오버헤드)", "실행 시간 − 모델 호출 시간 + <b>cold start 4단계 분해</b>"),
        ("새로 생기는 주의점", "—", f"드물게 실행이 모델 호출보다 약 {m['prompt_outlier_s']}초 길어짐 (이번 검증 {m['prompt_runs']}건 중 {m['prompt_outliers']}건 · 원인은 에이전트 런타임)", f"새 세션마다 cold start 약 {m['cold_startup_s']}초 · 컨테이너 시간 과금"),
    ]
    body = "".join(_row(r) for r in rows)
    return (
        '<table class="cmp"><thead><tr><th>항목</th><th>AOAI + VM 앱<br><small>원본 가이드</small></th><th>Foundry<br><small>프롬프트 에이전트</small></th><th>Foundry<br><small>호스티드 에이전트 (MAF)</small></th></tr></thead><tbody>'
        + body
        + "</tbody></table>"
    )


def build():
    m = measured()
    parts = []

    # ───────────────── 0. 시작하기 전에
    prereq = """<table class="nw"><thead><tr><th>항목</th><th>요구 사항</th><th>비고</th></tr></thead><tbody>
<tr><td>Azure CLI</td><td>2.60 이상 (2.86 으로 검증)</td><td><code>az version</code></td></tr>
<tr><td>Azure Developer CLI(azd)</td><td><b>1.37.1</b> 이상 + <code>microsoft.foundry</code> 확장 (azure.ai.agents 1.0.0-beta.22)</td><td>확장은 아직 <b>베타</b>라 버전이 자주 바뀝니다</td></tr>
<tr><td>Python</td><td>3.10 이상 (클라이언트 스크립트용 · 3.14 로 검증)</td><td>호스티드 에이전트는 Foundry 가 Python 3.13 으로 실행</td></tr>
<tr><td>셸</td><td>bash (macOS · Linux · WSL · Cloud Shell)</td><td>git · curl 필요</td></tr>
<tr><td>구독 권한</td><td>실습용 구독의 Owner (또는 Contributor + 역할 할당 권한)</td><td>호출자에게 Foundry User 역할을 부여합니다</td></tr>
<tr><td>모델 쿼터</td><td>koreacentral · Global Standard · gpt-5.4-mini 10 이상 (단위 1K TPM)</td><td>아래 확인 명령</td></tr>
<tr><td>비용(예상)</td><td>토큰 비용 소액 + Application Insights 수집 소액. 호스티드 에이전트는 <b>컨테이너 컴퓨트를 쓴 시간만큼</b> 과금(공식 가격 페이지), 프롬프트 에이전트는 추가 요금 없음</td><td>실습은 모두 합쳐 수십 분 규모</td></tr>
</tbody></table>"""
    body0 = (
        "<p>원본 가이드(AOAI + VM 앱)는 요청 단위 로그를 얻으려고 진단 설정 · VM 에이전트 · 앱 코드 · probe · 알림을 하나씩 켰습니다(R1~R8). "
        "이 가이드는 같은 목적을 <b>Foundry 프로젝트 + 프롬프트 에이전트 + MAF(Microsoft Agent Framework) 호스티드 에이전트</b>로 다시 만들어 보고, "
        "<b>새 리소스 그룹에서 실제로 실행해</b> 설정량과 얻는 데이터를 비교합니다.</p>"
        + SVG
        + '<div class="chips"><span class="chip"><b>A</b> azd up · 약 '
        + f"{(m['up_total_s'] + 59) // 60}분</span>"
        '<span class="chip">→</span><span class="chip"><b>B</b> 호출 · 약 3분</span><span class="chip">→</span>'
        '<span class="chip"><b>C</b> 확인·분석 · 약 5분</span><span class="chip">→</span>'
        '<span class="chip"><b>D</b> 알림 · 장애 재현 · 약 10분</span><span class="chip">→</span><span class="chip"><b>E</b> 정리 · 약 3분</span></div>'
        + "<h4>한눈에 비교 — 같은 모니터링, 설정은 얼마나 줄었나</h4>"
        + compare_table()
        + f'<p class="foot-note"><sup>①</sup> 빈 줄 · 주석을 뺀 줄 수. 원본은 <code>snippets/</code> 의 R1 {OLD["R1"]} · R3 {OLD["R3"]} · R4 {OLD["R4"]} · R5 {OLD["R5"]} · R6 {OLD["R6"]} · R7 {OLD["R7"]} · R8 {OLD["R8"]} 줄, '
        f'이 가이드는 <code>connect-appinsights.sh</code> {NEW["connect"]} + <code>alerts.sh</code> {NEW["alerts"]} 줄 (줄 수는 빌드할 때 파일에서 직접 센 값이며, <a href=\"#x4\">부록 D</a>에 상세). '
        f"<sup>②</sup> 목록은 <a href=\"#x4\">부록 D</a>. <sup>③</sup> 원본 가이드의 B1~B7 단계 표기(1+3+3+2+2+5분 등)를 더한 값이며, 위 줄 수는 VM · 네트워크 구간 로그를 포함합니다. "
        "Foundry 에이전트에는 VM 이 없어서 그 구간은 애초에 필요하지 않습니다. "
        "<sup>④</sup> 호출이 끝난 뒤 마지막 호출이 조회되기까지의 시간입니다. 연결을 만든 지 2분 이상 지나서 호출한 값이라, 연결 직후 곧바로 호출했을 때의 활성화 지연은 확인하지 못했습니다.</p>"
        + call(
            "warn",
            "읽을 때 주의 — 이 비교가 말하지 못하는 것",
            "<ul><li>원본 가이드는 <b>이미 있는 앱</b>(VM 위 앱 → AOAI)을 그대로 두고 로그를 더하는 방법입니다. 이 가이드는 <b>앱의 모델 호출 부분을 에이전트로 옮길 수 있을 때</b>의 이야기입니다. "
            "에이전트로 옮기지 못하는 앱은 원본 가이드의 방식이 그대로 필요합니다.</li>"
            "<li>엔드포인트만 AOAI → Foundry 로 바꿔서는 에이전트 트레이스가 생기지 않습니다. 에이전트(프롬프트 · 호스티드)를 거쳐 호출해야 합니다.</li>"
            "<li>수치는 <b>2026-10-24 Korea Central 한 환경에서 잰 값</b>입니다. 호스티드 에이전트는 <b>세션마다 cold start</b>(실측 약 "
            + f"{m['cold_startup_s']}초)가 있어 응답 시간 자체는 오히려 늘어날 수 있습니다 — 모니터링이 쉬워지는 것과 응답이 빨라지는 것은 별개입니다.</li>"
            "<li>프롬프트 · 응답 <b>본문이 트레이스에 기록</b>됩니다(원본 가이드는 메타데이터만 수집). 접근 제어는 <a href=\"#x3\">부록 C</a> 참고.</li></ul>",
        )
        + "<h4>준비물</h4>"
        + prereq
        + code(
            """az cognitiveservices usage list -l koreacentral --query "[?name.value=='OpenAI.GlobalStandard.gpt-5.4-mini'].{used:currentValue,limit:limit}" -o table""",
            cap="쿼터 확인 (limit − used 가 10 이상이면 됩니다)",
            run="A0",
        )
        + out(expected("A0") or "Used    Limit\n------  -------\n0.0     1000.0")
        + call(
            "warn",
            "안전 수칙",
            "<ul><li><b>실습용 구독</b>에서 실행하세요. 마지막 단계(E)에서 <code>azd down</code> 으로 리소스 그룹을 통째로 삭제합니다.</li>"
            "<li>이 가이드의 모든 명령은 <b>새 리소스 그룹</b>(<code>rg-&lt;azd 환경 이름&gt;</code>)만 만들고 기존 리소스는 건드리지 않습니다.</li>"
            "<li>키를 쓰지 않습니다 — 호출은 Entra ID(<code>az login</code>), 호스티드 에이전트는 Foundry 가 발급한 에이전트 ID 로 모델을 호출합니다.</li></ul>",
        )
    )
    parts.append(section("start", "시작하기 전에", "목표 · 구성 · 비교 · 준비물", body0))

    # ───────────────── A. 환경 만들기
    a1 = step(
        "a1",
        "도구 · 로그인",
        "A1",
        "소요 약 1분",
        "<p>azd 는 <code>az</code> 와 <b>로그인이 따로</b>입니다. 서로 다른 계정으로 로그인되어 있으면 azd 가 구독을 찾지 못합니다 "
        "(부록 B 의 첫 항목). <code>azd extension install microsoft.foundry</code> 한 줄이 에이전트 · 프로젝트 · 연결 확장을 함께 설치합니다.</p>"
        + code(
            """az version --query '"azure-cli"' -o tsv; azd version | head -1       # azd 1.37.1 이상
az login                                                              # 이미 로그인되어 있으면 생략 (Cloud Shell 은 불필요)
azd auth login                                                        # az 와 같은 계정을 쓰려면 대신: azd config set auth.useAzCliAuth true
azd extension install microsoft.foundry                               # Foundry 확장 묶음 (이미 있으면 건너뜀)
for e in application-insights log-analytics scheduled-query; do az extension add -n $e -y 2>/dev/null; done   # az monitor 확장 (설치 물음 방지)
export SUB="<구독 ID>"                                                # ← 실습용 구독 ID (az account list -o table)
az account set -s "$SUB\"""",
            cap="① 버전 확인 · 로그인 · 확장 설치",
            run="A1",
        )
        + out(expected("A1") or "azure-cli  2.86.0\nazd version 1.37.1 (commit …) (stable)")
    )

    a2 = step(
        "a2",
        "저장소 받기 → azd up (프로젝트 · 모델 · Application Insights 연결 · 에이전트 2개)",
        "A2",
        f"소요 약 {m['up_total_s'] // 60}~{m['up_total_s'] // 60 + 1}분 · 이 한 단계가 원본 가이드의 A · B1~B3 에 해당",
        "<p>이 저장소의 <code>foundry/</code> 폴더가 그대로 azd 프로젝트입니다. <b>azure.yaml 한 파일</b>이 Foundry 프로젝트 · 모델 배포 · 에이전트 2개를 정의하고, "
        "프로젝트가 만들어진 직후 <code>postprovision</code> 훅이 Application Insights 를 만들어 프로젝트에 연결합니다. 연결만 되어 있으면 두 에이전트의 트레이스가 코드 없이 쌓입니다.</p>"
        + code(
            """git clone --depth 1 https://github.com/junwoojeong100/azure-openai-latency-logging-lab.git
cd azure-openai-latency-logging-lab/foundry
azd env new fdmon-$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c5) --subscription "$SUB" --location koreacentral
azd up""",
            cap="한 번에: 저장소 → 환경 만들기 → azd up (azd 환경 이름이 리소스 그룹 이름 rg-<환경 이름> 이 됩니다)",
            run="A2",
        )
        + out(
            expected("A2")
            or f"SUCCESS: Your application was provisioned and deployed to Azure in {m['up_total_s'] // 60} minutes {m['up_total_s'] % 60} seconds.\n  Provisioning: …\n  Deploying:    …"
        )
        + call(
            "warn",
            "가끔 첫 시도가 실패합니다",
            "<p>검증 중 새 환경 3번 중 1번은 프로젝트 생성 단계에서 <code>FailedIdentityOperation … Conflict … pending delete operation</code> 으로 약 45초 만에 실패했고, "
            "<b>같은 <code>azd up</code> 을 다시 실행하면 성공</b>했습니다 (azd 는 이어서 진행합니다).</p>",
        )
        + details(
            "무엇이 만들어지나 — azure.yaml (모니터링과 관련된 부분은 hooks 한 블록뿐)",
            "<p><code>ai-project</code> 가 Foundry 리소스 · 프로젝트 · 모델 배포를, 나머지 두 서비스가 에이전트를 정의합니다. "
            "프롬프트 에이전트는 <b>모델 이름과 지시문뿐</b>이고 코드가 없습니다.</p>"
            + code(fd("azure.yaml"), cap="foundry/azure.yaml", lang="yaml")
            + code(fd("scripts/connect-appinsights.sh"), cap="foundry/scripts/connect-appinsights.sh — 연결 훅이 실행하는 스크립트 (아래 ‘모니터링 설정’ 전부)")
            + code(fd("src/report-maf-agent/main.py"), cap="foundry/src/report-maf-agent/main.py — 호스티드 에이전트 전체 (텔레메트리 코드 없음)", lang="python")
            + call(
                "info",
                "requirements.txt 를 쓰는 이유",
                "<p>호스티드 에이전트 코드 배포(<code>codeConfiguration</code>)는 Foundry 가 원격에서 의존성을 설치합니다. "
                "<code>pyproject.toml</code> 만 두면 <code>[tool.poetry] section not found</code> 로 실패해서(부록 B) <code>requirements.txt</code> 를 썼습니다. "
                "<code>uv.lock</code> 을 함께 두는 방법도 있습니다.</p>",
            ),
        )
    )

    a3 = step(
        "a3",
        "확인 — 환경 값 · 도우미 함수 · 만들어진 것",
        "A3",
        "소요 약 1분",
        "<p>이후 단계는 azd 환경 값을 파일로 저장해 두고 씁니다. 새 터미널에서는 <code>cd foundry &amp;&amp; set -a; . ./foundry.env; set +a</code> 로 다시 불러옵니다. "
        "<code>kq</code> 는 Application Insights 에 KQL 을 보내 결과를 표로 보여 주는 도우미입니다(포털에서는 Application Insights → Logs 에 같은 쿼리를 붙여 넣으면 됩니다).</p>"
        + code(
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
            cap="환경 값 저장 · kq 함수 · 리소스 확인 · 에이전트 상태",
            run="A3",
        )
        + out(expected("A3") or "Name  Type\n----  ----")
    )

    return parts[0] + section("a", "A · 환경 만들기", "azd up 한 번으로 프로젝트 · 모델 · 연결 · 에이전트", a1 + a2 + a3)
