"""
数据库连接配置
使用 SQLAlchemy 2.0 风格
"""

import re
from typing import Generator

from sqlalchemy import create_engine, event, MetaData, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Schema 名称安全校验
_SCHEMA_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def _validate_schema_name(schema_name: str) -> str:
    """校验 schema 名称，避免 SQL 注入"""
    if not _SCHEMA_PATTERN.match(schema_name):
        raise ValueError(
            f"无效的数据库 schema 名称: {schema_name}. "
            "仅允许字母、数字和下划线，且不能以数字开头。"
        )
    return schema_name


DB_SCHEMA = _validate_schema_name(settings.USER_DB_SCHEMA)

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,  # 自动检测断开的连接
    echo=settings.DEBUG  # 调试模式下打印 SQL
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 声明基类
Base = declarative_base(metadata=MetaData(schema=DB_SCHEMA))


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话的依赖注入"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话异常: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def ensure_schema_exists() -> None:
    """确保业务 schema 存在"""
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{DB_SCHEMA}"'))


# 连接事件：设置时区
@event.listens_for(engine, "connect")
def set_timezone(dbapi_connection, connection_record):
    """设置数据库连接时区与默认 schema"""
    cursor = dbapi_connection.cursor()
    cursor.execute("SET timezone = %s", (settings.TZ,))
    cursor.execute(f'SET search_path TO "{DB_SCHEMA}", public')
    cursor.close()
