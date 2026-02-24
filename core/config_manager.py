#!/usr/bin/env python3
"""
统一配置管理模块
支持环境变量、配置文件、默认值三级配置
"""
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import (
    BLUE, CYAN, GREEN, GREY, PURPLE, RED, RESET, YELLOW
)

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """TE 配置类"""
    # 路径配置
    te_path: str = field(default_factory=lambda: os.environ.get('TE_PATH', '/workspace/TransformerEngine'))
    work_space: str = field(default_factory=lambda: os.environ.get('WORK_SPACE', '/workspace'))
    te_init_script: str = field(default_factory=lambda: os.environ.get('TE_INIT_SCRIPT', ''))
    
    # DTK 配置
    dtk_base: str = "/opt/dtk-25.04.2"
    dtk_26_path: str = "/opt/dtk-26.04"
    
    # 日志级别
    log_level: str = field(default_factory=lambda: os.environ.get('TE_LOG_LEVEL', 'INFO'))
    
    def __post_init__(self):
        """初始化后处理"""
        # 自动检测 DTK 版本
        if os.path.isdir(self.dtk_26_path):
            self.dtk_base = self.dtk_26_path
            logger.debug(f"检测到 DTK 26.04: {self.dtk_base}")
        
        # 解析日志级别
        self._log_level_int = getattr(logging, self.log_level.upper(), logging.INFO)
    
    @property
    def log_level_int(self) -> int:
        """获取日志级别数值"""
        return self._log_level_int
    
    @property
    def log_files(self) -> Dict[str, str]:
        """获取日志文件路径映射"""
        return {
            "build_py": os.path.join(self.te_path, "build_python.log"),
            "build_cpp": os.path.join(self.te_path, "build_cpp.log"),
            "rebuild": os.path.join(self.te_path, "rebuild_dev.log"),
            "build_all": os.path.join(self.te_path, "build_all.log"),
            "l0cpp": os.path.join(self.te_path, "L0_cppunittest_kme.log"),
            "l0torch": os.path.join(self.te_path, "L0_pytorch_unittest_kme.log"),
            "l1torch": os.path.join(self.te_path, "L1_pytorch_distributed_unittest_kme.log"),
        }
    
    def get_init_script(self) -> str:
        """获取初始化脚本路径"""
        if self.te_init_script:
            return self.te_init_script
        return str(Path(__file__).resolve().parents[1] / "core" / "te_init.sh")
    
    def validate(self) -> Tuple[bool, List[str]]:
        """验证配置有效性
        
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 检查 TE 路径
        if not os.path.isdir(self.te_path):
            errors.append(f"TE_PATH 不存在: {self.te_path}")
        
        # 检查 DTK
        if not os.path.isdir(self.dtk_base):
            errors.append(f"DTK 未安装: {self.dtk_base}")
        
        # 检查初始化脚本
        init_script = self.get_init_script()
        if not os.path.isfile(init_script):
            errors.append(f"初始化脚本不存在: {init_script}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def from_file(cls, config_path: Optional[str] = None) -> 'Config':
        """从配置文件加载配置"""
        if config_path is None:
            config_path = os.path.expanduser("~/.te_config.json")
        
        config = cls()
        
        if os.path.isfile(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(config, key):
                            setattr(config, key, value)
                logger.info(f"已从 {config_path} 加载配置")
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}")
        
        return config
    
    def save(self, config_path: Optional[str] = None) -> None:
        """保存配置到文件"""
        if config_path is None:
            config_path = os.path.expanduser("~/.te_config.json")
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'te_path': self.te_path,
                    'work_space': self.work_space,
                    'te_init_script': self.te_init_script,
                    'log_level': self.log_level,
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存到 {config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例（单例模式）"""
    global _config
    if _config is None:
        _config = Config.from_file()
    return _config


def init_config(log_level: Optional[str] = None) -> Config:
    """初始化配置并设置日志"""
    global _config
    _config = Config.from_file()
    
    if log_level:
        _config.log_level = log_level
    
    # 设置日志级别
    logging.getLogger().setLevel(_config.log_level_int)
    
    return _config
