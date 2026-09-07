"""
gRPC 客户端封装
供其他微服务调用用户服务的 gRPC 接口
"""

from pathlib import Path

import grpc

from app.config import settings
from app.protos import user_pb2, user_pb2_grpc
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 默认连接地址
DEFAULT_GRPC_TARGET = "user-service:50051"


class UserServiceClient:
    """用户服务 gRPC 客户端"""

    def __init__(self, target: str = DEFAULT_GRPC_TARGET):
        self.target = target
        self._channel = None
        self._stub = None

    def _connect(self):
        """建立 gRPC 连接"""
        if self._channel is None:
            if settings.GRPC_TLS_ENABLED:
                root_certificates = None
                private_key = None
                certificate_chain = None

                ca_path = Path(settings.GRPC_CA_CERT_PATH)
                if ca_path.exists():
                    root_certificates = ca_path.read_bytes()
                elif settings.GRPC_MTLS_ENABLED:
                    raise FileNotFoundError(
                        f"gRPC mTLS 已启用，但 CA 证书不存在: {ca_path}"
                    )

                if settings.GRPC_MTLS_ENABLED:
                    client_cert_path = Path(settings.GRPC_CLIENT_CERT_PATH)
                    client_key_path = Path(settings.GRPC_CLIENT_KEY_PATH)
                    if not client_cert_path.exists() or not client_key_path.exists():
                        raise FileNotFoundError(
                            "gRPC mTLS 已启用，但客户端证书或私钥不存在。"
                            f" cert={client_cert_path}, key={client_key_path}"
                        )
                    certificate_chain = client_cert_path.read_bytes()
                    private_key = client_key_path.read_bytes()

                credentials = grpc.ssl_channel_credentials(
                    root_certificates=root_certificates,
                    private_key=private_key,
                    certificate_chain=certificate_chain,
                )
                self._channel = grpc.secure_channel(self.target, credentials)
            else:
                self._channel = grpc.insecure_channel(self.target)
            self._stub = user_pb2_grpc.UserServiceStub(self._channel)
            logger.info(f"已连接到 gRPC 服务: {self.target}")

    def close(self):
        """关闭连接"""
        if self._channel:
            self._channel.close()
            self._channel = None
            self._stub = None

    @property
    def stub(self):
        self._connect()
        return self._stub

    # ==================== 认证方法 ====================

    def login(self, username: str, password: str) -> dict:
        """用户登录"""
        try:
            response = self.stub.Login(
                user_pb2.LoginRequest(username=username, password=password)
            )
            return {
                "success": response.success,
                "message": response.message,
                "access_token": response.access_token,
                "refresh_token": response.refresh_token,
                "token_type": response.token_type,
                "expires_in": response.expires_in,
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC 登录调用失败: {e.code()} - {e.details()}")
            return {"success": False, "message": f"RPC 错误: {e.details()}"}

    def verify_token(self, token: str) -> dict:
        """验证 Token"""
        try:
            response = self.stub.VerifyToken(
                user_pb2.VerifyTokenRequest(token=token)
            )
            return {
                "valid": response.valid,
                "user_id": response.user_id,
                "role": response.role,
                "username": response.username,
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC Token 验证调用失败: {e.code()} - {e.details()}")
            return {"valid": False}

    def refresh_token(self, refresh_token: str) -> dict:
        """刷新 Token"""
        try:
            response = self.stub.RefreshToken(
                user_pb2.RefreshTokenRequest(refresh_token=refresh_token)
            )
            return {
                "success": response.success,
                "message": response.message,
                "access_token": response.access_token,
                "refresh_token": response.refresh_token,
                "token_type": response.token_type,
                "expires_in": response.expires_in,
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC Token 刷新调用失败: {e.code()} - {e.details()}")
            return {"success": False, "message": f"RPC 错误: {e.details()}"}

    # ==================== 用户管理方法 ====================

    def get_user(self, user_id: str) -> dict:
        """获取用户详情"""
        try:
            response = self.stub.GetUser(
                user_pb2.GetUserRequest(user_id=user_id)
            )
            if response.success and response.user:
                return {
                    "success": True,
                    "user": self._proto_user_to_dict(response.user)
                }
            return {"success": False, "message": response.message}
        except grpc.RpcError as e:
            logger.error(f"gRPC 获取用户调用失败: {e.code()} - {e.details()}")
            return {"success": False, "message": f"RPC 错误: {e.details()}"}

    def get_user_by_username(self, username: str) -> dict:
        """通过用户名获取用户"""
        try:
            response = self.stub.GetUserByUsername(
                user_pb2.GetUserByUsernameRequest(username=username)
            )
            if response.success and response.user:
                return {
                    "success": True,
                    "user": self._proto_user_to_dict(response.user)
                }
            return {"success": False, "message": response.message}
        except grpc.RpcError as e:
            logger.error(f"gRPC 获取用户调用失败: {e.code()} - {e.details()}")
            return {"success": False, "message": f"RPC 错误: {e.details()}"}

    def list_users(
        self,
        page: int = 1,
        page_size: int = 10,
        role: str = "",
        is_active: str = "",
        search: str = ""
    ) -> dict:
        """获取用户列表"""
        try:
            response = self.stub.ListUsers(
                user_pb2.ListUsersRequest(
                    page=page,
                    page_size=page_size,
                    role=role,
                    is_active=is_active,
                    search=search
                )
            )
            return {
                "success": response.success,
                "users": [self._proto_user_to_dict(u) for u in response.users],
                "total": response.total,
                "page": response.page,
                "page_size": response.page_size,
                "total_pages": response.total_pages,
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC 用户列表调用失败: {e.code()} - {e.details()}")
            return {"success": False, "message": f"RPC 错误: {e.details()}"}

    def health_check(self) -> dict:
        """健康检查"""
        try:
            response = self.stub.HealthCheck(user_pb2.HealthCheckRequest())
            return {
                "status": response.status,
                "service": response.service,
                "version": response.version,
                "timestamp": response.timestamp,
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC 健康检查失败: {e.code()} - {e.details()}")
            return {"status": "unhealthy", "error": str(e)}

    @staticmethod
    def _proto_user_to_dict(user_info) -> dict:
        """将 protobuf UserInfo 转换为字典"""
        return {
            "id": user_info.id,
            "username": user_info.username,
            "email": user_info.email,
            "nickname": user_info.nickname,
            "avatar": user_info.avatar,
            "phone": user_info.phone,
            "bio": user_info.bio,
            "role": user_info.role,
            "is_active": user_info.is_active,
            "is_verified": user_info.is_verified,
            "created_at": user_info.created_at,
            "updated_at": user_info.updated_at,
            "last_login_at": user_info.last_login_at,
        }
