#!/usr/bin/env python3
"""
setup.sh 和 uninstall.sh 集成测试
真实执行安装和卸载脚本
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest


# =============================================================================
# 辅助函数
# =============================================================================

def run_script(script_path, env=None, cwd=None):
    """运行 shell 脚本并返回结果"""
    result = subprocess.run(
        ["bash", str(script_path)],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd
    )
    return result


# =============================================================================
# setup.sh 集成测试
# =============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestSetupScript:
    """测试 setup.sh 的真实执行"""
    
    def test_setup_script_syntax(self, repo_root):
        """测试 setup.sh 脚本语法正确"""
        setup_script = repo_root / "setup.sh"
        
        result = subprocess.run(
            ["bash", "-n", str(setup_script)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"脚本语法错误: {result.stderr}"
    
    def test_setup_creates_symlinks(self, repo_root, tmp_path, monkeypatch):
        """测试 setup.sh 创建正确的符号链接"""
        # 设置 HOME 环境变量为临时目录
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        
        env = os.environ.copy()
        env["HOME"] = str(home_dir)
        
        setup_script = repo_root / "setup.sh"
        
        # 运行 setup.sh
        result = subprocess.run(
            ["bash", str(setup_script)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(repo_root)
        )
        
        # 检查脚本执行成功
        # 注意：脚本可能因为已经存在的配置而部分失败，但我们检查它尝试创建链接
        print(f"Setup stdout: {result.stdout}")
        print(f"Setup stderr: {result.stderr}")
        
        # 验证备份目录被创建（如果存在旧配置）
        backup_dirs = list(home_dir.glob(".config_backup_*"))
        
        # 验证符号链接或文件存在
        assert (home_dir / ".bashrc").exists() or "Linked .bashrc" in result.stdout, \
            "应该创建 .bashrc 链接"
        assert (home_dir / ".vimrc").exists() or "Linked .vimrc" in result.stdout, \
            "应该创建 .vimrc 链接"
    
    def test_setup_creates_backup(self, repo_root, tmp_path, monkeypatch):
        """测试 setup.sh 正确创建备份"""
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        
        # 创建现有的配置文件
        (home_dir / ".bashrc").write_text("# Original bashrc\n")
        (home_dir / ".vimrc").write_text("# Original vimrc\n")
        
        env = os.environ.copy()
        env["HOME"] = str(home_dir)
        
        setup_script = repo_root / "setup.sh"
        
        # 运行 setup.sh
        result = subprocess.run(
            ["bash", str(setup_script)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(repo_root)
        )
        
        print(f"Setup stdout: {result.stdout}")
        
        # 验证备份被创建
        backup_dirs = list(home_dir.glob(".config_backup_*"))
        assert len(backup_dirs) > 0, "应该创建备份目录"
        
        # 验证备份包含原始文件
        backup_dir = backup_dirs[0]
        assert (backup_dir / ".bashrc").exists(), "备份应该包含 .bashrc"
        assert (backup_dir / ".vimrc").exists(), "备份应该包含 .vimrc"
        assert (backup_dir / ".bashrc").read_text() == "# Original bashrc\n"


# =============================================================================
# uninstall.sh 集成测试
# =============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestUninstallScript:
    """测试 uninstall.sh 的真实执行"""
    
    def test_uninstall_script_syntax(self, repo_root):
        """测试 uninstall.sh 脚本语法正确"""
        uninstall_script = repo_root / "uninstall.sh"
        
        result = subprocess.run(
            ["bash", "-n", str(uninstall_script)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"脚本语法错误: {result.stderr}"
    
    def test_uninstall_removes_symlinks(self, repo_root, tmp_path):
        """测试 uninstall.sh 删除符号链接"""
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        
        # 创建符号链接
        (home_dir / ".bashrc").symlink_to(repo_root / "core" / ".bashrc")
        (home_dir / ".vimrc").symlink_to(repo_root / "core" / ".vimrc")
        (home_dir / "te_init.sh").symlink_to(repo_root / "core" / "te_init.sh")
        
        env = os.environ.copy()
        env["HOME"] = str(home_dir)
        
        uninstall_script = repo_root / "uninstall.sh"
        
        # 运行 uninstall.sh
        result = subprocess.run(
            ["bash", str(uninstall_script)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(repo_root)
        )
        
        print(f"Uninstall stdout: {result.stdout}")
        
        # 验证符号链接被删除
        assert not (home_dir / ".bashrc").exists(), ".bashrc 链接应该被删除"
        assert not (home_dir / ".vimrc").exists(), ".vimrc 链接应该被删除"
    
    def test_uninstall_restores_backup(self, repo_root, tmp_path):
        """测试 uninstall.sh 恢复备份"""
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        
        # 创建备份目录和原始文件
        backup_dir = home_dir / ".config_backup_20240115_120000"
        backup_dir.mkdir()
        (backup_dir / ".bashrc").write_text("# Restored bashrc\n")
        (backup_dir / ".vimrc").write_text("# Restored vimrc\n")
        
        # 创建符号链接
        (home_dir / ".bashrc").symlink_to(repo_root / "core" / ".bashrc")
        (home_dir / ".vimrc").symlink_to(repo_root / "core" / ".vimrc")
        
        env = os.environ.copy()
        env["HOME"] = str(home_dir)
        
        uninstall_script = repo_root / "uninstall.sh"
        
        # 运行 uninstall.sh
        result = subprocess.run(
            ["bash", str(uninstall_script)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(repo_root)
        )
        
        print(f"Uninstall stdout: {result.stdout}")
        
        # 验证文件被恢复
        assert (home_dir / ".bashrc").exists(), ".bashrc 应该存在"
        assert (home_dir / ".vimrc").exists(), ".vimrc 应该存在"
        assert not (home_dir / ".bashrc").is_symlink(), ".bashrc 不应该再是符号链接"
        assert (home_dir / ".bashrc").read_text() == "# Restored bashrc\n"
    
    def test_uninstall_no_backup(self, repo_root, tmp_path):
        """测试 uninstall.sh 在没有备份时的行为"""
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        
        # 创建符号链接但没有备份
        (home_dir / ".bashrc").symlink_to(repo_root / "core" / ".bashrc")
        
        env = os.environ.copy()
        env["HOME"] = str(home_dir)
        
        uninstall_script = repo_root / "uninstall.sh"
        
        # 运行 uninstall.sh
        result = subprocess.run(
            ["bash", str(uninstall_script)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(repo_root)
        )
        
        print(f"Uninstall stdout: {result.stdout}")
        
        # 应该显示警告
        assert "No backup" in result.stdout or "⚠️" in result.stdout or "Manual" in result.stdout or result.returncode == 0


# =============================================================================
# 安装-卸载循环测试
# =============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestSetupUninstallCycle:
    """测试完整的安装-卸载循环"""
    
    def test_full_setup_uninstall_cycle(self, repo_root, tmp_path):
        """测试完整的安装然后卸载流程"""
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        
        # 创建原始配置
        original_bashrc = "# Original user bashrc\nexport CUSTOM_VAR=1\n"
        original_vimrc = "# Original user vimrc\nset number\n"
        (home_dir / ".bashrc").write_text(original_bashrc)
        (home_dir / ".vimrc").write_text(original_vimrc)
        
        env = os.environ.copy()
        env["HOME"] = str(home_dir)
        
        setup_script = repo_root / "setup.sh"
        uninstall_script = repo_root / "uninstall.sh"
        
        # 第一步：运行 setup.sh
        setup_result = subprocess.run(
            ["bash", str(setup_script)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(repo_root)
        )
        print(f"Setup stdout: {setup_result.stdout}")
        assert setup_result.returncode == 0, f"Setup 失败: {setup_result.stderr}"
        
        # 验证备份被创建
        backup_dirs = list(home_dir.glob(".config_backup_*"))
        assert len(backup_dirs) == 1, "应该创建一个备份目录"
        
        # 验证符号链接存在
        assert (home_dir / ".bashrc").is_symlink(), "安装后 .bashrc 应该是符号链接"
        
        # 第二步：运行 uninstall.sh
        uninstall_result = subprocess.run(
            ["bash", str(uninstall_script)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(repo_root)
        )
        print(f"Uninstall stdout: {uninstall_result.stdout}")
        assert uninstall_result.returncode == 0, f"Uninstall 失败: {uninstall_result.stderr}"
        
        # 验证文件被恢复为原始内容
        assert (home_dir / ".bashrc").read_text() == original_bashrc, \
            ".bashrc 应该恢复为原始内容"
        assert (home_dir / ".vimrc").read_text() == original_vimrc, \
            ".vimrc 应该恢复为原始内容"
        assert not (home_dir / ".bashrc").is_symlink(), "卸载后 .bashrc 不应该是符号链接"
