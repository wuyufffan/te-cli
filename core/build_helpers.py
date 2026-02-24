#!/usr/bin/env python3
"""
构建辅助函数
"""
import logging
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Optional

from config import BLUE, GREEN, GREY, RED, RESET
from config_manager import get_config
from process_helpers import check_task_running, confirm_if_log_exists

logger = logging.getLogger(__name__)

# 公共环境变量（所有构建脚本共用）
COMMON_ENV_VARS = """
export NVTE_BUILD_SUPPRESS_UNUSED_WARNING=1
export NVTE_BUILD_SUPPRESS_RETURN_TYPE_WARNING=1
export NVTE_BUILD_SUPPRESS_SIGN_COMPARE_WARNING=1
export NVTE_FRAMEWORK=pytorch
export NVTE_USE_ROCM=1
export NVTE_USE_HIPBLASLT=1
export NVTE_USE_ROCBLAS=1
export NVTE_UB_WITH_MPI=0
export CXX=hipcc
export VERBOSE=1
""".strip()


def _get_dtk_config() -> str:
    """获取 DTK 配置脚本片段"""
    config = get_config()
    return f"""
DTK_BASE="{config.dtk_base}"
CMAKE_SUFFIX="lib64/cmake/amd_comgr"
if [ -d "{config.dtk_26_path}" ]; then
     DTK_BASE="{config.dtk_26_path}"
     CMAKE_SUFFIX="dcc/comgr/lib/cmake/amd_comgr"
fi
export CMAKE_PREFIX_PATH="${{DTK_BASE}}/${{CMAKE_SUFFIX}}"
export MPI_HOME=/opt/mpi
""".strip()


def _resolve_init_script() -> str:
    """解析初始化脚本路径"""
    return get_config().get_init_script()


def _start_background_script(
    log_file: str,
    script: str,
    success_message: str,
    log_prefix: str = "└─",
) -> int:
    """在后台启动脚本"""
    logger.info(f"启动后台任务: {success_message}")
    logger.debug(f"日志文件: {log_file}")
    
    with open(log_file, "w", encoding="utf-8") as log_handle:
        subprocess.Popen(
            ["nohup", "bash", "-c", script],
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    
    print(f"{GREEN}✅ {success_message}{RESET}")
    print(f"   {GREY}{log_prefix} Log:{RESET}  {BLUE}{log_file}{RESET}")
    return 0


def _build_script_header(init_script: str) -> str:
    """构建脚本头部（公共部分）"""
    return f"""
start_time=$(date +%s)

INIT_SCRIPT="{init_script}"

if [ -f "$INIT_SCRIPT" ]; then
     source "$INIT_SCRIPT"
else
     echo "❌ Error: TE init script not found at: $INIT_SCRIPT"
     exit 1
fi

{_get_dtk_config()}

{COMMON_ENV_VARS}
""".strip()


def _python_build_script(init_script: str, clean: bool) -> str:
    """生成 Python 构建脚本"""
    config = get_config()
    te_path = config.te_path
    clean_cmd = f"cd {te_path} && rm -rf build transformer_engine.egg-info/" if clean else f"cd {te_path} || exit 2"
    finish_label = "Python Clean Build Completed" if clean else "Python Build Completed"
    
    return f"""
{_build_script_header(init_script)}

{clean_cmd}

export PYTHONPATH="{te_path}/3rdparty/hipify_torch:$PYTHONPATH"

python3 -m pip install -e . -vv --no-build-isolation 2>&1

end_time=$(date +%s)
echo ""
echo "✅ {finish_label} (Duration: $((end_time - start_time))s)"
"""


def _cpp_build_script(init_script: str) -> str:
    """生成 C++ 构建脚本"""
    config = get_config()
    
    return f"""
{_build_script_header(init_script)}

cd {config.te_path}/tests/cpp || exit 2

export PYTHONPATH={config.te_path}/3rdparty/hipify_torch:$PYTHONPATH

cmake -GNinja -Bbuild . 2>&1
cmake --build build 2>&1

end_time=$(date +%s)
echo ""
echo "✅ C++ Build Completed (Duration: $((end_time - start_time))s)"
"""


def _common_build_check(log_file: str, task_name: str, pattern: str) -> int:
    """公共构建前检查"""
    if check_task_running(pattern, task_name, "", "", f"te -b -k") != 0:
        return 1
    if confirm_if_log_exists(log_file) != 0:
        return 1
    return 0


def build_te_func_incremental(args: Optional[Iterable[str]] = None) -> int:
    """增量构建 Python"""
    config = get_config()
    if _common_build_check(config.log_files["build_py"], "Python Build", "python3 -m pip") != 0:
        return 1
    
    init_script = _resolve_init_script()
    script = _python_build_script(init_script, clean=False)
    return _start_background_script(
        config.log_files["build_py"], 
        script, 
        "Python Build Started (Background)"
    )


def build_te_func(args: Optional[Iterable[str]] = None) -> int:
    """清理构建 Python"""
    config = get_config()
    if _common_build_check(config.log_files["build_py"], "Python Build", "python3 -m pip") != 0:
        return 1
    
    init_script = _resolve_init_script()
    script = _python_build_script(init_script, clean=True)
    return _start_background_script(
        config.log_files["build_py"],
        script,
        "Python Clean Build Started (Background)"
    )


def build_cpp_test_func(args: Optional[Iterable[str]] = None) -> int:
    """构建 C++ 测试"""
    config = get_config()
    if _common_build_check(config.log_files["build_cpp"], "C++ Build", "cmake --build") != 0:
        return 1
    
    init_script = _resolve_init_script()
    script = _cpp_build_script(init_script)
    return _start_background_script(
        config.log_files["build_cpp"],
        script,
        "C++ Build Started (Background)"
    )


def build_clean_cpp(args: Optional[Iterable[str]] = None) -> int:
    """清理 C++ 构建产物"""
    config = get_config()
    cpp_dir = os.path.join(config.te_path, "tests", "cpp")
    build_dir = os.path.join(cpp_dir, "build")
    
    if os.path.isdir(cpp_dir):
        logger.info(f"清理 C++ 构建目录: {build_dir}")
        print(f"   {GREY}├─ Step:{RESET} Cleaning C++ build artifacts...")
        shutil.rmtree(build_dir, ignore_errors=True)
    
    return 0


def build_all_func(args: Optional[Iterable[str]] = None) -> int:
    """全量构建"""
    config = get_config()
    if _common_build_check(config.log_files["build_all"], "Full Build", "python3 -m pip|cmake --build") != 0:
        return 1
    
    init_script = _resolve_init_script()
    target_path = config.te_path
    
    if args:
        args_list = list(args)
        if args_list:
            target_path = args_list[0]
    
    script = _full_build_script(init_script, target_path)
    return _start_background_script(
        config.log_files["build_all"],
        script,
        "Full Clean & Build Started (Background)"
    )


def _full_build_script(init_script: str, target_path: str) -> str:
    """生成全量构建脚本"""
    config = get_config()
    
    return f"""
{_build_script_header(init_script)}

echo "🔥 Full Clean & Build Started"

echo "🧹 Cleaning up..."
cd "{target_path}" || exit 2
rm -rf build transformer_engine.egg-info/ tests/cpp/build dist
find . -name "*.so" -type f -delete
find . -name "__pycache__" -type d -exec rm -rf {{}} +

echo "🚀 Building Python..."
export PYTHONPATH="{config.te_path}/3rdparty/hipify_torch:$PYTHONPATH"
python3 -m pip install -e . -vv --no-build-isolation 2>&1
py_status=$?

if [ $py_status -eq 0 ]; then
    echo "🚀 Building C++ Tests..."
    cd "{target_path}/tests/cpp" || exit 2
    cmake -GNinja -Bbuild . 2>&1
    cmake --build build 2>&1
else
    echo "Python Build Failed"
    exit $py_status
fi

end_time=$(date +%s)
echo ""
echo "✅ Full Build Completed (Duration: $((end_time - start_time))s)"
"""


def rebuild_dev(args: Optional[Iterable[str]] = None) -> int:
    """开发重建（增量）"""
    config = get_config()
    if not config.te_path:
        logger.error("TE_PATH not set!")
        print(f"   {GREY}└─ Error:{RESET} {RED}TE_PATH not set!{RESET}")
        return 1
    
    if _common_build_check(config.log_files["rebuild"], "Rebuild", "python3 -m pip|cmake --build") != 0:
        return 1
    
    init_script = _resolve_init_script()
    
    extra_args = []
    if args:
        extra_args = [str(arg) for arg in args]
    extra_files = " ".join(shlex.quote(arg) for arg in extra_args)
    
    script = _rebuild_script(init_script, config.te_path, extra_files)
    return _start_background_script(
        config.log_files["rebuild"],
        script,
        "Rebuild Started (Background)",
        log_prefix="├─",
    )


def _rebuild_script(init_script: str, te_path: str, extra_files: str) -> str:
    """生成重建脚本"""
    return f"""
{_build_script_header(init_script)}

cu_files=("{te_path}/transformer_engine/common/swizzle/swizzle.cu" {extra_files})
for cu_file in "${{cu_files[@]}}"; do
    [[ -z "$cu_file" ]] && continue
    if [ -f "$cu_file" ]; then
        touch -c "$cu_file"
        echo "Touched: $cu_file"
    fi
done

echo "=== [Phase 1] Python Incremental Build ==="
cd "{te_path}" || exit 1
python3 -m pip install --no-build-isolation -v -e . 2>&1
py_status=$?

if [ $py_status -eq 0 ]; then
     echo "=== [Phase 2] C++ Tests Incremental Build ==="
     cd "{te_path}/tests/cpp" || exit 1
     cmake -B build -G Ninja . 2>&1
     cmake --build build 2>&1
else
    echo "Python build failed."
    exit $py_status
fi

end_time=$(date +%s)
echo ""
echo "✅ Rebuild Completed (Duration: $((end_time - start_time))s)"
"""
