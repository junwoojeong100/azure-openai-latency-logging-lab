#!/usr/bin/env python3
# docs-as-tests: Foundry 가이드 HTML 안의 data-run 코드 블록을 문서 순서대로 실행해, 가이드가 실제로 동작하는지 확인한다.
#
# 사용:  SUB=<구독 ID> MAIL=<메일> [REPO=<저장소 경로 또는 URL>] [WORK=/tmp/fdlab-run] [ORDER=A0,A1,...] \
#        python3 run_foundry_html.py <html> [단계,단계...]
#
# - 새 리소스 그룹(rg-<azd 환경 이름>)이 만들어지고 비용이 듭니다. 마지막 정리(E2)는 data-skip 이라 실행하지 않습니다.
# - az 로 로그인되어 있어야 합니다. azd 는 WORK 안의 별도 설정 폴더(AZD_CONFIG_DIR)에서 az 로그인을 재사용하므로 사용자의 azd 설정은 바뀌지 않습니다.
# - 블록마다 출력을 WORK/evidence/blocks/<단계>[a|b|…].txt 로 저장합니다 (구독 ID · 메일 등은 가림).
import html
import json
import os
import re
import subprocess
import sys
import time

HTML = sys.argv[1]
WORK = os.environ.get("WORK", "/tmp/fdlab-run")
SUB = os.environ["SUB"]
MAIL = os.environ["MAIL"]
REPO = os.environ.get("REPO")
ONLY = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
ORDER = os.environ.get("ORDER")
for d in ("evidence/blocks", "stages", "azdcfg"):
    os.makedirs(f"{WORK}/{d}", exist_ok=True)

src = open(HTML, encoding="utf-8").read()
blocks = re.findall(r'<pre class="code" data-run="([^"]+)"( data-skip="1")?><code>(.*?)</code></pre>', src, re.S)
stages = {}
order = []
for sid, skip, body in blocks:
    if skip:
        continue
    code = html.unescape(re.sub(r"<[^>]+>", "", body)).replace("<구독 ID>", SUB).replace("<알림 받을 이메일>", MAIL)
    code = re.sub(r"^(az login|azd auth login)\b.*$", "true", code, flags=re.M)
    if REPO:
        code = code.replace("https://github.com/junwoojeong100/azure-openai-latency-logging-lab.git", REPO + " azure-openai-latency-logging-lab")
    if sid not in stages:
        stages[sid] = []
        order.append(sid)
    stages[sid].append(code)
if ORDER:
    order = ORDER.split(",")

env_base = {
    **os.environ,
    "AZD_CONFIG_DIR": f"{WORK}/azdcfg",
    "AZD_NON_INTERACTIVE": "true",
    "PYTHONUNBUFFERED": "1",
}
subprocess.run(["azd", "config", "set", "auth.useAzCliAuth", "true"], env=env_base, capture_output=True)

secrets = {SUB: "<구독 ID>", MAIL: "<메일>"}
try:
    tenant = subprocess.run(["az", "account", "show", "--query", "tenantId", "-o", "tsv"], capture_output=True, text=True).stdout.strip()
    upn = subprocess.run(["az", "ad", "signed-in-user", "show", "--query", "userPrincipalName", "-o", "tsv"], capture_output=True, text=True).stdout.strip()
    oid = subprocess.run(["az", "ad", "signed-in-user", "show", "--query", "id", "-o", "tsv"], capture_output=True, text=True).stdout.strip()
    for v, r in ((tenant, "<테넌트 ID>"), (upn, "<사용자>"), (oid, "<사용자 ID>")):
        if v:
            secrets[v] = r
except Exception:
    pass


def sanitize(text):
    for k, v in secrets.items():
        text = text.replace(k, v)
    text = text.replace(os.path.expanduser("~"), "~").replace("/private/tmp", "/tmp")
    text = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "<guid>", text)
    return text


PREAMBLE = f"""cd {WORK}
if [ -d azure-openai-latency-logging-lab/foundry ]; then cd azure-openai-latency-logging-lab/foundry; fi
[ -f foundry.env ] && set -a && . ./foundry.env && set +a
[ -d .venv ] && . .venv/bin/activate
"""

log = open(f"{WORK}/progress.log", "a", buffering=1)


def say(m):
    log.write(time.strftime("%H:%M:%S ") + m + "\n")


summary = {}
for i, sid in enumerate(order):
    if ONLY and sid not in ONLY:
        continue
    codes = stages[sid]
    parts = []
    for n, c in enumerate(codes):
        parts.append(f'echo "@@BLOCK {n}"\n{c}\n')
    script = PREAMBLE + "\n".join(parts)
    path = f"{WORK}/stages/{i:02d}_{sid}.sh"
    open(path, "w", encoding="utf-8").write(script)
    say(f"START {sid}")
    t0 = time.time()
    p = subprocess.run(["bash", path], capture_output=True, text=True, timeout=3600, env=env_base)
    dt = time.time() - t0
    out = sanitize(p.stdout)
    err = sanitize(p.stderr)
    open(f"{WORK}/evidence/{i:02d}_{sid}.log", "w", encoding="utf-8").write(out + "\n--- STDERR ---\n" + err)
    chunks = re.split(r"^@@BLOCK (\d+)\n", out, flags=re.M)
    # chunks = ['', '0', text0, '1', text1, ...]
    for k in range(1, len(chunks), 2):
        n = int(chunks[k])
        suffix = "" if len(codes) == 1 else "abcdefgh"[n]
        open(f"{WORK}/evidence/blocks/{sid}{suffix}.txt", "w", encoding="utf-8").write(chunks[k + 1].rstrip("\n") + "\n")
    errs = len(re.findall(r"ERROR|Error:|error:|Traceback|command not found|Failed|failed to", p.stdout + p.stderr))
    summary[sid] = {"rc": p.returncode, "errs": errs, "sec": round(dt)}
    say(f"DONE  {sid} rc={p.returncode} errs={errs} {dt:.0f}s")
json.dump(summary, open(f"{WORK}/evidence/summary.json", "w"), indent=1)
say("ALL STAGES FINISHED")
