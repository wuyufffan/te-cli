#!/usr/bin/env python3
"""
DTK 版本检测工具

统一的 DTK 安装路径检测逻辑，被 config_manager.py / build_helpers.py 共同使用。
若需新增 DTK 版本支持，只需修改此文件。
"""
import logging
import os

logger = logging.getLogger(__name__)

# DTK 路径常量（统一定义）
DTK_26_PATH = "/opt/dtk-26.04"
DTK_25_PATH = "/opt/dtk-25.04.2"
DTK_SYMLINK = "/opt/dtk"


def detect_dtk_base(
    dtk_26_path: str = DTK_26_PATH,
    dtk_default: str = DTK_25_PATH,
) -> str:
    """检测 DTK 安装路径。

    优先级：环境变量 DTK_BASE > 26.04 > /opt/dtk 软链 > 25.04.2 默认值

    Args:
        dtk_26_path: DTK 26.04 路径，默认 /opt/dtk-26.04
        dtk_default: 兜底默认路径，默认 /opt/dtk-25.04.2

    Returns:
        检测到的 DTK base 路径（不保证目录实际存在）
    """
    # 1. 环境变量优先
    override_base = os.environ.get("DTK_BASE")
    if override_base and os.path.isdir(override_base):
        logger.debug(f"使用环境变量 DTK_BASE: {override_base}")
        return override_base

    # 2. 26.04 版本
    if os.path.isdir(dtk_26_path):
        logger.debug(f"检测到 DTK 26.04: {dtk_26_path}")
        return dtk_26_path

    # 3. /opt/dtk 软链
    if os.path.isdir(DTK_SYMLINK):
        resolved = os.path.realpath(DTK_SYMLINK)
        logger.debug(f"检测到 DTK (symlink): {resolved}")
        return resolved

    # 4. 默认兜底
    logger.debug(f"使用默认 DTK: {dtk_default}")
    return dtk_default
