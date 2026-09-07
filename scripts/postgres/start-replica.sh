#!/bin/sh
set -eu

DATA_DIR="/var/lib/postgresql/data"

if [ "$(id -u)" = "0" ]; then
  mkdir -p "${DATA_DIR}"
  chown -R postgres:postgres "${DATA_DIR}"
  exec gosu postgres "$0"
fi

if [ ! -s "${DATA_DIR}/PG_VERSION" ]; then
  echo "Initializing replica from primary..."
  rm -rf "${DATA_DIR:?}"/*
  export PGPASSWORD="${POSTGRES_REPLICATION_PASSWORD:?POSTGRES_REPLICATION_PASSWORD is required}"

  until pg_basebackup \
    -h "${POSTGRES_PRIMARY_HOST:-postgres-primary}" \
    -p "${POSTGRES_PRIMARY_PORT:-5432}" \
    -D "${DATA_DIR}" \
    -U "${POSTGRES_REPLICATION_USER:-replicator}" \
    -Fp -Xs -P -R; do
    echo "pg_basebackup failed, retrying in 3s..."
    sleep 3
  done

  chmod 700 "${DATA_DIR}"
fi

exec postgres -c hot_standby=on
