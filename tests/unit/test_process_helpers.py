#!/usr/bin/env python3
"""
process_helpers 模块单元测试
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "te_python"))
import process_helpers


# =============================================================================
# 进程显示测试
# =============================================================================

@pytest.mark.unit
@pytest.mark.process
class TestShowProcesses:
    """测试 show_processes 函数"""
    
    def test_no_running_tasks(self, capsys):
        """没有运行中的任务"""
        with patch("process_helpers.pgrep") as pgrep:
            pgrep.return_value = []
            assert process_helpers.show_processes() == 0
            captured = capsys.readouterr()
            assert "Running TE Tasks" in captured.out
    
    def test_build_task_running(self, capsys):
        """有构建任务在运行"""
        with patch("process_helpers.pgrep") as pgrep, \
             patch("os.path.exists") as exists:
            pgrep.side_effect = lambda p: ["1234", "5678"] if "pip" in p or "cmake" in p else []
            exists.return_value = True
            
            with patch("os.stat") as stat:
                stat.return_value = MagicMock(st_mtime=1234567890)
                assert process_helpers.show_processes() == 0
                captured = capsys.readouterr()
                assert "Build Task" in captured.out or "PIDs:" in captured.out


# =============================================================================
# 日志确认测试
# =============================================================================

@pytest.mark.unit
@pytest.mark.process
class TestConfirmLog:
    """测试 confirm_if_log_exists 函数"""
    
    def test_log_not_exists(self):
        """日志不存在时直接通过"""
        with patch("os.path.exists") as exists:
            exists.return_value = False
            assert process_helpers.confirm_if_log_exists("/path/to/log") == 0
    
    def test_log_empty(self):
        """日志为空时直接通过"""
        with patch("os.path.exists") as exists, \
             patch("os.path.getsize") as getsize:
            exists.return_value = True
            getsize.return_value = 0
            assert process_helpers.confirm_if_log_exists("/path/to/log") == 0
    
    @pytest.mark.parametrize("user_input,expected", [
        ("y", 0),
        ("Y", 0),
        ("n", 1),
        ("N", 1),
        ("", 1),
    ])
    def test_log_exists_user_response(self, user_input, expected):
        """测试用户对日志覆盖的响应"""
        with patch("os.path.exists") as exists, \
             patch("os.path.getsize") as getsize, \
             patch("builtins.input") as mock_input, \
             patch("common_utils.get_human_size") as size:
            exists.return_value = True
            getsize.return_value = 1024
            mock_input.return_value = user_input
            size.return_value = "1.0K"
            
            assert process_helpers.confirm_if_log_exists("/path/to/log") == expected


# =============================================================================
# 任务检查和终止测试
# =============================================================================

@pytest.mark.unit
@pytest.mark.process
class TestTaskManagement:
    """测试任务管理功能"""
    
    def test_check_task_not_running(self):
        """没有任务在运行"""
        with patch("process_helpers.pgrep") as pgrep:
            pgrep.return_value = []
            assert process_helpers.check_task_running("pattern", "Test") == 0
    
    def test_check_task_running(self, capsys):
        """有任务在运行"""
        with patch("process_helpers.pgrep") as pgrep:
            pgrep.return_value = ["1234"]
            assert process_helpers.check_task_running("pattern", "Test") == 1
            captured = capsys.readouterr()
            assert "Task Already Running" in captured.out
    
    @pytest.mark.parametrize("confirm,expected", [
        ("y", 0),
        ("n", 1),
    ])
    def test_kill_task_confirmation(self, confirm, expected):
        """测试终止任务确认"""
        with patch("builtins.input") as mock_input, \
             patch("process_helpers.pkill") as pkill, \
             patch("time.sleep"), \
             patch("process_helpers.get_process_start_time") as start, \
             patch("process_helpers.get_process_elapsed") as elapsed:
            mock_input.return_value = confirm
            pkill.return_value = 0
            start.return_value = "Mon Jan 1 00:00:00 2024"
            elapsed.return_value = "00:05:00"
            
            result = process_helpers._kill_task_logic(["1234"], "pattern", "Test")
            
            if confirm == "y":
                pkill.assert_called_once()
            assert result == expected
    
    def test_kill_build_task_no_running(self, capsys):
        """没有构建任务时"""
        with patch("process_helpers.pgrep") as pgrep:
            pgrep.return_value = []
            assert process_helpers.kill_build_task() == 0
            captured = capsys.readouterr()
            assert "No build task" in captured.out
    
    def test_kill_test_task_no_running(self, capsys):
        """没有测试任务时"""
        with patch("process_helpers.pgrep") as pgrep:
            pgrep.return_value = []
            assert process_helpers.kill_test_task("pattern", "Test") == 0
