#!/bin/sh
# Foundry 프로젝트에 Application Insights 를 만들어 연결한다.
# 연결만 되어 있으면 프롬프트·호스티드 에이전트의 서버 쪽 트레이스가 코드 변경 없이 쌓인다.
set -eu
RG="$AZURE_RESOURCE_GROUP"; LOC="$AZURE_LOCATION"
LAW="law-$AZURE_ENV_NAME"; APPI="appi-$AZURE_ENV_NAME"
PROJECT_ID="/subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/$RG/providers/Microsoft.CognitiveServices/accounts/$AZURE_AI_ACCOUNT_NAME/projects/$AZURE_AI_PROJECT_NAME"

az monitor log-analytics workspace create -g "$RG" -n "$LAW" -l "$LOC" -o none
az monitor app-insights component create -g "$RG" -a "$APPI" -l "$LOC" -o none \
  --workspace "$(az monitor log-analytics workspace show -g "$RG" -n "$LAW" --query id -o tsv)" --kind web --application-type web
APPI_ID=$(az monitor app-insights component show -g "$RG" -a "$APPI" --query id -o tsv)
CS=$(az monitor app-insights component show -g "$RG" -a "$APPI" --query connectionString -o tsv)

az rest --method put -o none --url "https://management.azure.com$PROJECT_ID/connections/$APPI?api-version=2025-04-01-preview" \
  --body "{\"properties\":{\"category\":\"AppInsights\",\"target\":\"$APPI_ID\",\"authType\":\"ApiKey\",\"isSharedToAll\":true,\"credentials\":{\"key\":\"$CS\"},\"metadata\":{\"ApiType\":\"Azure\",\"ResourceId\":\"$APPI_ID\"}}}"

# 호출자에게 Foundry User(구 Azure AI User), 프로젝트 관리 ID 에게 Log Analytics Reader
az role assignment create -o none --assignee-object-id "$(az ad signed-in-user show --query id -o tsv)" --assignee-principal-type User \
  --role 53ca6127-db72-4b80-b1b0-d745d6d5456d --scope "$PROJECT_ID"
az role assignment create -o none --assignee-object-id "$(az rest --method get --url "https://management.azure.com$PROJECT_ID?api-version=2025-04-01-preview" --query identity.principalId -o tsv)" \
  --assignee-principal-type ServicePrincipal --role 73c42c96-874c-492b-b04d-ab87d138a893 --scope "$APPI_ID"
echo "Application Insights connected: $APPI"
