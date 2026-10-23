#!/bin/bash
# R7_aoai_probe.sh - 1분마다 실행하는 합성 probe (VM 안/밖 어디서나 같은 스크립트 사용)
#   (1) AOAI 소형 호출(max_tokens=1)  (2) VM 로컬 앱 URL  → 구간별 시간을 JSON 1줄로 기록
#   기록 위치: syslog(local5) → Azure Monitor Agent(R5) → Log Analytics 'Syslog' 테이블, 그리고 표준 출력
#   필요: curl(7.29 이상), awk, logger  |  설정: /etc/aoai-probe.env (R7_aoai-probe.env.sample 참고)
set -u
. "${PROBE_ENV:-/etc/aoai-probe.env}"
ROLE="${PROBE_ROLE:-vm-inside}"; SLOW_MS="${SLOW_MS:-8000}"; API_VER="${AOAI_API_VERSION:-2024-10-21}"

emit() {  # $1=대상  $2=curl 종료코드  $3=write-out 문자열 (curl 시간값은 누적이므로 차이를 구해 구간별로 기록)
  IFS="|" read -r dns tcp tls ttfb total code ip conns <<<"$3"
  local line
  line=$(awk -v role="$ROLE" -v tgt="$1" -v rc="$2" -v code="${code:-0}" -v ip="${ip:-}" -v cn="${conns:-0}" \
    -v d="${dns:-0}" -v c="${tcp:-0}" -v t="${tls:-0}" -v f="${ttfb:-0}" -v T="${total:-0}" 'BEGIN{
      tcp_ms = (c > d) ? c - d : 0; tls_ms = (t > c) ? t - c : 0; base = (t > 0) ? t : c;
      wait_ms = (f > base) ? f - base : ((f == 0 && T > base) ? T - base : 0);
      printf "{\"event\":\"aoai_probe\",\"role\":\"%s\",\"target\":\"%s\",\"rc\":%d,\"code\":\"%s\",\"dns_ms\":%d,\"tcp_ms\":%d,\"tls_ms\":%d,\"wait_ms\":%d,\"total_ms\":%d,\"ip\":\"%s\",\"new_conns\":%d}",
             role, tgt, rc, code, d*1000, tcp_ms*1000, tls_ms*1000, wait_ms*1000, T*1000, ip, cn }')
  echo "$line"; logger -t aoai-probe -p local5.info -- "$line"
  TOTAL_MS=$(awk -v T="${total:-0}" 'BEGIN{printf "%d", T*1000}')
}

# 인증: API 키가 없으면 VM의 Managed Identity 토큰 사용 (역할: Cognitive Services OpenAI User)
if [ -n "${AOAI_API_KEY:-}" ]; then AUTH=(-H "api-key: ${AOAI_API_KEY}")
else AUTH=(-H "Authorization: Bearer $(curl -s --max-time 5 -H Metadata:true "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://cognitiveservices.azure.com" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')"); fi

slow=0
# AOAI 소형 호출 — 같은 endpoint·deployment, max_tokens=1 (curl 시간값은 DNS→TCP→TLS 누적)
# >>> slide:probe-core
# --http1.1: HTTP/2 에서는 curl 의 첫 바이트(wait) 시간이 부정확합니다
WF='%{time_namelookup}|%{time_connect}|%{time_appconnect}|'
WF+='%{time_starttransfer}|%{time_total}|%{http_code}|%{remote_ip}|%{num_connects}'
BASE="${AOAI_ENDPOINT%/}/openai/deployments/${AOAI_DEPLOYMENT}"
URL="$BASE/chat/completions?api-version=${API_VER}"
out=$(curl -sS --http1.1 -o /dev/null --max-time "${PROBE_TIMEOUT:-60}" -X POST "$URL" \
  "${AUTH[@]}" -H "Content-Type: application/json" \
  -H "x-ms-client-request-id: probe-$(date +%s%N)" \
  -d '{"messages":[{"role":"user","content":"ping"}],"max_tokens":1}' \
  -w "$WF" 2>/dev/null); rc=$?
emit aoai "$rc" "$out"
# <<< slide:probe-core
{ [ "$rc" -ne 0 ] || [ "$TOTAL_MS" -ge "$SLOW_MS" ]; } && slow=1

# (2) VM 로컬 앱 URL (APP_URLS 에 공백으로 구분해 지정; VM 밖 probe 에서는 비워 둡니다)
for u in ${APP_URLS:-}; do
  out=$(curl -sS -o /dev/null --max-time 30 "$u" -w "$WF" 2>/dev/null); rc=$?
  emit "app:${u##*:}" "$rc" "$out"; { [ "$rc" -ne 0 ] || [ "$TOTAL_MS" -ge "$SLOW_MS" ]; } && slow=1
done

# 느리거나 실패했으면 5분에 한 번만 VM 상태 스냅샷 저장 (별도 transient 서비스)
SNAP="${SNAPSHOT:-/opt/aoai-probe/aoai_snapshot.sh}"
if [ "$slow" = 1 ] && [ -x "$SNAP" ] && [ -z "$(find /tmp/.aoai_snap -mmin -5 2>/dev/null)" ]; then
  touch /tmp/.aoai_snap   # systemd-run: 타이머 서비스가 끝나도 스냅샷이 중단되지 않게 별도 서비스로 실행
  systemd-run --quiet --no-block --collect "$SNAP" 2>/dev/null || { "$SNAP" >/dev/null 2>&1 & }
fi
