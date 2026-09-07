#!/bin/sh
set -eu

CONSUL_ADDR="${CONSUL_ADDR:-http://consul:8500}"
PREFIX="${CONSUL_CONFIG_PREFIX:-config/user-service}"

echo "等待 Consul 可用..."
until curl -sf "${CONSUL_ADDR}/v1/status/leader" >/dev/null; do
  sleep 2
done

put_kv() {
  key="$1"
  value="$2"
  curl -sf -X PUT "${CONSUL_ADDR}/v1/kv/${PREFIX}/${key}" -d "${value}" >/dev/null
  echo "已写入配置: ${PREFIX}/${key}"
}

put_kv "LOG_LEVEL" "${LOG_LEVEL:-INFO}"
put_kv "PASSWORD_MIN_LENGTH" "${PASSWORD_MIN_LENGTH:-6}"
put_kv "PASSWORD_MAX_LENGTH" "${PASSWORD_MAX_LENGTH:-128}"
put_kv "DATABASE_POOL_SIZE" "${DATABASE_POOL_SIZE:-5}"
put_kv "DATABASE_MAX_OVERFLOW" "${DATABASE_MAX_OVERFLOW:-10}"
put_kv "DATABASE_POOL_TIMEOUT" "${DATABASE_POOL_TIMEOUT:-30}"
put_kv "USER_DB_SCHEMA" "${USER_DB_SCHEMA:-user_service}"
put_kv "GRPC_TLS_ENABLED" "${GRPC_TLS_ENABLED:-true}"
put_kv "GRPC_MTLS_ENABLED" "${GRPC_MTLS_ENABLED:-false}"

echo "Consul KV 引导完成"
