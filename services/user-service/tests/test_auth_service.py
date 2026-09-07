"""
认证服务测试用例
覆盖 AuthService 的 JWT 认证逻辑
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

from app.models.user import User, UserRole
from app.services.auth_service import AuthService


class TestAuthenticate:
    """测试用户认证"""

    def test_authenticate_success(self, mock_db, mock_user):
        """测试认证成功"""
        with patch.object(AuthService, "__init__", lambda self, db: None):
            service = AuthService.__new__(AuthService)
            service.db = mock_db
            service.user_service = MagicMock()
            service.user_service.get_by_username_or_email.return_value = mock_user
            service.user_service.update_last_login.return_value = True

            with patch("app.services.auth_service.verify_password", return_value=True):
                result = service.authenticate("testuser", "password123")

        assert result is not None
        assert result.username == "testuser"

    def test_authenticate_user_not_found(self, mock_db):
        """测试认证失败 - 用户不存在"""
        with patch.object(AuthService, "__init__", lambda self, db: None):
            service = AuthService.__new__(AuthService)
            service.db = mock_db
            service.user_service = MagicMock()
            service.user_service.get_by_username_or_email.return_value = None

            result = service.authenticate("nonexistent", "password123")

        assert result is None

    def test_authenticate_wrong_password(self, mock_db, mock_user):
        """测试认证失败 - 密码错误"""
        with patch.object(AuthService, "__init__", lambda self, db: None):
            service = AuthService.__new__(AuthService)
            service.db = mock_db
            service.user_service = MagicMock()
            service.user_service.get_by_username_or_email.return_value = mock_user

            with patch("app.services.auth_service.verify_password", return_value=False):
                result = service.authenticate("testuser", "wrongpassword")

        assert result is None

    def test_authenticate_inactive_user(self, mock_db, mock_user):
        """测试认证失败 - 用户已禁用"""
        mock_user.is_active = False

        with patch.object(AuthService, "__init__", lambda self, db: None):
            service = AuthService.__new__(AuthService)
            service.db = mock_db
            service.user_service = MagicMock()
            service.user_service.get_by_username_or_email.return_value = mock_user

            with patch("app.services.auth_service.verify_password", return_value=True):
                result = service.authenticate("testuser", "password123")

        assert result is None


class TestTokenCreation:
    """测试 Token 生成"""

    def test_create_access_token(self, mock_db, mock_user):
        """测试生成访问 Token"""
        service = AuthService(mock_db)

        token = service.create_access_token(mock_user)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, mock_db, mock_user):
        """测试生成刷新 Token"""
        service = AuthService(mock_db)

        token = service.create_refresh_token(mock_user)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_tokens_returns_three(self, mock_db, mock_user):
        """测试 create_tokens 返回三元组"""
        service = AuthService(mock_db)

        result = service.create_tokens(mock_user)

        assert len(result) == 3
        access_token, refresh_token, expires_in = result
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        assert isinstance(expires_in, int)
        assert expires_in > 0


class TestTokenVerification:
    """测试 Token 验证"""

    def test_verify_valid_access_token(self, mock_db, mock_user):
        """测试验证有效的访问 Token"""
        service = AuthService(mock_db)

        token = service.create_access_token(mock_user)
        payload = service.verify_token(token, token_type="access")

        assert payload is not None
        assert payload.sub == str(mock_user.id)
        assert payload.type == "access"
        assert payload.role == mock_user.role.value

    def test_verify_valid_refresh_token(self, mock_db, mock_user):
        """测试验证有效的刷新 Token"""
        service = AuthService(mock_db)

        token = service.create_refresh_token(mock_user)
        payload = service.verify_token(token, token_type="refresh")

        assert payload is not None
        assert payload.sub == str(mock_user.id)
        assert payload.type == "refresh"

    def test_verify_invalid_token(self, mock_db):
        """测试验证无效的 Token"""
        service = AuthService(mock_db)

        result = service.verify_token("invalid.token.here")

        assert result is None

    def test_verify_wrong_token_type(self, mock_db, mock_user):
        """测试 Token 类型不匹配"""
        service = AuthService(mock_db)

        # 创建 access token 但当作 refresh token 验证
        token = service.create_access_token(mock_user)
        result = service.verify_token(token, token_type="refresh")

        assert result is None


class TestRefreshAccessToken:
    """测试刷新 Token"""

    def test_refresh_success(self, mock_db, mock_user):
        """测试成功刷新 Token"""
        service = AuthService(mock_db)
        service.user_service = MagicMock()
        service.user_service.get_by_id.return_value = mock_user

        refresh_token = service.create_refresh_token(mock_user)
        result = service.refresh_access_token(refresh_token)

        assert result is not None
        new_access, new_refresh, expires_in = result
        assert isinstance(new_access, str)
        assert isinstance(new_refresh, str)
        assert expires_in > 0

    def test_refresh_invalid_token(self, mock_db):
        """测试使用无效 Token 刷新"""
        service = AuthService(mock_db)

        result = service.refresh_access_token("invalid.refresh.token")

        assert result is None

    def test_refresh_inactive_user(self, mock_db, mock_user):
        """测试已禁用用户刷新 Token"""
        mock_user.is_active = False
        service = AuthService(mock_db)
        service.user_service = MagicMock()
        service.user_service.get_by_id.return_value = mock_user

        refresh_token = service.create_refresh_token(mock_user)
        result = service.refresh_access_token(refresh_token)

        assert result is None


class TestGetCurrentUser:
    """测试获取当前用户"""

    def test_get_current_user_success(self, mock_db, mock_user):
        """测试成功获取当前用户"""
        service = AuthService(mock_db)
        service.user_service = MagicMock()
        service.user_service.get_by_id.return_value = mock_user

        token = service.create_access_token(mock_user)
        result = service.get_current_user(token)

        assert result is not None
        assert result.username == "testuser"

    def test_get_current_user_invalid_token(self, mock_db):
        """测试无效 Token 获取用户"""
        service = AuthService(mock_db)

        result = service.get_current_user("invalid.token")

        assert result is None
