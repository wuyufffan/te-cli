#!/usr/bin/env python3
"""
测试执行辅助函数
"""
import logging
import os
import subprocess
from pathlib import Path
from typing import Iterable, Optional

from config import BLUE, GREEN, GREY, RESET
from config_manager import get_config
from process_helpers import check_task_running, confirm_if_log_exists

logger = logging.getLogger(__name__)


def _start_test(
    log_file: str,
    pattern: str,
    task_name: str,
    view_cmd: str,
    kill_cmd: str,
    script: str,
    success_message: str,
) -> int:
    """启动测试任务的通用函数
    
    Args:
        log_file: 日志文件路径
        pattern: 进程匹配模式
        task_name: 任务名称
        view_cmd: 查看日志命令
        kill_cmd: 终止任务命令
        script: 执行脚本
        success_message: 成功消息
    
    Returns:
        执行结果状态码
    """
    if check_task_running(pattern, task_name, log_file, view_cmd, kill_cmd) != 0:
        return 1
    
    if confirm_if_log_exists(log_file) != 0:
        return 1
    
    config = get_config()
    parent_dir = str(Path(config.te_path).resolve().parent)
    
    if not os.path.isdir(parent_dir):
        logger.error(f"父目录不存在: {parent_dir}")
        return 2
    
    logger.info(f"启动测试: {task_name}")
    logger.debug(f"日志文件: {log_file}")
    
    with open(log_file, "w", encoding="utf-8") as log_handle:
        subprocess.Popen(
            ["nohup", "bash", "-c", script],
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            cwd=parent_dir,
            start_new_session=True,
        )
    
    print(f"{GREEN}✅ {success_message}{RESET}")
    print(f"   {GREY}└─ Log:{RESET}  {BLUE}{log_file}{RESET}")
    return 0


def _conda_activation() -> str:
    """生成 conda 环境激活脚本"""
    return """
if [ -f '/opt/miniconda3/etc/profile.d/conda.sh' ]; then
    source /opt/miniconda3/etc/profile.d/conda.sh
    if conda env list | grep -q '^te27 '; then conda activate te27; fi
fi
""".strip()


def run_l0cpp(args: Optional[Iterable[str]] = None) -> int:
    """运行 L0 C++ 单元测试"""
    config = get_config()
    log_file = config.log_files["l0cpp"]
    
    script = f"""
{_conda_activation()}
bash {config.te_path}/qa/L0_cppunittest/test.sh
"""
    
    return _start_test(
        log_file=log_file,
        pattern="qa/L0_cppunittest/test.sh",
        task_name="L0 CPP Test",
        view_cmd="te -0 -c -l",
        kill_cmd="te -0 -c -k",
        script=script,
        success_message="L0 CPP Test Started",
    )


def run_l0torch(args: Optional[Iterable[str]] = None) -> int:
    """运行 L0 PyTorch 单元测试"""
    config = get_config()
    log_file = config.log_files["l0torch"]
    
    script = f"""
{_conda_activation()}
bash {config.te_path}/qa/L0_pytorch_unittest/test.sh
"""
    
    return _start_test(
        log_file=log_file,
        pattern="qa/L0_pytorch_unittest/test.sh",
        task_name="L0 Torch Test",
        view_cmd="te -0 -t -l",
        kill_cmd="te -0 -t -k",
        script=script,
        success_message="L0 Torch Test Started",
    )


def run_l1torch(args: Optional[Iterable[str]] = None) -> int:
    """运行 L1 PyTorch 分布式测试"""
    config = get_config()
    log_file = config.log_files["l1torch"]
    
    script = f"bash {config.te_path}/qa/L1_pytorch_distributed_unittest/test.sh"
    
    return _start_test(
        log_file=log_file,
        pattern="qa/L1_pytorch_distributed_unittest/test.sh",
        task_name="L1 Torch Test",
        view_cmd="te -1 -t -l",
        kill_cmd="te -1 -t -k",
        script=script,
        success_message="L1 Distributed Test Started",
    )
