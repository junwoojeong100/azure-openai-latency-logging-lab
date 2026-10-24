"""에이전트를 여러 번 호출하고, 호출마다 JSON 한 줄(클라이언트가 잰 시간 · 응답 ID · 트레이스 ID)을 출력한다.

사용: python invoke_agents.py <에이전트 이름> [횟수=3] [short|long] [new|same]
  new  : 호출마다 새 대화 (호스티드 에이전트는 매번 cold start)
  same : 하나의 대화를 재사용 (첫 호출만 cold, 이후 warm)
"""
import json
import os
import secrets
import sys
import time

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

PROMPTS = {
    "short": "보고서 첫 문단은 어떻게 쓰나요? 한 문장으로 답해줘.",
    "long": "일간 업무 보고서를 쓰는 방법을 한국어 700자 분량으로 자세히 설명해줘.",
}
name = sys.argv[1]
count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
prompt = PROMPTS[sys.argv[3] if len(sys.argv) > 3 else "short"]
same = (sys.argv[4] if len(sys.argv) > 4 else "new") == "same"

project = AIProjectClient(endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=DefaultAzureCredential(), allow_preview=True)
client = project.get_openai_client(agent_name=name)
conversation = client.conversations.create().id if same else None

for i in range(1, count + 1):
    trace_id = secrets.token_hex(16)
    options = {"conversation": conversation} if conversation else {}
    started = time.perf_counter()
    response = client.responses.create(
        input=prompt,
        extra_headers={"traceparent": f"00-{trace_id}-{secrets.token_hex(8)}-01"},
        **options,
    )
    usage = response.usage
    print(json.dumps({
        "agent": name, "i": i, "ms": round((time.perf_counter() - started) * 1000),
        "status": response.status, "response_id": response.id, "trace_id": trace_id,
        "input_tokens": usage.input_tokens if usage else None, "output_tokens": usage.output_tokens if usage else None,
        "error": response.error.message[:80] if response.error else None,
    }, ensure_ascii=False))
