#!/usr/bin/env python3
"""
TE CLI 主入口
"""
import argparse
import logging
import sys
from typing import List, Optional, Tuple

from build_helpers import (
    build_all_func,
    build_clean_cpp,
    build_cpp_test_func,
    build_te_func,
    build_te_func_incremental,
    rebuild_dev,
)
from config import CYAN, GREEN, GREY, RED, RESET, YELLOW
from config_manager import get_config, init_config
from env_checker import check_environment
from logger import setup_logging
from process_helpers import kill_build_task, kill_test_task, show_processes
from test_helpers import run_l0cpp, run_l0torch, run_l1torch
from utils_helpers import check_te, view_log

logger = logging.getLogger(__name__)


def print_help() -> int:
    """打印帮助信息"""
    print(f"{GREEN}✅ TE 开发工具命令行 (TE CLI){RESET}")
    print(f"   {GREY}用法:{RESET} te [指令] {GREY}(支持完整语法与简写乱序){RESET}")
    print("")
    print(f"   {GREY}├── 编译构建 (Build):{RESET}")
    print(f"   {GREY}│   ├──{RESET} {CYAN}--build --core [--delete] [--log]{RESET}     {GREY}或{RESET}  {CYAN}-b -c [-d] [-l]{RESET}   {GREY}编译 Python{RESET}")
    print(f"   {GREY}│   ├──{RESET} {CYAN}--build --test [--delete] [--log]{RESET}     {GREY}或{RESET}  {CYAN}-b -t [-d] [-l]{RESET}   {GREY}编译 C++ 测试{RESET}")
    print(f"   {GREY}│   ├──{RESET} {CYAN}--rebuild [--delete] [--log]{RESET}          {GREY}或{RESET}  {CYAN}-b -r [-d] [-l]{RESET}   {GREY}智能重编/全量重编{RESET}")
    print(f"   {GREY}│   └──{RESET} {CYAN}--build --kill{RESET}                        {GREY}或{RESET}  {CYAN}-b -k{RESET}            {GREY}终止编译任务{RESET}")
    print("")
    print(f"   {GREY}├── 测试运行 (Test):{RESET}")
    print(f"   {GREY}│   ├──{RESET} {CYAN}--l0 --cpp [--log|--kill]{RESET}             {GREY}或{RESET}  {CYAN}-0 -c [-l|-k]{RESET}     {GREY}L0 C++ 单元测试{RESET}")
    print(f"   {GREY}│   ├──{RESET} {CYAN}--l0 --torch [--log|--kill]{RESET}           {GREY}或{RESET}  {CYAN}-0 -t [-l|-k]{RESET}     {GREY}L0 Torch 单元测试{RESET}")
    print(f"   {GREY}│   └──{RESET} {CYAN}--l1 --torch [--log|--kill]{RESET}           {GREY}或{RESET}  {CYAN}-1 -t [-l|-k]{RESET}     {GREY}L1 Torch 分布式测试{RESET}")
    print("")
    print(f"   {GREY}└── 进程与状态查询 (Process & Status):{RESET}")
    print(f"   {GREY}    ├──{RESET} {CYAN}--process{RESET}                             {GREY}或{RESET}  {CYAN}-p{RESET}                {GREY}查看所有运行中的任务{RESET}")
    print(f"   {GREY}    └──{RESET} {CYAN}--status{RESET}                              {GREY}或{RESET}  {CYAN}-s{RESET}                {GREY}深度检查 TE 环境状态{RESET}")
    print("")
    print(f"   {GREY}其他选项:{RESET}")
    print(f"   {GREY}    ├──{RESET} {CYAN}--version{RESET}                             {GREY}或{RESET}  {CYAN}-v{RESET}                {GREY}显示版本信息{RESET}")
    print(f"   {GREY}    ├──{RESET} {CYAN}--check-env{RESET}                                               {GREY}检查环境依赖{RESET}")
    print(f"   {GREY}    └──{RESET} {CYAN}--verbose{RESET}                           {GREY}或{RESET}  {CYAN}-V{RESET}                {GREY}详细日志输出{RESET}")
    return 0


def parse_args(argv: List[str]) -> argparse.Namespace:
    """解析命令行参数
    
    Args:
        argv: 命令行参数列表
    
    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        prog='te',
        description='TE 开发工具命令行',
        add_help=False
    )
    
    # 帮助和版本
    parser.add_argument('-h', '--help', action='store_true', help='显示帮助')
    parser.add_argument('-v', '--version', action='store_true', help='显示版本')
    parser.add_argument('--check-env', action='store_true', help='检查环境依赖')
    parser.add_argument('-V', '--verbose', action='store_true', help='详细日志')
    
    # 构建相关
    parser.add_argument('-b', '--build', action='store_true', help='构建')
    parser.add_argument('-c', '--core', action='store_true', help='Python 核心')
    parser.add_argument('--cpp', action='store_true', help='C++ 测试 (与 -c 相同含义)')
    parser.add_argument('-t', '--test', '--torch', action='store_true', help='测试/C++')
    parser.add_argument('-r', '--rebuild', action='store_true', help='重建')
    parser.add_argument('-d', '--delete', '--clean', action='store_true', help='清理')
    parser.add_argument('-l', '--log', action='store_true', help='查看日志')
    parser.add_argument('-k', '--kill', action='store_true', help='终止任务')
    
    # 测试级别
    parser.add_argument('-0', '--l0', action='store_true', help='L0 测试')
    parser.add_argument('-1', '--l1', action='store_true', help='L1 测试')
    
    # 进程管理
    parser.add_argument('-p', '--process', action='store_true', help='查看进程')
    parser.add_argument('-s', '--status', action='store_true', help='环境状态')
    
    return parser.parse_args(argv)


def check_conflicts(args: argparse.Namespace) -> Tuple[bool, str]:
    """检查参数冲突
    
    Args:
        args: 解析后的参数
    
    Returns:
        (是否有冲突, 错误信息)
    """
    # 重建与其他构建选项冲突
    if args.rebuild and (args.core or args.test):
        return True, "Rebuild (-r) 是全量构建，不能与 Core (-c) 或 Test (-t) 同时使用"
    
    # 核心与测试冲突
    if args.core and args.test:
        return True, "Core (-c) 和 Test (-t) 不能同时运行 (请分两次执行)"
    
    return False, ""


def route_build_command(args: argparse.Namespace) -> int:
    """路由构建相关命令
    
    Args:
        args: 解析后的参数
    
    Returns:
        命令执行结果
    """
    # 检查冲突
    has_conflict, error_msg = check_conflicts(args)
    if has_conflict:
        logger.error(f"参数冲突: {error_msg}")
        print(f"{RED}❌ 错误: 参数冲突{RESET}")
        print(f"{GREY}{error_msg}{RESET}")
        return 1
    
    # 终止构建任务
    if args.kill:
        return kill_build_task()
    
    # 重建
    if args.rebuild:
        if args.log:
            return view_log("build_all" if args.delete else "rebuild")
        return build_all_func() if args.delete else rebuild_dev()
    
    # Python 构建
    if args.core:
        if args.log:
            return view_log("build_py")
        return build_te_func() if args.delete else build_te_func_incremental()
    
    # C++ 构建
    if args.test:
        if args.log:
            return view_log("build_cpp")
        if args.delete:
            status = build_clean_cpp()
            if status != 0:
                return status
        return build_cpp_test_func()
    
    # 默认：显示帮助
    return print_help()


def route_test_command(args: argparse.Namespace) -> int:
    """路由测试相关命令
    
    Args:
        args: 解析后的参数
    
    Returns:
        命令执行结果
    """
    # 判断是否使用 C++ 测试（-c, --core, --cpp）
    use_cpp = args.cpp or args.core
    
    # L0 测试
    if args.l0:
        if use_cpp:  # C++ 测试
            if args.log:
                return view_log("l0cpp")
            if args.kill:
                return kill_test_task("qa/L0_cppunittest/test.sh", "L0 CPP Test")
            return run_l0cpp()
        
        if args.test:  # PyTorch 测试
            if args.log:
                return view_log("l0torch")
            if args.kill:
                return kill_test_task("qa/L0_pytorch_unittest/test.sh", "L0 Torch Test")
            return run_l0torch()
    
    # L1 测试
    if args.l1 and args.test:
        if args.log:
            return view_log("l1torch")
        if args.kill:
            return kill_test_task("qa/L1_pytorch_distributed_unittest/test.sh", "L1 Torch Test")
        return run_l1torch()
    
    return print_help()


def route_command(args: argparse.Namespace) -> int:
    """主路由函数
    
    Args:
        args: 解析后的参数
    
    Returns:
        命令执行结果
    """
    # 帮助
    if args.help:
        return print_help()
    
    # 版本
    if args.version:
        print("TE CLI v1.0.0")
        return 0
    
    # 环境检查
    if args.check_env:
        return 0 if check_environment(quiet=False) else 1
    
    # 进程查看
    if args.process:
        return show_processes()
    
    # 环境状态
    if args.status:
        return check_te()
    
    # 构建相关
    if args.build:
        return route_build_command(args)
    
    # 测试相关
    if args.l0 or args.l1:
        return route_test_command(args)
    
    # 长格式参数处理
    if hasattr(args, 'rebuild') and args.rebuild:
        if args.log:
            return view_log("build_all" if args.delete else "rebuild")
        if args.delete:
            return build_all_func()
        return rebuild_dev()
    
    # 默认：显示帮助
    return print_help()


def main(argv: Optional[List[str]] = None) -> int:
    """主入口函数
    
    Args:
        argv: 可选的命令行参数列表，默认为 sys.argv[1:]
    
    Returns:
        程序退出码
    """
    if argv is None:
        argv = sys.argv[1:]
    
    # 快速检查是否需要帮助或环境检查（在完整解析前）
    if not argv or '-h' in argv or '--help' in argv:
        return print_help()
    
    # 检查详细日志模式
    verbose = '-V' in argv or '--verbose' in argv
    
    # 初始化配置和日志
    init_config(log_level='DEBUG' if verbose else 'INFO')
    setup_logging(level=logging.DEBUG if verbose else logging.INFO)
    
    logger.debug(f"命令行参数: {argv}")
    
    try:
        # 解析参数
        args = parse_args(argv)
        
        # 路由命令
        result = route_command(args)
        
        logger.debug(f"命令执行结果: {result}")
        return result
        
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    except Exception as e:
        logger.exception("命令执行失败")
        print(f"{RED}❌ 错误: {e}{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
