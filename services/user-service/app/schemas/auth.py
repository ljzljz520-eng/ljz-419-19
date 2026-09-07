"""
认证相关 Schema 定义
"""

from typing import Optional

from pydantic import BaseModel, Field, EmailStr, field_validator


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名或邮箱")
    password: str = Field(..., min_length=1, description="密码")


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    confirm_password: str = Field(..., description="确认密码")
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    
    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        """验证两次密码是否一致"""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("两次输入的密码不一致")
        return v


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class TokenPayload(BaseModel):
    """Token 载荷"""
    sub: str  # 用户ID
    exp: int  # 过期时间
    type: str  # token 类型: access / refresh
    role: Optional[str] = None  # 用户角色
