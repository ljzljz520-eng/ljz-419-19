"""
API 接口测试用例
覆盖 HTTP API 端点的请求与响应
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime

from fastapi.testclient import TestClient

from app.models.user import User, UserRole


@pytest.fixture
def test_client():
    """创建测试客户端"""
    # 在导入前 mock 数据库连接
    with patch("app.database.engine"), \
         patch("app.database.Base"), \
         patch("app.database.SessionLocal"), \
         patch("app.services.seed_service.seed_initial_data"):
        from app.main import app
        client = TestClient(app)
        yield client


@pytest.fixture
def auth_headers(mock_user):
    """认证请求头"""
    from app.services.auth_service import AuthService
    with patch("app.database.SessionLocal"):
        mock_db = MagicMock()
        service = AuthService(mock_db)
        token = service.create_access_token(mock_user)
        return {"Authorization": f"Bearer {token}"}


class TestHealthEndpoints:
    """健康检查接口测试"""

    def test_root_endpoint(self, test_client):
        """测试根路径返回服务信息"""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "user-service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert "timestamp" in data

    def test_health_check(self, test_client):
        """测试健康检查接口"""
        with patch("app.routers.health.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.execute = MagicMock()
            mock_get_db.return_value = iter([mock_db])

            response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert data["service"] == "user-service"

    def test_liveness_check(self, test_client):
        """测试存活检查接口"""
        response = test_client.get("/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestAuthEndpoints:
    """认证接口测试"""

    def test_register_success(self, test_client):
        """测试注册成功"""
        mock_user = MagicMock(spec=User)
        mock_user.id = uuid4()
        mock_user.username = "newuser"
        mock_user.email = "new@example.com"

        with patch("app.routers.auth.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])

            with patch("app.routers.auth.UserService") as MockUserService:
                service_instance = MockUserService.return_value
                service_instance.get_by_username.return_value = None
                service_instance.get_by_email.return_value = None
                service_instance.create.return_value = mock_user

                response = test_client.post("/api/v1/auth/register", json={
                    "username": "newuser",
                    "email": "new@example.com",
                    "password": "password123",
                    "confirm_password": "password123"
                })

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "注册成功"

    def test_register_duplicate_username(self, test_client, mock_user):
        """测试注册 - 用户名已存在"""
        with patch("app.routers.auth.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])

            with patch("app.routers.auth.UserService") as MockUserService:
                service_instance = MockUserService.return_value
                service_instance.get_by_username.return_value = mock_user

                response = test_client.post("/api/v1/auth/register", json={
                    "username": "testuser",
                    "email": "new@example.com",
                    "password": "password123",
                    "confirm_password": "password123"
                })

        assert response.status_code == 400

    def test_register_password_mismatch(self, test_client):
        """测试注册 - 密码不一致"""
        response = test_client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
            "confirm_password": "differentpassword"
        })

        assert response.status_code == 422  # 验证失败

    def test_login_success(self, test_client, mock_user):
        """测试登录成功"""
        with patch("app.routers.auth.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])

            with patch("app.routers.auth.AuthService") as MockAuthService:
                service_instance = MockAuthService.return_value
                service_instance.authenticate.return_value = mock_user
                service_instance.create_tokens.return_value = (
                    "access_token_xxx",
                    "refresh_token_xxx",
                    1800
                )

                response = test_client.post("/api/v1/auth/login", json={
                    "username": "testuser",
                    "password": "password123"
                })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["access_token"] == "access_token_xxx"
        assert data["data"]["token_type"] == "bearer"

    def test_login_wrong_password(self, test_client):
        """测试登录 - 密码错误"""
        with patch("app.routers.auth.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])

            with patch("app.routers.auth.AuthService") as MockAuthService:
                service_instance = MockAuthService.return_value
                service_instance.authenticate.return_value = None

                response = test_client.post("/api/v1/auth/login", json={
                    "username": "testuser",
                    "password": "wrongpassword"
                })

        assert response.status_code == 401

    def test_login_validation_error(self, test_client):
        """测试登录 - 缺少必填字段"""
        response = test_client.post("/api/v1/auth/login", json={
            "username": "ab"  # 太短, 缺少 password
        })

        assert response.status_code == 422


class TestSchemaValidation:
    """Schema 数据验证测试"""

    def test_user_create_valid(self):
        """测试有效的用户创建数据"""
        from app.schemas.user import UserCreate
        user = UserCreate(
            username="validuser",
            email="valid@example.com",
            password="password123"
        )
        assert user.username == "validuser"
        assert user.role == UserRole.USER

    def test_user_create_short_password(self):
        """测试密码太短"""
        from app.schemas.user import UserCreate
        with pytest.raises(Exception):
            UserCreate(
                username="validuser",
                email="valid@example.com",
                password="123"  # 太短
            )

    def test_user_create_invalid_email(self):
        """测试无效邮箱"""
        from app.schemas.user import UserCreate
        with pytest.raises(Exception):
            UserCreate(
                username="validuser",
                email="invalid-email",
                password="password123"
            )

    def test_login_request_valid(self):
        """测试有效的登录请求"""
        from app.schemas.auth import LoginRequest
        req = LoginRequest(username="testuser", password="password123")
        assert req.username == "testuser"

    def test_register_request_password_match(self):
        """测试注册请求密码一致"""
        from app.schemas.auth import RegisterRequest
        req = RegisterRequest(
            username="newuser",
            email="new@example.com",
            password="password123",
            confirm_password="password123"
        )
        assert req.password == req.confirm_password

    def test_register_request_password_mismatch(self):
        """测试注册请求密码不一致"""
        from app.schemas.auth import RegisterRequest
        with pytest.raises(Exception):
            RegisterRequest(
                username="newuser",
                email="new@example.com",
                password="password123",
                confirm_password="different"
            )


class TestSecurityUtils:
    """安全工具函数测试"""

    def test_password_hash_and_verify(self):
        """测试密码哈希与验证"""
        from app.utils.security import get_password_hash, verify_password

        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    def test_password_hash_uniqueness(self):
        """测试相同密码生成不同的哈希"""
        from app.utils.security import get_password_hash

        hash1 = get_password_hash("same_password")
        hash2 = get_password_hash("same_password")

        # bcrypt 每次生成不同的盐，所以哈希值不同
        assert hash1 != hash2
