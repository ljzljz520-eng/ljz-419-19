#!/bin/sh
set -e

REPL_USER="${POSTGRES_REPLICATION_USER:-replicator}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${REPL_USER}') THEN
        EXECUTE format('CREATE ROLE %I WITH REPLICATION LOGIN PASSWORD %L', '${REPL_USER}', '${POSTGRES_REPLICATION_PASSWORD}');
    ELSE
        EXECUTE format('ALTER ROLE %I WITH REPLICATION LOGIN PASSWORD %L', '${REPL_USER}', '${POSTGRES_REPLICATION_PASSWORD}');
    END IF;
END
\$\$;
EOSQL

echo "host replication ${REPL_USER} 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
echo "host replication ${REPL_USER} ::/0 md5" >> "$PGDATA/pg_hba.conf"
