#!/bin/sh
set -eu

STANDBY_HOST="${POSTGRES_REPLICA_HOST:-postgres-replica}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_NAME="${POSTGRES_DB:-postgres}"

export PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"

# 重试提升从库，避免在主库刚下线时瞬时失败
for _ in $(seq 1 20); do
  if psql -h "${STANDBY_HOST}" -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT pg_promote(wait_seconds => 60);" >/dev/null 2>&1; then
    exit 0
  fi
  sleep 2
done

exit 1
