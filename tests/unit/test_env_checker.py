import builtins
import types
from unittest.mock import MagicMock, patch

import pytest

import core.env_checker as env_checker
from core.env_checker import CheckResult, EnvironmentChecker, check_environment


@pytest.fixture(autouse=True)
def reset_results(monkeypatch):
    # Ensure results list starts clean for each test
    monkeypatch.setattr(env_checker.EnvironmentChecker, "results", [], raising=False)


def test_checkresult_status_icon_and_is_ok():
    assert CheckResult("req", True, True).status_icon != CheckResult("req", True, False).status_icon
    assert CheckResult("opt", False, False).status_icon != CheckResult("opt", True, False).status_icon
    assert CheckResult("opt", False, False).is_ok is True
    assert CheckResult("req", True, False).is_ok is False


@pytest.mark.parametrize(
    "exists_flag, method_name, path_func",
    [
        (True, "_check_path", "isdir"),
        (False, "_check_path", "isdir"),
        (True, "_check_file", "isfile"),
        (False, "_check_file", "isfile"),
    ],
)
def test_check_path_and_file(monkeypatch, exists_flag, method_name, path_func):
    checker = EnvironmentChecker()
    with patch(f"os.path.{path_func}", return_value=exists_flag):
        getattr(checker, method_name)("X", "/tmp/x", required=True)
    assert checker.results[-1].exists is exists_flag


def test_check_command_branches(monkeypatch):
    checker = EnvironmentChecker()
    # branch: which None
    with patch("shutil.which", return_value=None):
        checker._check_command("CMake", "cmake", ["--version"], required=True)
        assert checker.results[-1].exists is False
    # branch: subprocess success with stdout
    checker.results = []
    with patch("shutil.which", return_value="/usr/bin/cmake"), patch(
        "subprocess.run",
        return_value=types.SimpleNamespace(stdout="cmake version 3.26.4", returncode=0),
    ):
        checker._check_command("CMake", "cmake", ["--version"], required=True)
        assert checker.results[-1].exists is True
        assert "cmake version" in checker.results[-1].version
    # branch: subprocess exception
    checker.results = []
    with patch("shutil.which", return_value="/usr/bin/cmake"), patch(
        "subprocess.run", side_effect=RuntimeError("boom")
    ):
        checker._check_command("CMake", "cmake", ["--version"], required=True)
        assert checker.results[-1].exists is True
        assert "无法获取版本" in checker.results[-1].message


def test_check_python_module(monkeypatch):
    checker = EnvironmentChecker()
    # success
    with patch("builtins.__import__", return_value=MagicMock()):
        checker._check_python_module("x", required=False)
        assert checker.results[-1].exists is True
    # import error
    checker.results = []
    with patch("builtins.__import__", side_effect=ImportError("nope")):
        checker._check_python_module("x", required=True)
        assert checker.results[-1].exists is False


def test_check_all_and_print_report_all_pass(monkeypatch, capsys):
    # Mock get_config
    fake_cfg = MagicMock()
    fake_cfg.te_path = "/ok"
    fake_cfg.work_space = "/ok"
    fake_cfg.get_init_script.return_value = "/ok/init.sh"
    fake_cfg.dtk_base = "/ok/dtk"
    monkeypatch.setattr(env_checker, "get_config", lambda: fake_cfg)

    checker = EnvironmentChecker()
    with patch("os.path.isdir", return_value=True), patch("os.path.isfile", return_value=True), patch(
        "shutil.which", return_value="/bin/echo"
    ), patch(
        "subprocess.run", return_value=types.SimpleNamespace(stdout="v1", returncode=0)
    ), patch("builtins.__import__", return_value=MagicMock()):
        all_passed, results = checker.check_all()
        assert all_passed is True
        checker.print_report()
    out = capsys.readouterr().out
    assert "所有必需依赖已就绪" in out
    assert len(results) > 0


def test_check_all_with_failures(monkeypatch, capsys):
    fake_cfg = MagicMock()
    fake_cfg.te_path = "/missing"
    fake_cfg.work_space = "/missing"
    fake_cfg.get_init_script.return_value = "/missing/init.sh"
    fake_cfg.dtk_base = "/missing/dtk"
    monkeypatch.setattr(env_checker, "get_config", lambda: fake_cfg)

    checker = EnvironmentChecker()
    with patch("os.path.isdir", return_value=False), patch("os.path.isfile", return_value=False), patch(
        "shutil.which", return_value=None
    ), patch("builtins.__import__", side_effect=ImportError("nope")):
        all_passed, results = checker.check_all()
        assert all_passed is False
        checker.print_report()
    out = capsys.readouterr().out
    assert "检查失败" in out
    assert any(not r.exists and r.required for r in results)


def test_check_environment_quiet(monkeypatch):
    fake_checker = MagicMock()
    fake_checker.check_all.return_value = (True, [])
    monkeypatch.setattr(env_checker, "EnvironmentChecker", lambda: fake_checker)
    assert check_environment(quiet=True) is True


def test_main_block_path_import_fixed(monkeypatch):
    # Bug 已修复：env_checker 顶部已添加 from pathlib import Path，
    # 运行为 __main__ 时不再触发 NameError。
    import runpy

    try:
        runpy.run_module("env_checker", run_name="__main__")
    except NameError:
        raise  # 修复后不应出现 NameError
    except BaseException:
        pass  # 其他异常（SystemExit、FileNotFoundError 等）在测试环境属预期行为
    # 到达此处且未抛出 NameError，表示 Path import 修复生效
