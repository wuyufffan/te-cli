import json
import logging
import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

import core.config_manager as cm
from core.config_manager import Config, get_config, init_config

def test_config_post_init():
    with patch('os.environ.get') as mock_env_get:
        # Test override base
        mock_env_get.side_effect = lambda k, d=None: '/my/test/dtk' if k == 'DTK_BASE' else d
        with patch('os.path.isdir') as mock_isdir:
            mock_isdir.side_effect = lambda p: p == '/my/test/dtk'
            config = Config()
            assert config.dtk_base == "/my/test/dtk"

        # Test dtk 26
        mock_env_get.side_effect = lambda k, d=None: None if k == 'DTK_BASE' else d
        with patch('os.path.isdir') as mock_isdir:
            mock_isdir.side_effect = lambda p: p == '/opt/dtk-26.04'
            config = Config()
            assert config.dtk_base == "/opt/dtk-26.04"

        # Test /opt/dtk and realpath
        with patch('os.path.isdir') as mock_isdir, patch('os.path.realpath') as mock_realpath:
            mock_isdir.side_effect = lambda p: p == '/opt/dtk'
            mock_realpath.return_value = '/opt/dtk-resolved'
            config = Config()
            assert config.dtk_base == "/opt/dtk-resolved"

        # Test default base
        with patch('os.path.isdir') as mock_isdir:
            mock_isdir.side_effect = lambda p: p == '/opt/dtk-25.04.2'
            config = Config()
            assert config.dtk_base == "/opt/dtk-25.04.2"

        # Test no matching base
        with patch('os.path.isdir') as mock_isdir:
            mock_isdir.return_value = False
            config = Config()
            assert config.dtk_base == "/opt/dtk-25.04.2" # default value when not overriden

def test_config_log_level_int():
    config = Config(log_level='DEBUG')
    assert config.log_level_int == logging.DEBUG
    
    config = Config(log_level='UNKNOWN_LEVEL')
    assert config.log_level_int == logging.INFO  # Fallback to INFO

@patch('socket.gethostname', return_value='test-host')
def test_config_log_files(mock_gethostname):
    config = Config(te_path='/my/te')
    log_files = config.log_files
    
    assert log_files['build_py'] == '/my/te/build_python_test-host.log'
    assert log_files['build_cpp'] == '/my/te/build_cpp_test-host.log'
    assert log_files['rebuild'] == '/my/te/rebuild_dev_test-host.log'
    assert log_files['build_all'] == '/my/te/build_all_test-host.log'
    assert log_files['l0cpp'] == '/my/te/L0_cppunittest_test-host.log'
    assert log_files['l0torch'] == '/my/te/L0_pytorch_unittest_test-host.log'
    assert log_files['l1torch'] == '/my/te/L1_pytorch_distributed_unittest_test-host.log'

def test_config_get_init_script():
    # When te_init_script is set
    config = Config(te_init_script='/my/init.sh')
    assert config.get_init_script() == '/my/init.sh'
    
    # When te_init_script is empty, it should default to a path relative to the config file
    config = Config()
    config.te_init_script = ''
    script_path = config.get_init_script()
    assert script_path.endswith('te_init.sh')
    assert 'core' in script_path


def test_config_validate_success(tmp_path):
    cfg = Config(te_path=str(tmp_path), dtk_base=str(tmp_path / "dtk"))
    with patch('os.path.isdir') as mock_isdir, patch('os.path.isfile') as mock_isfile:
        mock_isdir.side_effect = lambda p: p in (cfg.te_path, cfg.dtk_base)
        mock_isfile.return_value = True
        ok, errors = cfg.validate()
    assert ok is True
    assert errors == []


def test_config_validate_failures(tmp_path):
    cfg = Config(te_path=str(tmp_path / "missing_te"), dtk_base=str(tmp_path / "missing_dtk"))
    with patch('os.path.isdir', return_value=False), patch('os.path.isfile', return_value=False):
        ok, errors = cfg.validate()
    assert ok is False
    # Expect three error messages for TE path, DTK, init script
    assert len(errors) == 3
    assert any("TE_PATH" in e for e in errors)
    assert any("DTK" in e for e in errors)
    assert any("初始化脚本" in e for e in errors)


def test_config_from_file_when_exists(tmp_path):
    cfg_path = tmp_path / "cfg.json"
    data = {
        "te_path": "/custom/te",
        "work_space": "/custom/work",
        "te_init_script": "/custom/init.sh",
        "log_level": "DEBUG",
    }
    cfg_path.write_text(json.dumps(data), encoding='utf-8')

    cfg = Config.from_file(str(cfg_path))
    assert cfg.te_path == data["te_path"]
    assert cfg.work_space == data["work_space"]
    assert cfg.te_init_script == data["te_init_script"]
    assert cfg.log_level == data["log_level"]


def test_config_from_file_missing(tmp_path):
    cfg_path = tmp_path / "missing.json"
    cfg = Config.from_file(str(cfg_path))
    # Should fall back to defaults
    assert cfg.te_path == os.environ.get('TE_PATH', '/workspace/TransformerEngine')


def test_config_from_file_load_error(tmp_path, caplog):
    cfg_path = tmp_path / "bad.json"
    cfg_path.write_text("not-json", encoding='utf-8')
    with caplog.at_level(logging.WARNING):
        cfg = Config.from_file(str(cfg_path))
    assert any("加载配置文件失败" in rec.message for rec in caplog.records)
    assert cfg.te_path == os.environ.get('TE_PATH', '/workspace/TransformerEngine')


def test_config_save_success(tmp_path):
    cfg_path = tmp_path / "out.json"
    cfg = Config(te_path="/save/te", work_space="/save/work", te_init_script="/save/init.sh", log_level="DEBUG")
    cfg.save(str(cfg_path))
    saved = json.loads(cfg_path.read_text(encoding='utf-8'))
    assert saved["te_path"] == "/save/te"
    assert saved["work_space"] == "/save/work"
    assert saved["te_init_script"] == "/save/init.sh"
    assert saved["log_level"] == "DEBUG"


def test_config_save_error(caplog):
    cfg = Config(te_path="/save/te")
    with patch('builtins.open', side_effect=IOError("disk full")), caplog.at_level(logging.ERROR):
        cfg.save("/cannot/write.json")
    assert any("保存配置失败" in rec.message for rec in caplog.records)


def test_get_config_singleton(monkeypatch):
    # Reset singleton
    monkeypatch.setattr(cm, '_config', None, raising=True)
    sentinel_cfg = Config(te_path="/singleton")
    with patch.object(Config, 'from_file', return_value=sentinel_cfg) as mock_from_file:
        first = get_config()
        second = get_config()
    assert first is second is sentinel_cfg
    mock_from_file.assert_called_once()


def test_init_config_sets_level(monkeypatch):
    monkeypatch.setattr(cm, '_config', None, raising=True)
    with patch.object(Config, 'from_file', return_value=Config(log_level='WARNING')) as mock_from_file, \
         patch('logging.getLogger') as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        cfg = init_config()
    assert cfg.log_level == 'WARNING'
    mock_from_file.assert_called_once()
    mock_logger.setLevel.assert_called_once_with(cfg.log_level_int)