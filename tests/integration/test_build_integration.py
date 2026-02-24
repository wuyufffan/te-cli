#!/usr/bin/env python3
"""
构建功能集成测试
真实执行 CMake 命令
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "te_python"))


# =============================================================================
# CMake 集成测试
# =============================================================================

@pytest.mark.integration
@pytest.mark.build
@pytest.mark.slow
class TestCMakeIntegration:
    """测试真实的 CMake 构建流程"""
    
    def test_cmake_available(self):
        """测试系统中是否安装了 CMake"""
        result = subprocess.run(
            ["cmake", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "CMake 必须安装才能运行集成测试"
        assert "cmake version" in result.stdout.lower()
    
    def test_ninja_available(self):
        """测试系统中是否安装了 Ninja"""
        result = subprocess.run(
            ["ninja", "--version"],
            capture_output=True,
            text=True
        )
        # Ninja 可能未安装，跳过而不是失败
        if result.returncode != 0:
            pytest.skip("Ninja 未安装，跳过相关测试")
    
    def test_minimal_cmake_project_build(self, minimal_cmake_project):
        """测试最小 CMake 项目的完整构建流程"""
        project_dir = minimal_cmake_project
        build_dir = project_dir / "build"
        
        # 配置
        result = subprocess.run(
            ["cmake", "-B", str(build_dir), "-S", str(project_dir)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"CMake 配置失败: {result.stderr}"
        
        # 构建
        result = subprocess.run(
            ["cmake", "--build", str(build_dir)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"CMake 构建失败: {result.stderr}"
        
        # 验证可执行文件存在
        executable = build_dir / "test_app"
        assert executable.exists(), "构建产物不存在"
        
        # 运行可执行文件
        result = subprocess.run(
            [str(executable)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Hello from CMake" in result.stdout
    
    def test_minimal_cmake_with_ninja(self, minimal_cmake_project):
        """测试使用 Ninja 构建"""
        # 检查 Ninja 是否可用
        ninja_check = subprocess.run(["ninja", "--version"], capture_output=True)
        if ninja_check.returncode != 0:
            pytest.skip("Ninja 未安装")
        
        project_dir = minimal_cmake_project
        build_dir = project_dir / "build_ninja"
        
        # 配置（使用 Ninja）
        result = subprocess.run(
            ["cmake", "-GNinja", "-B", str(build_dir), "-S", str(project_dir)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"CMake 配置失败: {result.stderr}"
        
        # 构建
        result = subprocess.run(
            ["cmake", "--build", str(build_dir)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"CMake 构建失败: {result.stderr}"
        
        # 验证可执行文件存在
        executable = build_dir / "test_app"
        assert executable.exists(), "构建产物不存在"


# =============================================================================
# 构建脚本生成测试
# =============================================================================

@pytest.fixture(autouse=True)
def init_config_fixture():
    """自动初始化配置"""
    from config_manager import init_config
    init_config()


@pytest.mark.integration
@pytest.mark.build
class TestBuildScriptGeneration:
    """测试构建脚本的生成和执行"""
    
    def test_python_build_script_syntax(self, tmp_path):
        """测试 Python 构建脚本语法正确"""
        import build_helpers
        
        script = build_helpers._python_build_script("/tmp/init.sh", clean=False)
        
        # 将脚本写入临时文件并检查语法
        script_file = tmp_path / "build_script.sh"
        script_file.write_text(script)
        
        # 使用 bash -n 检查语法
        result = subprocess.run(
            ["bash", "-n", str(script_file)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"脚本语法错误: {result.stderr}"
    
    def test_cpp_build_script_syntax(self, tmp_path):
        """测试 C++ 构建脚本语法正确"""
        import build_helpers
        
        script = build_helpers._cpp_build_script("/tmp/init.sh")
        
        # 将脚本写入临时文件并检查语法
        script_file = tmp_path / "build_script.sh"
        script_file.write_text(script)
        
        # 使用 bash -n 检查语法
        result = subprocess.run(
            ["bash", "-n", str(script_file)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"脚本语法错误: {result.stderr}"
    
    def test_script_contains_all_exports(self):
        """测试脚本包含所有必要的环境变量导出"""
        import build_helpers
        
        script = build_helpers._python_build_script("/tmp/init.sh", clean=False)
        
        required_vars = [
            "NVTE_FRAMEWORK=pytorch",
            "NVTE_USE_ROCM=1",
            "NVTE_USE_HIPBLASLT=1",
            "NVTE_USE_ROCBLAS=1",
            "CXX=hipcc",
        ]
        
        for var in required_vars:
            assert var in script, f"脚本缺少必要的环境变量: {var}"


# =============================================================================
# 文件系统操作测试
# =============================================================================

@pytest.mark.integration
@pytest.mark.build
class TestFilesystemOperations:
    """测试真实的文件系统操作"""
    
    def test_clean_cpp_build_directory(self, tmp_path):
        """测试清理 C++ 构建目录"""
        import build_helpers
        from unittest.mock import patch
        from config_manager import Config
        
        # 创建模拟的构建目录结构
        cpp_dir = tmp_path / "TransformerEngine" / "tests" / "cpp"
        build_dir = cpp_dir / "build"
        build_dir.mkdir(parents=True)
        (build_dir / "test_file.o").write_text("dummy")
        
        # 创建自定义配置
        config = Config()
        config.te_path = str(tmp_path / "TransformerEngine")
        
        with patch("build_helpers.get_config", lambda: config):
            result = build_helpers.build_clean_cpp()
            assert result == 0
            assert not build_dir.exists(), "构建目录应该被删除"
    
    def test_log_file_creation(self, tmp_path):
        """测试日志文件创建"""
        log_file = tmp_path / "test_build.log"
        
        # 模拟后台任务写入日志
        script = """
echo "Build started"
echo "Build step 1"
echo "Build completed"
"""
        with open(log_file, "w") as f:
            subprocess.Popen(
                ["bash", "-c", script],
                stdout=f,
                stderr=subprocess.STDOUT
            )
        
        # 等待进程完成
        import time
        time.sleep(0.5)
        
        # 验证日志文件内容
        assert log_file.exists()
        content = log_file.read_text()
        assert "Build started" in content
        assert "Build completed" in content
