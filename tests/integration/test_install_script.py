#!/usr/bin/env python3
"""
集成测试：测试 install.sh 脚本
使用 subprocess 进行端到端测试
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# 标记这些测试为慢速测试
pytestmark = pytest.mark.slow

# 项目根目录
REPO_DIR = Path(__file__).parent.parent.parent
INSTALL_SH = REPO_DIR / "install.sh"


class TestInstallProcess:
    """测试安装流程"""

    def test_install_creates_te_script(self, tmp_path, monkeypatch):
        """测试安装创建 te 脚本"""
        home = tmp_path / "home"
        home.mkdir()
        
        env = os.environ.copy()
        env["HOME"] = str(home)
        
        result = subprocess.run(
            ["bash", str(INSTALL_SH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
            env=env,
        )
        
        # 安装应该成功
        assert result.returncode == 0, f"Install failed: {result.stderr}"
        
        # 验证 te 脚本存在
        te_script = home / ".local" / "bin" / "te"
        assert te_script.exists(), "te script not created"
        assert os.access(te_script, os.X_OK), "te script not executable"

    def test_install_copies_python_code(self, tmp_path, monkeypatch):
        """测试安装复制 Python 代码"""
        home = tmp_path / "home"
        home.mkdir()
        
        env = os.environ.copy()
        env["HOME"] = str(home)
        
        result = subprocess.run(
            ["bash", str(INSTALL_SH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
            env=env,
        )
        
        assert result.returncode == 0
        
        # 验证 Python 代码存在于正确的目录下 (te-cli)
        te_cli_dir = home / ".local" / "share" / "te-cli"
        assert te_cli_dir.exists(), "te-cli directory not created"
        assert (te_cli_dir / "core" / "cli.py").exists(), "cli.py not copied"
        assert (te_cli_dir / "core" / "install_config.py").exists(), "install_config.py not copied"


class TestTeFirstRun:
    """测试 te 首次运行配置"""

    def test_te_first_run_creates_config(self, tmp_path):
        """测试 te 首次运行创建配置"""
        home = tmp_path / "home"
        home.mkdir()
        
        env = os.environ.copy()
        env["HOME"] = str(home)
        
        # 先安装
        install_result = subprocess.run(
            ["bash", str(INSTALL_SH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
            env=env,
        )
        assert install_result.returncode == 0, "Installation failed"
        
        # 运行 te --version（首次运行）
        te_script = home / ".local" / "bin" / "te"
        
        # 此处 mock DEFAULT_TE_PATH 或者提供一个不存在的路径，确保它会 prompt
        result = subprocess.run(
            ["bash", str(te_script), "--version"],
            capture_output=True,
            text=True,
            env=env,
            input="/test/TransformerEngine\n",  # 提供 TE_PATH
        )
        
        # 检查配置是否创建
        config_file = home / ".te_config.json"
        assert config_file.exists(), "Config file not created"
        
        # 返回结果应该是由环境决定的默认路径，或接收了输入
        config = json.loads(config_file.read_text())
        assert "te_path" in config
        assert isinstance(config["te_path"], str)

    def test_te_second_run_uses_existing_config(self, tmp_path):
        """测试 te 第二次运行使用已有配置"""
        home = tmp_path / "home"
        home.mkdir()
        
        env = os.environ.copy()
        env["HOME"] = str(home)
        
        # 安装
        subprocess.run(
            ["bash", str(INSTALL_SH)],
            capture_output=True,
            cwd=str(REPO_DIR),
            env=env,
        )
        
        # 预先创建配置文件
        config_file = home / ".te_config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text('{"te_path": "/test/path"}')
        
        # 运行 te --version（第二次）
        te_script = home / ".local" / "bin" / "te"
        result = subprocess.run(
            ["bash", str(te_script), "--version"],
            capture_output=True,
            text=True,
            env=env,
        )
        
        # 应该直接成功，不提示输入
        assert result.returncode == 0
        assert "First Time Setup" not in result.stdout


class TestPathCheck:
    """测试 PATH 检查"""

    def test_install_warns_when_path_not_in_env(self, tmp_path):
        """测试 PATH 不在环境变量中时显示警告"""
        home = tmp_path / "home"
        home.mkdir()
        
        # 使用空的 PATH
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["PATH"] = "/usr/bin:/bin"  # 不包含 ~/.local/bin
        
        result = subprocess.run(
            ["bash", str(INSTALL_SH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
            env=env,
        )
        
        assert result.returncode == 0
        # 应该显示警告
        assert "PATH" in result.stdout
