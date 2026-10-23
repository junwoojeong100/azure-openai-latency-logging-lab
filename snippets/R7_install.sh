#!/bin/bash
# R7_install.sh - probe 설치 (root 권한). 같은 폴더에 R7_* 파일이 있다고 가정합니다.
set -e
install -d /opt/aoai-probe /var/log/aoai-probe
install -m 0755 R7_aoai_probe.sh    /opt/aoai-probe/aoai_probe.sh
install -m 0755 R7_aoai_snapshot.sh /opt/aoai-probe/aoai_snapshot.sh
[ -f /etc/aoai-probe.env ] || install -m 0600 R7_aoai-probe.env.sample /etc/aoai-probe.env   # 설치 후 값을 채우세요
install -m 0644 R7_aoai-probe.service /etc/systemd/system/aoai-probe.service
install -m 0644 R7_aoai-probe.timer   /etc/systemd/system/aoai-probe.timer
systemctl daemon-reload
systemctl enable --now aoai-probe.timer
systemctl list-timers aoai-probe.timer --no-pager
