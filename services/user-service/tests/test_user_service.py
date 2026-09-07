"""
用户服务测试用例
覆盖 UserService 的核心业务逻辑
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4
from datetime import datetime

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService


class TestUserServiceGetByMethods:
    """测试 UserService 的查询方法"""

    def test_get_by_id_found(self, mock_db, mock_user):
        """测试通过 ID 获取用户 - 用户存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        service = UserService(mock_db)

        result = service.get_by_id(mock_user.id)

        assert result is not None
        assert result.username == "testuser"

    def test_get_by_id_not_found(self, mock_db):
        """测试通过 ID 获取用户 - 用户不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = UserService(mock_db)

        result = service.get_by_id(uuid4())

        assert result is None

    def test_get_by_username(self, mock_db, mock_user):
        """测试通过用户名获取用户"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        service = UserService(mock_db)

        result = service.get_by_username("testuser")

        assert result is not None
        assert result.username == "testuser"

    def test_get_by_email(self, mock_db, mock_user):
        """测试通过邮箱获取用户"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        service = UserService(mock_db)

        result = service.get_by_email("test@example.com")

        assert result is not None
        assert result.email == "test@example.com"

    def test_get_by_username_or_email(self, mock_db, mock_user):
        """测试通过用户名或邮箱获取用户"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        service = UserService(mock_db)

        result = service.get_by_username_or_email("testuser")

        assert result is not None


class TestUserServiceCreate:
    """测试用户创建"""

    def test_create_user_success(self, mock_db):
        """测试成功创建用户"""
        # 模拟用户名和邮箱都不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = UserService(mock_db)

        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="password123",
            role=UserRole.USER
        )

        with patch("app.services.user_service.get_password_hash", return_value="hashed"):
            result = service.create(user_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_user_duplicate_username(self, mock_db, mock_user):
        """测试创建用户 - 用户名已存在"""
        # 第一次查询(检查用户名) 返回已存在的用户
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = UserService(mock_db)

        user_data = UserCreate(
            username="testuser",
            email="new@example.com",
            password="password123",
            role=UserRole.USER
        )

        with pytest.raises(ValueError, match="用户名已存在"):
            service.create(user_data)


class TestUserServiceUpdate:
    """测试用户更新"""

    def test_update_user_success(self, mock_db, mock_user):
        """测试成功更新用户"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        service = UserService(mock_db)

        update_data = UserUpdate(nickname="更新昵称", phone="13900000000")
        result = service.update(mock_user.id, update_data)

        assert result is not None
        mock_db.commit.assert_called_once()

    def test_update_user_not_found(self, mock_db):
        """测试更新不存在的用户"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = UserService(mock_db)

        update_data = UserUpdate(nickname="新昵称")
        result = service.update(uuid4(), update_data)

        assert result is None


class TestUserServiceDelete:
    """测试用户删除"""

    def test_delete_user_success(self, mock_db, mock_user):
        """测试成功删除用户"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        service = UserService(mock_db)

        result = service.delete(mock_user.id)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()

    def test_delete_user_not_found(self, mock_db):
        """测试删除不存在的用户"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = UserService(mock_db)

        result = service.delete(uuid4())

        assert result is False

    def test_soft_delete_user(self, mock_db, mock_user):
        """测试软删除用户（禁用）"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        service = UserService(mock_db)

        result = service.soft_delete(mock_user.id)

        assert result is True
        mock_db.commit.assert_called_once()

    def test_activate_user(self, mock_db, mock_user):
        """测试激活用户"""
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        service = UserService(mock_db)

        result = service.activate(mock_user.id)

        assert result is True
        mock_db.commit.assert_called_once()


class TestUserServicePassword:
    """测试密码相关"""

    def test_update_password(self, mock_db, mock_user):
        """测试更新密码"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        service = UserService(mock_db)

        with patch("app.services.user_service.get_password_hash", return_value="new_hash"):
            result = service.update_password(mock_user.id, "newpassword123")

        assert result is True
        mock_db.commit.assert_called_once()


class TestUserServiceStats:
    """测试用户统计"""

    def test_get_stats(self, mock_db):
        """测试获取用户统计信息"""
        # 模拟不同的 count 查询返回值
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.scalar.return_value = 10
        mock_query.filter.return_value = mock_query

        service = UserService(mock_db)
        stats = service.get_stats()

        assert "total" in stats
        assert "active" in stats
        assert "inactive" in stats
        assert "by_role" in stats
