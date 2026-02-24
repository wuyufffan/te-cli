#!/usr/bin/env python3
"""
日志配置模块
支持彩色输出和可配置日志级别
"""
import logging
import sys
from typing import Optional

from config import CYAN, GREEN, GREY, RED, RESET, YELLOW


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    # 日志级别对应颜色
    LEVEL_COLORS = {
        logging.DEBUG: GREY,
        logging.INFO: GREEN,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: RED,
    }
    
    def __init__(self, fmt: Optional[str] = None, use_color: bool = True):
        super().__init__(fmt)
        self.use_color = use_color
    
    def format(self, record: logging.LogRecord) -> str:
        # 保存原始信息
        original_levelname = record.levelname
        original_msg = record.getMessage()
        
        # 添加颜色
        if self.use_color and sys.stderr.isatty():
            color = self.LEVEL_COLORS.get(record.levelno, '')
            record.levelname = f"{color}{original_levelname}{RESET}"
        
        result = super().format(record)
        
        # 恢复原始信息
        record.levelname = original_levelname
        
        return result


def setup_logging(
    level: int = logging.INFO,
    use_color: bool = True,
    log_file: Optional[str] = None
) -> logging.Logger:
    """设置日志配置
    
    Args:
        level: 日志级别
        use_color: 是否使用彩色输出
        log_file: 可选的日志文件路径
    
    Returns:
        配置好的 logger 实例
    """
    # 创建 logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    
    # 使用彩色格式化器
    console_format = ColoredFormatter(
        fmt=f"{GREY}%(asctime)s{RESET} [%(levelname)s] %(message)s",
        use_color=use_color
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger"""
    return logging.getLogger(name)


# 便捷日志函数
class LogContext:
    """日志上下文管理器，用于记录操作开始和结束"""
    
    def __init__(self, logger: logging.Logger, action: str, level: int = logging.INFO):
        self.logger = logger
        self.action = action
        self.level = level
    
    def __enter__(self):
        self.logger.log(self.level, f"开始: {self.action}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.log(self.level, f"完成: {self.action}")
        else:
            self.logger.error(f"失败: {self.action} - {exc_val}")
        return False  # 不吞掉异常
