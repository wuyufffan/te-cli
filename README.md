# te-cli

TransformerEngine (TE) 开发工具集，专为 AMD ROCm/HIP 平台设计。

## 特性

- 🔧 一键编译系统（Python/C++/全量）
- 🧪 测试运行器（L0/L1 测试）
- 📊 进程管理（查看/终止任务）
- ✅ 环境依赖检查
- 📝 可配置日志系统

## 安装

### 独立安装

```bash
git clone https://github.com/wuyufffan/te-cli.git
cd te-cli
./install.sh
```

### 作为 my_linux_config 的一部分安装

```bash
cd ~/my_linux_config
./install.sh --with-te
```

## 使用方法

```bash
# 首次运行 - 配置 TE 路径
te --help

# 编译命令
te -b -c              # Python 增量编译
te -b -c -d           # Python 全量编译（clean）
te -b -t              # C++ 测试编译
te -b -r              # 重建

# 测试命令
te -0 -c              # L0 C++ 单元测试
te -0 -t              # L0 PyTorch 测试
te -1 -t              # L1 分布式测试

# 进程管理
te -p                 # 查看运行中的任务
te -s                 # 检查环境状态

# 查看日志
te -b -c -l           # 查看编译日志
```

## 配置

配置保存在 `~/.te_config.json`：

```json
{
  "te_path": "/workspace/TransformerEngine"
}
```

## 系统要求

- Python 3.10+
- CMake 3.20+
- Ninja
- AMD ROCm/DTK 25.04.2 或 26.04

## 项目结构

```
te-cli/
├── cli.py              # 命令行入口
├── config_manager.py   # 配置管理
├── install_config.py   # 安装配置
├── logger.py           # 日志系统
├── env_checker.py      # 环境检查
├── build_helpers.py    # 编译功能
├── process_helpers.py  # 进程管理
├── test_helpers.py     # 测试执行
├── utils_helpers.py    # 工具函数
└── common_utils.py     # 系统命令封装
```

## 许可证

MIT License
