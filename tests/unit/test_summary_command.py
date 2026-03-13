#!/usr/bin/env python3
"""summary_command 模块单元测试。"""

from pathlib import Path

import core.summary_command as summary_command
from core.config_manager import TIMESTAMP_EXAMPLE


def test_summary_generates_markdown(tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        "FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path\n"
        "Error in the following test cases: test_sanity.py\n",
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file)]) == 0
    output_file = log_dir / "L0torch_log_summary.md"
    assert output_file.is_file()
    content = output_file.read_text(encoding="utf-8")
    assert "# 失败测试用例汇总报告" in content
    assert "test_sanity_drop_path" in content


def test_summary_rejects_non_l0torch_log(tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l1torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L1_pytorch_distributed_unittest_nmz76.log"
    log_file.write_text("FAILED foo\n", encoding="utf-8")
    assert summary_command.route_summary_command([str(log_file)]) == 1


def test_summary_help_shows_new_timestamp_example(capsys):
    assert summary_command.print_summary_help() == 0
    out = capsys.readouterr().out
    assert TIMESTAMP_EXAMPLE in out
    assert "输入:" in out
    assert "输出:" in out
    assert "模式:" in out


def test_summary_detailed_mode_reports_mode(capsys, tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        "FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path[param]\n"
        "Error in the following test cases: test_sanity.py\n",
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "--detailed"]) == 0
    out = capsys.readouterr().out
    assert "Mode:" in out
    assert "detailed" in out
    content = (log_dir / "L0torch_log_summary.md").read_text(encoding="utf-8")
    assert "### tests/pytorch/test_sanity.py::test_sanity_drop_path[param]" in content