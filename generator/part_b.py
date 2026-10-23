# -*- coding: utf-8 -*-
# B · 로그 켜기 (R1 R5 R3·R4 R7 R2 R8 R6)
from lib import *


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
        "코드·재배포 없음 · 소요 약 1분 · 권한: Monitoring Contributor",
        "<p>AOAI 가 서비스 쪽에서 잰 <b>요청별 처리 시간(DurationMs)과 상태 코드</b>를 Log Analytics 로 보냅니다. "
        "<code>RequestResponse</code>(요청 로그) · <code>Audit</code>(관리 이벤트) · <code>AllMetrics</code>(메트릭)만 켭니다.</p>"
        + code(snip("R1_aoai_diagnostic_settings.sh", "diag"), cap="22장 R1 스니펫 그대로", run="B1")
        + out("""Name               ResourceGroup  WorkspaceId
-----------------  -------------  ---------------------------------------------------------------
diag-aoai-latency  rg-lablog-…     /subscriptions/…/workspaces/law-lablog-…""", label="예상 결과 (생성된 설정의 JSON 이 먼저 출력되고, 마지막에 이 목록)")
        + call(
            "info",
            "로그는 바로 보이지 않습니다",
            "<p>실측(두 번 반복): <b>진단 설정 후 약 20~26분이 지나서야 AOAI 요청이 기록되기 시작</b>했고, 그 전에 한 호출은 로그에 남지 않았습니다(나중에 채워지지 않음). "
            "기록이 시작된 뒤에는 평균 약 2분 뒤에 조회됩니다. 그래서 <b>B1 을 가장 먼저</b> 하고 약 30분 뒤에 확인하며, 기다리는 동안 B2~B7 을 진행하세요. 확인은 C1 에서 합니다.</p>",
        ),
    )

    # ───────── B2 · R5
    dcr = snipfile("R5_dcr_linux.json")
    b2 = step(
        "b2",
        "VM 에이전트(Azure Monitor Agent) + 수집 규칙(DCR)",
        "B2 · R5",
        "소요 약 3분 · 권한: Monitoring Contributor",
        "<p>VM 의 CPU·메모리·디스크·네트워크 <b>성능 카운터 12개</b>(60초 간격)와 <b>cron·local5 syslog</b> 만 수집하는 규칙을 만들어 VM 에 연결합니다. "
        "cron 로그는 정각·30분에 어떤 작업이 도는지 찾기 위한 것이고, local5 는 R7 probe 와 스냅샷이 쓰는 로그 채널입니다.</p>"
        + code("cat > R5_dcr_linux.json <<'EOF'\n" + dcr + "\nEOF", cap="① 수집 규칙 파일 만들기", run="B2")
        + code(snip("R5_vm_ama_dcr.sh", "ama"), cap="② 에이전트 설치 + 수집 규칙 연결 (22장 R5 스니펫 그대로)", run="B2")
        + out("""{ "name": "AzureMonitorLinuxAgent", "provisioningState": "Succeeded", "typeHandlerVersion": "1.4x", … }
{ "name": "assoc-vm-lablog-rhel", "type": "Microsoft.Insights/dataCollectionRuleAssociations", … }""", label="예상 결과 (확장 · 규칙 연결 JSON)")
        + call(
            "info",
            "확인은 약 10분 뒤",
            "<p>연결 후 <b>약 5~10분</b>이면 <code>Heartbeat</code> · <code>Perf</code> · <code>Syslog</code> 가 들어옵니다(C1 에서 확인). "
            "카운터 이름은 Linux 형식(<code>Logical Disk</code> 는 공백 포함)을 지켜야 합니다.</p>",
        ),
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
# R4 ① 환경변수 파일 설치 + 연결 문자열 입력 (22장의 'vi' 대신 sed)
install -D -m 0600 /tmp/R4_telemetry.env.sample /etc/report-agent/telemetry.env
CS=$(printf %s "$CS_B64" | base64 -d)
sed -i "s#^APPLICATIONINSIGHTS_CONNECTION_STRING=.*#APPLICATIONINSIGHTS_CONNECTION_STRING=\\"$CS\\"#" /etc/report-agent/telemetry.env
# R4 ③ systemd 에 환경변수 파일 연결 (22장의 'systemctl edit' 와 같은 결과의 드롭인 파일)
install -d /etc/systemd/system/report-agent.service.d
printf '[Service]\\nEnvironmentFile=/etc/report-agent/telemetry.env\\n' > /etc/systemd/system/report-agent.service.d/telemetry.conf
systemctl daemon-reload
systemctl enable --now report-agent
sleep 25
systemctl is-active report-agent
journalctl -u report-agent -n 5 --no-pager -o cat | cut -c1-330
"""
    )
    b3 = step(
        "b3",
        "데모 앱 — 호출 로그(R3) + Application Insights(R4)",
        "B3 · R3 · R4",
        "소요 약 3분 · 앱 코드 변경은 ‘with 블록으로 감싸기’ 한 곳",
        "<p>22장의 R3 헬퍼(<code>call_log</code>)와 호출부 예시를 그대로 쓰는 <b>데모 앱</b>을 systemd 서비스로 띄웁니다. 12초 안팎마다 AOAI 를 호출하면서 일부러 "
        "<b>짧은 timeout(1초)</b> 호출과 <b>없는 배포 이름</b> 호출을 섞어, 운영에서 보게 될 상태(ok · client_timeout · error)를 모두 만듭니다. "
        "Application Insights(R4)는 <code>azure-monitor-opentelemetry</code> 자동 계측 + 환경변수 파일로 연결합니다.</p>"
        + code(
            """KEY=$(az cognitiveservices account keys list -g $RG -n $AOAI --query key1 -o tsv)
CS=$(az monitor app-insights component show -a $APPI -g $RG --query connectionString -o tsv)
vmrun AOAI_HOST=$AOAI_HOST DEP=$DEP AOAI_KEY=$KEY CS_B64="$(printf %s "$CS" | base64 | tr -d '\\n')" <<'VMEOF'
""" + script_b3 + "VMEOF",
            cap="앱 파일 설치 · 환경변수 · systemd 서비스 시작 (긴 스크립트 — 복사 버튼 사용)",
            run="B3",
        )
        + out("""active
{"event": "aoai_call", "cid": "83881d35-…", "inflight": 1, "deployment": "gpt41mini", "job_id": "job-6", "max_tokens": 800, "stream": false, "read_timeout_s": 60.0, "status": 200, "request_id": "dad156a2-…", "apim_request_id": "b951a6ab-…", "region": "Korea Central", "prompt_tokens": 16, "completion_tokens": 9, "finish_reason": "stop", "outcome": "ok", "total_ms": 1147}
{"event": "aoai_call", …, "deployment": "no-such-deployment", "outcome": "error", "error": "NotFoundError", "status": 404, "total_ms": 267}
{"event": "aoai_call", …, "read_timeout_s": 1.0, "outcome": "client_timeout", "error": "APITimeoutError", "status": null, "total_ms": 1027}""")
        + call(
            "info",
            "이 단계에서 확인되는 것",
            "<ul><li>JSON 한 줄에 <b>지연(total_ms) · 결과(outcome) · 요청 ID · 토큰 수 · 동시 호출 수(inflight)</b> 가 모두 남습니다. 프롬프트·응답 본문은 없습니다.</li>"
            "<li>응답 헤더 <code>x-request-id</code> · <code>apim-request-id</code> · <code>x-ms-region</code> 이 실제로 들어왔습니다.</li>"
            "<li><code>max_retries=0</code> 이라 SDK 의 자동 재시도가 꺼져 있어 <b>시도마다 한 줄</b>이 남습니다.</li></ul>",
        )
        + details(
            "앱이 보내는 텔레메트리 · 샘플링 주의",
            "<p><code>OTEL_TRACES_SAMPLER=always_on</code> 은 <b>진단 기간에 꼭 필요한 설정</b>입니다. 최근 버전의 기본값은 초당 5 트레이스(rate-limited)라서 호출이 많으면 dependency 가 빠집니다. "
            "로그(AppTraces)는 샘플링되지 않습니다. 샘플링 중에는 건수를 <code>count()</code> 가 아니라 <code>sum(ItemCount)</code> 로 세세요.</p>",
        ),
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
# ---- 22장 R7_usage.sh 의 순서 ----
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
    b4 = step(
        "b4",
        "합성 probe — DNS · TCP · TLS · 대기 시간 분리",
        "B4 · R7",
        "소요 약 2분 · 키 없이 관리 ID 로 인증",
        "<p>같은 소형 AOAI 호출(<code>max_tokens=1</code>)과 로컬 앱 URL 을 <b>1분마다</b> 호출해 DNS · TCP · TLS · 서버 대기 시간을 따로 JSON 한 줄로 남기고, "
        "syslog(local5) → Azure Monitor Agent(B2) → <code>Syslog</code> 테이블로 수집합니다. 느리거나 실패하면 VM 상태 <b>스냅샷</b>을 5분에 한 번 저장합니다.</p>"
        + code("vmrun AOAI_HOST=$AOAI_HOST DEP=$DEP <<'VMEOF'\n" + script_b4 + "VMEOF", cap="probe 설치 (긴 스크립트 — 복사 버튼 사용)", run="B4")
        + out("""{"event":"aoai_probe","role":"vm-inside","target":"aoai","rc":0,"code":"200","dns_ms":4,"tcp_ms":1,"tls_ms":19,"wait_ms":643,"total_ms":681,"ip":"20.214.130.66","new_conns":1}
{"event":"aoai_probe","role":"vm-inside","target":"app:11202/health","rc":0,"code":"200","dns_ms":0,"tcp_ms":0,"tls_ms":0,"wait_ms":1,"total_ms":1,"ip":"127.0.0.1","new_conns":1}""")
        + call(
            "warn",
            "실습에서 찾아 고친 두 가지",
            "<ul><li><b><code>curl --http1.1</code></b> — curl 7.x 는 HTTP/2 에서 첫 바이트 시간(<code>time_starttransfer</code>)을 연결 직후로 기록해 <code>wait_ms</code> 가 항상 0 이 됩니다. "
            "HTTP/1.1 로 고정하면 정상 값(예: 643ms)이 나옵니다. 앱의 Python SDK 도 HTTP/1.1 입니다.</li>"
            "<li><b><code>systemd-run</code> 으로 스냅샷 실행</b> — 타이머가 띄운 oneshot 서비스가 끝나면 그 안에서 백그라운드로 띄운 스냅샷이 함께 종료되어 파일이 중간에 잘렸습니다. "
            "별도 transient 서비스로 실행하도록 바꿨습니다.</li></ul>",
        )
        + details(
            "스냅샷이 실제로 만들어지는지 확인 (선택)",
            code(
                """vmrun <<'VMEOF'
sed -i 's/^SLOW_MS=.*/SLOW_MS=1/' /etc/aoai-probe.env          # 일부러 '느림' 으로 판정
rm -f /tmp/.aoai_snap; systemctl start aoai-probe.service; sleep 14
ls -l /var/log/aoai-probe/ | tail -2
f=$(ls -t /var/log/aoai-probe/snap-*.txt | head -1); echo "lines: $(wc -l < $f)  sections: $(grep -c '^== ' $f)"
journalctl -t aoai-snap --since "-1 min" -o cat --no-pager | cut -c1-240
sed -i 's/^SLOW_MS=.*/SLOW_MS=8000/' /etc/aoai-probe.env         # 원래대로
VMEOF""",
                cap="스냅샷 시험",
                run="B4",
            )
            + out("""-rw-r--r--. 1 root root 8628 …  snap-20261023T114408Z.txt
lines: 79  sections: 10
{"event":"aoai_snapshot","file":"snap-….txt","load1":"2.57","runq":0,"iowait_pct":0,"est443":8,"tcp_retrans_total":8}"""),
        ),
    )

    # ───────── B5 · R2
    b5 = step(
        "b5",
        "AOAI 메트릭 — StatusCode 값 확인",
        "B5 · R2",
        "B3 시작 후 5분 이상 지난 뒤 실행 · 메트릭은 약 7~10분 지연",
        "<p>AOAI 메트릭 <code>AzureOpenAIRequests</code> 를 <code>StatusCode</code> 로 나눠 보면 어떤 상태 코드가 실제로 찍히는지 알 수 있습니다. "
        "R8 의 499 알림을 만들기 전에 값(문자열 ‘499’)을 확인하는 용도입니다.</p>"
        + code(snip("R2_aoai_metrics.sh", "statuscode"), cap="22장 R2 스니펫 그대로", run="B5")
        + out("""Timestamp             Name                   Statuscode    Total
--------------------  ---------------------  ------------  -------
2026-10-23T09:25:00Z  Azure OpenAI Requests  200           0.0
…                                                                     (앱을 켜기 전 시간대는 0)
2026-10-23T10:25:00Z  Azure OpenAI Requests  200           72.0
2026-10-23T10:25:00Z  Azure OpenAI Requests  499           13.0""", label="예상 결과 (최근 24시간이 시간 단위로 나오며, 앱이 호출한 시간대에만 값이 보입니다)")
        + call(
            "info",
            "실측으로 확인한 것",
            "<ul><li>StatusCode 값은 <code>200</code> · <code>499</code> 처럼 <b>숫자 문자열</b>입니다. 앱이 일부러 1초 timeout 으로 끊은 호출이 <b>499</b> 로 집계되었습니다.</li>"
            "<li>없는 배포 이름(404)은 AOAI 지표·로그에 <b>나타나지 않습니다</b> — 앱 로그에서만 보입니다.</li>"
            "<li>이 환경(비스트리밍 · Global Standard)에서 <code>AzureOpenAITTLTInMS</code>(응답 완료 시간)·토큰 수 지표에는 값이 있었고, "
            "<code>TimeToResponse</code> · <code>NormalizedTimeBetweenTokens</code> 계열은 값이 없었습니다.</li></ul>",
        ),
    )

    # ───────── B6 · R8
    b6 = step(
        "b6",
        "알림 4종 + 수신 그룹",
        "B6 · R8",
        "소요 약 2분 · 알림 메일은 A1 의 <code>MAIL</code> 로 갑니다",
        "<p>지연이 난 순간을 놓치지 않도록 <b>메트릭 알림 2개</b>(AOAI 499 · 응답 완료 시간, 1분 평가)와 <b>로그 알림 2개</b>(앱 client_timeout · probe 지연, 5분 평가)를 만듭니다. "
        "로그 알림은 수집 지연만큼 늦게 울리므로 AOAI 쪽은 메트릭 알림이 빠릅니다.</p>"
        + code(snip("R8_alerts.sh", "alerts"), cap="22장 R8 스니펫 그대로 (RG · MAIL · AOAI_ID · LAW 는 A1·A4 에서 정한 값)", run="B6")
        + code(
            """az rest --method get --url "https://management.azure.com/subscriptions/$SUB/providers/Microsoft.AlertsManagement/alerts?api-version=2019-05-05-preview&targetResourceGroup=$RG" \\
  --query "value[].{rule:properties.essentials.alertRule, state:properties.essentials.monitorCondition, sev:properties.essentials.severity, fired:properties.essentials.startDateTime}" -o table""",
            cap="발화한 알림 확인 (앱을 켜고 약 10분 뒤)",
            run="B6",
        )
        + out("""Rule                 State   Sev   Fired
-------------------  ------  ----  ----------------------------
…/aoai-499           Fired   Sev2  2026-10-23T11:25:05Z
…/app-client-timeout Fired   Sev2  2026-10-23T11:28:47Z""")
        + call(
            "warn",
            "알림 메일이 옵니다",
            "<p>실습 중 timeout 호출이 계속 발생하므로 <code>aoai-499</code> 와 <code>app-client-timeout</code> 이 울리고 <code>MAIL</code> 로 알림이 갑니다. "
            "확인이 끝나면 D 단계에서 리소스 그룹을 삭제하세요(또는 <code>az monitor metrics alert update --enabled false</code>).</p>",
        ),
    )

    # ───────── B7 · R6
    cm = snip("R6_network_logs.sh", "cm")
    b7_cm = code(cm, cap="② Connection Monitor — VM → AOAI:443 을 30초마다 (22장 R6 스니펫 그대로)", run="B7")
    b7_flow = code(
        """az storage account create -n $ST -g $RG -l $LOC --sku Standard_LRS --kind StorageV2 --min-tls-version TLS1_2 --allow-blob-public-access false --tags $TAGS -o none
VNET_ID=$(az network vnet show -g $RG -n $VNET --query id -o tsv)
ST_ID=$(az storage account show -g $RG -n $ST --query id -o tsv)
az network watcher flow-log create -l koreacentral -n vnetfl-agent \\
  --vnet "$VNET_ID" --storage-account "$ST_ID" \\
  --traffic-analytics true --workspace $LAW --interval 10 --retention 30""",
        cap="③ (선택) VNet flow log — NSG flow log 는 2025-06-30 이후 신규 생성 불가 (22장 R6 스니펫의 자리 표시자를 실제 ID 로 채움)",
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
    b7 = step(
        "b7",
        "네트워크 경로 로그 — Connection Monitor · VNet flow log · (선택) Azure Firewall",
        "B7 · R6",
        "소요 약 5분 (Firewall 포함 시 약 25분) · 22장에서는 ‘조건부 3단계’",
        "<p>probe(VM 안)가 느리고 probe(VM 밖)가 정상일 때 우선 보는 <b>VM → AOAI 경로</b>의 로그입니다. "
        "Connection Monitor 는 VM 에서 AOAI 443 포트로 <b>TCP 연결 시간(RTT)과 실패율</b>을 30초마다 재고, 방화벽 로그는 FQDN 규칙·DNS·SNAT 포트 사용률을 줍니다.</p>"
        + b7_cm
        + out("""{ "name": "AzureNetworkWatcherExtension", "provisioningState": "Succeeded", "typeHandlerVersion": "1.4", … }
{ "name": "cm-vm-to-aoai", "provisioningState": "Succeeded", … "testConfigurations": [{ "name": "tcp443", "tcpConfiguration": { "port": 443 } … }] }""")
        + b7_flow
        + out("""{ "enabled": true, "name": "vnetfl-agent", "provisioningState": "Succeeded",
  "flowAnalyticsConfiguration": { "networkWatcherFlowAnalyticsConfiguration": { "enabled": true, "trafficAnalyticsInterval": 10 } }, … }""")
        + call(
            "info",
            "실측",
            "<p><code>NetworkWatcherAgentLinux</code> 는 22장 문서의 지원 목록(RHEL 6.10·7·8·9.2)에 없는 <b>RHEL 9.8</b> 에서도 설치되어 측정값이 들어왔습니다(같은 리전 TCP RTT 약 2ms · 실패 0). "
            "VNet flow log 는 연결 수·바이트만 기록하고 지연 정보는 없습니다.</p>",
        )
        + details(
            "(선택) Azure Firewall 진단 설정 — 시간당 과금, 확인 후 즉시 삭제",
            "<p>고객 환경에 Azure Firewall 이 있을 때의 ① 단계입니다. 실습에서는 Basic SKU 를 잠깐 만들어 <b>진단 설정 명령이 유효한지</b>(<code>AZFWApplicationRule</code> · <code>AZFWNetworkRule</code> · <code>AZFWDnsQuery</code> 전용 테이블, 메트릭 별도 설정)를 확인했습니다. "
            "VM 트래픽을 방화벽으로 보내는 경로(UDR·규칙)는 구성하지 않았으므로 로그 행은 생기지 않습니다.</p>"
            + code(fw_create, cap="Firewall 생성 → 진단 설정(22장 R6 ① 스니펫) → 삭제", run="B7", skip=True)
            + out("""Name                Dest
------------------  ----------------
fw-latency-logs     Dedicated
fw-latency-metrics  AzureDiagnostics"""),
        )
        + call(
            "warn",
            "Azure Firewall 이 아닌 경우",
            "<p>타사 NVA 라면 세션 수 · SNAT 풀 사용률 · 연결 실패 로그를 벤더 기준으로 요청해야 합니다. 방화벽 메트릭(예: <code>SNATPortUtilization</code>)은 로그와 <b>별도 진단 설정</b>으로 저장합니다.</p>",
        ),
        opt=False,
    )

    return section(
        "b",
        "B · 로그 켜기",
        "R1 · R5 · R3/R4 · R7 · R2 · R8 · R6 순서 — 데이터가 쌓이는 시간을 벌기 위해 가이드의 R 번호 순서와 다릅니다",
        b1 + b2 + b3 + b4 + b5 + b6 + b7,
    )
