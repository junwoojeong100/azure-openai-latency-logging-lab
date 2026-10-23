# /opt/report-agent/app_demo.py — 실습용 데모 앱(report-agent 흉내): AOAI 를 계속 호출하면서 R3(호출 로그)·R4(App Insights)를 적용합니다.
import logging, os, random, sys, time
sys.path.insert(0, "/opt/report-agent")

from azure.monitor.opentelemetry import configure_azure_monitor      # R4: 연결 문자열은 환경변수에서
configure_azure_monitor(logger_name="aoai")
logging.getLogger("aoai").setLevel(logging.INFO)                     # R3 로그 → AppTraces

import R3_usage_example as r3                                        # R3: 클라이언트 설정 + ask()
from R3_aoai_call_log import call_log
logging.getLogger().setLevel(logging.WARNING)                       # azure-core 의 HTTP 로그가 journald 를 채우지 않도록 (aoai 로거는 위에서 INFO)
from openai import AzureOpenAI, Timeout

DEP = os.environ.get("AOAI_DEPLOYMENT", "gpt41mini")
IMPATIENT_S = 1.0                                                    # 일부러 짧게 → client_timeout(서버 쪽에서는 499 예상)
impatient = AzureOpenAI(azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"], api_key=os.environ["AZURE_OPENAI_API_KEY"],
                        api_version="2024-10-21", timeout=Timeout(5.0, read=IMPATIENT_S), max_retries=0)

def ask_impatient(messages, deployment, job_id=""):                  # R3 의 ask() 와 같은 구조, 클라이언트만 다름
    with call_log(deployment=deployment, job_id=job_id, max_tokens=800, stream=False, read_timeout_s=IMPATIENT_S) as rec:
        raw = impatient.chat.completions.with_raw_response.create(
            model=deployment, messages=messages, max_tokens=800, extra_headers={"x-ms-client-request-id": rec["cid"]})
        res, h = raw.parse(), raw.headers
        rec.update(status=raw.status_code, request_id=h.get("x-request-id"), apim_request_id=h.get("apim-request-id"),
                   region=h.get("x-ms-region"), prompt_tokens=res.usage.prompt_tokens,
                   completion_tokens=res.usage.completion_tokens, finish_reason=res.choices[0].finish_reason)
    return res

SHORT = [{"role": "user", "content": "한 문장으로 인사해줘."}]
LONG = [{"role": "user", "content": "증권사 일간 시장 리포트를 쓰는 방법을 한국어 700자 분량으로 자세히 설명해줘."}]

i = 0
while True:
    i += 1
    r = random.random()
    try:
        if r < 0.55:   r3.ask(SHORT, DEP, job_id=f"job-{i}")
        elif r < 0.80: r3.ask(LONG, DEP, job_id=f"job-{i}")
        elif r < 0.95: ask_impatient(LONG, DEP, job_id=f"job-{i}")   # client_timeout
        else:          r3.ask(SHORT, "no-such-deployment", job_id=f"job-{i}")   # 404 → outcome=error
    except Exception:
        pass                                                         # call_log 가 이미 기록함
    time.sleep(random.uniform(8, 16))
