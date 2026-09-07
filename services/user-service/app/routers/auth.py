"""
认证路由
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, RefreshTokenRequest
from app.schemas.user import UserCreate
from app.services.interfaces import IAuthService, IUserService
from app.routers.deps import (
    get_auth_service,
    get_current_active_user,
    get_user_service,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册"
)
async def register(
    request: RegisterRequest,
    user_service: IUserService = Depends(get_user_service),
):
    """
    用户注册接口
    
    - **username**: 用户名（3-50字符）
    - **email**: 邮箱
    - **password**: 密码（至少6位）
    - **confirm_password**: 确认密码
    - **nickname**: 昵称（可选）
    """
    # 检查用户名是否存在
    if user_service.get_by_username(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否存在
    if user_service.get_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建用户
    user_create = UserCreate(
        username=request.username,
        email=request.email,
        password=request.password,
        nickname=request.nickname,
        role=UserRole.USER
    )
    
    try:
        user = user_service.create(user_create)
        logger.info(f"新用户注册: {user.username}")
        
        return {
            "success": True,
            "message": "注册成功",
            "data": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email
            },
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=dict,
    summary="用户登录"
)
async def login(
    request: LoginRequest,
    auth_service: IAuthService = Depends(get_auth_service),
):
    """
    用户登录接口
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    user = auth_service.authenticate(request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    access_token, refresh_token, expires_in = auth_service.create_tokens(user)
    
    logger.info(f"用户登录: {user.username}")
    
    return {
        "success": True,
        "message": "登录成功",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "nickname": user.nickname,
                "role": user.role.value,
                "avatar": user.avatar
            }
        },
        "timestamp": datetime.now().isoformat()
    }


@router.post(
    "/refresh",
    response_model=dict,
    summary="刷新令牌"
)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: IAuthService = Depends(get_auth_service),
):
    """
    刷新访问令牌
    
    - **refresh_token**: 刷新令牌
    """
    result = auth_service.refresh_access_token(request.refresh_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌无效或已过期"
        )
    
    access_token, refresh_token, expires_in = result
    
    return {
        "success": True,
        "message": "令牌刷新成功",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in
        },
        "timestamp": datetime.now().isoformat()
    }


@router.post(
    "/logout",
    summary="用户登出"
)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    用户登出接口
    
    注意：由于 JWT 是无状态的，服务端无法主动使 Token 失效
    客户端需要自行清除本地存储的 Token
    """
    logger.info(f"用户登出: {current_user.username}")
    
    return {
        "success": True,
        "message": "登出成功",
        "timestamp": datetime.now().isoformat()
    }


@router.get(
    "/me",
    response_model=dict,
    summary="获取当前用户信息"
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前登录用户信息
    """
    return {
        "success": True,
        "message": "获取成功",
        "data": {
            "id": str(current_user.id),
            "username": current_user.username,
            "email": current_user.email,
            "nickname": current_user.nickname,
            "avatar": current_user.avatar,
            "phone": current_user.phone,
            "bio": current_user.bio,
            "role": current_user.role.value,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None
        },
        "timestamp": datetime.now().isoformat()
    }
