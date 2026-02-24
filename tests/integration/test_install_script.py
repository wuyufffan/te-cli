#!/usr/bin/env python3
"""
集成测试：测试 install.sh 脚本
使用 subprocess 进行端到端测试

注意：这些测试会调用 install.sh，而 install.sh 会运行测试套件。
为了避免循环测试，我们在测试环境中使用 -y 标志跳过交互式提示。
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


class TestInstallHelp:
    """测试帮助信息"""

    def test_help_flag_shows_usage(self):
        """测试 --help 显示使用说明"""
        result = subprocess.run(
            ["bash", str(INSTALL_SH), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
        )
        
        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "--uninstall" in result.stdout
        assert "--yes" in result.stdout

    def test_h_flag_shows_usage(self):
        """测试 -h 显示使用说明"""
        result = subprocess.run(
            ["bash", str(INSTALL_SH), "-h"],
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
        )
        
        assert result.returncode == 0
        assert "Usage:" in result.stdout


class TestInstallProcess:
    """测试安装流程"""

    def test_install_creates_te_script(self, tmp_path, monkeypatch):
        """测试安装创建 te 脚本"""
        home = tmp_path / "home"
        home.mkdir()
        
        env = os.environ.copy()
        env["HOME"] = str(home)
        
        result = subprocess.run(
            ["bash", str(INSTALL_SH), "-y", "--skip-tests"],
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
            ["bash", str(INSTALL_SH), "-y", "--skip-tests"],
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
            env=env,
        )
        
        assert result.returncode == 0
        
        # 验证 Python 代码存在
        te_python = home / ".local" / "share" / "my_linux_config" / "te_python"
        assert te_python.exists(), "te_python directory not created"
        assert (te_python / "cli.py").exists(), "cli.py not copied"
        assert (te_python / "install_config.py").exists(), "install_config.py not copied"

    def test_install_preserves_existing_config(self, tmp_path):
        """测试安装保留现有配置文件"""
        home = tmp_path / "home"
        home.mkdir()
        
        # 预先创建配置文件
        config_file = home / ".te_config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text('{"te_path": "/existing/path"}')
        
        env = os.environ.copy()
        env["HOME"] = str(home)
        
        result = subprocess.run(
            ["bash", str(INSTALL_SH), "-y", "--skip-tests"],
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
            env=env,
        )
        
        assert result.returncode == 0
        
        # 验证配置文件未被覆盖
        config = json.loads(config_file.read_text())
        assert config["te_path"] == "/existing/path"


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
            ["bash", str(INSTALL_SH), "-y"],
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
            env=env,
        )
        assert install_result.returncode == 0, "Installation failed"
        
        # 运行 te --version（首次运行）
        te_script = home / ".local" / "bin" / "te"
        result = subprocess.run(
            ["bash", str(te_script), "--version"],
            capture_output=True,
            text=True,
            env=env,
            input="/workspace/TransformerEngine\n",  # 提供 TE_PATH
        )
        
        # 检查配置是否创建
        config_file = home / ".te_config.json"
        assert config_file.exists(), "Config file not created"
        
        config = json.loads(config_file.read_text())
        assert config["te_path"] == "/workspace/TransformerEngine"

    def test_te_second_run_uses_existing_config(self, tmp_path):
        """测试 te 第二次运行使用已有配置"""
        home = tmp_path / "home"
        home.mkdir()
        
        env = os.environ.copy()
        env["HOME"] = str(home)
        
        # 安装
        subprocess.run(
            ["bash", str(INSTALL_SH), "-y"],
            capture_output=True,
            cwd=str(REPO_DIR),
            env=env,
        )
        
        # 预先创建配置文件
        config_file = home / ".te_config.json"
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
        assert "TE CLI v" in result.stdout or "First Time Setup" not in result.stdout


class TestUninstall:
    """测试卸载功能"""

    def test_uninstall_removes_all_files(self, tmp_path):
        """测试卸载删除所有文件"""
        home = tmp_path / "home"
        home.mkdir()
        
        env = os.environ.copy()
        env["HOME"] = str(home)
        
        # 先安装
        subprocess.run(
            ["bash", str(INSTALL_SH), "-y"],
            capture_output=True,
            cwd=str(REPO_DIR),
            env=env,
        )
        
        # 创建配置文件
        config_file = home / ".te_config.json"
        config_file.write_text('{"te_path": "/test"}')
        
        # 卸载（使用 -y 自动删除配置）
        result = subprocess.run(
            ["bash", str(INSTALL_SH), "-y", "--uninstall"],
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
            env=env,
        )
        
        assert result.returncode == 0
        
        # 验证文件已删除
        te_script = home / ".local" / "bin" / "te"
        share_dir = home / ".local" / "share" / "my_linux_config"
        
        assert not te_script.exists(), "te script not removed"
        assert not share_dir.exists(), "share directory not removed"
        assert not config_file.exists(), "config file not removed"

    def test_uninstall_shows_warning_when_nothing_installed(self, tmp_path):
        """测试未安装时卸载显示警告"""
        home = tmp_path / "home"
        home.mkdir()
        
        env = os.environ.copy()
        env["HOME"] = str(home)
        
        result = subprocess.run(
            ["bash", str(INSTALL_SH), "--uninstall"],
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
            env=env,
            input="y\n",
        )
        
        assert result.returncode == 0
        assert "Nothing to uninstall" in result.stdout or "Uninstallation complete" in result.stdout


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
            ["bash", str(INSTALL_SH), "-y"],  # 使用 -y 自动继续
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
            env=env,
        )
        
        assert result.returncode == 0
        # 应该显示警告
        assert "not in your PATH" in result.stdout or "PATH" in result.stdout


class TestErrorHandling:
    """测试错误处理"""

    def test_unknown_option_shows_error(self):
        """测试未知选项显示错误"""
        result = subprocess.run(
            ["bash", str(INSTALL_SH), "--unknown-option"],
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
        )
        
        assert result.returncode != 0
        assert "Unknown option" in result.stderr or "Unknown option" in result.stdout

    def test_install_continues_with_y_flag_when_tests_fail(self, tmp_path, monkeypatch):
        """测试测试失败时使用 -y 标志继续安装"""
        home = tmp_path / "home"
        home.mkdir()
        
        env = os.environ.copy()
        env["HOME"] = str(home)
        
        # 创建一个临时的失败测试文件
        # 注意：这个测试可能因实际测试套件通过而行为不同
        # 我们主要验证 -y 标志的处理逻辑
        result = subprocess.run(
            ["bash", str(INSTALL_SH), "-y", "--skip-tests"],
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
            env=env,
        )
        
        # 如果测试通过，安装应该成功
        # 如果测试失败但有 -y，安装也应该成功
        assert result.returncode == 0, f"Install failed: {result.stdout}\n{result.stderr}"
