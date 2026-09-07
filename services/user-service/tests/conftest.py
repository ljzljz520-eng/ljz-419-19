"""
测试配置与 Fixtures
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime

# 确保 app 包可以被导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ==================== Mock 数据库 Fixtures ====================

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.rollback = MagicMock()
    db.close = MagicMock()
    return db


@pytest.fixture
def mock_user():
    """模拟用户对象"""
    from app.models.user import User, UserRole

    user = MagicMock(spec=User)
    user.id = uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.nickname = "测试用户"
    user.avatar = None
    user.phone = "13800138000"
    user.bio = "测试简介"
    user.role = UserRole.USER
    user.is_active = True
    user.is_verified = False
    user.hashed_password = "$2b$12$mockhashedpassword"
    user.created_at = datetime(2026, 1, 1, 0, 0, 0)
    user.updated_at = datetime(2026, 1, 1, 0, 0, 0)
    user.last_login_at = None
    return user


@pytest.fixture
def mock_admin_user():
    """模拟管理员用户对象"""
    from app.models.user import User, UserRole

    user = MagicMock(spec=User)
    user.id = uuid4()
    user.username = "admin"
    user.email = "admin@example.com"
    user.nickname = "系统管理员"
    user.avatar = None
    user.phone = None
    user.bio = None
    user.role = UserRole.ADMIN
    user.is_active = True
    user.is_verified = True
    user.hashed_password = "$2b$12$mockhashedpassword"
    user.created_at = datetime(2026, 1, 1, 0, 0, 0)
    user.updated_at = datetime(2026, 1, 1, 0, 0, 0)
    user.last_login_at = datetime(2026, 1, 30, 10, 0, 0)
    return user


@pytest.fixture
def user_create_data():
    """创建用户请求数据"""
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123",
        "nickname": "新用户",
        "phone": "13900139000",
        "bio": "新用户简介"
    }


@pytest.fixture
def login_data():
    """登录请求数据"""
    return {
        "username": "testuser",
        "password": "password123"
    }
