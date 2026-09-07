"""
gRPC 服务端实现
提供基于 gRPC 的服务间通信接口
"""

from pathlib import Path
from concurrent import futures
from datetime import datetime
from uuid import UUID

import grpc

from app.protos import user_pb2, user_pb2_grpc
from app.config import settings
from app.database import SessionLocal
from app.services.auth_service import AuthService
from app.services.interfaces import IAuthService, IUserService
from app.services.user_service import UserService
from app.models.user import UserRole
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _user_to_proto(user) -> user_pb2.UserInfo:
    """将 SQLAlchemy User 对象转换为 protobuf UserInfo"""
    return user_pb2.UserInfo(
        id=str(user.id),
        username=user.username,
        email=user.email,
        nickname=user.nickname or "",
        avatar=user.avatar or "",
        phone=user.phone or "",
        bio=user.bio or "",
        role=user.role.value,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else "",
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else ""
    )


class UserServiceServicer(user_pb2_grpc.UserServiceServicer):
    """用户服务 gRPC 实现"""

    def _get_db(self):
        """获取数据库会话"""
        return SessionLocal()

    @staticmethod
    def _get_user_service(db) -> IUserService:
        """获取用户服务接口实现"""
        return UserService(db)

    def _get_auth_service(self, db) -> IAuthService:
        """获取认证服务接口实现"""
        return AuthService(db, user_service=self._get_user_service(db))

    # ==================== 认证相关 ====================

    def Login(self, request, context):
        """用户登录"""
        db = self._get_db()
        try:
            auth_service = self._get_auth_service(db)
            user = auth_service.authenticate(request.username, request.password)

            if not user:
                return user_pb2.LoginResponse(
                    success=False,
                    message="用户名或密码错误"
                )

            access_token, refresh_token, expires_in = auth_service.create_tokens(user)

            logger.info(f"[gRPC] 用户登录: {user.username}")
            return user_pb2.LoginResponse(
                success=True,
                message="登录成功",
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=expires_in,
                user=_user_to_proto(user)
            )
        except Exception as e:
            logger.error(f"[gRPC] 登录异常: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.LoginResponse(success=False, message="服务器内部错误")
        finally:
            db.close()

    def Register(self, request, context):
        """用户注册"""
        db = self._get_db()
        try:
            from app.schemas.user import UserCreate
            user_service = self._get_user_service(db)

            # 检查用户名
            if user_service.get_by_username(request.username):
                return user_pb2.RegisterResponse(
                    success=False,
                    message="用户名已存在"
                )

            # 检查邮箱
            if user_service.get_by_email(request.email):
                return user_pb2.RegisterResponse(
                    success=False,
                    message="邮箱已被注册"
                )

            user_create = UserCreate(
                username=request.username,
                email=request.email,
                password=request.password,
                nickname=request.nickname or None,
                role=UserRole.USER
            )
            user = user_service.create(user_create)

            logger.info(f"[gRPC] 新用户注册: {user.username}")
            return user_pb2.RegisterResponse(
                success=True,
                message="注册成功",
                user=_user_to_proto(user)
            )
        except ValueError as e:
            return user_pb2.RegisterResponse(success=False, message=str(e))
        except Exception as e:
            logger.error(f"[gRPC] 注册异常: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.RegisterResponse(success=False, message="服务器内部错误")
        finally:
            db.close()

    def VerifyToken(self, request, context):
        """验证 Token"""
        db = self._get_db()
        try:
            auth_service = self._get_auth_service(db)
            payload = auth_service.verify_token(request.token, token_type="access")

            if not payload:
                return user_pb2.VerifyTokenResponse(valid=False)

            return user_pb2.VerifyTokenResponse(
                valid=True,
                user_id=payload.sub,
                role=payload.role or "",
                username=""
            )
        except Exception as e:
            logger.error(f"[gRPC] Token 验证异常: {e}")
            return user_pb2.VerifyTokenResponse(valid=False)
        finally:
            db.close()

    def RefreshToken(self, request, context):
        """刷新 Token"""
        db = self._get_db()
        try:
            auth_service = self._get_auth_service(db)
            result = auth_service.refresh_access_token(request.refresh_token)

            if not result:
                return user_pb2.RefreshTokenResponse(
                    success=False,
                    message="刷新令牌无效或已过期"
                )

            access_token, refresh_token, expires_in = result
            return user_pb2.RefreshTokenResponse(
                success=True,
                message="令牌刷新成功",
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=expires_in
            )
        except Exception as e:
            logger.error(f"[gRPC] 刷新 Token 异常: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.RefreshTokenResponse(success=False, message="服务器内部错误")
        finally:
            db.close()

    # ==================== 用户管理 ====================

    def GetUser(self, request, context):
        """获取用户详情"""
        db = self._get_db()
        try:
            user_service = self._get_user_service(db)
            user = user_service.get_by_id(UUID(request.user_id))

            if not user:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("用户不存在")
                return user_pb2.GetUserResponse(success=False, message="用户不存在")

            return user_pb2.GetUserResponse(
                success=True,
                message="获取成功",
                user=_user_to_proto(user)
            )
        except Exception as e:
            logger.error(f"[gRPC] 获取用户异常: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.GetUserResponse(success=False, message="服务器内部错误")
        finally:
            db.close()

    def GetUserByUsername(self, request, context):
        """通过用户名获取用户"""
        db = self._get_db()
        try:
            user_service = self._get_user_service(db)
            user = user_service.get_by_username(request.username)

            if not user:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("用户不存在")
                return user_pb2.GetUserResponse(success=False, message="用户不存在")

            return user_pb2.GetUserResponse(
                success=True,
                message="获取成功",
                user=_user_to_proto(user)
            )
        except Exception as e:
            logger.error(f"[gRPC] 获取用户异常: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.GetUserResponse(success=False, message="服务器内部错误")
        finally:
            db.close()

    def ListUsers(self, request, context):
        """获取用户列表"""
        db = self._get_db()
        try:
            user_service = self._get_user_service(db)

            role = None
            if request.role:
                try:
                    role = UserRole(request.role)
                except ValueError:
                    pass

            is_active = None
            if request.is_active == "true":
                is_active = True
            elif request.is_active == "false":
                is_active = False

            users, total = user_service.get_list(
                page=request.page or 1,
                page_size=request.page_size or 10,
                role=role,
                is_active=is_active,
                search=request.search or None
            )

            page = request.page or 1
            page_size = request.page_size or 10
            total_pages = (total + page_size - 1) // page_size

            return user_pb2.ListUsersResponse(
                success=True,
                message="查询成功",
                users=[_user_to_proto(u) for u in users],
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
        except Exception as e:
            logger.error(f"[gRPC] 列表查询异常: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.ListUsersResponse(success=False, message="服务器内部错误")
        finally:
            db.close()

    def UpdateUser(self, request, context):
        """更新用户"""
        db = self._get_db()
        try:
            from app.schemas.user import UserUpdate
            user_service = self._get_user_service(db)

            update_data = {}
            if request.nickname:
                update_data["nickname"] = request.nickname
            if request.phone:
                update_data["phone"] = request.phone
            if request.bio:
                update_data["bio"] = request.bio
            if request.avatar:
                update_data["avatar"] = request.avatar
            if request.role:
                update_data["role"] = UserRole(request.role)

            user_update = UserUpdate(**update_data)
            user = user_service.update(UUID(request.user_id), user_update)

            if not user:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("用户不存在")
                return user_pb2.GetUserResponse(success=False, message="用户不存在")

            return user_pb2.GetUserResponse(
                success=True,
                message="更新成功",
                user=_user_to_proto(user)
            )
        except Exception as e:
            logger.error(f"[gRPC] 更新用户异常: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.GetUserResponse(success=False, message="服务器内部错误")
        finally:
            db.close()

    def DeleteUser(self, request, context):
        """删除用户"""
        db = self._get_db()
        try:
            user_service = self._get_user_service(db)
            success = user_service.delete(UUID(request.user_id))

            if not success:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("用户不存在")
                return user_pb2.DeleteUserResponse(success=False, message="用户不存在")

            return user_pb2.DeleteUserResponse(success=True, message="删除成功")
        except Exception as e:
            logger.error(f"[gRPC] 删除用户异常: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.DeleteUserResponse(success=False, message="服务器内部错误")
        finally:
            db.close()

    # ==================== 健康检查 ====================

    def HealthCheck(self, request, context):
        """健康检查"""
        return user_pb2.HealthCheckResponse(
            status="healthy",
            service=settings.SERVICE_NAME,
            version="1.0.0",
            timestamp=datetime.now().isoformat()
        )


def serve():
    """启动 gRPC 服务端"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)

    listen_addr = f"[::]:{settings.GRPC_PORT}"
    if settings.GRPC_TLS_ENABLED:
        cert_path = Path(settings.GRPC_SERVER_CERT_PATH)
        key_path = Path(settings.GRPC_SERVER_KEY_PATH)
        if not cert_path.exists() or not key_path.exists():
            raise FileNotFoundError(
                "gRPC TLS 已启用，但服务端证书或私钥不存在。"
                f" cert={cert_path}, key={key_path}"
            )

        certificate_chain = cert_path.read_bytes()
        private_key = key_path.read_bytes()
        root_certificates = None

        if settings.GRPC_MTLS_ENABLED:
            ca_path = Path(settings.GRPC_CA_CERT_PATH)
            if not ca_path.exists():
                raise FileNotFoundError(
                    "gRPC mTLS 已启用，但 CA 证书不存在。"
                    f" ca={ca_path}"
                )
            root_certificates = ca_path.read_bytes()

        credentials = grpc.ssl_server_credentials(
            [(private_key, certificate_chain)],
            root_certificates=root_certificates,
            require_client_auth=settings.GRPC_MTLS_ENABLED,
        )
        server.add_secure_port(listen_addr, credentials)
        logger.info(
            f"🔐 gRPC TLS 已启用，监听端口: {settings.GRPC_PORT} "
            f"(mTLS={settings.GRPC_MTLS_ENABLED})"
        )
    else:
        server.add_insecure_port(listen_addr)
        logger.warning("⚠️ gRPC 以明文模式启动（未启用 TLS）")

    server.start()
    logger.info(f"🚀 gRPC 服务已启动，监听端口: {settings.GRPC_PORT}")
    return server
