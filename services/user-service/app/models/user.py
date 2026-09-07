"""
用户数据模型
"""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text, Index
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base, DB_SCHEMA


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    MANAGER = "manager"
    GUEST = "guest"


class User(Base):
    """用户表模型"""
    
    __tablename__ = "users"
    
    # 主键
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="用户唯一标识"
    )
    
    # 基本信息
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="用户名"
    )
    
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="邮箱"
    )
    
    hashed_password = Column(
        String(255),
        nullable=False,
        comment="加密后的密码"
    )
    
    # 用户详情
    nickname = Column(
        String(100),
        nullable=True,
        comment="昵称"
    )
    
    avatar = Column(
        String(500),
        nullable=True,
        comment="头像URL"
    )
    
    phone = Column(
        String(20),
        nullable=True,
        comment="手机号"
    )
    
    bio = Column(
        Text,
        nullable=True,
        comment="个人简介"
    )
    
    # 角色与权限
    role = Column(
        Enum(UserRole),
        default=UserRole.USER,
        nullable=False,
        comment="用户角色"
    )
    
    # 状态
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活"
    )
    
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已验证邮箱"
    )
    
    # 时间戳
    created_at = Column(
        DateTime,
        default=datetime.now,
        nullable=False,
        comment="创建时间"
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
        comment="更新时间"
    )
    
    last_login_at = Column(
        DateTime,
        nullable=True,
        comment="最后登录时间"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_user_role_active", "role", "is_active"),
        Index("idx_user_created_at", "created_at"),
        {"comment": "用户表", "schema": DB_SCHEMA}
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "nickname": self.nickname,
            "avatar": self.avatar,
            "phone": self.phone,
            "bio": self.bio,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }
