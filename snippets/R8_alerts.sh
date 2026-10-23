#!/bin/bash
# R8_alerts.sh - 알림 규칙: 메트릭 알림(AOAI) + 로그 알림(앱·probe). 권한: 대상 리소스 그룹의 Monitoring Contributor
# 로그 알림은 로그 수집 지연만큼 늦게 울립니다 — 빠른 신호는 메트릭 알림을 씁니다.
RG="<알림을 만들 리소스 그룹>"; MAIL="<수신 이메일>"
AOAI_ID="<AOAI 리소스 ID>"; LAW="<Log Analytics 워크스페이스 리소스 ID>"

# >>> slide:alerts
# 수신 그룹(이메일) 생성 후 ID 조회
az monitor action-group create -g $RG -n ag-aoai-latency --short-name aoailat \
  --action email owner $MAIL
AG=$(az monitor action-group show -g $RG -n ag-aoai-latency --query id -o tsv)
Q1="AppTraces | where Message has 'aoai_call' and Message has 'client_timeout'"
Q2="Syslog | where ProcessName == 'aoai-probe' | extend p = parse_json(SyslogMessage)
    | where toint(p.rc) != 0 or toint(p.total_ms) >= 8000"
az monitor metrics alert create -g $RG -n aoai-499 --scopes $AOAI_ID \
  --condition "total AzureOpenAIRequests > 0 where StatusCode includes 499" \
  --window-size 5m --evaluation-frequency 1m --severity 2 --action $AG
az monitor metrics alert create -g $RG -n aoai-ttlt-high --scopes $AOAI_ID \
  --condition "max AzureOpenAITTLTInMS > 20000" \
  --window-size 5m --evaluation-frequency 1m --severity 3 --action $AG
az monitor scheduled-query create -g $RG -n app-client-timeout --scopes $LAW \
  --condition "count 'Q' > 0" --condition-query Q="$Q1" \
  --window-size 5m --evaluation-frequency 5m --severity 2 --action-groups $AG
az monitor scheduled-query create -g $RG -n probe-slow --scopes $LAW \
  --condition "count 'Q' > 0" --condition-query Q="$Q2" \
  --window-size 5m --evaluation-frequency 5m --severity 3 --action-groups $AG
# <<< slide:alerts
