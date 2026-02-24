#!/usr/bin/env python3
"""
test_helpers 模块单元测试
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "te_python"))
import test_helpers


@pytest.fixture
def common_test_mocks():
    """提供通用 mock 设置"""
    with patch("test_helpers.check_task_running") as check, \
         patch("test_helpers.confirm_if_log_exists") as confirm, \
         patch("os.path.isdir") as isdir, \
         patch("subprocess.Popen") as popen:
        
        check.return_value = 0
        confirm.return_value = 0
        isdir.return_value = True
        instance = MagicMock()
        instance.pid = 12345
        popen.return_value = instance
        
        yield {
            "check": check,
            "confirm": confirm,
            "isdir": isdir,
            "popen": popen,
        }


@pytest.mark.unit
class TestTestOperations:
    """测试操作"""
    
    def test_task_already_running(self):
        """任务已在运行时阻止"""
        with patch("test_helpers.check_task_running") as check:
            check.return_value = 1
            assert test_helpers.run_l0cpp() == 1
    
    def test_log_exists_confirm_no(self):
        """用户拒绝覆盖日志"""
        with patch("test_helpers.check_task_running") as check, \
             patch("test_helpers.confirm_if_log_exists") as confirm:
            check.return_value = 0
            confirm.return_value = 1
            assert test_helpers.run_l0cpp() == 1
    
    def test_parent_dir_not_exist(self):
        """父目录不存在"""
        with patch("test_helpers.check_task_running") as check, \
             patch("test_helpers.confirm_if_log_exists") as confirm, \
             patch("os.path.isdir") as isdir:
            check.return_value = 0
            confirm.return_value = 0
            isdir.return_value = False
            assert test_helpers.run_l0cpp() == 2
    
    @pytest.mark.parametrize("func,expected_script", [
        (test_helpers.run_l0cpp, "L0_cppunittest"),
        (test_helpers.run_l0torch, "L0_pytorch_unittest"),
        (test_helpers.run_l1torch, "L1_pytorch_distributed_unittest"),
    ])
    def test_test_functions(self, common_test_mocks, func, expected_script):
        """测试各种测试启动函数"""
        assert func() == 0
        
        # 验证脚本内容
        call_args = common_test_mocks["popen"].call_args
        if call_args[0]:
            script = call_args[0][0][3]
        else:
            script = call_args[1].get('args', ['', '', '', ''])[3]
        assert expected_script in script
