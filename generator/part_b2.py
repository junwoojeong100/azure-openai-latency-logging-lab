# -*- coding: utf-8 -*-
# B5 · R2 / B6 · R8 / B7 · R6
from lib import *


def build():
    # ───────── B5 · R2
    b5 = step(
        "b5",
        "AOAI 메트릭 — StatusCode 값 확인",
        "B5 · R2",
        "B3 시작 후 5분 이상 지난 뒤 실행 · 메트릭은 약 7~10분 지연 · 필요한 권한: 읽기(Monitoring Reader 이상)",
        brief(
            what="AOAI 메트릭 `AzureOpenAIRequests`(분당 요청 수)를 **`StatusCode` 별로 나눠** 어떤 상태 코드가 실제로 찍히는지 봅니다.",
            why="R8 의 ‘499 알림’을 만들 때 쓰는 **값의 형태**(숫자가 아니라 문자열 `\"499\"`)와 실제로 어떤 코드가 집계되는지를 알림을 만들기 전에 확인하려는 용도입니다.",
            result="최근 24시간이 **시간 단위**로 나오고, 앱이 호출한 시간대에만 값이 보입니다.",
            apply="내 AOAI 리소스에서 그대로 실행합니다. **조회만 하는 읽기 전용 명령**이라 설정이 바뀌지 않습니다(메트릭은 설정 없이 이미 쌓이고 있습니다).",
        )
        + walk(
            snip("R2_aoai_metrics.sh", "statuscode"),
            [
                (
                    "",
                    "StatusCode 별 요청 수 조회",
                    """
                    첫 줄은 설명 주석입니다. 명령의 뜻:
                    * `az monitor metrics list --resource $AOAI_ID` — AOAI 리소스의 **메트릭**을 조회
                    * `--metrics AzureOpenAIRequests` — 메트릭 이름: **Azure OpenAI 요청 수**
                    * `--dimension StatusCode` — 값을 **HTTP 상태 코드별로 나눠서**(200 · 429 · 499 …) 보여 줌
                    * `--aggregation Total` — 구간 안의 **합계**
                    * `--interval 1h --offset 1d` — **1시간 단위**로, **최근 1일(24시간)** 만큼
                    * `-o table` — 표로 출력
                    """,
                )
            ],
            cap="StatusCode 별 요청 수 조회 (R2 · 읽기 전용)",
            tags={1: "apply"},
            run="B5",
        )
        + out(
            """Timestamp             Name                   Statuscode    Total
--------------------  ---------------------  ------------  -------
2026-10-23T09:25:00Z  Azure OpenAI Requests  200           0.0
…                                                                     (앱을 켜기 전 시간대는 0)
2026-10-23T10:25:00Z  Azure OpenAI Requests  200           72.0
2026-10-23T10:25:00Z  Azure OpenAI Requests  499           13.0""",
            label="예상 결과 (최근 24시간이 시간 단위로 나오며, 앱이 호출한 시간대에만 값이 보입니다)",
            read="""
            - `Timestamp` 는 **UTC** 시각의 1시간 구간입니다(한국 시각 = UTC + 9시간).
            - 같은 시간대에 `200` 이 72건, **`499` 가 13건** — 앱이 일부러 1초 timeout 으로 끊은 호출이 AOAI 쪽에서 `499` 로 집계된 것입니다. 앱을 켜기 전 시간대는 `0` 입니다.
            - `Statuscode` 는 숫자가 아니라 **문자열**(`"200"`, `"499"`)입니다. 알림 조건에도 문자열로 비교합니다.
            """,
        )
        + call(
            "info",
            "실측으로 확인한 것",
            """
            - StatusCode 값은 `200` · `499` 처럼 **숫자 문자열**입니다. 앱이 일부러 1초 timeout 으로 끊은 호출이 **499** 로 집계되었습니다.
            - 없는 배포 이름(404)은 AOAI 지표 · 로그에 **나타나지 않습니다** — 앱 로그에서만 보입니다.
            - 이 환경(비스트리밍 · Global Standard)에서 `AzureOpenAITTLTInMS`(응답 완료 시간) · 토큰 수 지표에는 값이 있었고, `TimeToLastByte` · `TimeToResponse` · `NormalizedTimeBetweenTokens` 계열은 값이 없었습니다.
            """,
        ),
        scope="check",
    )

    # ───────── B6 · R8
    b6 = step(
        "b6",
        "알림 4종 + 수신 그룹",
        "B6 · R8",
        "소요 약 2분 · 필요한 권한: 알림 규칙 · 수신 그룹을 만들 수 있는 권한(대상 리소스 그룹의 Monitoring Contributor) · 알림 메일은 A1 의 `MAIL` 로 갑니다",
        brief(
            what="지연이 난 순간을 놓치지 않도록 **메트릭 알림 2개**(AOAI 499 · 응답 완료 시간, 1분마다 평가)와 **로그 알림 2개**(앱 `client_timeout` · probe 지연, 5분마다 평가)를 만들고, 알림을 받을 **수신 그룹(이메일)** 을 만듭니다.",
            why="로그는 수집 지연(앱 약 10초 · VM 약 2분 · AOAI 로그 수 분)만큼 늦게 도착하므로 ‘방금 난 지연’을 로그로는 바로 알기 어렵습니다. **AOAI 쪽은 메트릭 알림이 더 빠릅니다.**",
            result="알림 규칙 4개와 수신 그룹 1개. 조건이 충족되면 `MAIL` 로 메일이 옵니다.",
            apply="알림을 만들 **리소스 그룹 · 수신 이메일 · AOAI 리소스 ID · 워크스페이스 ID** 만 내 환경 값으로 바꾸세요. 임계값(499 가 1건 이상 · 응답 완료 20초 · 8초 이상 느린 probe)은 **운영 기준에 맞게 조정**합니다.",
            caution="실습 중에는 timeout 호출이 계속 발생하므로 알림 메일이 **실제로 옵니다.** 끝나면 D 단계에서 리소스 그룹을 삭제하거나 **4개 규칙을 모두** 끄세요(아래 ‘알림 메일이 옵니다’ 참고). **수신자 확인 메일**도 있습니다(아래 ‘수신자 확인’ 상자).",
        )
        + walk(
            snip("R8_alerts.sh", "alerts"),
            [
                (
                    "# 수신 그룹",
                    "수신 그룹(액션 그룹) 만들기",
                    """
                    **액션 그룹**은 ‘알림이 울리면 누구에게 · 어떻게 알릴지’를 모아 둔 것입니다.
                    * `-n ag-aoai-latency --short-name aoailat` — 이름과 짧은 이름(알림 메시지에 표시되는 12자 이내 이름)
                    * `--action email owner $MAIL` — **이메일 수신자** 하나 추가(`owner` 는 수신자의 별칭). 수신자에게 **확인 메일**이 가며, 확인을 마쳐야 알림 메일을 받을 수 있습니다(아래 상자).
                    * `AG=$(… --query id -o tsv)` — 만들어진 그룹의 **리소스 ID** 를 변수에 담음(아래 알림 4개가 이 그룹을 가리킵니다)
                    """,
                ),
                (
                    "Q1=",
                    "로그 알림용 KQL 두 개",
                    """
                로그 알림은 **KQL 질의 결과의 행 수**가 조건에 맞으면 울립니다. KQL 은 `테이블 | 단계 | 단계 …` 처럼 **파이프(`|`)로 데이터를 걸러 가는** 질의 언어입니다.
                * `Q1` — `AppTraces`(앱 로그 테이블)에서 `where Message has 'aoai_call' and Message has 'client_timeout'` = 메시지에 **`aoai_call` 과 `client_timeout` 이 모두 들어 있는 행**만 남깁니다(`has` = 단어를 포함). 즉 **앱이 timeout 으로 포기한 호출**입니다.
                * `Q2` — `Syslog` 에서 `ProcessName == 'aoai-probe'`(probe 가 남긴 줄만) → `extend p = parse_json(SyslogMessage)`(JSON 문자열을 풀어 새 열 `p` 로) → `where toint(p.rc) != 0 or toint(p.total_ms) >= 8000` = **통신이 실패(`rc≠0`)했거나 전체 시간이 8000ms 이상**인 것 = **probe 가 본 느림 · 통신 실패**(`8000` 은 B4 의 `SLOW_MS=8000` 과 같은 기준입니다 — 한쪽을 바꾸면 다른 쪽도 맞추세요). HTTP 오류 코드(429 · 5xx)는 `rc` 가 0 이므로 **8초 이상 걸리지 않으면 이 알림에 잡히지 않습니다.**
                """,
                ),
                (
                    "az monitor metrics alert create -g $RG -n aoai-499",
                    "메트릭 알림 ① aoai-499 — 499 가 1건이라도 있으면",
                    """
                **메트릭 알림**은 Azure Monitor 가 **메트릭 값 자체**를 평가하므로, 로그가 워크스페이스에 도착하길 기다리지 않습니다(그래서 일반적으로 로그 알림보다 빠른 편입니다 — 이 실습에서 속도 차이를 따로 재지는 않았습니다).
                * `--scopes $AOAI_ID` — **AOAI 리소스**의 메트릭을 감시
                * `--condition "total AzureOpenAIRequests > 0 where StatusCode includes 499"` — 요청 수 합계가 0 보다 큰데 **상태 코드가 499 인 것만**
                * `--window-size 5m --evaluation-frequency 1m` — **1분마다**, **최근 5분**을 평가
                * `--severity 2` — 심각도: 0 심각 · 1 오류 · **2 경고** · 3 정보 · 4 상세 (여기서는 2 = 경고)
                * `--action $AG` — 울리면 위 수신 그룹으로 알림
                """,
                ),
                (
                    "az monitor metrics alert create -g $RG -n aoai-ttlt-high",
                    "메트릭 알림 ② aoai-ttlt-high — 응답 완료가 20초를 넘으면",
                    "`AzureOpenAITTLTInMS` 는 **응답이 끝나기까지 걸린 시간(ms)** 입니다. `max … > 20000` 은 최근 5분 안에 **20초를 넘긴 응답이 있으면** 울립니다(심각도 3 = 정보). 1분마다 평가합니다.",
                ),
                (
                    "az monitor scheduled-query create -g $RG -n app-client-timeout",
                    "로그 알림 ① app-client-timeout — 앱 timeout 발생",
                    """
                * `az monitor scheduled-query create` — **예약된 KQL 질의 알림**
                * `--scopes $LAW` — 이 워크스페이스에서 질의
                * `--condition "count 'Q' > 0" --condition-query Q="$Q1"` — `Q` 라는 이름을 붙인 질의(`Q1`)의 **결과 행 수(`count`)가 0 보다 크면**(= 1개 이상이면) 울림
                * `--window-size 5m --evaluation-frequency 5m` — 5분마다 최근 5분을 평가

                로그 알림은 로그가 워크스페이스에 **도착한 뒤에** 평가되므로 수집 지연(앱 약 10초 · VM 약 2분)만큼 늦게 울립니다.
                """,
                ),
                (
                    "az monitor scheduled-query create -g $RG -n probe-slow",
                    "로그 알림 ② probe-slow — probe 가 느림 · 실패를 감지",
                    "위와 같은 방식으로 질의 `Q2`(probe 실패 · 8초 이상)를 감시합니다. 심각도 3.",
                ),
            ],
            cap="수신 그룹 + 알림 4개 만들기 (R8)",
            tags={1: "apply", 2: "apply", 3: "apply", 4: "apply", 5: "apply", 6: "apply"},
            run="B6",
        )
        + walk(
            """az rest --method get --url "https://management.azure.com/subscriptions/$SUB/providers/Microsoft.AlertsManagement/alerts?api-version=2019-05-05-preview&targetResourceGroup=$RG" \\
  --query "value[].{rule:properties.essentials.alertRule, state:properties.essentials.monitorCondition, sev:properties.essentials.severity, fired:properties.essentials.startDateTime}" -o table""",
            [
                (
                    "az rest",
                    "울린 알림 목록 조회",
                    """
                Azure 의 REST API(알림 관리)를 직접 호출해 **이 리소스 그룹에서 울린 알림**을 조회합니다(`az rest` = 인증을 대신 붙여 주는 REST 호출 도구).
                * `--query "value[].{…}"` — 규칙 이름(`rule`) · 상태(`state`: Fired 울림 / Resolved 해소) · 심각도(`sev`) · 시작 시각(`fired`) 만 골라 표로 출력

                앞의 명령 직후나 앱을 켠 직후에는 **목록이 비어 있는 것이 정상**입니다. 알림은 조건이 충족된 뒤에야 생기고(보통 5~10분), 그 전에는 빈 줄만 나옵니다.
                """,
                )
            ],
            cap="울린 알림 확인 (앱을 켜고 약 10분 뒤)",
            tags={1: "apply"},
            run="B6",
        )
        + out(
            """Rule                 State   Sev   Fired
-------------------  ------  ----  ----------------------------
…/aoai-499           Fired   Sev2  2026-10-23T11:25:05Z
…/app-client-timeout Fired   Sev2  2026-10-23T11:28:47Z""",
            read="`State` 가 `Fired` 인 규칙이 **지금 조건을 충족해 울린 알림**입니다. 이 실습은 일부러 timeout 호출을 만들기 때문에 `aoai-499` 와 `app-client-timeout` 이 울리는 것이 정상입니다. `Fired` 시각은 UTC 입니다.",
        )
        + call(
            "warn",
            "알림 메일이 옵니다 — 끝나면 4개 규칙을 모두 끄거나 삭제하세요",
            """
            실습 중 timeout 호출이 계속 발생하므로 `aoai-499` 와 `app-client-timeout` 이 울리고 `MAIL` 로 알림이 갑니다. 확인이 끝나면 D 단계에서 리소스 그룹을 삭제하거나, 지우지 않을 거라면 **4개 규칙을 각각** 끄세요(규칙 종류에 따라 명령이 다릅니다):
            - 메트릭 알림 2개: `az monitor metrics alert update -g $RG -n aoai-499 --enabled false` · `-n aoai-ttlt-high` 도 같은 방식
            - 로그 알림 2개: `az monitor scheduled-query update -g $RG -n app-client-timeout --disabled true` · `-n probe-slow` 도 같은 방식
            """,
        )
        + call(
            "info",
            "알림 메일을 받으려면 ‘수신자 확인’이 필요합니다",
            """
            액션 그룹에 **처음 쓰는 이메일 주소**를 추가하면 Azure 가 그 주소로 **확인 메일**(OTP — 일회용 코드)을 보냅니다(스팸함도 보세요). 문서 기준(Microsoft Learn 의 Azure Monitor 액션 그룹 문서)으로 **약 30분 안에** 확인을 마쳐야 하고, 마치기 전에는 알림 메일이 오지 않을 수 있습니다. 같은 테넌트에서 이미 확인한 주소는 다시 확인하지 않습니다. 이 가이드에서는 메일 도착을 직접 확인하지 않았습니다 — 알림이 울렸는지는 위의 `az rest` 목록(`Fired`)으로 확인하세요.
            """,
        ),
        scope="apply",
    )

    # ───────── B7 · R6
    cm = snip("R6_network_logs.sh", "cm")
    b7_cm = walk(
        cm,
        [
            (
                "VM_ID=",
                "VM 의 리소스 ID",
                "측정의 **출발지**가 될 VM 의 리소스 ID 를 알아냅니다.",
            ),
            (
                "az vm extension set",
                "Network Watcher 에이전트 설치",
                """
                VM 에서 목적지까지의 연결을 재려면 VM 안에 측정용 에이전트가 필요합니다. VM 확장으로 설치합니다.
                * `--name NetworkWatcherAgentLinux --publisher Microsoft.Azure.NetworkWatcher` — Linux 용 에이전트
                * `--version 1.4 --extension-instance-name AzureNetworkWatcherExtension` — 버전과 확장 인스턴스 이름
                * `--enable-auto-upgrade true` — 자동 업그레이드
                """,
            ),
            (
                "az network watcher connection-monitor create",
                "Connection Monitor 만들기 — VM → AOAI:443 을 30초마다",
                """
                ‘VM 에서 AOAI 의 443 포트로 **TCP 연결**을 맺어 보는’ 테스트를 30초마다 실행해 **왕복 시간(RTT)과 실패율**을 기록합니다.
                * `--endpoint-source-name vm --endpoint-source-resource-id $VM_ID` — **출발지** = 이 VM
                * `--endpoint-dest-name aoai --endpoint-dest-address $AOAI_HOST --endpoint-dest-type ExternalAddress` — **목적지** = AOAI 호스트 주소(외부 주소로 취급)
                * `--test-group-name tg-aoai --test-config-name tcp443 --protocol Tcp --tcp-port 443 --frequency 30` — 테스트 이름 · **TCP 443** · **30초마다**
                * `--workspace-ids $LAW` — 결과를 **내 워크스페이스**(`NWConnectionMonitorTestResult` 테이블)로 보냄
                """,
            ),
        ],
        cap="가. Connection Monitor — VM → AOAI:443 을 30초마다 (R6)",
        tags={1: "apply", 2: "apply", 3: "apply"},
        run="B7",
    )
    b7_flow = walk(
        """az storage account create -n $ST -g $RG -l $LOC --sku Standard_LRS --kind StorageV2 --min-tls-version TLS1_2 --allow-blob-public-access false --tags $TAGS -o none
VNET_ID=$(az network vnet show -g $RG -n $VNET --query id -o tsv)
ST_ID=$(az storage account show -g $RG -n $ST --query id -o tsv)
az network watcher flow-log create -l koreacentral -n vnetfl-agent \\
  --vnet "$VNET_ID" --storage-account "$ST_ID" \\
  --traffic-analytics true --workspace $LAW --interval 10 --retention 30""",
        [
            (
                "az storage account create",
                "flow log 원본을 저장할 저장소 계정",
                "flow log 는 먼저 **저장소 계정**에 기록됩니다. `--sku Standard_LRS`(같은 리전의 표준 저장소) · `--min-tls-version TLS1_2` · `--allow-blob-public-access false`(**공개 접근 금지**)로 안전하게 만듭니다.",
            ),
            ("VNET_ID=", "ID 알아내기", "flow log 를 걸 **VNet** 과 **저장소 계정**의 리소스 ID 를 변수에 담습니다."),
            (
                "az network watcher flow-log create",
                "VNet flow log 만들기",
                """
                VNet 안의 **트래픽 흐름(누가 누구에게 몇 바이트)** 을 기록합니다.
                * `--vnet … --storage-account …` — 대상 VNet 과 저장소
                * `--traffic-analytics true --workspace $LAW --interval 10` — 저장소 기록을 **10분마다 분석해 워크스페이스로도** 보냄
                * `--retention 30` — 저장소에 **30일** 보관
                * NSG flow log 는 2025-06-30 이후 **신규 생성이 불가**해서 VNet flow log 를 씁니다. 연결 수 · 바이트만 기록하고 **지연 정보는 없습니다.**
                """,
            ),
        ],
        cap="나. (선택) VNet flow log — NSG flow log 는 2025-06-30 이후 신규 생성 불가",
        tags={1: "lab", 2: "apply", 3: "apply"},
        run="B7",
    )
    fw_create = """# 허브 VNet 과 Azure Firewall Basic (약 8분 소요 · 시간당 과금)
az network vnet create -g $RG -n vnet-lablog-hub -l $LOC --address-prefixes 10.30.0.0/16 \\
  --subnet-name AzureFirewallSubnet --subnet-prefixes 10.30.0.0/26 --tags $TAGS -o none
az network vnet subnet create -g $RG --vnet-name vnet-lablog-hub -n AzureFirewallManagementSubnet --address-prefixes 10.30.1.0/26 -o none
az network public-ip create -g $RG -n pip-lablog-fw -l $LOC --sku Standard --allocation-method Static --tags $TAGS -o none
az network public-ip create -g $RG -n pip-lablog-fwmgmt -l $LOC --sku Standard --allocation-method Static --tags $TAGS -o none
az network firewall policy create -g $RG -n fwp-lablog -l $LOC --sku Basic --tags $TAGS -o none
az network firewall create -g $RG -n fw-lablog -l $LOC --sku AZFW_VNet --tier Basic --firewall-policy fwp-lablog \\
  --vnet-name vnet-lablog-hub --conf-name ipconf --public-ip pip-lablog-fw \\
  --m-conf-name mgmtconf --m-public-ip pip-lablog-fwmgmt --tags $TAGS -o none
FW=$(az network firewall show -g $RG -n fw-lablog --query id -o tsv)
""" + snip("R6_network_logs.sh", "fw") + """
az monitor diagnostic-settings list --resource $FW --query "[].{name:name, dest:logAnalyticsDestinationType}" -o table
# 확인이 끝나면 바로 삭제 (시간당 과금 중지, 약 9분 소요)
az network firewall delete -g $RG -n fw-lablog
az network firewall policy delete -g $RG -n fwp-lablog
az network public-ip delete -g $RG -n pip-lablog-fw
az network public-ip delete -g $RG -n pip-lablog-fwmgmt
az network vnet delete -g $RG -n vnet-lablog-hub"""
    fw_walk = walk(
        fw_create,
        [
            (
                "# 허브 VNet",
                "(실습용) 허브 VNet · 공용 IP 2개 · 방화벽 정책 · 방화벽 만들기",
                """
                내 환경에는 **이미 있는 방화벽**이 대상이므로 이 부분은 실습용 임시 환경을 만드는 단계입니다. Azure Firewall 은 전용 서브넷(`AzureFirewallSubnet` · 관리용 `AzureFirewallManagementSubnet`)과 공용 IP 2개, 정책(`policy`)이 필요하고 Basic 등급은 시간당 과금됩니다.
                """,
            ),
            (
                "FW=",
                "방화벽 리소스 ID",
                "진단 설정을 걸 **방화벽의 리소스 ID** 를 변수에 담습니다.",
            ),
            (
                "az monitor diagnostic-settings create -n fw-latency-logs",
                "방화벽 진단 설정 — 로그 설정 · 메트릭 설정 (이 부분이 핵심)",
                """
                **이 부분이 내 방화벽에 그대로 적용하는 명령입니다.**
                * `fw-latency-logs` — 로그 3종 저장: `AZFWApplicationRule`(**FQDN 규칙** 처리 기록) · `AZFWNetworkRule`(네트워크 규칙) · `AZFWDnsQuery`(**DNS 조회 시간**). `--export-to-resource-specific true` 로 **전용 테이블**에 저장합니다.
                * `fw-latency-metrics` — 메트릭(예: **`SNATPortUtilization`**, SNAT 포트 사용률)은 로그와 **별도 진단 설정**으로 저장합니다.
                """,
            ),
            (
                "az monitor diagnostic-settings list --resource $FW",
                "확인 · 삭제",
                "진단 설정이 만들어졌는지 확인한 뒤, **시간당 과금을 멈추려고 방화벽 · 정책 · 공용 IP · 허브 VNet 을 즉시 삭제**합니다(약 9분 소요).",
            ),
        ],
        cap="다. (선택) Firewall 생성 → 진단 설정 → 삭제",
        tags={1: "lab", 2: "lab", 3: "apply", 4: "lab"},
        run="B7",
        skip=True,
    )
    b7 = step(
        "b7",
        "네트워크 경로 로그 — Connection Monitor · VNet flow log · (선택) Azure Firewall",
        "B7 · R6",
        "소요 약 5분 (Firewall 포함 시 약 25분) · 필요한 권한: VM 확장 설치 · Network Watcher 리소스 생성(예: Virtual Machine Contributor + Network Contributor) · 저장소 계정 생성",
        brief(
            what="**VM → AOAI 경로**의 로그를 모읍니다. Connection Monitor 는 VM 에서 AOAI 443 포트로 **TCP 연결 시간(RTT)과 실패율**을 30초마다 재고, VNet flow log 는 연결 수 · 바이트를, Azure Firewall 진단 로그는 FQDN 규칙 · DNS · SNAT 포트 사용률을 줍니다.",
            why="앱과 probe(VM 안)가 느린데 probe(VM 밖)는 정상일 때 **경로(방화벽 · DNS · SNAT)** 가 의심됩니다. 그때 쓰는 로그입니다.",
            result="`NWConnectionMonitorTestResult` 테이블에 30초마다 RTT 가 쌓이고, VNet flow log 가 켜집니다.",
            apply="**경로에 Azure Firewall 이 있으면** 방화벽 진단 설정(아래 ‘다’ 부분)을 내 방화벽에 그대로 적용합니다(허브 구독 권한 필요). 방화벽이 아닌 **타사 NVA** 라면 세션 수 · SNAT 풀 사용률 · 연결 실패 로그를 벤더 기준으로 요청해야 합니다. Network Watcher 가 해당 리전에 있어야 하고, 저장소는 같은 리전의 Standard 계정이어야 합니다. 리전이 koreacentral 이 아니면 아래 명령의 `-l koreacentral`(2곳)을 내 리전으로 바꾸세요.",
        )
        + call(
            "tip",
            "이 단계는 꼭 해야 하나요? — 경로가 의심될 때 필요합니다",
            """
            앱과 probe(VM 안)가 느린데 VM 밖 probe 는 정상이거나, **VM 에서 AOAI 로 가는 길에 방화벽 · 프록시 · NAT** 가 있을 때 필요합니다. 그런 의심이 없으면 **B7 은 건너뛰고 나중에 필요할 때** 해도 됩니다. 세 가지로 나뉩니다.
            - **가. Connection Monitor** — VM → AOAI 연결(TCP)에 걸린 **왕복 시간(RTT)과 실패율**을 30초마다 잽니다. 가장 쓸모가 큽니다.
            - **나. VNet flow log** — 네트워크 안의 **연결 수 · 바이트**를 기록합니다(지연 정보는 없음).
            - **다. (선택) Azure Firewall 진단 설정** — 방화벽이 있을 때만. FQDN 규칙 · DNS 조회 · SNAT 포트 사용률.
            """,
        )
        + call(
            "warn",
            "시작 전에 — 같은 이름이 이미 있는지 확인하세요",
            """
            Connection Monitor(`cm-vm-to-aoai`)와 flow log(`vnetfl-agent`)는 **리소스 그룹이 아니라 리전별 Network Watcher(`NetworkWatcherRG`)에 만들어지고 이름이 고정**되어 있습니다. 같은 구독을 다른 사람과 함께 쓰거나 이미 비슷한 설정이 있다면 이름이 겹쳐 **기존 설정을 덮어쓸 수 있습니다.** 만들기 전에 먼저 목록을 보세요. 겹치면 B7 명령의 `cm-vm-to-aoai` · `vnetfl-agent` 를 다른 이름으로 바꿔 쓰고, **D 의 삭제 명령도 같은 이름으로 바꾸세요.**
            """,
        )
        + code(
            "az network watcher connection-monitor list -l $LOC -o table      # 이미 있는 Connection Monitor 목록 (비어 있으면 OK)\n"
            "az network watcher flow-log list -l $LOC -o table                # 이미 있는 flow log 목록 (비어 있으면 OK)",
            cap="(확인) 같은 이름이 있는지 — 실행 블록이 아닌 확인용 명령",
        )
        + b7_cm
        + out(
            """{ "name": "AzureNetworkWatcherExtension", "provisioningState": "Succeeded", "typeHandlerVersion": "1.4", … }
{ "name": "cm-vm-to-aoai", "provisioningState": "Succeeded", … "testConfigurations": [{ "name": "tcp443", "tcpConfiguration": { "port": 443 } … }] }""",
            read="확장과 Connection Monitor 두 JSON 모두 `provisioningState: Succeeded` 이면 정상입니다. 측정값은 몇 분 뒤 `NWConnectionMonitorTestResult` 에 들어옵니다(C4 에서 이 결과를 읽어 봅니다 — 쿼리 `cm_aoai_rtt`).",
        )
        + b7_flow
        + out(
            """{ "enabled": true, "name": "vnetfl-agent", "provisioningState": "Succeeded",
  "flowAnalyticsConfiguration": { "networkWatcherFlowAnalyticsConfiguration": { "enabled": true, "trafficAnalyticsInterval": 10 } }, … }""",
            read="`enabled: true` · `provisioningState: Succeeded` 이면 켜진 것입니다. `trafficAnalyticsInterval: 10` 은 10분마다 분석한다는 뜻입니다.",
        )
        + call(
            "info",
            "실측",
            "`NetworkWatcherAgentLinux` 는 문서의 지원 목록(RHEL 6.10 · 7 · 8 · 9.2)에 없는 **RHEL 9.8** 에서도 설치되어 측정값이 들어왔습니다(같은 리전 TCP RTT 약 2ms · 실패 0). 다만 **지원 목록 밖이므로 실습용 확인일 뿐**이며, 운영 VM 은 지원되는 OS 버전인지 먼저 확인하세요. VNet flow log 는 연결 수 · 바이트만 기록하고 지연 정보는 없습니다.",
        )
        + details(
            "(선택) Azure Firewall 진단 설정 — 시간당 과금, 확인 후 즉시 삭제",
            md("내 환경에 Azure Firewall 이 있을 때의 ‘다’ 단계입니다. 실습에서는 Basic SKU 를 잠깐 만들어 **진단 설정 명령이 유효한지**(`AZFWApplicationRule` · `AZFWNetworkRule` · `AZFWDnsQuery` 전용 테이블, 메트릭 별도 설정)를 확인했습니다. VM 트래픽을 방화벽으로 보내는 경로(UDR · 규칙)는 구성하지 않았으므로 **로그 행은 생기지 않습니다.**")
            + fw_walk
            + out(
                """Name                Dest
------------------  ----------------
fw-latency-logs     Dedicated
fw-latency-metrics  AzureDiagnostics""",
                read="로그 설정은 **`Dedicated`**(전용 테이블), 메트릭 설정은 `AzureDiagnostics` 로 저장된다는 뜻입니다.",
            ),
        )
        + call(
            "warn",
            "Azure Firewall 이 아닌 경우",
            "타사 NVA 라면 세션 수 · SNAT 풀 사용률 · 연결 실패 로그를 벤더 기준으로 요청해야 합니다. 방화벽 메트릭(예: `SNATPortUtilization`)은 로그와 **별도 진단 설정**으로 저장합니다.",
        ),
        scope="opt",
    )
    return b5 + b6 + b7
