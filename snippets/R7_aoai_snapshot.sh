#!/bin/bash
# R7_aoai_snapshot.sh - 지연 순간의 VM 상태를 한 파일로 저장하고, 요약 1줄을 syslog(local5)로 남깁니다 (읽기 전용 명령만 사용)
#   필요: procps(vmstat, top, ps), iproute(ss, nstat). iostat 은 sysstat 패키지가 있을 때만 사용합니다.
DIR="${SNAP_DIR:-/var/log/aoai-probe}"; mkdir -p "$DIR"; OUT="$DIR/snap-$(date -u +%Y%m%dT%H%M%SZ).txt"
{
  echo "== 시각(UTC)";            date -u +%FT%TZ
  echo "== 부하/메모리";          uptime; free -m
  echo "== vmstat (r=실행 대기, wa=I/O 대기)"; vmstat 1 3
  echo "== CPU 상위 프로세스(순간값, top 2회차)"; top -b -n 2 -d 1 | awk '/^top - /{n++} n==2' | head -14
  echo "== 디스크 I/O";          command -v iostat >/dev/null && iostat -x 1 2 || echo "(sysstat 미설치)"
  echo "== 소켓 요약";            ss -s
  echo "== 443 연결 상세 (rto/rtt/cwnd)"; ss -tin '( dport = :443 )' | head -60
  echo "== TCP 카운터(누적)";     nstat -asz TcpRetransSegs TcpExtTCPTimeouts TcpExtTCPSynRetrans TcpAttemptFails
  echo "== systemd timer";       systemctl list-timers --all --no-pager | head -15
  echo "== 최근 5분 cron 로그";   journalctl -u crond --since "-5 min" --no-pager 2>/dev/null | tail -20
} > "$OUT" 2>&1

# 요약 1줄 → Syslog 테이블에서 시각으로 바로 대조 (r=실행 대기, wa=I/O 대기 %, est443=443 연결 수)
read -r R WA < <(vmstat 1 2 | tail -1 | awk '{print $1, $16}')
EST=$(ss -tn state established '( dport = :443 )' 2>/dev/null | tail -n +2 | wc -l | tr -d ' ')
RETR=$(nstat -az TcpRetransSegs 2>/dev/null | awk '$1=="TcpRetransSegs"{print $2}')
logger -t aoai-snap -p local5.info -- "{\"event\":\"aoai_snapshot\",\"file\":\"$(basename "$OUT")\",\"load1\":\"$(cut -d' ' -f1 /proc/loadavg 2>/dev/null)\",\"runq\":${R:-0},\"iowait_pct\":${WA:-0},\"est443\":$EST,\"tcp_retrans_total\":${RETR:-0}}"
find "$DIR" -name 'snap-*.txt' -mtime +7 -delete      # 7일 지난 스냅샷 정리
