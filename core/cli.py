#!/usr/bin/env python3
"""
TE CLI - 命令行入口模块

这是 TE 开发工具的命令行入口，负责解析参数并路由到相应的功能模块。
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
    print(f"   {GREY}用法:{RESET} te [简化参数组合]")
    print("")
    print(f"   {CYAN}编译构建:{RESET}")
    print(f"     {YELLOW}-b -c{RESET}        编译 Python（增量）")
    print(f"     {YELLOW}-b -c -d{RESET}     编译 Python（全量/clean）")
    print(f"     {YELLOW}-b -c -l{RESET}     查看 Python 编译日志")
    print(f"     {YELLOW}-b -t{RESET}        编译 C++ 测试")
    print(f"     {YELLOW}-b -t -d{RESET}     清理并编译 C++ 测试")
    print(f"     {YELLOW}-b -t -l{RESET}     查看 C++ 编译日志")
    print(f"     {YELLOW}-b -r{RESET}        智能重建（仅修改的文件）")
    print(f"     {YELLOW}-b -r -d{RESET}     全量重建（clean + build）")
    print(f"     {YELLOW}-b -r -l{RESET}     查看重建日志")
    print(f"     {YELLOW}-b -k{RESET}        终止编译任务")
    print("")
    print(f"   {CYAN}测试运行:{RESET}")
    print(f"     {YELLOW}-0 -c{RESET}        L0 C++ 单元测试")
    print(f"     {YELLOW}-0 -c -l{RESET}     查看 L0 C++ 测试日志")
    print(f"     {YELLOW}-0 -c -k{RESET}     终止 L0 C++ 测试")
    print(f"     {YELLOW}-0 -t{RESET}        L0 PyTorch 单元测试")
    print(f"     {YELLOW}-0 -t -l{RESET}     查看 L0 PyTorch 测试日志")
    print(f"     {YELLOW}-0 -t -k{RESET}     终止 L0 PyTorch 测试")
    print(f"     {YELLOW}-1 -t{RESET}        L1 PyTorch 分布式测试")
    print(f"     {YELLOW}-1 -t -l{RESET}     查看 L1 测试日志")
    print(f"     {YELLOW}-1 -t -k{RESET}     终止 L1 测试")
    print("")
    print(f"   {CYAN}进程与状态:{RESET}")
    print(f"     {YELLOW}-p{RESET}           查看所有运行中的任务")
    print(f"     {YELLOW}-s{RESET}           深度检查 TE 环境状态")
    print("")
    print(f"   {CYAN}其他选项:{RESET}")
    print(f"     {YELLOW}-v{RESET}           显示版本信息")
    print(f"     {YELLOW}--check-env{RESET}   检查环境依赖")
    print(f"     {YELLOW}-V{RESET}           详细日志输出")
    print(f"     {YELLOW}-h{RESET}           显示此帮助")
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
