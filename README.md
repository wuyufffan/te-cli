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
te --version     # 查看版本
te --check-env   # 检查环境依赖

# 构建
te -b -c         # Python 构建
te -b -t         # C++ 构建

# 测试
te -0 -t         # L0 测试
te -1 -t         # L1 测试

# 任务/日志
te -p            # 查看任务
te -p -l         # 查看日志
```

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
