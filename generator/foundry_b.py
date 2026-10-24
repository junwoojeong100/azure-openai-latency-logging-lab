# -*- coding: utf-8 -*-
# B · 호출 / C · 확인과 분석 (Foundry 에이전트 모니터링 가이드)
from lib import *
import foundry_a


def exp(name, label="예상 결과"):
    t = expected(name)
    return out(t, label=label) if t else ""


def kqb(name, cap, run, extra="", placeholder=None):
    """foundry/queries.kql 의 쿼리를 kq 로 실행하는 코드 블록. placeholder=('<trace_id>', '$TID') 이면 sed 로 값을 끼워 넣는다."""
    q = fkql(name)
    assert "'" not in q, name
    if placeholder:
        ph, val = placeholder
        text = extra + f'kq "$(sed "s/{ph}/{val}/" <<\'KQL\'\n{q}\nKQL\n)"'
    else:
        text = extra + "kq '\n" + q + "\n'"
    return code(text, cap=cap, run=run)


def build():
    m = foundry_a.measured()

    # ───────────────── B. 호출
    b1 = step(
        "b1",
        "azd 로 한 번씩 호출",
        "B1",
        "소요 약 30초",
        "<p>두 에이전트를 CLI 로 한 번씩 호출합니다. <b>호스티드 에이전트는 응답에 플랫폼이 잰 시간 분해가 같이 나옵니다</b>"
        "(<code>preprocess · infra · readiness · container</code>). 같은 값이 트레이스에도 속성으로 남습니다(C3).</p>"
        + code(
            """azd ai agent invoke report-prompt-agent "보고서 첫 문단은 어떻게 쓰나요? 한 문장으로 답해줘"
azd ai agent invoke report-maf-agent "보고서 첫 문단은 어떻게 쓰나요? 한 문장으로 답해줘\"""",
            cap="프롬프트 에이전트 → 호스티드 에이전트",
            run="B1",
        )
        + exp("B1")
    )

    b2 = step(
        "b2",
        "클라이언트 스크립트로 트래픽 만들기",
        "B2",
        "소요 약 2분",
        "<p>기존 앱이 모델 대신 에이전트를 부르게 바꾼다면 클라이언트가 바뀌는 부분은 <b>아래 몇 줄</b>이 전부입니다 — 텔레메트리 코드는 없습니다. "
        "눈여겨볼 곳은 <code>traceparent</code> 헤더 한 줄: <b>클라이언트가 trace_id 를 정해서 보내면 서버 쪽 모든 기록의 <code>operation_Id</code> 가 같은 값</b>이 됩니다 "
        "(원본 가이드에서 <code>apim-request-id</code> 로 하던 요청 단위 대조를 코드 한 줄로 대신합니다).</p>"
        + code(fd("invoke_agents.py"), cap="foundry/invoke_agents.py — 에이전트를 부르고 호출마다 JSON 한 줄 출력", lang="python")
        + code(
            """python3 -m venv .venv && . .venv/bin/activate
pip install -q azure-ai-projects azure-identity
python invoke_agents.py report-prompt-agent 5 short new | tee -a calls.jsonl     # 프롬프트 에이전트 · 짧은 질문
python invoke_agents.py report-prompt-agent 2 long new  | tee -a calls.jsonl     # 긴 답변(약 700자)
python invoke_agents.py report-maf-agent 2 short new    | tee -a calls.jsonl     # 호스티드 · 호출마다 새 대화 → 매번 cold start
python invoke_agents.py report-maf-agent 5 short same   | tee -a calls.jsonl     # 호스티드 · 한 대화 재사용 → 첫 호출만 cold
python invoke_agents.py report-maf-agent 2 long same    | tee -a calls.jsonl
date +%s > last_call.ts""",
            cap="가상환경 → 호출 16번 (약 2분). 첫 줄이 클라이언트가 잰 시간(ms) · 응답 ID · trace_id",
            run="B2",
        )
        + exp("B2")
        + call(
            "info",
            "클라이언트가 본 시간 — 호스티드 에이전트의 cold / warm",
            "<p>같은 <code>short</code> 질문인데 호스티드 에이전트는 <b>새 대화(세션)마다 약 8~12초</b>, <b>같은 대화를 재사용하면 첫 호출만 느리고 이후 1~2초</b>입니다. "
            "프롬프트 에이전트는 대부분 1~2초입니다. 이 차이가 어디서 오는지는 C3 에서 트레이스로 가려냅니다. "
            "또 <code>status</code> 가 <code>failed</code> 여도 HTTP 는 200 입니다 — 클라이언트 코드는 <b>status 를 확인</b>해야 합니다(D2).</p>",
        )
    )
    sec_b = section("b", "B · 호출", "에이전트를 부르고 클라이언트 쪽 기록을 남깁니다", b1 + b2)

    # ───────────────── C. 확인과 분석
    c1 = step(
        "c1",
        "트레이스가 들어왔는지",
        "C1",
        "호출 후 1~3분 (마지막 호출이 보일 때까지 기다림)",
        "<p>Application Insights 로 가는 길에는 이미 두 가지가 연결되어 있습니다 — ① <b>플랫폼 스팬</b>: 프롬프트 에이전트 실행과 모델 호출(<code>responsesapi</code>), 호스티드 에이전트 요청(<code>agentsv2</code>), "
        "② <b>컨테이너 스팬 · 로그</b>: 호스티드 에이전트 컨테이너가 스스로 보냄(역할 이름 = 에이전트 이름). 마지막 호출의 trace_id 가 조회될 때까지 기다린 뒤 건수를 봅니다.</p>"
        + code(
            """TID=$(tail -1 calls.jsonl | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["trace_id"])')
for i in $(seq 1 60); do
  N=$(az monitor app-insights query --app "appi-$AZURE_ENV_NAME" -g "$AZURE_RESOURCE_GROUP" --analytics-query "union requests, dependencies | where operation_Id == '$TID' | count" --query 'tables[0].rows[0][0]' -o tsv)
  [ "${N:-0}" -gt 0 ] && break; sleep 5
done
echo "마지막 호출(trace_id=$TID)의 스팬 ${N:-0}건 — 호출이 끝나고 $(( $(date +%s) - $(cat last_call.ts) ))초 뒤에 조회됨"
sleep 30""",
            cap="① 마지막 호출이 조회될 때까지 대기 (5초 간격)",
            run="C1",
        )
        + exp("C1a")
        + kqb("ingested_by_role", "② 최근 30분 — 테이블 · 역할별 건수", "C1")
        + exp("C1b")
        + call(
            "info",
            "실측으로 확인한 것",
            f"<ul><li>호출이 끝나고 마지막 호출의 스팬이 조회되기까지 약 <b>{m['first_visible_s']}초</b>였습니다. 이 가이드 전체 실행에서 텔레메트리 799건을 Log Analytics 로 세어 보니(스팬이 끝난 시각 → 수집 시각) "
            "<b>중앙값 약 6초, 96% 가 1분 안, 가장 늦은 것은 약 2분 40초</b>였습니다. "
            "원본 가이드의 AOAI 진단 로그는 설정 후 20~26분이 지나서야 기록되기 시작했습니다.</li>"
            "<li>역할(<code>cloud_RoleName</code>) <code>responsesapi</code> · <code>agentsv2</code> 는 <b>플랫폼이 보낸 것</b>, 에이전트 이름(<code>report-maf-agent</code>)은 <b>호스티드 컨테이너가 보낸 것</b>입니다. "
            "컨테이너는 시작할 때 Azure Monitor 를 스스로 설정합니다 — 컨테이너 로그에 “Azure Monitor configured via azure-monitor-opentelemetry package” 가 남습니다.</li>"
            "<li>컨테이너가 cold start 할 때마다 <code>ModuleNotFoundError: Failed to set up A365 OpenAI Agents instrumentation</code> 예외가 1건씩 남습니다 (무해한 소음 — 쿼리에서 제외).</li></ul>",
        )
    )

    c2 = step(
        "c2",
        "에이전트 단위 — 실행 수 · 지연",
        "C2",
        "원본 가이드의 C3(시간 패턴)에 해당",
        "<p>프롬프트 에이전트의 한 번 실행은 <code>dependencies</code> 의 <code>invoke_agent</code> 스팬, 호스티드 에이전트의 한 번 실행은 <code>requests</code> 의 <code>invoke_agent</code> 입니다. "
        "호스티드는 <b>요청 시간에 cold start 시간(플랫폼 전처리 + 인프라 + 컨테이너 준비)을 더해야</b> 클라이언트가 겪은 시간과 맞습니다.</p>"
        + kqb("prompt_runs_5min", "프롬프트 에이전트 — 5분 단위 실행 수 · 지연(ms)", "C2")
        + exp("C2a")
        + kqb("hosted_runs_5min", "호스티드 에이전트 — 5분 단위 실행 수 · cold 수 · 시작 지연 포함 총 시간(ms)", "C2")
        + exp("C2b")
    )

    c3 = step(
        "c3",
        "느린 호출은 어디서 느린가 — 모델 · 에이전트 런타임 · cold start",
        "C3",
        "원본 가이드의 C2(앱 vs AOAI 대조)에 해당",
        "<p>원본에서는 <b>앱이 잰 시간과 AOAI 가 잰 시간의 차이</b>로 “느린 곳이 앱 쪽인가 AOAI 쪽인가”를 가렸습니다. 여기서는 같은 질문을 두 쿼리로 풉니다.</p>"
        "<ul><li><b>프롬프트 에이전트</b>: <code>invoke_agent</code>(실행 전체) − <code>chat</code>(모델 호출) = <b>에이전트 런타임 오버헤드</b>. 정상일 때는 수백 ms 입니다.</li>"
        "<li><b>호스티드 에이전트</b>: 시작 지연을 4단계(<code>platform_preprocessing · infra_setup · container_readiness · container_response</code>)로 쪼갠 속성이 요청 스팬에 자동으로 붙습니다.</li></ul>"
        + kqb("prompt_overhead", "프롬프트 에이전트 — 모델 시간을 뺀 오버헤드가 큰 실행 TOP 10", "C3")
        + exp("C3a")
        + kqb("hosted_cold_vs_warm", "호스티드 에이전트 — cold / warm 별 시작 지연 구성(평균 ms)", "C3")
        + exp("C3b")
        + call(
            "info",
            "읽는 법",
            f"<ul><li>호스티드 <code>cold</code> 의 시간은 대부분 <b>infra_setup(세션 샌드박스 준비) + container_readiness(컨테이너 기동)</b> — 합치면 약 {m['cold_startup_s']}초 — 이고, 모델 호출은 그 뒤 1초 안팎입니다.</li>"
            f"<li>프롬프트 에이전트는 대부분 오버헤드가 수백 ms 이하입니다. 그런데 이번 검증의 {m['prompt_runs']}건 중 {m['prompt_outliers']}건은 <b>모델 호출은 1초 미만(정상)인데 실행 전체가 약 {m['prompt_outlier_s']}초</b>였습니다(위 예시 출력에는 없는, 다른 실행에서 나온 값) — 위 쿼리의 오버헤드 열이 바로 그 차이이며, "
            "원인은 모델이 아니라 에이전트 런타임입니다(쉬었다 온 호출이었다는 점 외에 재현 조건은 확인하지 못했습니다). 느린 호출을 만나면 모델 쪽부터 의심하지 말고 이 열부터 보세요.</li>"
            "<li>그래서 호스티드 에이전트를 쓸 때는 <b>세션(대화)을 재사용</b>하고 idle 시간을 맞추는 설계가 지연에 직접 영향을 줍니다(<code>invoke_agents.py … same</code>).</li></ul>",
        )
    )

    c4 = step(
        "c4",
        "요청 한 건 따라가기 — trace_id · 응답 ID",
        "C4",
        "원본 가이드의 C2 요청 단위 조인에 해당",
        "<p>클라이언트가 <code>traceparent</code> 로 정한 <code>trace_id</code> 는 서버 쪽 <b>모든 스팬 · 컨테이너 로그의 <code>operation_Id</code></b> 입니다. 호스티드 에이전트 한 건(첫 호출 = cold)을 따라가 봅니다.</p>"
        + kqb(
            "trace_by_id",
            "trace_id 한 건 — 플랫폼 · 컨테이너 스팬과 컨테이너 로그를 시간순으로",
            "C4",
            extra="""TID=$(grep report-maf-agent calls.jsonl | head -1 | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["trace_id"])')\n""",
            placeholder=("<trace_id>", "$TID"),
        )
        + exp("C4a")
        + "<p>trace_id 를 잃어버렸다면 클라이언트가 받은 <b>응답 ID</b>(프롬프트 <code>resp_…</code> · 호스티드 <code>caresp_…</code>)로도 찾을 수 있습니다.</p>"
        + kqb(
            "response_lookup",
            "응답 ID 로 서버 쪽 기록 찾기",
            "C4",
            extra="""RID=$(grep report-prompt-agent calls.jsonl | tail -1 | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["response_id"])')\n""",
            placeholder=("<response_id>", "$RID"),
        )
        + exp("C4b")
    )

    c5 = step(
        "c5",
        "토큰 · 모델 쪽 메트릭",
        "C5",
        "원본 가이드의 R1(토큰) · R2(메트릭)에 해당",
        "<p>토큰 수는 플랫폼 <code>chat</code> 스팬에 있고(원본에서는 AOAI 진단 로그의 <code>properties_s</code>), 모델 쪽 서비스 메트릭(요청 수 · 토큰 · 응답 완료 시간)은 "
        "<b>진단 설정 없이 Foundry 리소스에 이미 쌓입니다</b>(메트릭 정의 99개). 로그(<code>RequestResponse</code> 등)가 필요할 때만 원본 R1 의 진단 설정을 같은 방식으로 추가하면 됩니다.</p>"
        + kqb("tokens_by_agent", "에이전트 · 모델별 시간당 토큰 사용량", "C5")
        + exp("C5a")
        + code(
            """ACCT_ID=$(az cognitiveservices account show -g "$AZURE_RESOURCE_GROUP" -n "$AZURE_AI_ACCOUNT_NAME" --query id -o tsv)
az monitor metrics list --resource "$ACCT_ID" --metric AzureOpenAIRequests ProcessedPromptTokens GeneratedTokens AzureOpenAITTLTInMS \\
  --interval PT5M --offset 1h --aggregation Total Average -o json | python3 -c '
import json, sys
for m in json.load(sys.stdin)["value"]:
    pts = [(p["timeStamp"][11:16], round(p["total"]), round(p["average"])) for p in m["timeseries"][0]["data"] if p.get("total")]
    print(m["name"]["value"].ljust(24), pts[:6])'""",
            cap="Foundry 리소스의 모델 메트릭 — 설정 없이 조회 (시각 · 합계 · 평균). 메트릭은 7~10분 늦게 보입니다",
            run="C5",
        )
        + exp("C5b")
    )

    c6 = step(
        "c6",
        "포털에서 보는 곳",
        "C6",
        "화면 확인은 이 가이드에서 하지 못했습니다 — 문서 기준",
        "<p>같은 데이터를 Foundry 포털이 그대로 보여 줍니다(문서 기준). 이 가이드의 실습 계정으로는 포털 화면까지 열어 보지 못했고, <b>데이터가 같은 Application Insights 에 있다는 것</b>까지 확인했습니다.</p>"
        "<table class=\"nw\"><thead><tr><th>보고 싶은 것</th><th>Foundry 포털 위치 (New Foundry)</th><th>이 가이드의 대응</th></tr></thead><tbody>"
        "<tr><td>요청 한 건의 단계별 스팬 · 입출력 · 도구 호출</td><td>프로젝트 → <b>Agents → Traces</b> (90일 · Conversation 상세)</td><td>C4 <code>trace_by_id</code></td></tr>"
        "<tr><td>에이전트별 토큰 · 지연 · 실행 성공률</td><td>Build → 에이전트 → <b>Monitor</b> 탭 (프리뷰)</td><td>C2 · C5 쿼리</td></tr>"
        "<tr><td>알림(지연 · 토큰 · 평가 점수)</td><td>Monitor → 설정(톱니) → <b>Alerts</b> (프리뷰)</td><td>D1 <code>alerts.sh</code> (KQL 알림)</td></tr>"
        "<tr><td>여러 프로젝트 · 에이전트 한눈에</td><td>우측 상단 <b>Operate</b> → Overview · Assets</td><td>—</td></tr>"
        "</tbody></table>"
        + call(
            "warn",
            "트레이스를 보려면 권한이 따로 필요합니다",
            "<p>포털에서 트레이스를 보려면 <b>연결된 Application Insights 에 대한 Log Analytics Reader</b> 가 있어야 합니다. "
            "호출은 <b>Foundry User</b>(구 Azure AI User) 역할이 있어야 됩니다 — <code>connect-appinsights.sh</code> 가 두 역할을 모두 부여합니다.</p>",
        )
    )
    sec_c = section("c", "C · 확인과 분석", "트레이스가 들어왔는지, 어디서 느린지를 가립니다", c1 + c2 + c3 + c4 + c5 + c6)
    return sec_b + sec_c
