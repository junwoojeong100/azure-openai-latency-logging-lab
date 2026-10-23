# R4_appinsights_otel.py - Application Insights(OpenTelemetry) 연결. 앱 시작 코드에서 openai 클라이언트를 만들기 전에 1회 호출합니다.
# 요구: Python 3.10+,  pip install "azure-monitor-opentelemetry>=1.8.10"
#       (신규 앱은 microsoft-opentelemetry 도 가능하지만, 두 배포판을 함께 초기화하지 마세요)
# 환경변수: R4_telemetry.env.sample 참고 (연결 문자열·서비스 이름·샘플링)
import logging
from azure.monitor.opentelemetry import configure_azure_monitor

# >>> slide:init
configure_azure_monitor(logger_name="aoai")       # 연결 문자열은 환경변수에서
logging.getLogger("aoai").setLevel(logging.INFO)  # R3 로그 → AppTraces
# <<< slide:init
