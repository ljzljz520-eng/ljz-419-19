"""
用户服务 - 业务逻辑层
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.services.interfaces import IUserService
from app.utils.logger import get_logger
from app.utils.security import get_password_hash

logger = get_logger(__name__)


class UserService(IUserService):
    """用户服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """通过 ID 获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        """通过用户名或邮箱获取用户"""
        return self.db.query(User).filter(
            or_(User.username == identifier, User.email == identifier)
        ).first()
    
    def get_list(
        self,
        page: int = 1,
        page_size: int = 10,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> tuple[list[User], int]:
        """获取用户列表（分页）"""
        query = self.db.query(User)
        
        # 过滤条件
        if role is not None:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.nickname.ilike(search_pattern)
                )
            )
        
        # 获取总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
        
        return users, total
    
    def create(self, user_create: UserCreate) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        if self.get_by_username(user_create.username):
            raise ValueError("用户名已存在")
        
        # 检查邮箱是否已存在
        if self.get_by_email(user_create.email):
            raise ValueError("邮箱已被注册")
        
        # 创建用户
        user = User(
            username=user_create.username,
            email=user_create.email,
            hashed_password=get_password_hash(user_create.password),
            nickname=user_create.nickname or user_create.username,
            phone=user_create.phone,
            bio=user_create.bio,
            role=user_create.role
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"创建用户成功: {user.username} (ID: {user.id})")
        return user
    
    def update(self, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
        """更新用户"""
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        # 更新字段
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"更新用户成功: {user.username} (ID: {user.id})")
        return user
    
    def update_password(self, user_id: UUID, new_password: str) -> bool:
        """更新密码"""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        
        logger.info(f"更新密码成功: {user.username} (ID: {user.id})")
        return True
    
    def delete(self, user_id: UUID) -> bool:
        """删除用户"""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        username = user.username
        self.db.delete(user)
        self.db.commit()
        
        logger.info(f"删除用户成功: {username} (ID: {user_id})")
        return True
    
    def soft_delete(self, user_id: UUID) -> bool:
        """软删除用户（禁用）"""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        self.db.commit()
        
        logger.info(f"禁用用户成功: {user.username} (ID: {user.id})")
        return True
    
    def activate(self, user_id: UUID) -> bool:
        """激活用户"""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_active = True
        self.db.commit()
        
        logger.info(f"激活用户成功: {user.username} (ID: {user.id})")
        return True
    
    def update_last_login(self, user_id: UUID) -> bool:
        """更新最后登录时间"""
        from datetime import datetime
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.last_login_at = datetime.now()
        self.db.commit()
        return True
    
    def get_stats(self) -> dict:
        """获取用户统计信息"""
        total = self.db.query(func.count(User.id)).scalar()
        active = self.db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        
        role_stats = {}
        for role in UserRole:
            count = self.db.query(func.count(User.id)).filter(User.role == role).scalar()
            role_stats[role.value] = count
        
        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "by_role": role_stats
        }
