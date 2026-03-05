#!/usr/bin/env python3
"""
build_helpers 模块单元测试
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import core.build_helpers as build_helpers


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

    def test_cpp_incremental_script_does_not_delete_cmake_cache(self):
        """增量 C++ 构建脚本不应删除 CMakeCache.txt"""
        script = build_helpers._cpp_build_script("/init.sh")
        assert "rm -f build/CMakeCache.txt" not in script
        assert "rm -rf" not in script

    def test_rebuild_script_phase1_contains_pythonpath(self):
        """Rebuild Phase 1 应包含 hipify_torch PYTHONPATH"""
        script = build_helpers._rebuild_script("/init.sh", "/fake/te", "")
        assert "PYTHONPATH" in script
        assert "3rdparty/hipify_torch" in script

    def test_rebuild_script_phase1_contains_pip_install(self):
        """Rebuild Phase 1 应包含 pip 增量构建命令"""
        script = build_helpers._rebuild_script("/init.sh", "/fake/te", "")
        assert "python3 -m pip install" in script
        assert "--no-build-isolation" in script

    def test_rebuild_script_phase2_contains_cmake_params(self):
        """Rebuild Phase 2 应包含 HIP/HSA/COMPILER_AR 参数"""
        script = build_helpers._rebuild_script("/init.sh", "/fake/te", "")
        assert "-DHIP_CLANG_INCLUDE_PATH=\"$HIP_CLANG_INCLUDE_PATH\"" in script
        assert "-DHSA_HEADER=\"$HSA_HEADER\"" in script
        assert "$EXTRA_AR" in script

    def test_rebuild_script_contains_required_env_vars(self):
        """Rebuild 脚本应继承公共环境变量"""
        script = build_helpers._rebuild_script("/init.sh", "/fake/te", "")
        assert "NVTE_FRAMEWORK=pytorch" in script
        assert "NVTE_USE_ROCM=1" in script
        assert "CXX=hipcc" in script


@pytest.mark.unit
@pytest.mark.build
class TestScriptConsistency:
    """测试组合脚本与子脚本的一致性"""

    def test_rebuild_phase1_consistent_with_python_build(self):
        """Rebuild Phase 1 与 Python 构建关键参数保持一致"""
        py_script = build_helpers._python_build_script("/init.sh", clean=False)
        rebuild_script = build_helpers._rebuild_script("/init.sh", "/fake/te", "")

        assert "3rdparty/hipify_torch" in py_script
        assert "3rdparty/hipify_torch" in rebuild_script
        assert "-vv --no-build-isolation" in py_script
        assert "-vv --no-build-isolation" in rebuild_script

    def test_rebuild_phase2_consistent_with_cpp_build(self):
        """Rebuild Phase 2 与 C++ 构建关键参数保持一致"""
        cpp_script = build_helpers._cpp_build_script("/init.sh")
        rebuild_script = build_helpers._rebuild_script("/init.sh", "/fake/te", "")

        for key in [
            "-DHIP_CLANG_INCLUDE_PATH=\"$HIP_CLANG_INCLUDE_PATH\"",
            "-DHSA_HEADER=\"$HSA_HEADER\"",
            "$EXTRA_AR",
        ]:
            assert key in cpp_script
            assert key in rebuild_script

    def test_full_build_phase2_consistent_with_cpp_build(self):
        """Full Build Phase 2 与 C++ 构建关键参数保持一致"""
        cpp_script = build_helpers._cpp_build_script("/init.sh")
        full_script = build_helpers._full_build_script("/init.sh", "/fake/te")

        for key in [
            "-DHIP_CLANG_INCLUDE_PATH=\"$HIP_CLANG_INCLUDE_PATH\"",
            "-DHSA_HEADER=\"$HSA_HEADER\"",
            "$EXTRA_AR",
        ]:
            assert key in cpp_script
            assert key in full_script


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
        with patch("core.build_helpers.check_task_running") as check, \
             patch("core.build_helpers.confirm_if_log_exists") as confirm, \
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
        from core.config_manager import Config
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
        from core.config_manager import Config
        config = Config()
        config.te_init_script = ""
        monkeypatch.setattr(build_helpers, "get_config", lambda: config)
        result = build_helpers._resolve_init_script()
        assert "core/te_init.sh" in result
    
    def test_resolve_init_script_from_env(self, monkeypatch):
        """从环境变量解析初始化脚本"""
        from core.config_manager import Config
        config = Config()
        config.te_init_script = "/custom/path/te_init.sh"
        monkeypatch.setattr(build_helpers, "get_config", lambda: config)
        assert build_helpers._resolve_init_script() == "/custom/path/te_init.sh"
