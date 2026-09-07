"""
服务层接口定义（面向接口编程）
"""

from __future__ import annotations

from typing import Optional, Protocol, Tuple
from uuid import UUID

from app.models.user import User, UserRole
from app.schemas.auth import TokenPayload
from app.schemas.user import UserCreate, UserUpdate


class IUserService(Protocol):
    """用户服务接口"""

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        ...

    def get_by_username(self, username: str) -> Optional[User]:
        ...

    def get_by_email(self, email: str) -> Optional[User]:
        ...

    def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        ...

    def get_list(
        self,
        page: int = 1,
        page_size: int = 10,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> tuple[list[User], int]:
        ...

    def create(self, user_create: UserCreate) -> User:
        ...

    def update(self, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
        ...

    def update_password(self, user_id: UUID, new_password: str) -> bool:
        ...

    def delete(self, user_id: UUID) -> bool:
        ...

    def soft_delete(self, user_id: UUID) -> bool:
        ...

    def activate(self, user_id: UUID) -> bool:
        ...

    def update_last_login(self, user_id: UUID) -> bool:
        ...

    def get_stats(self) -> dict:
        ...


class IAuthService(Protocol):
    """认证服务接口"""

    def authenticate(self, username: str, password: str) -> Optional[User]:
        ...

    def create_access_token(self, user: User) -> str:
        ...

    def create_refresh_token(self, user: User) -> str:
        ...

    def create_tokens(self, user: User) -> Tuple[str, str, int]:
        ...

    def verify_token(self, token: str, token_type: str = "access") -> Optional[TokenPayload]:
        ...

    def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str, int]]:
        ...

    def get_current_user(self, token: str) -> Optional[User]:
        ...
