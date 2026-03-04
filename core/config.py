#!/usr/bin/env python3
"""
ANSI 颜色常量
被 cli.py / logger.py / build_helpers.py 等模块共享导入。
路径与日志文件常量已移至 config_manager.py，此处不再定义。
"""

# Colors
RED = '\033[1;31m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[1;34m'
CYAN = '\033[1;36m'
GREY = '\033[0;37m'
PURPLE = '\033[1;35m'
RESET = '\033[0m'

__all__ = ['RED', 'GREEN', 'YELLOW', 'BLUE', 'CYAN', 'GREY', 'PURPLE', 'RESET']
