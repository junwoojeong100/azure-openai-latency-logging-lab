#!/bin/bash
# R1_aoai_diagnostic_settings.sh - AOAI 진단 설정 → Log Analytics (코드 변경·재배포 없음)
# 권한: 진단 설정 생성 = 대상 리소스의 Monitoring Contributor / 로그 조회 = Log Analytics Reader
# 사전: R0 에서 정한 워크스페이스 리소스 ID (Application Insights 와 같은 워크스페이스 권장)
RG="<AOAI 리소스 그룹>"; AOAI=contoso-oai-prod-korea-central
LAW="<Log Analytics 워크스페이스 리소스 ID>"

# >>> slide:diag
AOAI_ID=$(az cognitiveservices account show -g $RG -n $AOAI --query id -o tsv)
az monitor diagnostic-settings create -n diag-aoai-latency --resource $AOAI_ID \
  --workspace $LAW --metrics '[{"category":"AllMetrics","enabled":true}]' \
  --logs '[{"category":"RequestResponse","enabled":true},
           {"category":"Audit","enabled":true}]'
az monitor diagnostic-settings list --resource $AOAI_ID -o table
# <<< slide:diag
