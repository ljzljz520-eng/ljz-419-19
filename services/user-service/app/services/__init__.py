"""
Services 包初始化
"""

from app.services.interfaces import IUserService, IAuthService
from app.services.user_service import UserService
from app.services.auth_service import AuthService

__all__ = ["IUserService", "IAuthService", "UserService", "AuthService"]
