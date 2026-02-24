#!/usr/bin/env python3
"""
测试运行脚本
提供多种测试运行模式
"""
import subprocess
import sys
from pathlib import Path


def run_unit_tests():
    """运行所有单元测试"""
    print("=" * 60)
    print("运行单元测试")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=short"],
        cwd=Path(__file__).parent.parent
    )
    return result.returncode


def run_integration_tests():
    """运行所有集成测试"""
    print("=" * 60)
    print("运行集成测试")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/integration/", "-v", "--tb=short"],
        cwd=Path(__file__).parent.parent
    )
    return result.returncode


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("运行所有测试")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=Path(__file__).parent.parent
    )
    return result.returncode


def run_tests_with_coverage():
    """运行测试并生成覆盖率报告"""
    print("=" * 60)
    print("运行测试并生成覆盖率报告")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/",
         "--cov=te_python", "--cov-report=term-missing",
         "--cov-fail-under=80"],
        cwd=Path(__file__).parent.parent
    )
    return result.returncode


def run_parallel_tests():
    """并行运行非串行测试"""
    print("=" * 60)
    print("并行运行测试 (排除串行测试)")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/",
         "-m", "not serial", "-n", "auto", "-v"],
        cwd=Path(__file__).parent.parent
    )
    return result.returncode


def run_serial_tests():
    """串行运行串行标记的测试"""
    print("=" * 60)
    print("串行运行串行标记的测试")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/",
         "-m", "serial", "-v", "--tb=short"],
        cwd=Path(__file__).parent.parent
    )
    return result.returncode


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TE CLI 测试运行器")
    parser.add_argument(
        "mode",
        choices=["unit", "integration", "all", "coverage", "parallel", "serial"],
        default="all",
        nargs="?",
        help="测试运行模式"
    )
    
    args = parser.parse_args()
    
    modes = {
        "unit": run_unit_tests,
        "integration": run_integration_tests,
        "all": run_all_tests,
        "coverage": run_tests_with_coverage,
        "parallel": run_parallel_tests,
        "serial": run_serial_tests,
    }
    
    return modes[args.mode]()


if __name__ == "__main__":
    sys.exit(main())
