#!/bin/sh
# 에이전트 알림 2개: 느린 실행(콜드 스타트 포함 8초 초과) · 실패한 실행. 사용: MAIL=<수신 이메일> sh scripts/alerts.sh
# 텔레메트리가 늦게 도착해도 놓치지 않도록 평가 창(15분)을 평가 주기(5분)보다 길게 잡았다 — 같은 사건이 최대 3번 평가된다.
set -eu
RG="$AZURE_RESOURCE_GROUP"; APPI_ID=$(az monitor app-insights component show -g "$RG" -a "appi-$AZURE_ENV_NAME" --query id -o tsv)
az monitor action-group create -g "$RG" -n ag-agent-latency --short-name agentlat --action email owner "$MAIL" -o none
AG=$(az monitor action-group show -g "$RG" -n ag-agent-latency --query id -o tsv)

SLOW=$(cat <<'KQL'
let hosted = requests | where cloud_RoleName == "agentsv2" | distinct agent = tostring(customDimensions["gen_ai.agent.name"]);
union
  (requests | where cloud_RoleName == "agentsv2" and customDimensions["gen_ai.operation.name"] == "invoke_agent"
   | project total_ms = duration + coalesce(toint(customDimensions["hosted_agent.latency.platform_preprocessing_ms"]), 0) + coalesce(toint(customDimensions["hosted_agent.latency.infra_setup_ms"]), 0) + coalesce(toint(customDimensions["hosted_agent.latency.container_readiness_ms"]), 0)),
  (dependencies | where cloud_RoleName == "responsesapi" and customDimensions["gen_ai.operation.name"] == "invoke_agent" and tostring(customDimensions["gen_ai.agent.name"]) !in (hosted)
   | project total_ms = duration)
| where total_ms > 8000
KQL
)
FAILED='dependencies | where success == false and isnotempty(customDimensions["gen_ai.operation.name"])'

az monitor scheduled-query create -g "$RG" -n agent-run-slow --scopes "$APPI_ID" --action-groups "$AG" -o none \
  --condition "count 'Q' > 0" --condition-query Q="$SLOW" --window-size 15m --evaluation-frequency 5m --severity 3
az monitor scheduled-query create -g "$RG" -n agent-run-failed --scopes "$APPI_ID" --action-groups "$AG" -o none \
  --condition "count 'Q' > 0" --condition-query Q="$FAILED" --window-size 15m --evaluation-frequency 5m --severity 2
