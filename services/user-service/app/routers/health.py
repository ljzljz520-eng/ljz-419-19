"""
健康检查路由
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", summary="健康检查")
async def health_check(db: Session = Depends(get_db)):
    """
    服务健康检查接口
    
    返回服务运行状态和依赖服务状态
    """
    # 检查数据库连接
    db_status = "healthy"
    db_latency = 0
    
    try:
        start = datetime.now()
        db.execute(text("SELECT 1"))
        db_latency = (datetime.now() - start).total_seconds() * 1000
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        db_status = "unhealthy"
    
    status = "healthy" if db_status == "healthy" else "degraded"
    
    return {
        "status": status,
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": {
                "status": db_status,
                "latency_ms": round(db_latency, 2)
            }
        }
    }


@router.get("/api/v1/health", summary="API 健康检查")
async def api_health_check(db: Session = Depends(get_db)):
    """
    API 健康检查接口（用于 Kong 路由）
    """
    return await health_check(db)


@router.get("/ready", summary="就绪检查")
async def readiness_check(db: Session = Depends(get_db)):
    """
    服务就绪检查接口
    
    用于 Kubernetes 就绪探针
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"就绪检查失败: {e}")
        return {"status": "not ready", "error": str(e)}


@router.get("/live", summary="存活检查")
async def liveness_check():
    """
    服务存活检查接口
    
    用于 Kubernetes 存活探针
    """
    return {"status": "alive"}
