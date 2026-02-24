#!/usr/bin/env python3
"""
配置常量定义
保留此文件以确保向后兼容
新的配置管理请使用 config_manager.py
"""
import os

# Colors
RED = '\033[1;31m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[1;34m'
CYAN = '\033[1;36m'
GREY = '\033[0;37m'
PURPLE = '\033[1;35m'
RESET = '\033[0m'

# Paths
TE_PATH = os.environ.get('TE_PATH', '/workspace/TransformerEngine')
WORK_SPACE = os.environ.get('WORK_SPACE', '/workspace')
TE_INIT_SCRIPT = os.environ.get('TE_INIT_SCRIPT', '')  # Needs to be passed or detected

# Log Files
LOG_FILE_PY = os.path.join(TE_PATH, "build_python.log")
LOG_FILE_CPP = os.path.join(TE_PATH, "build_cpp.log")
LOG_FILE_REBUILD = os.path.join(TE_PATH, "rebuild_dev.log")
LOG_FILE_ALL = os.path.join(TE_PATH, "build_all.log")
LOG_FILE_L0_CPP = os.path.join(TE_PATH, "L0_cppunittest_kme.log")
LOG_FILE_L0_TORCH = os.path.join(TE_PATH, "L0_pytorch_unittest_kme.log")
LOG_FILE_L1_TORCH = os.path.join(TE_PATH, "L1_pytorch_distributed_unittest_kme.log")

# 向后兼容导出
__all__ = [
    # Colors
    'RED', 'GREEN', 'YELLOW', 'BLUE', 'CYAN', 'GREY', 'PURPLE', 'RESET',
    # Paths
    'TE_PATH', 'WORK_SPACE', 'TE_INIT_SCRIPT',
    # Log Files
    'LOG_FILE_PY', 'LOG_FILE_CPP', 'LOG_FILE_REBUILD', 'LOG_FILE_ALL',
    'LOG_FILE_L0_CPP', 'LOG_FILE_L0_TORCH', 'LOG_FILE_L1_TORCH',
]
