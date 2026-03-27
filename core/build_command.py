#!/usr/bin/env python3
"""te build / te rebuild 子命令。"""

import argparse
from typing import List

from .build_helpers import (
    build_all_func,
    build_clean_cpp,
    build_cpp_test_func,
    build_te_func,
    build_te_func_incremental,
    rebuild_dev,
)
from .config import CYAN, GREEN, GREY, RED, RESET, YELLOW


def print_build_help() -> int:
    """打印 te build 帮助。"""
    print(f"{GREEN}✅ TE 全量构建命令{RESET}")
    print(f"   {GREY}用法:{RESET} te build [help|py|cpp|all]")
    print("")
    print(f"   {CYAN}可用目标:{RESET}")
    print(f"     {YELLOW}te build py{RESET}           全量构建 Python")
    print(f"     {YELLOW}te build cpp{RESET}          清理后全量构建 C++ 测试")
    print(f"     {YELLOW}te build all{RESET}          全量构建 Python + C++")
    print("")
    print(f"   {CYAN}说明:{RESET}")
    print(f"     {GREY}增量构建请使用 te rebuild ...{RESET}")
    print(f"     {GREY}旧 flag 兼容层仅保留 te -b -c / te -b -t / te -b -r 三条增量入口。{RESET}")
    return 0


def print_rebuild_help() -> int:
    """打印 te rebuild 帮助。"""
    print(f"{GREEN}✅ TE 增量构建命令{RESET}")
    print(f"   {GREY}用法:{RESET} te rebuild [help|py|cpp|all]")
    print("")
    print(f"   {CYAN}可用目标:{RESET}")
    print(f"     {YELLOW}te rebuild py{RESET}        增量构建 Python")
    print(f"     {YELLOW}te rebuild cpp{RESET}       增量构建 C++ 测试")
    print(f"     {YELLOW}te rebuild all{RESET}       增量重建 Python + C++")
    print("")
    print(f"   {CYAN}兼容映射:{RESET}")
    print(f"     {GREY}te -b -c{RESET}               等价于 te rebuild py")
    print(f"     {GREY}te -b -t{RESET}               等价于 te rebuild cpp")
    print(f"     {GREY}te -b -r{RESET}               等价于 te rebuild all")
    print("")
    print(f"   {CYAN}说明:{RESET}")
    print(f"     {GREY}全量构建请使用 te build ...{RESET}")
    print(f"     {GREY}旧 flag 的 -d / -l / -k 组合已收缩，不再作为正式接口。{RESET}")
    return 0


def _parse_build_args(prog_name: str, argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=prog_name, add_help=False)
    parser.add_argument("target", nargs="?")
    parser.add_argument("-h", "--help", action="store_true")
    return parser.parse_args(argv)


def route_build_named_command(argv: List[str]) -> int:
    """处理 te build 子命令。"""
    args = _parse_build_args("te build", argv)

    if args.help or args.target in (None, "help"):
        return print_build_help()
    if args.target == "py":
        return build_te_func()
    if args.target == "cpp":
        status = build_clean_cpp()
        if status != 0:
            return status
        return build_cpp_test_func()
    if args.target == "all":
        return build_all_func()

    print(f"{RED}❌ 未知构建目标: {args.target}{RESET}")
    print(f"   {GREY}可选值: help, py, cpp, all{RESET}")
    return 1


def route_rebuild_named_command(argv: List[str]) -> int:
    """处理 te rebuild 子命令。"""
    args = _parse_build_args("te rebuild", argv)

    if args.help or args.target in (None, "help"):
        return print_rebuild_help()
    if args.target == "py":
        return build_te_func_incremental()
    if args.target == "cpp":
        return build_cpp_test_func()
    if args.target == "all":
        return rebuild_dev()

    print(f"{RED}❌ 未知增量构建目标: {args.target}{RESET}")
    print(f"   {GREY}可选值: help, py, cpp, all{RESET}")
    return 1