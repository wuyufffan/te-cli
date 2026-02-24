#!/usr/bin/env python3
"""
环境依赖检查模块
启动时预检查所有外部依赖
"""
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from config import GREEN, RED, RESET, YELLOW
from config_manager import get_config

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    """检查结果"""
    name: str
    required: bool  # 是否为必需依赖
    exists: bool
    path: str = ""
    version: str = ""
    message: str = ""
    
    @property
    def status_icon(self) -> str:
        if self.exists:
            return f"{GREEN}✓{RESET}"
        elif self.required:
            return f"{RED}✗{RESET}"
        else:
            return f"{YELLOW}⚠{RESET}"
    
    @property
    def is_ok(self) -> bool:
        return self.exists or not self.required


class EnvironmentChecker:
    """环境检查器"""
    
    def __init__(self):
        self.config = get_config()
        self.results: List[CheckResult] = []
    
    def check_all(self) -> Tuple[bool, List[CheckResult]]:
        """执行所有检查
        
        Returns:
            (是否全部通过, 检查结果列表)
        """
        self.results = []
        
        # 路径检查
        self._check_path("TE_PATH", self.config.te_path, required=True)
        self._check_path("WORK_SPACE", self.config.work_space, required=True)
        self._check_file("初始化脚本", self.config.get_init_script(), required=True)
        
        # DTK 检查
        self._check_path("DTK", self.config.dtk_base, required=True)
        
        # 工具检查
        self._check_command("CMake", "cmake", ["--version"], required=True)
        self._check_command("Ninja", "ninja", ["--version"], required=False)
        self._check_command("Python3", "python3", ["--version"], required=True)
        self._check_command("pip", "pip", ["--version"], required=True)
        
        # Python 模块检查
        self._check_python_module("transformer_engine", required=False)
        
        # 检查所有必需项是否通过
        all_passed = all(r.is_ok for r in self.results)
        
        return all_passed, self.results
    
    def _check_path(self, name: str, path: str, required: bool = True) -> None:
        """检查目录路径"""
        exists = os.path.isdir(path)
        result = CheckResult(
            name=name,
            required=required,
            exists=exists,
            path=path,
            message=f"存在" if exists else f"不存在: {path}"
        )
        self.results.append(result)
        logger.debug(f"检查 {name}: {result.message}")
    
    def _check_file(self, name: str, path: str, required: bool = True) -> None:
        """检查文件"""
        exists = os.path.isfile(path)
        result = CheckResult(
            name=name,
            required=required,
            exists=exists,
            path=path,
            message=f"存在" if exists else f"不存在: {path}"
        )
        self.results.append(result)
        logger.debug(f"检查 {name}: {result.message}")
    
    def _check_command(self, name: str, cmd: str, args: List[str], required: bool = True) -> None:
        """检查命令是否可用"""
        cmd_path = shutil.which(cmd)
        if cmd_path is None:
            result = CheckResult(
                name=name,
                required=required,
                exists=False,
                message=f"未找到命令: {cmd}"
            )
        else:
            try:
                output = subprocess.run(
                    [cmd] + args,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                version = output.stdout.strip().split('\n')[0] if output.stdout else ""
                result = CheckResult(
                    name=name,
                    required=required,
                    exists=True,
                    path=cmd_path,
                    version=version,
                    message=f"{cmd_path}"
                )
            except Exception as e:
                result = CheckResult(
                    name=name,
                    required=required,
                    exists=True,
                    path=cmd_path,
                    message=f"存在但无法获取版本: {e}"
                )
        
        self.results.append(result)
        logger.debug(f"检查 {name}: {result.message}")
    
    def _check_python_module(self, name: str, required: bool = False) -> None:
        """检查 Python 模块"""
        try:
            __import__(name)
            result = CheckResult(
                name=f"Python模块:{name}",
                required=required,
                exists=True,
                message=f"已安装"
            )
        except ImportError:
            result = CheckResult(
                name=f"Python模块:{name}",
                required=required,
                exists=False,
                message=f"未安装"
            )
        
        self.results.append(result)
        logger.debug(f"检查 Python 模块 {name}: {result.message}")
    
    def print_report(self) -> None:
        """打印检查报告"""
        print(f"\n{'='*60}")
        print("环境依赖检查报告")
        print(f"{'='*60}")
        
        required_failed = []
        
        for result in self.results:
            status = result.status_icon
            req_mark = "[必需]" if result.required else "[可选]"
            print(f"{status} {req_mark} {result.name:20s} {result.message}")
            
            if result.required and not result.exists:
                required_failed.append(result)
        
        print(f"{'='*60}")
        
        if required_failed:
            print(f"{RED}✗ 检查失败，缺少 {len(required_failed)} 个必需依赖{RESET}")
            print("\n请安装或配置以下依赖：")
            for r in required_failed:
                print(f"  - {r.name}: {r.path}")
        else:
            print(f"{GREEN}✓ 所有必需依赖已就绪{RESET}")
        
        print(f"{'='*60}\n")


def check_environment(quiet: bool = False) -> bool:
    """便捷函数：检查环境并打印报告
    
    Args:
        quiet: 是否静默模式（不打印报告）
    
    Returns:
        是否通过检查
    """
    checker = EnvironmentChecker()
    passed, results = checker.check_all()
    
    if not quiet:
        checker.print_report()
    
    return passed


if __name__ == "__main__":
    # 直接运行进行测试
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    from logger import setup_logging
    setup_logging(level=logging.DEBUG)
    
    success = check_environment(quiet=False)
    sys.exit(0 if success else 1)
