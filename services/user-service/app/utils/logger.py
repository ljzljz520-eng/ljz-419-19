"""
日志配置模块 - 结构化日志输出
"""

import logging
import sys
from typing import Optional

import structlog
from structlog.typing import FilteringBoundLogger

from app.config import settings


def get_logger(name: Optional[str] = None) -> FilteringBoundLogger:
    """获取结构化日志实例"""
    return structlog.get_logger(name)


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    配置结构化日志
    
    Args:
        log_level: 日志级别，默认从配置读取
    """
    level = log_level or settings.LOG_LEVEL
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer = (
        structlog.dev.ConsoleRenderer()
        if settings.DEBUG
        else structlog.processors.JSONRenderer()
    )

    # 配置 structlog（供 structlog.get_logger 与 logging 共用）
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)

    # 设置第三方库日志级别
    for logger_name, logger_level in (
        ("uvicorn", logging.INFO),
        ("uvicorn.access", logging.INFO),
        ("sqlalchemy.engine", logging.WARNING),
    ):
        external_logger = logging.getLogger(logger_name)
        external_logger.handlers.clear()
        external_logger.propagate = True
        external_logger.setLevel(logger_level)

    logger = get_logger(__name__)
    logger.info("日志系统初始化完成", log_level=level, debug_mode=settings.DEBUG)
