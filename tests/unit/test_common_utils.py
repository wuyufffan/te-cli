#!/usr/bin/env python3
"""
common_utils 模块单元测试
"""
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "te_python"))
import common_utils


@pytest.mark.unit
class TestCommonUtils:
    """测试通用工具函数"""
    
    # ---------- get_human_size ----------
    
    def test_get_human_size_success(self):
        """正常获取文件大小"""
        with patch("subprocess.check_output") as mock:
            mock.return_value = "4.0K    /path/to/file\n"
            assert common_utils.get_human_size("/path/to/file") == "4.0K"
    
    def test_get_human_size_failure(self):
        """获取失败返回 0"""
        with patch("subprocess.check_output") as mock:
            mock.side_effect = subprocess.CalledProcessError(1, "du")
            assert common_utils.get_human_size("/nonexistent") == "0"
    
    # ---------- pgrep ----------
    
    def test_pgrep_found_processes(self):
        """找到匹配的进程"""
        with patch("subprocess.check_output") as mock:
            mock.return_value = "1234\n5678\n"
            assert common_utils.pgrep("python3") == ["1234", "5678"]
    
    def test_pgrep_no_match(self):
        """没有找到进程"""
        with patch("subprocess.check_output") as mock:
            mock.side_effect = subprocess.CalledProcessError(1, "pgrep")
            assert common_utils.pgrep("nonexistent") == []
    
    # ---------- pkill ----------
    
    def test_pkill_success(self):
        """成功终止进程"""
        with patch("subprocess.check_call") as mock:
            mock.return_value = 0
            assert common_utils.pkill("python3") == 0
    
    def test_pkill_failure(self):
        """终止失败"""
        with patch("subprocess.check_call") as mock:
            mock.side_effect = subprocess.CalledProcessError(1, "pkill")
            assert common_utils.pkill("nonexistent") == 1
    
    # ---------- 进程时间 ----------
    
    def test_get_process_start_time_success(self):
        """获取进程启动时间"""
        with patch("subprocess.check_output") as mock:
            mock.return_value = "Mon Jan 15 10:30:00 2024\n"
            assert common_utils.get_process_start_time("1234") == "Mon Jan 15 10:30:00 2024"
    
    def test_get_process_start_time_failure(self):
        """获取失败返回空"""
        with patch("subprocess.check_output") as mock:
            mock.side_effect = subprocess.CalledProcessError(1, "ps")
            assert common_utils.get_process_start_time("9999") == ""
    
    def test_get_process_elapsed_success(self):
        """获取进程运行时间"""
        with patch("subprocess.check_output") as mock:
            mock.return_value = "00:05:30\n"
            assert common_utils.get_process_elapsed("1234") == "00:05:30"
    
    def test_get_process_elapsed_failure(self):
        """获取失败返回空"""
        with patch("subprocess.check_output") as mock:
            mock.side_effect = subprocess.CalledProcessError(1, "ps")
            assert common_utils.get_process_elapsed("9999") == ""
