#!/usr/bin/env python3
"""
utils_helpers 模块单元测试
"""
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "te_python"))
import utils_helpers
from config import LOG_FILE_PY, LOG_FILE_CPP, LOG_FILE_L0_CPP


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
    
    def test_view_log_success(self):
        """成功查看日志"""
        with patch("os.path.isfile") as mock, \
             patch("subprocess.call") as call:
            mock.return_value = True
            call.return_value = 0
            
            assert utils_helpers.view_log("build_py") == 0
            call_args = call.call_args[0][0]
            assert call_args[0] == "tail"
    
    def test_view_log_keyboard_interrupt(self):
        """用户中断日志查看"""
        with patch("os.path.isfile") as mock, \
             patch("subprocess.call") as call:
            mock.return_value = True
            call.side_effect = KeyboardInterrupt()
            assert utils_helpers.view_log("build_py") == 0
    
    @pytest.mark.parametrize("log_type", ["build_py", "build_cpp", "rebuild", "build_all", "l0cpp", "l0torch", "l1torch"])
    def test_all_log_types(self, log_type):
        """测试所有日志类型映射"""
        with patch("os.path.isfile") as mock, \
             patch("subprocess.call") as call:
            mock.return_value = True
            call.return_value = 0
            assert utils_helpers.view_log(log_type) == 0


@pytest.mark.unit
class TestCheckTe:
    """测试 check_te 函数"""
    
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
