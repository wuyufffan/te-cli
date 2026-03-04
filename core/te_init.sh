#!/bin/bash
#
# TE (TransformerEngine) 环境初始化脚本
# 由 te-cli 自动调用
#

# 设置 DTK 环境，优先 26.04，其次 /opt/dtk（若为软链），最后 25.04.2
if [ -d "${DTK_BASE:-}" ]; then
    export DTK_BASE="${DTK_BASE}"
elif [ -d "/opt/dtk-26.04" ]; then
    export DTK_BASE="/opt/dtk-26.04"
elif [ -d "/opt/dtk" ]; then
    export DTK_BASE="$(readlink -f /opt/dtk)"
elif [ -d "/opt/dtk-25.04.2" ]; then
    export DTK_BASE="/opt/dtk-25.04.2"
fi

if [ -d "${DTK_BASE}/dcc/comgr/lib/cmake/amd_comgr" ]; then
    export CMAKE_PREFIX_PATH="${DTK_BASE}/dcc/comgr/lib/cmake/amd_comgr"
elif [ -d "${DTK_BASE}/lib64/cmake/amd_comgr" ]; then
    export CMAKE_PREFIX_PATH="${DTK_BASE}/lib64/cmake/amd_comgr"
elif [ -d "${DTK_BASE}/lib/cmake/amd_comgr" ]; then
    export CMAKE_PREFIX_PATH="${DTK_BASE}/lib/cmake/amd_comgr"
fi

# MPI 设置
export MPI_HOME=/opt/mpi

# TE 构建环境变量
export NVTE_BUILD_SUPPRESS_UNUSED_WARNING=1
export NVTE_BUILD_SUPPRESS_RETURN_TYPE_WARNING=1
export NVTE_BUILD_SUPPRESS_SIGN_COMPARE_WARNING=1
export NVTE_FRAMEWORK=pytorch
export NVTE_USE_ROCM=1
export NVTE_USE_HIPBLASLT=1
export NVTE_USE_ROCBLAS=1
export NVTE_UB_WITH_MPI=0

# 编译器设置
export CXX=hipcc
export VERBOSE=1
