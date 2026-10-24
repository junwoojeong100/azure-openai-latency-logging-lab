# -*- coding: utf-8 -*-
# D · 알림 · 장애 재현 / E · 정리와 판단 / 부록 (Foundry 에이전트 모니터링 가이드)
from lib import *
import foundry_a
from foundry_a import OLD, OLD_TOTAL, NEW, NEW_TOTAL, OLD_RESOURCES, NEW_RESOURCES, AGENT_LINES, CLIENT_LINES, YAML_LINES, PCT
from foundry_b import exp, kqb


def build():
    m = foundry_a.measured()

    # ───────────────── D. 알림 · 장애 재현
    d1 = step(
        "d1",
        "알림 2개 만들기 — 느린 실행 · 실패한 실행",
        "D1",
        f"소요 약 {m['alerts_s']}초 · 원본 가이드의 R8 에 해당",
        "<p>Application Insights 를 대상으로 하는 <b>로그 알림 2개</b>와 수신 그룹을 만듭니다. "
        "느린 실행은 <b>cold start 시간을 더한 총 시간이 8초를 넘는 실행</b>(프롬프트 · 호스티드 공통), 실패한 실행은 <b>실패한 GenAI 스팬</b>입니다. "
        "텔레메트리가 늦게 도착해도 놓치지 않도록 평가 창(15분)을 평가 주기(5분)보다 길게 잡았습니다 — 같은 사건이 최대 3번 평가됩니다.</p>"
        + code(fd("scripts/alerts.sh"), cap="foundry/scripts/alerts.sh", lang="bash")
        + code(
            """MAIL="<알림 받을 이메일>" sh scripts/alerts.sh
az monitor scheduled-query list -g "$AZURE_RESOURCE_GROUP" --query "[].{name:name, every:evaluationFrequency, window:windowSize, severity:severity}" -o table""",
            cap="알림 만들기 (수신 메일은 MAIL)",
            run="D1",
        )
        + exp("D1")
    )

    d2 = step(
        "d2",
        "장애 만들기 — 느린 실행 · 실패한 실행",
        "D2",
        "소요 약 4분",
        "<p>알림이 울리는지 보려고 일부러 두 가지를 만듭니다. ① 호출마다 새 세션을 만들어 <b>cold start 로 느린 실행</b>, "
        "② 호스티드 에이전트의 모델 배포 이름에 <b>오타</b>를 내고 새 버전을 배포해 <b>실패하는 실행</b>(원본 가이드의 “없는 배포 이름 → 404” 와 같은 실수).</p>"
        + code(
            """python invoke_agents.py report-maf-agent 3 short new | tee -a calls.jsonl                  # ① 느린 실행 (cold start)
azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME no-such-deployment                                  # ② 오타 난 배포 이름으로
azd deploy report-maf-agent                                                                    #    새 버전 배포 (약 1분)
python invoke_agents.py report-maf-agent 3 short new | tee -a calls.jsonl                  #    호출 → 실패""",
            cap="느린 호출 3번 → 오타 난 버전 배포 → 실패하는 호출 3번",
            run="D2",
        )
        + exp("D2")
        + call(
            "warn",
            "실패해도 HTTP 는 200 입니다",
            "<p>호스티드 에이전트가 모델 호출에 실패해도 응답은 <b>HTTP 200 + <code>status: failed</code></b> 이고 오류 메시지는 <code>An internal server error occurred.</code> 한 줄뿐입니다. "
            "진짜 원인(<code>DeploymentNotFound</code>)은 서버 트레이스에서만 보입니다 — 클라이언트 로그만으로는 알 수 없습니다.</p>",
        )
    )

    d3 = step(
        "d3",
        "알림 확인 · 실패 원인 보기",
        "D3",
        "알림은 보통 5~10분 안에 울립니다 (최대 약 20분 대기)",
        "<p>알림이 울릴 때까지 기다린 뒤, 알림이 가리키는 실패를 트레이스에서 찾아봅니다. 실패한 실행은 <b>요청(<code>requests</code>) 스팬이 아니라 "
        "<code>dependencies</code> · <code>exceptions</code> 에 남습니다</b> — 아래 두 번째 쿼리가 그 점을 보여 줍니다.</p>"
        + code(
            """SUB_ID=$(az account show --query id -o tsv)
for i in $(seq 1 40); do
  az rest --method get --url "https://management.azure.com/subscriptions/$SUB_ID/providers/Microsoft.AlertsManagement/alerts?api-version=2019-05-05-preview&targetResourceGroup=$AZURE_RESOURCE_GROUP" \\
    --query "value[].{rule:properties.essentials.alertRule, state:properties.essentials.monitorCondition, severity:properties.essentials.severity, fired:properties.essentials.startDateTime}" -o tsv | sed 's#.*/scheduledqueryrules/##' > alerts.txt
  [ "$(grep -c Fired alerts.txt)" -ge 2 ] && break; sleep 30
done
cat alerts.txt""",
            cap="① 발화한 알림 (30초 간격으로 확인)",
            run="D3",
        )
        + exp("D3a")
        + kqb("failed_runs", "② 실패한 실행 — 실패한 GenAI 스팬 + 예외 (최근 1시간)", "D3")
        + exp("D3b")
        + kqb("request_success_flag", "③ 같은 시간 requests 의 success — 실패한 버전(오타 난 배포 이름)도 success_false 가 0", "D3")
        + exp("D3c")
        + kqb("container_logs", "④ 호스티드 컨테이너 로그 — 경고 이상", "D3")
        + exp("D3d")
        + call(
            "info",
            "알림 · 실패 쿼리를 이렇게 짠 이유",
            "<ul><li>실패 알림은 <code>requests</code> 의 <code>success</code> 를 보면 <b>놓칩니다</b>(③). <code>dependencies</code> 의 <code>success == false</code> 를 봅니다.</li>"
            "<li>실행이 시작되기 전에 거절된 호출(예: 없는 에이전트 · 없는 모델 배포로 만든 프롬프트 에이전트의 404)은 <b>트레이스에 남지 않습니다</b> — 이번 검증에서 오타 난 모델로 만든 프롬프트 에이전트를 2번 불렀을 때 모든 테이블이 비어 있었습니다. "
            "이런 실패는 클라이언트 쪽 로그(<code>invoke_agents.py</code> 의 status · error)로 잡아야 합니다.</li></ul>",
        )
    )

    d4 = step(
        "d4",
        "복구 · 알림 끄기",
        "D4",
        "소요 약 2분",
        "<p>배포 이름을 되돌려 새 버전으로 복구하고, 실습이 끝났으면 알림을 끕니다(켜 두면 평가마다 메일이 올 수 있습니다).</p>"
        + code(
            """azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME gpt-5.4-mini
azd deploy report-maf-agent
python invoke_agents.py report-maf-agent 1 short new
for a in agent-run-slow agent-run-failed; do az monitor scheduled-query update -g "$AZURE_RESOURCE_GROUP" -n $a --disabled true --query "{name:name, enabled:enabled}" -o tsv; done""",
            cap="복구(새 버전) → 정상 호출 확인 → 알림 끄기",
            run="D4",
        )
        + exp("D4")
    )
    sec_d = section("d", "D · 알림 · 장애 재현", "원본 가이드의 R8 과 같은 알림이 에이전트에서도 울리는지 확인합니다", d1 + d2 + d3 + d4)

    # ───────────────── E. 정리와 판단
    map_rows = [
        ("R1 AOAI 진단 설정", f"{OLD['R1']}줄", "<b>불필요</b> — 요청 단위 지연 · 토큰 · 상태는 에이전트 트레이스가 대신(C2~C5). 서비스 쪽 로그가 더 필요하면 Foundry 리소스에 같은 진단 설정을 추가(범주 <code>RequestResponse</code> 등 확인 · 이 가이드는 미적용)"),
        ("R2 AOAI 메트릭", "—", "<b>자동</b> — 설정 없이 Foundry 리소스에 쌓임 (C5)"),
        ("R3 앱 호출 로그", f"{OLD['R3']}줄", f"<b>불필요</b> — 플랫폼 스팬이 대신. 클라이언트가 잰 시간이 필요하면 <code>invoke_agents.py</code>({CLIENT_LINES}줄, 선택)"),
        ("R4 Application Insights(OTel)", f"{OLD['R4']}줄", f"<b>연결 1회</b> — <code>connect-appinsights.sh</code> {NEW['connect']}줄. 에이전트 코드에는 OTel 코드 없음"),
        ("R5 VM 에이전트 · DCR", f"{OLD['R5']}줄", "<b>해당 없음</b> — VM 이 없음"),
        ("R6 네트워크 경로 로그", f"{OLD['R6']}줄", "<b>해당 없음</b> — 모델까지의 경로는 Foundry 내부. 클라이언트 → Foundry 구간만 클라이언트에서 측정"),
        ("R7 합성 probe", f"{OLD['R7']}줄", "<b>선택</b> — cold start · idle 지연은 트레이스로 직접 보임(C3). 정기 점검이 필요하면 <code>invoke_agents.py</code> 를 스케줄러로 호출"),
        ("R8 알림", f"{OLD['R8']}줄", f"<code>alerts.sh</code> {NEW['alerts']}줄 (D1). Foundry 포털의 Alerts(프리뷰)도 있으나 이 가이드에서 확인하지 못함"),
    ]
    mt = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in map_rows)
    e1 = step(
        "e1",
        "R1~R8 은 어디로 갔나 · 언제 어느 쪽을 쓰나",
        "E1",
        f"설정 코드 {OLD_TOTAL}줄 → {NEW_TOTAL}줄 (−{PCT}%)",
        '<table class="nw"><thead><tr><th>원본 가이드</th><th>줄 수</th><th>Foundry 에이전트에서는</th></tr></thead><tbody>'
        + mt
        + f"<tr><td><b>합계</b></td><td><b>{OLD_TOTAL}줄</b></td><td><b>{NEW_TOTAL}줄</b> (+ 에이전트 코드 {AGENT_LINES}줄 · azure.yaml {YAML_LINES}줄은 모니터링이 아니라 에이전트 정의)</td></tr>"
        "</tbody></table>"
        + call(
            "info",
            "판단 기준",
            "<ul><li><b>이미 운영 중인 VM 앱을 그대로 두어야 한다</b> → 원본 가이드(R1~R8). 엔드포인트만 Foundry 로 바꿔도 에이전트 트레이스는 생기지 않습니다.</li>"
            "<li><b>모델 호출 + 지시문 정도의 앱</b>을 옮길 수 있다 → <b>프롬프트 에이전트</b>가 가장 단순합니다(코드 · 서버 없음, 추가 요금 없음 · 토큰 비용만).</li>"
            "<li><b>도구 · 오케스트레이션 코드가 필요하다</b> → <b>MAF 호스티드 에이전트</b>. 모니터링은 여전히 코드 없이 되지만 <b>세션별 cold start</b>와 컨테이너 시간 과금을 설계에 넣어야 합니다.</li>"
            "<li>두 에이전트 모두 <b>프롬프트 · 응답 본문이 트레이스에 기록</b>되므로 접근 제어(부록 C)를 먼저 정하세요.</li></ul>",
        )
    )
    e2 = step(
        "e2",
        "정리 — 프로젝트 · 모델 · 에이전트 · 모니터링 리소스 전부 삭제",
        "E2",
        "소요 약 3분",
        "<p><code>azd down</code> 이 azd 가 만든 리소스 그룹을 통째로 지웁니다. <code>--purge</code> 를 붙이면 삭제된 Foundry 리소스도 영구 삭제해 같은 이름을 다시 쓸 수 있습니다. "
        "(Network Watcher 같은 리소스 그룹 밖 리소스는 만들지 않으므로 따로 지울 것이 없습니다.)</p>"
        + code(
            """azd down --force --purge
rm -f foundry.env calls.jsonl last_call.ts alerts.txt""",
            cap="전체 삭제",
            run="E2",
            skip=True,
        )
    )
    sec_e = section("e", "E · 비교 정리와 삭제", "R1~R8 대응표 · 판단 기준 · 정리", e1 + e2)

    # ───────────────── 부록
    facts = [
        ("azd up 한 번", "ok", f"프로젝트 · 모델 · Application Insights 연결 · 에이전트 2개가 {m['up_total_s'] // 60}분 {m['up_total_s'] % 60}초(프로비저닝+훅 {m['provision_s']}초, 배포 {m['deploy_s']}초). 새 환경 2번 중 1번은 첫 시도가 <code>FailedIdentityOperation Conflict</code> 로 실패, 재실행으로 성공"),
        ("azd 프로비저너가 만드는 것", "ok", "<code>infra.provider: microsoft.foundry</code> 는 Foundry 리소스 · 프로젝트 · 모델 배포만 만들고 <b>Application Insights 는 만들지 않습니다</b> → postprovision 훅(<code>connect-appinsights.sh</code>)이 연결"),
        ("서버 쪽 트레이스 자동 수집", "ok", "연결만으로 프롬프트 에이전트(<code>invoke_agent</code> · <code>chat</code> 스팬)와 호스티드 에이전트(플랫폼 요청 스팬 + 컨테이너 스팬 · 로그)가 코드 변경 없이 수집됨"),
        ("traceparent → operation_Id", "ok", "클라이언트가 보낸 trace_id 가 프롬프트 · 호스티드 모두에서 서버 쪽 모든 기록의 <code>operation_Id</code> 와 일치 (컨테이너 로그 포함)"),
        ("응답 ID 대조", "ok", "프롬프트: 클라이언트 <code>resp_…</code> = 스팬의 <code>gen_ai.response.id</code>, 호스티드: <code>caresp_…</code> = 요청 스팬의 <code>azure.ai.agentserver.response_id</code>"),
        ("호스티드 cold start 분해", "ok", "요청 스팬에 <code>hosted_agent.latency.*</code> 속성(start_type · platform_preprocessing · infra_setup · container_readiness · container_response · response_begin). 새 대화마다 cold, 같은 대화 재사용 시 warm"),
        ("프롬프트 에이전트 idle 뒤 첫 호출", "ok", "실행 시간이 모델 호출 시간보다 수 초 길어지는 호출이 쉬었다 온 첫 호출에서 재현됨 (모델 호출은 1초 미만 그대로)"),
        ("실패 가시성", "ok", "호스티드의 실행 중 실패: <code>dependencies</code>(success=false) · <code>exceptions</code> 에 남고 <code>requests</code> 는 success=true. 시작 전에 거절된 호출(없는 모델 배포로 만든 프롬프트 에이전트)은 어떤 테이블에도 남지 않음"),
        ("프롬프트 · 응답 본문", "ok", "<code>gen_ai.input.messages</code> · <code>gen_ai.output.messages</code> · 시스템 지시문이 <code>AppDependencies</code> 의 속성과 <code>AppGenAIContent</code> 테이블에 모두 기록됨(보호 플래그 미등록 상태)"),
        ("모델 메트릭", "ok", "Foundry 리소스에 진단 설정 없이 메트릭 정의 99개 · 요청 수 · 토큰 · 응답 완료 시간 값 확인. 진단 범주(<code>RequestResponse</code> 등) 목록은 확인했고 적용은 하지 않음"),
        ("알림", "ok", "느린 실행 · 실패한 실행 알림 2개 발화 확인(알림 목록 API). 수신 메일 도착은 확인하지 못함. 평가 창 5분일 때 지연 도착한 텔레메트리를 놓치는 경우가 있어 15분으로 늘림"),
        ("Foundry 포털 화면", "part", "Traces · Monitor · Operate 화면은 열어 보지 못함 — 같은 Application Insights 데이터까지만 확인"),
        ("로컬 실행", "part", "<code>azd ai agent run</code>(로컬 8088 포트)은 시도하지 않음"),
    ]
    ftr = "".join(f'<tr><td><b>{a}</b></td><td class="{b}">{"✔" if b == "ok" else "△"}</td><td>{c}</td></tr>' for a, b, c in facts)
    x1 = step(
        "x1",
        "실제 환경에서 확인한 사실",
        "부록 A",
        "2026-10-24 · Korea Central · gpt-5.4-mini · azd 1.37.1 · azure.ai.agents 1.0.0-beta.22 · azure-ai-projects 2.9 · Azure CLI 2.86",
        '<table><thead><tr><th>항목</th><th class="res">결과</th><th>실측 내용</th></tr></thead><tbody>' + ftr + "</tbody></table>",
    )

    trouble = [
        ("azd 가 <code>look up tenant for subscription … failed to resolve user</code>", "azd 와 az 가 서로 다른 계정으로 로그인됨. <code>azd auth login</code> 을 az 와 같은 계정으로 하거나 <code>azd config set auth.useAzCliAuth true</code>"),
        ("<code>azd up</code> 이 <code>FailedIdentityOperation … Conflict</code> 로 실패", "계정 생성 직후의 일시적 충돌. 같은 <code>azd up</code> 을 다시 실행"),
        ("호스티드 배포가 <code>[tool.poetry] section not found</code> 로 실패", "원격 빌더가 <code>pyproject.toml</code> 만 있으면 Poetry 로 가정. <code>requirements.txt</code> 를 쓰거나 <code>uv.lock</code> 을 함께 둠"),
        ("호출이 403 · 401", "호출자에게 <b>Foundry User</b>(구 Azure AI User) 역할이 없거나 아직 반영 전(최대 수 분). 프로젝트 범위에 부여했는지 확인"),
        ("트레이스가 안 보임", "① 프로젝트에 Application Insights 연결이 있는지(<code>…/projects/&lt;프로젝트&gt;/connections</code> 에 category AppInsights) ② 호출이 에이전트(프롬프트 · 호스티드)를 거쳤는지 — 모델 엔드포인트만 호출하면 트레이스가 없음 ③ 1~3분 대기"),
        ("호스티드 에이전트 첫 호출이 8~10초", "새 세션의 cold start. 같은 대화(<code>conversation</code>)를 재사용하거나 idle 시간을 조정. 원인 분해는 C3"),
        ("응답이 <code>status: failed</code> · <code>An internal server error occurred.</code>", "클라이언트에는 원인이 안 나옴. C4 의 <code>trace_by_id</code> 와 D3 의 <code>failed_runs</code> 로 컨테이너 쪽 예외 확인"),
        ("<code>azd down</code> 후 같은 이름 재사용 불가", "삭제된 Foundry 리소스가 소프트 삭제 상태. <code>azd down --purge</code> 또는 <code>az cognitiveservices account purge</code>"),
    ]
    ttr = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in trouble)
    x2 = step("x2", "문제 해결", "부록 B", "이번 검증에서 실제로 만난 것 위주", '<table><thead><tr><th>증상</th><th>확인 · 해결</th></tr></thead><tbody>' + ttr + "</tbody></table>")

    x3 = step(
        "x3",
        "운영에 적용할 때 달라지는 점 · 개인정보",
        "부록 C",
        "이 가이드는 공용 네트워크 · 기본 설정으로 검증했습니다",
        "<ul>"
        "<li><b>입출력 본문이 기록됩니다.</b> 프롬프트 · 응답 · 시스템 지시문 · 도구 인자가 트레이스에 남습니다. 문서의 절차: 구독에 <code>protectGenAISensitiveData</code> 기능 플래그를 등록해 본문을 "
        "<code>AppGenAIContent</code> 전용 테이블로만 보내고, 그 테이블을 보호 테이블로 설정한 뒤 <b>Privileged Monitoring Data Reader</b> 역할로 읽기 권한을 제한합니다(문서에서 확인 · 이 가이드는 적용하지 않음). "
        "이 실습 구독에서는 플래그가 등록되어 있지 않아 본문이 <code>AppDependencies</code> 속성과 전용 테이블 양쪽에 있었습니다.</li>"
        "<li><b>보존 · 비용</b>은 연결된 Application Insights / Log Analytics 설정을 따릅니다. 포털의 트레이스 보기는 최대 90일.</li>"
        "<li><b>역할</b>: 호출 = Foundry User, 포털에서 트레이스 · 모니터 보기 = 연결된 Application Insights 의 Log Analytics Reader(보호 테이블이면 Privileged Monitoring Data Reader 추가). 프로젝트 관리 ID 의 Log Analytics Reader 는 평가 기능용입니다.</li>"
        "<li><b>네트워크 격리</b>(private endpoint · 관리형 VNet)를 쓰는 프로젝트는 이 가이드의 공용 경로 명령이 그대로 되지 않습니다 — 별도 템플릿(Foundry 문서의 private-network)을 쓰세요. 이번 검증 범위 밖입니다.</li>"
        "<li><b>베타 · 프리뷰</b>: azd 의 Foundry 확장은 베타(버전 고정 권장), 포털의 Monitor · Alerts 는 프리뷰, 트레이싱 자체는 프롬프트 · 호스티드 에이전트에서 GA(문서 기준).</li>"
        "<li><b>샘플링 · 비용</b>: 호출량이 많으면 Application Insights 수집 비용이 커집니다. 수집량(GB/일)을 먼저 추정하고 샘플링 · 보존 기간을 정하세요.</li>"
        "</ul>",
    )

    def li(items):
        return "<ol>" + "".join(f"<li>{x}</li>" for x in items) + "</ol>"

    x4 = step(
        "x4",
        "직접 만드는 모니터링용 리소스 · 줄 수 상세",
        "부록 D",
        "비교표의 ② · ① 을 뒷받침하는 목록 (줄 수는 빌드할 때 파일에서 직접 셉니다)",
        '<div class="two"><div><h4>원본 가이드 — ' + f"{len(OLD_RESOURCES)}종</h4>" + li(OLD_RESOURCES) + "</div>"
        '<div><h4>이 가이드 — ' + f"{len(NEW_RESOURCES)}종</h4>" + li(NEW_RESOURCES) + "</div></div>"
        + '<table class="nw"><thead><tr><th>원본 가이드 스니펫 (빈 줄 · 주석 제외)</th><th>줄</th></tr></thead><tbody>'
        f"<tr><td>R1 AOAI 진단 설정</td><td>{OLD['R1']}</td></tr><tr><td>R3 앱 호출 로그(helper + 사용 예)</td><td>{OLD['R3']}</td></tr>"
        f"<tr><td>R4 Application Insights(OTel 코드 · env · systemd)</td><td>{OLD['R4']}</td></tr><tr><td>R5 VM 에이전트 · DCR</td><td>{OLD['R5']}</td></tr>"
        f"<tr><td>R6 네트워크 경로 로그</td><td>{OLD['R6']}</td></tr><tr><td>R7 합성 probe(스크립트 · 서비스 · 타이머)</td><td>{OLD['R7']}</td></tr>"
        f"<tr><td>R8 알림</td><td>{OLD['R8']}</td></tr><tr><td><b>합계</b></td><td><b>{OLD_TOTAL}</b></td></tr></tbody></table>"
        '<table class="nw"><thead><tr><th>이 가이드의 모니터링 설정 파일</th><th>줄</th></tr></thead><tbody>'
        f"<tr><td><code>scripts/connect-appinsights.sh</code> (Application Insights 연결 · 역할)</td><td>{NEW['connect']}</td></tr>"
        f"<tr><td><code>scripts/alerts.sh</code> (알림 2개)</td><td>{NEW['alerts']}</td></tr>"
        f"<tr><td><b>합계</b></td><td><b>{NEW_TOTAL}</b></td></tr></tbody></table>"
        f"<p class=\"foot-note\">모니터링이 아닌 파일: 에이전트 코드 <code>main.py</code> {AGENT_LINES}줄(텔레메트리 코드 0줄), 클라이언트 <code>invoke_agents.py</code> {CLIENT_LINES}줄(선택), 에이전트 · 모델 정의 <code>azure.yaml</code> {YAML_LINES}줄.</p>",
    )
    sec_x = section("x", "부록", "검증 기록 · 문제 해결 · 운영 적용 · 상세", x1 + x2 + x3 + x4)
    return sec_d + sec_e + sec_x
