# -*- coding: utf-8 -*-
# D · 알림 · 장애 재현 / E · 정리와 판단 / 부록 (Foundry 에이전트 모니터링 가이드)
from lib import *
import foundry_a
import foundry_app
from foundry_a import OLD, OLD_TOTAL, NEW, NEW_TOTAL, OLD_RESOURCES, NEW_RESOURCES, AGENT_LINES, CLIENT_LINES, YAML_LINES, HOOK_LINES, PCT
from foundry_b import exp, kqtext


def build():
    m = foundry_a.measured()

    # ───────────────── D. 알림 · 장애 재현
    alerts_walk = walk(
        fd("scripts/alerts.sh"),
        [
            (
                "#!/bin/sh",
                "스크립트 시작 — 목적과 주의",
                """
                위 주석이 목적입니다: **알림 2개**(느린 실행 · 실패한 실행). 사용법은 `MAIL=<수신 이메일> sh scripts/alerts.sh`. 두 번째 주석은 설계 이유입니다 — 텔레메트리가 늦게 도착해도 놓치지 않도록 **평가 창(15분)을 평가 주기(5분)보다 길게** 잡았고, 그래서 같은 사건이 **최대 3번** 평가됩니다.
                `set -eu` 는 처리되지 않은 명령 실패에서 중단하고(`-e`), 정의하지 않은 변수를 쓰면 오류(`-u`)입니다.
                """,
            ),
            (
                "RG=",
                "대상 Application Insights 찾기",
                "`AZURE_RESOURCE_GROUP` · `AZURE_ENV_NAME` 은 **azd 환경 값**(A3 에서 `foundry.env` 에 저장·적용)이고, `az monitor app-insights component show … --query id` 가 **Application Insights 의 리소스 ID** 를 알려 줍니다. 알림이 감시할 대상(`APPI_ID`)입니다.",
            ),
            (
                "az monitor action-group create",
                "수신 그룹(액션 그룹) 만들기",
                """
                알림이 울리면 **누구에게 알릴지**를 정합니다.
                * `-n ag-agent-latency --short-name agentlat` — 이름과 짧은 이름
                * `--action email owner "$MAIL"` — **이메일 수신자** 한 명(`MAIL` 은 스크립트를 실행할 때 `MAIL=… sh …` 로 넘긴 값, `owner` 는 별칭)
                * 아래 `AG=$(…)` 는 만들어진 그룹의 **리소스 ID** 를 담습니다.
                """,
            ),
            (
                "SLOW=$(cat",
                "‘느린 실행’ 알림용 KQL — 시작 지연을 더한 총 시간이 8초 초과",
                """
                `SLOW=$(cat <<'KQL' … KQL )` 은 **KQL 여러 줄을 `SLOW` 변수에 담는** 셸 표현입니다.
                * `let hosted = requests | … | distinct agent = …` — **호스티드 에이전트의 이름 목록**(`agentsv2` 요청이 있는 에이전트)
                * `union ( … ), ( … )` — 두 종류의 ‘실행 시간’을 한 목록으로:
                  - **호스티드**: `requests` 의 `invoke_agent` 스팬 시간 `duration` + **cold start 3단계**(`platform_preprocessing_ms` · `infra_setup_ms` · `container_readiness_ms`) = **서버가 본 총 시간**(클라이언트가 기다린 시간의 하한 — 네트워크 · SDK 는 빠짐)
                  - **프롬프트**: `dependencies` 의 `invoke_agent` 스팬 `duration`. 단 `!in (hosted)` 로 **호스티드 에이전트는 제외**합니다. 플랫폼은 호스티드 에이전트의 실행도 `dependencies` 에 `invoke_agent` 스팬으로 남기는데(C2), 그 시간에는 cold start 가 들어 있지 않으므로 호스티드는 위의 `requests` 쪽(실행 시간 + cold start)만 쓰고 **같은 실행이 두 번 세어지지 않게** 합니다.
                * `| where total_ms > 8000` — **총 시간이 8초(8000ms)를 넘는** 실행만 남김 → 이 행이 **1건이라도 있으면** 알림

                **계산 예(설명용 숫자)**: 호스티드 실행 `duration` 2.1초 + cold start 7.1초(3단계 합) = **총 9.2초 → 8초 초과 → 행 1건 → 알림**. 같은 에이전트가 warm 이라 cold start 가 거의 없으면 총 2.1~2.2초라 알림이 울리지 않습니다.
                """,
            ),
            (
                "FAILED=",
                "‘실패한 실행’ 알림용 KQL",
                "`dependencies` 중 **`success == false`** 이고 **GenAI 스팬**(`gen_ai.operation.name` 속성이 있는 것 = 에이전트 · 모델 호출)인 것입니다. 호스티드 에이전트의 실행 중 실패는 **`requests` 가 아니라 `dependencies` · `exceptions` 에 남기 때문에**(D3) `dependencies` 를 봅니다. **주의**: 실패한 *시도*마다 스팬이 하나 생기므로, 429 가 한 번 나고 SDK 재시도가 **성공한 호출**도 실패 스팬 1건이 남아 이 알림이 울릴 수 있습니다(C7 표 2). ‘최종 실패’만 보려면 앱 최소 기록(C7)의 `status` 를 쓰세요.",
            ),
            (
                "az monitor scheduled-query create -g \"$RG\" -n agent-run-slow",
                "로그 알림 ① agent-run-slow",
                """
                `scheduled-query` 는 **정해진 주기로 KQL 을 실행해 결과를 보는 알림**입니다.
                * `--scopes "$APPI_ID"` — 이 Application Insights 에서 질의
                * `--action-groups "$AG"` — 울리면 위 수신 그룹으로 알림
                * `--condition "count 'Q' > 0" --condition-query Q="$SLOW"` — 질의 `Q`(= `SLOW`)의 **결과 행이 1개 이상**이면 울림
                * `--window-size 15m --evaluation-frequency 5m` — **5분마다**, **최근 15분**을 평가
                * `--severity 3` — 심각도 3(정보)
                """,
            ),
            (
                "az monitor scheduled-query create -g \"$RG\" -n agent-run-failed",
                "로그 알림 ② agent-run-failed",
                "같은 방식으로 `FAILED` 질의를 감시합니다. 실패는 더 중요하므로 **심각도 2(경고)** 입니다.",
            ),
        ],
        cap="foundry/scripts/alerts.sh",
        lang="bash",
    )
    d1_run = walk(
        """MAIL="<알림 받을 이메일>" sh scripts/alerts.sh
az monitor scheduled-query list -g "$AZURE_RESOURCE_GROUP" --query "[].{name:name, every:evaluationFrequency, window:windowSize, severity:severity}" -o table""",
        [
            (
                "MAIL=",
                "알림 만들기 — 수신 메일은 MAIL 로 넘김",
                "`MAIL=… sh scripts/alerts.sh` 는 **이 한 번의 실행에만** `MAIL` 환경변수를 주고 스크립트를 실행합니다. `<알림 받을 이메일>` 을 본인 메일로 바꿔 넣으세요(꺾쇠는 지웁니다). `azd` 환경 값(`AZURE_RESOURCE_GROUP` 등)은 A3 에서 이미 적용되어 있습니다.",
            ),
            (
                "az monitor scheduled-query list",
                "만들어진 알림 확인",
                "리소스 그룹의 로그 알림을 **이름 · 평가 주기(`every`) · 평가 창(`window`) · 심각도**로 나열합니다.",
            ),
        ],
        cap="알림 만들기 (수신 메일은 MAIL)",
        run="D1",
    )
    d1 = step(
        "d1",
        "알림 2개 만들기 — 느린 실행 · 실패한 실행",
        "D1",
        f"소요 약 {m['alerts_s']}초 · 가이드 1 을 읽었다면: R8 에 해당",
        brief(
            what="Application Insights 를 대상으로 하는 **로그 알림 2개**(느린 실행 · 실패한 실행)와 **수신 그룹**을 만듭니다.",
            why="장애를 사람이 매번 쿼리로 찾지 않도록, **조건이 충족되면 메일로 알려 주게** 합니다. 느린 실행은 **cold start 시간을 더한 총 시간이 8초를 넘는** 실행, 실패한 실행은 **실패한 GenAI 스팬**입니다.",
            result="알림 규칙 `agent-run-slow`(심각도 3) · `agent-run-failed`(심각도 2) 와 수신 그룹. 5분마다 최근 15분을 평가합니다.",
            apply="수신 이메일 · 임계값(8초) · 평가 주기를 **운영 기준에 맞게** 바꾸세요. 호스티드 에이전트는 cold start 를 포함해 계산하므로 **새 대화(cold)마다 정상이어도 알림에 걸립니다**(아래 상자). 포털의 Alerts(프리뷰)도 있으나 이 가이드에서는 확인하지 못했습니다.",
        )
        + alerts_walk
        + d1_run
        + exp("D1", read="두 규칙이 **5분마다(`Every 0:05:00`) 최근 15분(`Window 0:15:00`)** 을 평가합니다. 심각도 `3` = agent-run-slow, `2` = agent-run-failed 입니다.")
        + call(
            "info",
            "알림 메일을 받으려면 ‘수신자 확인’이 필요합니다",
            """
            수신 그룹에 **처음 쓰는 이메일 주소**를 추가하면 Azure 가 그 주소로 **확인 메일**(OTP — 일회용 코드)을 보냅니다(스팸함도 보세요). 문서 기준으로 **약 30분 안에** 확인을 마쳐야 하고, 마치기 전에는 알림 메일이 오지 않을 수 있습니다. 같은 테넌트에서 이미 확인한 주소는 다시 확인하지 않습니다. 이 가이드에서는 **메일 도착을 확인하지 못했고**, 알림이 울렸는지는 D3 의 알림 목록(`Fired`)으로 확인했습니다.
            """,
        )
        + call(
            "warn",
            "호스티드는 cold 호출마다 ‘느린 실행’ 알림 조건에 걸립니다",
            "이 임계값(8초)은 cold start 시간을 더해서 계산하므로, 호스티드 에이전트는 **정상 동작인 cold 호출도** 조건에 걸립니다. 운영에서는 임계값을 높이거나 cold 호출을 제외한 지연을 따로 보세요. 같은 사건이 최대 3번 평가되지만 메일이 몇 통 오는지는 확인하지 못했습니다(재알림 설정에 따라 다를 수 있습니다).",
        ),
        scope="apply",
    )

    d2 = step(
        "d2",
        "장애 만들기 — 느린 실행 · 실패한 실행",
        "D2",
        "소요 약 4분",
        brief(
            what="알림이 울리는지 보려고 **일부러 두 가지**를 만듭니다. ① 호출마다 새 세션을 만들어 **cold start 로 느린 실행**, ② 호스티드 에이전트의 **모델 배포 이름에 오타**를 내고 새 버전을 배포해 **실패하는 실행**(‘없는 배포 이름 → 404’ 처럼 흔한 실수).",
            why="알림이 **실제로 울리는지**, 그리고 실패가 트레이스에 **어떤 모양으로** 남는지(D3)를 보려는 것입니다.",
            result="느린 호출 3건(약 8~12초)과 **실패한 호출 3건**(`status: failed`).",
            apply="실습 환경에서만 하세요. 운영 에이전트의 배포 이름을 바꾸면 **실제로 장애가 납니다.**",
        )
        + walk(
            """python invoke_agents.py report-maf-agent 3 short new | tee -a calls.jsonl                  # ① 느린 실행 (cold start)
azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME no-such-deployment                                  # ② 오타 난 배포 이름으로
azd deploy report-maf-agent                                                                    #    새 버전 배포 (약 1분)
python invoke_agents.py report-maf-agent 3 short new | tee -a calls.jsonl                  #    호출 → 실패""",
            [
                (
                    "python invoke_agents.py report-maf-agent 3 short new",
                    "① 느린 실행 만들기 — 매번 새 대화(cold start) 3번",
                    "`new` 이므로 호출마다 컨테이너를 새로 띄워 **8초를 넘는 느린 실행**이 3번 생깁니다. `agent-run-slow` 알림이 노리는 상황입니다.",
                ),
                (
                    "azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME",
                    "② 배포 이름을 일부러 오타로",
                    "`azd env set` 으로 azd 환경 값 `AZURE_AI_MODEL_DEPLOYMENT_NAME` 을 **존재하지 않는 이름**(`no-such-deployment`)으로 바꿉니다. 이 값은 `azure.yaml` 의 `env` 를 거쳐 컨테이너의 환경변수가 되고 `main.py` 가 모델 이름으로 씁니다.",
                ),
                (
                    "azd deploy report-maf-agent",
                    "새 버전 배포 (약 1분)",
                    "`azd deploy <서비스>` 는 **인프라는 그대로 두고 그 에이전트만 다시 배포**합니다. 환경변수가 바뀐 **새 버전**(버전 2)이 만들어집니다.",
                ),
                (
                    "python invoke_agents.py report-maf-agent 3 short new | tee -a calls.jsonl                  #    호출 → 실패",
                    "③ 호출 → 실패",
                    "에이전트가 존재하지 않는 모델 배포를 부르려다 **실패**합니다. 이번에는 `status` 가 `failed` 로 나옵니다(아래 알림 상자).",
                ),
            ],
            cap="느린 호출 3번 → 오타 난 버전 배포 → 실패하는 호출 3번",
            run="D2",
        )
        + exp(
            "D2",
            read="""
            - 앞 3줄: 정상(`completed`)이지만 **8.6~11.6초**(cold start) — 느린 실행입니다.
            - `SUCCESS: … deployed … in 1 minute` — 오타 버전 배포.
            - 뒤 3줄: **`status: "failed"`**, `input_tokens`/`output_tokens` 가 `null`, 오류는 `An internal server error occurred.` 한 줄뿐입니다. 그런데도 시간은 **8~10초 걸렸습니다.**
            """,
        )
        + call(
            "warn",
            "D4 에서 복구할 때까지 호스티드 에이전트는 실패합니다",
            "이 단계로 호스티드 에이전트의 모델 배포 이름이 **일부러 틀린 버전**이 됩니다. D4 에서 되돌리기 전에는 호출이 계속 실패하니, **그동안 B · C 단계의 호출은 하지 마세요.** 복구가 필요 없으면 D4 를 건너뛰고 바로 삭제(E2)해도 됩니다.",
        )
        + call(
            "warn",
            "실패해도 HTTP 는 200 입니다",
            "호스티드 에이전트가 모델 호출에 실패해도 응답은 **HTTP 200 + `status: failed`** 이고 오류 메시지는 `An internal server error occurred.` 한 줄뿐입니다. 진짜 원인(`DeploymentNotFound`)은 **서버 트레이스에서만** 보입니다 — 클라이언트 로그만으로는 알 수 없습니다.",
        ),
        scope="check",
    )

    d3_wait = walk(
        """SUB_ID=$(az account show --query id -o tsv)
for i in $(seq 1 40); do
  az rest --method get --url "https://management.azure.com/subscriptions/$SUB_ID/providers/Microsoft.AlertsManagement/alerts?api-version=2019-05-05-preview&targetResourceGroup=$AZURE_RESOURCE_GROUP" \\
    --query "value[].{rule:properties.essentials.alertRule, state:properties.essentials.monitorCondition, severity:properties.essentials.severity, fired:properties.essentials.startDateTime}" -o tsv | sed 's#.*/scheduledqueryrules/##' > alerts.txt
  [ "$(grep -c Fired alerts.txt)" -ge 2 ] && break; sleep 30
done
cat alerts.txt""",
        [
            ("SUB_ID=", "구독 ID 알아내기", "알림 조회 REST API 주소에 들어갈 **구독 ID** 를 `SUB_ID` 에 담습니다."),
            (
                "for i in $(seq 1 40)",
                "알림이 2개 울릴 때까지 30초 간격으로 확인 (최대 20분)",
                """
                `seq 1 40` 만큼(최대 40번 × 30초 = 20분) 반복합니다.
                * `az rest --method get --url …/providers/Microsoft.AlertsManagement/alerts?…&targetResourceGroup=…` — **이 리소스 그룹에서 울린 알림 목록**(알림 관리 REST API)
                * `--query "value[].{rule, state, severity, fired}" -o tsv` — 규칙 이름 · 상태 · 심각도 · 시작 시각만 탭으로 구분해 출력
                * `sed 's#.*/scheduledqueryrules/##' > alerts.txt` — 규칙의 긴 리소스 경로에서 **이름만 남겨** 파일에 저장
                * `[ "$(grep -c Fired alerts.txt)" -ge 2 ] && break` — **`Fired` 가 2개 이상**(두 알림 모두 울림)이면 반복 종료
                """,
            ),
            ("cat alerts.txt", "결과 출력", "마지막으로 저장된 알림 목록을 출력합니다."),
        ],
        cap="① 울린 알림 (30초 간격으로 확인)",
        run="D3",
    )
    d3 = step(
        "d3",
        "알림 확인 · 실패 원인 보기",
        "D3",
        "알림은 장애를 만든 뒤 보통 5~6분 안에 울립니다 (최대 약 20분 대기)",
        brief(
            what="알림이 울릴 때까지 기다린 뒤, 알림이 가리키는 **실패를 트레이스에서 찾아봅니다.** 실패한 실행은 `requests` 가 아니라 **`dependencies` · `exceptions`** 에 남습니다.",
            why="‘실패했다’는 알림만으로는 **왜** 실패했는지 알 수 없습니다. 클라이언트에는 `An internal server error occurred.` 한 줄뿐이므로, **진짜 원인은 서버 트레이스에서** 찾아야 합니다.",
            result="울린 알림 2개, 실패한 호출의 스팬과 예외, 그리고 원인(`404 DeploymentNotFound`).",
            apply="실패 알림 쿼리는 **`requests.success` 가 아니라 `dependencies.success == false`** 를 보세요(③ 쿼리가 이유를 보여 줍니다).",
        )
        + d3_wait
        + exp("D3a", read="두 알림이 모두 **`Fired`**(울림)입니다. `agent-run-slow`(심각도 `Sev3`)가 `01:02:55`, `agent-run-failed`(`Sev2`)가 `01:06:44`(UTC)에 울렸습니다 — 장애를 만든 지 **약 5~6분 뒤**입니다. 메일 도착은 확인하지 못했으니(D1 의 상자) 메일이 안 오면 스팸함과 수신자 확인(OTP)을 보세요. 단, 알림 평가 창(15분)에 **D2 이전의 느린 호출**(B · C 단계의 cold start)이 남아 있을 수 있어 `Fired` 만으로 D2 의 호출이 원인이라고 입증하지는 못합니다 — 원인을 가리려면 D2 직전에 15분 이상 쉬었다가 실행하거나 D2 호출의 `trace_id` 로 대조하세요.")
        + call(
            "tip",
            "20분이 지나도 Fired 가 없다면",
            "① 규칙이 켜져 있는지: `az monitor scheduled-query list -g \"$AZURE_RESOURCE_GROUP\" --query \"[].{name:name, enabled:enabled}\" -o table` ② 알림의 KQL(D1 의 `SLOW` · `FAILED`)을 `kq` 로 직접 실행해 행이 나오는지 확인하세요. 행이 안 나오면 장애 호출(D2)이 아직 조회되지 않았거나 15분 창을 벗어난 것입니다.",
        )
        + walk(
            kqtext("failed_runs"),
            [
                (
                    "",
                    "실패한 GenAI 스팬과 예외를 한 목록으로 (kq 로 감싸서 실행)",
                    "`union ( … ), ( … )` 는 괄호로 감싼 **두 질의의 결과를 한 목록으로** 합칩니다.",
                ),
                (
                    "(dependencies",
                    "① 실패한 스팬",
                    "`dependencies` 에서 최근 1시간의 **`success == false`** 이면서 **GenAI 스팬**(`gen_ai.operation.name` 속성이 있음)인 행의 시각 · 종류 · 역할 · 이름 · 결과 코드(`resultCode`) · trace_id 를 뽑습니다.",
                ),
                (
                    "(exceptions",
                    "② 예외",
                    "`exceptions` 의 최근 1시간 행을 뽑되, **`outerMessage !has \"A365\"`** 로 cold start 때마다 나오는 **무해한 소음 예외(A365)** 는 제외합니다.",
                ),
                ("| order by timestamp desc", "최신순 정렬", "가장 최근 실패가 위에 옵니다."),
            ],
            cap="② 실패한 실행 — 실패한 GenAI 스팬 + 예외 (최근 1시간) (queries.kql: failed_runs)",
            run="D3",
            lang="kql",
        )
        + exp(
            "D3b",
            read="""
            - 같은 `trace_id` 아래에 **`dependency`**(`invoke_agent` · `chat no-such-deployment`, `code 0` = 실패)와 **`exception`**(`ChatClientException`)이 함께 나옵니다.
            - `chat no-such-deployment` 라는 이름에서 **모델 배포 이름이 틀렸다**는 단서가 바로 보입니다.
            """,
        )
        + walk(
            kqtext("request_success_flag"),
            [
                (
                    "",
                    "호스티드 요청 스팬의 success 를 버전별로 세기 (kq 로 감싸서 실행)",
                    "호스티드 에이전트의 `requests` 를 모아 **`agent.version`(에이전트 버전)별로** 요청 수(`requests`)와 `success == false` 인 수(`success_false`)를 셉니다.",
                )
            ],
            cap="③ 같은 시간 requests 의 success — 실패한 버전(오타 난 배포 이름)도 success_false 가 0 (queries.kql: request_success_flag)",
            run="D3",
            lang="kql",
        )
        + exp(
            "D3c",
            read="**`success_false` 가 모든 버전에서 0** 입니다. 버전 2(오타 난 배포 이름, 호출 3건)는 실제로 **모두 실패**했는데도 `requests` 에는 **성공(success=true)** 으로 남았습니다. 그래서 **실패 알림을 `requests` 로 만들면 놓칩니다.** (`version 3` 행은 D4 에서 복구 버전을 만든 뒤에 생기므로, D3 를 하는 시점에는 아직 보이지 않을 수 있습니다.)",
        )
        + walk(
            kqtext("failure_reason"),
            [
                (
                    "",
                    "예외 메시지에서 HTTP 코드 · 오류 코드 · 설명을 뽑기 (kq 로 감싸서 실행)",
                    "`exceptions` 중 메시지에 `Error code` 가 있는 것만 고릅니다(컨테이너가 모델 호출 실패 시 남기는 예외).",
                ),
                (
                    "| summarize timestamp",
                    "trace 별로 정리",
                    """
                    `by trace_id = operation_Id` — **호출(trace)마다 한 줄**로 줄입니다.
                    * `timestamp = max(timestamp)` — 그 trace 의 마지막 예외 시각
                    * `extract(@"Error code: (\\d+)", 1, outerMessage)` — 메시지에서 **정규식으로 숫자(HTTP 코드)** 를 뽑기(`(\\d+)` 는 ‘숫자 한 덩어리’이고 괄호 안이 뽑을 부분입니다. 오류 문구가 다르면 이 패턴만 고치세요)
                    * `take_any(…)` — 같은 trace 의 여러 예외 중 하나의 값을 사용
                    * `code` · `message` 도 같은 방식으로 **오류 코드와 설명 문장**을 뽑습니다.
                    """,
                ),
                ("| order by timestamp desc", "최신순 정렬", "가장 최근 실패가 위에 옵니다."),
            ],
            cap="④ 실패 원인 — 컨테이너 예외 메시지에 진짜 이유(404 DeploymentNotFound)가 있습니다 (queries.kql: failure_reason)",
            run="D3",
            lang="kql",
        )
        + exp("D3d", read="실패한 호출 3건 모두 **`http 404` · `DeploymentNotFound` · ‘The API deployment for this resource does not exist’** — 배포 이름이 존재하지 않는다는 **진짜 원인**입니다. 클라이언트가 본 `An internal server error occurred.` 에는 없던 정보입니다.")
        + call(
            "info",
            "알림 · 실패 쿼리를 이렇게 짠 이유",
            """
            - 실패 알림은 `requests` 의 `success` 를 보면 **놓칩니다**(③). `dependencies` 의 `success == false` 를 봅니다.
            - **실행이 시작되기 전에 거절된 호출**은 **트레이스에 남지 않았습니다** — 별도 실험에서 오타 난 모델 배포로 만든 프롬프트 에이전트를 2번 불렀을 때(404) 모든 테이블이 비어 있었습니다(이 가이드의 실행 블록에는 없음. 없는 에이전트를 부른 경우는 확인하지 않았습니다). 이런 실패는 **앱 쪽 기록**으로 잡아야 합니다. 단 `invoke_agents.py` 는 예외를 잡지 않아 404 에서는 JSON 을 남기지 못하므로, C7 의 `try/except/finally` 스케치처럼 **예외도 한 줄로 남기는 코드**가 필요합니다.
            """,
        ),
        scope="check",
    )

    d4 = step(
        "d4",
        "복구 · 알림 끄기",
        "D4",
        "소요 약 2분",
        brief(
            what="배포 이름을 **되돌려 새 버전으로 복구**하고, 정상 호출을 확인한 뒤, 실습이 끝났으니 **알림 2개를 끕니다.**",
            why="켜 두면 평가마다 알림 메일이 올 수 있습니다. 복구한 뒤에는 `status: completed` 로 돌아오는지 확인해야 합니다.",
            result="새 버전(버전 3)이 배포되고 정상 호출이 성공하며, 두 알림이 `enabled=False` 가 됩니다.",
            apply="운영에서는 알림을 끄지 말고 **수신자 · 임계값을 조정**하세요.",
        )
        + walk(
            """azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME gpt-5.4-mini
azd deploy report-maf-agent
python invoke_agents.py report-maf-agent 1 short new
for a in agent-run-slow agent-run-failed; do az monitor scheduled-query update -g "$AZURE_RESOURCE_GROUP" -n $a --disabled true --query "{name:name, enabled:enabled}" -o tsv; done""",
            [
                ("azd env set", "배포 이름 되돌리기", "`AZURE_AI_MODEL_DEPLOYMENT_NAME` 을 **올바른 값 `gpt-5.4-mini`** 로 되돌립니다."),
                ("azd deploy", "복구 버전 배포", "에이전트만 다시 배포해 **새 버전**을 만듭니다(약 1분)."),
                ("python invoke_agents.py", "정상 호출 확인", "한 번 호출해 `status` 가 `completed` 로 돌아왔는지 확인합니다."),
                (
                    "for a in agent-run-slow",
                    "알림 2개 끄기",
                    "`az monitor scheduled-query update … --disabled true` 로 두 알림을 **비활성화**합니다. `--query \"{name:name, enabled:enabled}\"` 가 결과로 이름과 `enabled`(꺼졌으면 False)를 보여 줍니다.",
                ),
            ],
            cap="복구(새 버전) → 정상 호출 확인 → 알림 끄기",
            run="D4",
        )
        + exp("D4", read="**`completed`** 로 돌아왔고(`error: null`), 두 알림이 **`False`**(비활성)입니다."),
        scope="check",
    )
    sec_d = section("d", "D · 알림 · 장애 재현", "알림이 에이전트에서도 실제로 울리는지 확인합니다", d1 + d2 + d3 + d4)

    # ───────────────── E. 정리와 판단
    map_rows = [
        ("R1 AOAI 진단 설정", f"{OLD['R1']}줄", "**불필요** — 요청 단위 지연 · 토큰 · 상태는 에이전트 트레이스가 대신(C2~C5). 서비스 쪽 로그가 더 필요하면 Foundry 리소스에 같은 진단 설정을 추가(범주 `RequestResponse` 등 확인 · 이 가이드는 미적용)"),
        ("R2 AOAI 메트릭", "—", "**자동** — 설정 없이 Foundry 리소스에 쌓임 (C5)"),
        ("R3 앱 호출 로그", f"{OLD['R3']}줄", f"**서버 쪽은 불필요**(플랫폼 스팬이 대신) · **앱 쪽은 ‘앱 최소 기록’이 필요**(약 10~15줄, 추정). `invoke_agents.py`({CLIENT_LINES}줄)의 출력 한 줄이 그 예입니다(B2 · C7)"),
        ("R4 Application Insights(OTel)", f"{OLD['R4']}줄", f"**연결 1회** — `connect-appinsights.sh` {NEW['connect']}줄. 에이전트 코드에는 OTel 코드 없음"),
        ("R5 모니터링 에이전트(AMA) · DCR", f"{OLD['R5']}줄", "**에이전트 쪽은 해당 없음**(VM 이 없음). **앱이 도는 VM 은 그대로**이므로 지연 원인이 VM 이 의심되면 앱 VM 에 R5 를 그대로 적용"),
        ("R6 네트워크 경로 로그", f"{OLD['R6']}줄", "**에이전트 → 모델 경로는 해당 없음**(Foundry 내부). **앱 → Foundry 구간은 서버 트레이스에 없으므로** 앱 최소 기록으로 측정(필요하면 R6 를 앱 VM 에 적용)"),
        ("R7 합성 probe", f"{OLD['R7']}줄", "**선택** — cold start · idle 지연은 트레이스로 직접 보임(C3). 정기 점검이 필요하면 `invoke_agents.py` 를 cron 같은 스케줄러로 주기적으로 실행"),
        ("R8 알림", f"{OLD['R8']}줄", f"`alerts.sh` {NEW['alerts']}줄 (D1). Foundry 포털의 Alerts(프리뷰)도 있으나 이 가이드에서 확인하지 못함"),
    ]
    mt = "".join(f"<tr><td>{inline(a)}</td><td>{b}</td><td>{inline(c)}</td></tr>" for a, b, c in map_rows)
    e1 = step(
        "e1",
        "내 앱에는 어느 방법이 맞나 · 가이드 1 의 항목(R1~R8)은 어디로 갔나",
        "E1",
        f"설정 코드 {OLD_TOTAL}줄 → {NEW_TOTAL}줄 (−{PCT}%) — 서버 쪽 모니터링 설정 기준",
        brief(
            what="‘내 앱에는 어느 방법이 맞는지’ **판단 기준**을 먼저 주고(누구나), 가이드 1 의 R1~R8 이 이 가이드에서 **어디로 갔는지** 대응표로 정리합니다(가이드 1 을 읽은 분용).",
            why="두 방법은 **대체가 아니라 상황에 따라 고르는 것**입니다. 줄 수 감소는 서버 쪽 설정 기준이며, 앱 · VM 쪽 항목은 남습니다.",
            result="판단 기준 4가지와 R1~R8 대응표(필요한 줄 수).",
        )
        + call(
            "info",
            "내 앱에는 어느 쪽? — 네 가지를 차례로 물어보세요",
            f"""
            1. **모델 호출을 에이전트 호출로 바꿀 수 있나?** — B3 의 체크리스트 네 문항이 모두 ‘예’ 이면 전환 후보입니다. ‘아니오’ 가 있으면 그 호출은 지금 방식을 유지하고, 앱 · VM 쪽에 로그를 더하는 방식(가이드 1 — VM 앱에 진단 설정 · 수집 프로그램 · probe · 알림을 더함)을 씁니다. 엔드포인트만 Foundry 로 바꿔서는 트레이스가 생기지 않습니다.
            2. **모델 호출 + 지시문 정도의 앱인가, 도구 · 오케스트레이션 코드가 필요한가?** — 앞쪽이면 **프롬프트 에이전트**(코드 · 서버 없음, 추가 요금 없음 · 토큰 비용만), 뒤쪽이면 **MAF 호스티드 에이전트**입니다. 호스티드는 모니터링은 코드 없이 되지만 새 대화마다 **cold start 약 {m['cold_startup_s']}초**(총 응답 약 8~12초)와 컨테이너 시간 과금을 설계에 넣어야 합니다.
            3. **cold start 약 {m['cold_startup_s']}초를 견딜 수 있나?** — 아니오 → 프롬프트 에이전트를 쓰거나, 같은 대화(세션)를 재사용해 첫 호출만 느리게 하는 설계를 검토합니다.
            4. **프롬프트 · 응답 본문이 트레이스에 기록돼도 되나?** — 두 에이전트 모두 본문이 기록됩니다. 안 된다면 접근 제어([부록 C](#x3))를 먼저 정하세요.
            어느 쪽이든 **앱 ↔ 서비스 구간은 앱이 직접 기록**해야 합니다(C7).
            """,
        )
        + md("#### 가이드 1 의 R1~R8 은 어디로 갔나 (가이드 1 을 읽은 분용)")
        + '<table class="nw"><thead><tr><th>가이드 1 의 항목</th><th>줄 수</th><th>Foundry 에이전트에서는</th></tr></thead><tbody>'
        + mt
        + f"<tr><td><b>합계</b></td><td><b>{OLD_TOTAL}줄</b></td><td><b>{NEW_TOTAL}줄</b> (+ 에이전트 코드 {AGENT_LINES}줄 · azure.yaml {YAML_LINES}줄(그중 hooks {HOOK_LINES}줄은 위 스크립트를 연결하는 부분)은 모니터링이 아니라 에이전트 정의 · 앱 최소 기록 약 10~15줄은 추정이라 미포함)</td></tr>"
        "</tbody></table>",
        scope="read",
    )
    e2 = step(
        "e2",
        "정리 — 프로젝트 · 모델 · 에이전트 · 모니터링 리소스 전부 삭제",
        "E2",
        "소요 약 3분",
        brief(
            what="`azd down` 으로 azd 가 만든 **리소스 그룹을 통째로 삭제**하고, 내 컴퓨터의 임시 파일을 지웁니다.",
            why="Foundry 계정 · 호스티드 에이전트 컨테이너 · Application Insights 수집은 **계속 요금이 나올 수 있습니다.**",
            result="리소스 그룹 · Foundry 리소스가 삭제(+ 영구 삭제)되고 같은 이름을 다시 쓸 수 있습니다.",
            apply="**내 운영 환경에서는 실행하지 마세요.** 이 단계는 이 가이드로 만든 실습 환경 전용입니다.",
            caution="`azd down` 은 **지금 선택된 azd 환경**의 리소스 그룹을 지웁니다. 먼저 아래 `azd env list` 로 선택된 환경(`DEFAULT` 열)이 이 가이드로 만든 `fdmon-…` 인지 확인하세요.",
        )
        + code("azd env list", cap="(확인) 선택된 azd 환경이 이 가이드의 fdmon-… 인지 — 확인용 명령 · 실행 블록 아님")
        + walk(
            """azd down --force --purge
rm -f foundry.env calls.jsonl last_call.ts alerts.txt""",
            [
                (
                    "azd down",
                    "azd down — 전부 삭제",
                    "`azd down` 이 azd 가 만든 **리소스 그룹을 통째로 지웁니다.** `--force` 는 확인 질문 생략, **`--purge`** 는 **소프트 삭제된 Foundry 리소스까지 영구 삭제**해 같은 이름을 다시 쓸 수 있게 합니다. (Network Watcher 같은 리소스 그룹 밖 리소스는 만들지 않으므로 따로 지울 것이 없습니다.)",
                ),
                ("rm -f", "임시 파일 삭제", "이 가이드가 만든 **로컬 파일**(환경 값 · 호출 기록 파일 · 마지막 호출 시각 · 알림 목록)을 지웁니다."),
            ],
            cap="전체 삭제",
            run="E2",
            skip=True,
        )
        + md("삭제가 끝나면 `az group exists -n rg-<환경 이름>` 이 `false` 로 나오는지 확인하세요(`azd env list` 의 환경 이름 앞에 `rg-` 를 붙인 것이 리소스 그룹 이름입니다)."),
        scope="clean",
    )
    sec_e = section("e", "E · 판단 기준 · 정리와 삭제", "내 앱에는 어느 방법? · 가이드 1 과의 대응표 · 삭제", e1 + e2)

    # ───────────────── 부록
    rows_facts = [
        ("azd up 한 번", "ok", f"프로젝트 · 모델 · Application Insights 연결 · 에이전트 2개가 {m['up_total_s'] // 60}분 {m['up_total_s'] % 60}초(프로비저닝+훅 {m['provision_s']}초, 배포 {m['deploy_s']}초). 새 환경 3번 중 1번은 첫 시도가 <code>FailedIdentityOperation Conflict</code> 로 실패, 재실행으로 성공"),
        ("azd 프로비저너가 만드는 것", "ok", "<code>infra.provider: microsoft.foundry</code> 는 Foundry 리소스 · 프로젝트 · 모델 배포만 만들고 <b>Application Insights 는 만들지 않습니다</b> → postprovision 훅(<code>connect-appinsights.sh</code>)이 연결"),
        ("서버 쪽 트레이스 자동 수집", "ok", "연결만으로 프롬프트 에이전트(<code>invoke_agent</code> · <code>chat</code> 스팬)와 호스티드 에이전트(플랫폼 요청 스팬 + 컨테이너 스팬 · 로그)가 코드 변경 없이 수집됨"),
        ("직접 모델 호출의 트레이스", "ok", "같은 프로젝트 엔드포인트로 <b>모델을 직접 호출</b>(Responses · Chat Completions)하면 Application Insights 에 <b>0건</b>. 에이전트를 지정한 호출만 <code>invoke_agent</code> + <code>chat</code> 스팬 2건(B3)"),
        ("에이전트 지정 시 요청별 설정", "ok", "system 메시지(<code>type: \"message\"</code>) · <code>max_output_tokens</code> · <code>stream</code> · <code>metadata</code>/<code>user</code> 는 가능, <code>temperature</code> · <code>instructions</code> · <code>tools</code> · JSON 모드(<code>text.format</code>) · <code>reasoning</code> 은 HTTP 400 <code>invalid_payload</code> (‘Not allowed when agent is specified’). 직접 모델 호출은 모두 가능(각 1회 측정)"),
        ("클라이언트 − 서버 시간 차", "ok", "같은 호출 8건: 서버 <code>invoke_agent</code> 시간과 클라이언트 시간의 차 <b>328~488ms 7건 + 새 클라이언트 첫 호출 1,882ms</b>. 노트북 → Korea Central 에서 잰 값(C7)"),
        ("429 후 SDK 재시도", "ok", "429 를 받은 호출은 SDK 가 약 4.6초 기다려 재시도(<code>OPENAI_LOG=info</code> 로그). <b>서버에는 실패 스팬 1ms + 성공 스팬만</b> 있고 대기는 클라이언트에만 보임. 실습 배포 용량(10 단위)이 작아 생긴 것으로 보임 — 분당 토큰 · 분당 요청 중 어느 한도인지는 미확인(같은 시간대 모델 직접 호출 10회 중 4회도 약 5초)"),
        ("traceparent → operation_Id", "ok", "클라이언트가 보낸 trace_id 가 프롬프트 · 호스티드 모두에서 서버 쪽 모든 기록의 <code>operation_Id</code> 와 일치 (컨테이너 로그 포함)"),
        ("응답 ID 대조", "ok", "프롬프트: 클라이언트 <code>resp_…</code> = 스팬의 <code>gen_ai.response.id</code>, 호스티드: <code>caresp_…</code> = 요청 스팬의 <code>azure.ai.agentserver.response_id</code>"),
        ("호스티드 cold start 분해", "ok", "요청 스팬에 <code>hosted_agent.latency.*</code> 속성(start_type · platform_preprocessing · infra_setup · container_readiness · container_response · response_begin). 새 대화마다 cold, 같은 대화 재사용 시 warm"),
        ("프롬프트 에이전트의 런타임 오버헤드", "ok", f"실행 시간 − 모델 호출 시간은 보통 수백 ms 이하. 프롬프트 에이전트 호출 {m['prompt_runs']}건 중 {m['prompt_outliers']}건은 약 {m['prompt_outlier_s']}초(모델 호출 1초 미만 그대로)로 길었음 — 재현 조건은 확인하지 못함"),
        ("실패 가시성", "ok", "호스티드의 실행 중 실패: <code>dependencies</code>(success=false) · <code>exceptions</code> 에 남고 <code>requests</code> 는 success=true. 시작 전에 거절된 호출(없는 모델 배포로 만든 프롬프트 에이전트)은 어떤 테이블에도 남지 않음"),
        ("프롬프트 · 응답 본문", "ok", "<code>gen_ai.input.messages</code> · <code>gen_ai.output.messages</code> · 시스템 지시문이 <code>AppDependencies</code> 의 속성과 <code>AppGenAIContent</code> 테이블에 모두 기록됨(보호 플래그 미등록 상태)"),
        ("모델 메트릭", "ok", "Foundry 리소스에 진단 설정 없이 메트릭 정의 99개 · 요청 수 · 토큰 · 응답 완료 시간 값 확인. 진단 범주(<code>RequestResponse</code> 등) 목록은 확인했고 적용은 하지 않음"),
        ("알림", "ok", "느린 실행 · 실패한 실행 알림 2개가 울리는 것을 확인(알림 목록 API). 수신 메일 도착은 확인하지 못함. 평가 창 5분일 때 지연 도착한 텔레메트리를 놓치는 경우가 있어 15분으로 늘림"),
        ("삭제", "ok", "<code>azd down --force --purge</code> 가 리소스 그룹 삭제 + 소프트 삭제된 Foundry 리소스 purge 를 2분 24초에 마침 (자동 실행 러너는 이 블록을 건너뛰어 별도 환경에서 확인)"),
        ("AOAI → Foundry 업그레이드 · private endpoint · 리전", "part", "<b>문서 기준이며 이번에 검증하지 않음</b>: 업그레이드 시 엔드포인트 · 키 · 네트워크 유지, 기존 private endpoint 가 있으면 포털 업그레이드 불가(DNS zone 추가 필요), Agent Service 는 리전별 제공 범위가 다름"),
        ("에이전트 정의의 temperature 등 지원", "part", "요청별 설정이 거절되는 것은 확인했으나, <b>에이전트 정의에서 같은 설정을 지원하는지는 확인하지 못함</b>"),
        ("OTel 자동 계측의 traceparent 전파", "part", "앱에 OTel 을 넣었을 때 <code>traceparent</code> 가 자동으로 전파되는지는 확인하지 못함"),
        ("Foundry 포털 화면", "part", "Traces · Monitor · Operate 화면은 열어 보지 못함 — 같은 Application Insights 데이터까지만 확인"),
        ("로컬 실행", "part", "<code>azd ai agent run</code>(로컬 8088 포트)은 시도하지 않음"),
    ]
    ftr = "".join(f'<tr><td><b>{a}</b></td><td class="{b}">{"✔" if b == "ok" else "△"}</td><td>{c}</td></tr>' for a, b, c in rows_facts)
    x1 = step(
        "x1",
        "실제 환경에서 확인한 사실",
        "부록 A",
        "2026-10-24 · Korea Central · gpt-5.4-mini · azd 1.37.1 · azure.ai.agents 1.0.0-beta.22 · azure-ai-projects 2.9 · Azure CLI 2.86",
        '<table><thead><tr><th>항목</th><th class="res">결과</th><th>실측 내용</th></tr></thead><tbody>' + ftr + "</tbody></table>"
        + md("✔ = 확인함 · △ = 일부만 확인했거나 확인하지 못함."),
        done=False,
    )

    trouble = table(
        ["증상", "확인 · 해결"],
        [
            ["`$AZURE_RESOURCE_GROUP` 같은 변수가 비어 있다는 오류 · `kq` 가 `command not found`", "새 터미널이라 변수와 함수가 없는 것입니다. `foundry` 폴더에서 `set -a; . ./foundry.env; set +a` 를 실행하세요(A3)."],
            ["azd 가 `look up tenant for subscription … failed to resolve user`", "azd 와 az 가 서로 다른 계정으로 로그인됨. `azd auth login` 을 az 와 같은 계정으로 하거나 `azd config set auth.useAzCliAuth true`"],
            ["`azd up` 이 `FailedIdentityOperation … Conflict` 로 실패", "계정 생성 직후의 일시적 충돌. 같은 `azd up` 을 다시 실행"],
            ["호스티드 배포가 `[tool.poetry] section not found` 로 실패", "원격 빌더가 `pyproject.toml` 만 있으면 Poetry 로 가정. `requirements.txt` 를 쓰거나 `uv.lock` 을 함께 둠"],
            ["호출이 403 · 401", "호출자에게 **Foundry User**(구 Azure AI User) 역할이 없거나 아직 반영 전(최대 수 분). 프로젝트 범위에 부여했는지 확인"],
            ["호출이 400 `invalid_payload` — ‘Not allowed when agent is specified’", "에이전트를 지정한 호출에서는 요청별 `temperature` · `instructions` · `tools` · JSON 모드 · `reasoning` 을 쓸 수 없음. 에이전트 정의로 옮기거나 그 호출은 모델을 직접 호출(단, 트레이스 없음). B3 참고"],
            ["트레이스가 안 보임", "① 프로젝트에 Application Insights 연결이 있는지(`…/projects/<프로젝트>/connections` 에 category AppInsights) ② 호출이 에이전트(프롬프트 · 호스티드)를 거쳤는지 — **모델 엔드포인트만 호출하면 트레이스가 없음** ③ 1~3분 대기"],
            ["클라이언트는 5초 넘게 느린데 서버 스팬은 정상", "429 후 SDK 재시도 대기일 수 있음 — 서버에는 안 남음. `OPENAI_LOG=info` 로 재시도 로그를 보고 배포 쿼터를 확인(C7)"],
            ["호스티드 에이전트 첫 호출이 8~12초", "새 세션의 cold start. 같은 대화(`conversation`)를 재사용하면 첫 호출만 cold 였습니다(오래 쉰 뒤의 동작은 미측정). 원인 분해는 C3"],
            ["응답이 `status: failed` · `An internal server error occurred.`", "클라이언트에는 원인이 안 나옴. C4 의 `trace_by_id` 와 D3 의 `failed_runs` 로 컨테이너 쪽 예외 확인"],
            ["`kq` 결과가 비어 있음(표 머리만 나오거나 아무것도 안 나옴)", "`kq` 는 기본으로 **최근 1시간**만 조회합니다(`az monitor app-insights query` 의 기본값). 호출한 지 오래됐다면 A3 의 ‘`--offset 3d` 설정’을 하세요. 그래도 비면 호출이 에이전트를 거쳤는지, 1~3분 기다렸는지 확인합니다."],
            ["`kq` 가 `JSONDecodeError` 로 끝남", "`az` 가 JSON 대신 오류 문장을 돌려준 것입니다. `kq` 안의 명령(`az monitor app-insights query`)을 직접 실행해 오류 메시지를 보세요 — 흔한 원인: 확장 미설치(A1), 로그인 만료, `AZURE_ENV_NAME` 변수가 비어 있음(`set -a; . ./foundry.env; set +a`)."],
            ["D2 이후 호스티드 에이전트가 계속 실패", "D2 에서 일부러 만든 오타 버전이 남아 있는 것입니다. D4 를 실행해 배포 이름을 되돌리고 새 버전을 배포하세요."],
            ["알림 메일이 안 옴", "스팸함과 **수신자 확인 메일(OTP)** 을 마쳤는지 확인하세요(D1). 알림이 울렸는지는 D3 의 알림 목록(`Fired`)으로 봅니다."],
            ["`azd down` 후 같은 이름 재사용 불가", "삭제된 Foundry 리소스가 소프트 삭제 상태. `azd down --purge` 또는 `az cognitiveservices account purge`"],
        ],
    )
    x2 = step("x2", "문제 해결", "부록 B", "이번 검증에서 실제로 만난 것 위주", trouble, done=False)

    x3 = step(
        "x3",
        "운영에 적용할 때 달라지는 점 · 개인정보",
        "부록 C",
        "이 가이드는 공용 네트워크 · 기본 설정으로 검증했습니다",
        md(
            """
            - **입출력 본문이 기록됩니다.** 프롬프트 · 응답 · 시스템 지시문 · 도구 인자가 트레이스에 남습니다. 문서(Microsoft Learn, 2026-10 확인)의 절차: 본문을 `AppGenAIContent` 전용 테이블로만 보내고, 그 테이블을 **보호 테이블**로 설정한 뒤 **Privileged Monitoring Data Reader** 역할로 읽기 권한을 제한합니다(이 가이드는 적용하지 않음). 전용 테이블로만 보내는 동작은 문서상 **2026-09-30 이후 기본**입니다(그 전에 켜려면 `protectGenAISensitiveData` 플래그, 옛 동작을 임시로 유지하려면 `optOutProtectGenAISensitiveData` 플래그를 등록 — 후자는 2027-09-30 종료). 그런데 이 실습(2026-10-24)에서는 **두 플래그가 모두 등록되지 않았는데도 본문이 `AppDependencies` 속성과 전용 테이블 양쪽에 있었습니다.** 문서와 다른 동작이므로 운영 전에 **내 구독의 플래그 상태와 실제 기록 위치를 직접 확인**하세요.
            - **보존 · 비용**은 연결된 Application Insights / Log Analytics 설정을 따릅니다. 포털의 트레이스 보기는 최대 90일.
            - **역할**: 호출 = Foundry User, 포털에서 트레이스 · 모니터 보기 = 연결된 Application Insights 의 Log Analytics Reader(보호 테이블이면 Privileged Monitoring Data Reader 추가). 프로젝트 관리 ID 의 Log Analytics Reader 는 평가 기능용입니다.
            - **네트워크 격리**(private endpoint · 관리형 VNet)를 쓰는 프로젝트는 이 가이드의 공용 경로 명령이 그대로 되지 않습니다 — 별도 템플릿(Foundry 문서의 private-network)을 쓰세요. 이번 검증 범위 밖입니다.
            - **베타 · 프리뷰**: azd 의 Foundry 확장은 베타(버전 고정 권장), 포털의 Monitor · Alerts 는 프리뷰, 트레이싱 자체는 프롬프트 · 호스티드 에이전트에서 GA(문서 기준).
            - **샘플링 · 비용**: 호출량이 많으면 Application Insights 수집 비용이 커집니다. 수집량(GB/일)을 먼저 추정하고 샘플링 · 보존 기간을 정하세요. 모델 토큰 · 호스티드 에이전트 컨테이너 · 수집 요금은 [Azure 가격 계산기](https://azure.microsoft.com/pricing/calculator/)로 확인하세요(이 가이드는 비용을 비교하지 않았습니다).
            - **앱 · VM 구간은 그대로**: 앱이 VM 에서 에이전트를 호출한다면 그 VM · 앱 → Foundry 구간의 모니터링(앱 최소 기록 · 필요 시 가이드 1 의 R5~R7)은 이 가이드가 대신하지 않습니다.
            """
        ),
        done=False,
    )

    def li(items):
        return "<ol>" + "".join(f"<li>{x}</li>" for x in items) + "</ol>"

    x4 = step(
        "x4",
        "직접 만드는 모니터링용 리소스 · 줄 수 상세",
        "부록 D",
        "비교표의 ② · ① 을 뒷받침하는 목록 (줄 수는 빌드할 때 파일에서 직접 셉니다)",
        '<div class="two"><div><h4>가이드 1 — ' + f"{len(OLD_RESOURCES)}종</h4>" + li(OLD_RESOURCES) + "</div>"
        '<div><h4>이 가이드 — ' + f"{len(NEW_RESOURCES)}종</h4>" + li(NEW_RESOURCES) + "</div></div>"
        + '<table class="nw"><thead><tr><th>가이드 1 스니펫 (빈 줄 · 주석 제외)</th><th>줄</th></tr></thead><tbody>'
        f"<tr><td>R1 AOAI 진단 설정</td><td>{OLD['R1']}</td></tr><tr><td>R3 앱 호출 로그(helper + 사용 예)</td><td>{OLD['R3']}</td></tr>"
        f"<tr><td>R4 Application Insights(OTel 코드 · env · systemd)</td><td>{OLD['R4']}</td></tr><tr><td>R5 모니터링 에이전트(AMA) · DCR</td><td>{OLD['R5']}</td></tr>"
        f"<tr><td>R6 네트워크 경로 로그</td><td>{OLD['R6']}</td></tr><tr><td>R7 합성 probe(스크립트 · 서비스 · 타이머)</td><td>{OLD['R7']}</td></tr>"
        f"<tr><td>R8 알림</td><td>{OLD['R8']}</td></tr><tr><td><b>합계</b></td><td><b>{OLD_TOTAL}</b></td></tr></tbody></table>"
        '<table class="nw"><thead><tr><th>이 가이드의 모니터링 설정 파일</th><th>줄</th></tr></thead><tbody>'
        f"<tr><td><code>scripts/connect-appinsights.sh</code> (Application Insights 연결 · 역할)</td><td>{NEW['connect']}</td></tr>"
        f"<tr><td><code>scripts/alerts.sh</code> (알림 2개)</td><td>{NEW['alerts']}</td></tr>"
        f"<tr><td><b>합계</b></td><td><b>{NEW_TOTAL}</b></td></tr></tbody></table>"
        f"<p class=\"foot-note\">모니터링이 아닌 파일: 에이전트 코드 <code>main.py</code> {AGENT_LINES}줄(텔레메트리 코드 0줄), 클라이언트 <code>invoke_agents.py</code> {CLIENT_LINES}줄, 에이전트 · 모델 정의 <code>azure.yaml</code> {YAML_LINES}줄. <b>앱 최소 기록(약 10~15줄)은 추정이라 합계에 넣지 않았습니다.</b></p>",
        done=False,
    )
    sec_x = section("x", "부록", "검증 기록 · 문제 해결 · 운영 적용 · 상세", x1 + x2 + x3 + x4)
    return sec_d + sec_e + sec_x
