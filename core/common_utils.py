#!/usr/bin/env python3
"""
通用系统工具函数
提供对系统命令的封装
"""
import logging
import subprocess
from typing import List

logger = logging.getLogger(__name__)


def get_human_size(filepath: str) -> str:
    """获取文件的人类可读大小
    
    Args:
        filepath: 文件路径
    
    Returns:
        人类可读的大小字符串，如 "4.0K"
    """
    try:
        # du -h returns "4.0K    filename", we need just "4.0K"
        output = subprocess.check_output(["du", "-h", filepath], text=True).strip()
        return output.split()[0]
    except Exception as e:
        logger.debug(f"获取文件大小失败: {filepath}, {e}")
        return "0"


def pgrep(pattern: str) -> List[str]:
    """使用 pgrep 查找匹配的进程
    
    Args:
        pattern: 匹配模式
    
    Returns:
        匹配的 PID 列表
    """
    try:
        output = subprocess.check_output(["pgrep", "-f", pattern], text=True)
        # Filter empty lines
        pids = [line.strip() for line in output.splitlines() if line.strip()]
        logger.debug(f"pgrep '{pattern}' 找到 {len(pids)} 个进程: {pids}")
        return pids
    except subprocess.CalledProcessError:
        return []


def pkill(pattern: str, signal: str = "-9") -> int:
    """使用 pkill 终止匹配的进程
    
    Args:
        pattern: 匹配模式
        signal: 信号，默认为 -9 (SIGKILL)
    
    Returns:
        0 成功，1 失败
    """
    try:
        logger.info(f"终止进程: {pattern} (signal={signal})")
        subprocess.check_call(["pkill", signal, "-f", pattern])
        return 0
    except subprocess.CalledProcessError as e:
        logger.warning(f"终止进程失败: {pattern}, {e}")
        return 1


def get_process_start_time(pid: str) -> str:
    """获取进程启动时间
    
    Args:
        pid: 进程 ID
    
    Returns:
        启动时间字符串
    """
    try:
        return subprocess.check_output(
            ["ps", "-p", pid, "-o", "lstart="], text=True
        ).strip()
    except subprocess.CalledProcessError:
        return ""


def get_process_elapsed(pid: str) -> str:
    """获取进程运行时间
    
    Args:
        pid: 进程 ID
    
    Returns:
        运行时间字符串
    """
    try:
        return subprocess.check_output(
            ["ps", "-p", pid, "-o", "etime="], text=True
        ).strip()
    except subprocess.CalledProcessError:
        return ""
