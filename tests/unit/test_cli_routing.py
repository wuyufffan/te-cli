#!/usr/bin/env python3
"""
CLI 路由单元测试 - 使用参数化减少重复
"""
import sys
import pytest
from unittest.mock import patch, MagicMock

import core.cli as cli
from core.config_manager import TIMESTAMP_EXAMPLE


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
        "route_named_command": MagicMock(return_value=0),
        "init_config": MagicMock(return_value=None),
        "setup_logging": MagicMock(return_value=None),
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
        "route_build_named_command": MagicMock(return_value=0),
        "route_rebuild_named_command": MagicMock(return_value=0),
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

    def test_help_subcommand(self, mock_helpers):
        assert cli.main(["help"]) == 0
        mock_helpers["route_named_command"].assert_called_once_with(["help"])
    
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
        # C++ 构建
        (["-b", "-t"], "build_cpp_test_func"),
        (["--build", "--test"], "build_cpp_test_func"),
        # 重建
        (["-b", "-r"], "rebuild_dev"),
        (["-b", "--rebuild"], "rebuild_dev"),
    ])
    def test_build_commands(self, mock_helpers, args, expected, capsys):
        """测试各种构建命令组合"""
        sys.argv = ["te"] + args
        result = cli.main()

        out = capsys.readouterr().out
        assert "旧 flag 兼容入口将逐步退出" in out
        mock_helpers[expected].assert_called_once()

    def test_build_only_flag_shows_help(self, mock_helpers):
        """仅 -b 无子命令应回退帮助"""
        assert cli.main(["-b"]) == 0
        mock_helpers["print_help"].assert_called_once()

    @pytest.mark.parametrize("args", [
        ["-b", "-c", "-d"],
        ["--build", "--core", "--clean"],
        ["-b", "-c", "-l"],
        ["-b", "-t", "-l"],
        ["-b", "-t", "-d"],
        ["-b", "-r", "-d"],
        ["-b", "-r", "-l"],
        ["-b", "-r", "-d", "-l"],
        ["-b", "-k"],
    ])
    def test_removed_legacy_build_variants_fail_with_migration(self, mock_helpers, args, capsys):
        sys.argv = ["te"] + args
        assert cli.main() == 1
        out = capsys.readouterr().out
        assert "旧 flag 的 -l / -k / -d 兼容入口已收缩" in out
        mock_helpers["build_te_func"].assert_not_called()
        mock_helpers["build_clean_cpp"].assert_not_called()
        mock_helpers["build_cpp_test_func"].assert_not_called()


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
        # L0 PyTorch
        (["-0", "-t"], "run_l0torch", None),
        # L1 PyTorch
        (["-1", "-t"], "run_l1torch", None),
    ])
    def test_test_commands(self, mock_helpers, args, expected_func, expected_args, capsys):
        """测试各种测试命令组合"""
        assert cli.main(args) == 0
        out = capsys.readouterr().out
        assert "旧 flag 兼容入口将逐步退出" in out
        
        if expected_args:
            mock_helpers[expected_func].assert_called_once_with(*expected_args if isinstance(expected_args, tuple) else [expected_args])
        else:
            mock_helpers[expected_func].assert_called_once()

    @pytest.mark.parametrize("args", [
        ["-0", "-c", "-l"],
        ["-0", "-c", "-k"],
        ["-0", "-t", "-l"],
        ["-0", "-t", "-k"],
        ["-1", "-t", "-l"],
        ["-1", "-t", "-k"],
    ])
    def test_removed_legacy_test_variants_fail_with_migration(self, mock_helpers, args, capsys):
        assert cli.main(args) == 1
        out = capsys.readouterr().out
        assert "旧 flag 的 -l / -k / -d 兼容入口已收缩" in out
        mock_helpers["view_log"].assert_not_called()
        mock_helpers["kill_test_task"].assert_not_called()

    def test_gpu_flag_passed_to_l0cpp(self, mock_helpers):
        assert cli.main(["-0", "-c", "-g", "3"]) == 0
        mock_helpers["run_l0cpp"].assert_called_once_with(gpu="3")

    def test_gpu_flag_passed_to_l0torch(self, mock_helpers):
        assert cli.main(["-0", "-t", "-g", "5,6"]) == 0
        mock_helpers["run_l0torch"].assert_called_once_with(gpu="5,6")


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


# =============================================================================
# 追加分支覆盖
# =============================================================================


@pytest.mark.unit
@pytest.mark.cli
class TestAdditionalBranches:
    def test_route_test_without_level_shows_help(self, mock_helpers):
        # 仅 -t/-test 而无 -0/-1，route_test_command 会回退到 print_help
        sys.argv = ["te", "-t"]
        assert cli.main() == 0
        mock_helpers["print_help"].assert_called()

    def test_verbose_sets_debug_level(self, mock_helpers):
        # -V 应使 init_config/use DEBUG, setup_logging use logging.DEBUG
        sys.argv = ["te", "-V", "-p"]
        assert cli.main() == 0
        mock_helpers["init_config"].assert_called_once_with(log_level='DEBUG')
        mock_helpers["setup_logging"].assert_called_once_with(level=cli.logging.DEBUG)
        mock_helpers["show_processes"].assert_called_once()

    def test_version_flag(self, mock_helpers, capsys):
        sys.argv = ["te", "-v"]
        assert cli.main() == 0
        captured = capsys.readouterr()
        assert "TE CLI v1.0.0" in captured.out

    def test_check_env_flag(self, mock_helpers):
        with patch("core.cli.check_environment", return_value=True) as mock_check_env:
            sys.argv = ["te", "--check-env"]
            assert cli.main() == 0
            mock_check_env.assert_called_once_with(quiet=False)

    def test_check_env_failure_returns_1(self, mock_helpers):
        with patch("core.cli.check_environment", return_value=False) as mock_check_env:
            assert cli.main(["--check-env"]) == 1
            mock_check_env.assert_called_once_with(quiet=False)

    def test_main_catches_generic_exception(self, mock_helpers):
        with patch.object(cli, "route_command", side_effect=RuntimeError("boom")):
            assert cli.main(["-p"]) == 1

    def test_main_catches_system_exit_non_int(self, mock_helpers):
        with patch("core.cli.parse_args", side_effect=SystemExit(None)):
            assert cli.main(["-p"]) == 1

    def test_l0_alone_shows_help(self, mock_helpers):
        assert cli.main(["-0"]) == 0
        mock_helpers["print_help"].assert_called_once()

    def test_l1_alone_shows_help(self, mock_helpers):
        assert cli.main(["-1"]) == 0
        mock_helpers["print_help"].assert_called_once()

    def test_rebuild_without_build_flag_does_not_trigger_build(self, mock_helpers):
        """te --rebuild (无 -b) 不应触发编译，应回退到帮助"""
        assert cli.main(["--rebuild"]) == 0
        mock_helpers["rebuild_dev"].assert_not_called()
        mock_helpers["build_all_func"].assert_not_called()
        mock_helpers["print_help"].assert_called()

    @pytest.mark.parametrize("argv", [
        ["run", "l0cpp"],
        ["log", "list"],
        ["build", "py"],
        ["rebuild", "cpp"],
        ["sum", "/tmp/test.log"],
    ])
    def test_named_commands_are_routed(self, mock_helpers, argv):
        assert cli.main(argv) == 0
        mock_helpers["route_named_command"].assert_called_once_with(argv)


@pytest.mark.unit
@pytest.mark.cli
def test_print_help_real_function_executes_lines(capsys):
    # 不使用 mock_helpers，直接执行真实 print_help 覆盖帮助输出行
    assert cli.print_help() == 0
    out = capsys.readouterr().out
    assert "TE 开发工具命令行" in out
    assert "快速上手" in out
    assert "兼容入口" in out
    assert TIMESTAMP_EXAMPLE in out


@pytest.mark.unit
@pytest.mark.cli
def test_print_help_contains_recommended_paths(capsys):
    # 锁定根帮助的信息架构，防止再次退化成参数堆砌
    assert cli.print_help() == 0
    out = capsys.readouterr().out
    assert "te run help" in out
    assert "te build help" in out
    assert "te rebuild help" in out
    assert f"te log list {TIMESTAMP_EXAMPLE}" in out
    assert "te log watch" not in out
    assert "逐步退出" in out


@pytest.mark.unit
@pytest.mark.cli
def test_route_named_build_command_uses_build_router():
    with patch.object(cli, "route_build_named_command", return_value=0) as mock_route:
        assert cli.route_named_command(["build", "py"]) == 0
        mock_route.assert_called_once_with(["py"])


@pytest.mark.unit
@pytest.mark.cli
def test_route_named_rebuild_command_uses_rebuild_router():
    with patch.object(cli, "route_rebuild_named_command", return_value=0) as mock_route:
        assert cli.route_named_command(["rebuild", "cpp"]) == 0
        mock_route.assert_called_once_with(["cpp"])


@pytest.mark.unit
@pytest.mark.cli
def test_print_legacy_help_real_function_executes_lines(capsys):
    assert cli.print_legacy_help() == 0
    out = capsys.readouterr().out
    assert "te [简化参数组合]" in out
    assert "仍保留的旧兼容入口" in out
    assert "快速上手" not in out


@pytest.mark.unit
@pytest.mark.cli
def test_route_named_help_old_uses_legacy_help(capsys):
    assert cli.route_named_command(["help", "old"]) == 0
    out = capsys.readouterr().out
    assert "te [简化参数组合]" in out
    assert "等价于 te run l0cpp" in out


@pytest.mark.unit
@pytest.mark.cli
@pytest.mark.build
class TestBuildSemantics:
    """区分 -b -c / -b -t / -b -r 的语义"""

    def test_bc_only_calls_python_incremental(self, mock_helpers):
        assert cli.main(["-b", "-c"]) == 0
        mock_helpers["build_te_func_incremental"].assert_called_once()
        mock_helpers["build_te_func"].assert_not_called()
        mock_helpers["build_cpp_test_func"].assert_not_called()
        mock_helpers["build_all_func"].assert_not_called()
        mock_helpers["rebuild_dev"].assert_not_called()

    def test_bt_only_calls_cpp_build(self, mock_helpers):
        assert cli.main(["-b", "-t"]) == 0
        mock_helpers["build_cpp_test_func"].assert_called_once()
        mock_helpers["build_clean_cpp"].assert_not_called()
        mock_helpers["build_te_func_incremental"].assert_not_called()
        mock_helpers["build_te_func"].assert_not_called()
        mock_helpers["build_all_func"].assert_not_called()
        mock_helpers["rebuild_dev"].assert_not_called()

    def test_br_only_calls_rebuild_dev(self, mock_helpers):
        assert cli.main(["-b", "-r"]) == 0
        mock_helpers["rebuild_dev"].assert_called_once()
        mock_helpers["build_all_func"].assert_not_called()
        mock_helpers["build_te_func_incremental"].assert_not_called()
        mock_helpers["build_te_func"].assert_not_called()
        mock_helpers["build_cpp_test_func"].assert_not_called()
