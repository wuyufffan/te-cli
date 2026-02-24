#!/usr/bin/env python3
"""
进程管理辅助函数
"""
import logging
import os
import time
from typing import List, Optional

from config import RED, YELLOW, GREEN, CYAN, GREY, BLUE, RESET
from config_manager import get_config
from common_utils import (
    get_human_size,
    pgrep,
    pkill,
    get_process_start_time,
    get_process_elapsed,
)

logger = logging.getLogger(__name__)


def show_processes() -> int:
    """显示运行中的 TE 任务"""
    config = get_config()
    print(f"{GREEN}📋 Running TE Tasks:{RESET}")
    print("")
    
    found = 0
    log_files = config.log_files
    
    # 检查构建任务
    build_pids = pgrep(r"python3 -m pip|cmake --build")
    if build_pids:
        found = 1
        latest_log = _find_latest_log([
            log_files["build_py"],
            log_files["build_cpp"],
            log_files["rebuild"],
            log_files["build_all"]
        ])
        _print_build_task(build_pids, latest_log)
    
    # 检查测试任务
    test_patterns = [
        (r"qa/L0_cppunittest/test.sh", "L0 CPP Test", "te -0 -c"),
        (r"qa/L0_pytorch_unittest/test.sh", "L0 Torch Test", "te -0 -t"),
        (r"qa/L1_pytorch_distributed_unittest/test.sh", "L1 Torch Test", "te -1 -t"),
    ]
    
    for pattern, name, cmd_prefix in test_patterns:
        pids = pgrep(pattern)
        if pids:
            found = 1
            _print_test_task(pids, name, cmd_prefix)
    
    if found == 0:
        print(f"   {GREY}No running tasks found.{RESET}")
    
    return 0


def _find_latest_log(log_candidates: List[str]) -> str:
    """找到最新的日志文件"""
    latest_log = ""
    latest_time = 0
    
    for log_file in log_candidates:
        if os.path.exists(log_file):
            try:
                mod_time = os.stat(log_file).st_mtime
                if mod_time > latest_time:
                    latest_time = mod_time
                    latest_log = log_file
            except OSError:
                pass
    
    return latest_log


def _get_view_command(log_file: str) -> str:
    """根据日志文件获取查看命令"""
    config = get_config()
    log_files = config.log_files
    
    if log_file == log_files["build_py"]:
        return "te -b -c -l"
    elif log_file == log_files["build_cpp"]:
        return "te -b -t -l"
    elif log_file == log_files["rebuild"]:
        return "te -b -r -l"
    elif log_file == log_files["build_all"]:
        return "te -b -r -d -l"
    return "te -b -c -l / te -b -t -l / te -b -r -l"


def _print_build_task(pids: List[str], latest_log: str) -> None:
    """打印构建任务信息"""
    view_cmd = _get_view_command(latest_log)
    pid_display = " ".join(pids) + " "
    
    print(f"{CYAN}[Build Task]{RESET}")
    print(f"   {GREY}├─ PIDs:{RESET}  {RED}{pid_display}{RESET}")
    print(f"   {GREY}├─ View:{RESET}  {view_cmd}")
    print(f"   {GREY}└─ Kill:{RESET}  {YELLOW}te -b -k{RESET}")
    print("")


def _print_test_task(pids: List[str], name: str, cmd_prefix: str) -> None:
    """打印测试任务信息"""
    pid_display = " ".join(pids) + " "
    
    print(f"{CYAN}[{name}]{RESET}")
    print(f"   {GREY}├─ PIDs:{RESET}  {RED}{pid_display}{RESET}")
    print(f"   {GREY}├─ View:{RESET}  {cmd_prefix} -l")
    print(f"   {GREY}└─ Kill:{RESET}  {YELLOW}{cmd_prefix} -k{RESET}")
    print("")


def confirm_if_log_exists(log_file: str) -> int:
    """确认日志文件是否存在并提示用户"""
    if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
        logger.warning(f"日志文件已存在: {log_file}")
        
        print(f"{YELLOW}⚠️  Log file exists and is not empty!{RESET}")
        print(f"   {GREY}├─ Path:{RESET} {CYAN}{log_file}{RESET}")
        
        file_size = get_human_size(log_file)
        print(f"   {GREY}└─ Size:{RESET} {file_size}")
        
        try:
            choice = input(f"   ❓ Overwrite and continue? [y/N]: ")
        except EOFError:
            choice = ""
        
        if choice.strip() in ("y", "Y"):
            logger.info("用户选择覆盖日志文件")
            return 0
        else:
            print(f"{RED}🛑 Canceled by user.{RESET}")
            return 1
    
    return 0


def check_task_running(
    pattern: str,
    task_name: str,
    log_file: str = "",
    view_cmd: str = "",
    kill_cmd: str = "",
) -> int:
    """检查任务是否正在运行"""
    pids = pgrep(pattern)
    if not pids:
        return 0
    
    logger.warning(f"检测到任务正在运行: {task_name} (PIDs: {pids})")
    
    # 自动检测日志文件
    running_log = log_file
    if not running_log:
        running_log = _detect_running_log()
    
    # 自动检测查看命令
    view_command = view_cmd
    if not view_command and running_log:
        view_command = _get_view_command(running_log)
    
    # 显示错误信息
    print(f"{RED}❌ Task Already Running!{RESET}")
    print(f"   {GREY}├─ Task:{RESET}  {CYAN}{task_name}{RESET}")
    print(f"   {GREY}├─ PIDs:{RESET}  {RED}{' '.join(pids)} {RESET}")
    
    if running_log:
        print(f"   {GREY}├─ Log:{RESET}   {BLUE}{running_log}{RESET}")
    if view_command:
        print(f"   {GREY}├─ View:{RESET}  {view_command}")
    
    kill_display = kill_cmd if kill_cmd else f"kill {pids[0]}"
    print(f"   {GREY}└─ Kill:{RESET}  {YELLOW}{kill_display}{RESET}")
    
    return 1


def _detect_running_log() -> str:
    """检测正在运行的构建任务对应的日志文件"""
    config = get_config()
    
    if not (pgrep("python3 -m pip") or pgrep("cmake --build")):
        return ""
    
    log_candidates = [
        config.log_files["build_py"],
        config.log_files["rebuild"],
        config.log_files["build_all"],
        config.log_files["build_cpp"]
    ]
    
    return _find_latest_log(log_candidates)


def _kill_task_logic(pids: List[str], pattern: str, task_name: str) -> int:
    """终止任务的通用逻辑"""
    oldest_pid = pids[0]
    start_time = get_process_start_time(oldest_pid)
    elapsed = get_process_elapsed(oldest_pid)
    
    logger.info(f"准备终止任务: {task_name} (PID: {oldest_pid})")
    
    print(f"{YELLOW}⚠️  {task_name} is running:{RESET}")
    print(f"   {GREY}├─ PIDs:{RESET}    {RED}{' '.join(pids)} {RESET}")
    print(f"   {GREY}├─ Started:{RESET} {CYAN}{start_time}{RESET}")
    print(f"   {GREY}└─ Elapsed:{RESET} {CYAN}{elapsed}{RESET}")
    print("")
    
    try:
        choice = input(f"   {RED}Kill this task? [y/N]:{RESET} ")
    except EOFError:
        choice = ""
    
    if choice.strip() in ("y", "Y"):
        logger.info(f"终止任务: {task_name}")
        pkill(pattern)
        time.sleep(1)
        print(f"{GREEN}✅ {task_name} killed.{RESET}")
        return 0
    else:
        print(f"{CYAN}ℹ️  Cancelled.{RESET}")
        return 1


def kill_build_task() -> int:
    """终止构建任务"""
    pattern = r"python3 -m pip|cmake --build"
    pids = pgrep(pattern)
    
    if not pids:
        print(f"{YELLOW}⚠️  No build task running.{RESET}")
        return 0
    
    kill_pattern = r"python3 -m pip|cmake --build|bash -c.*pip"
    return _kill_task_logic(pids, kill_pattern, "Build task")


def kill_test_task(pattern: str, task_name: str) -> int:
    """终止测试任务"""
    pids = pgrep(pattern)
    
    if not pids:
        print(f"{YELLOW}⚠️  No {task_name} running.{RESET}")
        return 0
    
    return _kill_task_logic(pids, pattern, task_name)
