#!/usr/bin/env python3
"""
TE CLI 安装配置管理模块
处理首次运行的配置提示和配置文件管理
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional


def get_config_path() -> Path:
    """获取配置文件路径"""
    # 允许通过环境变量覆盖（用于测试）
    home = os.environ.get('HOME')
    if home:
        return Path(home) / ".te_config.json"
    return Path.home() / ".te_config.json"


def config_exists() -> bool:
    """检查配置文件是否存在"""
    return get_config_path().exists()


def load_config() -> Optional[dict]:
    """加载配置文件"""
    config_path = get_config_path()
    if not config_path.exists():
        return None
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def save_config(te_path: str) -> bool:
    """保存配置到文件"""
    config_path = get_config_path()
    try:
        with open(config_path, 'w') as f:
            json.dump({"te_path": te_path}, f, indent=4)
        return True
    except IOError:
        return False


def validate_te_path(te_path: str) -> tuple[bool, str]:
    """
    验证 TE 路径是否有效
    返回: (是否有效, 提示信息)
    """
    # 展开 ~ 到 $HOME
    expanded_path = os.path.expanduser(te_path)
    
    if not te_path:
        return False, "错误: TE_PATH 不能为空"
    
    if not os.path.isdir(expanded_path):
        return False, f"警告: 目录 '{te_path}' 不存在"
    
    return True, ""


def prompt_for_te_path() -> str:
    """
    提示用户输入 TE_PATH
    返回用户输入的路径（已展开 ~）
    """
    print("=" * 40)
    print("  TE CLI - First Time Setup")
    print("=" * 40)
    print()
    print("Please enter the path to your TransformerEngine source directory.")
    print("Example: /home/username/TransformerEngine")
    print()
    
    while True:
        try:
            te_path = input("TE_PATH: ").strip()
        except EOFError:
            # 非交互式环境（如测试），使用默认值
            te_path = "/workspace/TransformerEngine"
            print(f"TE_PATH: {te_path}")
        
        if not te_path:
            print("错误: TE_PATH 不能为空，请重新输入")
            continue
        
        # 展开 ~ 到 $HOME
        expanded_path = os.path.expanduser(te_path)
        
        # 验证路径
        is_valid, message = validate_te_path(expanded_path)
        if not is_valid:
            print(message)
            try:
                confirm = input("Continue anyway? [y/N] ").strip().lower()
            except EOFError:
                confirm = "y"  # 测试环境默认继续
            if confirm != 'y':
                continue
        
        return expanded_path


def setup_config_if_needed() -> Optional[str]:
    """
    检查并设置配置（如果需要）
    返回: te_path 或 None（如果配置失败）
    """
    if config_exists():
        config = load_config()
        if config and "te_path" in config:
            return config["te_path"]
    
    # 需要配置
    te_path = prompt_for_te_path()
    
    if save_config(te_path):
        print()
        print(f"Configuration saved to {get_config_path()}")
        print("You can edit this file later to change settings.")
        print()
        return te_path
    else:
        print("错误: 无法保存配置文件")
        return None


def is_path_in_env(path: str, env_path: str = None) -> bool:
    """
    检查路径是否在环境变量 PATH 中
    
    Args:
        path: 要检查的路径
        env_path: 可选，自定义 PATH 字符串，默认使用 os.environ.get('PATH', '')
    
    Returns:
        bool: 路径是否在 PATH 中
    """
    if env_path is None:
        env_path = os.environ.get('PATH', '')
    
    # 处理路径中的 ~
    expanded_path = os.path.expanduser(path)
    
    # PATH 格式为 : 分隔的路径列表
    paths = env_path.split(':')
    
    for p in paths:
        if os.path.expanduser(p) == expanded_path:
            return True
    
    return False


def get_install_paths(home_dir: Optional[str] = None) -> dict:
    """
    获取安装路径
    
    Args:
        home_dir: 可选，自定义 HOME 目录，默认使用 Path.home()
    
    Returns:
        dict: 包含 install_bin, install_share, config_file 的字典
    """
    if home_dir is None:
        home = Path.home()
    else:
        home = Path(home_dir)
    
    return {
        "install_bin": home / ".local" / "bin",
        "install_share": home / ".local" / "share" / "my_linux_config",
        "config_file": home / ".te_config.json",
    }


def check_installation(home_dir: Optional[str] = None) -> dict:
    """
    检查安装状态
    
    Returns:
        dict: 包含各组件安装状态的字典
    """
    paths = get_install_paths(home_dir)
    
    return {
        "te_script": paths["install_bin"].exists() and (paths["install_bin"] / "te").exists(),
        "python_code": paths["install_share"].exists() and (paths["install_share"] / "te_python").exists(),
        "config": paths["config_file"].exists(),
    }
