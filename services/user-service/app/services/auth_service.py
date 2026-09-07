"""
认证服务 - JWT Token 处理
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.services.interfaces import IAuthService, IUserService
from app.services.user_service import UserService
from app.utils.logger import get_logger
from app.utils.security import verify_password
from app.schemas.auth import TokenPayload

logger = get_logger(__name__)


class AuthService(IAuthService):
    """认证服务类"""
    
    def __init__(self, db: Session, user_service: IUserService | None = None):
        self.db = db
        self.user_service = user_service or UserService(db)
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """验证用户凭证"""
        user = self.user_service.get_by_username_or_email(username)
        
        if not user:
            logger.warning(f"登录失败: 用户不存在 - {username}")
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.warning(f"登录失败: 密码错误 - {username}")
            return None
        
        if not user.is_active:
            logger.warning(f"登录失败: 用户已禁用 - {username}")
            return None
        
        # 更新最后登录时间
        self.user_service.update_last_login(user.id)
        
        logger.info(f"用户登录成功: {username}")
        return user
    
    def create_access_token(self, user: User) -> str:
        """创建访问 Token"""
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": str(user.id),
            "exp": expire,
            "type": "access",
            "role": user.role.value,
            "username": user.username
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token
    
    def create_refresh_token(self, user: User) -> str:
        """创建刷新 Token"""
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": str(user.id),
            "exp": expire,
            "type": "refresh"
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token
    
    def create_tokens(self, user: User) -> Tuple[str, str, int]:
        """创建访问和刷新 Token"""
        access_token = self.create_access_token(user)
        refresh_token = self.create_refresh_token(user)
        expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 转换为秒
        
        return access_token, refresh_token, expires_in
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[TokenPayload]:
        """验证 Token"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # 检查 Token 类型
            if payload.get("type") != token_type:
                logger.warning(f"Token 类型不匹配: 期望 {token_type}, 实际 {payload.get('type')}")
                return None
            
            return TokenPayload(
                sub=payload.get("sub"),
                exp=payload.get("exp"),
                type=payload.get("type"),
                role=payload.get("role")
            )
            
        except JWTError as e:
            logger.warning(f"Token 验证失败: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str, int]]:
        """使用刷新 Token 获取新的访问 Token"""
        payload = self.verify_token(refresh_token, token_type="refresh")
        
        if not payload:
            return None
        
        user = self.user_service.get_by_id(UUID(payload.sub))
        
        if not user or not user.is_active:
            return None
        
        return self.create_tokens(user)
    
    def get_current_user(self, token: str) -> Optional[User]:
        """从 Token 获取当前用户"""
        payload = self.verify_token(token, token_type="access")
        
        if not payload:
            return None
        
        user = self.user_service.get_by_id(UUID(payload.sub))
        
        if not user or not user.is_active:
            return None
        
        return user
