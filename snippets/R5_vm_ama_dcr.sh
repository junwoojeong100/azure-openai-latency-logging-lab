#!/bin/bash
# R5_vm_ama_dcr.sh - VM에 Azure Monitor Agent 설치 + 수집 규칙(DCR) 연결. 권한: Monitoring Contributor
# 먼저 VM 에서 확인: cat /etc/redhat-release (7.9 / 8.x / 9+) · python3, which, initscripts 설치 · systemctl is-active rsyslog
#                    update-crypto-policies --show  (FUTURE 이면 AMA 동작 불가)
RG="<VM 리소스 그룹>"; VM=contoso-vm-prod-agent-rhel; LOC=koreacentral
LAW="<Log Analytics 워크스페이스 리소스 ID>"

# >>> slide:ama
VM_ID=$(az vm show -g $RG -n $VM --query id -o tsv)
az vm identity assign -g $RG -n $VM                  # 관리 ID (있으면 생략)
az vm extension set -g $RG --vm-name $VM --name AzureMonitorLinuxAgent \
  --publisher Microsoft.Azure.Monitor --enable-auto-upgrade true

sed "s#<LAW_ID>#$LAW#" R5_dcr_linux.json > /tmp/dcr.json   # ID 치환
DCR_ID=$(az monitor data-collection rule create -g $RG -n dcr-aoai-vm-latency \
  -l $LOC --kind Linux --rule-file /tmp/dcr.json --query id -o tsv)
az monitor data-collection rule association create --name assoc-$VM \
  --rule-id $DCR_ID --resource $VM_ID
# <<< slide:ama
