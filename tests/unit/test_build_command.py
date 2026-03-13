#!/usr/bin/env python3
"""build_command 模块单元测试。"""

from unittest.mock import patch

import core.build_command as build_command


def test_build_py_calls_full_python_build():
    with patch("core.build_command.build_te_func", return_value=0) as mock_func:
        assert build_command.route_build_named_command(["py"]) == 0
    mock_func.assert_called_once_with()


def test_rebuild_py_calls_incremental_python_build():
    with patch("core.build_command.build_te_func_incremental", return_value=0) as mock_func:
        assert build_command.route_rebuild_named_command(["py"]) == 0
    mock_func.assert_called_once_with()


def test_build_cpp_calls_clean_then_build():
    with patch("core.build_command.build_clean_cpp", return_value=0) as mock_clean, patch(
        "core.build_command.build_cpp_test_func", return_value=0
    ) as mock_build:
        assert build_command.route_build_named_command(["cpp"]) == 0
    mock_clean.assert_called_once_with()
    mock_build.assert_called_once_with()


def test_rebuild_cpp_calls_incremental_cpp_build():
    with patch("core.build_command.build_cpp_test_func", return_value=0) as mock_build:
        assert build_command.route_rebuild_named_command(["cpp"]) == 0
    mock_build.assert_called_once_with()


def test_build_all_calls_full_build():
    with patch("core.build_command.build_all_func", return_value=0) as mock_func:
        assert build_command.route_build_named_command(["all"]) == 0
    mock_func.assert_called_once_with()


def test_rebuild_all_calls_incremental_rebuild():
    with patch("core.build_command.rebuild_dev", return_value=0) as mock_func:
        assert build_command.route_rebuild_named_command(["all"]) == 0
    mock_func.assert_called_once_with()


def test_build_help_output(capsys):
    assert build_command.print_build_help() == 0
    out = capsys.readouterr().out
    assert "te build [help|py|cpp|all]" in out
    assert "te -b -c -d" in out


def test_rebuild_help_output(capsys):
    assert build_command.print_rebuild_help() == 0
    out = capsys.readouterr().out
    assert "te rebuild [help|py|cpp|all]" in out
    assert "te -b -c" in out