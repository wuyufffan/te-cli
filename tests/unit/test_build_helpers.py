#!/usr/bin/env python3
"""
build_helpers 模块单元测试
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "te_python"))
import build_helpers


# =============================================================================
# 脚本生成测试
# =============================================================================

@pytest.mark.unit
@pytest.mark.build
class TestScriptGeneration:
    """测试构建脚本生成"""
    
    def test_python_build_script_contains_required_vars(self):
        """Python 脚本包含必要环境变量"""
        script = build_helpers._python_build_script("/init.sh", clean=False)
        assert "NVTE_FRAMEWORK=pytorch" in script
        assert "NVTE_USE_ROCM=1" in script
        assert "CXX=hipcc" in script
        assert 'source "$INIT_SCRIPT"' in script
    
    def test_python_build_script_clean_mode(self):
        """Python 清理构建脚本"""
        script = build_helpers._python_build_script("/init.sh", clean=True)
        assert "rm -rf" in script
    
    def test_cpp_build_script_contains_cmake(self):
        """C++ 脚本包含 CMake 命令"""
        script = build_helpers._cpp_build_script("/init.sh")
        assert "cmake -GNinja -Bbuild" in script
        assert "cmake --build build" in script


# =============================================================================
# 构建启动测试 - 使用公共参数化
# =============================================================================

@pytest.mark.unit
@pytest.mark.build
class TestBuildOperations:
    """测试构建操作"""
    
    @pytest.fixture
    def common_mocks(self):
        """提供通用 mock 设置"""
        with patch("build_helpers.check_task_running") as check, \
             patch("build_helpers.confirm_if_log_exists") as confirm, \
             patch("subprocess.Popen") as popen, \
             patch("shutil.rmtree") as rmtree:
            
            check.return_value = 0
            confirm.return_value = 0
            instance = MagicMock()
            instance.pid = 12345
            popen.return_value = instance
            
            yield {
                "check": check,
                "confirm": confirm,
                "popen": popen,
                "rmtree": rmtree,
            }
    
    @pytest.mark.parametrize("func_name,expected_call", [
        ("build_te_func_incremental", "popen"),
        ("build_te_func", "popen"),
        ("build_cpp_test_func", "popen"),
        ("build_all_func", "popen"),
        ("rebuild_dev", "popen"),
    ])
    def test_build_functions_success(self, common_mocks, func_name, expected_call):
        """测试各种构建函数成功启动"""
        func = getattr(build_helpers, func_name)
        assert func() == 0
        common_mocks[expected_call].assert_called_once()
    
    def test_build_task_running_blocks(self, common_mocks):
        """任务运行中时阻止新任务"""
        common_mocks["check"].return_value = 1
        assert build_helpers.build_te_func_incremental() == 1
        common_mocks["popen"].assert_not_called()
    
    def test_build_log_confirm_no(self, common_mocks):
        """用户拒绝覆盖日志时取消"""
        common_mocks["confirm"].return_value = 1
        assert build_helpers.build_te_func_incremental() == 1
        common_mocks["popen"].assert_not_called()
    
    def test_clean_cpp_build_directory(self):
        """测试清理 C++ 构建目录"""
        with patch("os.path.isdir") as isdir, \
             patch("shutil.rmtree") as rmtree:
            isdir.return_value = True
            assert build_helpers.build_clean_cpp() == 0
            rmtree.assert_called_once()
    
    def test_clean_cpp_nonexistent_directory(self):
        """清理不存在的目录"""
        with patch("os.path.isdir") as isdir:
            isdir.return_value = False
            assert build_helpers.build_clean_cpp() == 0
    
    def test_rebuild_without_te_path(self, monkeypatch):
        """TE_PATH 未设置时返回错误"""
        from config_manager import Config
        config = Config()
        config.te_path = ""
        monkeypatch.setattr(build_helpers, "get_config", lambda: config)
        assert build_helpers.rebuild_dev() == 1


# =============================================================================
# 脚本启动测试
# =============================================================================

@pytest.mark.unit
@pytest.mark.build
class TestScriptExecution:
    """测试脚本执行"""
    
    def test_start_background_script_success(self, capsys):
        """成功启动后台脚本"""
        with patch("subprocess.Popen") as popen:
            instance = MagicMock()
            instance.pid = 12345
            popen.return_value = instance
            
            result = build_helpers._start_background_script(
                "/tmp/test.log", "echo test", "Test Started"
            )
            assert result == 0
            captured = capsys.readouterr()
            assert "Test Started" in captured.out
    
    def test_resolve_init_script_from_module(self, monkeypatch):
        """从模块路径解析初始化脚本"""
        from config_manager import Config
        config = Config()
        config.te_init_script = ""
        monkeypatch.setattr(build_helpers, "get_config", lambda: config)
        result = build_helpers._resolve_init_script()
        assert "core/te_init.sh" in result
    
    def test_resolve_init_script_from_env(self, monkeypatch):
        """从环境变量解析初始化脚本"""
        from config_manager import Config
        config = Config()
        config.te_init_script = "/custom/path/te_init.sh"
        monkeypatch.setattr(build_helpers, "get_config", lambda: config)
        assert build_helpers._resolve_init_script() == "/custom/path/te_init.sh"
