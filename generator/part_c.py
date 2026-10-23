# -*- coding: utf-8 -*-
# C · 확인과 분석 / D · 정리 / 부록
from lib import *


def build():
    # ───────── C1
    c1 = step(
        "c1",
        "데이터가 들어왔는지 — 테이블별 건수와 수집 지연",
        "C1",
        "B1 설정 후 약 30분 + 앱 호출 몇 분 뒤 (AOAI 로그는 활성화까지 가장 오래 걸립니다)",
        "<p>먼저 모든 로그가 한 워크스페이스에 들어왔는지, 그리고 <b>발생 시각에서 수집까지 몇 초 걸리는지</b>를 봅니다. "
        "이 지연이 있기 때문에 ‘방금 난 지연’은 로그가 아니라 메트릭 알림으로 잡아야 합니다.</p>"
        + code(
            kq(
                """union isfuzzy=true withsource=T Heartbeat, Perf, Syslog, AppDependencies, AppTraces, AzureMetrics, AzureDiagnostics
| where TimeGenerated > ago(1h)
| extend lag_s = datetime_diff("second", ingestion_time(), TimeGenerated)
| summarize rows = count(), avg_lag_s = round(avg(lag_s), 0), max_lag_s = max(lag_s) by T
| order by T asc""",
                is_name=False,
            ),
            run="C1",
        )
        + out("""T                 Avg_lag_s    Max_lag_s    Rows
----------------  -----------  -----------  ------
AppDependencies   11           174          146
AppTraces         7            163          143
AzureDiagnostics  85           279          41       ← AOAI 로그 (RequestResponse · Audit)
AzureMetrics      450          590          694      ← AOAI 메트릭 (AllMetrics)
Heartbeat         17           168          28
Perf              113          239          960
Syslog            94           237          53""")
        + call(
            "info",
            "읽는 법",
            "<p>앱 로그(App Insights)는 약 10초, VM 로그(Perf·Syslog)는 약 2분, AOAI 요청 로그는 <b>활성화된 뒤</b> 평균 1~2분, AOAI 메트릭은 7~10분 뒤에 보입니다(최대값은 처음 몇 분의 일괄 수집분이 올립니다). "
            "AzureDiagnostics 행이 아직 없다면 B1 설정 후 30분이 지났는지 확인하세요. Heartbeat 가 계속 들어오면 에이전트가 정상입니다.</p>",
        ),
    )

    # ───────── C2
    c2 = step(
        "c2",
        "요청 한 건씩 대조 — 앱이 잰 시간 vs AOAI 가 잰 시간",
        "C2",
        "가이드의 핵심 분석 · 앱 로그(R3)와 AOAI 로그(R1)를 요청 ID 로 조인",
        "<p>앱 로그의 <code>apim_request_id</code>(응답 헤더 <code>apim-request-id</code>)가 AOAI 로그의 <code>CorrelationId</code> 와 <b>같습니다</b>(실측 확인). "
        "그래서 요청 단위로 <b>앱 시간 − AOAI 시간 = 앱↔AOAI 사이(네트워크·클라이언트)에서 쓴 시간</b>을 구할 수 있습니다.</p>"
        + code(kq("app_vs_aoai_by_request"), run="C2")
        + out("""t                     outcome  status  app_ms  aoai_ms  gap_ms
--------------------  -------  ------  ------  -------  ------
2026-10-23T13:19:18Z  ok       200     7449    7217     232
2026-10-23T13:22:12Z  ok       200     905     790      115
2026-10-23T13:25:18Z  ok       200     6449    6349     100
2026-10-23T13:21:48Z  ok       200     6719    6623     96
…
(같은 리전에서 gap 은 대부분 70~130ms. 토큰 수는 앱 값과 AOAI 값이 정확히 일치했습니다)""")
        + call(
            "warn",
            "timeout 호출은 요청 ID 로 조인되지 않습니다",
            "<p>앱이 응답을 받기 전에 끊으면(client_timeout) 응답 헤더가 없어 <code>apim_request_id</code> 가 비어 있습니다. 이 경우에는 <b>시각 + 처리 시간</b>으로 맞춥니다 — "
            "앱 <code>total_ms≈1027</code>(timeout 1.0초) ↔ AOAI <code>ResultSignature=499 · DurationMs≈1062</code>. "
            "AOAI 쪽 499 행은 <code>responseLength=0</code> · <code>completionTokens=0</code> 입니다.</p>",
        )
        + code(
            kq(
                """AzureDiagnostics
| where TimeGenerated > ago(1h) and Category == "RequestResponse" and ResultSignature == "499"
| extend p = parse_json(properties_s)
| project TimeGenerated, ResultSignature, DurationMs, CallerIPAddress,
          responseLength = toint(p.responseLength), completionTokens = toint(p.completionTokens), deployment = tostring(p.modelDeploymentName)
| order by TimeGenerated desc
| take 5""",
                is_name=False,
            ),
            cap="499 행 확인",
            run="C2",
        )
        + out("""TimeGenerated         ResultSignature  DurationMs  CallerIPAddress  responseLength  completionTokens  deployment
--------------------  ---------------  ----------  ---------------  --------------  ----------------  ----------
2026-10-23T11:28:42Z  499              1062        20.200.208.**    0               0                 gpt41mini""")
        + call("info", "호출자 IP", "<p><code>CallerIPAddress</code> 는 마지막 자리가 가려져(<code>20.200.208.**</code>) 표시됩니다. VM 의 <b>송신 공용 IP</b>(방화벽·NAT 를 거치면 그 장치의 IP)를 확인하는 데 씁니다.</p>"),
    )

    # ───────── C3
    c3 = step(
        "c3",
        "1분·5분 단위로 보기 — 정각·30분 패턴 찾기",
        "C3",
        "운영에서는 ‘일주일 이상’ 겹쳐 봅니다",
        "<p>실제 장애 분석에서는 개별 요청보다 <b>시간 패턴</b>이 중요합니다. 앱(App Insights)과 AOAI 를 1분 단위로 나란히 놓고, 8초 이상 느린 분만 뽑습니다.</p>"
        + code(kq("app_dep_vs_aoai_by_minute"), cap="앱 ↔ AOAI — 1분 단위, 8초 이상 느린 분만", run="C3")
        + out("""t                     app_calls  app_failed  app_p95_ms  aoai_calls  aoai_p95_ms  c499
--------------------  ---------  ----------  ----------  ----------  -----------  ----
2026-10-23T13:10:00Z  5          0           8031        (없음)      (없음)       (없음)   ← 아직 AOAI 로그가 활성화되기 전
2026-10-23T13:16:00Z  4          2           8014        (없음)      (없음)       (없음)
2026-10-23T13:26:00Z  4          0           8355        5           8271         0""", label="예상 결과 (AOAI 로그가 활성화되기 전 시간대는 앱 쪽 값만 보입니다)")
        + code(kq("aoai_tokens_by_5min"), cap="AOAI 로그만으로 — 출력 토큰당 처리 시간 (토큰당 시간이 일정한데 총 시간만 늘면 출력 길이 때문)", run="C3")
        + out("""TimeGenerated         calls  p95_ms  out_tokens  ms_per_out_token
--------------------  -----  ------  ----------  ----------------
2026-10-23T13:15:00Z  5      7217    1431        11
2026-10-23T13:20:00Z  23     6623    2723        16
2026-10-23T13:25:00Z  14     8271    2112        15"""),
    )

    # ───────── C4
    c4 = step(
        "c4",
        "VM 쪽 — probe · cron · 성능 카운터",
        "C4",
        "정각·30분에 VM 에서 무슨 일이 도는지",
        "<p>probe 의 5분 요약, 정각·30분에 실행된 cron 작업, 에이전트가 수집 중인 성능 카운터를 봅니다.</p>"
        + code(kq("probe_by_5min"), cap="probe — 5분 단위 (VM 안, AOAI · 로컬 앱 URL)", run="C4")
        + out("""TimeGenerated         role       target            runs  p95_ms  max_tcp_ms  max_wait_ms  fails
--------------------  ---------  ----------------  ----  ------  ----------  -----------  -----
2026-10-23T11:15:00Z  vm-inside  aoai              6     1120    6           643          0
2026-10-23T11:15:00Z  vm-inside  app:11202/health  6     3       0           3            0""")
        + code(kq("cron_at_hh00_hh30"), cap="cron — 매시 정각·30분(분 0·1·30·31)에 실행된 작업", run="C4")
        + out("""ProcessName  cmd                                        runs
-----------  -----------------------------------------  ----
CROND        (root) CMD (run-parts /etc/cron.hourly)    1""")
        + call("info", "cron 결과가 비어 있다면", "<p>RHEL 의 <code>cron.hourly</code> 는 매시 <b>01분</b>에 돕니다. 첫 정각이 지난 뒤(약 1시간 후) 다시 실행하세요.</p>")
        + code(kq("ama_perf_counters"), cap="성능 카운터 — 12종이 모두 들어오는지", run="C4")
        + out("""CounterName              ObjectName    samples
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
Load1                    System        5"""),
    )

    # ───────── C5
    rows = [
        ("1", "진단 설정 저장", "<code>az monitor diagnostic-settings list</code>", "RequestResponse · Audit · AllMetrics 설정이 보임", "ok", "B1"),
        ("2", "AOAI 로그 도착", "C1 · aoai_requestresponse_check", "약 20분 내 행이 보이고 properties_s 에 본문이 없음", "ok", "properties_s: 토큰 수·길이·배포 이름만"),
        ("3", "요청 ID 대조", "C2", "apim_request_id = CorrelationId", "ok", "x-request-id 는 불일치"),
        ("4", "호출 로그 1줄", "B3 의 journalctl", "ok / client_timeout / error + 토큰 수", "ok", "ok · timeout · 404 모두 확인"),
        ("5", "App Insights 수집", "<code>AppDependencies</code> 의 Target 필터", "시도마다 행 + aoai_call 로그 (수 초~수십 초 내)", "ok", "200 · 0(timeout) · 404"),
        ("6", "AMA 연결", "ama_heartbeat · ama_perf_counters", "설치 후 10분 내 Heartbeat · Perf · cron 행", "ok", "카운터 12종 · cron · local5"),
        ("7", "시계 동기화", "<code>timedatectl</code>", "System clock synchronized: yes", "ok", "RHEL 9.8 기본값"),
        ("8", "probe 동작", "systemctl list-timers · probe_by_5min", "1분마다 JSON 줄, rc=0", "ok", "관리 ID 인증 · wait_ms 정상"),
        ("9", "알림 시험", "B6 의 알림 조회", "알림 발화", "ok", "aoai-499 · app-client-timeout"),
    ]
    tr = "".join(
        f"<tr><td>{a}</td><td><b>{b}</b></td><td>{c}</td><td>{d}</td><td class=\"{e}\">✔</td><td>{f}</td></tr>" for a, b, c, d, e, f in rows
    )
    c5 = step(
        "c5",
        "적용 직후 확인 체크리스트 9가지 — 이번 실습 결과",
        "C5",
        "22장 18쪽의 체크리스트를 실제로 돌려 본 결과",
        "<table><thead><tr><th>#</th><th>항목</th><th>확인 방법</th><th>기대</th><th class='res'>결과</th><th>실측 메모</th></tr></thead><tbody>" + tr + "</tbody></table>"
        + call(
            "info",
            "읽는 법 — 신호의 조합으로 원인 구간을 가립니다",
            "<table><thead><tr><th>관측되는 패턴</th><th>해석</th><th>다음 행동</th></tr></thead><tbody>"
            "<tr><td>앱만 길고 AOAI 처리 시간은 정상(gap 이 큼)</td><td>AOAI 밖 — 앱 대기 · 네트워크 · 큐</td><td>inflight · 작업 큐 계측, probe(VM 안) 확인</td></tr>"
            "<tr><td>앱 지연이 정각·30분 cron·CPU 상승과 겹침</td><td>VM 자원 · 스케줄 작업 경합</td><td>Syslog(cron) · 스냅샷으로 작업 식별 → 분산</td></tr>"
            "<tr><td>앱·probe(VM 안)만 느리고 probe(VM 밖)는 정상</td><td>VM → AOAI 경로(방화벽 · DNS · SNAT)</td><td>dns_ms · tcp_ms → R6 SNAT 사용률 · Connection Monitor</td></tr>"
            "<tr><td>앱 · AOAI · probe 모두 느림</td><td>AOAI 서비스 · 공유 용량</td><td>apim_request_id · 시각 · 메트릭을 첨부해 Support Case</td></tr>"
            "<tr><td>AOAI 에 499, 처리 시간이 앱 timeout 과 비슷</td><td>앱 timeout 이 먼저 끊음(긴 출력 · 큰 입력)</td><td>timeout · max_tokens · Streaming 조정, 재시도 중복 확인</td></tr>"
            "</tbody></table>",
        ),
    )

    sec_c = section("c", "C · 확인과 분석", "로그가 실제로 쌓였는지 확인하고, 지연의 원인 구간을 가립니다", c1 + c2 + c3 + c4 + c5)

    # ───────── D
    d1 = step(
        "d1",
        "정리 — 비용 중지 또는 전체 삭제",
        "D",
        "실습이 끝나면 꼭 실행하세요",
        code(
            """# (A) 잠시 멈추기 — VM 컴퓨팅 과금 중지 (디스크·공용 IP 요금은 남음). 다시 켤 때: az vm start -g $RG -n $VM
az vm deallocate -g $RG -n $VM

# (B) 전부 삭제
#   ① Connection Monitor · flow log 는 리소스 그룹 밖(NetworkWatcherRG)에 만들어져 그룹 삭제로 지워지지 않으니 먼저 지웁니다
az network watcher connection-monitor delete -l $LOC -n cm-vm-to-aoai
az network watcher flow-log delete -l $LOC -n vnetfl-agent
#   ② 리소스 그룹째 삭제 (알림 · 수집 규칙 · AOAI · VM · 저장소 모두 포함)
az group delete -n $RG --yes --no-wait
rm -f id_lab id_lab.pub lablog.env                       # 임시 SSH 키와 변수 파일""",
            cap="정리 (A 또는 B 중 하나)",
            run="D",
            skip=True,
        )
        + call(
            "info",
            "소프트 삭제",
            "<p>AOAI 계정과 Log Analytics 워크스페이스는 삭제 후에도 일정 기간 ‘소프트 삭제’ 상태로 이름이 남습니다. 이 실습은 이름에 <b>무작위 접미사</b>(<code>$SFX</code>)를 붙여서 다시 실행해도 충돌하지 않습니다. "
            "같은 이름을 꼭 다시 쓰려면 <code>az cognitiveservices account purge</code> 로 AOAI 를 영구 삭제하세요.</p>",
        ),
    )
    sec_d = section("d", "D · 정리", "", d1)

    # ───────── 부록
    facts = [
        ("R1 진단 설정", "ok", "설정 후 약 20~26분 뒤부터 요청이 기록됨(그 전 호출은 기록되지 않음, 2회 반복 확인) · 이후 지연 평균 약 2분. <code>properties_s</code>(JSON)에 promptTokens · completionTokens · streamType · 배포/모델 이름 · 요청/응답 길이, <b>본문 없음</b>, 호출자 IP 끝자리 마스킹"),
        ("요청 ID 대조", "ok", "<code>apim-request-id</code> = <code>CorrelationId</code>. <code>x-request-id</code> 는 불일치, <code>x-ms-client-request-id</code> 는 AOAI 로그에 남지 않음"),
        ("499 의 의미", "ok", "클라이언트 read timeout 1.0초 → AOAI <code>499</code>(DurationMs≈1.06초, 응답 길이 0). 앱은 <code>client_timeout</code>(1.03초)"),
        ("404 (없는 배포)", "ok", "앱 dependency 404 로는 보이지만 AOAI 지표·로그에는 없음"),
        ("R2 메트릭", "ok", "StatusCode 200 · 499 (숫자 문자열). <code>AzureOpenAITTLTInMS</code> · 토큰 지표에 값 있음, 신형 <code>TimeToLastByte</code> · <code>TimeToResponse</code> 계열은 이 환경에서 값 없음. AzureMetrics 지연 7~10분"),
        ("R3 호출 로그", "ok", "ok · client_timeout · error 기록, 응답 헤더 3종(<code>x-request-id</code> · <code>apim-request-id</code> · <code>x-ms-region</code>) 확인"),
        ("R4 App Insights", "ok", "dependency 200 · ResultCode 0(timeout, Success=false) · 404, <code>httpx2.ReadTimeout</code> 예외, 지연 약 10초. 부가 dependency(<code>settings.sdk.monitor.azure.com</code> · <code>169.254.169.254</code>)가 섞이므로 Target 필터 필요. <b>Python 3.10+ 필요</b>(RHEL 9 기본 3.9)"),
        ("앱 vs AOAI 시간", "ok", "같은 리전에서 앱 시간 − AOAI 시간 = 72~134ms(평균 94ms), 토큰 수 일치"),
        ("R5 에이전트", "ok", "AMA 1.45 · 성능 카운터 12종 · cron / local5 syslog · Heartbeat. 지연: Perf·Syslog 약 2분, Heartbeat 약 5초"),
        ("R6 네트워크", "part", "Connection Monitor(RHEL 9.8)와 VNet flow log 는 정상. Azure Firewall 은 진단 설정(AZFW* 전용 테이블 · SNAT 지표)만 확인 — <b>방화벽을 거치는 트래픽은 미검증</b>"),
        ("R7 probe", "ok", "관리 ID 인증 · 1분 타이머 · syslog 수집 정상. 실습 중 2건 수정(<code>--http1.1</code>, <code>systemd-run</code>)"),
        ("R8 알림", "ok", "<code>aoai-499</code>(메트릭) · <code>app-client-timeout</code>(로그) 발화 확인. 수신 메일 도착은 수신자가 확인"),
        ("분석 쿼리", "ok", "queries.kql 28개를 실제 워크스페이스에서 모두 오류 없이 실행 (데이터가 없는 방화벽·가용성 테스트 쿼리는 0행)"),
        ("수집량", "ok", "VM 1대 + 분당 약 5회 호출 기준 시간당 약 1MB (Log Analytics 월 5GB 무료 범위 안)"),
    ]
    ftr = "".join(f'<tr><td><b>{a}</b></td><td class="{b}">{"✔" if b == "ok" else "△"}</td><td>{c}</td></tr>' for a, b, c in facts)
    appx_a = step(
        "x1",
        "실제 환경에서 확인한 사실",
        "부록 A",
        "2026-10-23 · Korea Central · RHEL 9.8 · Azure CLI 2.86 · openai 3.37 · azure-monitor-opentelemetry 1.8.11 · 2회 검증(단계별 적용 → 이 문서의 코드 블록을 새 리소스 그룹에서 그대로 재실행)",
        "<table><thead><tr><th>항목</th><th class='res'>결과</th><th>실측 내용</th></tr></thead><tbody>" + ftr + "</tbody></table>",
    )
    fixes = (
        "<ul>"
        "<li><b>토큰 수는 AOAI 진단 로그에 있습니다</b> — 이전 안내(‘요청별 토큰 수는 로그에 없음’)를 바로잡고, <code>properties_s</code> 에서 꺼내는 쿼리를 추가했습니다.</li>"
        "<li><b>요청 ID 대조 키</b>는 <code>apim_request_id</code> = <code>CorrelationId</code> 입니다(<code>aoai_requestid_match</code> 쿼리 수정, 요청 단위 조인 쿼리 <code>app_vs_aoai_by_request</code> 추가).</li>"
        "<li><b>probe</b>: <code>curl --http1.1</code> 추가(wait_ms 정상화), 스냅샷을 <code>systemd-run</code> 으로 실행(중도 종료 방지).</li>"
        "<li><b>R4</b>: RHEL 9 의 기본 Python 3.9 → 3.10 이상(python3.12) 필요 명시, <code>systemctl edit</code> 대신 쓸 수 있는 비대화식 드롭인 방법 추가.</li>"
        "<li>본문 미기록 · 호출자 IP 마스킹 · 수집 지연(앱 10초 · VM 2분 · AOAI 최대 20분)을 실측값으로 교체. 신규 쿼리 <code>aoai_tokens_by_5min</code> · <code>billed_by_table</code>.</li>"
        "</ul>"
    )
    appx_b = step("x2", "실습에서 22장 가이드에 반영한 수정", "부록 B", None, fixes)
    trouble = (
        "<table><thead><tr><th>증상</th><th>확인 · 해결</th></tr></thead><tbody>"
        "<tr><td><code>vmrun</code> 이 ‘Conflict / another operation in progress’</td><td>이전 run-command 가 끝나기를 기다린 뒤 다시 실행합니다.</td></tr>"
        "<tr><td>AOAI 로그(AzureDiagnostics)가 안 보임</td><td>설정 후 20분 이상 기다립니다. <code>journalctl -u report-agent</code> 로 앱이 호출 중인지, B1 의 진단 설정이 켜져 있는지 확인합니다.</td></tr>"
        "<tr><td>AppDependencies 에 AOAI 호출이 없음</td><td><code>OTEL_TRACES_SAMPLER=always_on</code> · 연결 문자열 · Python 3.10+ · 아웃바운드 443(<code>*.in.applicationinsights.azure.com</code>)을 확인합니다. <code>Target has \"openai.azure.com\"</code> 로 필터하세요.</td></tr>"
        "<tr><td>Perf · Syslog 가 없음</td><td><code>az vm extension list -g $RG --vm-name $VM -o table</code> 로 AzureMonitorLinuxAgent 상태, DCR 연결(B2), <code>systemctl is-active rsyslog</code> 를 확인합니다.</td></tr>"
        "<tr><td>모델 배포가 실패 / 쿼터 부족</td><td>다른 리전(예: swedencentral)이나 모델로 바꾸고 <code>LOC</code> · 모델 이름을 수정합니다. 추론 모델은 <code>max_completion_tokens</code> 로 코드를 바꿔야 합니다.</td></tr>"
        "<tr><td>알림 메일이 안 옴</td><td>스팸함 확인, 액션 그룹 수신자(<code>az monitor action-group show -g $RG -n ag-aoai-latency</code>)를 확인합니다.</td></tr>"
        "</tbody></table>"
    )
    appx_c = step("x3", "문제 해결", "부록 C", None, trouble)
    prod = (
        "<ul>"
        "<li><b>키 대신 관리 ID</b>: 이 실습의 데모 앱은 22장 예시대로 키를 쓰지만, 운영 앱은 관리 ID(<code>azure_ad_token_provider</code>)를 권장합니다. probe 는 이미 관리 ID 입니다.</li>"
        "<li><b>기존 진단 설정</b>: 진단 설정은 리소스당 최대 5개이고 Azure Policy 가 이미 만들었을 수 있습니다 — B1 전에 확인하세요.</li>"
        "<li><b>방화벽 허용 목록</b>: VM 아웃바운드 443 에 Application Insights · Azure Monitor Agent · 워크스페이스 FQDN 을 허용해야 합니다(22장 5쪽).</li>"
        "<li><b>워크스페이스 통일 · 시간 동기화(NTP)</b>: 앱·AOAI·VM 로그를 같은 워크스페이스에, 시각은 UTC 기준으로 비교합니다. 일일 상한(daily cap)은 걸지 않습니다.</li>"
        "<li><b>앱 언어</b>: Python 이 아니면 22장 부록 A 를 따르되 R3 의 필드 이름은 그대로 유지합니다.</li>"
        "</ul>"
    )
    appx_d = step("x4", "운영 환경에 적용할 때 달라지는 점", "부록 D", None, prod)
    sec_x = section("x", "부록", "검증 기록 · 수정 내역 · 문제 해결", appx_a + appx_b + appx_c + appx_d)

    return sec_c + sec_d + sec_x
