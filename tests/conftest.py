#!/usr/bin/env python3
"""
pytest 全局 fixtures 和配置
"""
import os
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# 将 te-cli 根目录添加到路径
TE_CLI_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(TE_CLI_PATH))


def pytest_configure(config):
    """注册自定义标记"""
    config.addinivalue_line("markers", "serial: 串行执行的测试（进程管理相关）")
    config.addinivalue_line("markers", "parallel: 可并发执行的测试")
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")


# =============================================================================
# 基础路径 Fixtures
# =============================================================================

@pytest.fixture
def repo_root():
    """返回仓库根目录路径"""
    return Path(__file__).parent.parent


@pytest.fixture
def mock_te_path(tmp_path):
    """创建模拟的 TE 路径结构"""
    te_path = tmp_path / "TransformerEngine"
    te_path.mkdir()
    
    for subdir in ["tests/cpp", "qa/L0_cppunittest", "qa/L0_pytorch_unittest", 
                   "qa/L1_pytorch_distributed_unittest", "transformer_engine/common/swizzle",
                   "3rdparty/hipify_torch"]:
        (te_path / subdir).mkdir(parents=True)
    
    return te_path


# =============================================================================
# Mock Fixtures - 合并为通用 mock
# =============================================================================

@pytest.fixture
def mock_subprocess():
    """统一 mock 所有 subprocess 函数"""
    with patch("subprocess.run") as run, \
         patch("subprocess.call") as call, \
         patch("subprocess.check_output") as check_output, \
         patch("subprocess.check_call") as check_call, \
         patch("subprocess.Popen") as popen:
        
        popen_instance = MagicMock()
        popen_instance.pid = 12345
        popen_instance.returncode = 0
        popen.return_value = popen_instance
        
        yield {
            "run": run,
            "call": call,
            "check_output": check_output,
            "check_call": check_call,
            "popen": popen,
            "popen_instance": popen_instance,
        }


@pytest.fixture
def mock_os_operations():
    """统一 mock 文件系统操作"""
    with patch("os.path.exists") as exists, \
         patch("os.path.getsize") as getsize, \
         patch("os.path.isdir") as isdir, \
         patch("os.path.isfile") as isfile, \
         patch("os.stat") as stat:
        
        stat_obj = MagicMock()
        stat_obj.st_mtime = 1234567890
        stat_obj.st_size = 1024
        stat.return_value = stat_obj
        getsize.return_value = 1024
        
        yield {
            "exists": exists,
            "getsize": getsize,
            "isdir": isdir,
            "isfile": isfile,
            "stat": stat,
            "stat_obj": stat_obj,
        }


@pytest.fixture
def mock_common_utils():
    """Mock common_utils 函数"""
    with patch("common_utils.pgrep") as pgrep, \
         patch("common_utils.pkill") as pkill, \
         patch("common_utils.get_human_size") as size, \
         patch("common_utils.get_process_start_time") as start, \
         patch("common_utils.get_process_elapsed") as elapsed:
        
        pgrep.return_value = []
        pkill.return_value = 0
        size.return_value = "4.0K"
        start.return_value = "Mon Jan 1 00:00:00 2024"
        elapsed.return_value = "00:05:00"
        
        yield {
            "pgrep": pgrep,
            "pkill": pkill,
            "size": size,
            "start": start,
            "elapsed": elapsed,
        }


@pytest.fixture
def mock_input():
    """Mock input 函数"""
    with patch("builtins.input") as mock:
        yield mock


# =============================================================================
# 集成测试 Fixtures
# =============================================================================

@pytest.fixture
def create_test_process():
    """创建真实测试进程，自动清理"""
    processes = []
    
    def _create(cmd=None, sleep_time=10):
        if cmd is None:
            cmd = ["sleep", str(sleep_time)]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        processes.append(proc)
        return proc
    
    yield _create
    
    for proc in processes:
        try:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=2)
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                proc.kill()
            except ProcessLookupError:
                pass


@pytest.fixture
def minimal_cmake_project(tmp_path):
    """创建最小 CMake 项目"""
    project_dir = tmp_path / "cmake_project"
    project_dir.mkdir()
    
    (project_dir / "CMakeLists.txt").write_text("""cmake_minimum_required(VERSION 3.10)
project(TestProject LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 11)
add_executable(test_app main.cpp)
""")
    
    (project_dir / "main.cpp").write_text("""#include <iostream>
int main() {
    std::cout << "Hello from CMake!" << std::endl;
    return 0;
}
""")
    
    return project_dir


# =============================================================================
# 辅助函数
# =============================================================================

def run_cli_with_args(args_list):
    """使用指定参数运行 CLI main 函数"""
    import cli
    original_argv = sys.argv
    try:
        sys.argv = ["te"] + args_list
        return cli.main()
    finally:
        sys.argv = original_argv
