#!/usr/bin/env python3
"""
统一配置管理模块
支持环境变量、配置文件、默认值三级配置
"""
import json
import logging
import os
import re
import socket
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import (
    BLUE, CYAN, GREEN, GREY, PURPLE, RED, RESET, YELLOW
)
from .dtk_detect import detect_dtk_base

logger = logging.getLogger(__name__)

BUILD_LOG_FILENAMES = {
    "build_py": "build_python_{hostname}.log",
    "build_cpp": "build_cpp_{hostname}.log",
    "rebuild": "rebuild_dev_{hostname}.log",
    "build_all": "build_all_{hostname}.log",
}

TEST_LOG_FILENAMES = {
    "l0cpp": "L0_cppunittest_{hostname}.log",
    "l0torch": "L0_pytorch_unittest_{hostname}.log",
    "l1torch": "L1_pytorch_distributed_unittest_{hostname}.log",
}

TEST_LOG_TYPES = tuple(TEST_LOG_FILENAMES.keys())
LOG_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
LEGACY_LOG_TIMESTAMP_FORMAT = "%Y-%m-%d::%H-%M-%S"
TIMESTAMP_PATTERN = re.compile(r"(?:\d{8}_\d{6}|\d{4}-\d{2}-\d{2}::\d{2}-\d{2}-\d{2})")
TIMESTAMP_EXAMPLE = "20260313_091738"


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
        # 委托 dtk_detect 模块统一检测 DTK 路径
        self.dtk_base = detect_dtk_base(
            dtk_26_path=self.dtk_26_path,
            dtk_default=self.dtk_base,
        )

        # 解析日志级别
        self._log_level_int = getattr(logging, self.log_level.upper(), logging.INFO)
    
    @property
    def log_level_int(self) -> int:
        """获取日志级别数值"""
        return self._log_level_int
    
    @property
    def log_files(self) -> Dict[str, str]:
        """获取日志文件路径映射"""
        hostname = socket.gethostname()
        log_files = {
            key: os.path.join(self.te_path, value.format(hostname=hostname))
            for key, value in BUILD_LOG_FILENAMES.items()
        }
        for key in TEST_LOG_TYPES:
            log_files[key] = self.get_latest_test_log(key)
        return log_files

    def get_logs_root(self) -> Path:
        """获取测试日志根目录。"""
        return Path(self.work_space).expanduser() / "logs"

    @staticmethod
    def parse_log_timestamp(timestamp: str) -> datetime:
        """解析新旧两种日志时间戳格式。"""
        for fmt in (LOG_TIMESTAMP_FORMAT, LEGACY_LOG_TIMESTAMP_FORMAT):
            try:
                return datetime.strptime(timestamp, fmt)
            except ValueError:
                continue
        raise ValueError(f"无效日志时间戳: {timestamp}")

    def new_log_timestamp(self) -> str:
        """生成新的日志时间戳目录名。"""
        return datetime.now().strftime(LOG_TIMESTAMP_FORMAT)

    def get_test_log_filename(self, log_type: str) -> str:
        """根据测试类型返回日志文件名。"""
        if log_type not in TEST_LOG_FILENAMES:
            raise ValueError(f"未知测试日志类型: {log_type}")
        return TEST_LOG_FILENAMES[log_type].format(hostname=socket.gethostname())

    def get_test_log_path(self, log_type: str, timestamp: Optional[str] = None) -> str:
        """获取某个测试类型的目标日志路径。"""
        if timestamp is None:
            timestamp = self.new_log_timestamp()
        return str(self.get_logs_root() / timestamp / log_type / self.get_test_log_filename(log_type))

    def list_log_timestamps(self, limit: Optional[int] = None) -> List[str]:
        """按时间倒序列出日志时间戳目录。"""
        logs_root = self.get_logs_root()
        if not logs_root.is_dir():
            return []

        timestamps = sorted(
            [
                entry.name
                for entry in logs_root.iterdir()
                if entry.is_dir() and TIMESTAMP_PATTERN.fullmatch(entry.name)
            ],
            key=self.parse_log_timestamp,
            reverse=True,
        )
        if limit is not None:
            return timestamps[:limit]
        return timestamps

    def list_logs_for_type(self, log_type: str, limit: Optional[int] = None) -> List[str]:
        """按时间倒序列出指定类型的测试日志绝对路径。"""
        if log_type not in TEST_LOG_TYPES:
            raise ValueError(f"未知测试日志类型: {log_type}")

        results: List[str] = []
        logs_root = self.get_logs_root()
        for timestamp in self.list_log_timestamps():
            type_dir = logs_root / timestamp / log_type
            if not type_dir.is_dir():
                continue
            for log_file in sorted(type_dir.iterdir(), reverse=True):
                if log_file.is_file():
                    results.append(str(log_file.resolve()))
                    if limit is not None and len(results) >= limit:
                        return results
        return results

    def get_latest_test_log(self, log_type: str) -> str:
        """获取指定类型最新的一条测试日志。"""
        logs = self.list_logs_for_type(log_type, limit=1)
        return logs[0] if logs else ""

    def list_logs_in_timestamp(self, timestamp: str) -> List[str]:
        """列出指定时间戳目录下所有日志文件绝对路径。"""
        target_dir = self.get_logs_root() / timestamp
        if not target_dir.is_dir():
            return []
        return sorted(
            [str(path.resolve()) for path in target_dir.rglob("*") if path.is_file()]
        )
    
    def get_init_script(self) -> str:
        """获取初始化脚本路径"""
        if self.te_init_script:
            return self.te_init_script
        # 不使用 resolve()，避免穿透软链后指向源码目录而非安装目录
        return str(Path(__file__).parent.parent / "core" / "te_init.sh")
    
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
