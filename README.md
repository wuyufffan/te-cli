# te-cli

TransformerEngine 开发命令行工具，聚焦构建、测试与任务管理。

## 仓库定位

- 面向 TE 开发/调试流程，统一构建与测试入口。
- 提供 Python/C++ 构建、L0/L1 测试、日志与任务管理能力。
- 本仓库是 te 的功能与参数说明唯一来源。

## 安装

### 独立安装

```bash
git clone https://github.com/wuyufffan/te-cli.git
cd te-cli
./install.sh
```

### 通过主仓安装

```bash
cd ~/my_linux_config
make install C=te
```

## 快速使用

```bash
te -h            # 查看完整帮助
te help old      # 查看旧版参数风格帮助
te --version     # 查看版本
te --check-env   # 检查环境依赖
te run help      # 查看测试帮助
te log help      # 查看日志帮助
te build help    # 查看全量构建帮助
te rebuild help  # 查看增量构建帮助
te log watch     # 预留中的运行日志观看入口
te sum help      # 查看摘要帮助

# 推荐路径
te run           # 交互式选择测试
te log list      # 查看日志时间戳目录
te log list 20260313_091738
te build help
te rebuild help
te sum /workspace/logs/20260313_091738/l0torch/L0_pytorch_unittest_nmz76.log

# 测试
te -0 -t         # L0 测试
te -1 -t         # L1 测试
te run l0cpp     # L0 C++ 测试
te run l0torch   # L0 PyTorch 测试
te run l1torch   # L1 PyTorch 分布式测试
te run all       # 一次启动三个测试

# 构建
te build py      # Python 全量构建
te rebuild py    # Python 增量构建
te build cpp     # C++ 全量构建
te rebuild cpp   # C++ 增量构建
te build all     # Python + C++ 全量构建
te rebuild all   # Python + C++ 增量重建

# 任务/日志
te -p            # 查看任务
te log           # 查看日志帮助
te log help      # 查看日志帮助
te log watch     # 预留中的运行日志观看入口
te log list      # 查看日志时间戳目录
te log list 20260313_091738
te log l0torch -n 5
te sum help      # 查看摘要帮助
te sum /workspace/logs/20260313_091738/l0torch/L0_pytorch_unittest_nmz76.log

## 新旧命令映射

| 旧命令 | 新命令 | 状态 |
| --- | --- | --- |
| `te -b -c -d` | `te build py` | 推荐使用新命令 |
| `te -b -c` | `te rebuild py` | 推荐使用新命令 |
| `te -b -t -d` | `te build cpp` | 推荐使用新命令 |
| `te -b -t` | `te rebuild cpp` | 推荐使用新命令 |
| `te -b -r -d` | `te build all` | 推荐使用新命令 |
| `te -b -r` | `te rebuild all` | 推荐使用新命令 |
| `te -0 -c` | `te run l0cpp` | 推荐使用新命令 |
| `te -0 -t` | `te run l0torch` | 推荐使用新命令 |
| `te -1 -t` | `te run l1torch` | 推荐使用新命令 |
| `te -b ... -l` | `te log watch` | 新入口已预留，旧命令暂保留兼容 |
| `te -b ... -k` | 旧命令暂保留兼容 | 后续再补显式命名 |
```

## 测试日志目录

- 时间戳目录格式：`YYYYMMDD_HHMMSS`，例如 `20260313_091738`
- L0 C++: `/workspace/logs/20260313_091738/l0cpp/L0_cppunittest_HOST.log`
- L0 PyTorch: `/workspace/logs/20260313_091738/l0torch/L0_pytorch_unittest_HOST.log`
- L1 PyTorch: `/workspace/logs/20260313_091738/l1torch/L1_pytorch_distributed_unittest_HOST.log`

旧命令 `te -0 -c`、`te -0 -t`、`te -1 -t` 仍可继续使用，`-l` 会自动打开对应类型最新一条日志。

## 配置

- 配置文件：`~/.te_config.json`
- 首次建议先执行：`te --check-env`

示例：

```json
{
  "te_path": "/workspace/TransformerEngine"
}
```

## 运行要求

- Python 3.10+
- CMake 3.20+
- Ninja
- ROCm/DTK 环境（按实际平台版本）

## 开发与测试

```bash
python3 -m pytest tests/unit -q
python3 -m pytest --cov=core --cov-report=term-missing tests/
```

## 许可证

MIT
