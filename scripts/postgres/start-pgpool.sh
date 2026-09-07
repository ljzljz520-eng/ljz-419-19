#!/bin/sh
set -eu

# 清理上次异常退出残留的 PID/Socket，避免误判“已有 pgpool 在运行”
rm -f /var/run/pgpool/pgpool.pid
rm -f /var/run/pgpool/.s.PGSQL.*
rm -f /tmp/pgpool_status
rm -f /tmp/.s.PGSQL.*

exec /opt/pgpool-II/bin/start.sh
