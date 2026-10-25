# -*- coding: utf-8 -*-
# B · 로그 켜기 (R1 R5 R3·R4 R7 R2 R8 R6) — B1~B4 는 이 파일, B5~B7 은 part_b2.py
from lib import *
import part_b2


def vmfile(path, content, quoted=True):
    c = content.rstrip("\n")
    assert not any(l.strip() == "EOF" for l in c.split("\n")), path
    return f"cat > {path} <<{chr(39) + 'EOF' + chr(39) if quoted else 'EOF'}\n{c}\nEOF\n"


def build():
    # ───────── B1 · R1
    b1 = step(
        "b1",
        "AOAI 진단 설정 → Log Analytics",
        "B1 · R1",
        "코드 · 재배포 없음 · 소요 약 1분 · 필요한 권한: AOAI 리소스에 진단 설정을 만들 수 있는 권한(예: Monitoring Contributor) + 워크스페이스 접근 권한",
        brief(
            what="AOAI 가 **서비스 쪽에서 잰** 요청별 처리 시간(`DurationMs`) · 상태 코드 · 토큰 수를 Log Analytics 로 보내도록 **진단 설정**을 켭니다. `RequestResponse`(요청 로그) · `Audit`(관리 이벤트) · `AllMetrics`(메트릭) 세 가지만 켭니다.",
            why="앱이 잰 시간과 **AOAI 가 잰 시간을 비교**해야 ‘느린 곳이 AOAI 인지 아닌지’ 알 수 있습니다. 이 로그가 그 비교의 AOAI 쪽 기준 데이터입니다.",
            result="진단 설정 `diag-aoai-latency` 1개. 로그는 **설정 약 20~26분 뒤부터** 쌓이기 시작합니다(아래 알림 상자).",
            apply="내 AOAI 리소스에 **코드 변경 · 재배포 없이** 그대로 적용합니다. 먼저 `az monitor diagnostic-settings list --resource <AOAI 리소스 ID>` 로 **이미 진단 설정이 있는지** 확인하세요(리소스당 최대 5개, Azure Policy 가 자동으로 만들었을 수 있음).",
            caution="**B1 을 가장 먼저** 하세요. 로그가 보이기까지 가장 오래 걸리므로, 기다리는 동안 B2~B7 을 진행하면 시간이 절약됩니다.",
        )
        + walk(
            snip("R1_aoai_diagnostic_settings.sh", "diag"),
            [
                (
                    "AOAI_ID=",
                    "대상 리소스의 ID 알아내기",
                    "진단 설정은 ‘어떤 리소스의’ 설정인지 **리소스 ID** 로 지정합니다. `az cognitiveservices account show … --query id -o tsv` 가 AOAI 리소스의 ID 한 줄을 `AOAI_ID` 에 담습니다(A4 에서 이미 저장했다면 같은 값입니다).",
                ),
                (
                    "az monitor diagnostic-settings create",
                    "진단 설정 만들기 — 무엇을 어디로 보낼지",
                    """
                    * `-n diag-aoai-latency` — 설정 이름(자유)
                    * `--resource $AOAI_ID` — **AOAI 리소스**에 거는 설정
                    * `--workspace $LAW` — 로그를 보낼 **Log Analytics 워크스페이스**(리소스 ID)
                    * `--metrics '[{"category":"AllMetrics","enabled":true}]'` — **메트릭 전체**를 로그 테이블(`AzureMetrics`)로도 저장
                    * `--logs '[{"category":"RequestResponse",…},{"category":"Audit",…}]'` — 켤 **로그 범주** 두 가지

                    로그 범주의 뜻:
                    - **`RequestResponse`** — API 호출 **한 건마다 한 행**. 시각 · 작업 이름 · 결과 코드(`ResultSignature`, 200/429/499 …) · **처리 시간(`DurationMs`)** · 호출자 IP(끝자리는 마스킹) · 상관 ID(`CorrelationId`) 와, `properties_s`(JSON)에 **배포 이름 · 프롬프트/완료 토큰 수 · 요청/응답 길이**가 들어 있습니다. **프롬프트 · 응답 본문은 없습니다.** 이 실습에서는 **없는 배포 이름을 부른 404 요청이 기록되지 않았습니다**(실측) — ‘로그에 없다 = 요청이 안 왔다’ 로 단정하지 마세요.
                    - **`Audit`** — 감사(관리) 로그 범주입니다. 이 실습에서는 **내용을 분석하지 않았습니다**(지연 진단에 쓰지 않음). 리소스 설정 변경 이력은 보통 Azure **활동 로그(Activity Log)** 에서 봅니다.
                    - 이 로그들은 `AzureDiagnostics` 테이블에, 메트릭은 `AzureMetrics` 테이블에 저장됩니다.
                    """,
                ),
                (
                    "az monitor diagnostic-settings list",
                    "만들어졌는지 확인",
                    "AOAI 리소스에 걸린 진단 설정 목록을 표로 보여 줍니다. `diag-aoai-latency` 가 보이면 성공입니다.",
                ),
            ],
            cap="진단 설정 만들기 (R1)",
            tags={1: "apply", 2: "apply", 3: "apply"},
            run="B1",
        )
        + out(
            """Name               ResourceGroup  WorkspaceId
-----------------  -------------  ---------------------------------------------------------------
diag-aoai-latency  rg-lablog-…     /subscriptions/…/workspaces/law-lablog-…""",
            label="예상 결과 (생성된 설정의 JSON 이 먼저 출력되고, 마지막에 이 목록)",
            read="맨 마지막 표에 `diag-aoai-latency` 가 있고 `WorkspaceId` 가 A2 에서 만든 워크스페이스를 가리키면 정상입니다.",
        )
        + call(
            "info",
            "로그는 바로 보이지 않습니다 — 약 20~26분 기다려야 합니다",
            """
            실측(두 번 반복): **진단 설정 후 약 20~26분이 지나서야 AOAI 요청이 기록되기 시작**했고, 그 전에 한 호출은 로그에 남지 않았습니다(나중에 채워지지 않음). 기록이 시작된 뒤에는 평균 약 2분 뒤에 조회됩니다.
            그래서 **B1 을 가장 먼저** 하고 약 30분 뒤에 확인하며, 기다리는 동안 B2~B7 을 진행하세요. 확인은 [C1](#c1) 에서 합니다.
            """,
        ),
        scope="apply",
    )

    # ───────── B2 · R5
    dcr = snipfile("R5_dcr_linux.json")
    b2_dcr = walk(
        "cat > R5_dcr_linux.json <<'EOF'\n" + dcr + "\nEOF",
        [
            (
                "cat > R5_dcr_linux.json",
                "수집 규칙 파일을 만든다 — 큰 구조",
                """
                **수집 규칙(DCR)** 은 ‘어떤 데이터를 · 어디서 · 어디로 보낼지’를 적은 JSON 문서입니다. `cat > 파일 <<'EOF' … EOF` 는 EOF 사이의 내용을 **파일로 저장**하는 셸 문법입니다.
                JSON 은 크게 `dataSources`(무엇을 수집) · `destinations`(어디로) · `dataFlows`(둘을 연결) 세 부분입니다.
                """,
            ),
            (
                '"dataSources"',
                "수집 ① 성능 카운터 — 60초마다",
                """
                `performanceCounters` 에 `perf60s` 라는 수집 항목을 하나 둡니다.
                * `"streams": ["Microsoft-Perf"]` — 수집한 값이 들어갈 **데이터 흐름(스트림) 이름**. 워크스페이스의 `Perf` 테이블로 저장됩니다.
                * `"samplingFrequencyInSeconds": 60` — **60초마다** 한 번 측정
                """,
            ),
            (
                '"counterSpecifiers"',
                "수집할 카운터 12개",
                """
                지연 순간에 VM 이 **바빴는지**를 보려는 카운터들입니다. 이름은 Linux 형식 그대로여야 합니다(`Logical Disk` 는 공백 포함). 카운터 이름 속 `(*)` 는 **모든 인스턴스**를 뜻하는 와일드카드입니다 — `Processor(*)` 는 코어별 값과 전체 합계(`_Total`), `Logical Disk(*)` 는 파티션별 값이 각각 한 행씩 들어옵니다(`Perf` 테이블의 `InstanceName` 열로 구분). JSON 에서 역슬래시를 쓰려고 `\\\\` 로 두 번 썼습니다.
                - **CPU**: `% Processor Time`(사용률) · `% IO Wait Time`(디스크 입출력을 기다리느라 놀고 있는 비율)
                - **메모리**: `% Used Memory` · `Available MBytes Memory` · `% Used Swap Space`
                - **디스크**: `Disk Transfers/sec`(초당 입출력 횟수) · `% Free Space`
                - **네트워크**: `Total Bytes Received/Transmitted` · `Total Rx/Tx Errors`
                - **시스템**: `Load1`(최근 1분 평균 부하)
                """,
            ),
            (
                '"syslog"',
                "수집 ② syslog — cron 과 local5 만",
                """
                Linux 의 로그 통로(syslog)에서 **필요한 채널만** 가져옵니다.
                * `"facilityNames": ["cron", "local5"]` — syslog 의 **facility(로그를 구분하는 채널 이름)** 중 **`cron`**(정해진 시각에 도는 작업의 실행 기록. 정각 · 30분에 무슨 일이 도는지 찾는 용도)과 **`local5`**(사용자 정의 채널 중 하나. B4 의 probe 와 스냅샷이 `logger -p local5.info` 로 자기 기록을 남기는 데 씁니다)만 가져옵니다.
                * `"logLevels": ["Info", …, "Emergency"]` — Info 이상 모든 수준
                * 저장 위치는 `Microsoft-Syslog` 스트림 → 워크스페이스의 `Syslog` 테이블
                """,
            ),
            (
                '"destinations"',
                "보낼 곳 — 내 워크스페이스",
                "`<LAW_ID>` 는 **자리 표시자**입니다. 다음 단계의 `sed` 가 실제 워크스페이스 리소스 ID 로 바꿔 줍니다. `\"name\": \"law\"` 는 아래 dataFlows 가 이 목적지를 가리킬 때 쓰는 별명입니다.",
            ),
            (
                '"dataFlows"',
                "연결 — 어떤 데이터를 어디로",
                """
                데이터 흐름 2개: **성능(`Microsoft-Perf`)** 과 **syslog(`Microsoft-Syslog`)** 를 각각 `law` 로 보냅니다.
                * `"transformKql": "source"` — **변환 없이 있는 그대로** 저장(수집 단계에서 필터링 · 가공하지 않음)
                * `"outputStream"` — 저장될 테이블(스트림) 이름
                """,
            ),
        ],
        cap="① 수집 규칙 파일 만들기 (R5_dcr_linux.json)",
        run="B2",
        lang="json",
        tags={1: "apply", 2: "apply", 3: "apply", 4: "apply", 5: "apply", 6: "apply"},
    )
    b2_ama = walk(
        snip("R5_vm_ama_dcr.sh", "ama"),
        [
            ("VM_ID=", "VM 의 리소스 ID", "수집 규칙을 ‘어떤 VM 에’ 연결할지 지정하려고 VM 의 **리소스 ID** 를 알아냅니다."),
            (
                "az vm identity assign",
                "관리 ID 켜기 (이미 켜져 있으면 그대로)",
                "에이전트가 Azure 에 로그를 보낼 때 쓰는 VM 의 **신원(시스템 할당 관리 ID)** 입니다. A4 에서 이미 켰으므로 아무 일도 일어나지 않습니다. 내 VM 에 관리 ID 가 아직 없다면 이 줄이 켜 줍니다.",
            ),
            (
                "az vm extension set",
                "Azure Monitor Agent(AMA) 설치",
                """
                VM **확장(extension)** 으로 에이전트를 설치합니다. VM 안에서 직접 설치하지 않고 Azure 가 대신 설치해 줍니다.
                * `--name AzureMonitorLinuxAgent --publisher Microsoft.Azure.Monitor` — Linux 용 AMA
                * `--enable-auto-upgrade true` — 에이전트 새 버전이 나오면 **자동 업그레이드**
                """,
            ),
            (
                "sed \"s#<LAW_ID>#$LAW#\"",
                "자리 표시자를 실제 ID 로 치환",
                "`sed` 로 JSON 안의 `<LAW_ID>` 를 `$LAW` 값(워크스페이스 리소스 ID)으로 바꿔 `/tmp/dcr.json` 으로 저장합니다. 리소스 ID 에 `/` 가 들어 있으므로 구분자로 `/` 대신 `#` 을 썼습니다.",
            ),
            (
                "DCR_ID=",
                "수집 규칙(DCR) 만들기",
                """
                * `-n dcr-aoai-vm-latency` — 규칙 이름
                * `--kind Linux` — Linux VM 용 규칙
                * `--rule-file /tmp/dcr.json` — 위에서 만든 JSON 파일이 규칙의 내용
                * `--query id -o tsv` — 만들어진 규칙의 **ID** 만 `DCR_ID` 에 담습니다.
                """,
            ),
            (
                "az monitor data-collection rule association create",
                "규칙을 VM 에 연결",
                "‘규칙’과 ‘VM’은 **연결(association)** 을 만들어야 효력이 생깁니다. `--rule-id $DCR_ID --resource $VM_ID` 가 이 VM 이 위 규칙대로 수집하게 합니다.",
            ),
        ],
        cap="② 에이전트 설치 + 수집 규칙 연결 (R5)",
        tags={1: "apply", 2: "apply", 3: "apply", 4: "apply", 5: "apply", 6: "apply"},
        run="B2",
    )
    b2 = step(
        "b2",
        "모니터링 에이전트(Azure Monitor Agent, AMA) + 수집 규칙(DCR)",
        "B2 · R5",
        "소요 약 3분 · 필요한 권한: VM 에 확장을 설치하고 수집 규칙을 만들어 연결할 수 있는 권한(예: Virtual Machine Contributor + Monitoring Contributor)",
        brief(
            what="VM 의 CPU · 메모리 · 디스크 · 네트워크 **성능 카운터 12개**(60초 간격)와 **cron · local5 syslog** 만 수집하는 규칙(DCR)을 만들어 VM 에 연결하고, 수집 프로그램(Azure Monitor Agent)을 설치합니다.",
            why="‘정각 · 30분에 느려진다’ 같은 패턴은 VM 에서 도는 **배치 작업(cron)** 이나 CPU · 디스크 부하 때문일 수 있습니다. 그 순간 VM 의 상태를 시각으로 맞춰 보려는 것입니다. (local5 는 B4 의 probe 가 자기 기록을 남기는 로그 채널입니다.)",
            result="확장 `AzureMonitorLinuxAgent` 와 규칙 연결이 만들어지고, **5~10분 뒤** `Heartbeat` · `Perf` · `Syslog` 테이블에 데이터가 들어옵니다(C1 에서 확인).",
            apply="내 VM 에 그대로 적용합니다(RHEL 계열 기준). **먼저 아래 ‘사전 확인’ 표를 VM 안에서** 확인하세요.",
        )
        + md("**사전 확인 — 내 VM 안에서** (`vmrun <<'X'` 다음 줄에 명령을 쓰고 `X` 로 닫아 실행)")
        + table(
            ["확인 명령", "정상", "아니면"],
            [
                ["`cat /etc/redhat-release`", "RHEL 7.9 · 8.x · 9 이상", "다른 OS 면 Azure Monitor Agent 지원 OS 목록을 먼저 확인"],
                ["`python3 --version`", "버전이 출력됨", "없으면 설치(에이전트가 요구)"],
                ["`rpm -q which initscripts`", "두 패키지 모두 설치됨", "`sudo dnf install -y which initscripts`"],
                ["`systemctl is-active rsyslog`", "`active`", "rsyslog 를 설치 · 시작(syslog 수집이 안 됨)"],
                ["`update-crypto-policies --show`", "`FUTURE` 가 아님", "`FUTURE` 이면 에이전트가 **동작하지 않으므로** 보안 담당자와 정책 조정을 상의"],
            ],
        )
        + b2_dcr
        + b2_ama
        + out(
            """{ "name": "AzureMonitorLinuxAgent", "provisioningState": "Succeeded", "typeHandlerVersion": "1.4x", … }
{ "name": "assoc-vm-lablog-rhel", "type": "Microsoft.Insights/dataCollectionRuleAssociations", … }""",
            label="예상 결과 (확장 · 규칙 연결 JSON)",
            read="관리 ID · 확장 · 규칙 연결 JSON(2~3개)이 에러 없이 나오고 `provisioningState` 가 `Succeeded` 이면 정상입니다. 데이터 확인은 연결 후 5~10분 뒤 C1 에서 합니다.",
        )
        + call("info", "확인은 약 10분 뒤", "연결 후 **약 5~10분**이면 `Heartbeat`(에이전트가 살아 있다는 신호) · `Perf` · `Syslog` 가 들어옵니다. 카운터 이름은 Linux 형식(`Logical Disk` 는 공백 포함)을 지켜야 합니다."),
        scope="apply",
    )

    # ───────── B3 · R3 + R4
    r3_helper = snipfile("R3_aoai_call_log.py")
    r3_usage = snipfile("R3_usage_example.py")
    app_demo = open(VMF + "app_demo.py", encoding="utf-8").read()
    svc = open(VMF + "report-agent.service", encoding="utf-8").read()
    envs = snipfile("R4_telemetry.env.sample")
    script_b3 = (
        "set -e\ninstall -d /opt/report-agent /etc/report-agent\n"
        + vmfile("/opt/report-agent/R3_aoai_call_log.py", r3_helper)
        + vmfile("/opt/report-agent/R3_usage_example.py", r3_usage)
        + vmfile("/opt/report-agent/app_demo.py", app_demo)
        + vmfile("/etc/systemd/system/report-agent.service", svc)
        + vmfile("/tmp/R4_telemetry.env.sample", envs)
        + """# 앱 환경변수 (키는 권한 600 파일에만 둡니다)
umask 077
printf 'AZURE_OPENAI_ENDPOINT=https://%s\\nAZURE_OPENAI_API_KEY=%s\\nAOAI_DEPLOYMENT=%s\\n' "$AOAI_HOST" "$AOAI_KEY" "$DEP" > /etc/report-agent/app.env
umask 022
# 텔레메트리 환경변수 파일 설치 + 연결 문자열 입력 (편집기 대신 sed 사용)
install -D -m 0600 /tmp/R4_telemetry.env.sample /etc/report-agent/telemetry.env
CS=$(printf %s "$CS_B64" | base64 -d)
sed -i "s#^APPLICATIONINSIGHTS_CONNECTION_STRING=.*#APPLICATIONINSIGHTS_CONNECTION_STRING=\\"$CS\\"#" /etc/report-agent/telemetry.env
# systemd 에 환경변수 파일 연결 (드롭인 파일 — 'systemctl edit' 과 같은 결과)
install -d /etc/systemd/system/report-agent.service.d
printf '[Service]\\nEnvironmentFile=/etc/report-agent/telemetry.env\\n' > /etc/systemd/system/report-agent.service.d/telemetry.conf
systemctl daemon-reload
systemctl enable --now report-agent
sleep 25
systemctl is-active report-agent
journalctl -u report-agent -n 5 --no-pager -o cat | cut -c1-330
"""
    )
    b3_text = (
        """KEY=$(az cognitiveservices account keys list -g $RG -n $AOAI --query key1 -o tsv)
CS=$(az monitor app-insights component show -a $APPI -g $RG --query connectionString -o tsv)
vmrun AOAI_HOST=$AOAI_HOST DEP=$DEP AOAI_KEY=$KEY CS_B64="$(printf %s "$CS" | base64 | tr -d '\\n')" <<'VMEOF'
"""
        + script_b3
        + "VMEOF"
    )
    b3_walk = walk(
        b3_text,
        [
            (
                "KEY=$(az cognitiveservices",
                "내 컴퓨터에서: AOAI 키와 Application Insights 연결 문자열 가져오기",
                """
                데모 앱이 쓸 두 값을 **내 컴퓨터(터미널)** 에서 먼저 조회합니다.
                * `KEY` — AOAI 리소스의 **API 키**(`keys list … key1`). 이 데모 앱은 **단순하게 하려고 키로 인증**합니다. 키는 아래 `vmrun` 의 매개변수로 VM 에 전달되어 VM 의 `app.env`(권한 600)에 저장됩니다. 그래서 **실습이 끝나면 리소스 그룹을 삭제하거나 키를 재발급**하세요. 운영 앱은 키 없는 **관리 ID 인증**을 권장합니다([부록 B](#x2)).
                * `CS` — Application Insights 의 **연결 문자열**. 이 문자열이 있어야 앱이 데이터를 어디로 보낼지 압니다.
                """,
            ),
            (
                "vmrun AOAI_HOST",
                "VM 으로 값을 넘기며 스크립트 실행 시작",
                """
                `vmrun` 이 `<<'VMEOF'` 와 마지막 `VMEOF` 사이를 **VM 안에서** 실행합니다. 앞의 `이름=값` 들이 VM 안에서 `$AOAI_HOST` · `$DEP` · `$AOAI_KEY` · `$CS_B64` 가 됩니다.
                연결 문자열에는 `;` 가 들어 있어서 셸이 명령 구분자로 오해할 수 있으므로 **base64 로 바꿔서** 넘기고(`base64 | tr -d '\\n'` — `tr -d` 는 줄바꿈을 지웁니다), VM 안에서 원래대로 되돌립니다(`base64 -d`).
                """,
            ),
            ("set -e", "VM 안: 오류 시 중단 · 폴더 만들기", "`set -e` 로 처리되지 않은 명령 실패에서 스크립트가 멈추게 하고(A5 의 해설 참고), 앱 폴더 `/opt/report-agent` 와 설정 폴더 `/etc/report-agent` 를 만듭니다(`install -d` = 폴더 만들기)."),
            (
                "cat > /opt/report-agent/R3_aoai_call_log.py",
                "R3 헬퍼 ① 파일 만들기 · 도구 준비",
                """
                **호출 로그 헬퍼(`R3_aoai_call_log.py`)** 파일을 만드는 부분입니다. 이 파일은 **프로젝트에 한 번 추가**하면 되는 도구입니다. EOF 까지가 파일 내용입니다(주석의 ‘프롬프트·응답 본문은 기록하지 않는다’에 주목).
                가져오는 도구(import) 5개:
                * `json` — 기록을 JSON 한 줄로 만들기
                * `logging` — 로그 출력
                * `threading` — 동시에 진행 중인 호출 수를 **안전하게** 세기 위한 잠금
                * `time` — 걸린 시간 재기
                * `uuid` — 호출마다 **고유 ID(cid)** 만들기

                이어서 이 헬퍼가 쓰는 변수들입니다.
                * `log = logging.getLogger("aoai.call")` — 이 헬퍼가 쓰는 **로거 이름**. R4 가 `aoai` 로 시작하는 로거의 로그를 Application Insights 로 보내도록 설정합니다.
                * `_lock, _busy` — **이 프로세스 안에서** 지금 진행 중인 호출 수(`_busy`)와 그것을 보호하는 잠금(여러 프로세스 · 서버로 나뉜 앱은 각자 따로 셉니다)
                * `ERR` — 예외 종류에 붙일 **결과 이름표**: 타임아웃 예외(`APITimeoutError`)는 `client_timeout`, 그 외는 `error`
                """,
            ),
            (
                "@contextmanager",
                "R3 헬퍼 ② call_log() — 호출 시작 기록",
                """
                `call_log(...)` 는 **`with` 문으로 쓰는 도구**입니다(`@contextmanager`). `with call_log(…) as rec:` 안의 코드를 실행하기 전후에 자동으로 기록을 처리합니다.
                * `**fields` — 호출하는 쪽이 넘기는 **이름=값** 들(배포 이름 · job_id · max_tokens …)이 그대로 기록에 들어갑니다.
                * `_busy += 1` — 호출이 시작되었으니 진행 중 호출 수를 +1 하고, 그 값을 **`inflight`(시작 시점의 동시 호출 수)** 로 기록합니다. 동시 호출이 많을 때 느려지는지 볼 수 있습니다.
                * `rec` — 이 호출의 **기록 사전**: 사건 이름(`aoai_call`) · 호출 고유 ID(`cid`) · `inflight` · 넘겨받은 값들
                * `t0 = time.perf_counter()` — 시작 시각을 고정밀 타이머로 저장. 뒤의 `total_ms` 는 **여기서부터 `finally` 까지, 즉 `with` 블록 안(AOAI SDK 호출)에 걸린 시간**입니다. 호출 전의 준비 · 대기 시간은 들어 있지 않습니다.
                """,
            ),
            (
                "try:",
                "R3 헬퍼 ③ 성공 · 실패 · 마무리 — JSON 한 줄 남기기",
                """
                * `yield rec` — **여기서 `with` 블록 안의 코드(AOAI 호출)가 실행**됩니다. 블록 안에서 `rec` 에 응답 정보를 채워 넣습니다. 오류 없이 끝나면 `outcome = "ok"`.
                * `except Exception as e` — AOAI 호출이 **예외로 실패하면**: `outcome`(타임아웃이면 `client_timeout`, 아니면 `error`) · `error`(예외 이름) · `status`(HTTP 코드가 있으면) · `request_id` 를 기록하고, **`raise` 로 예외를 그대로 다시 던집니다.** 그래서 앱의 기존 오류 처리 동작은 바뀌지 않습니다.
                * `finally` — 성공이든 실패든 **항상 실행**: 진행 중 호출 수 −1, **`total_ms`**(걸린 시간, 밀리초) 기록, 그리고 `log.info(json.dumps(rec))` 로 **JSON 한 줄을 로그로 남깁니다.** `ensure_ascii=False` 는 한글이 `\\uXXXX` 로 깨지지 않게 합니다.
                """,
            ),
            (
                "cat > /opt/report-agent/R3_usage_example.py",
                "R3 호출부 ① 클라이언트 설정",
                """
                **기존 호출부에 적용하는 예시** 파일입니다. 먼저 필요한 것을 가져오고 클라이언트를 만듭니다.
                * `from R3_aoai_call_log import call_log` — 위에서 만든 헬퍼 사용
                * `logging.basicConfig(level=INFO, format="%(message)s")` — 로그를 **시각 · 레벨 없이 메시지만** 출력해서 JSON 한 줄이 그대로 보이게 합니다(운영에서는 파일이나 R4 핸들러로 대체).
                """,
            ),
            (
                "READ_TIMEOUT",
                "R3 호출부 ② AzureOpenAI 클라이언트 — timeout 과 재시도",
                """
                * `READ_TIMEOUT = 60.0` — 응답을 **기다려 주는 최대 시간(초)**. **내 앱의 현재 timeout 값**으로 바꿔 쓰세요.
                * `timeout=Timeout(5.0, read=READ_TIMEOUT)` — 연결 · 쓰기 · 연결 풀 대기는 각 5초, **응답 읽기는 `READ_TIMEOUT` 초**까지 기다립니다(읽기 제한은 ‘데이터가 오지 않고 흐른 시간’에 적용됩니다). 비스트리밍 호출에서는 사실상 ‘요청을 보낸 뒤 응답이 오기까지 기다리는 시간’입니다. **어느 단계든 시간 초과가 나면** `APITimeoutError` → 기록상 `client_timeout` 입니다. 그래서 `client_timeout` 이 항상 ‘AOAI 가 499 로 기록한 것’ 은 아닙니다(연결 단계에서 끊겼다면 AOAI 에는 기록이 없을 수 있습니다).
                * **`max_retries=0`** — SDK 기본 동작인 **자동 재시도를 끕니다.** 재시도가 켜져 있으면 한 번의 `ask()` 안에서 여러 번 호출되는데 기록은 한 줄뿐이라, ‘느린 이유가 재시도’라는 사실이 숨겨집니다. 끄면 **시도마다 한 줄**이 남습니다. **이것은 진단용 설정입니다.** 내 앱에서는 진단이 끝나면 **원래 값(기본 2회 재시도)으로 되돌리세요** — 끄면 일시적인 429/5xx 오류에서 자동 재시도가 사라져 실제 실패가 늘 수 있습니다.
                * `api_key` — 데모는 키를 쓰지만 운영은 **관리 ID** 를 권장한다는 주석이 있습니다.
                """,
            ),
            (
                "def ask(",
                "R3 호출부 ③ with call_log(…)로 감싼 호출",
                """
                **이 부분이 기존 코드에서 바뀌는 곳**입니다. 원래의 호출을 `with call_log(…) as rec:` 안에 넣습니다.
                * `call_log(deployment=…, job_id=…, max_tokens=800, stream=False, read_timeout_s=…)` — 이 호출의 **조건**을 기록에 남깁니다.
                * `client.chat.completions.with_raw_response.create(…)` — 평소의 `create` 와 같은 호출인데, **응답 헤더까지 볼 수 있는** 형태입니다(요청 ID 를 얻으려면 필요).
                * `extra_headers={"x-ms-client-request-id": rec["cid"]}` — 호출마다 만든 **고유 ID 를 요청 헤더에 실어 보냅니다.** 앱 로그의 `cid` 와 같은 값입니다(실측에서 이 값은 AOAI 진단 로그에 남지 않았으므로, 짝짓기는 아래 `apim-request-id` 로 합니다).
                """,
            ),
            (
                "res, h = raw.parse()",
                "R3 호출부 ④ 응답에서 기록할 값 꺼내기",
                """
                * `raw.parse()` — 평소 `create` 가 돌려주던 **응답 객체**
                * `raw.headers` — **응답 헤더**
                * `rec.update(…)` — 기록 사전에 응답 정보를 채웁니다:
                  - `status` — HTTP 상태 코드 · `region` — 요청을 처리한 리전(`x-ms-region`)
                  - `request_id`(`x-request-id`) · **`apim_request_id`(`apim-request-id`)** — 요청 ID. **`apim-request-id` 는 AOAI 진단 로그의 `CorrelationId` 와 같은 값**이라 C2 에서 앱 기록과 AOAI 기록을 **한 건씩 짝짓는 열쇠**입니다.
                  - `prompt_tokens` · `completion_tokens` — 입력 · 출력 토큰 수 · `finish_reason` — `stop`(정상 완료) / `length`(`max_tokens` 에 걸려 잘림)
                * `return res` — 호출한 쪽은 **예전과 똑같은 결과**를 받습니다.
                """,
            ),
            (
                "cat > /opt/report-agent/app_demo.py",
                "데모 앱 ① R4 — Application Insights 켜기 (핵심 두 줄)",
                """
                **실습용 데모 앱** 파일입니다(내 환경에는 설치하지 않습니다). 맨 위의 두 줄(`configure_azure_monitor` 호출과 `setLevel`)이 **R4 의 코드 변경 전부**이고, **내 앱에는 이 두 줄만 시작 코드에 추가**합니다.
                * `configure_azure_monitor(logger_name="aoai")` — OpenTelemetry 를 켜서 ① 앱의 **외부 HTTP 호출(= AOAI 호출)을 `AppDependencies` 로**, ② 이름이 `aoai` 로 시작하는 로거의 **로그를 `AppTraces` 로** Application Insights 에 보냅니다. 연결 문자열은 코드에 쓰지 않고 **환경변수**(`APPLICATIONINSIGHTS_CONNECTION_STRING`)에서 읽습니다. **openai 클라이언트를 만들기 전에 호출**해야 계측이 적용됩니다.
                * `setLevel(logging.INFO)` — INFO 수준 로그까지 전송(R3 가 INFO 로 남깁니다)
                """,
            ),
            (
                "import R3_usage_example as r3",
                "데모 앱 ② R3 가져오기 · 일부러 참을성 없는 클라이언트",
                """
                * `r3.ask` — 위 R3 호출부의 정상 호출 함수
                * `logging.getLogger().setLevel(WARNING)` — 다른 라이브러리의 HTTP 로그가 서비스 로그를 가득 채우지 않도록 합니다(`aoai` 로거는 위에서 INFO 로 유지).
                * `impatient` — **응답을 1초만 기다리는** 두 번째 클라이언트(`read=IMPATIENT_S=1.0`). 긴 답변은 1초 안에 끝나지 않으므로 `client_timeout` 이 나고, AOAI 쪽에서는 **499** 로 기록됩니다. 운영에서 겪을 상황을 일부러 만드는 장치입니다.
                """,
            ),
            (
                "def ask_impatient",
                "데모 앱 ③ ask_impatient — 같은 구조, 클라이언트만 다름",
                "R3 의 `ask()` 와 **완전히 같은 구조**이고 `impatient` 클라이언트를 쓰는 점만 다릅니다.",
            ),
            (
                "SHORT = ",
                "데모 앱 ④ 질문 두 가지",
                "`SHORT` = 한 문장 인사(답이 짧아 빠름), `LONG` = 700자 분량 설명 요청(출력 토큰이 많아 **몇 초 걸림**). 응답 길이에 따른 지연 차이를 보려는 것입니다.",
            ),
            (
                "i = 0",
                "데모 앱 ⑤ 무한 반복 — 호출 종류를 섞기",
                """
                8~16초마다 한 번씩 난수로 호출 종류를 고릅니다:
                - 55% 짧은 질문(정상) · 25% 긴 질문(정상, 느림)
                - 15% 긴 질문 + 1초 timeout → **`client_timeout`** (AOAI 쪽 499)
                - 5% **없는 배포 이름** → 404 → `outcome=error`
                예외는 `call_log` 가 이미 기록했으므로 `except Exception: pass` 로 삼켜서 앱이 멈추지 않게 합니다.
                """,
            ),
            (
                "cat > /etc/systemd/system/report-agent.service",
                "서비스 파일 — 데모 앱을 상시 실행",
                """
                **systemd 서비스 정의**입니다. 이 파일 덕분에 앱이 백그라운드로 계속 돌고, 죽으면 다시 살아나며, VM 을 재시작해도 자동으로 켜집니다.
                * `After/Wants=network-online.target` — **네트워크가 준비된 뒤** 시작
                * `EnvironmentFile=/etc/report-agent/app.env` — 아래에서 만들 **환경변수 파일**(AOAI 주소 · 키 · 배포 이름)을 읽음
                * `ExecStart=… venv/bin/python app_demo.py` — 가상환경의 Python 으로 앱 실행
                * `Restart=always` · `RestartSec=5` — **종료되면 5초 뒤 재시작**
                * `WantedBy=multi-user.target` — 부팅 시 자동 시작
                """,
            ),
            (
                "cat > /tmp/R4_telemetry.env.sample",
                "R4 환경변수 샘플 — 무엇을 어떻게 보낼지",
                """
                Application Insights 연결을 **코드 대신 환경변수로** 정합니다.
                * `APPLICATIONINSIGHTS_CONNECTION_STRING` — 데이터를 보낼 곳(연결 문자열). 아래에서 실제 값으로 채웁니다.
                * 맨 위 주석 `pip install "azure-monitor-opentelemetry>=1.8.10"` — **내 앱 환경에 한 번 설치**해야 하는 패키지입니다. 이 실습에서 검증한 버전(1.8.11)은 **Python 3.10 이상**이 필요합니다. 더 낮은 Python(RHEL 9 기본 3.9)에서는 pip 가 더 낮은 버전을 고를 수 있지만 그 조합은 검증하지 않았고, 그래서 이 실습은 Python 3.12 를 설치합니다.
                * `OTEL_SERVICE_NAME=report-agent` · `OTEL_RESOURCE_ATTRIBUTES=service.namespace=contoso` — 두 값이 합쳐져 Application Insights 에서 이 앱을 부르는 **이름(역할 이름, `AppRoleName`)이 `contoso.report-agent`** 로 나타납니다. 여러 앱이 같은 Application Insights 를 쓸 때 ‘어느 앱의 기록인지’ 구분하는 이름표입니다(내 앱 이름으로 바꾸세요).
                * **`OTEL_TRACES_SAMPLER=always_on`** — **샘플링을 끄고 모든 호출을 기록**합니다. 진단 기간에 꼭 필요한 설정입니다. 최근 버전의 기본값은 초당 약 5 트레이스(rate-limited)라 호출이 많으면 외부 호출 기록(`AppDependencies`)이 빠집니다. 로그(`AppTraces`)는 샘플링되지 않습니다.
                """,
            ),
            (
                "# 앱 환경변수",
                "앱 환경변수 파일 만들기 (키는 권한 600)",
                """
                * `umask 077` — 이후 만드는 파일의 권한을 **소유자만 읽기/쓰기(600)** 로. AOAI 키가 들어 있으니 다른 사용자가 못 읽게 합니다.
                * `printf '…' "$AOAI_HOST" "$AOAI_KEY" "$DEP" > /etc/report-agent/app.env` — **주소 · 키 · 배포 이름** 3줄을 파일로 씁니다. 서비스 파일의 `EnvironmentFile` 이 읽는 파일입니다.
                * `umask 022` — 권한 규칙을 일반적인 기본값(022)으로 되돌립니다(앞의 `umask 077` 은 이 위치까지만 적용하려는 것)
                """,
            ),
            (
                "# 텔레메트리 환경변수",
                "R4 환경변수 파일 설치 + 연결 문자열 입력",
                """
                * `install -D -m 0600 … /etc/report-agent/telemetry.env` — 샘플을 **권한 600** 으로 설치(없는 폴더는 자동 생성)
                * `CS=$(printf %s "$CS_B64" | base64 -d)` — 위에서 base64 로 넘긴 연결 문자열을 **원래대로 복원**
                * `sed -i "s#^APPLICATIONINSIGHTS_CONNECTION_STRING=.*#…\\"$CS\\"#" …` — 파일의 해당 줄(`APPLICATIONINSIGHTS_CONNECTION_STRING=` 로 시작하는 줄)을 실제 값으로 **치환**합니다. 편집기(`vi`)로 직접 고치는 것을 자동화한 것이고, `\\"` 는 값을 큰따옴표로 감싸려는 표기입니다.
                """,
            ),
            (
                "# systemd 에 환경변수",
                "서비스에 환경변수 파일 연결 (드롭인)",
                "`report-agent.service.d/telemetry.conf` 는 서비스 정의에 **설정을 덧붙이는 조각 파일**(드롭인)입니다. `EnvironmentFile=/etc/report-agent/telemetry.env` 한 줄로, 앱이 시작할 때 R4 환경변수도 읽게 합니다. (`systemctl edit report-agent` 로 편집기를 열어 넣는 것과 같은 결과입니다.) **내 앱이 systemd 가 아니라 컨테이너 · IIS 등으로 실행된다면, 그 실행 방식에 맞게 같은 환경변수 4개를 전달**하세요.",
            ),
            (
                "systemctl daemon-reload",
                "서비스 시작 · 확인",
                """
                * `systemctl daemon-reload` — 방금 만든 서비스 파일을 systemd 가 **다시 읽게** 함
                * `systemctl enable --now report-agent` — **부팅 시 자동 시작으로 등록하고(`enable`) 지금 바로 시작(`--now`)**
                * `sleep 25` — 앱이 몇 번 호출하도록 25초 기다림
                * `systemctl is-active report-agent` — 실행 중이면 `active`
                * `journalctl -u report-agent -n 5 … | cut -c1-330` — 앱 서비스의 **최근 로그 5줄**(R3 의 JSON 줄)을 330자까지 출력
                """,
            ),
        ],
        cap="앱 파일 설치 · 환경변수 · systemd 서비스 시작 (156줄 — 복사 버튼은 ‘전체 복사’ 하나만 쓰세요)",
        run="B3",
        tags={1: "lab", 2: "lab", 3: "lab", 4: "apply", 5: "apply", 6: "apply", 7: "apply", 8: "apply", 9: "apply", 10: "apply", 11: "apply", 12: "lab", 13: "lab", 14: "lab", 15: "lab", 16: "lab", 17: "apply", 18: "lab", 19: "apply", 20: "apply", 21: "lab"},
    )
    b3_intro = (
        md("**먼저 큰 그림 — R3 와 R4 는 무엇이 다른가요?** 이 단계는 서로 다른 두 가지를 한꺼번에 설치합니다.")
        + table(
            ["", "R3 · 호출 로그 헬퍼", "R4 · Application Insights 연결"],
            [
                ["하는 일", "앱이 AOAI 를 **한 번 부를 때마다** 걸린 시간 · 결과 · 요청 ID · 토큰 수 · 동시 호출 수를 **JSON 한 줄**로 남깁니다.", "앱의 **외부 호출(AOAI 포함)** 과 앱 로그를 **Application Insights** 로 자동 전송합니다."],
                ["코드 변경", "기존 호출을 `with call_log(…)` 로 **감쌈**(헬퍼 파일 1개 추가)", "앱 시작 코드 **2줄**(`configure_azure_monitor(…)` · `setLevel`) + **환경변수**"],
                ["남는 곳", "앱 로그(`journalctl`) — R4 덕분에 `AppTraces` 에도 들어감", "`AppDependencies`(외부 호출 1건 = 1행) · `AppTraces`"],
                ["C 단계에서 쓰임", "`apim_request_id` 로 **AOAI 로그와 한 건씩 짝짓기**, `inflight` 로 동시 호출 영향 보기", "앱이 잰 시간 · 성공 여부를 **쿼리로 조회**"],
            ],
        )
        + md("**왜 둘 다 필요한가요?** R3 만 있으면 기록이 앱 서버의 로그 파일에만 남아 쿼리로 모아 보기 어렵고, R4 만 있으면 AOAI 로그와 한 건씩 맞출 열쇠(`apim_request_id`)와 앱의 timeout 설정 · 동시 호출 수가 없습니다. **R3 가 기록을 만들고, R4 가 그 기록을 Application Insights 로 실어 나릅니다.**")
        + details(
            "이 스크립트의 구간 지도 — 21개 구간이 어떻게 나뉘는지 (아래 해설 번호와 같습니다)",
            md(
                """
                * **구간 1~3 · 준비** (실습 전용): 내 컴퓨터에서 키와 연결 문자열을 가져오고, VM 으로 값을 넘겨 스크립트 실행을 시작합니다.
                * **구간 4~6 · R3 헬퍼** (내 앱에 추가): 호출 로그를 JSON 한 줄로 남기는 도구 파일입니다.
                * **구간 7~10 · R3 호출부 예시** (내 앱에 적용): 기존 AOAI 호출을 어떻게 감싸는지 보여 주는 파일입니다.
                * **구간 11 · 데모 앱의 R4 두 줄** (내 앱에도): Application Insights 를 켜는 코드입니다. **12~16 은 데모 앱 자체**(호출을 반복해서 만들고 서비스로 실행)라서 내 환경에는 필요 없습니다.
                * **구간 17~20 · R4 환경변수** (내 앱에 적용): 연결 문자열과 샘플링 설정을 환경변수로 넣습니다.
                * **구간 21 · 서비스 시작 · 확인** (실습 전용)
                """
            ),
            open_=True,
        )
    )
    apply_snip = (
        "# (설명용 발췌 — 실행 블록이 아닙니다) 기존 호출을 R3 로 감싸는 변경의 모양\n"
        "# 변경 전\n"
        "res = client.chat.completions.create(model=deployment, messages=messages, max_tokens=800)\n"
        "\n"
        "# 변경 후 — 호출을 with call_log(…) 로 감싸고, 응답에서 기록할 값을 rec 에 채운다\n"
        "with call_log(deployment=deployment, job_id=job_id, max_tokens=800, stream=False, read_timeout_s=READ_TIMEOUT) as rec:\n"
        "    raw = client.chat.completions.with_raw_response.create(\n"
        "        model=deployment, messages=messages, max_tokens=800,\n"
        "        extra_headers={\"x-ms-client-request-id\": rec[\"cid\"]})\n"
        "    res, h = raw.parse(), raw.headers\n"
        "    rec.update(status=raw.status_code, apim_request_id=h.get(\"apim-request-id\"), …)   # 전체 항목은 아래 구간 10 의 rec.update(…)"
    )
    b3 = step(
        "b3",
        "데모 앱 — 호출 로그(R3) + Application Insights(R4)",
        "B3 · R3 · R4",
        "소요 약 3분 · 필요한 권한: VM 에서 명령을 실행할 수 있는 권한(Run Command) · 앱 코드 변경은 ‘with 블록으로 감싸기’ + 시작 코드 2줄",
        brief(
            what="R3 의 헬퍼(`call_log`)와 호출부 예시를 그대로 쓰는 **데모 앱**을 서비스로 띄웁니다. 12초 안팎마다 AOAI 를 호출하되 일부러 **짧은 timeout(1초) 호출**과 **없는 배포 이름 호출**을 섞어, 운영에서 보게 될 상태(`ok` · `client_timeout` · `error`)를 모두 만듭니다. Application Insights(R4)는 계측 패키지 + 환경변수로 연결합니다.",
            why="앱이 **호출마다 잰 시간 · 결과 · 요청 ID · 토큰 수 · 동시 호출 수**를 JSON 한 줄로 남기고, 앱의 외부 호출이 Application Insights 에도 기록되어야 C 단계에서 AOAI 기록과 한 건씩 맞춰 볼 수 있습니다.",
            result="앱 로그에 호출마다 JSON 한 줄(`total_ms` · `outcome` · `apim_request_id` …)이 남고, Application Insights 에 `AppDependencies` · `AppTraces` 가 쌓입니다.",
            apply="내 앱에는 **데모 앱을 설치하지 않습니다.** ① `R3_aoai_call_log.py` 를 프로젝트에 추가, ② 기존 AOAI 호출을 `with call_log(…)` 로 감싸기(아래 ‘바뀌는 모양’), ③ 앱 시작 코드에 `configure_azure_monitor(…)` 2줄 + 환경변수 4개를 추가합니다. Python 앱이 아니면 [부록 B](#x2) 를 보세요.",
            caution="**`max_retries=0`(자동 재시도 끔)은 진단용**입니다 — 진단이 끝나면 되돌리세요. 호출 종류를 난수로 섞는 데모 앱이라 **출력 줄은 매번 다릅니다.**",
        )
        + b3_intro
        + details(
            "내 앱에 적용하려면 — 기존 호출이 어떻게 바뀌나 (설명용 발췌)",
            code(apply_snip, cap="변경 전 → 변경 후 (실행 블록 아님)", lang="python", nocopy=True)
            + md("바뀌는 것은 **호출을 `with` 로 감싸고 응답에서 값을 꺼내 `rec` 에 채우는 몇 줄**뿐이고, 호출 결과(`res`)와 예외 동작은 그대로입니다. 호출이 여러 곳이면 그 호출부마다 같은 방식으로 감싸거나, 호출 함수 하나로 모아 한 곳만 감쌉니다."),
            open_=True,
        )
        + details(
            "내 앱으로 가져갈 파일 ① R3_aoai_call_log.py — 호출 로그 헬퍼 전체",
            code(r3_helper, cap="R3_aoai_call_log.py (이 파일을 내 프로젝트에 추가하고 호출부에서 import)", lang="python"),
        )
        + details(
            "내 앱으로 가져갈 설정 ② Application Insights 환경변수 4개 · 시작 코드",
            code(envs, cap="환경변수 4개 (앱 실행 방식에 맞게 전달 — systemd 의 EnvironmentFile · 컨테이너 환경변수 등)", lang="bash")
            + md("앱 시작 코드(가장 먼저 실행되는 곳)에 `from azure.monitor.opentelemetry import configure_azure_monitor` · `configure_azure_monitor(logger_name=\"aoai\")` 와 `logging.getLogger(\"aoai\").setLevel(logging.INFO)` 2줄이 필요합니다(데모 앱 구간 11). 패키지는 `pip install \"azure-monitor-opentelemetry>=1.8.10\"` 로 설치합니다."),
        )
        + b3_walk
        + out(
            """active
{"event": "aoai_call", "cid": "83881d35-…", "inflight": 1, "deployment": "gpt41mini", "job_id": "job-6", "max_tokens": 800, "stream": false, "read_timeout_s": 60.0, "status": 200, "request_id": "dad156a2-…", "apim_request_id": "b951a6ab-…", "region": "Korea Central", "prompt_tokens": 16, "completion_tokens": 9, "finish_reason": "stop", "outcome": "ok", "total_ms": 1147}
{"event": "aoai_call", …, "deployment": "no-such-deployment", "outcome": "error", "error": "NotFoundError", "status": 404, "total_ms": 267}
{"event": "aoai_call", …, "read_timeout_s": 1.0, "outcome": "client_timeout", "error": "APITimeoutError", "status": null, "total_ms": 1027}""",
            read="""
            - 첫 줄 **`active`** — 앱 서비스가 실행 중입니다.
            - 호출 종류는 난수로 정해지므로 **여러분의 출력은 이 예와 줄 순서 · 값이 다릅니다**(5줄 안에 404 · timeout 줄이 없을 수도 있습니다 — 몇 분 더 두면 나옵니다).
            - 아래 JSON 줄들이 **호출 한 건 = 한 줄**의 기록입니다. 첫 줄은 정상(`outcome: ok`, `status: 200`, `total_ms: 1147` = 앱이 잰 1.1초). `apim_request_id` 가 C2 의 짝짓기 열쇠입니다.
            - 둘째 줄은 없는 배포 이름 호출(`error` · 404), 셋째 줄은 1초 timeout 호출(`client_timeout` · `status: null` — 응답을 받기 전에 끊어서 상태 코드가 없습니다).
            """,
        )
        + call(
            "info",
            "이 단계에서 확인되는 것",
            """
            - JSON 한 줄에 **지연(`total_ms`) · 결과(`outcome`) · 요청 ID · 토큰 수 · 동시 호출 수(`inflight`)** 가 모두 남습니다. 프롬프트 · 응답 본문은 없습니다.
            - 응답 헤더 `x-request-id` · `apim-request-id` · `x-ms-region` 이 실제로 들어왔습니다.
            - `max_retries=0` 이라 SDK 의 자동 재시도가 꺼져 있어 **시도마다 한 줄**이 남습니다.
            """,
        )
        + details(
            "이 단계에 나오는 ID 5종 — 무엇이 무엇인가",
            table(
                ["이름", "누가 만드나", "어디서 보나", "무엇에 쓰나"],
                [
                    ["`cid`", "앱(R3 가 호출마다 새로 만든 UUID)", "앱 로그 JSON 의 `cid`", "앱 로그 **한 줄의 고유 번호**"],
                    ["`x-ms-client-request-id`", "앱이 **요청 헤더**에 실어 보냄(값 = `cid`)", "—", "서버에 전달되지만, 이 실습의 AOAI 진단 로그에서는 **확인되지 않아** 짝짓기에 쓰지 못했습니다"],
                    ["`x-request-id`", "AOAI 가 **응답 헤더**로 돌려줌", "앱 로그의 `request_id`", "요청 1건을 가리키는 번호 — 지원 문의 때 알려 주는 용도"],
                    ["`apim-request-id`", "AOAI 가 응답 헤더로 돌려줌", "앱 로그의 `apim_request_id`", "AOAI 진단 로그의 `CorrelationId` 와 **같은 값** → 한 건씩 짝짓는 열쇠"],
                    ["`CorrelationId`", "AOAI 진단 로그의 열", "`AzureDiagnostics` 테이블", "위 `apim-request-id` 와 같은 값(C2)"],
                ],
            ),
            open_=True,
        )
        + details(
            "앱이 보내는 텔레메트리 · 샘플링 주의",
            md("`OTEL_TRACES_SAMPLER=always_on` 은 **진단 기간에 꼭 필요한 설정**입니다. 최근 버전의 기본값은 초당 5 트레이스(rate-limited)라서 호출이 많으면 dependency 가 빠집니다. 로그(`AppTraces`)는 샘플링되지 않습니다. 샘플링 중에는 건수를 `count()` 가 아니라 `sum(ItemCount)` 로 세세요."),
        ),
        scope="apply",
    )

    # ───────── B4 · R7
    probe = snipfile("R7_aoai_probe.sh")
    snap = snipfile("R7_aoai_snapshot.sh")
    penv = snipfile("R7_aoai-probe.env.sample")
    psvc = snipfile("R7_aoai-probe.service")
    ptim = snipfile("R7_aoai-probe.timer")
    pins = snipfile("R7_install.sh")
    lab_http = open(VMF + "lab-http.service", encoding="utf-8").read()
    script_b4 = (
        "set -e\ninstall -d /tmp/r7 /opt/lab-www\ncd /tmp/r7\n"
        + vmfile("R7_aoai_probe.sh", probe)
        + vmfile("R7_aoai_snapshot.sh", snap)
        + vmfile("R7_aoai-probe.env.sample", penv)
        + vmfile("R7_aoai-probe.service", psvc)
        + vmfile("R7_aoai-probe.timer", ptim)
        + vmfile("R7_install.sh", pins)
        + "chmod +x R7_*.sh\n"
        + "# 실습용 '로컬 앱 URL' (운영에서는 앱의 실제 URL 을 APP_URLS 에 넣습니다)\n"
        + vmfile("/etc/systemd/system/lab-http.service", lab_http)
        + """echo ok > /opt/lab-www/health
systemctl daemon-reload && systemctl enable --now lab-http.service
# ---- 설치 → 설정 → 시작 순서 ----
bash R7_install.sh                          # 설치 + 1분 타이머 등록
# ('sudo vi /etc/aoai-probe.env' 대신 비대화식으로 값 입력 — AOAI_API_KEY 를 비워 관리 ID 로 인증)
cat > /etc/aoai-probe.env <<EOF
AOAI_ENDPOINT="https://$AOAI_HOST"
AOAI_DEPLOYMENT="$DEP"
AOAI_API_KEY=""
APP_URLS="http://127.0.0.1:11202/health"
SLOW_MS=8000
PROBE_ROLE=vm-inside
EOF
chmod 600 /etc/aoai-probe.env
systemctl start aoai-probe.service          # 1회 실행 → JSON 줄 확인
sleep 2
journalctl -u aoai-probe -n 6 --no-pager -o cat | cut -c1-300
systemctl list-timers aoai-probe.timer --no-pager | head -3
"""
    )
    b4_walk = walk(
        "vmrun AOAI_HOST=$AOAI_HOST DEP=$DEP <<'VMEOF'\n" + script_b4 + "VMEOF",
        [
            (
                "vmrun AOAI_HOST",
                "VM 안에서 실행 시작 · 작업 폴더",
                "`vmrun` 으로 `VMEOF` 까지를 VM 안에서 실행합니다. `/tmp/r7` 은 파일을 만들어 둘 **작업 폴더**, `/opt/lab-www` 는 실습용 로컬 웹 폴더입니다. 스크립트 파일들은 모두 `cat > 파일 <<'EOF' … EOF` 로 만들고, 마지막에 `R7_install.sh` 가 제자리에 설치합니다.",
            ),
            (
                "cat > R7_aoai_probe.sh",
                "probe 스크립트 ① 시작 — 설정 읽기",
                """
                **합성 probe**(`R7_aoai_probe.sh`) 파일입니다. 사용자 요청이 없어도 **1분마다 AOAI 와 앱 URL 을 직접 호출**해서 구간별 시간을 JSON 한 줄로 남기는 작은 셸 스크립트입니다. (‘합성’ = 사람이 쓰는 대신 **일부러 만든 호출**이라는 뜻입니다.)
                * `#!/bin/bash` — 이 파일을 bash 로 실행하라는 표시(첫 줄)
                * `set -u` — 정의하지 않은 변수를 쓰면 오류(오타 방지)
                * `. "${PROBE_ENV:-/etc/aoai-probe.env}"` — 설정 파일(`/etc/aoai-probe.env`)을 **읽어 들임**(`.` 은 `source` 와 같음). `${변수:-기본값}` 은 ‘변수가 비어 있으면 기본값’이라는 뜻입니다.
                * `ROLE` · `SLOW_MS` · `API_VER` — 설정에 없으면 쓰는 **기본값**(역할 이름 `vm-inside` · ‘느림’ 기준 8000ms · API 버전)
                """,
            ),
            (
                "emit() {",
                "probe 스크립트 ② emit() — curl 시간값을 구간별로 계산해 기록",
                """
                curl 이 알려 주는 시간값은 **누적**(DNS 끝 · 연결 끝 · TLS 끝 …)이라서, **차이를 계산해 구간별 시간**으로 바꿔 JSON 한 줄로 만드는 함수입니다. 함수 이름 `emit` 은 ‘내보내다’라는 뜻입니다. 인자는 `$1` = 대상 이름, `$2` = curl 종료 코드, `$3` = curl 이 출력한 시간값 문자열입니다.
                * `read … <<<"$3"` — `|` 로 이어 둔 curl 출력을 `dns tcp tls ttfb total code ip conns` 변수 8개로 쪼갭니다(`IFS="|"` 가 구분 문자).
                * `awk` — 줄 · 숫자를 계산하는 도구입니다. `-v 이름=값` 으로 셸 변수를 넘기고, `BEGIN{ … }` 안에서 계산한 뒤 `printf` 로 JSON 을 출력합니다.
                * 계산 규칙: **`tcp_ms` = 연결 − DNS · `tls_ms` = TLS − 연결 · `wait_ms` = 첫 응답 바이트 − TLS 완료**(= 요청을 보낸 뒤 첫 응답이 올 때까지, 서버 처리 + 왕복) · `dns_ms` 는 DNS 조회 시간 · `total_ms` 는 전체. 음수가 나오지 않도록 `(c > d) ? c - d : 0` 처럼 0 으로 막습니다. 초 단위 값에 1000 을 곱해 **밀리초 정수**로 바꿉니다.
                * 출력 JSON: `event` · `role` · `target` · `rc`(curl 종료 코드) · `code`(HTTP 코드) · `dns_ms` · `tcp_ms` · `tls_ms` · `wait_ms` · `total_ms` · `ip`(접속한 IP) · `new_conns`(새로 맺은 연결 수)
                * `echo "$line"` — 화면(표준출력)에 출력, `logger -t aoai-probe -p local5.info` — **syslog(local5)로도 기록** → 에이전트(B2)가 `Syslog` 테이블로 수집
                * `TOTAL_MS` — 아래 ‘느림 판정’에 쓰려고 전체 시간(ms)을 저장

                **계산 예** — curl 출력이 `0.004|0.005|0.024|0.667|0.681|200|20.41.5.9|1` 이면: DNS 0.004s → `dns_ms` 4 · 연결 0.005 − 0.004 → `tcp_ms` 1 · TLS 0.024 − 0.005 → `tls_ms` 19 · 첫 바이트 0.667 − 0.024 → `wait_ms` 643 · 전체 0.681 → `total_ms` 681. 곱셈 뒤 정수로 자르므로 ±1ms 차이는 생길 수 있습니다.

                **읽을 때 주의** — `rc` 는 **curl 이 통신을 끝냈는지**만 말합니다. 서버가 HTTP 401 · 429 · 5xx 로 답해도 `rc` 는 0 이므로 성공 여부는 **`code`** 도 함께 보세요. 연결이 실패하거나 시간 초과가 난 호출은 단계별 값이 0 이어서 `wait_ms` 등이 믿을 수 없는 값(0 또는 전체−기준 시간)으로 찍힙니다 — 그런 행은 `rc` 와 `total_ms` 를 우선 보세요.
                """,
            ),
            (
                "# 인증:",
                "probe 스크립트 ③ 인증 — 키가 없으면 관리 ID",
                """
                `AUTH` 는 curl 에 줄 **인증 헤더**입니다.
                * `AOAI_API_KEY` 가 설정에 있으면 `api-key` 헤더를 씁니다.
                * **비어 있으면(권장)** VM 의 **관리 ID 토큰**을 받아 `Authorization: Bearer …` 로 씁니다. `169.254.169.254` 는 Azure VM 안에서만 접근되는 **인스턴스 메타데이터 서비스(IMDS)** 주소이고, 여기서 `https://cognitiveservices.azure.com` 용 접근 토큰을 받습니다. 이것이 A4 에서 준 `Cognitive Services OpenAI User` 역할이 쓰이는 곳입니다. 코드로는 `AUTH=( … )` 가 curl 에 넘길 헤더를 담는 bash 배열이고, 안쪽 `$(curl … 169.254.169.254 …)` 가 토큰이 든 JSON 을 받아 오며, 끝의 `sed` 가 그 JSON 에서 `access_token` 값만 잘라 냅니다(jq 없이).
                """,
            ),
            (
                "slow=0",
                "probe 스크립트 ④ 호출 준비 — 측정 항목과 주소",
                """
                * `slow=0` — ‘느림 판정’ 깃발(아래에서 켜짐)
                * `WF` — curl 의 `-w`(write-out)에 줄 **측정 항목 8개**: `time_namelookup`(DNS) · `time_connect`(TCP) · `time_appconnect`(TLS) · `time_starttransfer`(첫 바이트) · `time_total` · `http_code` · `remote_ip` · `num_connects`. `|` 로 이어 붙여 `emit()` 이 쪼갭니다(`WF+=` 는 문자열 뒤에 덧붙이기).
                * `BASE` · `URL` — 호출 주소 `https://<리소스>.openai.azure.com/openai/deployments/<배포>/chat/completions?api-version=…` (`${AOAI_ENDPOINT%/}` 는 주소 끝의 `/` 를 떼는 표기)
                """,
            ),
            (
                "out=$(curl -sS --http1.1",
                "probe 스크립트 ⑤ AOAI 소형 호출 + 기록 + 느림 판정",
                """
                * `curl -sS` — 진행 표시는 끄되 오류는 표시 · `-X POST "$URL"` — 채팅 API 로 POST 요청
                * `-o /dev/null` — 응답 본문은 버림
                * `--max-time 60` — 최대 60초(설정 `PROBE_TIMEOUT` 으로 바꿈)
                * **`--http1.1`** — HTTP/1.1 로 고정합니다. 이 실습의 curl · RHEL 조합에서는 HTTP/2 일 때 curl 이 첫 바이트 시간을 연결 직후로 기록해 `wait_ms` 가 항상 0 으로 찍혔기 때문입니다(다른 환경에서도 같은지는 확인하지 않았습니다). 앱의 Python SDK 도 HTTP/1.1 입니다.
                * `-H "x-ms-client-request-id: probe-<시각>"` — probe 호출임을 알아볼 수 있는 ID
                * `-d '{"messages":[{"role":"user","content":"ping"}],"max_tokens":1}'` — **가장 작은 호출**: 질문 `ping`, 출력 토큰 **1개** → 모델 처리 부하를 최소로 하고 연결 · 대기 시간 위주로 잽니다.
                * `rc=$?` — curl 종료 코드(0 = 통신 완료 · 28 = 시간 초과 · 6 = DNS 실패 등). HTTP 오류 코드(429 등)는 `rc` 가 아니라 `code` 에 나옵니다.
                * `emit aoai …` 로 JSON 한 줄을 남기고, **`rc≠0` 이거나 `total ≥ SLOW_MS`(8초)면 `slow=1`** 로 표시합니다. 즉 **HTTP 오류 코드만으로는 ‘느림’이 아니며**, 통신이 실패했거나 8초 이상 걸렸을 때만 스냅샷 조건이 됩니다.
                """,
            ),
            (
                "# (2) VM 로컬 앱 URL",
                "probe 스크립트 ⑥ 로컬 앱 URL 도 같은 방식으로",
                "설정의 `APP_URLS` 에 적은 **VM 안 앱 주소**를 같은 방식으로 호출해 시간을 잽니다. AOAI 가 느릴 때 **같은 VM 의 앱 자체도 느린지**를 비교하는 대조군입니다. `${u##*:}` 는 URL 에서 마지막 `:` 뒤(포트와 경로)만 떼어 `app:11202/health` 같은 이름을 만듭니다.",
            ),
            (
                "# 느리거나 실패했으면",
                "probe 스크립트 ⑦ 느리면 VM 상태 스냅샷 저장",
                """
                느리거나 실패한 호출이 있으면 **그 순간의 VM 상태 스냅샷**을 남깁니다. 단, **5분에 한 번만**(`/tmp/.aoai_snap` 파일의 수정 시각으로 판단 — `find … -mmin -5`).
                * `systemd-run --quiet --no-block --collect "$SNAP"` — 스냅샷을 **별도의 임시 서비스로 실행**합니다. 이유: probe 는 1회 실행 후 끝나는 서비스(oneshot)라서, 그 안에서 백그라운드로 띄운 스냅샷이 **서비스 종료와 함께 중간에 잘리는** 문제가 있었기 때문입니다.
                * `|| { "$SNAP" >/dev/null 2>&1 & }` — `systemd-run` 이 안 될 때 쓰는 **차선책**(`&` = 백그라운드 실행)입니다. 이 경우에는 위의 잘림 문제가 다시 생길 수 있습니다(이 실습에서는 `systemd-run` 이 동작했습니다).
                """,
            ),
            (
                "cat > R7_aoai_snapshot.sh",
                "스냅샷 스크립트 ① 시작 · 저장 위치",
                "**스냅샷**(`R7_aoai_snapshot.sh`)은 **읽기 전용 명령만** 써서 VM 상태를 한 파일로 저장합니다. `DIR` 은 `/var/log/aoai-probe`, 파일 이름은 `snap-<UTC 시각>.txt` 입니다.",
            ),
            (
                "{",
                "스냅샷 스크립트 ② 무엇을 수집하나 — 10개 구역",
                """
                `{ … } > "$OUT"` 안의 명령 출력이 모두 파일 하나에 모입니다. 각 구역이 가리키는 것:
                - **부하/메모리**(`uptime` · `free -m`) · **`vmstat 1 3`**(`r` = 실행을 기다리는 프로세스 수, `wa` = 디스크 입출력 대기 비율)
                - **CPU 상위 프로세스**(`top`) · **디스크 I/O**(`iostat`, `sysstat` 이 있을 때만)
                - **소켓 요약**(`ss -s`) · **443 연결 상세**(`ss -tin` — 재전송 타이머 rto · 왕복 시간 rtt · 혼잡 창 cwnd)
                - **TCP 카운터**(`nstat` — 재전송 · 타임아웃 · 연결 실패 누적 횟수)
                - **systemd 타이머**와 **최근 5분 cron 로그**(그 순간 도는 작업)
                """,
            ),
            (
                "# 요약 1줄",
                "스냅샷 스크립트 ③ 요약 1줄을 syslog 로 + 오래된 파일 정리",
                """
                파일은 VM 에만 남으므로, 핵심 수치를 **JSON 한 줄로 요약해 syslog(local5)로 보냅니다.** 그러면 `Syslog` 테이블에서 시각으로 바로 대조할 수 있습니다.
                * `read -r R WA < <(vmstat 1 2 | tail -1 | awk '{print $1, $16}')` — `vmstat` 마지막 줄에서 **1번째 열(`r` = 실행 대기 프로세스 수)과 16번째 열(`wa` = I/O 대기 %)** 만 꺼내 변수 `R` · `WA` 에 담습니다. `< <( … )` 는 명령 출력을 파일처럼 읽게 하는 셸 문법입니다.
                * `${R:-0}` — 값이 비어 있으면 0 을 씁니다(JSON 이 깨지지 않게).
                * 요약 항목: `runq`(실행 대기 프로세스 수) · `iowait_pct`(I/O 대기 %) · `est443`(443 포트 연결 수) · `tcp_retrans_total`(TCP 재전송 **누적** 횟수) · `load1`(1분 평균 부하)
                * 마지막 `find … -mtime +7 -delete` — **7일 지난 스냅샷은 삭제**

                **경험칙으로 읽는 법**(대략적인 어림값이며 절대 기준은 아닙니다): `runq` 가 **CPU 코어 수보다 계속 크면** CPU 가 모자란 것, `iowait_pct` 가 **수십 %** 면 디스크 대기, `tcp_retrans_total` 은 누적값이라 **스냅샷 사이의 증가분**이 늘었는지를 봅니다.
                """,
            ),
            (
                "cat > R7_aoai-probe.env.sample",
                "probe 설정 파일 샘플",
                """
                probe 가 읽는 **설정**입니다(`/etc/aoai-probe.env` 로 설치되며 권한 600).
                * `AOAI_ENDPOINT` · `AOAI_DEPLOYMENT` — **앱이 쓰는 것과 같은** 엔드포인트 · 배포 이름
                * `AOAI_API_KEY=""` — **비워 두면 관리 ID 사용**(권장)
                * `APP_URLS` — 함께 점검할 **로컬 앱 주소**(공백으로 구분)
                * `SLOW_MS=8000` — ‘느림’ 기준(밀리초)
                * `PROBE_ROLE` — VM 안이면 `vm-inside`, **VM 밖에 둔 probe 는 `vm-outside`**. 안과 밖이 모두 느리면 AOAI 쪽, 안만 느리면 VM → AOAI 경로가 의심됩니다(경향을 보는 규칙이며 단정은 아닙니다).
                """,
            ),
            (
                "cat > R7_aoai-probe.service",
                "systemd 서비스 — 한 번 실행하고 끝나는 작업",
                "`Type=oneshot` 은 **한 번 실행하고 끝나는** 서비스라는 뜻이고, `ExecStart` 가 probe 스크립트를 실행합니다. 반복은 아래 타이머가 맡습니다.",
            ),
            (
                "cat > R7_aoai-probe.timer",
                "systemd 타이머 — 매분 정각에 실행",
                """
                * `OnCalendar=*-*-* *:*:00` — **매일 · 매시 · 매분 0초**에 실행 = **1분마다**
                * `AccuracySec=1s` — systemd 는 기본적으로 비슷한 시각의 타이머를 **묶어서 최대 1분까지 늦춰 실행**할 수 있는데, 이 **허용 오차를 1초로 줄입니다.**
                * `WantedBy=timers.target` — 타이머 목록에 등록되어 부팅 시 자동 시작
                """,
            ),
            (
                "cat > R7_install.sh",
                "설치 스크립트 — 파일을 제자리에 놓고 타이머 켜기",
                """
                * `install -d …` — 폴더 `/opt/aoai-probe`(프로그램) · `/var/log/aoai-probe`(스냅샷) 생성
                * `install -m 0755 … /opt/aoai-probe/…` — 스크립트를 **실행 가능**하게 설치
                * `[ -f /etc/aoai-probe.env ] || install -m 0600 …` — 설정 파일이 **없을 때만** 샘플을 설치(이미 값을 채운 설정을 덮어쓰지 않음)
                * `.service` · `.timer` 를 `/etc/systemd/system/` 에 설치 → `daemon-reload` → **`enable --now aoai-probe.timer`**(부팅 시 자동 + 지금 시작) → 타이머 목록 출력
                """,
            ),
            (
                "chmod +x R7_*.sh",
                "실습용 로컬 앱 URL — 대조군",
                """
                `chmod +x` 로 스크립트에 실행 권한을 줍니다. 그다음 **실습용 ‘앱’ 역할**을 할 아주 작은 웹 서버(`lab-http.service`, 포트 11202, `127.0.0.1` 에만 응답)를 서비스로 만들고 `health` 파일(`ok`)을 둡니다. 실제 환경에서는 **내 앱의 실제 URL** 을 `APP_URLS` 에 넣으므로 이 부분은 필요 없습니다.
                """,
            ),
            (
                "bash R7_install.sh",
                "설치 실행 · 설정 채우기 · 1회 실행해 확인",
                """
                * `bash R7_install.sh` — 위의 설치 스크립트 실행(타이머 등록)
                * `cat > /etc/aoai-probe.env <<EOF …` — 설정 파일을 **값을 채워** 만듭니다. 따옴표 없는 `EOF` 이므로 `$AOAI_HOST` · `$DEP` 가 실제 값으로 바뀝니다. **`AOAI_API_KEY` 는 비워서 관리 ID 로 인증**합니다.
                * `chmod 600` — 설정 파일을 소유자만 읽게
                * `systemctl start aoai-probe.service` — **1회 즉시 실행** → 2초 뒤 `journalctl` 로 결과 JSON 줄 확인 → `list-timers` 로 다음 실행 예정 확인
                """,
            ),
        ],
        cap="probe 설치 (164줄 — ‘전체 복사’ 한 번이면 됩니다)",
        run="B4",
        tags={1: "lab", 2: "apply", 3: "apply", 4: "apply", 5: "apply", 6: "apply", 7: "apply", 8: "apply", 9: "apply", 10: "apply", 11: "apply", 12: "apply", 13: "apply", 14: "apply", 15: "apply", 16: "lab", 17: "apply"},
    )
    b4 = step(
        "b4",
        "합성 probe — DNS · TCP · TLS · 대기 시간 분리",
        "B4 · R7",
        "소요 약 2분 · 필요한 권한: VM 에서 명령 실행(Run Command) · AOAI 호출 역할은 A4 에서 부여 · 키 없이 관리 ID 로 인증",
        brief(
            what="같은 소형 AOAI 호출(`max_tokens=1`)과 로컬 앱 URL 을 **1분마다** 호출해 DNS · TCP · TLS · 서버 대기 시간을 따로 JSON 한 줄로 남기고, syslog(local5) → Azure Monitor Agent(B2) → `Syslog` 테이블로 수집합니다. 느리거나 **통신이 실패**하면(HTTP 오류 코드는 제외 — 아래 설명) VM 상태 **스냅샷**을 5분에 한 번 저장합니다.",
            why="앱 로그에는 ‘느렸다’만 남고 **어느 구간(DNS · 연결 · 서버 대기)** 인지는 알 수 없습니다. probe 는 **평소 기준선**을 만들어 주고, 구간을 쪼개 보여 줍니다. 사용자 요청이 없을 때도 매분 돌기 때문에 ‘그 시각에 정말 느렸는지’를 판단할 수 있습니다.",
            result="`aoai-probe` 서비스가 1분 타이머로 돌며 JSON 줄을 남깁니다(`journalctl` 과 `Syslog` 테이블).",
            apply="내 VM 에 설치하되 **전체를 그대로 붙이지 말고** 구간 2~15(파일들)와 구간 17(설치 · 설정)만 가져가세요(구간 1 · 16 은 실습용 웹 서버 `lab-http` 준비). 구간 17 의 `AOAI_ENDPOINT` · `AOAI_DEPLOYMENT` · `APP_URLS` 는 **앱의 실제 값**으로 바꿉니다.",
        )
        + b4_walk
        + out(
            """{"event":"aoai_probe","role":"vm-inside","target":"aoai","rc":0,"code":"200","dns_ms":4,"tcp_ms":1,"tls_ms":19,"wait_ms":643,"total_ms":681,"ip":"20.214.130.66","new_conns":1}
{"event":"aoai_probe","role":"vm-inside","target":"app:11202/health","rc":0,"code":"200","dns_ms":0,"tcp_ms":0,"tls_ms":0,"wait_ms":1,"total_ms":1,"ip":"127.0.0.1","new_conns":1}""",
            read="""
            - 첫 줄이 **AOAI 호출**: DNS 4ms + TCP 1ms + TLS 19ms 로 **연결은 24ms 안에 끝났고**, 대부분은 `wait_ms` 643ms(= AOAI 가 처리하고 첫 응답을 줄 때까지)입니다. 전체 681ms. 이 정도가 **평소 기준선**입니다.
            - 둘째 줄은 **로컬 앱 URL**(127.0.0.1)로 거의 0ms. AOAI 가 느릴 때도 이 값이 정상이면 VM 자체는 문제가 아니라는 뜻입니다.
            - `rc: 0` · `code: "200"` 이면 성공입니다. (`rc` 는 curl 이 통신을 끝냈는지만 뜻하므로 서버의 401 · 429 · 5xx 도 `rc: 0` 입니다 — `code` 를 함께 보세요.)
            """,
        )
        + call(
            "info",
            "probe 도 AOAI 호출입니다",
            """
            probe 는 **분당 1회**, 토큰 1개짜리 소형 호출을 AOAI 에 보냅니다. 비용과 할당량(분당 요청 수)에 미치는 영향은 아주 작지만 0 은 아닙니다. 또 **AOAI 쪽 로그(R1)에서도 probe 호출이 앱 호출과 같은 1건으로 기록**되므로, AOAI 호출 수를 셀 때 섞여 들어갑니다.
            """,
        )
        + call(
            "info",
            "VM 밖 probe — 이 실습에서는 만들지 않습니다",
            """
            ‘VM 안은 느린데 밖은 정상’ 같은 비교를 하려면 **VM 밖의 다른 서버**에도 같은 probe 를 둡니다(이 실습은 만들지 않았습니다). ① 그 서버에 `R7_aoai_probe.sh` · `R7_install.sh` 등을 복사 ② `/etc/aoai-probe.env` 에 `PROBE_ROLE=vm-outside` 를 넣고 설치 ③ 그 서버의 syslog 가 **같은 워크스페이스로 올라오도록** B2 와 같이 수집 에이전트 · 규칙을 연결합니다. 그러면 C4 의 probe 쿼리 `role` 열(`vm-inside` / `vm-outside`)로 안 · 밖을 비교할 수 있습니다.
            """,
        )
        + details(
            "스냅샷이 실제로 만들어지는지 확인 (선택)",
            walk(
                """vmrun <<'VMEOF'
sed -i 's/^SLOW_MS=.*/SLOW_MS=1/' /etc/aoai-probe.env          # 일부러 '느림' 으로 판정
rm -f /tmp/.aoai_snap; systemctl start aoai-probe.service; sleep 14
ls -l /var/log/aoai-probe/ | tail -2
f=$(ls -t /var/log/aoai-probe/snap-*.txt | head -1); echo "lines: $(wc -l < $f)  sections: $(grep -c '^== ' $f)"
journalctl -t aoai-snap --since "-1 min" -o cat --no-pager | cut -c1-240
sed -i 's/^SLOW_MS=.*/SLOW_MS=8000/' /etc/aoai-probe.env         # 원래대로
VMEOF""",
                [
                    (
                        "vmrun <<",
                        "느림 기준을 1ms 로 낮춰 스냅샷을 강제로 만들어 보기",
                        """
                        * `sed -i 's/^SLOW_MS=.*/SLOW_MS=1/' …` — 설정의 느림 기준을 **1ms** 로 바꿔, 모든 호출이 ‘느림’으로 판정되게 합니다.
                        * `rm -f /tmp/.aoai_snap` — ‘5분에 한 번’ 제한 파일을 지워 즉시 만들 수 있게 함 → probe 를 1회 실행 → 14초 대기
                        * `ls -l …` — 스냅샷 파일이 생겼는지
                        * `wc -l` · `grep -c '^== '` — 파일의 **줄 수와 구역(`== …`) 수**
                        * `journalctl -t aoai-snap` — 요약 JSON 줄(syslog)
                        * 마지막 `sed` 로 **기준을 8000ms 로 되돌립니다.**
                        """,
                    )
                ],
                cap="스냅샷 시험",
                run="B4",
            )
            + out(
                """-rw-r--r--. 1 root root 8628 …  snap-20261023T114408Z.txt
lines: 79  sections: 10
{"event":"aoai_snapshot","file":"snap-….txt","load1":"2.57","runq":0,"iowait_pct":0,"est443":8,"tcp_retrans_total":8}""",
                read="`snap-….txt` 파일이 생겼고(약 79줄, 10개 구역), 요약 JSON 에 `load1` · `runq` · `iowait_pct` · `est443` · `tcp_retrans_total` 이 있으면 정상입니다.",
            )
            + code(
                "vmrun <<'VMEOF'\nhead -40 $(ls -t /var/log/aoai-probe/snap-*.txt | head -1)\nVMEOF",
                cap="(확인) 스냅샷 파일 앞부분 열어 보기 — 확인용 명령 · 실행 블록 아님",
            )
            + md("`== ` 로 시작하는 줄이 구역 제목입니다. 지연이 난 시각의 스냅샷에서 **평소와 다른 구역**(CPU 상위 프로세스 · TCP 재전송 카운터 · 최근 cron 로그 등)을 찾으세요."),
        ),
        scope="apply",
    )

    return section(
        "b",
        "B · 로그 켜기",
        "R1 · R5 · R3/R4 · R7 · R2 · R8 · R6 순서 — 데이터가 쌓이는 시간을 벌기 위해 R 번호 순서와 다릅니다",
        b1 + b2 + b3 + b4 + part_b2.build(),
    )
