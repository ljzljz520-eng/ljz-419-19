"""
用户服务 - FastAPI 应用入口
企业级微服务架构

同时提供 HTTP (REST) 和 gRPC 两种服务间通信机制
- HTTP/REST: 端口 8000 (FastAPI)
- gRPC: 端口 50051
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import structlog
from fastapi import FastAPI, Request, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import engine, Base, get_db, ensure_schema_exists
from app.routers import auth, users, health
from app.utils.logger import setup_logging, get_logger
from app.services.seed_service import seed_initial_data

# 设置日志
setup_logging()
logger = get_logger(__name__)

# gRPC 服务实例（全局引用以便生命周期管理）
_grpc_server = None


def _error_response(
    status_code: int,
    message: str,
    error_code: str,
    details: dict[str, Any] | None = None,
):
    """构造统一错误响应"""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "error_code": error_code,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        },
    )


def _http_status_to_error_code(status_code: int) -> str:
    """将 HTTP 状态码映射为统一错误码"""
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "TOO_MANY_REQUESTS",
    }
    return mapping.get(status_code, "HTTP_ERROR")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _grpc_server

    logger.info(f"🚀 启动 {settings.SERVICE_NAME} 服务...")

    # 创建数据库表
    try:
        ensure_schema_exists()
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 数据库表创建/同步完成")

        # 填充初始数据
        from sqlalchemy.orm import Session
        db = next(get_db())
        try:
            seed_initial_data(db)
        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise

    # 启动 gRPC 服务（在独立线程中运行）
    try:
        from app.grpc_server import serve as grpc_serve
        _grpc_server = grpc_serve()
        logger.info(f"✅ gRPC 服务已启动 (端口: {settings.GRPC_PORT})")
    except Exception as e:
        logger.warning(f"⚠️ gRPC 服务启动失败（可能缺少 proto 编译文件）: {e}")
        logger.warning("HTTP 服务将继续正常运行")

    yield

    # 关闭 gRPC 服务
    if _grpc_server:
        _grpc_server.stop(grace=5)
        logger.info("👋 gRPC 服务已关闭")

    logger.info(f"👋 关闭 {settings.SERVICE_NAME} 服务...")


# 创建 FastAPI 应用
app = FastAPI(
    title="用户服务 API",
    description="""
## 企业级用户管理服务

提供完整的用户认证与管理功能：

- 🔐 **认证**: 用户注册、登录、Token 刷新
- 👥 **用户管理**: CRUD 操作、角色管理
- 🏥 **健康检查**: 服务状态监控
- 📊 **监控指标**: Prometheus 指标

### 服务间通信
- **HTTP/REST**: FastAPI 提供标准 RESTful API (端口 8000)
- **gRPC**: 基于 Protocol Buffers 的高性能 RPC (端口 50051)

### 技术栈
- FastAPI + SQLAlchemy
- PostgreSQL
- JWT 认证
- gRPC
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求参数校验异常处理"""
    return _error_response(
        status_code=422,
        message="请求参数校验失败",
        error_code="VALIDATION_ERROR",
        details={"errors": jsonable_encoder(exc.errors())},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """业务 HTTPException 统一响应"""
    details = None
    error_code = _http_status_to_error_code(exc.status_code)
    message: str | Any = exc.detail if exc.detail is not None else "请求失败"

    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", message)
        error_code = exc.detail.get("error_code", error_code)
        details = exc.detail.get("details")

    if isinstance(message, list):
        details = {"errors": message}
        message = "请求失败"

    return _error_response(
        status_code=exc.status_code,
        message=str(message),
        error_code=error_code,
        details=details,
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """框架级 HTTP 异常（如 404）统一响应"""
    return _error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        error_code=_http_status_to_error_code(exc.status_code),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局兜底异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return _error_response(
        status_code=500,
        message="服务器内部错误",
        error_code="INTERNAL_ERROR",
    )


# 请求 ID 中间件
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """添加请求追踪 ID"""
    import uuid
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        http_method=request.method,
        http_path=request.url.path,
    )

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        structlog.contextvars.clear_contextvars()


# Prometheus 监控
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# 注册路由
app.include_router(health.router, tags=["健康检查"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户管理"])


@app.get("/", summary="服务信息")
async def root():
    """获取服务基本信息"""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running",
        "communication": {
            "http": f":{settings.SERVICE_PORT}",
            "grpc": f":{settings.GRPC_PORT}"
        },
        "timestamp": datetime.now().isoformat(),
        "docs_url": "/docs"
    }
