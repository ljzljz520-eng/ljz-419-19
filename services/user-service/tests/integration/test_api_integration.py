"""
用户服务接口集成测试

基于本地 PostgreSQL 测试库运行（默认 user_db_test），
覆盖：健康检查、注册、登录、未授权访问、管理员查询用户、禁用账号。
"""

from app.models.user import User, UserRole

from .conftest import ADMIN_PASSWORD, USER_PASSWORD


def _login(client, username: str, password: str) -> str:
    """登录并返回 access_token"""
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestHealthCheck:
    """健康检查"""

    def test_health_check(self, client):
        resp = client.get("/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["checks"]["database"]["status"] == "healthy"


class TestRegister:
    """用户注册"""

    def test_register_success(self, client, db_session):
        resp = client.post("/api/v1/auth/register", json={
            "username": "it_register",
            "email": "it_register@example.com",
            "password": "Register@123",
            "confirm_password": "Register@123",
            "nickname": "集成测试注册用户",
        })

        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["username"] == "it_register"

        # 数据库中应能查到新注册用户
        user = db_session.query(User).filter(User.username == "it_register").first()
        assert user is not None
        assert user.email == "it_register@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True

    def test_register_duplicate_username(self, client, normal_user):
        resp = client.post("/api/v1/auth/register", json={
            "username": normal_user.username,
            "email": "someone_else@example.com",
            "password": "Register@123",
            "confirm_password": "Register@123",
        })

        assert resp.status_code == 400
        assert resp.json()["success"] is False

    def test_register_password_mismatch(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "username": "it_register",
            "email": "it_register@example.com",
            "password": "Register@123",
            "confirm_password": "Register@456",
        })

        assert resp.status_code == 422


class TestLogin:
    """用户登录"""

    def test_login_success(self, client, normal_user):
        resp = client.post("/api/v1/auth/login", json={
            "username": "it_user",
            "password": USER_PASSWORD,
        })

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "it_user"
        assert data["user"]["role"] == "user"

    def test_login_with_email(self, client, normal_user):
        resp = client.post("/api/v1/auth/login", json={
            "username": "it_user@example.com",
            "password": USER_PASSWORD,
        })

        assert resp.status_code == 200
        assert resp.json()["data"]["user"]["username"] == "it_user"

    def test_login_wrong_password(self, client, normal_user):
        resp = client.post("/api/v1/auth/login", json={
            "username": "it_user",
            "password": "WrongPass@123",
        })

        assert resp.status_code == 401

    def test_login_user_not_found(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "username": "no_such_user",
            "password": "Whatever@123",
        })

        assert resp.status_code == 401


class TestUnauthorizedAccess:
    """未授权访问"""

    def test_user_list_without_token(self, client):
        resp = client.get("/api/v1/users")

        assert resp.status_code == 401

    def test_user_list_with_invalid_token(self, client):
        resp = client.get(
            "/api/v1/users",
            headers=_auth("invalid.token.here"),
        )

        assert resp.status_code == 401

    def test_user_list_with_normal_user(self, client, normal_user):
        token = _login(client, "it_user", USER_PASSWORD)
        resp = client.get("/api/v1/users", headers=_auth(token))

        assert resp.status_code == 403

    def test_me_without_token(self, client):
        resp = client.get("/api/v1/users/me")

        assert resp.status_code == 401


class TestAdminQueryUsers:
    """管理员查询用户"""

    def test_admin_get_user_list(self, client, admin_user, normal_user):
        token = _login(client, "it_admin", ADMIN_PASSWORD)
        resp = client.get("/api/v1/users", headers=_auth(token))

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["total"] == 2
        usernames = [u["username"] for u in body["data"]]
        assert "it_admin" in usernames
        assert "it_user" in usernames

    def test_admin_get_user_detail(self, client, admin_user, normal_user):
        token = _login(client, "it_admin", ADMIN_PASSWORD)
        resp = client.get(f"/api/v1/users/{normal_user.id}", headers=_auth(token))

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["username"] == "it_user"
        assert data["email"] == "it_user@example.com"
        assert data["is_active"] is True

    def test_admin_get_user_stats(self, client, admin_user, normal_user):
        token = _login(client, "it_admin", ADMIN_PASSWORD)
        resp = client.get("/api/v1/users/stats", headers=_auth(token))

        assert resp.status_code == 200
        stats = resp.json()["data"]
        assert stats["total"] == 2
        assert stats["active"] == 2
        assert stats["by_role"]["admin"] == 1
        assert stats["by_role"]["user"] == 1


class TestDeactivateAccount:
    """禁用账号"""

    def test_admin_deactivate_user(self, client, db_session, admin_user, normal_user):
        admin_token = _login(client, "it_admin", ADMIN_PASSWORD)
        user_token = _login(client, "it_user", USER_PASSWORD)

        resp = client.post(
            f"/api/v1/users/{normal_user.id}/deactivate",
            headers=_auth(admin_token),
        )

        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # 数据库中账号已被禁用
        db_session.expire_all()
        user = db_session.query(User).filter(User.id == normal_user.id).first()
        assert user.is_active is False

        # 被禁用后无法再登录
        resp = client.post("/api/v1/auth/login", json={
            "username": "it_user",
            "password": USER_PASSWORD,
        })
        assert resp.status_code == 401

        # 禁用前签发的 token 也随之失效
        resp = client.get("/api/v1/users/me", headers=_auth(user_token))
        assert resp.status_code == 401

    def test_deactivate_requires_admin(self, client, admin_user, normal_user):
        user_token = _login(client, "it_user", USER_PASSWORD)
        resp = client.post(
            f"/api/v1/users/{admin_user.id}/deactivate",
            headers=_auth(user_token),
        )

        assert resp.status_code == 403

    def test_admin_cannot_deactivate_self(self, client, admin_user):
        admin_token = _login(client, "it_admin", ADMIN_PASSWORD)
        resp = client.post(
            f"/api/v1/users/{admin_user.id}/deactivate",
            headers=_auth(admin_token),
        )

        assert resp.status_code == 400
