#!/bin/bash
# R7_usage.sh - probe 설치·확인 순서 (VM 안과 VM 밖 모두 같은 절차). root 권한(sudo)으로 실행합니다.
# >>> slide:run
sudo bash R7_install.sh                  # 설치 + 1분 타이머 등록
sudo vi /etc/aoai-probe.env              # 엔드포인트·deployment·URL 입력
sudo systemctl start aoai-probe.service  # 1회 실행 → JSON 줄 출력 확인
journalctl -u aoai-probe -n 5 --no-pager # 타이머 실행 결과 확인
# <<< slide:run
