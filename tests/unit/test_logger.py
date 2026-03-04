import logging
from unittest.mock import MagicMock, patch

import pytest

from core.logger import ColoredFormatter, LogContext, get_logger, setup_logging


@patch("sys.stderr.isatty", return_value=True)
def test_colored_formatter_with_color(mock_isatty):
    formatter = ColoredFormatter(fmt="%(levelname)s: %(message)s", use_color=True)
    record = logging.LogRecord(name="x", level=logging.ERROR, pathname=__file__, lineno=1, msg="oops", args=(), exc_info=None)

    formatted = formatter.format(record)

    # 应包含颜色码，且原 levelname 已恢复
    from config import RED, RESET  # noqa: WPS433 (test import)
    assert RED in formatted and RESET in formatted
    assert "ERROR" in formatted
    assert record.levelname == "ERROR"


@patch("sys.stderr.isatty", return_value=False)
def test_colored_formatter_no_color(mock_isatty):
    formatter = ColoredFormatter(fmt="%(levelname)s: %(message)s", use_color=True)
    record = logging.LogRecord(name="x", level=logging.WARNING, pathname=__file__, lineno=1, msg="warn", args=(), exc_info=None)

    formatted = formatter.format(record)

    assert "\033" not in formatted  # 无颜色
    assert "WARNING" in formatted
    assert record.levelname == "WARNING"


def test_colored_formatter_use_color_false():
    formatter = ColoredFormatter(fmt="%(levelname)s: %(message)s", use_color=False)
    record = logging.LogRecord(name="x", level=logging.INFO, pathname=__file__, lineno=1, msg="info", args=(), exc_info=None)

    formatted = formatter.format(record)

    assert "\033" not in formatted
    assert "INFO" in formatted
    assert record.levelname == "INFO"


def test_setup_logging_console_only():
    root_logger = logging.getLogger()
    root_logger.handlers = [logging.NullHandler()]  # 放一个占位，确保会被清空

    logger = setup_logging(level=logging.DEBUG, use_color=False, log_file=None)

    assert logger is root_logger
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 1

    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.level == logging.DEBUG
    assert isinstance(handler.formatter, ColoredFormatter)
    assert handler.formatter.use_color is False


def test_setup_logging_with_file(tmp_path):
    log_path = tmp_path / "out.log"

    logger = setup_logging(level=logging.INFO, use_color=False, log_file=str(log_path))

    assert logger.level == logging.INFO
    # 控制台 + 文件
    assert len(logger.handlers) == 2
    stream_handler = logger.handlers[0]
    file_handler = logger.handlers[1]

    assert isinstance(stream_handler, logging.StreamHandler)
    assert isinstance(file_handler, logging.FileHandler)
    assert file_handler.baseFilename == str(log_path)


def test_get_logger():
    name = "my.logger"
    logger = get_logger(name)
    assert logger is logging.getLogger(name)


def test_log_context_success():
    logger = MagicMock()
    with LogContext(logger, "task", level=logging.INFO):
        logger.do_work = MagicMock()
        logger.do_work()

    logger.log.assert_any_call(logging.INFO, "开始: task")
    logger.log.assert_any_call(logging.INFO, "完成: task")


def test_log_context_failure():
    logger = MagicMock()
    with pytest.raises(ValueError):
        with LogContext(logger, "task", level=logging.INFO):
            raise ValueError("boom")

    logger.log.assert_any_call(logging.INFO, "开始: task")
    logger.error.assert_any_call("失败: task - boom")
