#!/usr/bin/env python3
# docs-as-tests: HTML 안의 data-run 코드 블록을 문서 순서대로 실행해 실습 가이드가 실제로 동작하는지 확인한다.
# 사용: SUB=<구독 ID> MAIL=<메일> python3 run_html.py <html> [단계,단계...]   (WORK=/tmp/lablog-run 에서 실행, 새 리소스 그룹이 만들어지며 비용이 듭니다)
import re, html, subprocess, time, sys, os
HTML = sys.argv[1]; WORK = os.environ.get("WORK", "/tmp/lablog-run"); os.makedirs(WORK + "/evidence", exist_ok=True); os.makedirs(WORK + "/stages", exist_ok=True)
SUB = os.environ["SUB"]; MAIL = os.environ["MAIL"]
only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
src = open(HTML, encoding="utf-8").read()
# 구간별 해설이 붙은 코드는 한 스크립트가 여러 <pre>(data-part=1,2,…)로 나뉘어 있으므로 이어 붙여 한 블록으로 만든다
blocks = re.findall(r'<pre class="code" data-run="([^"]+)"(?: data-part="(\d+)")?( data-skip="1")?><code>(.*?)</code></pre>', src, re.S)
stages = []
for sid, part, skip, body in blocks:
    if skip: continue
    code = html.unescape(re.sub(r"<[^>]+>", "", body)).replace("<구독 ID>", SUB).replace("<알림 받을 이메일>", MAIL)
    code = re.sub(r"^az login .*$", "true", code, flags=re.M)
    if part and int(part) > 1: stages[-1][1][-1] += "\n" + code
    elif stages and stages[-1][0] == sid: stages[-1][1].append(code)
    else: stages.append([sid, [code]])
log = open(f"{WORK}/progress.log", "a", buffering=1)
def say(m): log.write(time.strftime("%H:%M:%S ") + m + "\n")
b3_done = None
for i, (sid, codes) in enumerate(stages):
    if only and sid not in only: continue
    if sid.startswith("C") and b3_done and not os.environ.get("NOWAIT"):
        target = b3_done + 1800
        if time.time() < target: say("WAIT (로그 수집 대기)"); time.sleep(target - time.time())
    script = f"cd {WORK}\n[ -f lablog.env ] && source lablog.env\n" + "\n".join(codes) + "\n"
    path = f"{WORK}/stages/{i:02d}_{sid}.sh"; open(path, "w", encoding="utf-8").write(script)
    say(f"START {sid}"); t0 = time.time()
    p = subprocess.run(["bash", path], capture_output=True, text=True, timeout=3000)
    open(f"{WORK}/evidence/{i:02d}_{sid}.log", "w", encoding="utf-8").write(p.stdout + "\n--- STDERR ---\n" + p.stderr)
    errs = len(re.findall(r"ERROR|Error:|error:|Traceback|command not found|Failed", p.stdout + p.stderr))
    say(f"DONE  {sid} rc={p.returncode} errs={errs} {time.time()-t0:.0f}s")
    if sid == "B3": b3_done = time.time()
say("ALL STAGES FINISHED")
