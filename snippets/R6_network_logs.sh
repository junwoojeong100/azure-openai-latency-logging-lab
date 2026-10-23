#!/bin/bash
# R6_network_logs.sh - 네트워크 경로 로그 (허브 구독 권한 필요). <...> 값을 채워 실행합니다.
# 사전: Network Watcher 가 koreacentral 에 있어야 합니다. 스토리지는 같은 리전의 Standard 계정이어야 합니다. Azure Firewall 이 아니면 ①은 건너뜁니다(NVA 는 벤더 기준 세션/SNAT 로그).
FW="<방화벽 리소스 ID>"      LAW="<Log Analytics 워크스페이스 리소스 ID>"
VM_RG="<VM 리소스 그룹>"     VM=contoso-vm-prod-agent-rhel      AOAI_HOST="<리소스 이름>.openai.azure.com"

# ① Azure Firewall: 리소스 로그(전용 테이블)와 메트릭은 별도 진단 설정으로 저장
# >>> slide:fw
az monitor diagnostic-settings create -n fw-latency-logs \
  --resource $FW --workspace $LAW --export-to-resource-specific true \
  --logs '[{"category":"AZFWApplicationRule","enabled":true},
           {"category":"AZFWNetworkRule","enabled":true},
           {"category":"AZFWDnsQuery","enabled":true}]'
az monitor diagnostic-settings create -n fw-latency-metrics \
  --resource $FW --workspace $LAW \
  --metrics '[{"category":"AllMetrics","enabled":true}]'
# <<< slide:fw

# ② Connection Monitor: VM → AOAI:443 을 30초마다 (Linux 확장 설치 후 생성)
# >>> slide:cm
VM_ID=$(az vm show -g $VM_RG -n $VM --query id -o tsv)
az vm extension set -g $VM_RG --vm-name $VM --name NetworkWatcherAgentLinux \
  --publisher Microsoft.Azure.NetworkWatcher --enable-auto-upgrade true \
  --version 1.4 --extension-instance-name AzureNetworkWatcherExtension
az network watcher connection-monitor create -n cm-vm-to-aoai -l koreacentral \
  --endpoint-source-name vm --endpoint-source-resource-id $VM_ID \
  --endpoint-dest-name aoai --endpoint-dest-address $AOAI_HOST \
  --endpoint-dest-type ExternalAddress --test-group-name tg-aoai \
  --test-config-name tcp443 --protocol Tcp --tcp-port 443 --frequency 30 \
  --workspace-ids $LAW
# <<< slide:cm

# >>> slide:flow
# ③ (선택) VNet flow log — NSG flow log 는 2025-06-30 이후 신규 생성이 불가합니다
az network watcher flow-log create -l koreacentral -n vnetfl-agent \
  --vnet "<VNet 리소스 ID>" --storage-account "<스토리지 계정 리소스 ID>" \
  --traffic-analytics true --workspace $LAW --interval 10 --retention 30
# <<< slide:flow
