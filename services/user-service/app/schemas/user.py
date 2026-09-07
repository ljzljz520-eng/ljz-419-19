"""
用户相关 Schema 定义
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, field_validator

from app.models.user import UserRole


class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")


class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    role: UserRole = Field(default=UserRole.USER, description="用户角色")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 6:
            raise ValueError("密码长度至少为6位")
        return v


class UserUpdate(BaseModel):
    """更新用户请求"""
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    avatar: Optional[str] = Field(None, max_length=500, description="头像URL")
    is_active: Optional[bool] = Field(None, description="是否激活")
    role: Optional[UserRole] = Field(None, description="用户角色")


class UserPasswordUpdate(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        """验证新密码"""
        if len(v) < 6:
            raise ValueError("新密码长度至少为6位")
        return v


class UserResponse(BaseModel):
    """用户响应"""
    id: UUID
    username: str
    email: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class UserListResponse(BaseModel):
    """用户列表响应"""
    success: bool = True
    message: str = "查询成功"
    data: List[UserResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0


class UserInDB(UserResponse):
    """数据库中的用户（包含密码哈希）"""
    hashed_password: str
    
    class Config:
        from_attributes = True
