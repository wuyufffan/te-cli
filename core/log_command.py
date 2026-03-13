#!/usr/bin/env python3
"""te log 子命令。"""

import argparse
from typing import List

from .config import CYAN, GREEN, GREY, RED, RESET, YELLOW
from .config_manager import TEST_LOG_TYPES, TIMESTAMP_EXAMPLE, TIMESTAMP_PATTERN, get_config


def print_log_help() -> int:
    """打印 te log 帮助。"""
    print(f"{GREEN}✅ TE 日志导航命令{RESET}")
    print(f"   {GREY}用法:{RESET} te log [help|l0cpp|l0torch|l1torch|list [TIMESTAMP]] [-n N]")
    print("")
    print(f"   {CYAN}查看帮助:{RESET}")
    print(f"     {YELLOW}te log{RESET}                显示帮助")
    print(f"     {YELLOW}te log help{RESET}           显示帮助")
    print(f"     {YELLOW}te log watch{RESET}          预留中的运行日志观看入口")
    print("")
    print(f"   {CYAN}列出时间戳目录:{RESET}")
    print(f"     {YELLOW}te log list{RESET}           列出最近日志时间戳目录")
    print(f"     {YELLOW}te log list -n 10{RESET}     列出最近 10 个日志时间戳目录")
    print("")
    print(f"   {CYAN}按类型查看日志:{RESET}")
    print(f"     {YELLOW}te log l0cpp -n 5{RESET}      最近 5 条 L0 C++ 日志绝对路径")
    print(f"     {YELLOW}te log l0torch -n 5{RESET}    最近 5 条 L0 PyTorch 日志绝对路径")
    print(f"     {YELLOW}te log l1torch -n 5{RESET}    最近 5 条 L1 日志绝对路径")
    print("")
    print(f"   {CYAN}查看某次运行:{RESET}")
    print(f"     {YELLOW}te log list {TIMESTAMP_EXAMPLE}{RESET} 列出该时间戳目录下全部日志文件")
    print("")
    print(f"   {CYAN}兼容写法:{RESET}")
    print(f"     {GREY}te log {TIMESTAMP_EXAMPLE}{RESET}  与 te log list {TIMESTAMP_EXAMPLE} 等价")
    return 0


def _parse_log_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="te log", add_help=False)
    parser.add_argument("target", nargs="?")
    parser.add_argument("detail", nargs="?")
    parser.add_argument("-n", type=int, default=None)
    parser.add_argument("-h", "--help", action="store_true")
    return parser.parse_args(argv)


def route_log_command(argv: List[str]) -> int:
    """处理 te log 子命令。"""
    args = _parse_log_args(argv)
    config = get_config()

    if args.help or args.target in (None, "help") or args.detail == "help":
        return print_log_help()

    if args.target == "watch":
        print(f"{GREEN}✅ te log watch 入口已预留{RESET}")
        print(f"   {GREY}后续将自动检测正在运行的日志并引导选择观看对象。{RESET}")
        print(f"   {GREY}当前请先使用 te log list / te log l0torch -n 5 等命令。{RESET}")
        return 0

    if args.target == "list":
        if args.detail and TIMESTAMP_PATTERN.fullmatch(args.detail):
            log_paths = config.list_logs_in_timestamp(args.detail)
            if not log_paths:
                print(f"{GREY}时间戳目录下暂无日志文件: {args.detail}{RESET}")
                return 0
            for log_path in log_paths:
                print(log_path)
            return 0

        timestamps = config.list_log_timestamps(limit=args.n)
        if not timestamps:
            print(f"{GREY}暂无日志时间戳目录{RESET}")
            return 0
        for timestamp in timestamps:
            print(timestamp)
        return 0

    if args.target in TEST_LOG_TYPES:
        log_paths = config.list_logs_for_type(args.target, limit=args.n)
        if not log_paths:
            print(f"{GREY}暂无 {args.target} 日志{RESET}")
            return 0
        for log_path in log_paths:
            print(log_path)
        return 0

    if TIMESTAMP_PATTERN.fullmatch(args.target):
        log_paths = config.list_logs_in_timestamp(args.target)
        if not log_paths:
            print(f"{GREY}时间戳目录下暂无日志文件: {args.target}{RESET}")
            return 0
        for log_path in log_paths:
            print(log_path)
        return 0

    print(f"{RED}❌ 未知日志目标: {args.target}{RESET}")
    print(f"   {GREY}可选值: help, list, l0cpp, l0torch, l1torch, list {TIMESTAMP_EXAMPLE}{RESET}")
    return 1