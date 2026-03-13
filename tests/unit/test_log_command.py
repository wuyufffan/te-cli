#!/usr/bin/env python3
"""log_command 模块单元测试。"""

from pathlib import Path
from unittest.mock import patch

import core.log_command as log_command
from core.config_manager import Config


def test_log_list(capsys, tmp_path):
    cfg = Config(work_space=str(tmp_path))
    (tmp_path / "logs" / "20260312_110000").mkdir(parents=True)
    (tmp_path / "logs" / "20260312_120000").mkdir(parents=True)
    with patch("core.log_command.get_config", return_value=cfg):
        assert log_command.route_log_command(["list", "-n", "1"]) == 0
    out = capsys.readouterr().out
    assert "20260312_120000" in out
    assert "20260312_110000" not in out


def test_log_by_type(capsys, tmp_path):
    cfg = Config(work_space=str(tmp_path))
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0cpp"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_cppunittest_nmz76.log"
    log_file.write_text("hello", encoding="utf-8")
    with patch("core.log_command.get_config", return_value=cfg):
        assert log_command.route_log_command(["l0cpp", "-n", "5"]) == 0
    assert str(log_file.resolve()) in capsys.readouterr().out


def test_log_timestamp_detail(capsys, tmp_path):
    cfg = Config(work_space=str(tmp_path))
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text("hello", encoding="utf-8")
    with patch("core.log_command.get_config", return_value=cfg):
        assert log_command.route_log_command(["list", "20260312_120000"]) == 0
    assert str(log_file.resolve()) in capsys.readouterr().out


def test_log_timestamp_detail_supports_legacy_name(capsys, tmp_path):
    cfg = Config(work_space=str(tmp_path))
    log_dir = tmp_path / "logs" / "2026-03-12::12-00-00" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text("hello", encoding="utf-8")
    with patch("core.log_command.get_config", return_value=cfg):
        assert log_command.route_log_command(["2026-03-12::12-00-00"]) == 0
    assert str(log_file.resolve()) in capsys.readouterr().out


def test_log_help_alias(capsys):
    assert log_command.route_log_command(["help"]) == 0
    out = capsys.readouterr().out
    assert "te log help" in out
    assert "te log watch" in out
    assert "查看某次运行" in out
    assert "兼容写法" in out


def test_log_watch_placeholder(capsys):
    assert log_command.route_log_command(["watch"]) == 0
    out = capsys.readouterr().out
    assert "te log watch 入口已预留" in out
    assert "自动检测正在运行的日志" in out


def test_log_unknown_target():
    assert log_command.route_log_command(["unknown"]) == 1