from __future__ import annotations

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any

from config.constants import resource_path


# ================= Structured Logger =================

class StructuredLogger:
    """Enhanced logger with structured output and file rotation."""

    def __init__(self, name: str = "api_tester", log_dir: str = "logs") -> None:
        self.name = name
        self.log_dir = resource_path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        self._setup_console_handler()
        self._setup_file_handler()
        self._setup_json_handler()
        self._setup_error_handler()

    def _setup_console_handler(self) -> None:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)

    def _setup_file_handler(self) -> None:
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        ))
        self.logger.addHandler(handler)

    def _setup_json_handler(self) -> None:
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}_structured.jsonl",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)

    def _setup_error_handler(self) -> None:
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}_errors.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setLevel(logging.ERROR)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n'
            'Exception: %(exc_info)s\n---'
        ))
        self.logger.addHandler(handler)

    def debug(self, message: str, **kwargs: Any) -> None:
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        self.logger.critical(message, extra=kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        self.logger.exception(message, extra=kwargs)

    def log_request(self, method: str, url: str, status_code: int,
                    response_time: float, **kwargs: Any) -> None:
        self.info(
            f"HTTP {method} {url} - {status_code} - {response_time:.3f}s",
            request_method=method,
            request_url=url,
            response_status=status_code,
            response_time=response_time,
            **kwargs,
        )

    def log_preset_action(self, action: str, preset_name: str, **kwargs: Any) -> None:
        self.info(f"Preset {action}: {preset_name}", action=action,
                  preset_name=preset_name, **kwargs)

    def log_user_action(self, action: str, **kwargs: Any) -> None:
        self.debug(f"User action: {action}", user_action=action, **kwargs)

    def log_application_event(self, event: str, **kwargs: Any) -> None:
        self.info(f"Application event: {event}", app_event=event, **kwargs)


# ================= Custom Formatters =================

class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            entry["stack_trace"] = record.stack_info

        _skip = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "lineno", "funcName", "created", "msecs",
            "relativeCreated", "thread", "threadName", "processName",
            "process", "getMessage", "exc_info", "exc_text", "stack_info",
            "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in _skip:
                entry[key] = value

        return json.dumps(entry, default=str)


# ================= Logging Manager =================

class LoggingManager:
    def __init__(self) -> None:
        self.loggers: dict[str, StructuredLogger] = {}
        logging.getLogger().setLevel(logging.INFO)

    def get_logger(self, name: str) -> StructuredLogger:
        if name not in self.loggers:
            self.loggers[name] = StructuredLogger(name)
        return self.loggers[name]

    def set_global_level(self, level: str) -> None:
        log_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        for logger in self.loggers.values():
            logger.logger.setLevel(log_level)

    def cleanup(self) -> None:
        for logger in self.loggers.values():
            for handler in logger.logger.handlers:
                handler.close()
            logger.logger.handlers.clear()


_logging_manager = LoggingManager()


def get_logger(name: str = "api_tester") -> StructuredLogger:
    return _logging_manager.get_logger(name)


def set_logging_level(level: str) -> None:
    _logging_manager.set_global_level(level)


def cleanup_logging() -> None:
    _logging_manager.cleanup()
