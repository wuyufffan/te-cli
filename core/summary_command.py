#!/usr/bin/env python3
"""te sum 子命令。"""

import argparse
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set

from .config import CYAN, GREEN, GREY, RED, RESET, YELLOW
from .config_manager import TIMESTAMP_EXAMPLE


DEFAULT_TEST_SH = "/workspace/TransformerEngine/qa/L0_pytorch_unittest/test.sh"


def _normalize_log_test_path(path: str) -> str:
    return path.replace("TransformerEngine/", "", 1) if path.startswith("TransformerEngine/") else path


def _extract_filename_and_env(line: str):
    pattern = re.compile(
        r'^(?P<env>(?:[A-Z_]+=[^\s]+\s+)*)python3\s+-m\s+pytest\b.*?(?:/|\\)(?P<filename>test_\w+\.py)\b'
    )
    match = pattern.search(line.strip())
    if not match:
        return None
    return {
        "filename": match.group("filename"),
        "env_prefix": (match.group("env") or "").strip(),
    }


def parse_test_runs_from_test_sh(test_sh_path: str) -> List[Dict[str, str]]:
    runs: List[Dict[str, str]] = []
    try:
        with open(test_sh_path, "r", encoding="utf-8") as handle:
            for line in handle:
                parsed = _extract_filename_and_env(line)
                if parsed:
                    runs.append(parsed)
    except FileNotFoundError:
        print(f"{YELLOW}⚠ 找不到 test.sh，复现命令将不附加环境变量: {test_sh_path}{RESET}")
    return runs


def parse_log_runs(log_file_path: str) -> List[Dict[str, str]]:
    runs: List[Dict[str, str]] = []
    pending_env: List[str] = []
    pattern_env = re.compile(r"^\+\s+([A-Z_]+=[^\s]+)$")
    pattern_pytest = re.compile(
        r'^\+\s+python3\s+-m\s+pytest\b.*?(?:/|\\)(?P<path>(?:TransformerEngine/)?tests/[\w/-]+\.py)\b'
    )

    with open(log_file_path, "r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\n")
            env_match = pattern_env.match(line)
            if env_match:
                pending_env.append(env_match.group(1))
                continue

            pytest_match = pattern_pytest.match(line)
            if pytest_match:
                file_path = _normalize_log_test_path(pytest_match.group("path"))
                runs.append(
                    {
                        "line_number": str(line_number),
                        "file_path": file_path,
                        "filename": os.path.basename(file_path),
                        "env_prefix": " ".join(pending_env),
                    }
                )
                pending_env = []
                continue

            if line.startswith("+ "):
                pending_env = []
    return runs


def build_run_env_map(test_sh_runs: List[Dict[str, str]], log_runs: List[Dict[str, str]]) -> Dict[int, str]:
    runs_by_filename = defaultdict(list)
    for run in test_sh_runs:
        runs_by_filename[run["filename"]].append(run["env_prefix"])

    log_run_env_map: Dict[int, str] = {}
    used_count = defaultdict(int)
    for run in log_runs:
        filename = run["filename"]
        index = used_count[filename]
        env_candidates = runs_by_filename.get(filename, [])
        env_prefix = env_candidates[index] if index < len(env_candidates) else run["env_prefix"]
        log_run_env_map[int(run["line_number"])] = env_prefix
        used_count[filename] += 1
    return log_run_env_map


def _parse_summary_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="te sum", add_help=False)
    parser.add_argument("log_file", nargs="?")
    parser.add_argument("arg2", nargs="?")
    parser.add_argument("arg3", nargs="?")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)

    level = "l2"
    keyword = None
    extra_args = [value for value in (args.arg2, args.arg3) if value is not None]

    if len(extra_args) > 2:
        parser.error("too many arguments")

    if extra_args:
        if extra_args[0] in ("l1", "l2", "l3"):
            level = extra_args[0]
            if len(extra_args) == 2:
                keyword = extra_args[1]
        elif re.fullmatch(r"l\d+", extra_args[0]):
            parser.error(f"invalid choice: '{extra_args[0]}' (choose from 'l1', 'l2', 'l3')")
        else:
            keyword = extra_args[0]
            if len(extra_args) == 2:
                parser.error("keyword mode does not accept an extra argument")

    args.level = level
    args.keyword = keyword
    return args


def print_summary_help() -> int:
    """打印 te sum 帮助。"""
    print(f"{GREEN}✅ TE 日志汇总命令{RESET}")
    print(f"   {GREY}用法:{RESET} te sum <L0torch log abs path> [l1|l2|l3]")
    print(f"         te sum <L0torch log abs path> <keyword>")
    print("")
    print(f"   {CYAN}输入:{RESET}")
    print(f"     {YELLOW}te sum /workspace/logs/{TIMESTAMP_EXAMPLE}/l0torch/L0_pytorch_unittest_nmz76.log{RESET}")
    print("")
    print(f"   {CYAN}输出:{RESET}")
    print(f"     {YELLOW}/workspace/logs/{TIMESTAMP_EXAMPLE}/l0torch/L0torch_log_summary.md{RESET}")
    print("")
    print(f"   {CYAN}行为:{RESET}")
    print(f"     {YELLOW}按日志中的 pytest 实际运行顺序匹配 test.sh 环境变量{RESET}")
    print(f"     {YELLOW}默认 l2：输出一级标题、二级标题，不显示复现命令{RESET}")
    print(f"     {YELLOW}l1{RESET}                   只输出一级标题")
    print(f"     {YELLOW}l2{RESET}                   输出一级标题、二级标题，不显示复现命令")
    print(f"     {YELLOW}l3{RESET}                   输出完整内容，包含复现命令和三级参数用例标题")
    print(f"     {YELLOW}keyword{RESET}              精确匹配一级/二级/三级标题并裁剪输出")
    print(f"     {YELLOW}help{RESET}                 显示本帮助")
    print("")
    print(f"   {CYAN}最短示例:{RESET}")
    print(f"     {YELLOW}te sum /workspace/logs/{TIMESTAMP_EXAMPLE}/l0torch/L0_pytorch_unittest_nmz76.log{RESET}")
    print(f"     {YELLOW}te sum /workspace/logs/{TIMESTAMP_EXAMPLE}/l0torch/L0_pytorch_unittest_nmz76.log l1{RESET}")
    print(f"     {YELLOW}te sum /workspace/logs/{TIMESTAMP_EXAMPLE}/l0torch/L0_pytorch_unittest_nmz76.log test_sanity.py{RESET}")
    return 0


def _is_supported_l0torch_log(log_path: Path) -> bool:
    if not log_path.is_file():
        return False
    return log_path.parent.name == "l0torch" or log_path.name.startswith("L0_pytorch_unittest")


def _build_repro_command(base_test: str, env_prefix: str) -> str:
    if env_prefix:
        return f"{env_prefix} python3 -m pytest -v -s $TE_PATH/{base_test}"
    return f"python3 -m pytest -v -s $TE_PATH/{base_test}"


def _build_search_output_path(log_path: Path, keyword: str) -> Path:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", keyword).strip("._-") or "keyword"
    return log_path.parent / f"L0torch_log_summary_{sanitized}.md"


def _build_group_aliases(file_path: str, base_test: str) -> Set[str]:
    file_basename = os.path.basename(file_path)
    test_name = base_test.split("::")[-1]
    return {
        file_path,
        file_basename,
        base_test,
        f"{file_basename}::{test_name}",
        test_name,
    }


def _build_case_aliases(file_path: str, case: str) -> Set[str]:
    file_basename = os.path.basename(file_path)
    case_tail = case.split("::", 1)[-1] if "::" in case else case
    return {
        case,
        f"{file_basename}::{case_tail}",
        case_tail,
    }


def collect_summary_data(log_file_path: str, log_run_env_map: Dict[int, str]) -> List[Dict[str, object]]:
    grouped_tests = defaultdict(list)
    group_lookup = {}
    pattern_test = re.compile(r"(?:FAILED|ERROR).*?((?:TransformerEngine/)?tests/[\w/-]+\.py)::(?:\w+::)?(test_\w+)(?:\[(.*?)\])?")
    pattern_order = re.compile(r"Error in the following test cases:\s+(.*)")
    pattern_pytest = re.compile(
        r'^\+\s+python3\s+-m\s+pytest\b.*?(?:/|\\)(?P<path>(?:TransformerEngine/)?tests/[\w/-]+\.py)\b'
    )
    pattern_test_fail = re.compile(r'^\+\s+test_fail\s+(?P<failed_name>test_\w+\.py(?:_[\w]+)?)$')

    ordered_files_list: List[str] = []
    current_run_line = None
    current_run_file = None
    run_has_failure_details = set()

    def add_failure_entry(file_path: str, base_test: str, full_test: str, env_prefix: str) -> None:
        group_key = (file_path, base_test, env_prefix)
        if group_key not in group_lookup:
            group_lookup[group_key] = len(grouped_tests[file_path])
            grouped_tests[file_path].append(
                {
                    "base_test": base_test,
                    "env_prefix": env_prefix,
                    "failed_cases": set(),
                }
            )
        grouped_tests[file_path][group_lookup[group_key]]["failed_cases"].add(full_test)

    with open(log_file_path, "r", encoding="utf-8") as log_handle:
        for line_number, line in enumerate(log_handle, start=1):
            pytest_match = pattern_pytest.match(line)
            if pytest_match:
                current_run_line = line_number
                current_run_file = _normalize_log_test_path(pytest_match.group("path"))

            if "FAILED" in line or "ERROR" in line:
                match = pattern_test.search(line)
                if match:
                    file_path = _normalize_log_test_path(match.group(1))
                    test_func = match.group(2)
                    params = match.group(3)

                    base_test = f"{file_path}::{test_func}"
                    full_test = f"{base_test}[{params}]" if params else base_test
                    env_prefix = log_run_env_map.get(current_run_line, "")
                    add_failure_entry(file_path, base_test, full_test, env_prefix)
                    run_has_failure_details.add(current_run_line)

            test_fail_match = pattern_test_fail.match(line)
            if test_fail_match and current_run_line is not None and current_run_file is not None:
                if current_run_line not in run_has_failure_details:
                    env_prefix = log_run_env_map.get(current_run_line, "")
                    add_failure_entry(current_run_file, current_run_file, current_run_file, env_prefix)

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

    sorted_files = sorted(grouped_tests.keys(), key=get_sort_key)
    summary: List[Dict[str, object]] = []
    for file_path in sorted_files:
        groups = []
        for group in grouped_tests[file_path]:
            base_test = group["base_test"]
            env_prefix = group["env_prefix"]
            groups.append(
                {
                    "base_test": base_test,
                    "env_prefix": env_prefix,
                    "command": _build_repro_command(base_test, env_prefix),
                    "failed_cases": sorted(group["failed_cases"]),
                }
            )
        summary.append({"file_path": file_path, "groups": groups})
    return summary


def _filter_summary_data(summary_data: List[Dict[str, object]], keyword: Optional[str]) -> List[Dict[str, object]]:
    if not keyword:
        return summary_data

    filtered_summary = []
    for file_entry in summary_data:
        file_path = str(file_entry["file_path"])
        groups = file_entry["groups"]
        file_matches = file_path == keyword or os.path.basename(file_path) == keyword
        filtered_groups = []

        for group in groups:
            base_test = str(group["base_test"])
            failed_cases = list(group["failed_cases"])
            group_aliases = _build_group_aliases(file_path, base_test)
            second_level_matches = keyword in group_aliases
            matched_cases = [case for case in failed_cases if keyword in _build_case_aliases(file_path, case)]

            if file_matches:
                filtered_groups.append(
                    {
                        **group,
                        "matched_cases": [],
                        "render_mode": "group-only",
                        "match_level": "l1",
                        "matched_target": file_path,
                    }
                )
            elif second_level_matches:
                filtered_groups.append(
                    {
                        **group,
                        "matched_cases": failed_cases,
                        "render_mode": "group-with-cases",
                        "match_level": "l2",
                        "matched_target": base_test,
                    }
                )
            elif matched_cases:
                filtered_groups.append(
                    {
                        **group,
                        "matched_cases": matched_cases,
                        "render_mode": "group-with-cases",
                        "match_level": "l3",
                        "matched_target": matched_cases[0],
                    }
                )

        if filtered_groups:
            filtered_summary.append({"file_path": file_path, "groups": filtered_groups})

    return filtered_summary


def _summarize_keyword_matches(summary_data: List[Dict[str, object]]) -> Dict[str, object]:
    levels: Set[str] = set()
    targets: List[str] = []
    for file_entry in summary_data:
        for group in file_entry["groups"]:
            match_level = group.get("match_level")
            matched_target = group.get("matched_target")
            if match_level:
                levels.add(str(match_level))
            if matched_target and matched_target not in targets:
                targets.append(str(matched_target))
    return {
        "levels": sorted(levels, key=lambda item: (item != "l1", item != "l2", item != "l3", item)),
        "targets": targets,
    }


def generate_markdown_report(output_md_path: str, summary_data: List[Dict[str, object]], level: str, keyword: Optional[str]) -> None:
    with open(output_md_path, "w", encoding="utf-8") as output_handle:
        output_handle.write("# 失败测试用例汇总报告\n\n")
        for file_index, file_entry in enumerate(summary_data, start=1):
            file_path = str(file_entry["file_path"])
            groups = file_entry["groups"]
            output_handle.write(f"# {file_index}. {file_path}\n\n")
            if level == "l1":
                continue
            for test_index, group in enumerate(groups, start=1):
                base_test = group["base_test"]
                output_handle.write(f"## {file_index}.{test_index} {base_test}\n\n")
                render_mode = group.get("render_mode", "full")
                if keyword is None and level == "l2":
                    continue
                if render_mode == "group-only":
                    output_handle.write("**复现命令**:\n")
                    output_handle.write(f"```python\n{group['command']}\n```\n\n")
                    continue
                output_handle.write("**复现命令**:\n")
                output_handle.write(f"```python\n{group['command']}\n```\n\n")
                cases_to_render = group.get("matched_cases", group["failed_cases"])
                for case_index, case in enumerate(cases_to_render, start=1):
                    output_handle.write(f"### {file_index}.{test_index}.{case_index} {case}\n")
                output_handle.write("\n")


def route_summary_command(argv: List[str]) -> int:
    """处理 te sum 子命令。"""
    args = _parse_summary_args(argv)
    if args.help or args.log_file == "help" or not args.log_file:
        return print_summary_help()

    log_path = Path(args.log_file).expanduser()
    if not _is_supported_l0torch_log(log_path):
        print(f"{RED}❌ 当前只支持 l0torch 日志: {log_path}{RESET}")
        return 1

    output_path = log_path.parent / "L0torch_log_summary.md"
    test_sh_runs = parse_test_runs_from_test_sh(DEFAULT_TEST_SH)
    log_runs = parse_log_runs(str(log_path))
    log_run_env_map = build_run_env_map(test_sh_runs, log_runs)
    summary_data = collect_summary_data(str(log_path), log_run_env_map)
    filtered_summary = _filter_summary_data(summary_data, args.keyword)
    if args.keyword and not filtered_summary:
        print(f"{RED}❌ 未匹配到关键词: {args.keyword}{RESET}")
        return 1

    if args.keyword:
        args.level = "l3"
        output_path = _build_search_output_path(log_path, args.keyword)

    generate_markdown_report(str(output_path), filtered_summary, args.level, args.keyword)
    print(f"{GREEN}✅ Summary 已生成{RESET}")
    print(f"   {GREY}└─ Output:{RESET} {output_path}")
    if args.keyword:
        match_summary = _summarize_keyword_matches(filtered_summary)
        levels = ", ".join(match_summary["levels"])
        targets = " | ".join(match_summary["targets"][:3])
        if len(match_summary["targets"]) > 3:
            targets = f"{targets} | ..."
        print(f"   {GREY}└─ Search:{RESET} {args.keyword}")
        print(f"   {GREY}└─ Match:{RESET} {levels}")
        print(f"   {GREY}└─ Expand:{RESET} {targets}")
    else:
        print(f"   {GREY}└─ Level:{RESET} {args.level}")
    return 0