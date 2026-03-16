#!/bin/bash
SERVICES=(bird bird6 accel-ppp ssh sshd snmpd systemd-journald rsyslog cron)
for SVC in "${SERVICES[@]}"; do
    systemctl set-property "$SVC".service AllowedCPUs=2 3 || true
done
