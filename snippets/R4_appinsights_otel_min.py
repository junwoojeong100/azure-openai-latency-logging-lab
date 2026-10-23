# R4_appinsights_otel_min.py - Application Insights(OpenTelemetry) 가장 간단한 연결 (간단판 2단계)
# 앱 시작 코드에서 openai 클라이언트를 만들기 전에 1회 호출합니다.
# 요구: Python 3.10+,  pip install "azure-monitor-opentelemetry>=1.8.10"
# 환경변수: R4_telemetry.env.sample 참고 (연결 문자열·서비스 이름·샘플링)

# >>> slide:init-min
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor()   # 연결 문자열은 환경변수에서 읽음
# <<< slide:init-min
