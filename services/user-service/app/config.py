"""
应用配置管理
使用 Pydantic Settings 进行配置验证
"""

import base64
from functools import lru_cache

import httpx
import structlog

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger(__name__)


class Settings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # 服务配置
    SERVICE_NAME: str = "user-service"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8000
    TZ: str = "Asia/Shanghai"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:postgres123@localhost:5432/user_db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    USER_DB_SCHEMA: str = "user_service"

    # JWT 配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS 配置
    CORS_ORIGINS: str = "*"
    
    # 密码配置
    PASSWORD_MIN_LENGTH: int = 6
    PASSWORD_MAX_LENGTH: int = 128

    # Consul 配置中心
    CONSUL_ENABLED: bool = False
    CONSUL_HOST: str = "consul"
    CONSUL_PORT: int = 8500
    CONSUL_SCHEME: str = "http"
    CONSUL_CONFIG_PREFIX: str = "config/user-service"
    CONSUL_TIMEOUT_SECONDS: float = 2.0

    # gRPC 安全配置
    GRPC_PORT: int = 50051
    GRPC_TLS_ENABLED: bool = False
    GRPC_MTLS_ENABLED: bool = False
    GRPC_SERVER_CERT_PATH: str = "/app/certs/server.crt"
    GRPC_SERVER_KEY_PATH: str = "/app/certs/server.key"
    GRPC_CA_CERT_PATH: str = "/app/certs/ca.crt"
    GRPC_CLIENT_CERT_PATH: str = "/app/certs/client.crt"
    GRPC_CLIENT_KEY_PATH: str = "/app/certs/client.key"

    @property
    def cors_origins_list(self) -> list[str]:
        """获取 CORS 源列表"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


def _load_consul_overrides(base_settings: Settings) -> dict[str, str]:
    """从 Consul KV 读取配置覆盖项"""
    if not base_settings.CONSUL_ENABLED:
        return {}

    url = (
        f"{base_settings.CONSUL_SCHEME}://{base_settings.CONSUL_HOST}:"
        f"{base_settings.CONSUL_PORT}/v1/kv/{base_settings.CONSUL_CONFIG_PREFIX}?recurse=true"
    )
    try:
        response = httpx.get(url, timeout=base_settings.CONSUL_TIMEOUT_SECONDS)
        if response.status_code == 404:
            return {}
        response.raise_for_status()
        kv_items = response.json() or []
    except Exception as exc:
        logger.warning(f"从 Consul 加载配置失败，继续使用环境变量配置: {exc}")
        return {}

    prefix = f"{base_settings.CONSUL_CONFIG_PREFIX.rstrip('/')}/"
    overrides: dict[str, str] = {}
    valid_fields = set(Settings.model_fields.keys())
    for item in kv_items:
        key = item.get("Key", "")
        raw_value = item.get("Value")
        if not key.startswith(prefix) or raw_value is None:
            continue

        field_name = key[len(prefix):].strip().upper()
        if field_name not in valid_fields:
            continue

        try:
            overrides[field_name] = base64.b64decode(raw_value).decode("utf-8")
        except Exception:
            continue

    return overrides


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    base_settings = Settings()
    consul_overrides = _load_consul_overrides(base_settings)
    if not consul_overrides:
        return base_settings

    merged = base_settings.model_dump()
    merged.update(consul_overrides)
    return Settings(**merged)


settings = get_settings()
