#!/usr/bin/env python3
"""
utils_helpers 模块单元测试
"""
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import core.utils_helpers as utils_helpers
from core.config_manager import Config


@pytest.mark.unit
class TestViewLog:
    """测试 view_log 函数"""
    
    def test_view_unknown_log_type(self, capsys):
        """未知的日志类型"""
        assert utils_helpers.view_log("unknown_type") == 1
        captured = capsys.readouterr()
        assert "Unknown log type" in captured.out
    
    def test_view_log_not_exist(self, capsys):
        """日志文件不存在"""
        with patch("os.path.isfile") as mock:
            mock.return_value = False
            assert utils_helpers.view_log("build_py") == 0
            captured = capsys.readouterr()
            assert "not found" in captured.out.lower()

    def test_view_test_log_uses_latest_timestamped_path(self, tmp_path):
        cfg = Config(work_space=str(tmp_path), te_path=str(tmp_path / "TransformerEngine"))
        log_dir = tmp_path / "logs" / "2026-03-12::12-00-00" / "l0cpp"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "L0_cppunittest_test.log"
        log_file.write_text("hello", encoding="utf-8")

        with patch("core.utils_helpers.get_config", return_value=cfg), \
             patch("shutil.which", return_value=None), \
             patch("subprocess.call", return_value=0) as call:
            assert utils_helpers.view_log("l0cpp") == 0
            assert str(log_file.resolve()) in call.call_args[0][0]
    
    def test_view_log_success_with_less(self):
        """成功查看日志 (支持 less)"""
        with patch("os.path.isfile") as mock, \
             patch("shutil.which") as which_mock, \
             patch("subprocess.call") as call:
            mock.return_value = True
            which_mock.return_value = "/usr/bin/less"
            call.return_value = 0
            
            assert utils_helpers.view_log("build_py") == 0
            call_args = call.call_args[0][0]
            assert call_args[0] == "less"
            assert "+F" in call_args

    def test_view_log_success_fallback_tail(self):
        """成功查看日志 (没有 less 时回退 tail)"""
        with patch("os.path.isfile") as mock, \
             patch("shutil.which") as which_mock, \
             patch("subprocess.call") as call:
            mock.return_value = True
            which_mock.return_value = None
            call.return_value = 0
            
            assert utils_helpers.view_log("build_py") == 0
            call_args = call.call_args[0][0]
            assert call_args[0] == "tail"
    
    def test_view_log_keyboard_interrupt(self):
        """用户中断日志查看"""
        with patch("os.path.isfile") as mock, \
             patch("shutil.which") as which_mock, \
             patch("subprocess.call") as call:
            mock.return_value = True
            which_mock.return_value = None
            call.side_effect = KeyboardInterrupt()
            assert utils_helpers.view_log("build_py") == 0
    
    @pytest.mark.parametrize("log_type", ["build_py", "build_cpp", "rebuild", "build_all"])
    def test_all_log_types(self, log_type):
        """测试所有日志类型映射"""
        with patch("os.path.isfile") as mock, \
             patch("shutil.which") as which_mock, \
             patch("subprocess.call") as call:
            mock.return_value = True
            which_mock.return_value = "/usr/bin/less"
            call.return_value = 0
            assert utils_helpers.view_log(log_type) == 0


@pytest.mark.unit
class TestCheckTe:
    """测试 check_te 函数"""

    def test_check_te_shows_version(self, capsys):
        with patch("subprocess.check_output") as check, \
             patch("subprocess.run") as run:
            check.side_effect = subprocess.CalledProcessError(1, "find")

            result = MagicMock()
            result.returncode = 1
            result.stdout = ""
            result.stderr = ""
            run.return_value = result

            assert utils_helpers.check_te() == 0
            captured = capsys.readouterr()
            assert "TE CLI Version" in captured.out
            assert f"v{utils_helpers.__version__}" in captured.out
    
    def test_check_te_no_artifacts(self, capsys):
        """没有构建产物"""
        with patch("subprocess.check_output") as mock:
            mock.side_effect = subprocess.CalledProcessError(1, "find")
            assert utils_helpers.check_te() == 0
            captured = capsys.readouterr()
            assert "TE Environment" in captured.out
    
    def test_check_te_import_success(self, capsys):
        """Python 导入检查成功"""
        with patch("subprocess.check_output") as check, \
             patch("subprocess.run") as run:
            check.side_effect = subprocess.CalledProcessError(1, "find")
            
            result = MagicMock()
            result.returncode = 0
            result.stdout = "/path/to/transformer_engine/__init__.py\n"
            result.stderr = ""
            run.return_value = result
            
            assert utils_helpers.check_te() == 0
            captured = capsys.readouterr()
            assert "Success" in captured.out or "Import" in captured.out
    
    def test_check_te_import_failure(self, capsys):
        """Python 导入检查失败"""
        with patch("subprocess.check_output") as check, \
             patch("subprocess.run") as run:
            check.side_effect = subprocess.CalledProcessError(1, "find")
            
            result = MagicMock()
            result.returncode = 1
            run.return_value = result
            
            assert utils_helpers.check_te() == 0
            captured = capsys.readouterr()
            assert "Failed" in captured.out or "Import" in captured.out


# =============================================================================
# 追加：文件探测与产物检查分支
# =============================================================================


@pytest.mark.unit
class TestFindAndStatHelpers:
    def test_find_file_success(self):
        with patch("subprocess.check_output", return_value="/tmp/a.so\n/tmp/b.so\n"):
            assert utils_helpers._find_file("/tmp", "*.so") == "/tmp/a.so"

    def test_find_file_not_found(self):
        with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "find")):
            assert utils_helpers._find_file("/tmp", "*.so") == ""

    def test_find_file_empty_output(self):
        # find 返回空白行时应返回空字符串
        with patch("subprocess.check_output", return_value="\n  \n\n"):
            assert utils_helpers._find_file("/tmp", "*.so") == ""

    def test_get_file_time_success(self):
        with patch("subprocess.check_output", return_value="2024-01-01 00:00:00.123456789\n"):
            assert utils_helpers._get_file_time("/tmp/x") == "2024-01-01 00:00:00"

    def test_get_file_time_failure(self):
        with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "stat")):
            assert utils_helpers._get_file_time("/tmp/x") == ""

    def test_get_file_size_success(self):
        with patch("subprocess.check_output", side_effect=["1024\n", "1.0KiB\n"]):
            assert utils_helpers._get_file_size("/tmp/x") == "1.0KiB"

    def test_get_file_size_failure(self):
        with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "stat")):
            assert utils_helpers._get_file_size("/tmp/x") == ""

    def test_get_file_size_numfmt_failure(self):
        # 第二次 numfmt 调用失败时返回空字符串
        with patch("subprocess.check_output", side_effect=["1024\n", subprocess.CalledProcessError(1, "numfmt")]):
            assert utils_helpers._get_file_size("/tmp/x") == ""


@pytest.mark.unit
class TestArtifacts:
    def test_check_python_artifact_found(self, capsys):
        with patch.object(utils_helpers, "_find_file", return_value="/tmp/libte.so"), \
             patch("os.path.isfile", return_value=True), \
             patch.object(utils_helpers, "_get_file_time", return_value="2024-01-01 00:00:00"), \
             patch.object(utils_helpers, "_get_file_size", return_value="1.0KiB"):
            utils_helpers._check_python_artifact("/tmp")
        out = capsys.readouterr().out
        assert "libte.so" in out
        assert "1.0KiB" in out
        assert "2024-01-01" in out

    def test_check_python_artifact_missing(self, capsys):
        with patch.object(utils_helpers, "_find_file", return_value=""), \
             patch("os.path.isfile", return_value=False):
            utils_helpers._check_python_artifact("/tmp")
        out = capsys.readouterr().out
        assert "Not Found" in out

    def test_check_python_artifact_path_not_file(self, capsys):
        # 找到路径但不是文件时也应视为缺失
        with patch.object(utils_helpers, "_find_file", return_value="/tmp/libte.so"), \
             patch("os.path.isfile", return_value=False):
            utils_helpers._check_python_artifact("/tmp")
        out = capsys.readouterr().out
        assert "Not Found" in out

    def test_check_cpp_artifact_found(self, capsys):
        with patch("os.path.isfile", return_value=True), \
             patch.object(utils_helpers, "_get_file_time", return_value="2024-01-01 00:00:00"), \
             patch.object(utils_helpers, "_get_file_size", return_value="2.0MiB"):
            utils_helpers._check_cpp_artifact("/tmp/te")
        out = capsys.readouterr().out
        assert "test_operator" in out
        assert "2.0MiB" in out

    def test_check_cpp_artifact_missing(self, capsys):
        with patch("os.path.isfile", return_value=False):
            utils_helpers._check_cpp_artifact("/tmp/te")
        out = capsys.readouterr().out
        assert "Not Found" in out

    def test_check_python_import_success(self, capsys):
        result = MagicMock(returncode=0, stdout="/tmp/te/__init__.py\n", stderr="")
        with patch("subprocess.run", return_value=result):
            utils_helpers._check_python_import()
        out = capsys.readouterr().out
        assert "Success" in out
        assert "__init__.py" in out

    def test_check_python_import_uses_sys_executable(self, capsys):
        result = MagicMock(returncode=0, stdout="/tmp/te/__init__.py\n", stderr="")
        with patch("subprocess.run", return_value=result) as run_mock:
            utils_helpers._check_python_import()

        call_args = run_mock.call_args[0][0]
        assert call_args[0] == utils_helpers.sys.executable
        out = capsys.readouterr().out
        assert "Success" in out

    def test_check_python_import_failure(self, capsys):
        result = MagicMock(returncode=1, stdout="", stderr="boom")
        with patch("subprocess.run", return_value=result):
            utils_helpers._check_python_import()
        out = capsys.readouterr().out
        assert "Import Failed" in out

    def test_check_python_import_exception(self, capsys):
        # subprocess.run 本身抛异常的分支
        with patch("subprocess.run", side_effect=OSError("run failed")):
            utils_helpers._check_python_import()
        out = capsys.readouterr().out
        assert "Import Failed" in out

    def test_check_python_import_success_with_stderr(self, capsys):
        # 成功但 stderr 非空时也要提示
        result = MagicMock(returncode=0, stdout="/tmp/te/__init__.py\n", stderr="warning")
        with patch("subprocess.run", return_value=result):
            utils_helpers._check_python_import()
        out = capsys.readouterr().out
        assert "Success" in out
        assert "warning" in out

    def test_check_python_import_fallback_to_system_python_when_in_venv(self, capsys):
        fail_in_venv = MagicMock(returncode=1, stdout="", stderr="venv failed")
        success_in_system = MagicMock(returncode=0, stdout="/system/te/__init__.py\n", stderr="")

        with patch.dict("os.environ", {"VIRTUAL_ENV": "/workspace/.venv"}, clear=False), \
             patch.object(utils_helpers.sys, "executable", "/workspace/.venv/bin/python3"), \
             patch("subprocess.run", side_effect=[fail_in_venv, success_in_system]) as run_mock:
            utils_helpers._check_python_import()

        assert run_mock.call_count == 2
        first_cmd = run_mock.call_args_list[0][0][0]
        second_cmd = run_mock.call_args_list[1][0][0]
        assert first_cmd[0] == "/workspace/.venv/bin/python3"
        assert second_cmd[0] == "/usr/bin/python3"
        out = capsys.readouterr().out
        assert "Success" in out

    def test_no_fallback_when_not_in_venv(self, capsys):
        fail_once = MagicMock(returncode=1, stdout="", stderr="failed")

        with patch.dict("os.environ", {}, clear=False), \
             patch.object(utils_helpers.sys, "executable", "/usr/bin/python3"), \
             patch("subprocess.run", return_value=fail_once) as run_mock:
            utils_helpers._check_python_import()

        assert run_mock.call_count == 1
        first_cmd = run_mock.call_args_list[0][0][0]
        assert first_cmd[0] == "/usr/bin/python3"
        out = capsys.readouterr().out
        assert "Import Failed" in out
