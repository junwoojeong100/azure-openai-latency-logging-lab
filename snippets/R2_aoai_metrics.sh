#!/bin/bash
# R2_aoai_metrics.sh - AOAI 메트릭 확인용 읽기 전용 명령 (차트는 포털 메트릭 탐색기에서 구성)
AOAI_ID="<R1과 같은 AOAI 리소스 ID>"

# >>> slide:statuscode
# StatusCode 값(200/429/499…) 확인
az monitor metrics list \
  --resource $AOAI_ID \
  --metrics AzureOpenAIRequests \
  --dimension StatusCode \
  --aggregation Total \
  --interval 1h --offset 1d -o table
# <<< slide:statuscode
