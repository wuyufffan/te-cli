#!/usr/bin/env python3
"""
TE CLI - 命令行入口模块

这是 TE 开发工具的命令行入口，负责解析参数并路由到相应的功能模块。
"""
import argparse
import logging
import sys
from typing import List, Optional, Tuple

from .build_helpers import (
    build_all_func,
    build_clean_cpp,
    build_cpp_test_func,
    build_te_func,
    build_te_func_incremental,
    rebuild_dev,
)
from .build_command import (
    route_build_named_command,
    route_rebuild_named_command,
)
from .config import CYAN, GREEN, GREY, RED, RESET, YELLOW
from .config_manager import TIMESTAMP_EXAMPLE, init_config
from .env_checker import check_environment
from .log_command import route_log_command
from .logger import setup_logging
from .process_helpers import kill_build_task, kill_test_task, show_processes
from .run_command import route_run_command
from .summary_command import route_summary_command
from .test_helpers import run_l0cpp, run_l0torch, run_l1torch
from .utils_helpers import check_te, view_log

logger = logging.getLogger(__name__)


LEGACY_COMPAT_MAPPINGS = {
    ("-0", "-c"): "te run l0cpp",
    ("-0", "-t"): "te run l0torch",
    ("-1", "-t"): "te run l1torch",
    ("-b", "-c"): "te rebuild py",
    ("-b", "-t"): "te rebuild cpp",
    ("-b", "-r"): "te rebuild all",
}


def _detect_legacy_compat_target(args: argparse.Namespace) -> Optional[str]:
    if args.l0 and (args.core or args.cpp) and not (args.log or args.kill or args.delete):
        return LEGACY_COMPAT_MAPPINGS[("-0", "-c")]
    if args.l0 and args.test and not (args.log or args.kill or args.delete):
        return LEGACY_COMPAT_MAPPINGS[("-0", "-t")]
    if args.l1 and args.test and not (args.log or args.kill or args.delete):
        return LEGACY_COMPAT_MAPPINGS[("-1", "-t")]
    if args.build and args.core and not (args.log or args.kill or args.delete or args.rebuild):
        return LEGACY_COMPAT_MAPPINGS[("-b", "-c")]
    if args.build and args.test and not (args.log or args.kill or args.delete or args.rebuild):
        return LEGACY_COMPAT_MAPPINGS[("-b", "-t")]
    if args.build and args.rebuild and not (args.log or args.kill or args.delete):
        return LEGACY_COMPAT_MAPPINGS[("-b", "-r")]
    return None


def _legacy_compat_message(target: str) -> None:
    print(f"{YELLOW}⚠️  旧 flag 兼容入口将逐步退出，请改用: {target}{RESET}")


def _legacy_compat_error(args: argparse.Namespace) -> bool:
    legacy_like = args.build or args.l0 or args.l1
    if not legacy_like:
        return False

    target = _detect_legacy_compat_target(args)
    if target is not None:
        _legacy_compat_message(target)
        return False

    if args.log or args.kill or args.delete:
        print(f"{RED}❌ 旧 flag 的 -l / -k / -d 兼容入口已收缩，请改用命名式命令。{RESET}")
        print(f"{GREY}示例: te log l0torch -n 1, te build py, te rebuild all{RESET}")
        return True

    return False


def print_help() -> int:
    """打印帮助信息"""
    print(f"{GREEN}✅ TE 开发工具命令行 (TE CLI){RESET}")
    print(f"   {GREY}用法:{RESET} te <command> [args] | te [兼容 flag]")
    print("")
    print(f"   {CYAN}快速上手:{RESET}")
    print(f"     {YELLOW}te run{RESET}                 交互式选择并启动测试")
    print(f"     {YELLOW}te log list{RESET}            查看最近日志时间戳目录")
    print(f"     {YELLOW}te log list {TIMESTAMP_EXAMPLE}{RESET} 查看某次运行的全部日志")
    print(f"     {YELLOW}te sum LOG{RESET}             生成 L0torch 失败摘要")
    print(f"     {YELLOW}te build help{RESET}          查看全量构建命令")
    print(f"     {YELLOW}te rebuild help{RESET}        查看增量构建命令")
    print("")
    print(f"   {CYAN}子命令帮助:{RESET}")
    print(f"     {YELLOW}te run help{RESET}            查看测试运行帮助")
    print(f"     {YELLOW}te log help{RESET}            查看日志浏览帮助")
    print(f"     {YELLOW}te sum help{RESET}            查看摘要生成帮助")
    print("")
    print(f"   {CYAN}兼容入口（逐步退出）:{RESET}")
    print(f"     {YELLOW}te -0 -c{RESET} / {YELLOW}te -0 -t{RESET} / {YELLOW}te -1 -t{RESET}")
    print(f"     {YELLOW}te -b -c{RESET} / {YELLOW}te -b -t{RESET} / {YELLOW}te -b -r{RESET}")
    print(f"     {GREY}更多旧 flag 仅保留在 te help old 中的迁移说明，不建议继续使用。{RESET}")
    print("")
    print(f"   {CYAN}状态与通用选项:{RESET}")
    print(f"     {YELLOW}-p{RESET} 查看任务  {YELLOW}-s{RESET} 查看状态  {YELLOW}--check-env{RESET} 检查环境")
    print(f"     {YELLOW}-g, --gpu{RESET} 指定 GPU  {YELLOW}-v{RESET} 版本  {YELLOW}-V{RESET} 详细日志  {YELLOW}-h{RESET} 帮助")
    return 0


def print_legacy_help() -> int:
    """打印旧版根帮助信息。"""
    print(f"{GREEN}✅ TE 开发工具命令行 (TE CLI){RESET}")
    print(f"   {GREY}用法:{RESET} te [简化参数组合]")
    print("")
    print(f"   {CYAN}仍保留的旧兼容入口:{RESET}")
    print(f"     {YELLOW}-b -c{RESET}        等价于 te rebuild py")
    print(f"     {YELLOW}-b -t{RESET}        等价于 te rebuild cpp")
    print(f"     {YELLOW}-b -r{RESET}        等价于 te rebuild all")
    print("")
    print(f"   {CYAN}仍保留的旧测试入口:{RESET}")
    print(f"     {YELLOW}-0 -c{RESET}        等价于 te run l0cpp")
    print(f"     {YELLOW}-0 -t{RESET}        等价于 te run l0torch")
    print(f"     {YELLOW}-1 -t{RESET}        等价于 te run l1torch")
    print("")
    print(f"   {CYAN}迁移说明:{RESET}")
    print(f"     {GREY}旧 flag 的 -l / -k / -d 组合不再建议继续使用，请改用 te log / te build / te rebuild。{RESET}")
    print(f"     {GREY}例如: te log l0torch -n 1, te build py, te rebuild all{RESET}")
    return 0


def route_named_command(argv: List[str]) -> int:
    """路由 te 子命令。"""
    command = argv[0]
    sub_argv = argv[1:]

    if command == "help":
        if sub_argv and sub_argv[0] == "old":
            return print_legacy_help()
        return print_help()
    if command == "run":
        return route_run_command(sub_argv)
    if command == "log":
        return route_log_command(sub_argv)
    if command == "build":
        return route_build_named_command(sub_argv)
    if command == "rebuild":
        return route_rebuild_named_command(sub_argv)
    if command in {"sum", "summary"}:
        return route_summary_command(sub_argv)
    return print_help()


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
    
    # 资源管理
    parser.add_argument('-g', '--gpu', type=str, help='指定运行的 GPU (例如 "3" 或 "5,6")')
    
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
            return run_l0cpp(gpu=args.gpu)
        
        if args.test:  # PyTorch 测试
            if args.log:
                return view_log("l0torch")
            if args.kill:
                return kill_test_task("qa/L0_pytorch_unittest/test.sh", "L0 Torch Test")
            return run_l0torch(gpu=args.gpu)
    
    # L1 测试
    if args.l1 and args.test:
        if args.log:
            return view_log("l1torch")
        if args.kill:
            return kill_test_task("qa/L1_pytorch_distributed_unittest/test.sh", "L1 Torch Test")
        return run_l1torch(gpu=args.gpu)
    
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

    if _legacy_compat_error(args):
        return 1
    
    # 构建相关
    if args.build:
        return route_build_command(args)
    
    # 测试相关
    if args.l0 or args.l1:
        return route_test_command(args)
    
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
    
    # 快速检查根帮助
    if not argv:
        return print_help()

    # 检查详细日志模式
    verbose = '-V' in argv or '--verbose' in argv
    
    # 初始化配置和日志
    init_config(log_level='DEBUG' if verbose else 'INFO')
    setup_logging(level=logging.DEBUG if verbose else logging.INFO)
    
    logger.debug(f"命令行参数: {argv}")
    
    try:
        if argv[0] in {"help", "run", "log", "build", "rebuild", "sum", "summary"}:
            result = route_named_command(argv)
            logger.debug(f"命令执行结果: {result}")
            return result

        if '-h' in argv or '--help' in argv:
            return print_help()

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
