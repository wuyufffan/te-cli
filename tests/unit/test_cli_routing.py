#!/usr/bin/env python3
"""
CLI 路由单元测试 - 使用参数化减少重复
"""
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent.parent / "te_python"))
import cli


@pytest.fixture(autouse=True)
def reset_sys_argv():
    """每个测试后重置 sys.argv"""
    original_argv = sys.argv.copy()
    yield
    sys.argv = original_argv


@pytest.fixture
def mock_helpers():
    """Mock 所有 helper 函数"""
    mocks = {
        "print_help": MagicMock(return_value=0),
        "show_processes": MagicMock(return_value=0),
        "check_te": MagicMock(return_value=0),
        "kill_build_task": MagicMock(return_value=0),
        "build_te_func": MagicMock(return_value=0),
        "build_te_func_incremental": MagicMock(return_value=0),
        "build_cpp_test_func": MagicMock(return_value=0),
        "build_clean_cpp": MagicMock(return_value=0),
        "build_all_func": MagicMock(return_value=0),
        "rebuild_dev": MagicMock(return_value=0),
        "run_l0cpp": MagicMock(return_value=0),
        "run_l0torch": MagicMock(return_value=0),
        "run_l1torch": MagicMock(return_value=0),
        "view_log": MagicMock(return_value=0),
        "kill_test_task": MagicMock(return_value=0),
    }
    with patch.multiple(cli, **mocks):
        yield mocks


# =============================================================================
# 基础命令
# =============================================================================

@pytest.mark.unit
@pytest.mark.cli
class TestBasicCommands:
    """基础命令测试"""
    
    @pytest.mark.parametrize("flag", ["-h", "--help"])
    def test_help_flags(self, mock_helpers, flag):
        """测试帮助参数（短格式和长格式）"""
        assert cli.main([flag]) == 0
        mock_helpers["print_help"].assert_called()
    
    def test_no_args_shows_help(self, mock_helpers):
        """无参数时显示帮助"""
        assert cli.main([]) == 0
        mock_helpers["print_help"].assert_called_once()


@pytest.mark.unit
@pytest.mark.cli
class TestProcessCommands:
    """进程和状态查询命令"""
    
    @pytest.mark.parametrize("flag,expected", [
        ("-p", "show_processes"),
        ("--process", "show_processes"),
        ("-s", "check_te"),
        ("--status", "check_te"),
    ])
    def test_process_status_flags(self, mock_helpers, flag, expected):
        """测试进程和状态查询参数"""
        sys.argv = ["te", flag]
        assert cli.main() == 0
        mock_helpers[expected].assert_called_once()


# =============================================================================
# 构建命令 - 使用参数化
# =============================================================================

@pytest.mark.unit
@pytest.mark.cli
@pytest.mark.build
class TestBuildCommands:
    """构建命令测试"""
    
    @pytest.mark.parametrize("args,expected", [
        # Python 构建
        (["-b", "-c"], "build_te_func_incremental"),
        (["--build", "--core"], "build_te_func_incremental"),
        (["-b", "-c", "-d"], "build_te_func"),
        (["--build", "--core", "--clean"], "build_te_func"),
        (["-b", "-c", "-l"], "view_log"),
        # C++ 构建
        (["-b", "-t"], "build_cpp_test_func"),
        (["--build", "--test"], "build_cpp_test_func"),
        (["-b", "-t", "-l"], "view_log"),
        (["-b", "-t", "-d"], "build_cpp_test_func"),
        # 重建
        (["-b", "-r"], "rebuild_dev"),
        (["--rebuild"], "rebuild_dev"),
        (["-b", "-r", "-d"], "build_all_func"),
        (["-b", "-r", "-l"], "view_log"),
        (["-b", "-r", "-d", "-l"], "view_log"),
        # 终止构建
        (["-b", "-k"], "kill_build_task"),
    ])
    def test_build_commands(self, mock_helpers, args, expected):
        """测试各种构建命令组合"""
        sys.argv = ["te"] + args
        result = cli.main()
        
        if args == ["-b", "-t", "-d"]:
            # 清理+构建会调用两个函数
            mock_helpers["build_clean_cpp"].assert_called_once()
        
        mock_helpers[expected].assert_called_once()
    
    def test_build_cpp_clean_calls_both(self, mock_helpers):
        """测试 C++ 清理构建会调用清理和构建两个函数"""
        sys.argv = ["te", "-b", "-t", "-d"]
        assert cli.main() == 0
        mock_helpers["build_clean_cpp"].assert_called_once()
        mock_helpers["build_cpp_test_func"].assert_called_once()


# =============================================================================
# 测试命令
# =============================================================================

@pytest.mark.unit
@pytest.mark.cli
class TestTestCommands:
    """测试执行命令"""
    
    @pytest.mark.parametrize("args,expected_func,expected_args", [
        # L0 C++
        (["-0", "-c"], "run_l0cpp", None),
        (["--l0", "--cpp"], "run_l0cpp", None),
        (["-0", "-c", "-l"], "view_log", "l0cpp"),
        (["-0", "-c", "-k"], "kill_test_task", ("qa/L0_cppunittest/test.sh", "L0 CPP Test")),
        # L0 PyTorch
        (["-0", "-t"], "run_l0torch", None),
        (["-0", "-t", "-l"], "view_log", "l0torch"),
        (["-0", "-t", "-k"], "kill_test_task", ("qa/L0_pytorch_unittest/test.sh", "L0 Torch Test")),
        # L1 PyTorch
        (["-1", "-t"], "run_l1torch", None),
        (["-1", "-t", "-l"], "view_log", "l1torch"),
        (["-1", "-t", "-k"], "kill_test_task", ("qa/L1_pytorch_distributed_unittest/test.sh", "L1 Torch Test")),
    ])
    def test_test_commands(self, mock_helpers, args, expected_func, expected_args):
        """测试各种测试命令组合"""
        assert cli.main(args) == 0
        
        if expected_args:
            mock_helpers[expected_func].assert_called_once_with(*expected_args if isinstance(expected_args, tuple) else [expected_args])
        else:
            mock_helpers[expected_func].assert_called_once()


# =============================================================================
# 参数冲突和错误处理
# =============================================================================

@pytest.mark.unit
@pytest.mark.cli
class TestArgumentValidation:
    """参数验证测试"""
    
    @pytest.mark.parametrize("args", [
        ["-b", "-c", "-t"],      # core + test 冲突
        ["-b", "-r", "-c"],      # rebuild + core 冲突
        ["-b", "-r", "-t"],      # rebuild + test 冲突
    ])
    def test_conflicting_arguments(self, mock_helpers, args):
        """测试参数冲突检测"""
        sys.argv = ["te"] + args
        assert cli.main() == 1  # 应该返回错误
    
    @pytest.mark.parametrize("args", [
        ["--unknown"],
        ["-x"],
    ])
    def test_unknown_arguments(self, mock_helpers, args):
        """测试未知参数处理 - argparse 对未知参数返回 2"""
        result = cli.main(args)
        assert result != 0  # 应该返回非零值
