#!/usr/bin/env python3
"""
工具辅助函数
"""
import logging
import os
import shutil
import subprocess
import sys

from . import __version__
from .config import CYAN, GREEN, GREY, RED, RESET
from .config_manager import get_config

logger = logging.getLogger(__name__)


def view_log(log_type: str) -> int:
    """查看日志文件
    
    Args:
        log_type: 日志类型，如 'build_py', 'build_cpp' 等
    
    Returns:
        命令执行结果
    """
    config = get_config()
    log_files = config.log_files
    
    file_path = log_files.get(log_type, "")
    if not file_path:
        logger.error(f"未知日志类型: {log_type}")
        print(f"{RED}❌ Unknown log type: {log_type}{RESET}")
        return 1
    
    if os.path.isfile(file_path):
        logger.info(f"查看日志: {file_path}")
        print(f"{GREEN}📄 Tailing log file: {CYAN}{file_path}{RESET}")
        try:
            if shutil.which("less"):
                return subprocess.call(["less", "+F", "-R", file_path])
            return subprocess.call(["tail", "-f", "-n", "50", file_path])
        except KeyboardInterrupt:
            # 补一个空换行防止 \r 带来的覆盖前行现象
            print()
            print(f"{GREY}Log tail stopped by user.{RESET}")
            return 0
    
    logger.warning(f"日志文件不存在: {file_path}")
    print(f"{RED}❌ Log file not found:{RESET} {file_path}")
    print(f"   {GREY}(Task might not have started yet){RESET}")
    return 0


def check_te() -> int:
    """检查 TE 环境状态
    
    Returns:
        检查结果状态码
    """
    config = get_config()
    
    print(f"{GREEN}🔍 TE Environment Check{RESET}")
    print(f"   {GREY}├─ TE CLI Version:{RESET} {CYAN}v{__version__}{RESET}")
    
    # 1. Python Build Artifact
    print(f"   {GREY}├─ [1] Python Build Artifact:{RESET}")
    _check_python_artifact(config.te_path)
    
    # 2. C++ Test Build Artifact
    print(f"   {GREY}├─ [2] C++ Test Binary:{RESET}")
    _check_cpp_artifact(config.te_path)
    
    # 3. Python Import
    print(f"   {GREY}└─ [3] Python Import Check:{RESET}")
    _check_python_import()
    
    return 0


def _check_python_artifact(te_path: str) -> None:
    """检查 Python 构建产物"""
    py_ext = _find_file(te_path, "transformer_engine_torch*.so", maxdepth=2)
    
    if py_ext and os.path.isfile(py_ext):
        mod_time = _get_file_time(py_ext)
        file_size = _get_file_size(py_ext)
        
        print(f"   {GREY}│      ├─ File:{RESET}   {GREEN}{os.path.basename(py_ext)}{RESET}")
        print(f"   {GREY}│      ├─ Size:{RESET}   {CYAN}{file_size}{RESET}")
        print(f"   {GREY}│      └─ Modified:{RESET} {CYAN}{mod_time}{RESET}")
    else:
        print(f"   {GREY}│      └─ Status:{RESET} {RED}Not Found (Build failed?){RESET}")


def _check_cpp_artifact(te_path: str) -> None:
    """检查 C++ 构建产物"""
    cpp_test_bin = os.path.join(te_path, "tests/cpp/build/operator/test_operator")
    
    if os.path.isfile(cpp_test_bin):
        mod_time = _get_file_time(cpp_test_bin)
        file_size = _get_file_size(cpp_test_bin)
        
        print(f"   {GREY}│      ├─ File:{RESET}   {GREEN}test_operator{RESET}")
        print(f"   {GREY}│      ├─ Size:{RESET}   {CYAN}{file_size}{RESET}")
        print(f"   {GREY}│      └─ Modified:{RESET} {CYAN}{mod_time}{RESET}")
    else:
        print(f"   {GREY}│      └─ Status:{RESET} {RED}Not Found (C++ Tests not built){RESET}")


def _check_python_import() -> None:
    """检查 Python 导入"""
    import_cmd = "import sys; import transformer_engine; print(transformer_engine.__file__)"
    check_cmd = [sys.executable, "-c", import_cmd]
    
    try:
        result = subprocess.run(check_cmd, capture_output=True, text=True)

        # If running inside a venv and import fails, retry with system python.
        if (
            result.returncode != 0
            and os.environ.get("VIRTUAL_ENV")
            and sys.executable != "/usr/bin/python3"
        ):
            result = subprocess.run(["/usr/bin/python3", "-c", import_cmd], capture_output=True, text=True)

        if result.returncode == 0:
            loc_out = result.stdout.rstrip("\n")
            if result.stderr:
                print(result.stderr.rstrip("\n"))
            print(f"          └─ Result: {GREEN}Success{RESET} -> {CYAN}{loc_out}{RESET}")
        else:
            print(f"          └─ Result: {RED}Import Failed!{RESET}")
    except Exception as e:
        logger.error(f"导入检查失败: {e}")
        print(f"          └─ Result: {RED}Import Failed!{RESET}")


def _find_file(path: str, pattern: str, maxdepth: int = 2) -> str:
    """查找文件"""
    try:
        find_out = subprocess.check_output(
            ["find", path, "-maxdepth", str(maxdepth), "-name", pattern],
            text=True,
        )
        for line in find_out.splitlines():
            if line.strip():
                return line.strip()
    except subprocess.CalledProcessError:
        pass
    return ""


def _get_file_time(filepath: str) -> str:
    """获取文件修改时间"""
    try:
        mod_time = subprocess.check_output(
            ["stat", "-c", "%y", filepath], text=True
        ).strip()
        return mod_time.split(".")[0]
    except subprocess.CalledProcessError:
        return ""


def _get_file_size(filepath: str) -> str:
    """获取文件大小（人类可读）"""
    try:
        size = subprocess.check_output(
            ["stat", "-c", "%s", filepath], text=True
        ).strip()
        return subprocess.check_output(
            ["numfmt", "--to=iec-i", "--suffix=B", size], text=True
        ).strip()
    except subprocess.CalledProcessError:
        return ""
