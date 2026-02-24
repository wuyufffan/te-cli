#!/usr/bin/env python3
"""
测试 install_config.py 模块
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 确保可以导入 te_python 模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "te_python"))

from install_config import (
    check_installation,
    config_exists,
    get_config_path,
    get_install_paths,
    is_path_in_env,
    load_config,
    save_config,
    setup_config_if_needed,
    validate_te_path,
)


def set_home(monkeypatch, tmp_path):
    """辅助函数：设置 HOME 环境变量"""
    monkeypatch.setenv("HOME", str(tmp_path))


class TestGetConfigPath:
    """测试 get_config_path 函数"""

    def test_returns_path_in_home(self, tmp_path, monkeypatch):
        """测试返回用户主目录下的配置文件路径"""
        # 通过修改 HOME 环境变量来测试
        monkeypatch.setenv("HOME", str(tmp_path))
        path = get_config_path()
        assert path == tmp_path / ".te_config.json"


class TestConfigExists:
    """测试 config_exists 函数"""

    def test_returns_false_when_file_not_exists(self, tmp_path, monkeypatch):
        """测试文件不存在时返回 False"""
        set_home(monkeypatch, tmp_path)
        assert config_exists() is False

    def test_returns_true_when_file_exists(self, tmp_path, monkeypatch):
        """测试文件存在时返回 True"""
        set_home(monkeypatch, tmp_path)
        config_file = tmp_path / ".te_config.json"
        config_file.write_text("{}")
        assert config_exists() is True


class TestLoadConfig:
    """测试 load_config 函数"""

    def test_returns_none_when_file_not_exists(self, tmp_path, monkeypatch):
        """测试文件不存在时返回 None"""
        set_home(monkeypatch, tmp_path)
        assert load_config() is None

    def test_returns_dict_when_file_exists(self, tmp_path, monkeypatch):
        """测试文件存在时返回字典"""
        set_home(monkeypatch, tmp_path)
        config_file = tmp_path / ".te_config.json"
        config_file.write_text('{"te_path": "/test/path"}')
        result = load_config()
        assert result == {"te_path": "/test/path"}

    def test_returns_none_for_invalid_json(self, tmp_path, monkeypatch):
        """测试无效 JSON 时返回 None"""
        set_home(monkeypatch, tmp_path)
        config_file = tmp_path / ".te_config.json"
        config_file.write_text("invalid json{")
        assert load_config() is None


class TestSaveConfig:
    """测试 save_config 函数"""

    def test_saves_config_correctly(self, tmp_path, monkeypatch):
        """测试正确保存配置"""
        set_home(monkeypatch, tmp_path)
        result = save_config("/test/te/path")
        assert result is True
        
        config_file = tmp_path / ".te_config.json"
        assert config_file.exists()
        
        content = json.loads(config_file.read_text())
        assert content["te_path"] == "/test/te/path"

    def test_returns_false_on_io_error(self, tmp_path, monkeypatch):
        """测试 IO 错误时返回 False"""
        set_home(monkeypatch, tmp_path)
        
        # 模拟写入失败
        with patch("builtins.open", side_effect=PermissionError("No permission")):
            result = save_config("/test/te/path")
        
        assert result is False


class TestValidateTePath:
    """测试 validate_te_path 函数"""

    def test_empty_path_returns_invalid(self):
        """测试空路径返回无效"""
        is_valid, message = validate_te_path("")
        assert is_valid is False
        assert "不能为空" in message

    def test_nonexistent_path_returns_warning(self, tmp_path):
        """测试不存在的路径返回警告"""
        nonexistent = tmp_path / "nonexistent"
        is_valid, message = validate_te_path(str(nonexistent))
        assert is_valid is False
        assert "不存在" in message

    def test_valid_path_returns_true(self, tmp_path):
        """测试有效路径返回 True"""
        valid_dir = tmp_path / "valid_te"
        valid_dir.mkdir()
        is_valid, message = validate_te_path(str(valid_dir))
        assert is_valid is True
        assert message == ""

    def test_expands_tilde_in_path(self, tmp_path, monkeypatch):
        """测试展开 ~ 为用户主目录"""
        monkeypatch.setenv("HOME", str(tmp_path))
        valid_dir = tmp_path / "te"
        valid_dir.mkdir()
        
        is_valid, message = validate_te_path("~/te")
        assert is_valid is True


class TestSetupConfigIfNeeded:
    """测试 setup_config_if_needed 函数"""

    def test_returns_existing_config(self, tmp_path, monkeypatch):
        """测试已有配置时直接返回"""
        set_home(monkeypatch, tmp_path)
        config_file = tmp_path / ".te_config.json"
        config_file.write_text('{"te_path": "/existing/path"}')
        
        result = setup_config_if_needed()
        assert result == "/existing/path"

    def test_prompts_for_config_when_not_exists(self, tmp_path, monkeypatch):
        """测试无配置时提示用户输入"""
        set_home(monkeypatch, tmp_path)
        
        valid_dir = tmp_path / "test_te"
        valid_dir.mkdir()
        
        # 模拟用户输入
        with patch("builtins.input", return_value=str(valid_dir)):
            result = setup_config_if_needed()
        
        assert result == str(valid_dir)
        
        # 验证配置已保存
        config_file = tmp_path / ".te_config.json"
        assert config_file.exists()

    def test_handles_eof_error_gracefully(self, tmp_path, monkeypatch):
        """测试 EOFError 时使用默认值"""
        set_home(monkeypatch, tmp_path)
        
        # 模拟非交互式环境（EOFError）
        with patch("builtins.input", side_effect=EOFError()):
            result = setup_config_if_needed()
        
        # 使用默认值
        assert result == "/workspace/TransformerEngine"


class TestIsPathInEnv:
    """测试 is_path_in_env 函数"""

    def test_returns_true_when_path_in_env(self):
        """测试路径在 PATH 中时返回 True"""
        env_path = "/usr/bin:/home/user/.local/bin:/bin"
        assert is_path_in_env("/home/user/.local/bin", env_path) is True

    def test_returns_false_when_path_not_in_env(self):
        """测试路径不在 PATH 中时返回 False"""
        env_path = "/usr/bin:/bin"
        assert is_path_in_env("/home/user/.local/bin", env_path) is False

    def test_expands_tilde_when_comparing(self, tmp_path, monkeypatch):
        """测试比较时展开 ~"""
        monkeypatch.setenv("HOME", str(tmp_path))
        expanded = str(tmp_path / ".local" / "bin")
        env_path = f"/usr/bin:{expanded}:/bin"
        assert is_path_in_env("~/.local/bin", env_path) is True

    def test_uses_os_path_when_env_path_is_none(self, monkeypatch):
        """测试 env_path 为 None 时使用 os.environ['PATH']"""
        monkeypatch.setenv("PATH", "/test/path:/another/path")
        assert is_path_in_env("/test/path") is True
        assert is_path_in_env("/not/in/path") is False


class TestGetInstallPaths:
    """测试 get_install_paths 函数"""

    def test_returns_default_paths(self, tmp_path, monkeypatch):
        """测试返回默认路径"""
        set_home(monkeypatch, tmp_path)
        paths = get_install_paths()
        
        assert paths["install_bin"] == tmp_path / ".local" / "bin"
        assert paths["install_share"] == tmp_path / ".local" / "share" / "my_linux_config"
        assert paths["config_file"] == tmp_path / ".te_config.json"

    def test_returns_custom_paths_when_home_dir_provided(self, tmp_path):
        """测试提供自定义 home_dir 时返回相应路径"""
        paths = get_install_paths(str(tmp_path))
        
        assert paths["install_bin"] == tmp_path / ".local" / "bin"
        assert paths["install_share"] == tmp_path / ".local" / "share" / "my_linux_config"
        assert paths["config_file"] == tmp_path / ".te_config.json"


class TestCheckInstallation:
    """测试 check_installation 函数"""

    def test_returns_all_false_when_nothing_installed(self, tmp_path, monkeypatch):
        """测试未安装时全部返回 False"""
        set_home(monkeypatch, tmp_path)
        status = check_installation()
        
        assert status["te_script"] is False
        assert status["python_code"] is False
        assert status["config"] is False

    def test_returns_true_for_installed_components(self, tmp_path, monkeypatch):
        """测试已安装组件返回 True"""
        set_home(monkeypatch, tmp_path)
        
        # 创建所有必要的文件
        bin_dir = tmp_path / ".local" / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "te").write_text("#!/bin/bash")
        
        share_dir = tmp_path / ".local" / "share" / "my_linux_config" / "te_python"
        share_dir.mkdir(parents=True)
        (share_dir / "__init__.py").write_text("")
        
        config_file = tmp_path / ".te_config.json"
        config_file.write_text('{"te_path": "/test"}')
        
        status = check_installation()
        
        assert status["te_script"] is True
        assert status["python_code"] is True
        assert status["config"] is True
