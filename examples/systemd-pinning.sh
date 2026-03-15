#!/bin/bash
# перенос процессов в control-plane
SERVICES=(bird bird6 accel-ppp ssh sshd snmpd systemd-journald rsyslog cron)
for SVC in "${SERVICES[@]}"; do
    systemctl set-property "$SVC".service AllowedCPUs=8 9 10 11 || true
done

