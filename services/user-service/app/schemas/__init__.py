"""
Schemas 包初始化
"""

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserInDB
)
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest
)
from app.schemas.common import (
    ResponseBase,
    PaginationParams,
    ErrorResponse
)

__all__ = [
    # User schemas
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "UserInDB",
    # Auth schemas
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    # Common schemas
    "ResponseBase",
    "PaginationParams",
    "ErrorResponse"
]
