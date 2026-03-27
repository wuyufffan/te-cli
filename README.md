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
te sum help      # 查看摘要帮助

# 推荐路径
te run           # 交互式选择测试
te log list      # 查看日志时间戳目录
te log list 20260313_091738
te build help
te rebuild help
te sum /workspace/logs/20260313_091738/l0torch/L0_pytorch_unittest_nmz76.log   # 默认 l2
te sum /workspace/logs/20260313_091738/l0torch/L0_pytorch_unittest_nmz76.log l1
te sum /workspace/logs/20260313_091738/l0torch/L0_pytorch_unittest_nmz76.log l3
te sum /workspace/logs/20260313_091738/l0torch/L0_pytorch_unittest_nmz76.log test_sanity.py

# 测试
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
te log list      # 查看日志时间戳目录
te log list 20260313_091738
te log l0torch -n 5
te sum help      # 查看摘要帮助
te sum /workspace/logs/20260313_091738/l0torch/L0_pytorch_unittest_nmz76.log
te sum /workspace/logs/20260313_091738/l0torch/L0_pytorch_unittest_nmz76.log l1
te sum /workspace/logs/20260313_091738/l0torch/L0_pytorch_unittest_nmz76.log l3
te sum /workspace/logs/20260313_091738/l0torch/L0_pytorch_unittest_nmz76.log test_sanity.py

## te sum 级别说明

- `te sum LOG` 或 `te sum LOG l2`：输出一级标题、二级标题，不显示复现命令
- `te sum LOG l1`：只输出一级标题
- `te sum LOG l3`：输出完整内容，包含复现命令和三级参数用例标题
- `te sum LOG keyword`：精确匹配一级/二级/三级标题的完整文本或常用别名，并按匹配层级裁剪输出
- `te sum` 只支持 `l0torch` 目录日志或文件名以 `L0_pytorch_unittest` 开头的 L0 日志

## 新旧命令映射

| 旧命令 | 新命令 | 状态 |
| --- | --- | --- |
| `te -b -c` | `te rebuild py` | 推荐使用新命令 |
| `te -b -t` | `te rebuild cpp` | 推荐使用新命令 |
| `te -b -r` | `te rebuild all` | 推荐使用新命令 |
| `te -0 -c` | `te run l0cpp` | 推荐使用新命令 |
| `te -0 -t` | `te run l0torch` | 推荐使用新命令 |
| `te -1 -t` | `te run l1torch` | 推荐使用新命令 |

说明：V1 起旧 flag 兼容层只保留以上 6 条常用入口；旧的 `-l`、`-k`、`-d` 组合不再作为正式接口，请改用 `te log ...`、`te build ...`、`te rebuild ...`。
```

## 测试日志目录

- 时间戳目录格式：`YYYYMMDD_HHMMSS`，例如 `20260313_091738`
- L0 C++: `/workspace/logs/20260313_091738/l0cpp/L0_cppunittest_HOST.log`
- L0 PyTorch: `/workspace/logs/20260313_091738/l0torch/L0_pytorch_unittest_HOST.log`
- L1 PyTorch: `/workspace/logs/20260313_091738/l1torch/L1_pytorch_distributed_unittest_HOST.log`

旧命令 `te -0 -c`、`te -0 -t`、`te -1 -t` 仍可继续使用，其余旧 flag 组合请迁移到命名式子命令。

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
