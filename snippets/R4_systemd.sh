#!/bin/bash
# R4_systemd.sh - 앱이 systemd 서비스일 때 환경변수 파일을 연결하는 예시 (서비스 이름은 환경에 맞게 변경)
# >>> slide:systemd
sudo install -D -m 0600 R4_telemetry.env.sample /etc/report-agent/telemetry.env
sudo vi /etc/report-agent/telemetry.env      # 연결 문자열 입력
sudo systemctl edit report-agent             # [Service] EnvironmentFile=… 추가
sudo systemctl restart report-agent
# <<< slide:systemd
