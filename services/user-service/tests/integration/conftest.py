"""
接口集成测试 Fixtures

在本地 PostgreSQL 测试库中初始化和清理测试数据：
- session 级：创建测试 schema 与表结构，全部用例结束后整体删除
- 用例级：每个用例执行前后清空用户表，保证数据隔离、可重复执行

默认连接 localhost 的 user_db_test，可用 DATABASE_URL / USER_DB_SCHEMA 覆盖，
但为防止误删数据，禁止指向非本机数据库。
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres123@localhost:5432/user_db_test",
)
TEST_SCHEMA = os.environ.get("USER_DB_SCHEMA", "user_service_test")

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.utils.security import get_password_hash  # noqa: E402

# 测试账号密码（fixtures 与用例共用）
ADMIN_PASSWORD = "ItAdmin@123"
USER_PASSWORD = "ItUser@123"


def _ensure_local_database() -> None:
    """集成测试会删改数据，禁止指向非本机数据库"""
    host = make_url(TEST_DATABASE_URL).host
    if host not in ("localhost", "127.0.0.1", "::1"):
        pytest.fail(
            f"集成测试数据库必须指向本机，当前 host: {host!r}。"
            "请通过 DATABASE_URL 指定本地测试库。"
        )


@pytest.fixture(scope="session")
def db_engine():
    """初始化测试库表结构，全部用例结束后删除测试 schema"""
    _ensure_local_database()
    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.exec_driver_sql(f'CREATE SCHEMA IF NOT EXISTS "{TEST_SCHEMA}"')
    Base.metadata.create_all(bind=engine)

    yield engine

    with engine.begin() as conn:
        conn.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{TEST_SCHEMA}" CASCADE')
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """每个用例独立的数据库会话，执行前后清空用户表"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    session.execute(User.__table__.delete())
    session.commit()

    yield session

    session.execute(User.__table__.delete())
    session.commit()
    session.close()


@pytest.fixture()
def client(db_session):
    """测试客户端：将 get_db 依赖替换为测试会话，请求直接落到测试库"""
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _create_user(db_session, *, username, email, password, role):
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        nickname=username,
        role=role,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def admin_user(db_session):
    """测试管理员账号"""
    return _create_user(
        db_session,
        username="it_admin",
        email="it_admin@example.com",
        password=ADMIN_PASSWORD,
        role=UserRole.ADMIN,
    )


@pytest.fixture()
def normal_user(db_session):
    """测试普通用户账号"""
    return _create_user(
        db_session,
        username="it_user",
        email="it_user@example.com",
        password=USER_PASSWORD,
        role=UserRole.USER,
    )
