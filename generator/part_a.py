# -*- coding: utf-8 -*-
# 0 · 시작하기 전에 / A · 실습 환경 만들기
from lib import *

SVG = """<div class="diagram"><svg viewBox="0 0 960 330" role="img" aria-label="실습 환경 구성도: VM의 앱·probe·에이전트와 Azure OpenAI, Application Insights, Connection Monitor가 하나의 Log Analytics 워크스페이스로 로그를 보냅니다">
<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="arrh"/></marker></defs>
<rect class="box" x="16" y="28" width="340" height="276" rx="14"/>
<text class="ttl" x="32" y="50">VM · RHEL 9 (인바운드 포트 없음)</text>
<rect class="boxa" x="32" y="62" width="308" height="66" rx="10"/>
<text class="lbl" x="46" y="86">데모 앱 report-agent</text><text class="sub" x="46" y="106">R3 호출 로그(JSON) + R4 OpenTelemetry</text>
<rect class="box" x="32" y="140" width="308" height="52" rx="10"/>
<text class="lbl" x="46" y="162">합성 probe (1분 타이머)</text><text class="sub" x="46" y="180">R7 · syslog local5 + 지연 순간 스냅샷</text>
<rect class="box" x="32" y="204" width="308" height="52" rx="10"/>
<text class="lbl" x="46" y="226">Azure Monitor Agent</text><text class="sub" x="46" y="244">R5 · 성능 카운터 12개 + cron·local5 syslog</text>
<rect class="boxa" x="470" y="28" width="262" height="86" rx="12"/>
<text class="ttl" x="486" y="50">AZURE OPENAI</text><text class="lbl" x="486" y="72">gpt-4.1-mini (Global Standard)</text><text class="sub" x="486" y="92">R1 진단 설정 · R2 메트릭</text>
<rect class="box" x="470" y="130" width="262" height="62" rx="12"/>
<text class="lbl" x="486" y="156">Application Insights</text><text class="sub" x="486" y="176">R4 · AppDependencies · AppTraces</text>
<rect class="box" x="470" y="208" width="262" height="62" rx="12"/>
<text class="lbl" x="486" y="234">Connection Monitor</text><text class="sub" x="486" y="254">R6 · VM → AOAI:443 · 30초 간격</text>
<rect class="boxa" x="800" y="28" width="148" height="276" rx="14"/>
<text class="ttl" x="814" y="52">LOG ANALYTICS</text>
<text class="sub" x="814" y="82">AzureDiagnostics</text><text class="sub" x="814" y="102">AzureMetrics</text><text class="sub" x="814" y="122">AppDependencies</text>
<text class="sub" x="814" y="142">AppTraces</text><text class="sub" x="814" y="162">Perf</text><text class="sub" x="814" y="182">Syslog</text>
<text class="sub" x="814" y="202">Heartbeat</text><text class="sub" x="814" y="222">NWConnectionMonitor…</text>
<text class="lbl" x="814" y="274">한 곳에서 시간으로</text><text class="lbl" x="814" y="292">맞춰 봅니다</text>
<path class="arr" d="M340,92 L470,64" marker-end="url(#ah)"/>
<path class="arr" d="M340,160 L470,100" marker-end="url(#ah)"/>
<path class="arr" d="M340,112 L470,158" marker-end="url(#ah)"/>
<path class="arr" d="M340,236 L420,236 L420,300 L874,300 L874,304" marker-end="url(#ah)"/>
<path class="arr" d="M732,70 L800,70" marker-end="url(#ah)"/>
<path class="arr" d="M732,162 L800,162" marker-end="url(#ah)"/>
<path class="arr" d="M732,240 L800,240" marker-end="url(#ah)"/>
<text class="sub" x="372" y="62">호출</text>
</svg></div>"""


def build():
    parts = []

    # ───────────────── 0. 시작하기 전에
    prereq_tbl = """<table class="nw"><thead><tr><th>항목</th><th>요구 사항</th><th>비고</th></tr></thead><tbody>
<tr><td>Azure CLI</td><td>2.60 이상 (이 가이드는 2.86 으로 검증)</td><td><code>az version</code></td></tr>
<tr><td>셸</td><td>bash (macOS · Linux · WSL · Azure Cloud Shell)</td><td>Cloud Shell 이면 설치가 필요 없습니다</td></tr>
<tr><td>구독 권한</td><td>실습용 구독의 Owner (또는 Contributor + 역할 할당 권한)</td><td>관리 ID 에 AOAI 호출 역할을 부여합니다</td></tr>
<tr><td>AOAI 쿼터</td><td>koreacentral · Global Standard · gpt-4.1-mini 20K TPM 이상</td><td>아래 확인 명령</td></tr>
<tr><td>비용(예상)</td><td>3시간 기준 약 $2 이내 — VM(B2s·RHEL) 약 $0.1/시간 + AOAI 토큰 소액, Log Analytics 는 시간당 약 1MB(월 5GB 무료 범위)</td><td>Azure Firewall(선택)은 시간당 과금 — 쓰면 바로 삭제</td></tr>
</tbody></table>"""
    body0 = (
        "<p>애플리케이션 · VM · Azure OpenAI(AOAI) 세 구간에서 <b>요청 단위 로그</b>를 모으는 방법(22장 가이드의 R1~R8)을, "
        "<b>새 리소스 그룹에 실습 환경을 처음부터 만들면서</b> 직접 해 보고 결과까지 확인합니다. "
        "모든 명령·코드·쿼리는 실제 Azure(Korea Central, RHEL 9.8, gpt-4.1-mini)에서 그대로 실행해 검증한 것입니다.</p>"
        + SVG
        + '<div class="chips"><span class="chip"><b>A</b> 환경 만들기 · 약 15분</span><span class="chip">→</span><span class="chip"><b>B</b> 로그 켜기 · 약 15분</span><span class="chip">→</span>'
        '<span class="chip"><b>⏱</b> 로그 대기 약 20분 (그동안 B 진행)</span><span class="chip">→</span><span class="chip"><b>C</b> 확인·분석 · 약 10분</span><span class="chip">→</span><span class="chip"><b>D</b> 정리 · 약 5분</span></div>'
        + prereq_tbl
        + code(
            """az cognitiveservices usage list -l koreacentral --query "[?name.value=='OpenAI.GlobalStandard.gpt4.1-mini'].{used:currentValue,limit:limit}" -o table""",
            cap="쿼터 확인 (limit − used 가 20 이상이면 됩니다 — 단위: 1K TPM)",
        )
        + out("""Used    Limit
------  -------
0.0     5000.0""")
        + call(
            "warn",
            "안전 수칙",
            "<ul><li><b>실습용 구독</b>에서 실행하세요. 마지막 단계(D)에서 리소스 그룹을 통째로 삭제합니다.</li>"
            "<li>VM 에는 <b>인바운드 포트가 없습니다</b>(NSG 규칙 없음). 모든 VM 작업은 <code>az vm run-command</code> 로 수행하므로 SSH 가 필요 없습니다.</li>"
            "<li>AOAI 키는 VM 의 <code>/etc/report-agent/app.env</code>(권한 600)에만 저장합니다. 운영에서는 키 대신 관리 ID 를 쓰세요(probe 는 이미 관리 ID 를 사용).</li>"
            "<li>수집하는 것은 시간·상태·토큰 수 같은 메타데이터뿐이며 프롬프트·응답 본문은 기록하지 않습니다.</li></ul>",
        )
    )
    parts.append(section("start", "시작하기 전에", "목표 · 구성 · 준비물", body0))

    # ───────────────── A. 실습 환경
    a1 = step(
        "a1",
        "구독 선택 · 변수 · 도우미 함수",
        "A1",
        "소요 약 2분",
        "<p>실습용 구독을 선택하고, 이후 모든 단계에서 쓰는 변수를 정합니다. "
        "변수 이름은 22장 가이드의 스니펫과 같아서(<code>RG</code> · <code>AOAI</code> · <code>LAW</code> · <code>VM</code> …) 가이드의 명령을 그대로 붙여 넣을 수 있습니다.</p>"
        + code(
            """az login                                        # 이미 로그인되어 있으면 생략 (Cloud Shell 은 불필요)
export SUB="<구독 ID>"                          # ← 실습용 구독 ID 로 바꿉니다 (az account list -o table)
az account set -s "$SUB"
for e in application-insights log-analytics scheduled-query monitor-control-service; do az extension add -n $e -y 2>/dev/null; done
for p in Microsoft.CognitiveServices Microsoft.Insights Microsoft.OperationalInsights Microsoft.Compute Microsoft.Network Microsoft.Storage Microsoft.AlertsManagement; do az provider register -n $p >/dev/null; done""",
            cap="① 구독과 확장 설치",
            run="A1",
        )
        + code(
            """export LOC=koreacentral
export SFX=$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c5)      # 이름 충돌을 피하는 5자리 접미사
export RG=rg-lablog-$SFX LAW_NAME=law-lablog-$SFX APPI=appi-lablog-$SFX AOAI=oai-lablog-$SFX ST=stlablog$SFX
export DEP=gpt41mini VNET=vnet-lablog SNET=snet-vm NSG=nsg-lablog-vm PIP=pip-lablog-vm VM=vm-lablog-rhel
export MAIL="<알림 받을 이메일>"                                      # ← 본인 메일 (B6 알림 수신)
# 22장 가이드의 변수 이름과 같게 맞춰 둔 값
export LAW=/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.OperationalInsights/workspaces/$LAW_NAME
export VM_RG=$RG AOAI_HOST=$AOAI.openai.azure.com
export TAGS="purpose=aoai-logging-lab created=$(date +%F)"
# 새 터미널에서도 이어서 쓰도록 파일로 저장합니다 (다시 열 때: source lablog.env)
cat > lablog.env <<EOF
export SUB="$SUB" LOC=$LOC SFX=$SFX RG=$RG LAW_NAME=$LAW_NAME APPI=$APPI AOAI=$AOAI ST=$ST
export DEP=$DEP VNET=$VNET SNET=$SNET NSG=$NSG PIP=$PIP VM=$VM MAIL="$MAIL"
export LAW=$LAW VM_RG=$VM_RG AOAI_HOST=$AOAI_HOST TAGS="$TAGS"
EOF
cat >> lablog.env <<'EOF'
# VM 에서 스크립트 실행 (SSH 없이 az vm run-command 사용). 사용: vmrun [KEY=값 ...] <<'X' ... X
vmrun() { local s; s="$(cat)"; if [ $# -gt 0 ]; then az vm run-command invoke -g "$RG" -n "$VM" --command-id RunShellScript --scripts "$s" --parameters "$@" --query "value[0].message" -o tsv; else az vm run-command invoke -g "$RG" -n "$VM" --command-id RunShellScript --scripts "$s" --query "value[0].message" -o tsv; fi; }
# Log Analytics 쿼리 실행 (사용: kq '<KQL>')
kq() { : "${WSID:=$(az monitor log-analytics workspace show -g "$RG" -n "$LAW_NAME" --query customerId -o tsv)}"; az monitor log-analytics query -w "$WSID" --analytics-query "$1" -o table; }
EOF
source lablog.env
echo "RG=$RG  AOAI=$AOAI  VM=$VM" """,
            cap="② 변수 · 파일 저장 · 도우미 함수 (vmrun, kq)",
            run="A1",
        )
        + out("RG=rg-lablog-x7k2q  AOAI=oai-lablog-x7k2q  VM=vm-lablog-rhel")
        + call(
            "info",
            "도우미 함수",
            "<p><code>vmrun</code> 은 VM 안에서 실행할 스크립트를 표준입력(heredoc)으로 받아 <code>az vm run-command</code> 로 실행하고, "
            "<code>kq</code> 는 Log Analytics 쿼리를 실행해 표로 보여 줍니다. VM 에 값을 넘길 때는 <code>vmrun KEY=값</code> 형식을 쓰며, "
            "<code>;</code> 처럼 셸 특수문자가 들어간 값(예: 연결 문자열)은 base64 로 넘깁니다(B3 참고). <code>az</code> 는 표의 열을 알파벳순으로 보여 주므로 아래 ‘예상 결과’와 열 순서가 다를 수 있습니다.</p>",
        ),
    )

    a2 = step(
        "a2",
        "리소스 그룹 · Log Analytics · Application Insights · 네트워크",
        "A2",
        "소요 약 2분",
        "<p>모든 로그가 모이는 <b>Log Analytics 워크스페이스</b>와, 그 워크스페이스에 연결된(workspace-based) <b>Application Insights</b>를 만듭니다. "
        "앞서 정한 대로 앱·AOAI·VM 로그를 한 워크스페이스에서 시간으로 조인하기 위함입니다.</p>"
        + code(
            """az group create -n $RG -l $LOC --tags $TAGS -o none
az monitor log-analytics workspace create -g $RG -n $LAW_NAME -l $LOC --sku PerGB2018 --retention-time 30 --tags $TAGS -o none
az monitor app-insights component create -a $APPI -g $RG -l $LOC --kind web --application-type web --workspace "$LAW" --tags $TAGS -o none
az network nsg create -g $RG -n $NSG -l $LOC --tags $TAGS -o none
az network vnet create -g $RG -n $VNET -l $LOC --address-prefixes 10.20.0.0/16 --subnet-name $SNET --subnet-prefixes 10.20.1.0/24 --nsg $NSG --tags $TAGS -o none
az network public-ip create -g $RG -n $PIP -l $LOC --sku Standard --allocation-method Static --tags $TAGS -o none""",
            run="A2",
        )
        + call(
            "info",
            "공용 IP 는 왜 만드나요",
            "<p>새 가상 네트워크의 VM 은 기본 아웃바운드 접속이 없습니다. Standard 공용 IP 를 붙이면 <b>아웃바운드만</b> 열리고(인바운드는 NSG 에 규칙이 없어 차단), "
            "VM 이 AOAI · Azure Monitor · 패키지 저장소에 나갈 수 있습니다.</p>",
        )
        + code("az resource list -g $RG -o table", cap="확인", run="A2")
        + out("""Name              ResourceGroup     Location      Type
----------------  ----------------  ------------  ---------------------------------------
law-lablog-…       rg-lablog-…        koreacentral  Microsoft.OperationalInsights/workspaces
appi-lablog-…      rg-lablog-…        koreacentral  Microsoft.Insights/components
nsg-lablog-vm      rg-lablog-…        koreacentral  Microsoft.Network/networkSecurityGroups
vnet-lablog        rg-lablog-…        koreacentral  Microsoft.Network/virtualNetworks
pip-lablog-vm      rg-lablog-…        koreacentral  Microsoft.Network/publicIPAddresses"""),
    )

    a3 = step(
        "a3",
        "Azure OpenAI 리소스와 모델 배포",
        "A3",
        "소요 약 2분",
        "<p>실제 고객 환경과 같은 종류(<code>kind=OpenAI</code>)의 리소스를 만들고, 비추론(non-reasoning) 모델 <b>gpt-4.1-mini</b> 를 Global Standard 로 배포합니다. "
        "사용자 지정 도메인(<code>--custom-domain</code>)은 관리 ID(Entra) 인증에 필요합니다.</p>"
        + code(
            """az cognitiveservices account create -g $RG -n $AOAI -l $LOC --kind OpenAI --sku S0 --custom-domain $AOAI --tags $TAGS --yes -o none
az cognitiveservices account deployment create -g $RG -n $AOAI --deployment-name $DEP \\
  --model-name gpt-4.1-mini --model-version 2025-04-14 --model-format OpenAI --sku-name GlobalStandard --sku-capacity 20 -o none
az cognitiveservices account deployment show -g $RG -n $AOAI --deployment-name $DEP --query properties.provisioningState -o tsv""",
            run="A3",
        )
        + out("Succeeded")
        + call(
            "warn",
            "추론 모델(gpt-5 계열 등)을 쓰려면",
            "<p>이 실습의 코드는 <code>max_tokens</code> 를 사용합니다. gpt-5 계열 같은 추론 모델은 <code>max_tokens</code> 를 받지 않고 <code>max_completion_tokens</code> 를 요구하므로, "
            "그 모델로 실습하려면 R3 의 호출부와 R7 probe 의 요청 본문(<code>\"max_tokens\":1</code>)을 바꿔야 합니다.</p>",
        ),
    )

    a4 = step(
        "a4",
        "RHEL 9 VM 과 관리 ID 권한",
        "A4",
        "소요 약 3분",
        "<p>앱·probe·에이전트가 돌 VM 입니다. <b>시스템 할당 관리 ID</b>를 켜고, 이 ID 에 AOAI 호출 역할(<code>Cognitive Services OpenAI User</code>)을 주어 probe 가 키 없이 호출하게 합니다.</p>"
        + code(
            """ssh-keygen -t rsa -b 3072 -N "" -f ./id_lab -C lablog-temp -q        # VM 생성에만 필요한 임시 키 (실습 후 삭제 — SSH 는 쓰지 않습니다)
az vm create -g $RG -n $VM -l $LOC --image RedHat:RHEL:9-lvm-gen2:latest --size Standard_B2s \\
  --admin-username azureuser --ssh-key-values ./id_lab.pub --vnet-name $VNET --subnet $SNET \\
  --public-ip-address $PIP --nsg "" --assign-identity '[system]' --os-disk-size-gb 64 --storage-sku StandardSSD_LRS --tags $TAGS -o none
VM_MI=$(az vm show -g $RG -n $VM --query identity.principalId -o tsv)
AOAI_ID=$(az cognitiveservices account show -g $RG -n $AOAI --query id -o tsv)
az role assignment create --assignee-object-id $VM_MI --assignee-principal-type ServicePrincipal \\
  --role "Cognitive Services OpenAI User" --scope $AOAI_ID -o none
echo "export AOAI_ID=$AOAI_ID" >> lablog.env
az vm show -g $RG -n $VM --query "{state:provisioningState, identity:identity.type}" -o table""",
            run="A4",
        )
        + out("""State      Identity
---------  --------------
Succeeded  SystemAssigned"""),
    )

    a5 = step(
        "a5",
        "VM 준비 — Python 3.12 · 패키지",
        "A5",
        "소요 약 3분 · 첫 <code>vmrun</code> 은 30~60초 걸립니다",
        "<p><b>RHEL 9 의 기본 <code>python3</code> 는 3.9</b> 입니다. R4(Application Insights 계측, <code>azure-monitor-opentelemetry</code>)는 Python 3.10 이상이 필요하므로 3.12 를 설치해 전용 가상환경을 만듭니다. "
        "<code>initscripts</code> 는 Azure Monitor Agent(R5) 문서가 요구하는 패키지입니다.</p>"
        + code(
            """vmrun AOAI_HOST=$AOAI_HOST DEP=$DEP <<'VMEOF'
set -e
dnf install -y python3.12 python3.12-pip initscripts >/tmp/dnf.log 2>&1 || { tail -20 /tmp/dnf.log; exit 1; }
python3.12 --version
install -d -m 0755 /opt/report-agent
python3.12 -m venv /opt/report-agent/venv
/opt/report-agent/venv/bin/pip install --quiet --upgrade pip
/opt/report-agent/venv/bin/pip install --quiet "openai>=3.0.0" "azure-monitor-opentelemetry>=1.8.10"
/opt/report-agent/venv/bin/pip list 2>/dev/null | grep -i -E "^(openai|azure-monitor-opentelemetry|opentelemetry-sdk|httpx2?) "
echo "== AOAI 엔드포인트 도달 확인 (키 없이 호출하므로 401 이 정상)"
curl -s -o /dev/null -w "%{http_code} dns=%{time_namelookup}s tcp=%{time_connect}s tls=%{time_appconnect}s\\n" --max-time 15 "https://$AOAI_HOST/openai/deployments/$DEP/chat/completions?api-version=2024-10-21" -X POST -H "Content-Type: application/json" -d '{}'
VMEOF""",
            run="A5",
        )
        + out("""Python 3.12.x
azure-monitor-opentelemetry  1.8.11
httpx2                       2.x
openai                       3.x
opentelemetry-sdk            1.4x
== AOAI 엔드포인트 도달 확인 (키 없이 호출하므로 401 이 정상)
401 dns=0.019s tcp=0.021s tls=0.048s""")
        + call("info", "run-command 한 번에 약 30초", "<p>VM 에이전트가 스크립트를 받아 실행하는 시간입니다. 오래 걸리는 설치는 한 번에 묶어서 실행하세요.</p>"),
    )

    parts.append(
        section(
            "a",
            "A · 실습 환경 만들기",
            "리소스 그룹부터 VM 까지 약 15분",
            a1 + a2 + a3 + a4 + a5,
        )
    )
    return "".join(parts)
