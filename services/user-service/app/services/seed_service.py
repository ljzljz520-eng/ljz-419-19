"""
数据填充服务 - 初始化演示数据
"""

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.utils.logger import get_logger
from app.utils.security import get_password_hash

logger = get_logger(__name__)


def seed_initial_data(db: Session) -> None:
    """填充初始数据"""
    
    # 检查是否已有数据
    existing_users = db.query(User).count()
    if existing_users > 0:
        logger.info(f"数据库已有 {existing_users} 个用户，跳过数据填充")
        return
    
    logger.info("开始填充初始数据...")
    
    # 创建管理员账户
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("123456"),
        nickname="系统管理员",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        bio="系统超级管理员账户"
    )
    db.add(admin)
    
    # 创建普通用户
    user = User(
        username="user",
        email="user@example.com",
        hashed_password=get_password_hash("123456"),
        nickname="测试用户",
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
        bio="普通测试用户账户"
    )
    db.add(user)
    
    # 创建管理者账户
    manager = User(
        username="manager",
        email="manager@example.com",
        hashed_password=get_password_hash("123456"),
        nickname="部门经理",
        role=UserRole.MANAGER,
        is_active=True,
        is_verified=True,
        bio="部门管理者账户"
    )
    db.add(manager)
    
    # 创建更多演示用户
    demo_users = [
        {
            "username": "zhangsan",
            "email": "zhangsan@example.com",
            "nickname": "张三",
            "role": UserRole.USER,
            "bio": "研发部门工程师"
        },
        {
            "username": "lisi",
            "email": "lisi@example.com",
            "nickname": "李四",
            "role": UserRole.USER,
            "bio": "产品部门设计师"
        },
        {
            "username": "wangwu",
            "email": "wangwu@example.com",
            "nickname": "王五",
            "role": UserRole.MANAGER,
            "bio": "销售部门经理"
        },
        {
            "username": "zhaoliu",
            "email": "zhaoliu@example.com",
            "nickname": "赵六",
            "role": UserRole.USER,
            "bio": "市场部门专员"
        },
        {
            "username": "guest",
            "email": "guest@example.com",
            "nickname": "访客",
            "role": UserRole.GUEST,
            "bio": "临时访客账户"
        }
    ]
    
    for user_data in demo_users:
        demo_user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=get_password_hash("123456"),
            nickname=user_data["nickname"],
            role=user_data["role"],
            is_active=True,
            is_verified=True,
            bio=user_data["bio"]
        )
        db.add(demo_user)
    
    db.commit()
    
    total_users = db.query(User).count()
    logger.info(f"✅ 初始数据填充完成，共创建 {total_users} 个用户")
