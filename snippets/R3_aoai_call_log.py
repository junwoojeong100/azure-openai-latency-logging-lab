# R3_aoai_call_log.py - AOAI 호출 1회(시도)마다 JSON 1줄을 남기는 헬퍼. 프로젝트에 한 번 추가합니다.
# 요구: Python 3.9+ / openai 패키지 (AzureOpenAI). 프롬프트·응답 본문은 기록하지 않습니다(메타데이터만).
import json, logging, threading, time, uuid
from contextlib import contextmanager

# >>> slide:helper
log = logging.getLogger("aoai.call")       # 파일·App Insights(R4)로
_lock, _busy = threading.Lock(), 0
ERR = {"APITimeoutError": "client_timeout"}    # 그 외 예외는 "error"

@contextmanager
def call_log(**fields):
    global _busy
    with _lock:
        _busy += 1
        n = _busy                       # 시작 시점의 동시 호출 수
    rec = {"event": "aoai_call", "cid": str(uuid.uuid4()),
           "inflight": n, **fields}
    t0 = time.perf_counter()
    try:
        yield rec
        rec["outcome"] = "ok"
    except Exception as e:              # 기록 후 예외는 그대로 전달
        rec.update(outcome=ERR.get(type(e).__name__, "error"),
                   error=type(e).__name__,
                   status=getattr(e, "status_code", None),
                   request_id=getattr(e, "request_id", None))
        raise
    finally:
        with _lock:
            _busy -= 1
        rec["total_ms"] = round((time.perf_counter() - t0) * 1000)
        log.info(json.dumps(rec, ensure_ascii=False))
# <<< slide:helper
