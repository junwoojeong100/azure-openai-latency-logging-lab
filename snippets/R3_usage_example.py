# R3_usage_example.py - 기존 호출부에 적용하는 방법 (클라이언트 설정 + with 블록으로 감싸기)
import logging, os
from openai import AzureOpenAI, Timeout
from R3_aoai_call_log import call_log

logging.basicConfig(level=logging.INFO, format="%(message)s")   # 운영에서는 파일/R4 핸들러로 대체

# >>> slide:client
READ_TIMEOUT = 60.0                  # ← 현재 운영 값으로
client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],  # 권장: 관리 ID
    api_version="2024-10-21",
    timeout=Timeout(5.0, read=READ_TIMEOUT),
    max_retries=0)           # SDK 자동 재시도 끔 → 시도마다 기록
# <<< slide:client

# >>> slide:usage
def ask(messages, deployment, job_id=""):
    with call_log(deployment=deployment, job_id=job_id, max_tokens=800,
                  stream=False, read_timeout_s=READ_TIMEOUT) as rec:
        raw = client.chat.completions.with_raw_response.create(
            model=deployment, messages=messages, max_tokens=800,
            extra_headers={"x-ms-client-request-id": rec["cid"]})
        res, h = raw.parse(), raw.headers
        rec.update(status=raw.status_code,
                   request_id=h.get("x-request-id"),
                   apim_request_id=h.get("apim-request-id"),
                   region=h.get("x-ms-region"),
                   prompt_tokens=res.usage.prompt_tokens,
                   completion_tokens=res.usage.completion_tokens,
                   finish_reason=res.choices[0].finish_reason)
    return res
# <<< slide:usage
