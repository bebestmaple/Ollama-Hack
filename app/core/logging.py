import os
import sys
from typing import Optional

from loguru import logger

from app.core.config import settings


def get_logger(
    name: str = "OllamaHack",
    level: str = settings.LOG_LEVEL,
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "1 week",
    format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
) -> logger:
    """
    获取配置好的logger实例

    Args:
        name: 日志名称
        level: 日志级别, 可选值 TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL
        log_file: 日志文件路径, 为None时不记录到文件
        rotation: 日志文件切割条件, 例如 "10 MB", "1 day"
        retention: 日志文件保留时长, 例如 "1 week", "1 month"
        format: 日志格式

    Returns:
        配置好的logger实例
    """
    # 移除所有现有处理器
    logger.remove()

    # 添加控制台输出
    logger.add(sys.stderr, level=level, format=format)

    # 添加文件输出(如果指定了文件路径)
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        logger.add(
            log_file,
            level=level,
            format=format,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
        )

    # 创建命名日志器
    named_logger = logger.bind(name=name)

    return named_logger


def configure_app_logging(
    app_name: str = "OllamaHack",
    log_level: str = settings.LOG_LEVEL,
    log_dir: Optional[str] = None,
) -> logger:
    """
    配置应用程序的日志系统

    Args:
        app_name: 应用程序名称
        log_level: 日志级别
        log_dir: 日志目录, 为None时不保存到文件

    Returns:
        配置好的主日志器
    """
    log_file = None
    if log_dir:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, f"{app_name}.log")

    return get_logger(name=app_name, level=log_level, log_file=log_file)
