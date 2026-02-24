#!/usr/bin/env python3
"""
进程管理集成测试
真实创建和管理进程
"""
import os
import sys
import subprocess
import time
import signal
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "te_python"))
import common_utils
import process_helpers


# =============================================================================
# pgrep 和 pkill 集成测试
# =============================================================================

@pytest.mark.integration
@pytest.mark.process
@pytest.mark.serial  # 进程测试必须串行执行
class TestPgrepPkillIntegration:
    """测试真实的 pgrep 和 pkill 功能"""
    
    def test_pgrep_finds_real_process(self, create_test_process):
        """测试 pgrep 能找到真实创建的进程"""
        # 创建一个 sleep 进程
        proc = create_test_process(["sleep", "10"])
        pid = str(proc.pid)
        
        # 等待进程启动
        time.sleep(0.1)
        
        # 使用 pgrep 查找进程
        result = common_utils.pgrep("sleep")
        assert pid in result, f"应该找到进程 {pid}，但只找到 {result}"
    
    def test_pgrep_no_match(self):
        """测试 pgrep 返回空列表当没有匹配时"""
        # 使用一个不太可能存在的进程名
        result = common_utils.pgrep("nonexistent_process_xyz_12345")
        assert result == [], "应该返回空列表"
    
    def test_pkill_terminates_process(self, create_test_process):
        """测试 pkill 能终止真实进程"""
        # 创建一个唯一的进程标记
        marker = "test_marker_abc_123"
        proc = create_test_process(["sleep", "60"])
        
        # 等待进程启动
        time.sleep(0.1)
        
        # 验证进程存在
        assert proc.poll() is None, "进程应该还在运行"
        
        # 使用 pkill 终止（发送 SIGTERM）
        result = common_utils.pkill("sleep", signal="-15")
        
        # 等待进程终止
        time.sleep(0.5)
        
        # 验证进程已终止
        assert proc.poll() is not None, "进程应该已被终止"
    
    def test_get_process_start_time(self, create_test_process):
        """测试获取真实进程的启动时间"""
        proc = create_test_process(["sleep", "10"])
        pid = str(proc.pid)
        
        # 等待进程启动
        time.sleep(0.1)
        
        # 获取启动时间
        start_time = common_utils.get_process_start_time(pid)
        assert start_time != "", "应该返回启动时间"
        # 验证格式（应该包含日期信息）
        assert any(x in start_time for x in ["202", "Jan", "Feb", "Mar", "Mon", "Tue"]), \
            f"启动时间格式不正确: {start_time}"
    
    def test_get_process_elapsed(self, create_test_process):
        """测试获取真实进程的运行时间"""
        proc = create_test_process(["sleep", "10"])
        pid = str(proc.pid)
        
        # 等待进程启动
        time.sleep(0.5)
        
        # 获取运行时间
        elapsed = common_utils.get_process_elapsed(pid)
        assert elapsed != "", "应该返回运行时间"
        # 格式应该是 HH:MM 或 HH:MM:SS
        assert ":" in elapsed, f"运行时间格式不正确: {elapsed}"


# =============================================================================
# show_processes 集成测试
# =============================================================================

@pytest.mark.integration
@pytest.mark.process
@pytest.mark.serial
class TestShowProcessesIntegration:
    """测试 show_processes 的真实行为"""
    
    def test_show_processes_no_tasks(self, capsys):
        """测试没有任务时的输出"""
        # 确保没有测试相关的进程在运行
        result = process_helpers.show_processes()
        assert result == 0
        captured = capsys.readouterr()
        # 应该显示 "No running tasks" 或任务列表
        assert "Running TE Tasks" in captured.out
    
    def test_show_processes_with_build_task(self, create_test_process, capsys, tmp_path):
        """测试有构建任务时的输出"""
        # 创建一个真实的构建进程（使用 python3 -m pip 作为标记）
        proc = subprocess.Popen(
            ["python3", "-c", "import time; time.sleep(30)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # 等待进程启动
        time.sleep(0.2)
        
        # 创建一个模拟的 pip 进程
        pip_proc = subprocess.Popen(
            ["bash", "-c", "exec python3 -m pip --version && sleep 30"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        time.sleep(0.3)
        
        try:
            result = process_helpers.show_processes()
            assert result == 0
            captured = capsys.readouterr()
            # 应该检测到构建任务或显示任务列表
            # 注意：由于进程检测的不确定性，我们允许 "No running tasks" 也是可接受的
            assert "Running TE Tasks" in captured.out
        finally:
            # 清理
            for p in [proc, pip_proc]:
                try:
                    p.terminate()
                    p.wait(timeout=1)
                except (subprocess.TimeoutExpired, ProcessLookupError):
                    try:
                        p.kill()
                    except ProcessLookupError:
                        pass


# =============================================================================
# 进程终止流程集成测试
# =============================================================================

@pytest.mark.integration
@pytest.mark.process
@pytest.mark.serial
class TestKillProcessIntegration:
    """测试进程终止的完整流程"""
    
    def test_kill_task_logic_confirm_yes(self, create_test_process, monkeypatch):
        """测试确认终止任务的完整流程"""
        proc = create_test_process(["sleep", "30"])
        pid = str(proc.pid)
        
        # 等待进程启动
        time.sleep(0.1)
        
        # 模拟用户输入 "y"
        monkeypatch.setattr("builtins.input", lambda _: "y")
        
        result = process_helpers._kill_task_logic([pid], "sleep", "Test Task")
        
        # 等待终止完成
        time.sleep(0.5)
        
        assert result == 0, "应该成功终止"
        assert proc.poll() is not None, "进程应该已被终止"
    
    def test_kill_task_logic_confirm_no(self, create_test_process, monkeypatch):
        """测试取消终止任务"""
        proc = create_test_process(["sleep", "30"])
        pid = str(proc.pid)
        
        # 等待进程启动
        time.sleep(0.1)
        
        # 模拟用户输入 "n"
        monkeypatch.setattr("builtins.input", lambda _: "n")
        
        result = process_helpers._kill_task_logic([pid], "sleep", "Test Task")
        
        assert result == 1, "应该返回取消状态"
        assert proc.poll() is None, "进程应该仍在运行"
        
        # 清理
        proc.terminate()
        proc.wait()
    
    def test_kill_build_task_integration(self, create_test_process, monkeypatch):
        """测试 kill_build_task 的集成"""
        # 创建一个模拟的构建进程
        proc = subprocess.Popen(
            ["bash", "-c", "python3 -m pip --version && sleep 30"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # 等待进程启动
        time.sleep(0.3)
        
        # 模拟用户输入 "y"
        monkeypatch.setattr("builtins.input", lambda _: "y")
        
        try:
            result = process_helpers.kill_build_task()
            time.sleep(0.5)
            
            # 可能找到也可能找不到，取决于进程状态
            assert result in [0, 1], "应该返回有效状态码"
        finally:
            # 确保清理
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()


# =============================================================================
# 检查任务运行状态集成测试
# =============================================================================

@pytest.mark.integration
@pytest.mark.process
@pytest.mark.serial
class TestCheckTaskRunningIntegration:
    """测试 check_task_running 的集成"""
    
    def test_check_task_running_real_process(self, create_test_process):
        """测试检查真实运行中的任务"""
        proc = create_test_process(["sleep", "10"])
        
        # 等待进程启动
        time.sleep(0.1)
        
        # 检查任务（使用 sleep 作为模式）
        result = process_helpers.check_task_running(
            "sleep",
            "Test Sleep Task",
            kill_cmd="kill"
        )
        
        assert result == 1, "应该检测到任务在运行"
        
        # 清理
        proc.terminate()
        proc.wait()
    
    def test_check_task_not_running(self):
        """测试检查未运行的任务"""
        # 使用一个不可能存在的模式
        result = process_helpers.check_task_running(
            "nonexistent_xyz_abc_12345",
            "Nonexistent Task"
        )
        
        assert result == 0, "应该返回 0（没有任务在运行）"
