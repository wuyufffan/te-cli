# te-cli

TransformerEngine (TE) Development Toolkit for AMD ROCm/HIP Platform.

## Features

- 🔧 One-command build system (Python/C++/Full)
- 🧪 Test runner (L0/L1 tests)
- 📊 Process management (view/kill tasks)
- ✅ Environment dependency checking
- 📝 Configurable logging system

## Installation

### Standalone Installation

```bash
git clone https://github.com/wuyufffan/te-cli.git
cd te-cli
pip install -e .  # or ./install.sh
```

### As Part of my_linux_config

```bash
cd ~/my_linux_config
./install.sh --with-te
```

## Usage

```bash
# First run - configure TE_PATH
te --help

# Build commands
te -b -c              # Build Python (incremental)
te -b -c -d           # Build Python (clean)
te -b -t              # Build C++ tests
te -b -r              # Rebuild

# Test commands
te -0 -c              # L0 C++ unit tests
te -0 -t              # L0 PyTorch tests
te -1 -t              # L1 distributed tests

# Process management
te -p                 # View running tasks
te -s                 # Check environment status

# View logs
te -b -c -l           # View build log
```

## Configuration

Configuration is stored in `~/.te_config.json`:

```json
{
  "te_path": "/workspace/TransformerEngine"
}
```

## Requirements

- Python 3.10+
- CMake 3.20+
- Ninja
- AMD ROCm/DTK 25.04.2 or 26.04

## Structure

```
te-cli/
├── cli.py              # CLI entry point
├── config_manager.py   # Configuration management
├── install_config.py   # Installation configuration
├── logger.py           # Logging system
├── env_checker.py      # Environment checking
├── build_helpers.py    # Build functionality
├── process_helpers.py  # Process management
├── test_helpers.py     # Test execution
├── utils_helpers.py    # Utility functions
└── common_utils.py     # System command wrappers
```

## License

MIT License
