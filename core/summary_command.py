#!/usr/bin/env python3
"""te summary 子命令。"""

import argparse
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, List, Set

from .config import CYAN, GREEN, GREY, RED, RESET, YELLOW
from .config_manager import TIMESTAMP_EXAMPLE


def _parse_summary_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="te summary", add_help=False)
    parser.add_argument("log_file", nargs="?")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--brief", action="store_true")
    group.add_argument("--detailed", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    return parser.parse_args(argv)


def print_summary_help() -> int:
    """打印 te summary 帮助。"""
    print(f"{GREEN}✅ TE 日志汇总命令{RESET}")
    print(f"   {GREY}用法:{RESET} te summary <L0torch log abs path> [--brief|--detailed]")
    print("")
    print(f"   {CYAN}输入:{RESET}")
    print(f"     {YELLOW}te summary /workspace/logs/{TIMESTAMP_EXAMPLE}/l0torch/L0_pytorch_unittest_nmz76.log{RESET}")
    print("")
    print(f"   {CYAN}输出:{RESET}")
    print(f"     {YELLOW}/workspace/logs/{TIMESTAMP_EXAMPLE}/l0torch/L0torch_log_summary.md{RESET}")
    print("")
    print(f"   {CYAN}模式:{RESET}")
    print(f"     {YELLOW}--brief{RESET}              默认模式，只输出到二级标题")
    print(f"     {YELLOW}--detailed{RESET}           输出三级参数用例标题")
    print("")
    print(f"   {CYAN}最短示例:{RESET}")
    print(f"     {YELLOW}te summary /workspace/logs/{TIMESTAMP_EXAMPLE}/l0torch/L0_pytorch_unittest_nmz76.log{RESET}")
    return 0


def _is_supported_l0torch_log(log_path: Path) -> bool:
    return log_path.is_file() and log_path.parent.name == "l0torch"


def generate_markdown_report(log_file_path: str, output_md_path: str, is_brief: bool) -> None:
    """复用 summary.py 的核心解析逻辑。"""
    test_hierarchy: DefaultDict[str, DefaultDict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
    pattern_test = re.compile(r"(?:FAILED|ERROR).*?(tests/[\w/-]+\.py)::(test_\w+)(?:\[(.*?)\])?")
    pattern_order = re.compile(r"Error in the following test cases:\s+(.*)")

    ordered_files_list: List[str] = []

    with open(log_file_path, "r", encoding="utf-8") as log_handle:
        for line in log_handle:
            if "FAILED" in line or "ERROR" in line:
                match = pattern_test.search(line)
                if match:
                    file_path = match.group(1)
                    test_func = match.group(2)
                    params = match.group(3)

                    base_test = f"{file_path}::{test_func}"
                    full_test = f"{base_test}[{params}]" if params else base_test
                    test_hierarchy[file_path][base_test].add(full_test)

            order_match = pattern_order.search(line)
            if order_match:
                files_str = order_match.group(1).replace("'", "").strip()
                ordered_files_list = files_str.split()

    def get_sort_key(file_path: str) -> float:
        file_name = os.path.basename(file_path)
        try:
            return float(ordered_files_list.index(file_name))
        except ValueError:
            return float("inf")

    sorted_files = sorted(test_hierarchy.keys(), key=get_sort_key)
    with open(output_md_path, "w", encoding="utf-8") as output_handle:
        output_handle.write("# 失败测试用例汇总报告\n\n")
        for file_path in sorted_files:
            output_handle.write(f"# {file_path}\n\n")
            for base_test in sorted(test_hierarchy[file_path].keys()):
                output_handle.write(f"## {base_test}\n\n")
                output_handle.write("**复现命令**:\n")
                output_handle.write(f"```python\npython3 -m pytest -v -s $TE_PATH/{base_test}\n```\n\n")
                if not is_brief:
                    for case in sorted(test_hierarchy[file_path][base_test]):
                        output_handle.write(f"### {case}\n")
                    output_handle.write("\n")


def route_summary_command(argv: List[str]) -> int:
    """处理 te summary 子命令。"""
    args = _parse_summary_args(argv)
    if args.help or not args.log_file:
        return print_summary_help()

    log_path = Path(args.log_file).expanduser()
    if not _is_supported_l0torch_log(log_path):
        print(f"{RED}❌ 当前只支持 l0torch 日志: {log_path}{RESET}")
        return 1

    output_path = log_path.parent / "L0torch_log_summary.md"
    is_brief_mode = not args.detailed
    generate_markdown_report(str(log_path), str(output_path), is_brief_mode)
    print(f"{GREEN}✅ Summary 已生成{RESET}")
    print(f"   {GREY}└─ Output:{RESET} {output_path}")
    print(f"   {GREY}└─ Mode:{RESET} {'brief' if is_brief_mode else 'detailed'}")
    return 0