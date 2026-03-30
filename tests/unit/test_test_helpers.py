#!/usr/bin/env python3
"""
test_helpers 模块单元测试
"""
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest

import core.test_helpers as test_helpers
from core.config_manager import Config


@pytest.fixture
def common_test_mocks(tmp_path):
    """提供通用 mock 设置"""
    te_root = tmp_path / "TransformerEngine"
    te_root.mkdir()
    cfg = Config(te_path=str(te_root), work_space=str(tmp_path))
    with patch("core.test_helpers.check_task_running") as check, \
         patch("core.test_helpers.confirm_if_log_exists") as confirm, \
         patch("core.test_helpers.get_config", return_value=cfg) as get_config, \
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
            "get_config": get_config,
            "isdir": isdir,
            "popen": popen,
            "config": cfg,
        }


@pytest.mark.unit
class TestTestOperations:
    """测试操作"""

    def test_conda_activation_prefers_repo_venv(self, tmp_path):
        te_root = tmp_path / "TransformerEngine"
        te_root.mkdir()
        cfg = Config(te_path=str(te_root), work_space=str(tmp_path))

        with patch("core.test_helpers.get_config", return_value=cfg):
            script = test_helpers._conda_activation()

        assert f"source '{te_root}/.venv/bin/activate'" in script
        assert "for env_name in te210 te27; do" in script
    
    def test_task_already_running(self):
        """任务已在运行时阻止"""
        with patch("core.test_helpers.check_task_running") as check:
            check.return_value = 1
            assert test_helpers.run_l0cpp() == 1
    
    def test_log_exists_confirm_no(self):
        """用户拒绝覆盖日志"""
        with patch("core.test_helpers.check_task_running") as check, \
             patch("core.test_helpers.confirm_if_log_exists") as confirm:
            check.return_value = 0
            confirm.return_value = 1
            assert test_helpers.run_l0cpp() == 1
    
    def test_parent_dir_not_exist(self):
        """父目录不存在"""
        with patch("core.test_helpers.check_task_running") as check, \
             patch("core.test_helpers.confirm_if_log_exists") as confirm, \
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
        assert f"source '{common_test_mocks['config'].te_path}/.venv/bin/activate'" in script

    @pytest.mark.parametrize("func,log_type", [
        (test_helpers.run_l0cpp, "l0cpp"),
        (test_helpers.run_l0torch, "l0torch"),
        (test_helpers.run_l1torch, "l1torch"),
    ])
    def test_test_functions_create_timestamped_logs(self, common_test_mocks, func, log_type):
        assert func() == 0
        expected_root = Path(common_test_mocks["config"].work_space) / "logs"
        created_logs = list(expected_root.rglob("*.log"))
        assert len(created_logs) == 1
        assert created_logs[0].parent.name == log_type
