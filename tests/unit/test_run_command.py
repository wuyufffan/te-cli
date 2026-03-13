#!/usr/bin/env python3
"""run_command 模块单元测试。"""

from unittest.mock import MagicMock, patch

import pytest

import core.run_command as run_command


@pytest.fixture
def mock_runners():
    original_runners = dict(run_command.RUNNERS)
    mocks = {
        "run_l0cpp": MagicMock(return_value=0),
        "run_l0torch": MagicMock(return_value=0),
        "run_l1torch": MagicMock(return_value=0),
    }
    with patch.multiple(run_command, **mocks):
        run_command.RUNNERS.update(
            {
                "l0cpp": run_command.run_l0cpp,
                "l0torch": run_command.run_l0torch,
                "l1torch": run_command.run_l1torch,
            }
        )
        yield mocks
    run_command.RUNNERS.clear()
    run_command.RUNNERS.update(original_runners)


def test_route_single_target(mock_runners):
    assert run_command.route_run_command(["l0cpp"]) == 0
    mock_runners["run_l0cpp"].assert_called_once_with(gpu=None)


def test_route_all_targets(mock_runners):
    assert run_command.route_run_command(["all"]) == 0
    mock_runners["run_l0cpp"].assert_called_once_with(gpu=None)
    mock_runners["run_l0torch"].assert_called_once_with(gpu=None)
    mock_runners["run_l1torch"].assert_called_once_with(gpu=None)


def test_route_single_target_with_gpu(mock_runners):
    assert run_command.route_run_command(["l0torch", "-g", "3"]) == 0
    mock_runners["run_l0torch"].assert_called_once_with(gpu="3")


def test_interactive_selection(mock_runners):
    with patch("builtins.input", return_value="1,3"):
        assert run_command.route_run_command([]) == 0
    mock_runners["run_l0cpp"].assert_called_once_with(gpu=None)
    mock_runners["run_l1torch"].assert_called_once_with(gpu=None)
    mock_runners["run_l0torch"].assert_not_called()


def test_interactive_invalid_selection(mock_runners):
    with patch("builtins.input", return_value="9"):
        assert run_command.route_run_command([]) == 1


def test_unknown_target(mock_runners):
    assert run_command.route_run_command(["unknown"]) == 1


def test_run_help_sections(capsys):
    assert run_command.print_run_help() == 0
    out = capsys.readouterr().out
    assert "单项运行" in out
    assert "批量运行" in out
    assert "交互选择" in out
    assert "兼容入口" in out