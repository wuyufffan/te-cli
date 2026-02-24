# te-cli

TransformerEngine (TE) 开发工具集，专为 AMD ROCm/HIP 平台设计。

## 功能特性

- **编译构建**：支持 Python 和 C++ 的增量/全量编译、智能重建
- **测试运行**：支持 L0/L1 级别测试（C++、PyTorch、分布式）
- **进程管理**：查看运行中的任务、查看日志、终止任务
- **环境检查**：自动检测 TE 环境依赖

## 快速开始

```bash
# 首次运行配置 TE 路径
te --help

# 查看所有可用命令
te -h
```

## 安装

### 独立安装

```bash
git clone https://github.com/wuyufffan/te-cli.git
cd te-cli
./install.sh
```

### 作为 my_linux_config 的一部分

```bash
cd ~/my_linux_config
./install.sh --with-te
```

## 配置

配置文件保存在 `~/.te_config.json`：

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
├── core/               # 核心代码
│   ├── cli.py         # 命令行入口
│   ├── build_helpers.py
│   ├── test_helpers.py
│   └── ...
├── tests/              # 测试套件
│   ├── unit/
│   └── integration/
├── install.sh          # 安装脚本
└── README.md
```

## 许可证

MIT License
