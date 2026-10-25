# -*- coding: utf-8 -*-
# B · 호출 / C · 확인과 분석 (Foundry 에이전트 모니터링 가이드)
from lib import *
import foundry_a
import foundry_app


def exp(name, label="예상 결과", read=None):
    t = expected(name)
    return out(t, label=label, read=read) if t else ""


def kqtext(name, extra="", placeholder=None):
    """foundry/queries.kql 의 쿼리를 kq 로 실행하는 코드 텍스트. placeholder=('<trace_id>', '$TID') 이면 sed 로 값을 끼워 넣는다."""
    q = fkql(name)
    assert "'" not in q, name
    if placeholder:
        ph, val = placeholder
        return extra + f'kq "$(sed "s/{ph}/{val}/" <<\'KQL\'\n{q}\nKQL\n)"'
    return extra + "kq '\n" + q + "\n'"


def kqtext_raw(q):
    """따옴표가 없는 KQL 을 kq 로 감싸 실행하는 코드 텍스트"""
    assert "'" not in q
    return "kq '\n" + q + "\n'"


SPAN_LAG_KQL = """union requests, dependencies, traces, exceptions
| where timestamp > ago(3d)
| extend end_time = iff(itemType in ("request", "dependency"), timestamp + duration * 1ms, timestamp)
| extend lag_s = datetime_diff("second", ingestion_time(), end_time)
| summarize rows = count(), p50_s = percentile(lag_s, 50), p95_s = percentile(lag_s, 95), max_s = max(lag_s),
            within_60s = round(100.0 * countif(lag_s <= 60) / count(), 0)"""


def build():
    m = foundry_a.measured()

    # ───────────────── B. 호출
    b1 = step(
        "b1",
        "azd 로 한 번씩 호출",
        "B1",
        "소요 약 30초",
        brief(
            what="두 에이전트를 CLI(`azd ai agent invoke`)로 **한 번씩 호출**합니다.",
            why="가장 쉬운 방법으로 에이전트가 동작하는지 보고, **호스티드 에이전트는 응답에 플랫폼이 잰 단계별 시간**(`preprocess · infra · readiness · container`)이 같이 나오는 것을 확인합니다. 같은 값이 트레이스에도 속성으로 남습니다(C3).",
            result="프롬프트 에이전트의 응답 문장과 `Trace ID` · `Response` ID, 호스티드 에이전트의 응답 문장과 cold start 단계별 시간(호스티드의 ID 는 B2 의 JSON 에서 확인).",
            apply="앱 코드가 없어도 호출 가능한 **동작 확인용**입니다. 실제 앱은 B2 · B3 의 SDK 호출을 씁니다.",
            caution="호출이 **401 · 403** 으로 거절되면 역할(Foundry User)이 막 부여된 직후일 수 있습니다. 일반적으로 Azure 의 역할 부여는 **반영에 몇 분** 걸리니 잠시 뒤 다시 시도하세요.",
        )
        + walk(
            """azd ai agent invoke report-prompt-agent "보고서 첫 문단은 어떻게 쓰나요? 한 문장으로 답해줘"
azd ai agent invoke report-maf-agent "보고서 첫 문단은 어떻게 쓰나요? 한 문장으로 답해줘\"""",
            [
                (
                    "azd ai agent invoke report-prompt-agent",
                    "프롬프트 에이전트 호출",
                    "`azd ai agent invoke <에이전트 이름> \"<질문>\"` 은 **에이전트에 질문을 보내 응답을 출력**합니다. 응답 문장과 함께 이 호출의 **Trace ID**(트레이스 이름표)와 **Response ID** 도 보여 줍니다.",
                ),
                (
                    "azd ai agent invoke report-maf-agent",
                    "호스티드 에이전트 호출",
                    "같은 질문을 호스티드 에이전트에 보냅니다. **새 대화이므로 컨테이너를 새로 띄우는 cold start 가 일어나** 응답이 느리고(약 10초), 출력 끝에 **플랫폼이 잰 단계별 시간**이 붙습니다.",
                ),
            ],
            cap="프롬프트 에이전트 → 호스티드 에이전트",
            run="B1",
        )
        + exp(
            "B1",
            read="""
            - 위쪽은 **프롬프트 에이전트** 호출 결과이고, 그 아래 `[report-maf-agent]` 는 **호스티드 에이전트** 호출 결과입니다. 위쪽의 `Trace ID` · `Response` 는 **응답 한 건의 이름표**입니다(참고용 — C4 는 B2 가 만든 `calls.jsonl` 에서 trace_id 를 꺼내 씁니다).
            - 아래 `[report-maf-agent]` 블록: `Client elapsed 9.998s` 는 클라이언트가 잰 총 시간(약 10초)입니다.
            - `Platform latency (cold)` 줄의 네 값: `preprocess 180ms`(플랫폼 전처리) · `infra 1119ms`(세션 샌드박스 준비) · `readiness 5744ms`(**컨테이너 기동 대기**) · `container 1106ms`(**컨테이너가 응답한 시간**). 앞의 **세 값의 합(180 + 1119 + 5744 ≈ 7.0초)이 cold start(시작 지연)** 이고 대부분은 infra + readiness 입니다. `container` 는 시작이 아니라 **응답에 쓴 시간**이라 시작 지연에 더하지 않습니다.
            - 네 값을 모두 더하면 8,149ms(`response headers 8149 ms`)인데 클라이언트가 잰 시간은 9.998초라 **약 1.8초가 더 있습니다.** 이 차이는 플랫폼이 잰 구간 밖의 시간(앱 · SDK · 네트워크 등)이며, 이 호출에서 원인을 나누어 보지는 않았습니다 — 이런 시간은 서버 트레이스에 없고 앱 최소 기록(C7)으로 잡습니다.
            - 출력 순서와 문장은 모델이 만들므로 **여러분의 응답 문장은 다릅니다.** 숫자도 환경에 따라 조금씩 다릅니다.
            """,
        ),
        scope="check",
    )

    inv_walk = walk(
        fd("invoke_agents.py"),
        [
            (
                '"""에이전트를',
                "사용법 (파일 맨 위의 설명)",
                """
                `python invoke_agents.py <에이전트 이름> [횟수=3] [short|long] [new|same]`
                * **`new`** — 호출마다 **새 대화**를 만듭니다(호스티드 에이전트는 매번 cold start).
                * **`same`** — **하나의 대화를 재사용**합니다(첫 호출만 cold, 이후 warm).
                * 호출마다 **JSON 한 줄**(클라이언트가 잰 시간 · 응답 ID · trace ID)을 출력합니다.
                """,
            ),
            (
                "import json",
                "가져오는 것",
                """
                `json`(출력 만들기) · `os`(환경변수) · `secrets`(무작위 ID) · `sys`(실행 인자) · `time`(시간 재기).
                * `AIProjectClient` — **Foundry 프로젝트에 접속**하는 클라이언트(`azure-ai-projects` 패키지)
                * `DefaultAzureCredential` — **내 `az login` 신원**으로 인증(키 없음)
                """,
            ),
            (
                "PROMPTS = {",
                "질문 두 종류",
                "`short` = 한 문장 답변을 요구하는 짧은 질문, `long` = 700자 분량을 요구하는 긴 질문. 응답 길이에 따라 시간이 어떻게 달라지는지 비교하려는 것입니다.",
            ),
            (
                "name = sys.argv[1]",
                "실행 인자 읽기",
                "`name` = 에이전트 이름, `count` = 호출 횟수(기본 3), `prompt` = 질문(기본 short), `same` = 대화를 재사용할지(`same` 이면 True). 인자를 생략하면 기본값을 씁니다.",
            ),
            (
                "project = AIProjectClient",
                "에이전트를 대상으로 하는 클라이언트 만들기",
                """
                * `AIProjectClient(endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=DefaultAzureCredential(), allow_preview=True)` — 프로젝트 주소(환경변수)에 접속합니다. `allow_preview=True` 는 미리보기 기능을 허용합니다.
                * **`project.get_openai_client(agent_name=name)`** — **그 에이전트를 대상으로 하는** OpenAI 호환 클라이언트를 얻습니다. 이 클라이언트로 `responses.create` 를 부르면 모델이 아니라 **에이전트가 실행**됩니다(B3 에서 비교).
                * `conversation = client.conversations.create().id if same else None` — `same` 이면 **대화를 하나 만들어 그 ID 를 재사용**합니다.
                """,
            ),
            (
                "for i in range",
                "호출 반복 — trace_id 를 직접 만들기",
                """
                * `trace_id = secrets.token_hex(16)` — **무작위 32자리 16진수**를 만들어 이 호출의 **trace_id** 로 씁니다.
                * `options` — `same` 이면 대화 ID 를 함께 보냄
                * `started = time.perf_counter()` — **클라이언트가 시간을 재기 시작**(고정밀 타이머)
                """,
            ),
            (
                "response = client.responses.create(",
                "★ 에이전트 호출 — traceparent 로 trace_id 를 서버에 전달",
                """
                * `client.responses.create(input=prompt, …)` — 질문을 보내 에이전트를 실행합니다.
                * **`extra_headers={"traceparent": f"00-{trace_id}-{secrets.token_hex(8)}-01"}`** — W3C **Trace Context** 헤더입니다. 형식은 `00-<trace_id 32자>-<span id 16자>-01`(버전 `00`, 마지막 `01` = 추적 대상). 서버는 이 trace_id 를 **그대로 이어받아 서버 쪽 모든 기록의 `operation_Id` 로** 씁니다.
                  → 이 헤더 한 줄로 **요청 한 건을 서버 기록과 짝지을 수 있습니다**(가이드 1 을 읽었다면: `apim-request-id` 로 하던 일을 대신합니다).
                * `**options` — (있으면) 대화 ID 를 함께 전달
                """,
            ),
            (
                "usage = response.usage",
                "호출 결과를 JSON 한 줄로 출력",
                """
                한 줄에 담는 것(= **앱 최소 기록의 예**):
                * `ms` — 호출 전 · 후 시간 차(**클라이언트가 잰 시간**)
                * `status` — `completed`(정상) · `failed`(실패) · `incomplete`(출력 상한 등에 걸려 중간에 끝남)
                * `response_id` — 서버가 준 응답 ID
                * `trace_id` — 위에서 만든 ID
                * `input_tokens` · `output_tokens` — 입력 · 출력 토큰 수
                * `error` — 응답이 `failed` 로 돌아왔을 때의 오류 메시지(80자까지)
                `ensure_ascii=False` 는 한글이 깨지지 않게 합니다.

                **주의**: 이 스크립트는 API 가 **응답을 돌려준 경우**만 한 줄로 기록합니다. 호출이 **예외로 끝나면**(HTTP 400 · 429 · timeout 등) 이 줄까지 오지 못하고 스크립트가 오류로 종료됩니다. 앱에서는 호출을 `try/except` 로 감싸 **예외도 한 줄로 남겨야** 합니다(C7).
                """,
            ),
        ],
        cap="foundry/invoke_agents.py — 에이전트를 부르고 호출마다 JSON 한 줄 출력",
        lang="python",
    )
    run_walk = walk(
        """python3 -m venv .venv && . .venv/bin/activate
pip install -q azure-ai-projects azure-identity
python invoke_agents.py report-prompt-agent 5 short new | tee -a calls.jsonl     # 프롬프트 에이전트 · 짧은 질문
python invoke_agents.py report-prompt-agent 2 long new  | tee -a calls.jsonl     # 긴 답변(약 700자)
python invoke_agents.py report-maf-agent 2 short new    | tee -a calls.jsonl     # 호스티드 · 호출마다 새 대화 → 매번 cold start
python invoke_agents.py report-maf-agent 5 short same   | tee -a calls.jsonl     # 호스티드 · 한 대화 재사용 → 첫 호출만 cold
python invoke_agents.py report-maf-agent 2 long same    | tee -a calls.jsonl
date +%s > last_call.ts""",
        [
            (
                "python3 -m venv",
                "가상환경 만들고 패키지 설치",
                "`python3 -m venv .venv && . .venv/bin/activate` — 이 폴더에 **전용 Python 환경**을 만들고 켭니다. `pip install -q azure-ai-projects azure-identity` — 클라이언트가 쓰는 **Foundry SDK** 와 **인증 라이브러리**를 설치합니다(`-q` 는 조용히). 이 가이드는 `azure-ai-projects` 2.9 로 확인했습니다(`pip show azure-ai-projects` 로 버전을 볼 수 있습니다).",
            ),
            (
                "python invoke_agents.py report-prompt-agent 5 short new",
                "프롬프트 에이전트 — 짧은 질문 5번 · 긴 질문 2번",
                "`tee -a calls.jsonl` 은 출력을 **화면에 보여 주면서 동시에 `calls.jsonl` 파일 끝에 덧붙여 저장**합니다. 이 파일이 C 단계에서 trace_id · 응답 ID 를 찾는 **호출 기록 파일**입니다. 긴 질문은 약 700자 답변을 만들어 시간이 더 걸립니다.",
            ),
            (
                "python invoke_agents.py report-maf-agent 2 short new",
                "호스티드 — 매번 새 대화(cold start) 2번",
                "`new` 는 호출마다 **새 대화**이므로 매번 컨테이너를 새로 띄우는 **cold start**(약 8~12초)가 일어납니다.",
            ),
            (
                "python invoke_agents.py report-maf-agent 5 short same",
                "호스티드 — 한 대화 재사용(첫 호출만 cold) 5번 + 긴 질문 2번",
                "`same` 은 **같은 대화를 재사용**하므로 **첫 호출만 cold** 이고 이후는 1~2초로 빠릅니다(warm). 이 대비가 C2 · C3 에서 cold / warm 으로 나뉘어 보입니다.",
            ),
            (
                "date +%s",
                "마지막 호출 시각 저장",
                "`date +%s`(UNIX 초)를 `last_call.ts` 에 저장합니다. C1 에서 ‘호출이 끝나고 몇 초 뒤에 트레이스가 조회되는지’를 계산하는 데 씁니다.",
            ),
        ],
        cap="가상환경 → 호출 16번 (약 2분). 첫 줄이 클라이언트가 잰 시간(ms) · 응답 ID · trace_id",
        run="B2",
    )
    b2 = step(
        "b2",
        "클라이언트 스크립트로 트래픽 만들기",
        "B2",
        "소요 약 2분",
        brief(
            what="Python 클라이언트(`invoke_agents.py` — A2 에서 받은 `foundry/` 폴더에 이미 있습니다)로 두 에이전트를 **16번** 호출해 트레이스를 만들고, 호출마다 **클라이언트 쪽 기록(JSON 한 줄)** 을 남깁니다.",
            why="분석할 데이터가 있어야 합니다. 그리고 **클라이언트가 trace_id 를 정해서 보내면** 서버 쪽 모든 기록의 `operation_Id` 가 같은 값이 되므로, 이 호출이 서버 기록의 어느 것인지 **한 번에 찾을 수 있습니다.** (가이드 1 을 읽었다면: 가이드 1 에서 `apim-request-id` 로 짝짓던 일을 헤더 한 줄이 대신합니다.)",
            result="`calls.jsonl` 에 호출 16건이 JSON 한 줄씩 쌓입니다(`ms` · `status` · `response_id` · `trace_id` …).",
            apply="내 앱이 에이전트를 부르게 바꾼다면 **바뀌는 부분은 이 파일의 몇 줄**이 전부입니다. **에이전트 쪽에는 텔레메트리 코드가 없지만**, 이 클라이언트에는 trace_id 만들기 · `traceparent` 전달 · 시간 재기 · JSON 출력이 들어 있습니다. **지연 진단에는 이런 호출 1건당 한 줄의 기록이 필요**합니다(B3 · C7).",
        )
        + inv_walk
        + run_walk
        + exp(
            "B2",
            read="""
            - 한 줄 = 호출 1건입니다. **`ms`** 는 클라이언트가 잰 시간, **`status`** 는 `completed`(정상), **`trace_id`** 는 서버 기록과 짝짓는 키입니다.
            - 프롬프트 에이전트(`report-prompt-agent`)는 대부분 1~2초이고, 호스티드 에이전트(`report-maf-agent`)는 **`new` 일 때 약 9~11초**, **`same` 일 때 첫 호출만 느리고(약 11초) 이후 약 1.8초**입니다.
            - `input_tokens` 가 113 → 177 로 늘어나는 것은 **같은 대화를 재사용**해서 앞선 대화가 입력에 포함되기 때문입니다.
            - **줄 수 확인**: `wc -l calls.jsonl` 이 **16**(호출 수)이고 모든 줄의 `status` 가 `completed` 이면 정상입니다.
            """,
        )
        + call(
            "tip",
            "다시 실행하려면 · 막히면",
            """
            - `calls.jsonl` 은 `tee -a` 로 **계속 덧붙여집니다.** 처음부터 다시 쌓으려면 `rm -f calls.jsonl last_call.ts` 를 먼저 실행하세요.
            - Ubuntu · Debian 에서 `python3 -m venv` 가 `ensurepip` 오류를 내면 `sudo apt install python3-venv` 후 다시 실행합니다.
            """,
        )
        + call(
            "info",
            "클라이언트가 본 시간 — 호스티드 에이전트의 cold / warm",
            "같은 `short` 질문인데 호스티드 에이전트는 **새 대화(세션)마다 약 8~12초**, **같은 대화를 재사용하면 첫 호출만 느리고 이후 1~2초**입니다. 프롬프트 에이전트는 대부분 1~2초입니다. 이 차이가 어디서 오는지는 C3 에서 트레이스로 구분합니다. (오래 쉰 뒤 다시 cold 가 되는지는 측정하지 않았습니다.) 또 `status` 가 `failed` 여도 HTTP 는 200 입니다 — 클라이언트 코드는 **status 를 확인**해야 합니다(D2).",
        ),
        scope="check",
    )
    b3 = foundry_app.build_b3()
    sec_b = section("b", "B · 호출", "에이전트를 부르고, 호출 방식이 어떻게 바뀌는지 봅니다", b1 + b2 + b3)

    # ───────────────── C. 확인과 분석
    wait_walk = walk(
        """TID=$(tail -1 calls.jsonl | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["trace_id"])')
for i in $(seq 1 60); do
  N=$(az monitor app-insights query --app "appi-$AZURE_ENV_NAME" -g "$AZURE_RESOURCE_GROUP" --analytics-query "union requests, dependencies | where operation_Id == '$TID' | count" --query 'tables[0].rows[0][0]' -o tsv)
  [ "${N:-0}" -gt 0 ] && break; sleep 5
done
echo "마지막 호출(trace_id=$TID)의 스팬 ${N:-0}건 — 호출이 끝나고 $(( $(date +%s) - $(cat last_call.ts) ))초 뒤에 조회됨"
sleep 30""",
        [
            (
                "TID=",
                "마지막 호출의 trace_id 꺼내기",
                "`tail -1 calls.jsonl` 은 호출 기록 파일(`calls.jsonl`)의 **마지막 줄**(= 마지막 호출)이고, 짧은 Python 이 그 JSON 에서 `trace_id` 만 꺼내 `TID` 에 담습니다.",
            ),
            (
                "for i in $(seq 1 60)",
                "트레이스가 조회될 때까지 5초 간격으로 확인 (최대 5분)",
                """
                `seq 1 60` 만큼(최대 60번) 반복하며 **Application Insights 에 ‘이 trace_id 의 스팬이 몇 건인지’** 묻습니다.
                * `union requests, dependencies | where operation_Id == '$TID' | count` — 두 테이블에서 trace_id 가 `TID` 인 행의 수
                * `--query 'tables[0].rows[0][0]' -o tsv` — 결과 표의 **첫 값(숫자)** 만 꺼냄 → `N`
                * `[ "${N:-0}" -gt 0 ] && break` — `N` 이 비었으면 0 으로 보고, **1건이라도 있으면 반복 종료** · 아니면 `sleep 5`
                """,
            ),
            (
                "echo ",
                "조회까지 걸린 시간 출력",
                "`$(date +%s) − $(cat last_call.ts)` 로 ‘마지막 호출이 끝난 뒤 몇 초 만에 조회됐는지’를 계산해 보여 줍니다(B2 에서 저장한 `last_call.ts` 사용).",
            ),
            ("sleep 30", "30초 더 기다리기", "마지막 호출만이 아니라 **다른 호출들의 스팬도 도착할 가능성을 높이려고** 30초를 더 기다립니다. 수집 지연이 길면(실측 최대 약 2분 40초) 일부는 더 늦게 보일 수 있습니다."),
        ],
        cap="① 마지막 호출이 조회될 때까지 대기 (5초 간격)",
        run="C1",
    )
    c1 = step(
        "c1",
        "트레이스가 들어왔는지",
        "C1",
        "호출 후 1~3분 (마지막 호출이 보일 때까지 기다림)",
        brief(
            what="마지막 호출의 트레이스가 Application Insights 에서 **조회될 때까지 기다린 뒤**, 최근 30분의 **테이블 · 역할별 건수**를 봅니다.",
            why="데이터가 들어왔는지 확인하고, **호출 후 몇 초 만에 보이는지**(수집 지연)를 잽니다. (비교: 가이드 1 의 AOAI 진단 로그는 켠 뒤 20~26분이 지나서야 기록이 시작됐습니다. 가이드 1 을 읽지 않았다면 건너뛰어도 됩니다.)",
            result="‘스팬 N건 — 호출이 끝나고 약 11초 뒤에 조회됨’ 한 줄 + 건수 표.",
            apply="앱에서 에이전트를 호출한 뒤 같은 쿼리로 **자기 앱 호출이 보이는지** 확인하세요.",
        )
        + md("**어떤 기록이 어디에 남는지** 먼저 한눈에 봅니다. ‘역할 이름’(`cloud_RoleName`)은 기록을 보낸 쪽의 이름표입니다. 이 장의 코드 상자 제목에 붙은 ‘queries.kql: 이름’ 은 저장소 `foundry/queries.kql`(쿼리 모음 파일) 안의 쿼리 이름입니다.")
        + table(
            ["기록", "남긴 쪽(역할 이름)", "테이블", "프롬프트 에이전트", "호스티드 에이전트"],
            [
                ["에이전트 실행(`invoke_agent`) · 모델 호출(`chat`) 스팬", "플랫폼 `responsesapi`", "`dependencies`", "✔", "✔"],
                ["호스티드 에이전트가 받은 요청 + cold start 속성", "플랫폼 `agentsv2`", "`requests`", "—", "✔"],
                ["컨테이너 자신의 스팬 · 로그 · 예외", "에이전트 이름(`report-maf-agent`)", "`dependencies` · `traces` · `exceptions`", "—", "✔"],
            ],
        )
        + md("호스티드 에이전트의 실행은 **플랫폼이 본 요청**(`requests`)과 **플랫폼이 남긴 실행 · 모델 호출 스팬**(`dependencies`)에 **양쪽으로** 남고, 컨테이너가 자기 기록을 더 보냅니다. 프롬프트 에이전트는 컨테이너가 없어 첫 줄만 남습니다. 프로젝트에 연결만 되어 있으면 이 모두가 코드 없이 쌓입니다.")
        + wait_walk
        + exp("C1a", read="`스팬 6건` 은 마지막 호출 하나가 만든 서버 쪽 기록(요청 · 외부 호출) 수이고(내용은 C4 에서 봅니다), **‘11초 뒤에 조회됨’** 이 이 환경에서 측정한 수집 지연입니다. 5초 간격으로 확인하므로 **±5초 오차**가 있고, **B2 가 끝난 직후(1분 안)에 실행했을 때의 값**입니다 — B3 를 읽는 데 몇 분이 걸린 뒤 실행하면 마지막 호출이 이미 조회 가능해서 ‘N초 뒤’ 의 N 이 **읽은 시간만큼 커집니다**(지연이 늘어난 것이 아닙니다).")
        + walk(
            kqtext("ingested_by_role"),
            [
                (
                    "",
                    "네 개 테이블을 합치기 (kq 로 감싸서 실행)",
                    """
                    `kq '…'` 의 작은따옴표 안이 KQL 입니다(A3 에서 만든 도우미).
                    * `union requests, dependencies, traces, exceptions` — Application Insights 의 **네 테이블을 한 번에** 봅니다. `requests` = 들어온 요청(호스티드 에이전트 실행), `dependencies` = 외부 호출(프롬프트 에이전트 실행 · 모델 호출), `traces` = 로그, `exceptions` = 예외
                    """,
                ),
                ("| where timestamp > ago(30m)", "최근 30분만", "`timestamp` 는 기록 시각, `ago(30m)` 는 ‘지금부터 30분 전’입니다."),
                (
                    "| summarize rows",
                    "종류 · 역할별 건수",
                    "`itemType`(테이블 종류: request · dependency · trace · exception)과 **`cloud_RoleName`(기록을 보낸 쪽의 역할 이름)** 별로 건수를 셉니다. 플랫폼이 보낸 것은 `responsesapi` · `agentsv2`, 호스티드 컨테이너가 보낸 것은 에이전트 이름입니다.",
                ),
                ("| order by itemType asc", "정렬", "종류 · 역할 이름 오름차순."),
            ],
            cap="② 최근 30분 — 테이블 · 역할별 건수 (queries.kql: ingested_by_role)",
            run="C1",
            lang="kql",
        )
        + exp(
            "C1b",
            read="""
            - **`responsesapi`**(dependency 36건)와 **`agentsv2`**(request 10건)는 **플랫폼이 보낸 것**입니다. 36건 = 프롬프트 에이전트 8번 × 2 + 호스티드 에이전트 10번 × 2(호출 하나당 실행 `invoke_agent` 스팬 1 + 모델 호출 `chat` 스팬 1)이고, `agentsv2` 10건 = 호스티드 호출 10번(B1 1 + B2 9)입니다. **`report-maf-agent`**(dependency · exception · trace)는 **호스티드 컨테이너가 직접 보낸 것**입니다 — 컨테이너가 시작할 때 Azure Monitor 를 스스로 설정합니다. `exception` 5건은 cold start 가 **한 번 일어날 때마다 1건씩** 남는 무해한 소음입니다(이번에는 cold start 가 5번이라 5건 — 아래 상자).
            - 이 쿼리는 **최근 30분**만 봅니다. 호출한 지 30분이 넘었다면 쿼리의 `ago(30m)` 를 `ago(24h)` 로 바꿔 보세요(C2 · C3 의 `ago(1h)` 도 같습니다). 또 `kq` 는 기본으로 **최근 1시간**만 조회하므로(`az monitor app-insights query` 의 기본값), 1시간이 지났다면 A3 의 ‘`--offset 3d` 설정’을 먼저 하세요. 시각(`timestamp`)은 **UTC** 입니다 — 한국 시각(KST)은 +9시간입니다.
            - 코드에 텔레메트리를 넣지 않았는데도 네 종류가 모두 들어와 있는 것이 이 가이드의 핵심입니다.
            """,
        )
        + call(
            "info",
            "실측으로 확인한 것",
            f"""
            - 호출이 끝나고 마지막 호출의 스팬이 조회되기까지 약 **{m['first_visible_s']}초**였습니다. 이 가이드 전체 실행에서 텔레메트리 799건을 ‘스팬이 끝난 시각 → 수집 시각’으로 세어 보니 **중앙값 약 6초, 96% 가 1분 안, 가장 늦은 것은 약 2분 40초**였습니다(수동 측정 — 아래 ‘직접 재 보기’ 쿼리로 확인할 수 있습니다). 가이드 1 의 AOAI 진단 로그는 설정 후 20~26분이 지나서야 기록되기 시작했습니다.
            - 역할(`cloud_RoleName`) `responsesapi` · `agentsv2` 는 **플랫폼이 보낸 것**, 에이전트 이름(`report-maf-agent`)은 **호스티드 컨테이너가 보낸 것**입니다. 컨테이너 로그에 “Azure Monitor configured via azure-monitor-opentelemetry package” 가 남습니다.
            - 컨테이너가 cold start 할 때마다 `ModuleNotFoundError: Failed to set up A365 OpenAI Agents instrumentation` 예외가 1건씩 남습니다(무해한 소음 — 쿼리에서 제외).
            - 이 가이드의 쿼리는 **Application Insights 의 테이블 이름**(`requests` · `dependencies` · `traces` · `exceptions`)을 씁니다. Log Analytics 워크스페이스에서 직접 조회하면 이름이 `AppRequests` · `AppDependencies` · `AppTraces` · `AppExceptions` 로 바뀌고 열 이름도 다릅니다(`timestamp` → `TimeGenerated`, `duration` → `DurationMs`, `cloud_RoleName` → `AppRoleName`, `customDimensions` → `Properties`, `operation_Id` → `OperationId`).
            """,
        )
        + details(
            "수집 지연을 직접 재 보기 (선택 · 위 ‘중앙값 약 6초’ 수동 측정과 같은 방식)",
            md("각 기록이 **끝난 시각**(`timestamp + duration`)에서 **수집된 시각**(`ingestion_time()`)까지의 차이(`lag_s`)를 구해 분포를 봅니다. 이 환경에서 실습 이후 시험까지 포함해 다시 재면 **947건 · 중앙값 6초 · p95 9초 · 최대 164초 · 96% 가 1분 안**이었습니다(이 가이드의 실행 블록에는 넣지 않은 확인용 쿼리입니다).")
            + code(
                kqtext_raw(SPAN_LAG_KQL),
                cap="수집 지연 분포 — 기록이 끝난 시각 → 조회 가능해진 시각 (확인용 · 실행 블록 아님)",
                lang="kql",
            )
            + out(
                "rows  p50_s  p95_s  max_s  within_60s\n----  -----  -----  -----  ----------\n947   6      9      164    96",
                label="예상 결과 (이 환경의 실제 값 — 여러분의 값은 호출 수에 따라 다릅니다)",
                read="`within_60s` 는 1분 안에 조회된 기록의 비율(%)입니다. 최대 164초(약 2분 44초) 이상 늦게 도착하는 기록도 있을 수 있으니, 방금 한 호출이 안 보이면 몇 분 기다려 보세요.",
            ),
        ),
        scope="check",
    )

    c2 = step(
        "c2",
        "에이전트 단위 — 실행 수 · 지연",
        "C2",
        "5분 단위 지연 보기 · 가이드 1 을 읽었다면: 가이드 1 의 C3(시간 패턴)에 해당",
        brief(
            what="프롬프트 에이전트와 호스티드 에이전트의 **5분 단위 실행 수 · 지연**을 봅니다.",
            why="평소 기준선(p50)과 느린 꼬리(p95)를 알아야 ‘이번 호출이 느린 건지’ 판단할 수 있습니다. 호스티드는 **요청 시간에 cold start 시간을 더해야** 클라이언트가 겪은 시간에 가까워집니다(네트워크 · SDK · 재시도 대기는 여전히 빠집니다).",
            result="에이전트별 `runs` · `p50` · `p95` 표. 호스티드는 `cold` 수와 시작 지연 포함 총 시간이 나옵니다.",
            apply="앱이 부르는 에이전트 이름으로 바꿔 5분 · 1시간 단위 지연을 상시 확인하세요.",
        )
        + md("**에이전트 한 번 실행 = `invoke_agent` 스팬**입니다. 프롬프트 에이전트의 실행은 `dependencies`(역할 `responsesapi`)에, 호스티드 에이전트의 실행은 `requests`(역할 `agentsv2`)에 기록됩니다. 호스티드도 `dependencies`(`responsesapi`)에 `invoke_agent` · `chat` 스팬이 **함께** 남으므로, 아래 쿼리는 에이전트 이름으로 걸러 중복 없이 셉니다.")
        + walk(
            kqtext("prompt_runs_5min"),
            [
                (
                    "",
                    "프롬프트 에이전트의 실행 스팬 고르기 (kq 로 감싸서 실행)",
                    """
                    `dependencies` 테이블에서 최근 1시간(`ago(1h)`)의 행을 대상으로 합니다.
                    """,
                ),
                (
                    '| where cloud_RoleName == "responsesapi"',
                    "플랫폼이 남긴 ‘에이전트 실행’ 스팬만",
                    "`cloud_RoleName == \"responsesapi\"` — **플랫폼(Responses API)** 이 보낸 기록. `customDimensions[\"gen_ai.operation.name\"] == \"invoke_agent\"` — 스팬 속성(OpenTelemetry GenAI 규약)의 **작업 이름이 `invoke_agent`(에이전트 실행 전체)** 인 것. `customDimensions` 는 스팬에 붙은 속성 모음입니다.",
                ),
                (
                    '| where customDimensions["gen_ai.agent.name"]',
                    "이 에이전트의 것만",
                    "`gen_ai.agent.name` 속성이 `report-prompt-agent`(azure.yaml 의 이름)인 것만 남깁니다.",
                ),
                (
                    "| summarize runs",
                    "5분 단위 집계",
                    """
                    * `runs = count()` — 실행 **스팬** 수(재시도가 있으면 실제 호출 수보다 많을 수 있음)
                    * `failed = countif(success == false)` — 실패 횟수
                    * `p50_ms = round(percentile(duration, 50))` — **중앙값**(보통 걸리는 시간)
                    * `p95_ms` — **느린 쪽 꼬리**(95%)
                    * `max_ms` — 최댓값(`duration` 은 ms)
                    * `by bin(timestamp, 5m)` — **5분 단위로 묶기**
                    """,
                ),
                ("| order by timestamp desc", "최신순 정렬", "가장 최근 5분 구간이 맨 위에 옵니다."),
            ],
            cap="프롬프트 에이전트 — 5분 단위 실행 수 · 지연(ms) (queries.kql: prompt_runs_5min)",
            run="C2",
            lang="kql",
        )
        + exp(
            "C2a",
            read="이 5분 구간에 **8번 실행**, 실패 0, **중앙값 927ms** · p95 3089ms. p50 은 약 1초인데 p95 가 3초인 것은 **긴 질문(700자 답변)** 호출이 섞여서입니다.",
        )
        + walk(
            kqtext("hosted_runs_5min"),
            [
                (
                    "",
                    "호스티드 에이전트의 요청 스팬 고르기 (kq 로 감싸서 실행)",
                    "호스티드 에이전트의 한 번 실행은 **`requests` 테이블**에 기록됩니다. `cloud_RoleName == \"agentsv2\"`(플랫폼 · 호스티드 요청) 이고 에이전트 이름이 `report-maf-agent` 인 것만 고릅니다.",
                ),
                (
                    "| extend start_type",
                    "시작 방식과 ‘시작 지연’ 계산",
                    """
                    요청 스팬에는 플랫폼이 잰 **시작 지연 속성**이 자동으로 붙어 있습니다.
                    * `start_type` — **`cold`**(새로 띄움) 또는 **`warm`**(이미 떠 있음)
                    * `startup_ms` — **시작 지연 3단계의 합**: `platform_preprocessing_ms`(플랫폼 전처리) + `infra_setup_ms`(세션 샌드박스 준비) + `container_readiness_ms`(컨테이너 기동 대기). 값이 없으면 `coalesce(…, 0)` 이 0 으로 취급합니다(warm 은 대부분 0).
                    """,
                ),
                (
                    "| extend total_ms",
                    "서버가 본 총 시간 = 실행 + 시작 지연",
                    "`total_ms = duration + startup_ms`. 요청 스팬의 `duration` 에는 cold start 가 **빠져 있으므로** 시작 지연을 더해야 **서버가 관측한 총 시간**이 됩니다. 이 값은 클라이언트가 기다린 시간의 **근사(하한)** 입니다 — 네트워크 · SDK · 재시도 대기는 포함되지 않으므로 실제 사용자 시간은 앱의 `client_ms`(C7)로 재세요(B1 의 예: 클라이언트 9.998초 vs 플랫폼이 잰 8,149ms).",
                ),
                (
                    "| summarize runs",
                    "5분 단위 집계",
                    "`runs`(실행 수) · `cold`(cold 로 시작한 수) · `p50_total_ms` · `p95_total_ms`(시작 지연 포함) · `p50_run_ms`(시작 지연 **제외** 실행 시간)을 5분 단위로 묶습니다.",
                ),
                ("| order by timestamp desc", "최신순 정렬", "최근 구간이 위에 옵니다."),
            ],
            cap="호스티드 에이전트 — 5분 단위 실행 수 · cold 수 · 시작 지연 포함 총 시간(ms) (queries.kql: hosted_runs_5min)",
            run="C2",
            lang="kql",
        )
        + exp(
            "C2b",
            read="10번 실행 중 **5번이 cold**. **p50_run_ms 2120ms**(실행만)보다 **p50_total_ms 4377ms**(시작 지연 포함)가 큰 것은 **cold 호출이 섞인 영향**입니다(두 중앙값의 차이가 그대로 cold start 시간은 아닙니다 — 크기는 C3 의 평균으로 봅니다). cold 가 섞이면 **p95_total 이 11.4초**까지 올라갑니다.",
        ),
        scope="check",
    )

    c3 = step(
        "c3",
        "느린 호출은 어디서 느린가 — 모델 · 에이전트 런타임 · cold start",
        "C3",
        "느린 호출의 원인 구분 · 가이드 1 을 읽었다면: 가이드 1 의 C2(앱 vs AOAI 대조)에 해당",
        brief(
            what="느린 호출이 **모델 때문인지 · 에이전트 런타임 때문인지 · cold start 때문인지** 구분합니다.",
            why="‘응답이 느리다’는 신고를 받으면 먼저 **모델 때문인지, 에이전트 런타임(또는 cold start) 때문인지** 나눠야 합니다. 에이전트 실행 전체 시간에서 모델 호출 시간을 빼면 런타임이 쓴 시간이 남습니다. (가이드 1 을 읽었다면: 가이드 1 에서 ‘앱이 잰 시간 − AOAI 가 잰 시간’으로 하던 구분에 해당합니다.)",
            result="(프롬프트) 실행 − 모델 호출 = **런타임 오버헤드** 상위 10건, (호스티드) cold / warm 별 시작 지연 구성.",
            apply="‘응답이 느리다’는 신고가 오면 이 두 쿼리부터 보세요. 모델부터 의심하지 말고 **오버헤드 열**을 먼저 봅니다.",
        )
        + md(
            """
            - **프롬프트 에이전트**: `invoke_agent`(실행 전체) − `chat`(모델 호출) = **에이전트 런타임 오버헤드**. 정상일 때는 수백 ms 입니다.
            - **호스티드 에이전트**: 시작 지연 3단계(`platform_preprocessing · infra_setup · container_readiness`)와 컨테이너 응답 구간(`container_response`)까지 4개 구간으로 쪼갠 속성이 요청 스팬에 자동으로 붙습니다.
            """
        )
        + walk(
            kqtext("prompt_overhead"),
            [
                (
                    "",
                    "프롬프트 에이전트의 스팬을 모아 `spans` 로 이름 붙이기 (kq 로 감싸서 실행)",
                    "`let spans = …;` 는 **질의 결과에 이름을 붙이는 문법**입니다. 플랫폼(`responsesapi`)이 남긴 `report-prompt-agent` 의 스팬(실행 · 모델 호출 모두)을 최근 1시간 분량 모아 둡니다.",
                ),
                (
                    "=spans",
                    "실행 전체 스팬(invoke_agent)의 시간",
                    "`spans` 중 작업 이름이 **`invoke_agent`**(에이전트 실행 전체)인 것에서 `operation_Id`(= trace_id) · 시각 · `run_ms`(실행 시간)를 꺼냅니다.",
                ),
                (
                    "| join kind = inner",
                    "같은 trace 의 모델 호출(chat) 시간과 짝짓기",
                    "`join kind = inner … on operation_Id` — **같은 trace 안의 `chat` 스팬**(= 모델 호출, `model_ms`)과 이어 붙입니다. 같은 호출의 ‘실행 전체’와 ‘모델 호출’이 한 행에 놓입니다. **주의**: trace 하나에 `invoke_agent` 와 `chat` 이 하나씩 있는 정상 호출을 가정합니다. 재시도(C7)나 도구 호출로 한 trace 에 여러 개가 있으면 행이 늘어나 오버헤드가 정확하지 않으니, 운영에서는 스팬별 식별자로 짝짓거나 모델 호출 시간을 먼저 합산하세요.",
                ),
                (
                    "| extend overhead_ms",
                    "차이 = 런타임 오버헤드",
                    "`overhead_ms = run_ms − model_ms` — **모델이 쓴 시간을 뺀, 에이전트 런타임이 쓴 시간**입니다.",
                ),
                (
                    "| top 10 by overhead_ms desc",
                    "오버헤드가 큰 순서로 10건",
                    "`top 10 by overhead_ms desc` 로 **오버헤드가 큰 호출 10건**을 뽑고, 보기 좋게 반올림해(`round`) 시각 · trace_id · 세 시간을 보여 줍니다.",
                ),
            ],
            cap="프롬프트 에이전트 — 모델 시간을 뺀 오버헤드가 큰 실행 TOP 10 (queries.kql: prompt_overhead)",
            run="C3",
            lang="kql",
        )
        + exp(
            "C3a",
            read="""
            - `run_ms` = 실행 전체, `model_ms` = 모델 호출, **`overhead_ms` = 그 차이**입니다. 위 예에서 오버헤드는 **72~335ms** 로 정상 범위입니다.
            - 이번 검증에서 28건 중 **1건은 모델 호출이 1초 미만인데 실행 전체가 약 10초**였습니다(위 예시 출력에는 없는 다른 실행). 그 차이가 이 열에 그대로 나타나며, 원인은 모델이 아니라 **에이전트 런타임**입니다.
            """,
        )
        + walk(
            kqtext("hosted_cold_vs_warm"),
            [
                (
                    "",
                    "호스티드 에이전트의 요청 스팬만 (kq 로 감싸서 실행)",
                    "`requests` 에서 `agentsv2` 가 남긴 `report-maf-agent` 의 요청 스팬을 최근 1시간 분량 고릅니다.",
                ),
                (
                    "| summarize runs",
                    "cold / warm 별로 시작 지연 단계의 평균 구하기",
                    """
                    `by start_type = tostring(customDimensions["hosted_agent.latency.start_type"])` — **`cold` 와 `warm` 으로 나눠서** 각각 평균을 냅니다.
                    * `preprocess_ms` — 플랫폼 전처리
                    * `infra_ms` — **세션 샌드박스 준비**
                    * `readiness_ms` — **컨테이너 기동 대기** (각각 `coalesce(todouble(…), 0.0)` 로 값이 없으면 0 취급 후 `avg`)
                    * `run_ms` — 실행 시간(`duration`) 평균
                    * `runs` — 실행 수
                    """,
                ),
            ],
            cap="호스티드 에이전트 — cold / warm 별 시작 지연 구성(평균 ms) (queries.kql: hosted_cold_vs_warm)",
            run="C3",
            lang="kql",
        )
        + exp(
            "C3b",
            read="**cold**: `infra_ms` 1252 + `readiness_ms` 5867 ≈ **7.1초**가 시작 지연이고, **warm** 은 `infra` · `readiness` 가 **0** 입니다. 같은 에이전트라도 cold 인지 warm 인지에 따라 클라이언트가 겪는 시간이 이렇게 달라집니다.",
        )
        + call(
            "info",
            "읽는 법",
            f"""
            - 호스티드 `cold` 의 시간은 대부분 **infra_setup(세션 샌드박스 준비) + container_readiness(컨테이너 기동)** — 합치면 약 {m['cold_startup_s']}초 — 이고, 모델 호출은 그 뒤 1초 안팎입니다.
            - 프롬프트 에이전트는 대부분 오버헤드가 수백 ms 이하입니다. 그런데 이 가이드를 실행하며 만든 프롬프트 에이전트 호출 {m['prompt_runs']}건 중 {m['prompt_outliers']}건은 **모델 호출은 1초 미만(정상)인데 실행 전체가 약 {m['prompt_outlier_s']}초**였습니다. 원인은 모델이 아니라 에이전트 런타임입니다(한동안 호출이 없다가 들어온 첫 호출이었다는 점 외에 재현 조건은 확인하지 못했습니다). **느린 호출을 만나면 모델 쪽부터 의심하지 말고 이 열부터 보세요.**
            - 같은 대화를 재사용하면(`invoke_agents.py … same`) **첫 호출만 cold** 였습니다(실측). 오래 쉰 뒤에 다시 cold 가 되는지는 측정하지 않았으니, **세션 재사용 방식이 지연에 영향을 준다**는 점까지만 확인한 것으로 보세요.
            """,
        ),
        scope="check",
    )

    c4 = step(
        "c4",
        "요청 한 건 따라가기 — trace_id · 응답 ID",
        "C4",
        "요청 한 건의 서버 기록 따라가기 · 가이드 1 을 읽었다면: 가이드 1 의 C2 요청 단위 조인에 해당",
        brief(
            what="호출 한 건의 **전체 흐름**(플랫폼 스팬 · 컨테이너 스팬 · 컨테이너 로그)을 trace_id 한 개로 시간순으로 따라갑니다. trace_id 를 잃어버렸다면 **응답 ID** 로도 찾습니다.",
            why="클라이언트가 `traceparent` 로 정한 `trace_id` 는 서버 쪽 **모든 스팬 · 컨테이너 로그의 `operation_Id`** 입니다. 그래서 **trace_id 하나로 이 호출의 서버 기록 전체**를 찾을 수 있습니다. (가이드 1 을 읽었다면: `apim-request-id` 로 앱과 AOAI 기록을 짝짓던 일을 헤더 한 줄이 대신합니다.)",
            result="호스티드 에이전트 첫 호출(= cold)의 서버 쪽 기록이 시간순으로 나열됩니다.",
            apply="사용자가 ‘이 요청이 느렸다’고 알려 주면 **trace_id 또는 응답 ID** 만 받아서 서버 기록 전체를 조회하세요.",
        )
        + walk(
            kqtext("trace_by_id", extra="TID=$(grep report-maf-agent calls.jsonl | head -1 | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())[\"trace_id\"])')\n", placeholder=("<trace_id>", "$TID")),
            [
                (
                    "TID=",
                    "첫 호스티드 호출의 trace_id 꺼내기",
                    "`grep report-maf-agent calls.jsonl | head -1` 은 호출 기록 파일에서 **호스티드 에이전트의 첫 호출**(= cold start 가 있었던 호출)의 줄이고, 짧은 Python 이 `trace_id` 만 꺼내 `TID` 에 담습니다.",
                ),
                (
                    'kq "$(sed',
                    "KQL 의 자리 표시자를 trace_id 로 바꿔 실행",
                    """
                    `kq "$(sed "s/<trace_id>/$TID/" <<'KQL' … KQL )"` 는 **쿼리 안의 `<trace_id>` 를 `TID` 값으로 바꿔서** `kq` 에 넘기는 셸 표현입니다.
                    * `<<'KQL' … KQL` — 그 사이의 줄들을 **그대로 `sed` 의 입력으로 넘기는 셸 문법(heredoc)**. 쿼리 본문은 두고 `<trace_id>` 자리만 값으로 갈아 끼우려는 것입니다.
                    * `sed "s/<trace_id>/$TID/"` — 자리 표시자를 값으로 치환
                    * `"$( … )"` — 치환된 결과를 `kq` 의 인자로 전달
                    * `let tid = "<trace_id>";` — KQL 에서 **변수 `tid` 를 정의**(치환된 trace_id)
                    """,
                ),
                (
                    "union requests, dependencies, traces",
                    "세 테이블에서 이 trace 의 행만",
                    "`union requests, dependencies, traces` 로 **세 테이블을 합치고**, `where operation_Id == tid` 로 **이 trace_id 의 행만** 남깁니다. 플랫폼 스팬 · 컨테이너 스팬 · **컨테이너 로그(traces)** 가 한 줄기로 모입니다.",
                ),
                (
                    "| project timestamp",
                    "보여 줄 열 · 시간순",
                    "시각 · 종류(`itemType`) · 역할 · **이름**(스팬 이름 또는 로그 메시지 앞 80자, `coalesce(name, substring(message, 0, 80))`) · 걸린 시간 · 성공 여부를 시간순으로 보여 줍니다.",
                ),
            ],
            cap="trace_id 한 건 — 플랫폼 · 컨테이너 스팬과 컨테이너 로그를 시간순으로 (queries.kql: trace_by_id)",
            run="C4",
            lang="kql",
        )
        + exp(
            "C4a",
            read="""
            - 위에서 아래로 **시간 순서**입니다. `/readiness` 로그 → **`request agentsv2 invoke_agent`**(플랫폼이 본 호스티드 요청, 3003ms) → `POST /responses` 수신 → 컨테이너가 **`invoke_agent`** → **`chat gpt-5.4-mini`**(모델 호출 1977ms) 순으로 이어집니다.
            - `role` 열로 **누가 남긴 기록인지**(플랫폼 `agentsv2` vs 컨테이너 `report-maf-agent`)가 구분됩니다. `trace` 행은 컨테이너 로그 메시지입니다.
            - 이 표의 `TID` 는 호스티드 첫 호출(= cold start)로 고정돼 있습니다. 다른 호출을 보려면 구간 1 의 `TID=` 줄을 그 trace_id 로 바꾸세요(C7 의 ‘직접 해 보기’). **cold start 약 7초는 이 표에 행으로 나오지 않고** C3 의 `hosted_cold_vs_warm`(요청 스팬의 속성)에만 있습니다.
            """,
        )
        + md("trace_id 를 잃어버렸다면 클라이언트가 받은 **응답 ID**(프롬프트 `resp_…` · 호스티드 `caresp_…`)로도 찾을 수 있습니다.")
        + walk(
            kqtext("response_lookup", extra="RID=$(grep report-prompt-agent calls.jsonl | tail -1 | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())[\"response_id\"])')\n", placeholder=("<response_id>", "$RID")),
            [
                (
                    "RID=",
                    "프롬프트 에이전트 마지막 호출의 응답 ID 꺼내기",
                    "호출 기록 파일에서 `report-prompt-agent` 의 **마지막 호출**(`tail -1`)의 `response_id` 를 `RID` 에 담습니다.",
                ),
                (
                    'kq "$(sed',
                    "자리 표시자를 응답 ID 로 바꿔 실행",
                    "앞과 같은 방식으로 `<response_id>` 를 `RID` 값으로 바꾼 KQL 을 실행합니다. `let rid = \"<response_id>\";` 가 KQL 변수입니다.",
                ),
                (
                    "union requests, dependencies",
                    "응답 ID 가 같은 스팬 찾기",
                    "`requests` 와 `dependencies` 에서 **`gen_ai.response.id`**(프롬프트 에이전트 스팬의 응답 ID 속성) 또는 **`azure.ai.agentserver.response_id`**(호스티드 요청 스팬의 응답 ID 속성)가 `rid` 와 같은 행을 찾습니다.",
                ),
                (
                    "| project timestamp",
                    "보여 줄 열",
                    "시각 · 종류 · 역할 · 이름 · 걸린 시간 · **trace_id**(`operation_Id`)를 보여 줍니다. 응답 ID 로 **trace_id 를 되찾을 수 있습니다.**",
                ),
            ],
            cap="응답 ID 로 서버 쪽 기록 찾기 (queries.kql: response_lookup)",
            run="C4",
            lang="kql",
        )
        + exp("C4b", read="응답 ID 하나로 **같은 trace 의 두 스팬**(`invoke_agent report-prompt-agent:1` 2576ms · `chat gpt-5.4-mini` 2241ms)이 나옵니다. 오른쪽 `trace_id` 가 C4 첫 쿼리의 키입니다."),
        scope="check",
    )

    c5 = step(
        "c5",
        "토큰 · 모델 쪽 메트릭",
        "C5",
        "토큰 수 · 모델 메트릭 · 가이드 1 을 읽었다면: 가이드 1 의 R1(토큰) · R2(메트릭)에 해당",
        brief(
            what="토큰 수는 **플랫폼 `chat` 스팬**에서, 모델 쪽 서비스 메트릭(요청 수 · 토큰 · 응답 완료 시간)은 **Foundry 리소스의 메트릭**에서 봅니다.",
            why="토큰 사용량은 비용 · 한도(429)와 직결되고, 모델 쪽 메트릭(요청 수 · 응답 완료 시간)은 **서비스 전체 추세**를 보여 줍니다. 여기서는 **별도 설정 없이** 둘 다 이미 쌓여 있습니다(메트릭 정의 99개). (가이드 1 을 읽었다면: 토큰은 AOAI 진단 로그의 `properties_s` 에서, 메트릭은 R2 로 조회하던 것입니다.)",
            result="에이전트 · 모델별 시간당 토큰 사용량 표, 5분 단위 메트릭 값.",
            apply="요청별 **서비스 로그**(`RequestResponse` 등)까지 필요할 때만 Foundry 리소스에 진단 설정을 추가하세요(가이드 1 의 R1 방식 — 범주 이름은 확인하세요. 이 가이드는 적용하지 않았습니다).",
        )
        + walk(
            kqtext("tokens_by_agent"),
            [
                (
                    "",
                    "모델 호출(chat) 스팬 모으기 (kq 로 감싸서 실행)",
                    "플랫폼(`responsesapi`)이 남긴 **`chat` 스팬**(= 모델 호출)을 최근 24시간 분량 고릅니다. 토큰 수 · 모델 이름이 이 스팬의 속성에 있습니다.",
                ),
                (
                    "| summarize calls",
                    "에이전트 · 모델 · 시간(1시간)별로 집계",
                    """
                    * `calls` — 호출 수
                    * `input_tokens` · `output_tokens` — `gen_ai.usage.input_tokens` / `output_tokens` 속성의 **합계**(`toint` 로 숫자 변환)
                    * `avg_model_ms` — 모델 호출 평균 시간
                    * `by agent, model, bin(timestamp, 1h)` — **에이전트 이름 · 응답한 모델 이름(`gen_ai.response.model`) · 1시간 단위**로 묶기
                    """,
                ),
                ("| order by timestamp desc", "최신순 정렬", "최근 구간이 위에 옵니다."),
            ],
            cap="에이전트 · 모델별 시간당 토큰 사용량 (queries.kql: tokens_by_agent)",
            run="C5",
            lang="kql",
        )
        + exp(
            "C5a",
            read="에이전트 · 시간 구간별로 **호출 수 · 입력/출력 토큰 · 평균 모델 시간**이 나옵니다. 모델 이름에 **날짜 버전(`…-2026-03-17`)** 까지 붙어 있어 **어떤 모델 버전이 응답했는지** 알 수 있습니다. 호스티드의 입력 토큰이 큰 것(1381)은 `same` 대화 재사용으로 앞선 대화가 입력에 포함되어서입니다. 예시의 `01:00` 구간 4건은 이 가이드의 이후 단계(D2)에서 만든 호출이 섞인 것이라, B 단계까지만 했다면 호스티드 10건 · 프롬프트 8건이 보입니다.",
        )
        + walk(
            """ACCT_ID=$(az cognitiveservices account show -g "$AZURE_RESOURCE_GROUP" -n "$AZURE_AI_ACCOUNT_NAME" --query id -o tsv)
az monitor metrics list --resource "$ACCT_ID" --metric AzureOpenAIRequests ProcessedPromptTokens GeneratedTokens AzureOpenAITTLTInMS \\
  --interval PT5M --offset 1h --aggregation Total Average -o json | python3 -c '
import json, sys
for m in json.load(sys.stdin)["value"]:
    pts = [(p["timeStamp"][11:16], round(p["total"]), round(p["average"])) for p in m["timeseries"][0]["data"] if p.get("total")]
    print(m["name"]["value"].ljust(24), pts[:6])'""",
            [
                (
                    "ACCT_ID=",
                    "Foundry 계정의 리소스 ID",
                    "메트릭은 **리소스 단위**로 쌓이므로 대상(Foundry 계정)의 리소스 ID 가 필요합니다.",
                ),
                (
                    "az monitor metrics list",
                    "메트릭 4종 조회 — 5분 단위, 최근 1시간",
                    """
                    * `--metric AzureOpenAIRequests ProcessedPromptTokens GeneratedTokens AzureOpenAITTLTInMS` — **요청 수 · 입력(처리한 프롬프트) 토큰 · 출력(생성한) 토큰 · 응답 완료 시간(ms)**
                    * `--interval PT5M --offset 1h` — **5분 단위**로 **최근 1시간**(`PT5M` 은 ISO 8601 기간 표기)
                    * `--aggregation Total Average` — **합계와 평균** 두 가지
                    * `-o json | python3 -c '…'` — JSON 으로 받아 짧은 Python 이 보기 좋게 정리합니다.
                    """,
                ),
                (
                    "import json, sys",
                    "Python 으로 정리해 출력",
                    "각 메트릭마다 **값이 있는 5분 구간**만 골라 `(시각 HH:MM, 합계, 평균)` 으로 만들고(`p[\"timeStamp\"][11:16]` 이 시각 부분), 앞 6개를 한 줄로 출력합니다.",
                ),
            ],
            cap="Foundry 리소스의 모델 메트릭 — 설정 없이 조회 (시각 · 합계 · 평균). 메트릭은 7~10분 늦게 보입니다",
            run="C5",
        )
        + exp(
            "C5b",
            read="각 줄이 메트릭 하나이고, 괄호 안이 `(시각 UTC, 합계, 평균)` 입니다. 예: `AzureOpenAIRequests ('00:59', 13, 1)` = 00:59 구간에 요청 **13건**. `ProcessedPromptTokens` · `GeneratedTokens` 가 입력 · 출력 토큰, `AzureOpenAITTLTInMS` 가 응답 완료 시간 합계/평균(ms)입니다(합계보다 **평균**이 읽기 좋은 값입니다). 출력이 **`[]` 로 비어 있으면** 메트릭이 7~10분 늦게 보이기 때문이니 잠시 뒤 다시 실행하세요.",
        ),
        scope="check",
    )

    c6 = step(
        "c6",
        "포털에서 보는 곳",
        "C6",
        "화면 확인은 이 가이드에서 하지 못했습니다 — 문서 기준",
        brief(
            what="같은 데이터를 **Foundry 포털**(https://ai.azure.com)이 어디서 보여 주는지 정리합니다.",
            why="CLI 와 KQL 에 익숙하지 않은 담당자는 포털에서 같은 정보를 볼 수 있습니다.",
            result="‘보고 싶은 것 → 포털 위치 → 이 가이드의 대응’ 표.",
            caution="이 가이드의 실습 계정으로는 **포털 화면까지 열어 보지 못했고**, 데이터가 같은 Application Insights 에 있다는 것까지만 확인했습니다. 아래 위치는 문서 기준입니다.",
        )
        + "<table class=\"nw\"><thead><tr><th>보고 싶은 것</th><th>Foundry 포털 위치 (New Foundry)</th><th>이 가이드의 대응</th></tr></thead><tbody>"
        "<tr><td>요청 한 건의 단계별 스팬 · 입출력 · 도구 호출</td><td>프로젝트 → <b>Agents → Traces</b> (90일 · Conversation 상세)</td><td>C4 <code>trace_by_id</code></td></tr>"
        "<tr><td>에이전트별 토큰 · 지연 · 실행 성공률</td><td>Build → 에이전트 → <b>Monitor</b> 탭 (프리뷰)</td><td>C2 · C5 쿼리</td></tr>"
        "<tr><td>알림(지연 · 토큰 · 평가 점수)</td><td>Monitor → 설정(톱니) → <b>Alerts</b> (프리뷰)</td><td>D1 <code>alerts.sh</code> (KQL 알림)</td></tr>"
        "<tr><td>여러 프로젝트 · 에이전트 한눈에</td><td>우측 상단 <b>Operate</b> → Overview · Assets</td><td>—</td></tr>"
        "</tbody></table>"
        + call(
            "warn",
            "트레이스를 보려면 권한이 따로 필요합니다",
            "포털에서 트레이스를 보려면 **연결된 Application Insights 에 대한 Log Analytics Reader** 가 있어야 하고, 호출하려면 **Foundry User**(구 Azure AI User) 역할이 있어야 합니다. `connect-appinsights.sh` 가 부여하는 것은 **호출하는 나에게 Foundry User**(프로젝트 범위)와 **프로젝트 관리 ID 에게 Log Analytics Reader** 입니다. **포털에서 트레이스를 볼 다른 사용자에게는 Log Analytics Reader 를 따로** 주어야 합니다(이 실습 계정은 구독 소유자라 별도 설정 없이 조회됩니다).",
        ),
        scope="check",
    )
    c7 = foundry_app.build_c7()
    sec_c = section("c", "C · 확인과 분석", "트레이스가 들어왔는지, 어디서 느린지, 서버에 없는 시간은 무엇인지를 확인합니다", c1 + c2 + c3 + c4 + c5 + c6 + c7)
    return sec_b + sec_c
