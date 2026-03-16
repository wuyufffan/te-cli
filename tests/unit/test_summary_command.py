#!/usr/bin/env python3
"""summary_command 模块单元测试。"""

import textwrap
from pathlib import Path

import core.summary_command as summary_command
from core.config_manager import TIMESTAMP_EXAMPLE


def test_summary_generates_markdown(tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        "+ python3 -m pytest -v -s --junitxml=/logs/pytest_test_sanity.xml /workspace/TransformerEngine/tests/pytorch/test_sanity.py\n"
        "FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path\n"
        "Error in the following test cases: test_sanity.py\n",
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file)]) == 0
    output_file = log_dir / "L0torch_log_summary.md"
    assert output_file.is_file()
    content = output_file.read_text(encoding="utf-8")
    assert "# 失败测试用例汇总报告" in content
    assert "# 1. tests/pytorch/test_sanity.py" in content
    assert "## 1.1 tests/pytorch/test_sanity.py::test_sanity_drop_path" in content
    assert "test_sanity_drop_path" in content


def test_summary_rejects_non_l0torch_log(tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l1torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L1_pytorch_distributed_unittest_nmz76.log"
    log_file.write_text("FAILED foo\n", encoding="utf-8")
    assert summary_command.route_summary_command([str(log_file)]) == 1


def test_summary_accepts_l0_prefix_log_outside_l0torch_dir(tmp_path):
    log_file = tmp_path / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        "+ python3 -m pytest -v -s --junitxml=/logs/pytest_test_sanity.xml /workspace/TransformerEngine/tests/pytorch/test_sanity.py\n"
        "FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path\n"
        "Error in the following test cases: test_sanity.py\n",
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file)]) == 0
    output_file = tmp_path / "L0torch_log_summary.md"
    assert output_file.is_file()


def test_summary_help_shows_new_timestamp_example(capsys):
    assert summary_command.print_summary_help() == 0
    out = capsys.readouterr().out
    assert TIMESTAMP_EXAMPLE in out
    assert "输入:" in out
    assert "输出:" in out
    assert "行为:" in out
    assert "l1" in out
    assert "l2" in out
    assert "l3" in out
    assert "keyword" in out
    assert "te sum " in out


def test_summary_help_subcommand_shows_help(capsys):
    assert summary_command.route_summary_command(["help"]) == 0
    out = capsys.readouterr().out
    assert "te sum " in out
    assert "显示本帮助" in out


def test_summary_is_always_detailed(capsys, tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        "+ python3 -m pytest -v -s --junitxml=/logs/pytest_test_sanity.xml /workspace/TransformerEngine/tests/pytorch/test_sanity.py\n"
        "FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path[param]\n"
        "Error in the following test cases: test_sanity.py\n",
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "l3"]) == 0
    out = capsys.readouterr().out
    assert "Level:" in out
    assert "l3" in out
    content = (log_dir / "L0torch_log_summary.md").read_text(encoding="utf-8")
    assert "### 1.1.1 tests/pytorch/test_sanity.py::test_sanity_drop_path[param]" in content


def test_summary_defaults_to_l2(tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        "+ python3 -m pytest -v -s --junitxml=/logs/pytest_test_sanity.xml /workspace/TransformerEngine/tests/pytorch/test_sanity.py\n"
        "FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path[param]\n"
        "Error in the following test cases: test_sanity.py\n",
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file)]) == 0
    content = (log_dir / "L0torch_log_summary.md").read_text(encoding="utf-8")
    assert "# 1. tests/pytorch/test_sanity.py" in content
    assert "## 1.1 tests/pytorch/test_sanity.py::test_sanity_drop_path" in content
    assert "**复现命令**:" not in content
    assert "### 1.1.1" not in content


def test_summary_l1_outputs_only_top_level_headers(tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        "+ python3 -m pytest -v -s --junitxml=/logs/pytest_test_sanity.xml /workspace/TransformerEngine/tests/pytorch/test_sanity.py\n"
        "FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path[param]\n"
        "Error in the following test cases: test_sanity.py\n",
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "l1"]) == 0
    content = (log_dir / "L0torch_log_summary.md").read_text(encoding="utf-8")
    assert "# 1. tests/pytorch/test_sanity.py" in content
    assert "## 1.1 tests/pytorch/test_sanity.py::test_sanity_drop_path" not in content
    assert "**复现命令**:" not in content
    assert "### 1.1.1" not in content


def test_summary_l2_outputs_headers_without_commands(tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        "+ python3 -m pytest -v -s --junitxml=/logs/pytest_test_sanity.xml /workspace/TransformerEngine/tests/pytorch/test_sanity.py\n"
        "FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path[param]\n"
        "Error in the following test cases: test_sanity.py\n",
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "l2"]) == 0
    content = (log_dir / "L0torch_log_summary.md").read_text(encoding="utf-8")
    assert "## 1.1 tests/pytorch/test_sanity.py::test_sanity_drop_path" in content
    assert "**复现命令**:" not in content
    assert "### 1.1.1" not in content


def test_summary_l3_outputs_commands_and_third_level(tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        "+ python3 -m pytest -v -s --junitxml=/logs/pytest_test_sanity.xml /workspace/TransformerEngine/tests/pytorch/test_sanity.py\n"
        "FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path[param]\n"
        "Error in the following test cases: test_sanity.py\n",
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "l3"]) == 0
    content = (log_dir / "L0torch_log_summary.md").read_text(encoding="utf-8")
    assert "## 1.1 tests/pytorch/test_sanity.py::test_sanity_drop_path" in content
    assert "**复现命令**:" in content
    assert "### 1.1.1 tests/pytorch/test_sanity.py::test_sanity_drop_path[param]" in content


def test_summary_invalid_level_returns_parse_error():
    try:
        summary_command.route_summary_command(["/tmp/foo.log", "l4"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("invalid level should raise SystemExit(2)")


def test_summary_keyword_matches_top_level_file_and_keeps_group_commands(tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        "+ python3 -m pytest -v -s --junitxml=/logs/pytest_test_sanity.xml /workspace/TransformerEngine/tests/pytorch/test_sanity.py\n"
        "FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path[param]\n"
        "+ python3 -m pytest -v -s --junitxml=/logs/pytest_test_recipe.xml /workspace/TransformerEngine/tests/pytorch/test_recipe.py\n"
        "FAILED tests/pytorch/test_recipe.py::test_dynamic_recipe_update[param]\n"
        "Error in the following test cases: test_sanity.py test_recipe.py\n",
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "test_sanity.py"]) == 0
    content = (log_dir / "L0torch_log_summary_test_sanity.py.md").read_text(encoding="utf-8")
    assert "# 1. tests/pytorch/test_sanity.py" in content
    assert "## 1.1 tests/pytorch/test_sanity.py::test_sanity_drop_path" in content
    assert "test_recipe.py" not in content
    assert "### 1.1.1" not in content


def test_summary_keyword_matches_second_level_and_only_shows_matched_cases(tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        textwrap.dedent(
            """\
            + python3 -m pytest -v -s --junitxml=/logs/pytest_test_sanity.xml /workspace/TransformerEngine/tests/pytorch/test_sanity.py
            FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path[param_a]
            FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path[param_b]
            Error in the following test cases: test_sanity.py
            """
        ),
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "tests/pytorch/test_sanity.py::test_sanity_drop_path"]) == 0
    content = (log_dir / "L0torch_log_summary_tests_pytorch_test_sanity.py_test_sanity_drop_path.md").read_text(encoding="utf-8")
    assert "## 1.1 tests/pytorch/test_sanity.py::test_sanity_drop_path" in content
    assert "### 1.1.1 tests/pytorch/test_sanity.py::test_sanity_drop_path[param_a]" in content
    assert "### 1.1.2 tests/pytorch/test_sanity.py::test_sanity_drop_path[param_b]" in content


def test_summary_keyword_matches_second_level_by_test_name_alias(tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        textwrap.dedent(
            """\
            + python3 -m pytest -v -s --junitxml=/logs/pytest_test_sanity.xml /workspace/TransformerEngine/tests/pytorch/test_sanity.py
            FAILED tests/pytorch/test_sanity.py::test_sanity_layernorm_linear[param_a]
            FAILED tests/pytorch/test_sanity.py::test_sanity_layernorm_linear[param_b]
            Error in the following test cases: test_sanity.py
            """
        ),
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "test_sanity_layernorm_linear"]) == 0
    content = (log_dir / "L0torch_log_summary_test_sanity_layernorm_linear.md").read_text(encoding="utf-8")
    assert "## 1.1 tests/pytorch/test_sanity.py::test_sanity_layernorm_linear" in content
    assert "### 1.1.1 tests/pytorch/test_sanity.py::test_sanity_layernorm_linear[param_a]" in content
    assert "### 1.1.2 tests/pytorch/test_sanity.py::test_sanity_layernorm_linear[param_b]" in content


def test_summary_keyword_matches_second_level_by_file_and_test_alias(tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        textwrap.dedent(
            """\
            + python3 -m pytest -v -s --junitxml=/logs/pytest_test_sanity.xml /workspace/TransformerEngine/tests/pytorch/test_sanity.py
            FAILED tests/pytorch/test_sanity.py::test_sanity_layernorm_linear[param_a]
            Error in the following test cases: test_sanity.py
            """
        ),
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "test_sanity.py::test_sanity_layernorm_linear"]) == 0
    content = (log_dir / "L0torch_log_summary_test_sanity.py_test_sanity_layernorm_linear.md").read_text(encoding="utf-8")
    assert "## 1.1 tests/pytorch/test_sanity.py::test_sanity_layernorm_linear" in content
    assert "### 1.1.1 tests/pytorch/test_sanity.py::test_sanity_layernorm_linear[param_a]" in content


def test_summary_keyword_matches_third_level_and_only_shows_that_case(tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        textwrap.dedent(
            """\
            + python3 -m pytest -v -s --junitxml=/logs/pytest_test_sanity.xml /workspace/TransformerEngine/tests/pytorch/test_sanity.py
            FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path[param_a]
            FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path[param_b]
            Error in the following test cases: test_sanity.py
            """
        ),
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "tests/pytorch/test_sanity.py::test_sanity_drop_path[param_b]"]) == 0
    content = (log_dir / "L0torch_log_summary_tests_pytorch_test_sanity.py_test_sanity_drop_path_param_b.md").read_text(encoding="utf-8")
    assert "## 1.1 tests/pytorch/test_sanity.py::test_sanity_drop_path" in content
    assert "### 1.1.1 tests/pytorch/test_sanity.py::test_sanity_drop_path[param_b]" in content
    assert "param_a" not in content


def test_summary_keyword_prints_match_metadata(capsys, tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        "+ python3 -m pytest -v -s --junitxml=/logs/pytest_test_sanity.xml /workspace/TransformerEngine/tests/pytorch/test_sanity.py\n"
        "FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path[param]\n"
        "Error in the following test cases: test_sanity.py\n",
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "test_sanity.py"]) == 0
    out = capsys.readouterr().out
    assert "Search:" in out
    assert "Match:" in out
    assert "Expand:" in out
    assert "Level:" not in out


def test_summary_keyword_no_match_returns_error(capsys, tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        "+ python3 -m pytest -v -s --junitxml=/logs/pytest_test_sanity.xml /workspace/TransformerEngine/tests/pytorch/test_sanity.py\n"
        "FAILED tests/pytorch/test_sanity.py::test_sanity_drop_path[param]\n"
        "Error in the following test cases: test_sanity.py\n",
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "not_found_keyword"]) == 1
    out = capsys.readouterr().out
    assert "未匹配到关键词" in out


def test_summary_matches_env_by_run_order(tmp_path, monkeypatch):
    test_sh = tmp_path / "test.sh"
    test_sh.write_text(
        textwrap.dedent(
            """\
            NVTE_INT8_SIM_FP8=1 python3 -m pytest -v -s --tb=auto $TE_PATH/tests/pytorch/test_float8_current_scaling_exact.py
            python3 -m pytest -v -s --tb=auto $TE_PATH/tests/pytorch/test_float8_current_scaling_exact.py
            NVTE_INT8_SIM_FP8=1 NVTE_INT8_SIM_FP8_TENSORWISE=1 python3 -m pytest -v -s --tb=auto $TE_PATH/tests/pytorch/test_float8_current_scaling_exact.py
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(summary_command, "DEFAULT_TEST_SH", str(test_sh))

    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        textwrap.dedent(
            """\
            + NVTE_INT8_SIM_FP8=1
            + python3 -m pytest -v -s --tb=auto --junitxml=/logs/pytest_test_float8_current_scaling_exact_int8.xml /workspace/TransformerEngine/tests/pytorch/test_float8_current_scaling_exact.py
            PASSED anything
            + python3 -m pytest -v -s --tb=auto --junitxml=/logs/pytest_test_float8_current_scaling_exact.xml /workspace/TransformerEngine/tests/pytorch/test_float8_current_scaling_exact.py
            FAILED TransformerEngine/tests/pytorch/test_float8_current_scaling_exact.py::TestFP8CurrentScalingRecipeLinear::test_fp8_current_scaling_with_linear_module[param]
            + NVTE_INT8_SIM_FP8=1
            + NVTE_INT8_SIM_FP8_TENSORWISE=1
            + python3 -m pytest -v -s --tb=auto --junitxml=/logs/pytest_test_float8_current_scaling_exact_int8_tensorwise.xml /workspace/TransformerEngine/tests/pytorch/test_float8_current_scaling_exact.py
            PASSED anything
            Error in the following test cases: test_float8_current_scaling_exact.py
            """
        ),
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "l3"]) == 0
    content = (log_dir / "L0torch_log_summary.md").read_text(encoding="utf-8")
    assert "python3 -m pytest -v -s $TE_PATH/tests/pytorch/test_float8_current_scaling_exact.py::test_fp8_current_scaling_with_linear_module" in content
    assert "NVTE_INT8_SIM_FP8=1 python3 -m pytest -v -s $TE_PATH/tests/pytorch/test_float8_current_scaling_exact.py::test_fp8_current_scaling_with_linear_module" not in content


def test_summary_parses_class_based_failures(tmp_path):
    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        textwrap.dedent(
            """\
            + python3 -m pytest -v -s --junitxml=/logs/pytest_test_fusible_ops.xml /workspace/TransformerEngine/tests/pytorch/test_fusible_ops.py
            FAILED TransformerEngine/tests/pytorch/test_fusible_ops.py::TestFuser::test_fp8_scale_update[bf16]
            Error in the following test cases: test_fusible_ops.py
            """
        ),
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "l3"]) == 0
    content = (log_dir / "L0torch_log_summary.md").read_text(encoding="utf-8")
    assert "## 1.1 tests/pytorch/test_fusible_ops.py::test_fp8_scale_update" in content
    assert "### 1.1.1 tests/pytorch/test_fusible_ops.py::test_fp8_scale_update[bf16]" in content


def test_summary_reports_crash_only_file_failures(tmp_path, monkeypatch):
    test_sh = tmp_path / "test.sh"
    test_sh.write_text(
        "ROCBLAS_ATOMICS_MOD=0 HIPBLASLT_ATOMICS_MOD=0 PYTORCH_JIT=0 NVTE_TORCH_COMPILE=0 NVTE_ALLOW_NONDETERMINISTIC_ALGO=0 python3 -m pytest -v -s $TE_PATH/tests/pytorch/test_numerics.py\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(summary_command, "DEFAULT_TEST_SH", str(test_sh))

    log_dir = tmp_path / "logs" / "20260312_120000" / "l0torch"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "L0_pytorch_unittest_nmz76.log"
    log_file.write_text(
        textwrap.dedent(
            """\
            + ROCBLAS_ATOMICS_MOD=0
            + HIPBLASLT_ATOMICS_MOD=0
            + PYTORCH_JIT=0
            + NVTE_TORCH_COMPILE=0
            + NVTE_ALLOW_NONDETERMINISTIC_ALGO=0
            + python3 -m pytest -v -s --junitxml=/logs/pytest_test_numerics.xml /workspace/TransformerEngine/tests/pytorch/test_numerics.py
            /workspace/TransformerEngine/qa/L0_pytorch_unittest/test.sh: line 31: 2004208 Segmentation fault      (core dumped) ROCBLAS_ATOMICS_MOD=0 HIPBLASLT_ATOMICS_MOD=0 PYTORCH_JIT=0 NVTE_TORCH_COMPILE=0 NVTE_ALLOW_NONDETERMINISTIC_ALGO=0 python3 -m pytest -v -s --junitxml=$XML_LOG_DIR/pytest_test_numerics.xml $TE_PATH/tests/pytorch/test_numerics.py
            + test_fail test_numerics.py
            Error in the following test cases: test_numerics.py
            """
        ),
        encoding="utf-8",
    )

    assert summary_command.route_summary_command([str(log_file), "l3"]) == 0
    content = (log_dir / "L0torch_log_summary.md").read_text(encoding="utf-8")
    assert "## 1.1 tests/pytorch/test_numerics.py" in content
    assert "ROCBLAS_ATOMICS_MOD=0 HIPBLASLT_ATOMICS_MOD=0 PYTORCH_JIT=0 NVTE_TORCH_COMPILE=0 NVTE_ALLOW_NONDETERMINISTIC_ALGO=0 python3 -m pytest -v -s $TE_PATH/tests/pytorch/test_numerics.py" in content
    assert "### 1.1.1 tests/pytorch/test_numerics.py" in content