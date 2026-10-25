# -*- coding: utf-8 -*-
# B3 · 기존 앱의 호출을 에이전트 호출로 바꾸면 (전환 공수) / C7 · 앱에서 본 시간 vs 서버에서 본 시간 (앱 최소 기록)
# 표의 값은 foundry_expected/ 의 실측 파일(E1 · P1 · E2 · E2_log · E2_direct · E3)에서 읽어 옵니다.
import re

from lib import *
import foundry_a


def _lines(name):
    t = expected(name)
    assert t, f"foundry_expected/{name}.txt 가 없습니다"
    return t.split("\n")


def e1_rows():
    rows = []
    for ln in _lines("E1"):
        m = re.match(r"^(\S+)\s+\S+\s+-> (.+)$", ln)
        assert m, ln
        rows.append((m.group(1), m.group(2)))
    assert [r[0] for r in rows] == ["agent_basic", "direct_responses", "direct_chat"]
    assert "rows=2" in rows[0][1] and "NO TELEMETRY" in rows[1][1] and "NO TELEMETRY" in rows[2][1]
    return rows


def p1_rows():
    out_rows = []
    for ln in _lines("P1")[2:]:
        m = re.match(r"^(.+?)\s{2,}(.+?) \| (.+)$", ln)
        assert m, ln
        out_rows.append((m.group(1).strip(), m.group(2).strip(), m.group(3).strip()))
    assert len(out_rows) == 9
    return out_rows


def e3_rows():
    rows = [ln.split() for ln in _lines("E3")[1:]]
    assert len(rows) == 8 and all(len(r) == 5 for r in rows)
    return rows


def e2_rows():
    rows = []
    for ln in _lines("E2")[2:]:
        m = re.match(r"^(\S+)\s+(\d+)\s+(\S+)\s+(.+)$", ln)
        assert m, ln
        rows.append((m.group(1), int(m.group(2)), m.group(3), m.group(4).split(" -> ")))
    assert len(rows) == 2
    return rows


def e2_direct():
    d = {}
    for ln in _lines("E2_direct")[1:]:
        k, v = ln.split(":", 1)
        d[k.strip()] = [int(x) for x in re.findall(r"\d+", v)]
    assert len(d["agent"]) == 10 and len(d["direct"]) == 10
    return d


def retry_log_line():
    ln = _lines("E2_log")[1]
    m = re.search(r"Retrying request in ([\d.]+) seconds \(retry (\d) of (\d)\)", ln)
    assert m
    return ln, float(m.group(1))


def _pick(text, start, n):
    """text 에서 start 로 시작하는 줄부터 n 줄 (원본 그대로)"""
    lines = text.split("\n")
    i = next(j for j, l in enumerate(lines) if l.lstrip().startswith(start))
    return "\n".join(lines[i : i + n])


def build_b3():
    e1 = e1_rows()
    tele = {
        "agent_basic": ("에이전트를 지정해 호출 (`get_openai_client(agent_name=…)` → `responses.create`)", "**있음** — `responsesapi` 역할의 `invoke_agent` · `chat` 스팬 2건"),
        "direct_responses": ("같은 프로젝트 엔드포인트로 **모델을 직접** 호출 — Responses API", "**없음** (0건)"),
        "direct_chat": ("같은 프로젝트 엔드포인트로 **모델을 직접** 호출 — Chat Completions API", "**없음** (0건)"),
    }
    e1_tbl = table(["호출 방법", "Application Insights 트레이스"], [[tele[k][0], tele[k][1]] for k, _ in e1])

    r3 = snipfile("R3_usage_example.py")
    inv = fd("invoke_agents.py")
    before = (
        "# 기존 — 모델을 직접 부르는 호출부 (API 키 · Chat Completions · 배포 이름 · 가이드 1 의 R3 예제에서 발췌)\n# (READ_TIMEOUT · Timeout · rec 는 그 예제의 변수 — 내 앱의 기존 timeout 값 · 기록용 변수로 읽으세요)\n"
        + _pick(r3, "client = AzureOpenAI(", 6)
        + "\n…\n"
        + _pick(r3, "raw = client.chat.completions.with_raw_response.create(", 3)
    )
    after = (
        "# 에이전트 경유 — invoke_agents.py (Entra ID · Responses · 에이전트 이름)\n"
        + _pick(inv, "project = AIProjectClient(", 2)
        + "\n…\n"
        + _pick(inv, "response = client.responses.create(", 5)
    )
    code_cmp = code(before + "\n\n" + after, cap="호출부 — 기존에서 에이전트 경유로 (두 파일의 발췌, …은 생략한 부분 · 실행 블록 아님)", lang="python", nocopy=True)

    p1 = p1_rows()
    label_map = {
        "system 메시지": "system 메시지 (input 항목 `type: \"message\"`)",
        "max_output_tokens": "`max_output_tokens`",
        "stream": "`stream` (스트리밍)",
        "metadata + user": "`metadata` · `user`",
        "temperature": "`temperature`",
        "instructions": "`instructions` (요청별 지시문)",
        "tools": "`tools` (function)",
        "text.format": "JSON 모드 (`text.format`)",
        "reasoning.effort": "`reasoning.effort`",
    }

    def yn(s):
        if s.startswith("OK"):
            m = re.search(r"첫 토큰 (\d+)ms", s)
            return Raw('<td class="ok">가능' + (f" <small>(첫 토큰 {m.group(1)}ms)</small>" if m else "") + "</td>")
        assert s.startswith("ERR 400"), s
        return Raw('<td class="no">불가 <small>(HTTP 400)</small></td>')

    body = ""
    for lab, a, d in p1:
        key = next(k for k in label_map if lab.startswith(k))
        body += f"<tr><td>{inline(label_map[key])}</td>{yn(a)}{yn(d)}</tr>"
    p1_tbl = (
        '<table><thead><tr><th>요청별 설정 (2026-10-24 실측 · 각 1회)</th><th>에이전트를 지정한 호출</th><th>모델을 직접 호출</th></tr></thead><tbody>' + body + "</tbody></table>"
    )

    return step(
        "b3",
        "기존 앱의 호출을 에이전트 호출로 바꾸면 — 전환 공수",
        "B3",
        "읽는 단계 · 실행하는 명령 없음 · 2026-10-24 실측(랩 환경) · 트레이스를 본 뒤(C 단계) 다시 읽어도 됩니다",
        brief(
            what="기존 앱이 AOAI 를 직접 부르던 호출을 **에이전트를 부르는 호출로 바꿀 때 무엇이 바뀌는지** 봅니다.",
            why="에이전트를 거치면 서버 쪽 모니터링이 쉬워지는 대신 **호출 방식이 바뀌고, 요청마다 정하던 설정은 에이전트 정의로 옮겨야** 합니다. 도입 전에 영향을 평가하려는 것입니다.",
            result="‘엔드포인트만 바꾸면 안 되는 이유’ · 호출 코드의 변경점 5가지 · 요청별 설정 가능/불가 표 · 전환 후보 판단 체크리스트 · 인프라 전환 시 주의(문서 기준).",
            apply="내 앱이 **실제로 쓰는 요청 옵션**(temperature · tools · JSON 모드 …)을 아래 표와 대조해 보세요. 불가 항목을 쓰고 있다면 **에이전트 정의로 옮길 수 있는지** 시범(PoC, 작은 규모로 먼저 해 보는 시험)에서 확인해야 합니다.",
        )
        + md("#### 가. 엔드포인트만 바꾸면 트레이스가 생기나요? — 아니요")
        + md("같은 Foundry 프로젝트 엔드포인트라도 **모델을 직접 부르면** Application Insights 에 아무것도 남지 않습니다. 트레이스는 **에이전트를 거친 호출**에서만 생깁니다.")
        + e1_tbl
        + call("warn", "그래서 ‘엔드포인트 교체’가 아니라 ‘호출 방식 변경’입니다", "트레이스를 얻으려면 앱의 호출부가 **에이전트를 지정하는 방식**으로 바뀌어야 합니다. 에이전트로 옮기지 못하는 호출은 앱 · VM 쪽에 로그와 진단 설정을 따로 더하는 방식(가이드 1 의 R1~R8)이 그대로 필요합니다.")
        + md("#### 나. 호출 코드는 어떻게 바뀌나요 — 바뀌는 것 · 그대로인 것")
        + code_cmp
        + md(
            """
            바뀌는 것은 크게 다섯 가지입니다.
            1. **인증**: API 키 → **Entra ID**(`az login` 한 계정 또는 에이전트 ID). 호출하는 쪽에 **Foundry User 역할**이 필요합니다(앱이 VM 에서 돈다면 그 VM 의 관리 ID 에 같은 역할을 줍니다 — 이 가이드는 노트북의 `az login` 계정으로만 확인했습니다). 이 실습은 키를 쓰지 않았습니다.
            2. **호출**: `chat.completions.create(model=배포 이름)` → **에이전트를 대상으로 하는 클라이언트**(`get_openai_client(agent_name=…)`)의 `responses.create(…)` (Chat Completions 와 Responses 는 모델을 부르는 두 가지 호출 규격입니다 — [용어 사전](#terms))
            3. **응답**: `choices[0]…` · `usage.prompt_tokens` → `output_text` · `usage.input_tokens` / `usage.output_tokens`
            4. **모델 · 지시문 · 도구**: 요청마다 넘기던 것 → **에이전트 정의**(`azure.yaml`)에 고정
            5. **실패 처리**: 에이전트 호출은 실행이 실패해도 **HTTP 200** 으로 돌아오고 응답의 `status` 가 `failed` 일 수 있습니다. 기존의 `try/except` 만으로는 부족하고 **`status` 도 확인**해야 합니다(D2 · C7).

            **그대로인 것**: 요청 ID 를 서버 기록과 짝짓는 역할은 `x-ms-client-request-id` · `apim-request-id` 대신 **`traceparent` 헤더의 trace_id**(서버의 `operation_Id`)가 맡습니다(C4 에서 확인). timeout · 재시도 같은 **클라이언트 설정은 계속 앱이 책임집니다.** 다만 기존 값이 **자동으로 넘어오지는 않습니다** — 위 코드 비교에서 ‘변경 후’에는 둘 다 없고, SDK 기본값(429 뒤 최대 2회 재시도)이 동작하는 것을 C7 에서 확인했습니다. 에이전트 클라이언트에 필요한 값을 다시 정하고 동작을 확인하세요(설정 방법은 이번에 따로 검증하지 않았습니다).
            """
        )
        + md("**전환 작업 순서(예시 — 팀 사정에 맞게 조정)**: ① 에이전트 정의를 만들고 `azd up`(A2 의 방식) → ② 호출부 · 응답 읽는 부분 교체 → ③ 요청별 옵션을 에이전트 정의로 옮기기(**가장 불확실** — 아래 표의 ‘불가’ 항목은 시범에서 확인) → ④ 키를 Entra ID 인증으로 바꾸고 호출하는 쪽에 Foundry User 역할 부여 → ⑤ 앱 최소 기록(C7) 추가. 작업량은 호출 지점 수와 쓰는 요청 옵션에 따라 달라지며 이 가이드는 시간을 측정하지 않았습니다 — 호출 지점이 적고 ‘불가’ 항목을 쓰지 않는다면 호출부 교체 중심의 작업이 됩니다(추정).")
        + md("#### 다. 요청마다 정하던 설정은 어떻게 되나요 — 에이전트를 지정하면 일부는 쓸 수 없습니다")
        + p1_tbl
        + md("**헷갈리기 쉬운 점** — ‘system 메시지’는 **가능**한데 ‘instructions’는 **불가**입니다. system 메시지는 **대화 입력(`input`)의 한 항목**으로 들어가므로 허용되고, `instructions` 는 **에이전트에 이미 정의된 지시문을 요청이 덮어쓰려는 것**이라 거절되는 것으로 이해하면 쉽습니다(거절 메시지는 ‘에이전트를 지정했을 때는 허용되지 않음’ 한 가지뿐이라 이 설명은 추정입니다). 지시문 · 모델 · 도구를 바꾸려면 **에이전트 정의를 바꿔 다시 배포**합니다.")
        + call(
            "warn",
            "불가 항목은 이렇게 거절됩니다",
            """
            HTTP **400 `invalid_payload`** — 메시지는 ‘Not allowed when agent is specified’(에이전트를 지정했을 때는 허용되지 않음)입니다. 같은 요청을 **에이전트 없이 모델에 직접** 보내면 모두 받아들여졌습니다.
            **에이전트 정의가 같은 설정(temperature 등)을 지원하는지는 이번에 확인하지 못했습니다.** 시범(PoC)에서 확인하세요. 스트리밍 첫 토큰 시간은 각 1회 측정이라 참고용입니다.
            """,
        )
        + call(
            "tip",
            "전환 후보인지 판단하는 체크리스트",
            """
            내 앱의 모델 호출을 에이전트 호출로 바꿀 수 있는지, 아래 네 가지를 차례로 확인하세요(‘다’ · ‘라’ 는 이 장의 소제목입니다).
            1. 요청마다 넘기는 **temperature · tools · JSON 모드 · reasoning** 이 없거나, 에이전트 정의로 옮길 수 있는가? (위 ‘다’ 의 표 — 옮길 수 있는지는 시범에서 확인)
            2. 응답을 쓰는 코드를 Responses 형식(`output_text` · `usage.input_tokens`)에 맞게 고칠 수 있는가?
            3. 인증을 API 키에서 **Entra ID**(Foundry User 역할)로 바꿀 수 있는가?
            4. 기존 AOAI 에 **private endpoint** 가 있다면 아래 ‘라’ 의 절차로 전환할 수 있는가?
            **모두 ‘예’** 이면 전환 후보이고, **하나라도 ‘아니오’** 이면 그 호출은 지금 방식을 유지하고 앱 · VM 쪽에 로그를 더하는 방식(가이드 1)을 씁니다. 앱 전체 기준은 [E1](#e1)에 있습니다.
            """,
        )
        + md("#### 라. 인프라 쪽 전환 — 문서 기준 (이번에 검증하지 않음)")
        + md(
            """
            - 기존 AOAI 리소스를 Foundry 리소스로 **업그레이드**하면 엔드포인트 · 키 · 네트워크 설정이 유지됩니다(Microsoft Learn ‘Upgrade Azure OpenAI to Microsoft Foundry’, 2026-08-19).
            - 기존 **private endpoint**(인터넷이 아닌 사설 주소로만 서비스에 접속하게 하는 연결)가 있으면 포털 업그레이드가 되지 않습니다. 삭제 후 다시 만들거나 **Bicep/Terraform**(Azure 리소스를 코드로 만드는 도구)으로 해야 하고, 그 사설 주소로 이름을 풀어 주는 **DNS zone** 도 추가해야 합니다.
            - Agent Service 는 **리전별 제공 범위**가 다릅니다(이번에는 Korea Central 에서 확인).
            - 모델 호출 한도(쿼터, 분당 토큰)는 **모델 배포 단위**입니다(문서 기준). 이 가이드의 429 도 작은 배포 용량에서 생겼습니다(C7).
            """
        ),
        scope="read",
    )


SKETCH = '''import json, secrets, time

def call_agent(client, prompt, conversation=None):
    """에이전트를 한 번 부르고, 성공 · 실패(예외 포함)와 관계없이 JSON 한 줄을 남깁니다."""
    trace_id = secrets.token_hex(16)                 # 서버 기록의 operation_Id 와 1:1 로 짝지을 키
    rec = {"trace_id": trace_id, "status": None, "response_id": None, "error": None}
    options = {"conversation": conversation} if conversation else {}
    t0 = time.perf_counter()
    try:
        response = client.responses.create(
            input=prompt,
            extra_headers={"traceparent": f"00-{trace_id}-{secrets.token_hex(8)}-01"},
            **options,
        )
        rec.update(status=response.status, response_id=response.id,     # completed · failed · incomplete
                   error=response.error.message[:80] if response.error else None)
        return response
    except Exception as e:                           # HTTP 400 · 429(재시도 후에도 실패) · timeout … 응답을 받지 못한 호출
        rec.update(status="exception", error=type(e).__name__)
        raise                                        # 앱의 기존 오류 처리는 그대로 둡니다
    finally:
        rec["client_ms"] = round((time.perf_counter() - t0) * 1000)     # 클라이언트가 잰 총 시간
        print(json.dumps(rec, ensure_ascii=False))   # 운영에서는 앱 로그 · Application Insights 로 보냅니다'''


def build_c7():
    e3 = e3_rows()
    first = e3[0]
    rest = e3[1:]
    diffs = [int(r[4]) for r in rest]
    lo, hi = min(diffs), max(diffs)
    t3 = table(
        ["호출 (trace 앞 8자)", "클라이언트가 잰 시간(ms)", "서버 invoke_agent(ms)", "서버 모델 호출 chat(ms)", "차이(클라이언트 − 서버)"],
        [[Raw(f"<code>{r[0]}</code>"), r[1], r[2], r[3], Raw(f"<b>{r[4]}</b>")] for r in e3],
    )
    e2 = e2_rows()
    log_line, wait_s = retry_log_line()
    d = e2_direct()
    slow_direct = sum(1 for x in d["direct"] if x >= 4000)
    first_e2 = e2[0]
    ok_ms = re.search(r"성공 (\d+)ms", first_e2[3][1]).group(1)
    t2_rows = []
    for tr, cms, res, spans in e2:
        t2_rows.append([Raw(f"<code>{tr}</code>"), f"{cms:,}", res, Raw("<br>".join(esc(s) for s in spans))])
    t2 = table(["호출", "클라이언트 ms", "클라이언트 결과", "서버 invoke_agent 스팬 (UTC 시각 · 결과 · 시간)"], t2_rows)

    rec_line = None
    for ln in (expected("B2") or "").split("\n"):
        if ln.startswith("{"):
            rec_line = ln
            break
    assert rec_line
    import json

    j = json.loads(rec_line)
    rec_show = (
        '{"agent": "%s", "i": %s, "ms": %s, "status": "%s",\n "response_id": "%s…", "trace_id": "%s…",\n "input_tokens": %s, "output_tokens": %s, "error": null}'
        % (j["agent"], j["i"], j["ms"], j["status"], j["response_id"][:12], j["trace_id"][:8], j["input_tokens"], j["output_tokens"])
    )

    return step(
        "c7",
        "앱에서 본 시간 vs 서버에서 본 시간 — 앱 최소 기록",
        "C7",
        "읽는 단계 · 실행하는 명령 없음 · 2026-10-24 실측(노트북 → Korea Central)",
        brief(
            what="같은 호출을 **클라이언트(앱)가 잰 시간**과 **서버 트레이스가 잰 시간**으로 비교하고, 서버 트레이스에 **없는 시간**과 이를 메우는 **앱 최소 기록**을 설명합니다.",
            why="서버(에이전트 · 모델)가 정상이어도 **사용자는 느리다고 느낄 수 있습니다.** 그 차이가 어디서 생기는지는 서버 트레이스만으로는 알 수 없어서, 앱 쪽에도 호출 1건당 한 줄의 기록이 필요합니다.",
            result="클라이언트 − 서버 시간 차(표 1), 429 후 재시도 대기 사례(표 2), 앱 최소 기록에 담을 4가지.",
            apply="내 앱의 에이전트 호출부에 **호출 1건당 한 줄**을 남기세요(약 10~15줄, 추정). `invoke_agents.py` 가 출력하는 JSON 한 줄이 그 예이고, 아래 ③ 에 **예외까지 남기는 스케치**가 있습니다.",
        )
        + md("#### 표 1 · 같은 호출을 클라이언트와 서버가 잰 시간")
        + t3
        + md(
            f"""
            - **차이(마지막 열)** = 앱 · SDK · 인증 · 네트워크에서 쓴 시간(‘요청 한 건의 시간’ 그림의 **① 앱 · SDK · 인증 + ② 네트워크**)이며 **서버 트레이스에는 없습니다.** 재시도가 없었던 호출 기준이고, 재시도 대기 · 호스티드의 cold start 는 아래에서 따로 봅니다.
            - 표의 ‘서버 invoke_agent’ · ‘서버 chat’ 은 각 호출의 trace_id 로 찾은 **`invoke_agent` · `chat` 스팬의 시간**입니다(호출한 에이전트 종류는 구분해 적지 않았습니다). 호스티드 에이전트의 cold start 시간은 이 `invoke_agent` 시간에 들어 있지 않습니다(C2).
            - 새 클라이언트의 **첫 호출을 뺀 {len(rest)}건은 {lo}~{hi}ms**, **첫 호출은 {int(first[4]):,}ms** 였습니다(연결 · 토큰 준비가 포함된 것으로 추정).
            - **노트북 → Korea Central** 에서 잰 값입니다. Azure VM 에서 호출하면 값이 달라질 수 있습니다.
            """
        )
        + md("#### 표 2 · 429(한도 초과) 뒤 SDK 재시도 — 서버에는 1ms 스팬뿐")
        + t2
        + out(log_line, label="SDK 로그 (환경변수 OPENAI_LOG=info 를 켜고 실행한 호출)", read=f"SDK 가 429 를 받고 **약 {wait_s:.1f}초 기다렸다가 다시 보낸** 기록입니다(2회까지 재시도). 이 대기는 클라이언트에서만 보입니다.")
        + md(
            f"""
            - 표의 **두 번째 행**은 재시도 2번(약 5초 · 6초 대기) 끝에도 429 로 실패해 `RateLimitError` 가 난 경우입니다. 클라이언트는 {e2[1][1]:,}ms 를 기다렸지만 서버 스팬은 1ms 짜리 실패 3건뿐입니다. 한도가 큰 배포에서는 재현되지 않을 수 있습니다.
            - 서버에는 **실패 스팬(1ms)** 과 **성공 스팬({ok_ms}ms)** 만 있고, 둘 사이 **약 {wait_s:.1f}초(재시도 대기)** 는 서버 트레이스에 없습니다. 그래서 클라이언트는 {first_e2[1]:,}ms 를 느꼈습니다.
            - 이 429 는 **실습 배포의 용량(10 단위)이 작아서** 생긴 것으로 보입니다(분당 토큰 한도인지 분당 요청 한도인지는 확인하지 않았습니다). 같은 시간대에 **모델을 직접 호출**해도 10회 중 {slow_direct}회가 약 5초 걸렸습니다.
            - **시각 읽기**: 위 SDK 로그의 시각(`16:51`)은 이 노트북의 현지 시각(KST)이고, 표 속 서버 스팬의 시각(`07:51`)은 UTC 입니다. 같은 순간입니다(KST = UTC + 9시간).
            - **시작 전에 거절된 호출**은 서버 트레이스에 **흔적이 없었습니다.** 확인한 것은 ‘없는 모델 배포’로 만든 에이전트를 부른 경우(404)입니다. 요청별 설정을 넣었다가 400 으로 거절된 호출이 트레이스에 남는지는 확인하지 못했습니다.
            """
        )
        + md("#### 앱 최소 기록 — 호출 1건당 한 줄에 남길 것")
        + md(
            """
            1. **`trace_id`** — 앱이 직접 만들어 `traceparent` 헤더로 보냅니다. 서버 기록의 `operation_Id` 와 **1:1** 로 짝지어집니다.
            2. **`client_ms`** — 호출 전 · 후 시간 차(`invoke_agents.py` 의 출력에서는 `ms` 라는 이름). 여기서 서버 `invoke_agent` 시간을 빼면 **서버 트레이스가 설명하지 못하는 시간**(앱 → 에이전트 구간 · 재시도 대기 등)입니다. 재시도가 있었다면 한 `trace_id` 에 `invoke_agent` 스팬이 여러 개이니 모두 합쳐서 빼야 합니다.
            3. **`status` · `error`** — `failed` · timeout · 429. **거절된 호출은 이 줄이 유일한 기록**입니다. 호출이 **예외로 끝나는 경우**도 한 줄을 남겨야 하므로 `try/except` 가 필요합니다(아래 스케치).
            4. **재시도** — SDK 로그(`OPENAI_LOG=info`)로 보거나, 재시도를 끄고(`max_retries=0`) 시도마다 한 줄씩 기록합니다(가이드 1 의 R3 방식).
            """
        )
        + out(
            rec_show,
            label="예시 — invoke_agents.py 의 출력 한 줄 (B2 의 실제 출력, 일부 줄임)",
            read="이미 `ms`(클라이언트가 잰 시간 = 위의 `client_ms`) · `status` · `trace_id` · `response_id` · 토큰 수 · `error` 가 있습니다. **재시도 횟수만 빠져 있으며**, 이 스크립트는 **예외로 끝난 호출은 기록하지 못합니다**(B2 설명). 예외까지 기록하는 코드는 아래 스케치를 참고하세요.",
        )
        + md("**예외까지 남기는 앱 최소 기록 — 미검증 스케치**입니다. `invoke_agents.py` 를 바탕으로 한 설명용 코드이며, 구문과 흐름(정상 · `failed` · 예외)은 가짜 클라이언트로 점검했지만 **실제 Foundry 호출로는 실행해 검증하지 않았습니다.** 스케치 전체는 호출 코드까지 합쳐 약 20줄이고, 기존 호출 위에 **추가되는 줄은 약 10~15줄**입니다. 내 앱에 맞게 고쳐 쓰세요.")
        + walk(
            SKETCH,
            [
                ("import json", "함수 시작 — 호출마다 이름표 만들기", "`call_agent(client, prompt, conversation)` 은 **에이전트를 한 번 부르는 함수**입니다. `trace_id = secrets.token_hex(16)` 로 이 호출의 이름표를 만들고, 기록용 사전 `rec` 를 준비합니다(`status` · `response_id` · `error` 는 아직 비어 있음). `conversation` 을 넘기면 같은 대화를 이어 갑니다."),
                ("t0 = time.perf_counter()", "시간 재기 시작 · 호출 — traceparent 로 trace_id 전달", "`t0` 에 시작 시각을 고정밀 타이머로 저장하고, `try:` 안에서 `client.responses.create(…)` 로 에이전트를 부릅니다. `extra_headers` 의 `traceparent` 에 trace_id 를 실어 보내므로 **서버 기록의 `operation_Id` 가 이 `trace_id` 와 같아집니다.**"),
                ("rec.update(status=response.status", "정상 응답 — status 를 기록", "응답이 돌아오면 `status`(`completed` · `failed` · `incomplete`)와 `response_id`, 오류 메시지를 `rec` 에 담고 응답을 그대로 돌려줍니다. **`failed` 여도 여기까지 오므로** `status` 를 꼭 남깁니다(HTTP 200 이어도 실패일 수 있음)."),
                ("except Exception", "예외 — 응답을 받지 못한 호출을 기록", "HTTP 400 · 429(재시도 후에도 실패) · timeout 같은 **예외**는 여기로 옵니다. `status` 를 `exception` 으로, `error` 에 예외 이름을 담고 **`raise` 로 예외를 그대로 다시 던져** 앱의 기존 오류 처리가 달라지지 않게 합니다."),
                ("finally:", "마무리 — 총 시간과 JSON 한 줄", "`finally` 는 **성공이든 실패든 항상 실행**됩니다. 여기서 `client_ms`(클라이언트가 잰 총 시간)를 계산하고, `rec` 를 **JSON 한 줄로 출력**합니다. 운영에서는 `print` 대신 앱 로그나 Application Insights 로 보냅니다."),
            ],
            cap="앱 최소 기록 스케치 — 성공 · 실패 · 예외를 모두 한 줄로 (설명용 · 미검증 · 실행 블록 아님)",
            lang="python",
            nocopy=True,
        )
        + out(
            """{"trace_id": "9f1c…", "status": "completed", "response_id": "resp_…", "error": null, "client_ms": 1213}
{"trace_id": "4be0…", "status": "failed", "response_id": "caresp_…", "error": "An internal server error occurred.", "client_ms": 9100}
{"trace_id": "c7a2…", "status": "exception", "response_id": null, "error": "RateLimitError", "client_ms": 11405}""",
            label="출력 예 (설명용 — 가짜 클라이언트로 만든 모양이며 실제 측정값이 아닙니다)",
            read="첫 줄은 정상, 둘째 줄은 **HTTP 200 이지만 `status` 가 `failed`**(D2 에서 본 모양), 셋째 줄은 **응답을 받지 못하고 예외**로 끝난 호출입니다. 이 한 줄들을 앱 로그에 남기면 ‘어느 호출이 왜 느렸거나 실패했는지’를 `trace_id` 로 서버 기록과 이어 볼 수 있습니다.",
        )
        + md("**어디로 보내나** — `print` 대신 앱이 이미 쓰는 로그 경로에 한 줄을 남깁니다. 예: `logging.getLogger(\"app\").info(json.dumps(rec, ensure_ascii=False))`. 앱 로그를 Application Insights 나 로그 수집기로 모으고 있다면 그 경로를 그대로 쓰세요.")
        + md("**차이(`client_ms` − 서버 `invoke_agent`) 읽는 법**")
        + table(
            ["보이는 모양", "뜻", "할 일"],
            [
                [f"차이가 약 {lo}~{hi}ms", "정상 — 앱 · SDK · 인증 · 네트워크 (이 가이드 실측)", "평소 기준선으로 기록"],
                [f"새 클라이언트의 첫 호출만 크다(실측 {int(first[4]):,}ms)", "연결 · 토큰 준비", "정상 — 첫 호출만 보고 판단하지 않기"],
                ["차이가 1초 이상 반복", "앱 · 네트워크 · 인증 · 재시도 대기 의심", "`OPENAI_LOG=info` 로 재시도 로그 확인 · 앱 쪽 구간 점검"],
                ["`status: failed`", "에이전트 실행 실패(HTTP 는 200)", "서버 트레이스에서 원인 확인(D3)"],
                ["`status: exception`", "응답을 받지 못함(400 · 429 · timeout 등)", "`error` 이름으로 원인 구분"],
            ],
        )
        + code(
            "OPENAI_LOG=info python invoke_agents.py report-prompt-agent 1 short new",
            cap="(참고 — 실행 블록 아님) SDK 의 재시도 로그를 보려면 환경변수 OPENAI_LOG=info 를 켜고 실행합니다",
            lang="bash",
        )
        + call(
            "info",
            "선택 · 한계",
            """
            - **OTel 자동 계측**으로 앱 스팬을 같은 trace 에 붙여 한 화면에서 볼 수도 있습니다. 단, 같은 Application Insights 로 보내야 하고 `traceparent` **자동 전파는 이번에 확인하지 못했습니다.**
            - **앱이 도는 VM · 경로**가 의심되면 앱 VM 에 성능 카운터 수집 · 네트워크 경로 로그 · probe 를 따로 둡니다(가이드 1 의 R5 · R6 · R7 방식).
            - 이 장의 값은 **노트북에서 잰 단일 환경 값**입니다. 운영 부하와 Azure VM 에서는 다를 수 있습니다.
            """,
        )
        + md("#### 정리 — 세 가지만 기억하세요")
        + md(
            """
            1. **서버 트레이스는 서버 쪽만** 보여 줍니다. 앱 · SDK · 네트워크 · 재시도 대기 · 시작 전에 거절된 호출은 보이지 않습니다.
            2. 그래서 앱은 **호출 1건당 한 줄**(`trace_id` · `client_ms` · `status` · `error`)을 남기고, **예외도 `try/except` 로 잡아** 한 줄로 남겨야 합니다.
            3. 이 한 줄의 `trace_id` 로 서버 기록 전체를 찾고, `client_ms` 에서 서버 `invoke_agent` 시간을 뺀 값으로 **서버 트레이스에 없는 시간**(앱 · SDK · 네트워크 · 재시도 대기 등)을 계산합니다.
            """
        )
        + md("#### 직접 해 보기 — 이 장의 표 1 을 내 호출로 만들어 보기")
        + md(
            """
            1. B2 에서 만든 `calls.jsonl` 에서 한 줄을 골라 **`ms`**(클라이언트가 잰 시간)와 **`trace_id`** 를 적어 둡니다.
            2. 그 `trace_id` 로 [C4](#c4) 의 첫 쿼리(`trace_by_id`)를 실행합니다. **구간 1 의 `TID=` 줄을 `TID=<방금 적어 둔 trace_id>` 로 바꾼 뒤** 전체를 실행하고, 결과에서 **`invoke_agent` 스팬의 시간**을 찾습니다(프롬프트 에이전트는 역할 `responsesapi`, 호스티드는 역할 `agentsv2` 요청 행).
            3. **`ms − invoke_agent`** 가 그 호출에서 **서버 트레이스에 없는 시간**(앱 · SDK · 인증 · 네트워크, 그리고 재시도 대기)입니다. 한 `trace_id` 에 `invoke_agent` 스팬이 여러 개면(재시도) 모두 합쳐서 빼세요. 호스티드 에이전트의 cold start 호출이라면 서버 `invoke_agent` 시간에 cold start 가 빠져 있으므로 **`ms − invoke_agent` 에 cold start 시간이 섞여 나옵니다**(cold start 시간은 C2 · C3 에서 따로 구합니다).
            """
        ),
        scope="read",
    )
