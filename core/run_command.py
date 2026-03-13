#!/usr/bin/env python3
"""te run 子命令。"""

import argparse
from typing import Callable, Dict, List, Optional

from .config import CYAN, GREEN, GREY, RED, RESET, YELLOW
from .test_helpers import run_l0cpp, run_l0torch, run_l1torch

RUNNERS: Dict[str, Callable[..., int]] = {
    "l0cpp": run_l0cpp,
    "l0torch": run_l0torch,
    "l1torch": run_l1torch,
}

RUN_LABELS = {
    "l0cpp": "L0 C++ 单元测试",
    "l0torch": "L0 PyTorch 单元测试",
    "l1torch": "L1 PyTorch 分布式测试",
}


def print_run_help() -> int:
    """打印 te run 帮助。"""
    print(f"{GREEN}✅ TE 测试运行命令{RESET}")
    print(f"   {GREY}用法:{RESET} te run [l0cpp|l0torch|l1torch|all] [-g GPU]")
    print("")
    print(f"   {CYAN}单项运行:{RESET}")
    print(f"     {YELLOW}te run l0cpp{RESET}        运行 L0 C++ 单元测试")
    print(f"     {YELLOW}te run l0torch{RESET}      运行 L0 PyTorch 单元测试")
    print(f"     {YELLOW}te run l1torch{RESET}      运行 L1 PyTorch 分布式测试")
    print("")
    print(f"   {CYAN}批量运行:{RESET}")
    print(f"     {YELLOW}te run all{RESET}          依次启动全部三个测试")
    print("")
    print(f"   {CYAN}交互选择:{RESET}")
    print(f"     {YELLOW}te run{RESET}              列出测试并交互选择")
    print("")
    print(f"   {CYAN}GPU 绑定:{RESET}")
    print(f"     {YELLOW}te run l0torch -g 3{RESET}   指定 GPU 运行")
    print("")
    print(f"   {CYAN}兼容入口:{RESET}")
    print(f"     {YELLOW}te -0 -c{RESET}            等价于 te run l0cpp")
    print(f"     {YELLOW}te -0 -t{RESET}            等价于 te run l0torch")
    print(f"     {YELLOW}te -1 -t{RESET}            等价于 te run l1torch")
    return 0


def _parse_run_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="te run", add_help=False)
    parser.add_argument("target", nargs="?")
    parser.add_argument("-g", "--gpu", type=str)
    parser.add_argument("-h", "--help", action="store_true")
    return parser.parse_args(argv)


def _run_targets(targets: List[str], gpu: Optional[str] = None) -> int:
    status = 0
    for target in targets:
        result = RUNNERS[target](gpu=gpu)
        if result != 0:
            status = result
    return status


def _parse_selection(raw: str) -> Optional[List[str]]:
    raw = raw.strip().lower()
    if not raw:
        return None
    if raw == "all":
        return list(RUNNERS.keys())

    index_map = {"1": "l0cpp", "2": "l0torch", "3": "l1torch"}
    selected: List[str] = []
    for part in [item.strip() for item in raw.split(",") if item.strip()]:
        target = index_map.get(part)
        if target is None:
            return None
        if target not in selected:
            selected.append(target)
    return selected or None


def _interactive_run(gpu: Optional[str] = None) -> int:
    print(f"{GREEN}可用测试:{RESET}")
    print(f"  {YELLOW}1){RESET} l0cpp    {GREY}- {RUN_LABELS['l0cpp']}{RESET}")
    print(f"  {YELLOW}2){RESET} l0torch  {GREY}- {RUN_LABELS['l0torch']}{RESET}")
    print(f"  {YELLOW}3){RESET} l1torch  {GREY}- {RUN_LABELS['l1torch']}{RESET}")
    try:
        choice = input("请选择要运行的测试 (例如 1,3 或 all): ")
    except EOFError:
        print(f"{RED}❌ 未收到有效选择{RESET}")
        return 1

    selected = _parse_selection(choice)
    if not selected:
        print(f"{RED}❌ 无效选择，请输入 1,2,3 或 all{RESET}")
        return 1
    return _run_targets(selected, gpu=gpu)


def route_run_command(argv: List[str]) -> int:
    """处理 te run 子命令。"""
    args = _parse_run_args(argv)

    if args.help or args.target == "help":
        return print_run_help()
    if not args.target:
        return _interactive_run(gpu=args.gpu)
    if args.target == "all":
        return _run_targets(list(RUNNERS.keys()), gpu=args.gpu)
    if args.target in RUNNERS:
        return RUNNERS[args.target](gpu=args.gpu)

    print(f"{RED}❌ 未知测试目标: {args.target}{RESET}")
    print(f"   {GREY}可选值: l0cpp, l0torch, l1torch, all{RESET}")
    return 1