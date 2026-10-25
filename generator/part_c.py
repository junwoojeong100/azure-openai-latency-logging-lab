# -*- coding: utf-8 -*-
# C · 확인과 분석 / D · 정리 / 부록
from lib import *


def build():
    # ───────── C1
    c1_q = kq(
        """union isfuzzy=true withsource=T Heartbeat, Perf, Syslog, AppDependencies, AppTraces, AzureMetrics, AzureDiagnostics
| where TimeGenerated > ago(1h)
| extend lag_s = datetime_diff("second", ingestion_time(), TimeGenerated)
| summarize rows = count(), avg_lag_s = round(avg(lag_s), 0), max_lag_s = max(lag_s) by T
| order by T asc""",
        is_name=False,
    )
    c1 = step(
        "c1",
        "데이터가 들어왔는지 — 테이블별 건수와 수집 지연",
        "C1",
        "B1 설정 후 약 30분 + 앱 호출 몇 분 뒤 (AOAI 로그는 활성화까지 가장 오래 걸립니다)",
        brief(
            what="이 가이드가 쓰는 핵심 7개 테이블의 로그가 한 워크스페이스에 **들어왔는지**, 그리고 **발생 시각에서 수집(조회 가능)까지 몇 초 걸리는지**를 테이블별로 봅니다.",
            why="로그가 없는데 분석을 시작하면 헛수고입니다. 또 이 **수집 지연** 때문에 ‘방금 난 지연’은 로그가 아니라 **메트릭 알림**으로 잡아야 한다는 근거가 됩니다.",
            result="테이블(`T`)마다 행 수 · 평균/최대 수집 지연(초)이 나옵니다. 7개 테이블이 모두 보이면 준비 완료입니다.",
            apply="내 워크스페이스에서 같은 쿼리를 실행하세요(포털 → 내 Log Analytics 워크스페이스 → 왼쪽 메뉴 ‘로그’ 창에 붙여 넣어도 됩니다. **작은따옴표가 든 쿼리는 `kq` 대신 포털에서** 실행하세요). 환경에 따라 테이블 이름이 다를 수 있으니 처음에는 `| take 5` 로 열을 먼저 확인하세요.",
            caution="**처음에는 일부 테이블만 보이는 것이 정상**입니다. B1(AOAI 로그)은 설정 후 20~26분, B2(VM)는 5~10분, B3(앱)은 수 분 뒤에 나타납니다. 아직이면 시간을 두고 이 쿼리를 다시 실행하세요.",
        )
        + walk(
            c1_q,
            [
                (
                    "",
                    "여러 테이블을 한 번에 합치기 (kq 로 감싸서 실행)",
                    """
                    `kq '…'` 는 A1 에서 만든 도우미 함수입니다. **작은따옴표 안이 KQL 질의**이고 결과를 표로 보여 줍니다(포털에서는 작은따옴표 안의 질의만 붙여 넣으면 됩니다).

                    `union` 은 **여러 테이블을 위아래로 이어 붙입니다.** 이 가이드가 만든 7개 테이블을 한 번에 봅니다.
                    * `isfuzzy=true` — 아직 데이터가 없어서 **존재하지 않는 테이블이 있어도 오류 없이** 진행
                    * `withsource=T` — 각 행이 **어느 테이블에서 왔는지**를 `T` 열에 기록
                    """,
                ),
                ("| where TimeGenerated > ago(1h)", "최근 1시간만", "`where` 는 **조건에 맞는 행만 남깁니다.** `TimeGenerated` 는 **로그가 발생한 시각**, `ago(1h)` 는 ‘지금부터 1시간 전’입니다."),
                (
                    "| extend lag_s",
                    "수집 지연 계산",
                    "`extend` 는 **새 열을 만듭니다.** `ingestion_time()` 은 **워크스페이스가 그 행을 받은 시각**이므로, `datetime_diff(\"second\", 받은 시각, 발생 시각)` = **수집 지연(초)** 입니다.",
                ),
                (
                    "| summarize rows",
                    "테이블별로 집계",
                    "`summarize … by T` 는 **`T`(테이블)별로 묶어서** 집계합니다: `rows` = 행 수, `avg_lag_s` = 평균 지연(소수점 없이 반올림), `max_lag_s` = 최대 지연.",
                ),
                ("| order by T asc", "정렬 · 질의 끝", "`T` 이름 오름차순으로 정렬합니다. 마지막 줄의 `'` 가 KQL 을 감싼 따옴표를 닫습니다."),
            ],
            cap="C1 쿼리 — 테이블별 건수와 수집 지연",
            run="C1",
            lang="kql",
        )
        + out(
            """T                 Avg_lag_s    Max_lag_s    Rows
----------------  -----------  -----------  ------
AppDependencies   11           174          146
AppTraces         7            163          143
AzureDiagnostics  85           279          41       ← AOAI 로그 (RequestResponse · Audit)
AzureMetrics      450          590          694      ← AOAI 메트릭 (AllMetrics)
Heartbeat         17           168          28
Perf              113          239          960
Syslog            94           237          53""",
            read="""
            - **`T`** 열은 테이블, **`Rows`** 는 최근 1시간 행 수, **`Avg_lag_s`** 는 평균 수집 지연(초), **`Max_lag_s`** 는 최대 지연(초)입니다(`az` 는 열을 알파벳순으로 보여 주고, 버전에 따라 맨 앞에 `TableName` 열을 하나 더 붙입니다).
            - **출력이 비어 있으면**(헤더도 없이 끝나면) `echo $LAW_NAME` 으로 변수가 있는지 확인하세요. 비어 있으면 새 터미널이라 변수가 없는 것이므로 작업 폴더에서 `source lablog.env` 를 먼저 실행합니다.
            - 앱 로그(`AppDependencies` · `AppTraces`)는 평균 약 10초, VM 로그(`Perf` · `Syslog`)는 약 2분, AOAI 요청 로그(`AzureDiagnostics`)는 **활성화된 뒤** 평균 1~2분, AOAI 메트릭(`AzureMetrics`)은 7~10분 뒤에 보입니다(최대값은 처음 몇 분의 일괄 수집분이 올립니다).
            - **`AzureDiagnostics` 행이 아직 없다면** B1 설정 후 30분이 지났는지 확인하세요. `Heartbeat` 가 계속 들어오면 모니터링 에이전트(AMA)는 정상입니다.
            """,
        ),
        scope="check",
    )

    # ───────── C2
    c2_q = kq("app_vs_aoai_by_request")
    c2_base = kq(
        """let app = AppTraces
    | where TimeGenerated > ago(7d) and Message has "aoai_call"
    | extend r = parse_json(Message)
    | where tostring(r.outcome) == "ok"
    | project apim = tostring(r.apim_request_id), app_ms = toint(r.total_ms);
AzureDiagnostics
| where TimeGenerated > ago(7d) and Category == "RequestResponse"
| project CorrelationId, aoai_ms = DurationMs
| join kind=inner app on $left.CorrelationId == $right.apim
| extend gap_ms = app_ms - aoai_ms
| summarize calls = count(), p50_gap_ms = percentile(gap_ms, 50), p95_gap_ms = percentile(gap_ms, 95), max_gap_ms = max(gap_ms)""",
        is_name=False,
    )
    c2_499 = kq(
        """AzureDiagnostics
| where TimeGenerated > ago(1h) and Category == "RequestResponse" and ResultSignature == "499"
| extend p = parse_json(properties_s)
| project TimeGenerated, ResultSignature, DurationMs, CallerIPAddress,
          responseLength = toint(p.responseLength), completionTokens = toint(p.completionTokens), deployment = tostring(p.modelDeploymentName)
| order by TimeGenerated desc
| take 5""",
        is_name=False,
    )
    c2 = step(
        "c2",
        "요청 한 건씩 대조 — 앱이 잰 시간 vs AOAI 가 잰 시간",
        "C2",
        "가이드의 핵심 분석 · 앱 로그(R3)와 AOAI 로그(R1)를 요청 ID 로 조인",
        brief(
            what="같은 요청 한 건에 대해 **앱이 잰 시간(`app_ms`)** 과 **AOAI 가 잰 시간(`aoai_ms`)** 을 **요청 ID 로 짝지어** 나란히 놓고 그 차이(`gap_ms`)를 계산합니다.",
            why="앱 시간(R3 의 `total_ms` = **AOAI 호출 코드 구간**) − AOAI 시간 = **AOAI 바깥(SDK · 연결 · 네트워크)에서 쓴 시간**입니다. 이 값이 평소(실습에서는 중앙값 83ms · p95 104ms — 아래 기준선 쿼리)보다 크면 그 지연은 AOAI 안이 아니라 **AOAI 바깥**에서 생긴 것입니다. (호출 코드에 들어가기 *전*의 큐 대기 · 프롬프트 준비 시간은 `total_ms` 에 포함되지 않으므로 이 표로는 보이지 않습니다.)",
            result="요청별로 `outcome` · `status` · `app_ms` · `aoai_ms` · `gap_ms` 가 나옵니다(gap 이 큰 순서).",
            apply="내 환경에서도 앱 로그(R3)에 `apim_request_id` 가 남아 있으면 그대로 됩니다. **앱이 응답을 받기 전에 끊은 호출(timeout)은 이 방식으로 짝지어지지 않으므로** 아래 ‘쿼리 ②’ 처럼 시각 + 처리 시간으로 눈으로 맞춥니다.",
        )
        + md("앱 로그의 `apim_request_id`(응답 헤더 `apim-request-id`)가 AOAI 로그의 `CorrelationId` 와 **같습니다**(실측 확인). 이 값이 두 기록을 잇는 **열쇠**입니다.")
        + walk(
            c2_q,
            [
                (
                    "",
                    "① 앱 로그를 읽어 `app` 이라는 임시 표로 만들기 (kq 로 감싸서 실행)",
                    """
                    `kq '…'` 의 작은따옴표 안이 KQL 입니다. 이 질의는 두 개의 표(앱 로그 · AOAI 로그)를 **조인(join)** 합니다.

                    `let app = …;` 는 **질의 결과에 이름을 붙여 두는 문법**입니다(세미콜론으로 끝남).
                    * `AppTraces` 에서 메시지에 `aoai_call` 이 있는 것 = **R3 가 남긴 JSON 한 줄**
                    * `parse_json(Message)` — 문자열인 JSON 을 **필드로 풀어서** `r.total_ms` 처럼 꺼낼 수 있게 함
                    * `project` — 필요한 열만 남김: `t`(시각) · `apim`(**요청 ID**) · `outcome`(ok / client_timeout / error) · `app_ms`(**앱이 잰 시간**)
                    """,
                ),
                (
                    "=AzureDiagnostics",
                    "② AOAI 로그에서 필요한 열만 고르기",
                    "`AzureDiagnostics` 의 `RequestResponse` 행에서 `CorrelationId`(요청 ID) · `status`(결과 코드) · `aoai_ms`(**AOAI 가 잰 시간 = DurationMs**) 만 남깁니다.",
                ),
                (
                    "| join kind=inner app",
                    "③ 요청 ID 가 같은 행끼리 짝짓기",
                    "`join kind=inner` 는 **양쪽에 모두 있는 행만** 이어 붙입니다. `$left.CorrelationId == $right.apim` — AOAI 의 `CorrelationId` 와 앱의 `apim` 이 같은 행끼리 연결합니다(= 같은 요청).",
                ),
                (
                    "| project t, outcome",
                    "④ 차이 계산 · 정렬 · 상위 50건",
                    "`gap_ms = app_ms − aoai_ms` 가 **AOAI 바깥에서 쓴 시간**입니다. `order by gap_ms desc` 로 **차이가 큰 요청부터** 나열하고 `take 50` 으로 50건만 봅니다.",
                ),
            ],
            cap="C2 쿼리 ① — 요청 한 건씩 짝지어 gap 계산",
            run="C2",
            lang="kql",
        )
        + out(
            """t                     outcome  status  app_ms  aoai_ms  gap_ms
--------------------  -------  ------  ------  -------  ------
2026-10-23T13:19:18Z  ok       200     7449    7217     232
2026-10-23T13:22:12Z  ok       200     905     790      115
2026-10-23T13:25:18Z  ok       200     6449    6349     100
2026-10-23T13:21:48Z  ok       200     6719    6623     96
…
(같은 리전에서 gap 은 대부분 100ms 안팎 — 아래 기준선 쿼리 참고. 토큰 수는 앱 값과 AOAI 값이 정확히 일치했습니다)""",
            read="""
            - 첫 행: 앱은 **7449ms** 걸렸다고 기록했고 AOAI 는 **7217ms** 라고 기록했습니다 → 차이 **232ms** 만 AOAI 바깥에서 쓴 시간. 즉 **느린 7초는 AOAI 안에서**(긴 응답 생성) 쓰인 것입니다.
            - 만약 `gap_ms` 가 수 초로 커진 행이 나온다면, 그 요청은 **AOAI 가 아니라 AOAI 바깥(SDK · 연결 · 네트워크)** 에서 시간을 쓴 것이므로 C4(probe · VM)로 넘어가세요.
            - `t` 는 **UTC** 입니다. `outcome` 이 `ok` 가 아닌 행은 요청 ID 가 비어 이 표에 나오지 않습니다(아래 상자).
            - **B1 을 켠 직후 20~26분 동안의 호출**은 AOAI 쪽 기록이 없어 조인에서 빠지므로 이 표에 나오지 않습니다.
            """,
        )
        + md("**‘평소 gap’ 기준선 만들기** — 위 표는 gap 이 큰 50건이라 ‘평소 값’은 따로 요약해 봐야 합니다. 같은 조인에서 **성공(`ok`) 호출의 gap 분포만** 계산합니다(최근 7일). 이 쿼리는 위 표의 쿼리에서 마지막 단계만 바꾼 것으로, **실습 환경에서 실제로 실행해 확인한 값**입니다.")
        + walk(
            c2_base,
            [
                ("", "위와 같은 조인 (앞 줄들 + join)", "앱 로그 중 **성공한 호출**(`outcome == \"ok\"`)만 골라 AOAI 로그와 요청 ID 로 짝짓는 부분은 위 쿼리와 같습니다."),
                (
                    "| extend gap_ms",
                    "gap 의 분포 요약",
                    "`percentile(gap_ms, 50)` = **중앙값**(절반은 이보다 작음), `percentile(gap_ms, 95)` = **느린 쪽 5% 를 뺀 값**, `max` = 최댓값. 건수(`calls`)와 함께 **‘평소 AOAI 바깥에서 쓰는 시간’의 기준선**을 만듭니다.",
                ),
            ],
            cap="gap 기준선 — 성공 호출의 gap 분포 (최근 7일)",
            lang="kql",
        )
        + out(
            """calls  p50_gap_ms  p95_gap_ms  max_gap_ms
-----  ----------  ----------  ----------
67     83          104         232""",
            read="이 실습(앱 VM 과 AOAI 가 같은 리전)에서는 **성공 호출 67건의 gap 이 중앙값 83ms · p95 104ms · 최대 232ms** 였습니다. 내 환경의 기준선은 VM 위치 · 프록시 · 방화벽에 따라 다르므로 **내 숫자를 이 값과 비교하지 말고, 내 환경의 평소 값과 ‘지연이 난 순간의 gap’을 비교**하세요.",
        )
        + call(
            "warn",
            "timeout 호출은 요청 ID 로 짝지어지지 않습니다",
            """
            앱이 응답을 받기 전에 끊으면(`client_timeout`) 응답 헤더가 없어 `apim_request_id` 가 비어 있습니다. 이 경우에는 **시각 + 처리 시간**으로 맞춥니다 — 앱 `total_ms≈1027`(timeout 1.0초) ↔ AOAI `ResultSignature=499 · DurationMs≈1062`. 아래 ‘쿼리 ②’ 는 **앱 쪽과 자동으로 조인하지 않고 AOAI 쪽 499 행만** 보여 주므로, 앱 로그의 `client_timeout` 행(시각 · `total_ms`)과 **눈으로 대조**하세요. 이 실습의 499 행은 `responseLength=0` · `completionTokens=0` 이었습니다(비스트리밍 호출 기준 — 스트리밍이면 다를 수 있습니다).
            """,
        )
        + walk(
            c2_499,
            [
                (
                    "",
                    "499 행만 고르기 (kq 로 감싸서 실행)",
                    """
                    AOAI 로그에서 499 행만 직접 봅니다.
                    * `Category == "RequestResponse" and ResultSignature == "499"` — 요청 로그 중 **결과 코드가 499**(클라이언트가 응답 전에 끊음)인 것
                    * `parse_json(properties_s)` — `properties_s` 안의 JSON(토큰 수 · 응답 길이 · 배포 이름)을 풀어 `p` 로 둠
                    """,
                ),
                (
                    "| project TimeGenerated",
                    "보여 줄 열 · 최근 5건",
                    "시각 · 코드 · **처리 시간** · **호출자 IP** · **응답 길이** · **완료 토큰 수** · 배포 이름을 고르고, 최신 5건만 봅니다. 499 행은 응답을 받기 전에 끊겼으므로 `responseLength` · `completionTokens` 가 0 입니다.",
                ),
            ],
            cap="C2 쿼리 ② — 499 행 확인",
            run="C2",
            lang="kql",
        )
        + out(
            """TimeGenerated         ResultSignature  DurationMs  CallerIPAddress  responseLength  completionTokens  deployment
--------------------  ---------------  ----------  ---------------  --------------  ----------------  ----------
2026-10-23T11:28:42Z  499              1062        20.200.208.**    0               0                 gpt41mini""",
            read="`DurationMs` 1062 ≈ 앱의 timeout(1초) 입니다 — **앱 timeout 이 먼저 끊은** 요청이라는 증거입니다. `CallerIPAddress` 는 마지막 자리가 가려져(`20.200.208.**`) 나옵니다. AOAI 가 본 호출자의 **송신 공용 IP**(방화벽 · NAT 를 거치면 그 장치의 IP)를 확인하는 데 씁니다.",
        ),
        scope="check",
    )

    # ───────── C3
    c3_a = kq("app_dep_vs_aoai_by_minute")
    c3_b = kq("aoai_tokens_by_5min")
    c3_m1 = kq("aoai_minute_of_hour")
    c3_m2 = kq("app_by_minute_of_hour")
    c3 = step(
        "c3",
        "1분 · 5분 단위로 보기 — 정각 · 30분 패턴 찾기",
        "C3",
        "운영에서는 ‘일주일 이상’ 겹쳐 봅니다",
        brief(
            what="앱(Application Insights)과 AOAI 를 **1분 단위로 나란히** 놓고 **8초 이상 느린 분**만 뽑습니다. 그다음 AOAI 로그만으로 **출력 토큰당 처리 시간**을 보고, 마지막으로 날짜 · 시는 무시하고 **‘시각의 분(0~59)’별로 겹쳐서** 정각 · 30분 패턴이 있는지 봅니다.",
            why="실제 장애 분석은 개별 요청보다 **시간 패턴**(예: 매시 정각 · 30분에만 느림)이 중요합니다. 느린 이유가 **출력 길이** 때문인지 아닌지도 구분해야 합니다.",
            result="느린 분의 앱 · AOAI p95 비교표, 5분 단위 토큰당 시간(`ms_per_out_token`), 그리고 ‘분(minute)’별 패턴표 두 개(AOAI 쪽 · 앱 쪽).",
            apply="내 워크스페이스에서 **기간을 7일 이상**(`ago(3d)` → `ago(7d)` 등)으로 늘려 실행해 패턴을 찾으세요. 이 실습 데이터는 1시간 남짓이라 패턴이 없습니다.",
        )
        + walk(
            c3_a,
            [
                (
                    "",
                    "① 앱이 본 AOAI 호출 — 1분 단위 (kq 로 감싸서 실행)",
                    """
                    앱 쪽 표 하나와 AOAI 쪽 표 하나를 **1분 단위로 합치는** 질의입니다.
                    * `AppDependencies` 는 R4 가 기록한 **앱의 외부 호출** 테이블. `Target has "openai.azure.com"` 로 **AOAI 호출만** 골라냅니다(다른 호출이 섞여 있어서 필터가 필요).
                    * `sum(ItemCount)` — 호출 수. **샘플링 중에도 정확**하도록 `count()` 가 아니라 `ItemCount` 의 합을 씁니다.
                    * `sumif(ItemCount, Success == false)` — 실패 수
                    * `percentile(DurationMs, 95)` — **p95 지연**
                    * `by t = bin(TimeGenerated, 1m)` — **1분 단위로 묶기**
                    """,
                ),
                (
                    "let aoai = AzureDiagnostics",
                    "② AOAI 가 본 호출 — 1분 단위",
                    "같은 방식으로 AOAI 진단 로그를 1분 단위로 집계합니다: 호출 수 · **p95 처리 시간** · `c499`(**499 건수**, `countif`). `ResourceProvider == \"MICROSOFT.COGNITIVESERVICES\"` 는 AOAI(Cognitive Services) 로그만 고르는 조건입니다.",
                ),
                (
                    "=app",
                    "③ 두 표를 시간(t)으로 합치기",
                    "`join kind=fullouter` 는 **한쪽에만 있어도 행을 남기는** 합치기입니다. 앱 로그만 있고 AOAI 로그가 없는 시간(예: 아직 B1 이 활성화되기 전)도 보이게 하려는 것입니다. 두 표에 같은 이름의 열 `t` 가 있으면 합친 뒤 **오른쪽(AOAI 표)의 것이 `t1`** 이라는 이름이 되므로, `coalesce(t, t1)` 으로 ‘양쪽 시각 중 값이 있는 것’을 골라 한 열로 만듭니다.",
                ),
                (
                    "| where app_p95_ms > 8000",
                    "④ 8초 이상 느린 분만 · 시간순",
                    "앱 p95 나 AOAI p95 가 **8000ms 를 넘은 분**만 남기고 시간순으로 나열합니다.",
                ),
            ],
            cap="앱 ↔ AOAI — 1분 단위, 8초 이상 느린 분만",
            run="C3",
            lang="kql",
        )
        + out(
            """t                     app_calls  app_failed  app_p95_ms  aoai_calls  aoai_p95_ms  c499
--------------------  ---------  ----------  ----------  ----------  -----------  ----
2026-10-23T13:10:00Z  5          0           8031        -           -            -   ← AOAI 로그 켜기 전
2026-10-23T13:16:00Z  4          2           8014        -           -            -
2026-10-23T13:26:00Z  4          0           8355        5           8271         0""",
            label="예상 결과 (AOAI 로그가 활성화되기 전 시간대는 앱 쪽 값만 보입니다)",
            read="""
            - **13:26 행**: 앱 p95 8355ms, AOAI p95 8271ms — **둘이 거의 같은 크기로 함께 높아진 것**은 느린 시간이 AOAI 쪽에서 쓰였을 가능성을 보여 주는 **단서**입니다. 단, 두 표는 **호출 집합이 다르고**(이 행은 앱 4건 · AOAI 5건 — probe 호출 등이 AOAI 쪽에 섞임) p95 도 **각각 따로 계산한 값**이라 서로 빼서 ‘차이’로 해석하면 안 됩니다. 확정은 C2 의 요청 ID 조인으로 하세요.
            - **13:10 · 13:16 행**: AOAI 쪽이 `-`(비어 있음) — 이 시점은 아직 B1 로그가 활성화되기 전이라 **AOAI 로그가 없을 뿐**, AOAI 가 정상이라는 뜻이 아닙니다.
            - 패턴을 볼 때는 `t` 의 **분(minute)** 이 반복해서 0 · 30 근처인지 보세요.
            """,
        )
        + walk(
            c3_b,
            [
                (
                    "",
                    "AOAI 요청 로그에서 토큰 수 꺼내기 (kq 로 감싸서 실행)",
                    "AOAI 진단 로그만으로 보는 질의입니다. 요청 로그(`RequestResponse`)의 `properties_s`(JSON)를 `parse_json` 으로 풀어 `p` 로 둡니다. 여기에 `completionTokens`(**출력 토큰 수**)가 들어 있습니다.",
                ),
                (
                    "| summarize calls",
                    "5분 단위 집계 — 토큰당 처리 시간",
                    """
                    * `calls` · `p95_ms` — 호출 수 · p95 처리 시간
                    * `out_tokens = sum(completionTokens)` — 출력 토큰 총합
                    * **`ms_per_out_token = sum(DurationMs) / sum(completionTokens)`** — **출력 토큰 1개당 걸린 시간(ms)**
                    * `by bin(TimeGenerated, 5m)` — 5분 단위로 묶기
                    """,
                ),
                ("| order by TimeGenerated asc", "정렬", "시간 오름차순."),
            ],
            cap="AOAI 로그만으로 — 출력 토큰당 처리 시간",
            run="C3",
            lang="kql",
        )
        + out(
            """TimeGenerated         calls  p95_ms  out_tokens  ms_per_out_token
--------------------  -----  ------  ----------  ----------------
2026-10-23T13:15:00Z  5      7217    1431        11
2026-10-23T13:20:00Z  23     6623    2723        16
2026-10-23T13:25:00Z  14     8271    2112        15""",
            read="**토큰당 시간(`ms_per_out_token`)이 11~16ms 로 비슷한데 총 시간(`p95_ms`)만 늘었다면 원인은 ‘출력이 길어서’**일 가능성이 큽니다. 반대로 토큰당 시간 자체가 갑자기 커졌다면 AOAI 처리 속도가 느려졌을 수 있으므로 Support Case 후보입니다. 이 값은 **어림 지표**입니다 — 처리 시간에는 입력(프롬프트) 처리도 들어 있고, 499 · 토큰 0 인 행도 합계에 섞입니다. 생성 속도를 따로 보려면 AOAI 메트릭 `AzureOpenAITokenPerSecond` 도 함께 참고하세요.",
        )
        + md("**마지막으로 ‘시각의 분’ 패턴** — 지금까지는 시각별(13:10, 13:15 …)로 봤습니다. ‘매시 정각 · 30분에만 느린가?’를 보려면 **날짜 · 시를 무시하고 같은 ‘분’끼리 며칠치를 합쳐서** 봅니다. 아래 두 쿼리가 각각 AOAI 쪽과 앱 쪽입니다(이 실습 환경에서 실행해 확인한 결과입니다).")
        + walk(
            c3_m1,
            [
                (
                    "",
                    "AOAI 쪽 — 대화형(Completions) 요청만 골라 ‘분’ 뽑기 (kq 로 감싸서 실행)",
                    "최근 14일 AOAI 요청 로그 중 `OperationName contains \"Completions\"`(채팅 · 텍스트 생성 호출)만 남기고, `datetime_part(\"minute\", TimeGenerated)` 로 **시각의 ‘분’(0~59)** 을 새 열 `minute_of_hour` 로 만듭니다.",
                ),
                (
                    "| summarize calls",
                    "5분 구간으로 묶어 집계",
                    "`bin(minute_of_hour, 5)` 는 분을 **5분 구간**(0 · 5 · 10 … 55)으로 묶습니다. 구간마다 호출 수 · p95 · **8초 초과 건수**(`over_8s`) · **499 건수**(`c499`)를 셉니다. 날짜와 시는 구분하지 않으므로 **14일치가 같은 분끼리 합쳐집니다.**",
                ),
            ],
            cap="AOAI 쪽 — ‘시각의 분’ 구간별 (최근 14일)",
            lang="kql",
        )
        + out(
            """minute_of_hour  calls  p95_ms  over_8s  c499
--------------  -----  ------  -------  ----
15              5      7217    0        1
20              23     6623    0        1
25              24     8271    3        2
30              26     7426    1        2
35              20     1290    1        4""",
            label="예상 결과 (이 실습 데이터 — 약 1시간 분량이라 5개 구간만 나옵니다)",
            read="`minute_of_hour` 가 **15 = 매시 15~19분** 구간입니다. 이 실습은 1시간 남짓한 데이터에 호출 종류를 난수로 섞었으므로 **정각 · 30분 패턴이 없습니다**(25분 구간의 8초 초과 3건도 우연). 내 환경에서는 호출이 계속 있었다면 12개 구간(0 ~ 55)이 나오며, **0 구간과 30 구간만 `p95_ms` · `over_8s` 가 유독 크면** 정각 · 30분에 반복되는 원인(스케줄 작업 · 배치 호출)을 의심하고 C4 의 cron 쿼리로 넘어가세요.",
        )
        + walk(
            c3_m2,
            [
                (
                    "",
                    "앱 쪽 — R3 JSON 한 줄씩 읽기 (kq 로 감싸서 실행)",
                    "앱 로그(`AppTraces`)에서 R3 가 남긴 `aoai_call` 줄을 최근 7일치 읽고 `parse_json` 으로 풀어 `r` 에 둡니다.",
                ),
                (
                    "| summarize calls",
                    "‘분’(0~59)별 집계 — 동시 호출 수까지",
                    "분(0~59)별로 호출 수 · **최대 동시 호출 수**(`max_inflight` = R3 가 기록한 `inflight` 의 최댓값) · p95 · timeout 수(`outcome == client_timeout`)를 셉니다. **`max_inflight` 가 같은 분에 커지면** ‘동시 호출이 몰려서 느린 것’이라는 단서입니다.",
                ),
            ],
            cap="앱 쪽 — ‘시각의 분’(0~59)별 (최근 7일)",
            lang="kql",
        )
        + out(
            """minute_of_hour  calls  max_inflight  p95_ms  timeouts
--------------  -----  ------------  ------  --------
0               5      1             1258    0
1               4      1             6922    1
2               4      1             5783    1
3               4      1             7182    0
…               (4~28 생략 — 한 분마다 한 행, 모두 calls 3~5 · max_inflight 1)
29              5      1             8269    1
30              4      1             7338    0
31              5      1             8101    0
…               (32~59 생략)""",
            label="예상 결과 (이 실습 데이터 — 지면상 일부 행만 보입니다. 실제로는 호출이 있었던 분마다 한 행이 나옵니다)",
            read="분 하나가 한 행입니다. 데모 앱이 **한 번에 하나씩만 호출**해서 `max_inflight` 가 항상 1 이고, 호출이 난수로 섞여 한 분에 3~5건뿐이라 `p95_ms` 는 분마다 들쭉날쭉합니다(패턴 없음). 내 운영 환경에서는 **`minute_of_hour` 가 0 · 30 근처인 행의 `calls` · `max_inflight` · `p95_ms` 가 다른 분보다 뚜렷하게 큰지**를 보세요.",
        ),
        scope="check",
    )

    # ───────── C4
    c4_a = kq("probe_by_5min")
    c4_b = kq("cron_at_hh00_hh30")
    c4_c = kq("ama_perf_counters")
    c4_d = kq("cm_aoai_rtt")
    c4 = step(
        "c4",
        "VM 쪽 — probe · cron · 성능 카운터",
        "C4",
        "정각 · 30분에 VM 에서 무슨 일이 도는지",
        brief(
            what="probe 의 5분 요약, **정각 · 30분에 실행된 cron 작업**, 에이전트가 수집 중인 **성능 카운터**를 봅니다.",
            why="앱 로그와 AOAI 로그가 모두 정상인데 느리다면 VM 안(스케줄 작업 · CPU · 디스크) 또는 VM → AOAI 경로가 원인일 수 있습니다.",
            result="probe 구간별 시간 요약, cron 작업 목록, 카운터 12종의 수집 상태.",
            apply="내 워크스페이스에서 쓰세요. 카운터 쿼리의 `Computer has \"…\"` 는 **내 VM 이름**으로 바꾸고, 워크스페이스를 여러 VM 이 함께 쓴다면 probe · cron 쿼리의 `Syslog` 줄 다음에도 `| where Computer has \"내 VM 이름\"` 을 추가하세요.",
        )
        + walk(
            c4_a,
            [
                (
                    "",
                    "probe 의 기록만 골라 JSON 풀기 (kq 로 감싸서 실행)",
                    "B4 의 probe 가 남긴 `Syslog` 를 5분 단위로 요약합니다. `Syslog` 테이블에서 프로세스 이름이 **`aoai-probe`** 인 행만 고르고, 메시지(`SyslogMessage`, probe 가 남긴 JSON)를 `parse_json` 으로 풀어 `p` 에 담습니다.",
                ),
                (
                    "| summarize runs",
                    "5분 · 역할 · 대상별 집계",
                    """
                    * `runs` — probe 실행 횟수(= JSON 줄 수). 1분마다 돌므로 5분 구간이면 보통 5~6
                    * `p95_ms` — 전체 시간 p95
                    * `max_tcp_ms` — **TCP 연결** 시간의 최댓값
                    * `max_wait_ms` — **서버 대기** 시간의 최댓값
                    * `fails` — **통신 실패**(`rc≠0`) 횟수. **HTTP 401 · 429 · 5xx 는 `rc` 가 0 이라 여기에 세어지지 않습니다**(그 코드는 JSON 의 `code` 에 있고 이 쿼리는 요약하지 않습니다)
                    * `by bin(…, 5m), role, target` — 5분 · **역할**(`vm-inside`/`vm-outside`) · **대상**(`aoai` 또는 `app:…`)별로
                    """,
                ),
                ("| order by TimeGenerated asc", "정렬", "시간 오름차순."),
            ],
            cap="probe — 5분 단위 (VM 안, AOAI · 로컬 앱 URL)",
            run="C4",
            lang="kql",
        )
        + out(
            """TimeGenerated         role       target            runs  p95_ms  max_tcp_ms  max_wait_ms  fails
--------------------  ---------  ----------------  ----  ------  ----------  -----------  -----
2026-10-23T11:15:00Z  vm-inside  aoai              6     1120    6           643          0
2026-10-23T11:15:00Z  vm-inside  app:11202/health  6     3       0           3            0""",
            read="""
            - 같은 5분 동안 AOAI 대상 probe 6번의 p95 는 1120ms, 최대 TCP 연결은 6ms, 최대 서버 대기는 643ms 이고 실패는 0 입니다 → **평소 기준선**입니다.
            - 이 값이 **갑자기 커지는 시각**이 앱의 느린 시각과 같다면, `max_tcp_ms`(연결)가 커졌으면 **연결 구간**(DNS · 네트워크 · 방화벽)의 단서, `max_wait_ms`(요청을 보낸 뒤 첫 응답까지)가 커졌으면 **네트워크 + AOAI 처리** 양쪽의 단서입니다. 한 값만으로 원인을 확정하지 말고 C2 · AOAI 메트릭 · Connection Monitor(B7)와 함께 판단하세요.
            """,
        )
        + walk(
            c4_b,
            [
                (
                    "",
                    "cron 로그 중 ‘실행(CMD)’만 (kq 로 감싸서 실행)",
                    "cron 이 실행한 작업을 시각별로 찾습니다. `Facility == \"cron\"` 은 cron 채널, `SyslogMessage has \"CMD\"` 는 **작업이 실행된 기록**만 고릅니다.",
                ),
                (
                    "| extend minute_of_hour",
                    "분(0~59) 계산 후 정각 · 30분 근처만",
                    "`datetime_part(\"minute\", …)` 로 **시각의 ‘분’** 을 뽑고, `minute_of_hour in (0, 1, 30, 31)` 으로 **정각 · 30분과 그 다음 1분**(0 · 1 · 30 · 31분)에 실행된 것만 남깁니다. (`cron.hourly` 같은 작업은 매시 1분에 돌기 때문에 1분과 31분도 포함합니다.)",
                ),
                (
                    "| summarize runs",
                    "작업별 실행 횟수",
                    "프로세스 이름과 **실행한 명령의 앞 100글자**(`substring(…, 0, 100)`)별로 몇 번 실행되었는지 세고 많은 순으로 나열합니다. **결과에는 시각이 없고** ‘작업 · 횟수’만 나옵니다. 시각이 필요하면 `summarize` 의 `by` 에 `bin(TimeGenerated, 1h)` 같은 항목을 추가하세요.",
                ),
            ],
            cap="cron — 매시 정각 · 30분(분 0 · 1 · 30 · 31)에 실행된 작업",
            run="C4",
            lang="kql",
        )
        + out(
            """ProcessName  cmd                                        runs
-----------  -----------------------------------------  ----
CROND        (root) CMD (run-parts /etc/cron.hourly)    1""",
            read="정각 · 30분 근처에 **어떤 작업이 몇 번** 돌았는지 보입니다(시각은 나오지 않습니다). 위 예에서는 `cron.hourly` 가 한 번 돌았습니다. 앱이 느려지는 시각과 **같은 시각에 도는 작업**이 있다면 원인 후보입니다.",
        )
        + call("info", "cron 결과가 비어 있다면", "RHEL 의 `cron.hourly` 는 매시 **01분**에 돕니다. 첫 정각이 지난 뒤(약 1시간 후) 다시 실행하세요.")
        + walk(
            c4_c,
            [
                (
                    "",
                    "이 VM 의 최근 30분 성능 데이터를 카운터별로 세기 (kq 로 감싸서 실행)",
                    "B2 에서 수집하기로 한 **성능 카운터 12종**이 모두 들어오는지 확인합니다. `Perf` 는 성능 카운터 테이블입니다. `Computer has \"vm-lablog-rhel\"` 로 이 VM 만 고르고, `ObjectName`(분류: Processor · Memory …)과 `CounterName`(카운터 이름)별로 **샘플 수**(`samples`)와 마지막 수신 시각(`last_seen`)을 봅니다.",
                ),
            ],
            cap="성능 카운터 — 12종이 모두 들어오는지",
            run="C4",
            lang="kql",
        )
        + out(
            """CounterName              ObjectName    samples
-----------------------  ------------  -------
% Processor Time         Processor     15
% IO Wait Time           Processor     15
% Used Memory            Memory        5
Available MBytes Memory  Memory        5
% Used Swap Space        Memory        5
Disk Transfers/sec       Logical Disk  45
% Free Space             Logical Disk  65
Total Bytes Received     Network       10
Total Bytes Transmitted  Network       10
Total Rx Errors          Network       10
Total Tx Errors          Network       10
Load1                    System        5""",
            read="**12줄이 모두 보이면** B2 의 수집 규칙이 제대로 동작하는 것입니다. `samples` 는 60초마다 수집한 횟수(디스크 · 프로세서처럼 인스턴스가 여러 개인 카운터는 더 많음)입니다. 쿼리는 마지막 수신 시각 `last_seen` 열도 계산하지만, 예시에서는 지면상 뺐습니다.",
        )
        + walk(
            c4_d,
            [
                (
                    "",
                    "Connection Monitor 결과에서 AOAI 대상만 (kq 로 감싸서 실행)",
                    "B7 의 Connection Monitor 가 30초마다 잰 결과 테이블(`NWConnectionMonitorTestResult`)에서 목적지가 `*.openai.azure.com` 인 것만 고릅니다. **B7 을 하지 않았다면 이 쿼리는 0행이 정상입니다.**",
                ),
                (
                    "| summarize avg_rtt_ms",
                    "1분 단위로 RTT · 실패 집계",
                    "`avg(AvgRoundTripTimeMs)` · `max(MaxRoundTripTimeMs)` — 그 1분의 **평균 · 최대 왕복 시간(RTT, ms)**, `sum(ChecksFailed)` · `sum(ChecksTotal)` — **실패한 검사 수와 전체 검사 수**입니다. 테스트 이름(`TestConfigurationName`)별로 나눕니다.",
                ),
            ],
            cap="Connection Monitor — VM → AOAI:443 연결 시간 (B7 을 했을 때만 · 최근 1일)",
            lang="kql",
        )
        + out(
            """TimeGenerated         TestConfigurationName  avg_rtt_ms  max_rtt_ms  failed  total
--------------------  ---------------------  ----------  ----------  ------  -----
2026-10-23T12:58:00Z  tcp443                 1.45        2.09        0       6
2026-10-23T12:59:00Z  tcp443                 1.48        1.96        0       6
2026-10-23T13:00:00Z  tcp443                 3.99        10.68       0       6
2026-10-23T13:01:00Z  tcp443                 1.49        1.89        0       6""",
            label="예상 결과 (이 실습의 실제 값 — 소수점 아래는 줄였습니다)",
            read="같은 리전의 VM → AOAI TCP 연결은 **평균 약 1.5ms**, 가끔 10ms 정도로 튀고 **실패(`failed`)는 0** 입니다 → **평소 기준선**입니다. 이 값이 수십~수백 ms 로 커지거나 `failed` 가 늘면 VM → AOAI **경로**(방화벽 · NAT · 프록시)를 의심하고 C5 표의 해당 행으로 가세요.",
        ),
        scope="check",
    )

    # ───────── C5
    rows = [
        ("1", "진단 설정 저장", "<code>az monitor diagnostic-settings list</code>", "RequestResponse · Audit · AllMetrics 설정이 보임", "ok", "B1"),
        ("2", "AOAI 로그 도착", "C1 · 부록 E 의 <code>aoai_requestresponse_check</code>", "약 20분 내 행이 보이고 properties_s 에 본문이 없음", "ok", "properties_s: 토큰 수 · 길이 · 배포 이름만"),
        ("3", "요청 ID 대조", "C2", "apim_request_id = CorrelationId", "ok", "x-request-id 는 불일치"),
        ("4", "호출 로그 1줄", "B3 의 journalctl", "ok / client_timeout / error + 토큰 수", "ok", "ok · timeout · 404 모두 확인"),
        ("5", "App Insights 수집", "<code>AppDependencies</code> 의 Target 필터", "시도마다 행 + aoai_call 로그 (수 초~수십 초 내)", "ok", "200 · 0(timeout) · 404"),
        ("6", "AMA 연결", "부록 E 의 <code>ama_heartbeat</code> · C4 의 카운터 쿼리", "Heartbeat · Perf 는 설치 후 약 10분 내, local5(probe)는 B4 실행 후, cron 은 실제 작업이 돈 뒤(최대 약 1시간)", "ok", "카운터 12종 · cron · local5"),
        ("7", "시계 동기화", "VM 에서 <code>timedatectl</code> (아래 상자)", "System clock synchronized: yes", "ok", "RHEL 9.8 기본값"),
        ("8", "probe 동작", "<code>systemctl list-timers</code> · C4 의 probe 쿼리", "1분마다 JSON 줄, rc=0", "ok", "관리 ID 인증 · wait_ms 정상"),
        ("9", "알림 시험", "B6 의 알림 조회", "알림이 울림(<code>Fired</code>)", "ok", "aoai-499 · app-client-timeout"),
    ]
    tr = "".join(f'<tr><td>{a}</td><td><b>{b}</b></td><td>{c}</td><td>{d}</td><td class="{e}">✔</td><td>{f}</td><td class="mine">☐</td></tr>' for a, b, c, d, e, f in rows)
    c5 = step(
        "c5",
        "적용 직후 확인 체크리스트 9가지 — 이번 실습 결과",
        "C5",
        "적용 직후 점검할 9가지 · 오른쪽 ‘내 결과’ 칸에 직접 체크하세요(‘이번 실습 결과’는 이 가이드를 직접 돌려 본 값)",
        brief(
            what="로그 수집 설정이 **제대로 적용됐는지** 9가지를 점검합니다(표). 그리고 분석 결과를 **원인 구간으로 해석하는 표**(‘읽는 법’)를 봅니다.",
            why="한 가지라도 빠지면 장애 때 필요한 데이터가 없습니다. 적용 직후에 확인해 두면 ‘그때 켜 둘걸’ 하는 일을 막습니다.",
            result="9개 항목이 모두 ✔ 이면 준비 완료입니다.",
            apply="내 환경에 적용한 뒤 **같은 9가지를 점검**하세요. ‘확인 방법’의 이름(C1 · C2 · B3 …)은 이 문서의 단계입니다.",
        )
        + "<table><thead><tr><th>#</th><th>항목</th><th>확인 방법</th><th>기대</th><th class='res'>이번 실습 결과</th><th>실측 메모</th><th>내 결과</th></tr></thead><tbody>"
        + tr
        + "</tbody></table>"
        + code(
            "vmrun <<'VMEOF'\ntimedatectl | grep -i synchronized\nVMEOF",
            cap="7번 확인 — VM 의 시계가 동기화됐는지 (확인용 명령 · 실행 블록 아님)",
        )
        + md("`System clock synchronized: yes`(RHEL 7 · 8 은 `NTP synchronized: yes`)가 나오면 정상입니다. 앱 · AOAI · VM 의 시각을 서로 비교하므로 시계가 어긋나 있으면 ‘같은 순간’을 잘못 짝지을 수 있습니다.")
        + call(
            "info",
            "읽는 법 — 신호의 조합으로 원인 구간을 구분합니다",
            "느린 호출을 만났을 때 **어느 신호가 같이 나빠졌는지**로 원인 구간을 좁힙니다. 이 실습에서 직접 재현되는 것은 **마지막 행(499 ≈ timeout) 하나**뿐이고, 나머지는 내 환경에서 마주쳤을 때 읽는 방법입니다.",
        )
        + "<table><thead><tr><th>관측되는 패턴</th><th>해석</th><th>다음 행동</th></tr></thead><tbody>"
        "<tr><td>앱만 길고 AOAI 처리 시간은 정상(gap 이 큼)</td><td>AOAI 바깥 — SDK 호출 구간의 연결 · 네트워크 · 재시도 대기 등 (호출 <i>전</i>의 작업 큐는 <code>total_ms</code> 밖이라 별도 계측)</td><td>앱의 동시 호출 수(<code>inflight</code>)와 호출 전 작업 큐를 계측하고, probe(VM 안)의 연결 시간도 확인합니다</td></tr>"
        "<tr><td>앱 지연이 정각 · 30분 cron · CPU 상승과 겹침</td><td>VM 자원 · 스케줄 작업 경합</td><td>Syslog(cron)와 스냅샷으로 그 시각에 도는 작업을 찾고, 배치를 몇 분씩 어긋나게 하거나 다른 서버로 옮깁니다</td></tr>"
        "<tr><td>앱 · probe(VM 안)만 느리고 probe(VM 밖)는 정상</td><td>VM → AOAI 경로(방화벽 · DNS · SNAT)</td><td>probe 의 <code>dns_ms</code> · <code>tcp_ms</code> 가 커졌는지 보고, 방화벽 SNAT 사용률 · Connection Monitor(B7)로 경로를 확인합니다</td></tr>"
        "<tr><td>앱 · AOAI · probe 모두 느림</td><td>AOAI 서비스 · 공유 용량</td><td><code>apim_request_id</code> · 시각 · 메트릭을 첨부해 Support Case 를 엽니다(아래 상자)</td></tr>"
        "<tr><td>AOAI 에 499, 처리 시간이 앱 timeout 과 비슷</td><td>앱 timeout 이 먼저 끊음(긴 출력 · 큰 입력)</td><td>앱 timeout 을 늘리거나 <code>max_tokens</code> 를 줄이고, 스트리밍(응답을 생성되는 대로 조각으로 받는 방식)을 검토합니다. 재시도가 겹쳐 호출이 중복되는지도 확인합니다</td></tr>"
        "</tbody></table>"
        + details(
            "Support Case 를 열 때 첨부하면 좋은 정보",
            md(
                """
                위 표에서 ‘AOAI 서비스 · 공유 용량’ 쪽으로 보일 때 Azure 지원 팀(포털의 **도움말 + 지원 → 새 지원 요청**)에 아래를 함께 알려 주면 서버 쪽에서 해당 요청을 찾기 쉽습니다.
                - **증상이 있던 시각 범위(UTC)** 와 AOAI 리소스 ID · 배포 이름 · 리전
                - **느린 요청 몇 건의 `apim_request_id`**(필요하면 `x-request-id` 도) — C2 쿼리 ① 의 마지막 줄을 `order by aoai_ms desc` 로 바꾸면 위로 올라오는, gap 이 작고 `aoai_ms` 가 큰 행
                - 앱이 잰 시간(`total_ms`)과 AOAI 가 잰 시간(`DurationMs`) 대조 결과(C2) · probe 결과(C4)
                - 어느 신호가 같이 나빠졌는지(위 표의 어느 행에 해당하는지)
                """
            ),
        ),
        scope="check",
    )

    sec_c = section("c", "C · 확인과 분석", "로그가 실제로 쌓였는지 확인하고, 지연이 생긴 구간을 찾아냅니다", c1 + c2 + c3 + c4 + c5)

    # ───────── D
    d1 = step(
        "d1",
        "정리 — 비용 중지 또는 전체 삭제",
        "D",
        "실습이 끝나면 꼭 실행하세요",
        brief(
            what="실습 리소스를 **잠시 멈추거나(A)** **전부 삭제(B)** 합니다. (A) 와 (B) 는 별도의 코드 블록입니다.",
            why="VM · 공용 IP · 디스크 · 로그 저장은 **계속 요금이 나옵니다.** 또 알림이 켜져 있으면 메일이 계속 옵니다.",
            result="(A) VM 컴퓨팅 과금 중지 또는 (B) 모든 실습 리소스 삭제.",
            apply="**내 운영 환경에서는 이 단계를 실행하지 마세요.** 이 단계는 이 가이드로 만든 실습 리소스 전용입니다. 내 환경에 적용한 설정은 [부록 B](#x2) 3번의 ‘되돌릴 것’ 목록을 따라 정리하세요.",
            caution="(B) 는 **되돌릴 수 없습니다.** 코드에 안전 확인(태그 검사)을 넣었지만, 그래도 `echo $RG` 로 리소스 그룹 이름이 실습 것이 맞는지 먼저 눈으로 확인하세요.",
        )
        + walk(
            """# (A) 잠시 멈추기 — VM 컴퓨팅 과금 중지 (디스크·공용 IP 요금은 남음). 다시 켤 때: az vm start -g $RG -n $VM
az vm deallocate -g $RG -n $VM""",
            [
                (
                    "# (A)",
                    "(A) 잠시 멈추기 — VM 할당 해제",
                    "`az vm deallocate` 는 VM 을 **할당 해제**해 컴퓨팅 요금을 멈춥니다(디스크 · 공용 IP 요금은 계속). 나중에 `az vm start -g $RG -n $VM` 으로 다시 켭니다. **(A) 와 (B) 는 따로 복사해 실행하세요 — (A) 만 하면 리소스는 그대로 남습니다.**",
                ),
            ],
            cap="(A) 잠시 멈추기",
            run="D",
            skip=True,
        )
        + walk(
            """# (B) 전부 삭제 — 먼저 이 리소스 그룹이 실습 그룹(태그 purpose=aoai-logging-lab)인지 확인하고, 맞을 때만 지웁니다
if [ "$(az group show -n $RG --query tags.purpose -o tsv)" = "aoai-logging-lab" ]; then
  # ① Connection Monitor · flow log 는 리소스 그룹 밖(NetworkWatcherRG)에 만들어져 그룹 삭제로 지워지지 않으니 먼저 지웁니다
  #    이름이 고정이라 남의 것일 수 있으므로, 이 실습의 VM · VNet 을 가리키는 것만 지웁니다
  VM_ID=$(az vm show -g $RG -n $VM --query id -o tsv)
  VNET_ID=$(az network vnet show -g $RG -n $VNET --query id -o tsv)
  az network watcher connection-monitor show -l $LOC -n cm-vm-to-aoai -o json 2>/dev/null | grep -qi "$VM_ID" && az network watcher connection-monitor delete -l $LOC -n cm-vm-to-aoai
  az network watcher flow-log show -l $LOC -n vnetfl-agent -o json 2>/dev/null | grep -qi "$VNET_ID" && az network watcher flow-log delete -l $LOC -n vnetfl-agent
  # ② 리소스 그룹째 삭제 (알림 · 수집 규칙 · AOAI · VM · 저장소 모두 포함)
  az group delete -n $RG --yes --no-wait
  rm -f id_lab id_lab.pub lablog.env                     # 임시 SSH 키와 변수 파일
else
  echo "중단: $RG 는 실습 리소스 그룹(purpose=aoai-logging-lab 태그)이 아닙니다 — 아무것도 지우지 않았습니다"
fi""",
            [
                (
                    "# (B)",
                    "(B) 안전 확인 — 실습 그룹이 맞을 때만 지우기",
                    """
                    **되돌릴 수 없는 삭제**라서 먼저 확인합니다.
                    * `az group show -n $RG --query tags.purpose -o tsv` — 리소스 그룹의 `purpose` **태그 값**만 출력합니다. A2 에서 이 가이드가 만든 그룹에는 `purpose=aoai-logging-lab` 이 붙어 있습니다.
                    * `if [ "…" = "aoai-logging-lab" ]; then … else … fi` — 태그가 **맞을 때만** 안쪽 삭제 명령을 실행하고, 아니면 `else` 의 메시지만 출력하고 아무것도 지우지 않습니다. (`$RG` 가 비어 있거나 다른 그룹을 가리키는 실수를 막아 줍니다.)
                    * 아래 ① 의 두 줄은 **리소스 그룹 밖**(`NetworkWatcherRG`)의 리소스를 지우므로 태그 검사만으로는 막을 수 없습니다. 그래서 다음 구간에서 따로 확인합니다.
                    """,
                ),
                (
                    "VM_ID=",
                    "(B) ① 이 실습의 VM · VNet ID 알아내기",
                    "Connection Monitor 와 flow log 는 이름이 **고정**(`cm-vm-to-aoai` · `vnetfl-agent`)이라, 같은 구독의 **다른 사람이 만든 같은 이름**일 수 있습니다. 그래서 이 실습의 VM 과 VNet 의 리소스 ID 를 먼저 구해 둡니다.",
                ),
                (
                    "az network watcher connection-monitor show",
                    "(B) ① Connection Monitor — 내 VM 을 가리킬 때만 삭제",
                    "`connection-monitor show … -o json` 으로 설정을 JSON 으로 읽어 **이 실습의 VM ID 가 들어 있는지**(`grep -qi` = 대소문자 무시, 출력 없이 있으면 성공) 확인하고, **있을 때만 `&&` 뒤의 삭제**를 실행합니다. 없거나(B7 을 안 했음) 다른 VM 것이면 아무것도 지우지 않습니다. `2>/dev/null` 은 ‘없음’ 오류 출력을 숨깁니다.",
                ),
                (
                    "az network watcher flow-log show",
                    "(B) ① flow log — 내 VNet 을 가리킬 때만 삭제",
                    "같은 방식으로 flow log 설정에 **이 실습의 VNet ID** 가 들어 있을 때만 삭제합니다.",
                ),
                (
                    "# ② 리소스 그룹째 삭제",
                    "(B) ② 리소스 그룹째 삭제",
                    "`--yes` 로 확인 없이, `--no-wait` 로 **삭제 완료를 기다리지 않고** 즉시 반환합니다. 그룹 안의 **알림 · 수집 규칙 · AOAI · VM · 저장소 등이 모두** 지워집니다. 삭제는 백그라운드에서 몇 분 걸리며, 끝났는지는 `az group exists -n $RG` 가 `false` 인지로 봅니다.",
                ),
                (
                    "rm -f id_lab",
                    "(B) ③ 내 컴퓨터의 임시 파일 삭제 · 안전 확인 실패 시",
                    "A4 에서 만든 임시 SSH 키(`id_lab`, `id_lab.pub`)와 변수 파일 `lablog.env` 를 지웁니다. 그 아래 `else` 쪽은 **태그가 맞지 않을 때** 위의 어떤 삭제도 하지 않고 안내만 출력하는 부분입니다.",
                ),
            ],
            cap="(B) 전부 삭제 — 되돌릴 수 없음",
            run="D",
            skip=True,
        )
        + call(
            "info",
            "소프트 삭제",
            "AOAI 계정과 Log Analytics 워크스페이스는 삭제 후에도 일정 기간 ‘소프트 삭제’ 상태로 이름이 남습니다. 이 실습은 이름에 **무작위 접미사**(`$SFX`)를 붙여서 다시 실행해도 충돌하지 않습니다. 같은 이름을 꼭 다시 쓰려면 `az cognitiveservices account purge -g <리소스 그룹> -n <AOAI 이름> -l <리전>` 로 AOAI 를 영구 삭제하세요.",
        ),
        scope="clean",
    )
    sec_d = section("d", "D · 정리", "", d1)

    # ───────── 부록
    facts = [
        ("R1 진단 설정", "ok", "설정 후 약 20~26분 뒤부터 요청이 기록됨(그 전 호출은 기록되지 않음, 2회 반복 확인) · 이후 지연 평균 약 2분. <code>properties_s</code>(JSON)에 promptTokens · completionTokens · streamType · 배포/모델 이름 · 요청/응답 길이, <b>본문 없음</b>, 호출자 IP 끝자리 마스킹"),
        ("요청 ID 대조", "ok", "<code>apim-request-id</code> = <code>CorrelationId</code>. <code>x-request-id</code> 는 불일치, <code>x-ms-client-request-id</code> 는 AOAI 로그에 남지 않음"),
        ("499 의 의미", "ok", "클라이언트 read timeout 1.0초 → AOAI <code>499</code>(DurationMs≈1.06초, 응답 길이 0). 앱은 <code>client_timeout</code>(1.03초)"),
        ("404 (없는 배포)", "ok", "앱 dependency 404 로는 보이지만 AOAI 지표 · 로그에는 없음"),
        ("R2 메트릭", "ok", "StatusCode 200 · 499 (숫자 문자열). <code>AzureOpenAITTLTInMS</code> · 토큰 지표에 값 있음, 신형 <code>TimeToLastByte</code> · <code>TimeToResponse</code> · <code>NormalizedTimeBetweenTokens</code> 계열은 이 환경에서 값 없음. AzureMetrics 지연 7~10분"),
        ("R3 호출 로그", "ok", "ok · client_timeout · error 기록, 응답 헤더 3종(<code>x-request-id</code> · <code>apim-request-id</code> · <code>x-ms-region</code>) 확인"),
        ("R4 App Insights", "ok", "dependency 200 · ResultCode 0(timeout, Success=false) · 404, <code>httpx2.ReadTimeout</code> 예외, 지연 약 10초. 부가 dependency(<code>settings.sdk.monitor.azure.com</code> · <code>169.254.169.254</code>)가 섞이므로 Target 필터 필요. <b>Python 3.10+ 필요</b>(RHEL 9 기본 3.9)"),
        ("앱 vs AOAI 시간", "ok", "같은 리전의 성공 호출 67건: 앱 시간 − AOAI 시간 = 중앙값 83ms · p95 104ms · 최대 232ms(C2 기준선 쿼리), 토큰 수 일치"),
        ("R5 에이전트", "ok", "AMA 1.45 · 성능 카운터 12종 · cron / local5 syslog · Heartbeat. 지연: Perf · Syslog 약 2분, Heartbeat 약 5초"),
        ("R6 네트워크", "part", "Connection Monitor(RHEL 9.8)와 VNet flow log 는 정상. Azure Firewall 은 진단 설정(AZFW* 전용 테이블 · SNAT 지표)만 확인 — <b>방화벽을 거치는 트래픽은 미검증</b>"),
        ("R7 probe", "ok", "관리 ID 인증 · 1분 타이머 · syslog 수집 정상. 실습 중 2건 수정(<code>--http1.1</code>, <code>systemd-run</code>)"),
        ("R8 알림", "ok", "<code>aoai-499</code>(메트릭) · <code>app-client-timeout</code>(로그) 알림이 울리는 것을 확인. 수신 메일 도착은 수신자가 확인"),
        ("분석 쿼리", "ok", "분석 쿼리 28개(부록 E)를 실제 워크스페이스에서 모두 오류 없이 실행 (데이터가 없는 방화벽 · 가용성 테스트 쿼리는 0행)"),
        ("수집량", "ok", "VM 1대 + 분당 약 5회 호출 기준 시간당 약 1MB — 계정당 월 5GB 무료 한도에 견주어 본 값이며, 실제 청구는 요금제 · 구독에 따라 다릅니다(비용은 본인 청구 화면으로 확인)"),
    ]
    ftr = "".join(f'<tr><td><b>{a}</b></td><td class="{b}">{"✔" if b == "ok" else "△"}</td><td>{c}</td></tr>' for a, b, c in facts)
    appx_a = step(
        "x1",
        "실제 환경에서 확인한 사실",
        "부록 A",
        "2026-10-23 · Korea Central · RHEL 9.8 · Azure CLI 2.86 · openai 3.37 · azure-monitor-opentelemetry 1.8.11 · 2회 검증(단계별 적용 → 이 문서의 실행 코드 블록을 새 리소스 그룹에서 그대로 재실행). 선택 Firewall 블록은 따로 실행했고 정리(D)는 실행하지 않았으며, 2026-10-25 개정에서는 설명만 고쳐 전체 실습을 다시 돌리지 않았습니다(README)",
        "<table><thead><tr><th>항목</th><th class='res'>결과</th><th>실측 내용</th></tr></thead><tbody>" + ftr + "</tbody></table>"
        + md("✔ = 확인함 · △ = 일부만 확인함. 같은 환경에서 잰 값이므로 운영 계획에는 본인 환경에서 다시 측정하세요."),
        done=False,
    )
    apply_vars = table(
        ["이 가이드의 변수", "내 환경에서는", "내 값 찾는 법 (예)"],
        [
            ["`RG` · `VM_RG`", "AOAI · VM 이 있는 리소스 그룹(둘이 다르면 각각)", "`az group list --query \"[].name\" -o tsv`"],
            ["`AOAI` · `AOAI_HOST`", "내 AOAI 리소스 이름과 호출 주소의 호스트(`<이름>.openai.azure.com`, 커스텀 도메인이면 그 주소)", "`az cognitiveservices account list --query \"[].{name:name, rg:resourceGroup, kind:kind}\" -o table` · 앱의 endpoint 설정값"],
            ["`DEP`", "앱이 부르는 **배포 이름**(모델 이름이 아닙니다)", "`az cognitiveservices account deployment list -g $RG -n $AOAI -o table`"],
            ["`VM`", "앱이 실행되는 VM 이름", "`az vm list --query \"[].{name:name, rg:resourceGroup}\" -o table`"],
            ["`LAW`", "로그를 모을 Log Analytics 워크스페이스의 **리소스 ID**", "`az monitor log-analytics workspace list --query \"[].{name:name, rg:resourceGroup, id:id}\" -o table` (구독 전체에서 찾아 하나를 고릅니다)"],
            ["`APPI`", "Application Insights 이름(워크스페이스 기반)", "`az monitor app-insights component show -g <Application Insights 리소스 그룹> --query \"[].{name:name, id:id}\" -o table`"],
            ["`MAIL`", "알림을 받을 메일 주소", "—"],
        ],
    )
    apply_steps = table(
        ["단계", "내 환경에서는"],
        [
            ["A1 ~ A3", "**하지 않습니다**(실습용 리소스를 새로 만드는 단계). A1 의 도우미 함수(`vmrun` · `kq`)와 변수 파일만 필요하면 가져다 씁니다."],
            ["A4", "VM 을 새로 만들지 않고 **① 내 VM 에 관리 ID 켜기 ② 그 ID 에 `Cognitive Services OpenAI User` 역할 부여**만 합니다."],
            ["A5", "**하지 않습니다**(데모 앱용 Python 설치). 단, 내 앱이 **Python 3.10 이상**인지 확인합니다(R4 패키지 요구)."],
            ["B1 · B2 · B5", "**그대로** 적용합니다(각 단계 맨 위 ‘내 환경에서는’ 상자의 사전 확인 먼저)."],
            ["B4", "**전체를 그대로 붙이지 말고** 구간 2~15(파일들)와 구간 17(설치 · 설정)만 가져가세요(구간 16 은 실습용 웹 서버). 구간 17 의 `AOAI_ENDPOINT` · `AOAI_DEPLOYMENT` · `APP_URLS` 를 내 값으로 바꿉니다."],
            ["B3", "데모 앱은 설치하지 않고 **R3 헬퍼 추가 + 호출 감싸기 + 시작 코드 2줄 + 환경변수 4개**만 내 앱에 적용합니다."],
            ["B6", "리소스 그룹 · 메일 · 리소스 ID 를 바꾸고 **임계값을 운영 기준에 맞게** 조정합니다."],
            ["B7", "경로에 방화벽 · 프록시가 있을 때만. 시작 전 같은 이름이 있는지 확인합니다."],
            ["C1 ~ C5", "쿼리 속 VM 이름 · 기간(`ago(…)`)을 바꿔 실행합니다."],
            ["D", "**실행하지 않습니다**(실습 리소스 전용)."],
        ],
    )
    mi_code = code(
        """# pip install azure-identity   (키 대신 관리 ID 로 인증하는 표준 패턴)
import os
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI, Timeout

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_ad_token_provider=token_provider,      # api_key 대신 이것
    api_version="2024-10-21",
    timeout=Timeout(5.0, read=60.0), max_retries=0)""",
        cap="키 없이 관리 ID 로 인증하는 클라이언트 (설명용 · 이 실습의 데모 앱에는 적용해 실행하지 않음)",
        lang="python",
        nocopy=True,
    )
    appx_b = step(
        "x2",
        "내 환경에 적용하기",
        "부록 B",
        "실습이 아니라 **내 앱 · 내 구독**에 적용할 때 무엇을 바꾸는지",
        md("이 가이드의 코드는 실습용 이름(`rg-lablog-…` 등)으로 쓰여 있습니다. 내 환경에 적용할 때 바꿔야 할 값과 하지 않아도 되는 단계를 정리했습니다. 각 단계 맨 위 **‘내 환경에서는’** 상자와 코드 해설의 **‘실습 전용’ / ‘내 환경에도’** 이름표도 같은 기준입니다.")
        + md("**1. 내 값 찾는 법**")
        + apply_vars
        + md("이 가이드의 도우미 함수는 **VM 과 워크스페이스가 같은 리소스 그룹(`$RG`)에 있다**고 가정합니다. 다르면 `vmrun` 의 `-g \"$RG\"` 는 VM 의 리소스 그룹(`$VM_RG`)으로, `kq` 의 `-g \"$RG\"` 는 워크스페이스의 리소스 그룹으로 바꿔 `lablog.env` 에 넣으세요. 아래는 **내 환경용 `lablog.env` 최소 예시**입니다.")
        + code(
            '''# 내 환경용 lablog.env 최소 예시 — 값을 내 것으로 바꿔 저장한 뒤 source lablog.env
export SUB="<구독 ID>" LOC=koreacentral
export RG=<AOAI · VM · 워크스페이스가 있는 리소스 그룹> VM_RG=$RG
export LAW_NAME=<워크스페이스 이름> AOAI=<AOAI 이름> AOAI_HOST=$AOAI.openai.azure.com DEP=<배포 이름> VM=<VM 이름> MAIL="<알림 받을 이메일>"
export LAW=$(az monitor log-analytics workspace show -g $RG -n $LAW_NAME --query id -o tsv)
# vmrun · kq 도우미 함수는 A1 에서 lablog.env 에 덧붙인 두 함수 정의를 그대로 복사해 넣으세요''',
            cap="내 환경용 lablog.env 최소 예시 (설명용 · 값은 내 것으로)",
        )
        + md("**2. 단계별로 무엇을 하나**")
        + apply_steps
        + md("**3. 진단이 끝난 뒤 되돌릴 것**")
        + md(
            """
            - **`max_retries=0`(자동 재시도 끔)** — 진단용 설정입니다. 끝나면 원래 값(SDK 기본 2회)으로 되돌립니다. 끈 채로 두면 일시적인 429 · 5xx 에서 자동 재시도가 사라져 실제 실패가 늘 수 있습니다.
            - **`OTEL_TRACES_SAMPLER=always_on`** — 모든 호출을 기록하므로 호출이 많은 앱에서는 수집량 · 비용이 늘 수 있습니다. 진단이 끝나면 기본 샘플링으로 되돌리는 것을 검토하세요.
            - **알림 4개 · probe · 진단 설정** — 계속 쓸지, 끌지 정합니다(B6 의 ‘알림 메일이 옵니다’ 상자에 끄는 명령이 있습니다). 진단 설정 · 수집 로그는 **계속 비용이 발생**합니다.
            """
        )
        + md("**4. 키 대신 관리 ID 로 인증하기** — 데모 앱은 단순함을 위해 API 키를 쓰지만, 운영 앱은 관리 ID 를 권장합니다(probe 는 이미 관리 ID 를 씁니다). 아래는 Azure 문서의 표준 패턴이며, **이 실습에서는 데모 앱에 적용해 실행해 보지 않았습니다.** 관리 ID 에는 A4 의 `Cognitive Services OpenAI User` 역할이 필요합니다.")
        + mi_code
        + md("**5. R3 헬퍼의 한계** — R3 의 `call_log` 는 **한 번에 응답을 다 받는 일반(비스트리밍) 호출**을 기준으로 만들고 검증했습니다. `stream=True` 로 받는 앱은 `with` 블록이 끝나는 시점이 ‘스트림 완료’와 다를 수 있어 `total_ms` 의 의미(첫 토큰까지인지 전체인지)를 따로 정해야 하고, 비동기(`AsyncAzureOpenAI`) 앱에서는 호출 부분을 같은 방식으로 감싸 쓰되 **이 실습에서는 검증하지 않았습니다.**")
        + md("**6. Python 이 아닌 앱** — R3 가 남기는 **필드 이름**(`event` · `cid` · `inflight` · `total_ms` · `outcome` · `apim_request_id` …)을 그대로 유지하면 C 단계의 쿼리를 그대로 쓸 수 있습니다. Application Insights 연결은 해당 언어의 Azure Monitor OpenTelemetry 배포판(.NET · Java · Node.js · Python 지원)을 쓰며, 이 실습에서는 Python 만 검증했습니다. 아래는 **C 단계의 쿼리가 읽는 필드**입니다(한 호출 = JSON 한 줄을 로그 메시지로 남깁니다).")
        + table(
            ["필드", "값", "읽는 쪽"],
            [
                ["`event`", "항상 `aoai_call`", "모든 쿼리 · 알림 `Q1` 이 `Message has \"aoai_call\"` 로 이 줄을 찾음"],
                ["`outcome`", "`ok` · `client_timeout` · `error`", "알림 `Q1` · C2 · 부록 E"],
                ["`total_ms`", "AOAI 호출 구간에 걸린 시간(ms, 정수)", "C2 · C3 · 부록 E"],
                ["`apim_request_id`", "응답 헤더 `apim-request-id` 값", "C2 (AOAI 의 `CorrelationId` 와 조인)"],
                ["`inflight`", "호출 시작 시점의 동시 호출 수", "C3 의 `app_by_minute_of_hour`"],
                ["`deployment` · `status` · `request_id` · `region` · `prompt_tokens` · `completion_tokens` · `finish_reason` · `cid`", "부가 정보", "진단 · 부록 E 일부"],
            ],
        ),
        done=False,
    )
    trouble = table(
        ["증상", "확인 · 해결"],
        [
            ["`$RG` 같은 변수가 비어 있다는 오류 · `kq` / `vmrun` 이 `command not found`", "새 터미널이라 변수와 함수가 없는 것입니다. 작업 폴더에서 `source lablog.env` 를 실행하세요(A1)."],
            ["`az` 가 확장이 없다고 하거나 설치를 묻는 경우", "A1 의 확장 설치 명령(`for e in application-insights …`)을 다시 실행하세요."],
            ["`vmrun` 이 ‘Conflict / another operation in progress’", "이전 run-command 가 끝나기를 기다린 뒤 다시 실행합니다."],
            ["AOAI 로그(AzureDiagnostics)가 안 보임", "설정 후 20분 이상 기다립니다. `journalctl -u report-agent` 로 앱이 호출 중인지, B1 의 진단 설정이 켜져 있는지 확인합니다."],
            ["AppDependencies 에 AOAI 호출이 없음", "`OTEL_TRACES_SAMPLER=always_on` · 연결 문자열 · Python 3.10+ · 아웃바운드 443(`*.in.applicationinsights.azure.com`)을 확인합니다. `Target has \"openai.azure.com\"` 로 필터하세요."],
            ["Perf · Syslog 가 없음", "`az vm extension list -g $RG --vm-name $VM -o table` 로 AzureMonitorLinuxAgent 상태, DCR 연결(B2), `systemctl is-active rsyslog` 를 확인합니다."],
            ["모델 배포가 실패 / 쿼터 부족", "다른 리전(예: swedencentral)이나 모델로 바꿀 때는 `LOC` · 모델 이름뿐 아니라 **그 리전의 지원 여부 · 모델 버전 · 배포 SKU/용량 · 준비물의 쿼터 확인 필터 · API 버전**을 함께 확인하세요. 추론 모델은 `max_tokens` 대신 `max_completion_tokens` 로 코드를 바꿔야 합니다."],
            ["알림 메일이 안 옴", "스팸함과 **수신자 확인 메일(OTP)** 을 마쳤는지 확인하고(B6), 액션 그룹 수신자(`az monitor action-group show -g $RG -n ag-aoai-latency`)를 확인합니다. 알림이 울렸는지는 B6 의 `az rest` 목록(`Fired`)으로 봅니다."],
            ["`MissingSubscriptionRegistration` / ‘subscription is not registered’ 오류", "A1 의 `az provider register` 가 아직 끝나지 않은 것입니다. `az provider show -n Microsoft.CognitiveServices --query registrationState -o tsv` 가 `Registered` 가 될 때까지 몇 분 기다린 뒤 다시 실행합니다(다른 네임스페이스도 같은 방식)."],
            ["VM 생성이 크기 · 코어 한도 오류(`SkuNotAvailable` 등)로 실패", "`az vm list-skus -l $LOC --size Standard_B2 -o table` 로 쓸 수 있는 크기(`Restrictions` 가 `None` 인 것)를 보고 A4 의 `--size` 를 바꾸세요. 코어 한도 오류라면 구독의 vCPU 쿼터를 확인합니다."],
            ["`az login` 이 브라우저를 열지 못함", "`az login --use-device-code` 로 표시되는 코드를 다른 기기의 브라우저에 입력합니다."],
            ["A5 의 curl 결과가 `401` 이 아님", "`000` = 연결 자체가 안 됨(DNS · 방화벽 · 네트워크 · Private Endpoint 확인), `404` = 배포 이름(`DEP`) 오류, `403` = 네트워크 규칙으로 차단(방화벽 · 허용 IP 확인)."],
            ["`systemctl is-active report-agent` 가 `active` 가 아님", "`journalctl -u report-agent -n 30 --no-pager` 로 오류를 봅니다. 흔한 원인: A5 의 Python 패키지 설치 실패, `/etc/report-agent/app.env` 의 주소 · 키 · 배포 이름 오타."],
            ["probe(B4)의 `code` 가 401 / 403", "VM 의 관리 ID 에 `Cognitive Services OpenAI User` 역할이 있는지(A4) 확인합니다. 역할 부여 직후에는 **반영에 몇 분** 걸릴 수 있으니 잠시 뒤 다시 확인합니다."],
            ["`429 Too Many Requests`", "배포의 분당 토큰 · 요청 한도를 넘은 것입니다. 실습의 데모 앱은 호출이 적어 드뭅니다. 운영에서는 배포 용량(쿼터)과 재시도 설정(`max_retries`)을 확인합니다."],
            ["쿼리 결과가 비어 있음", "① AOAI 로그는 B1 설정 후 20~26분 뒤부터 ② 쿼리의 시간 범위(`ago(…)`) ③ VM 이름 · 변수(`source lablog.env`)를 확인합니다."],
        ],
    )
    appx_c = step("x3", "문제 해결", "부록 C", None, md("표의 `journalctl` · `systemctl` · `cat /etc/redhat-release` 같은 **VM 안 명령**은 내 컴퓨터가 아니라 VM 안에서 실행합니다 — `vmrun <<'X'` 다음 줄에 명령을 쓰고 `X` 로 닫으면 됩니다(A1 의 도우미 함수).") + trouble, done=False)
    prod = md(
        """
        - **키 대신 관리 ID**: 이 실습의 데모 앱은 단순함을 위해 키를 쓰지만, 운영 앱은 관리 ID(`azure_ad_token_provider`)를 권장합니다([부록 B](#x2)). probe 는 이미 관리 ID 입니다.
        - **기존 진단 설정**: 진단 설정은 리소스당 최대 5개이고 Azure Policy 가 이미 만들었을 수 있습니다 — B1 전에 확인하세요.
        - **방화벽 허용 목록**: VM 아웃바운드 443 에 Application Insights(`*.in.applicationinsights.azure.com`) · Azure Monitor Agent · 워크스페이스 FQDN 을 허용해야 합니다. 정확한 목록은 Microsoft Learn 의 ‘Azure Monitor Agent 네트워크 구성’ 문서를 확인하세요.
        - **워크스페이스 통일 · 시간 동기화(NTP)**: 앱 · AOAI · VM 로그를 같은 워크스페이스에, 시각은 UTC 기준으로 비교합니다. 일일 상한(daily cap)은 걸지 않습니다.
        - **앱 언어**: Python 이 아니면 [부록 B](#x2) 의 6번을 보세요 — R3 의 필드 이름은 그대로 유지합니다.
        """
    )
    appx_d = step("x4", "운영 환경에 적용할 때 달라지는 점", "부록 D", None, prod, done=False)

    q_rows = [
        ("aoai_requestresponse_check", "AOAI 요청 로그(`AzureDiagnostics` 의 `RequestResponse`) 최근 2시간 20건: 시각 · 작업 이름 · 결과 코드 · 처리 시간 · 상관 ID · 호출자 IP · `properties_s`", "B1 설정 뒤 **로그가 들어오는지** 처음 확인할 때 (C5 의 2번)"),
        ("aoai_by_5min", "AOAI 가 본 호출을 5분 단위로(최근 7일, Completions 계열): 호출 수 · p95 · 최대 · 429 · 499 · 5xx 건수", "AOAI 서비스 쪽 지연 · 오류의 **추이**를 볼 때"),
        ("aoai_minute_of_hour", "최근 14일 AOAI 호출을 ‘시각의 분(0~59)’을 5분 구간으로 묶어: 호출 수 · p95 · 8초 초과 수 · 499 수", "**정각 · 30분 패턴**(매시 같은 분에 느려지는지)을 찾을 때"),
        ("aoai_requestid_match", "앱 로그의 `apim_request_id` 를 넣어 AOAI 로그에서 **같은 요청 한 건**을 찾아 처리 시간 · 결과 · 토큰 수를 보여 줌(`<apim_request_id>` 자리 표시자를 바꿔 실행)", "느린 요청 **한 건**을 AOAI 쪽 기록과 대조할 때"),
        ("app_calls_by_5min", "앱 로그(R3)를 5분 · 배포별로: 호출 수 · p95 · timeout 수 · 재시도 수(`attempt` 필드가 있을 때만 — R3 는 이 필드를 남기지 않으므로 **이 실습에서는 항상 0**. 재시도를 꺼서 시도마다 한 줄로 남기므로 `calls` 에 그대로 보입니다)", "앱이 본 지연의 **추이**"),
        ("app_vs_aoai_by_minute", "앱 로그와 AOAI 로그를 **1분 단위로** 나란히(앱 호출 수 · p95 · timeout / AOAI 호출 수 · p95 · 499)", "앱 로그(R3)만으로 AOAI 와 시간대별 대조(C3 의 쿼리는 Application Insights 기준)"),
        ("app_after_idle", "직전 호출 이후 경과 시간(1분 미만 / 1~5분 / 5분 초과)별 호출 수 · p95 · timeout (직전 호출이 없는 첫 행은 제외)", "**쉬었다 온 첫 호출이 느린지** 볼 때"),
        ("app_by_minute_of_hour", "앱 호출을 시각의 분(0~59)별로: 호출 수 · **최대 동시 호출(`inflight`)** · p95 · timeout", "앱 쪽 **정각 패턴 · 동시 호출 증가** 확인"),
        ("app_dependencies_aoai", "Application Insights 의 AOAI 외부 호출(`AppDependencies`)을 5분 · 결과 코드별: 호출 수 · 실패 수 · p95 · 최대", "R4 가 제대로 들어오는지, 상태 코드별 분포 확인"),
        ("app_dep_vs_aoai_by_minute", "(C3) 앱(Application Insights)과 AOAI 를 1분 단위로 대조, 8초 이상 느린 분만", "시간 패턴 분석 — [C3](#c3)"),
        ("app_vs_aoai_by_request", "(C2) 요청 ID 로 앱 시간과 AOAI 시간을 한 건씩 짝지어 차이 계산", "요청 단위 대조 — [C2](#c2)"),
        ("aoai_tokens_by_5min", "(C3) AOAI 로그만으로 5분 단위 출력 토큰당 처리 시간", "느린 이유가 **출력 길이**인지 확인 — [C3](#c3)"),
        ("probe_by_5min", "(C4) probe 의 5분 요약(구간별 시간 · 실패)", "VM 안 · 밖 비교 — [C4](#c4)"),
        ("vm_cpu_mem", "VM 의 CPU 사용률 · I/O 대기 · 메모리 사용률을 1분 최댓값으로", "지연 시각의 **VM 부하** 확인"),
        ("cron_at_hh00_hh30", "(C4) 정각 · 30분 근처에 실행된 cron 작업", "스케줄 작업 경합 확인 — [C4](#c4)"),
        ("fw_openai_connections", "방화벽 응용 프로그램 규칙 로그에서 `*.openai.azure.com` 연결을 1분 · 원본 IP별로: 연결 수 · 서로 다른 원본 포트 수", "방화벽을 거치는 **연결 수 · 원본 포트 수 추이**(Azure Firewall 이 있을 때). SNAT 고갈 여부는 아래 `fw_snat_utilization` 으로 판단합니다"),
        ("fw_dns_duration", "방화벽 DNS 조회 중 AOAI 도메인: 조회 수 · p95 · 최대 소요(초) · 응답 코드별", "**DNS 가 느린지** 확인(Azure Firewall 이 있을 때)"),
        ("fw_snat_utilization", "방화벽 메트릭 `SNATPortUtilization` 을 1분 최댓값(%)으로", "**SNAT 포트 고갈** 징후 확인"),
        ("cm_aoai_rtt", "Connection Monitor 결과(`NWConnectionMonitorTestResult`) 중 AOAI 대상: 평균/최대 RTT · 실패 검사 수 · 전체 검사 수", "VM → AOAI **연결 시간 · 실패율** 확인(B7)"),
        ("avail_tests", "Application Insights 가용성 테스트 결과(`AppAvailabilityResults`)를 5분 단위로: 실행 · 실패 · 평균/최대 시간", "내 환경에 **가용성 테스트**가 있을 때"),
        ("alert_client_timeout", "(B6 의 Q1) 앱 `client_timeout` 로그만 고르는 알림용 질의", "알림이 보는 조건을 직접 조회해 볼 때"),
        ("alert_probe_slow", "(B6 의 Q2) probe 실패 · 8초 이상 호출만 고르는 알림용 질의", "알림이 보는 조건을 직접 조회해 볼 때"),
        ("ama_heartbeat", "에이전트의 Heartbeat: 최근 30분의 마지막 수신 시각 · 횟수 · OS · 에이전트 버전", "**에이전트(AMA)가 살아 있는지** 확인(C5 의 6번)"),
        ("ama_perf_counters", "(C4) 성능 카운터별 샘플 수", "카운터 12종 수집 확인 — [C4](#c4)"),
        ("ama_syslog_sources", "최근 1시간 Syslog 를 facility · 프로세스별로 건수", "`local5` · `cron` 로그가 들어오는지 확인"),
        ("snapshot_summary", "probe 스냅샷의 요약 JSON(실행 대기 · iowait · 443 연결 수 · TCP 재전송 누계)을 시간순으로", "**지연 순간의 VM 상태** 확인"),
        ("usage_by_table", "`Usage` 테이블로 과금 대상 데이터의 **테이블별 일일 수집량(GB)**", "비용 · 수집량 점검(새 워크스페이스는 몇 시간 늦게 채워짐)"),
        ("billed_by_table", "`_BilledSize` 로 최근 1일 **테이블별 수집량(MB)**", "새 워크스페이스에서 **바로** 수집량을 볼 때"),
    ]
    # 문서가 설명하는 쿼리 이름 = snippets/queries.kql 의 쿼리 이름 (둘이 어긋나면 빌드 실패)
    kql_names = [l.split("|")[0].replace("//##", "").strip() for l in open(SN + "queries.kql", encoding="utf-8").read().split("\n") if l.startswith("//## ")]
    assert sorted(kql_names) == sorted(r[0] for r in q_rows), (set(kql_names) ^ {r[0] for r in q_rows})
    appx_e = step(
        "x5",
        "분석 쿼리 모음 — 28개",
        "부록 E",
        "이 문서 본문에 나온 쿼리와 나오지 않은 쿼리를 한곳에 정리했습니다 · 실행은 Log Analytics 워크스페이스의 Logs 화면 또는 `kq`",
        md("본문(C 단계)에서는 핵심 쿼리를 한 줄씩 해설했습니다. 이 페이지에는 아래 28개가 모두 실려 있고(저장소의 `snippets/queries.kql` 에도 같은 내용이 있습니다), 쿼리마다 **무엇을 보여 주는지 · 언제 쓰는지**를 정리했습니다. 처음 쓰는 환경에서는 테이블 · 열 이름이 다를 수 있으니 쿼리 끝에 `| take 5` 를 붙여 열을 먼저 확인하세요.")
        + table(["쿼리 이름", "무엇을 보여 주나", "이럴 때 쓰세요"], [[Raw("<code>" + n + "</code>"), what, when] for n, what, when in q_rows], cls="nw")
        + md("`//## 이름 | …` 줄로 구분된 파일이라, 해당 이름의 블록(주석 제외)을 복사해 `kq '…'` 로 감싸 실행하면 됩니다(작은따옴표가 들어 있는 쿼리는 포털에서 실행하세요). **각 쿼리의 코드는 아래에서 펼쳐 볼 수 있습니다**(VM 이름은 이 실습 값 `vm-lablog-rhel` 입니다).")
        + "".join(details(n, code(kql(n), cap=n, lang="kql")) for n, _, _ in q_rows),
        done=False,
    )
    sec_x = section("x", "부록", "검증 기록 · 내 환경에 적용하기 · 문제 해결 · 운영 적용 시 차이 · 분석 쿼리", appx_a + appx_b + appx_c + appx_d + appx_e)

    return sec_c + sec_d + sec_x
