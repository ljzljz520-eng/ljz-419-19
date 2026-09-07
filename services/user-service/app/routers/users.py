"""
用户管理路由
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserPasswordUpdate
from app.services.interfaces import IUserService
from app.routers.deps import (
    get_current_active_user,
    get_current_admin_user,
    get_current_manager_or_admin,
    get_user_service
)
from app.utils.logger import get_logger
from app.utils.security import verify_password

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=dict,
    summary="获取用户列表"
)
async def get_users(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    role: Optional[UserRole] = Query(default=None, description="用户角色筛选"),
    is_active: Optional[bool] = Query(default=None, description="激活状态筛选"),
    search: Optional[str] = Query(default=None, max_length=50, description="搜索关键词"),
    current_user: User = Depends(get_current_manager_or_admin),
    user_service: IUserService = Depends(get_user_service)
):
    """
    获取用户列表（分页）
    
    需要管理者或管理员权限
    """
    users, total = user_service.get_list(
        page=page,
        page_size=page_size,
        role=role,
        is_active=is_active,
        search=search
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "success": True,
        "message": "查询成功",
        "data": [
            {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "nickname": user.nickname,
                "avatar": user.avatar,
                "phone": user.phone,
                "role": user.role.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
            }
            for user in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "timestamp": datetime.now().isoformat()
    }


@router.get(
    "/stats",
    response_model=dict,
    summary="获取用户统计"
)
async def get_user_stats(
    current_user: User = Depends(get_current_admin_user),
    user_service: IUserService = Depends(get_user_service)
):
    """
    获取用户统计信息
    
    需要管理员权限
    """
    stats = user_service.get_stats()
    
    return {
        "success": True,
        "message": "获取成功",
        "data": stats,
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
    获取当前登录用户详细信息
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
            "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None,
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None
        },
        "timestamp": datetime.now().isoformat()
    }


@router.put(
    "/me",
    response_model=dict,
    summary="更新当前用户信息"
)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: IUserService = Depends(get_user_service)
):
    """
    更新当前登录用户信息
    
    普通用户只能更新自己的基本信息，不能修改角色和激活状态
    """
    # 普通用户不能修改角色和激活状态
    if current_user.role != UserRole.ADMIN:
        user_update.role = None
        user_update.is_active = None
    
    user = user_service.update(current_user.id, user_update)
    
    return {
        "success": True,
        "message": "更新成功",
        "data": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "phone": user.phone,
            "bio": user.bio,
            "role": user.role.value
        },
        "timestamp": datetime.now().isoformat()
    }


@router.put(
    "/me/password",
    response_model=dict,
    summary="修改当前用户密码"
)
async def update_current_user_password(
    password_update: UserPasswordUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: IUserService = Depends(get_user_service)
):
    """
    修改当前登录用户密码
    """
    # 验证原密码
    if not verify_password(password_update.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    # 更新密码
    user_service.update_password(current_user.id, password_update.new_password)
    
    return {
        "success": True,
        "message": "密码修改成功",
        "timestamp": datetime.now().isoformat()
    }


@router.get(
    "/{user_id}",
    response_model=dict,
    summary="获取用户详情"
)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_manager_or_admin),
    user_service: IUserService = Depends(get_user_service)
):
    """
    获取指定用户详情
    
    需要管理者或管理员权限
    """
    user = user_service.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {
        "success": True,
        "message": "获取成功",
        "data": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "phone": user.phone,
            "bio": user.bio,
            "role": user.role.value,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
        },
        "timestamp": datetime.now().isoformat()
    }


@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户"
)
async def create_user(
    user_create: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    user_service: IUserService = Depends(get_user_service)
):
    """
    创建新用户
    
    需要管理员权限
    """
    try:
        user = user_service.create(user_create)
        
        return {
            "success": True,
            "message": "创建成功",
            "data": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "nickname": user.nickname,
                "role": user.role.value
            },
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{user_id}",
    response_model=dict,
    summary="更新用户"
)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    user_service: IUserService = Depends(get_user_service)
):
    """
    更新指定用户信息
    
    需要管理员权限
    """
    user = user_service.update(user_id, user_update)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {
        "success": True,
        "message": "更新成功",
        "data": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "role": user.role.value,
            "is_active": user.is_active
        },
        "timestamp": datetime.now().isoformat()
    }


@router.delete(
    "/{user_id}",
    response_model=dict,
    summary="删除用户"
)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    user_service: IUserService = Depends(get_user_service)
):
    """
    删除指定用户
    
    需要管理员权限
    """
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    success = user_service.delete(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {
        "success": True,
        "message": "删除成功",
        "timestamp": datetime.now().isoformat()
    }


@router.post(
    "/{user_id}/activate",
    response_model=dict,
    summary="激活用户"
)
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    user_service: IUserService = Depends(get_user_service)
):
    """
    激活指定用户
    
    需要管理员权限
    """
    success = user_service.activate(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {
        "success": True,
        "message": "激活成功",
        "timestamp": datetime.now().isoformat()
    }


@router.post(
    "/{user_id}/deactivate",
    response_model=dict,
    summary="禁用用户"
)
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    user_service: IUserService = Depends(get_user_service)
):
    """
    禁用指定用户
    
    需要管理员权限
    """
    # 不能禁用自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己"
        )
    
    success = user_service.soft_delete(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {
        "success": True,
        "message": "禁用成功",
        "timestamp": datetime.now().isoformat()
    }
