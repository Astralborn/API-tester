from __future__ import annotations

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from constants import resource_path


# ================= Structured Logger =================

class StructuredLogger:
    """Enhanced logger with structured output and file rotation."""
    
    def __init__(self, name: str = "api_tester", log_dir: str = "logs") -> None:
        self.name = name
        self.log_dir = Path(resource_path(log_dir))
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_console_handler()
        self._setup_file_handler()
        self._setup_json_handler()
        self._setup_error_handler()
    
    def _setup_console_handler(self) -> None:
        """Setup console handler with colored output."""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Custom formatter for console
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self) -> None:
        """Setup rotating file handler for general logs."""
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def _setup_json_handler(self) -> None:
        """Setup JSON structured log handler."""
        json_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}_structured.jsonl",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(json_handler)
    
    def _setup_error_handler(self) -> None:
        """Setup dedicated error log handler."""
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}_errors.log",
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n'
            'Exception: %(exc_info)s\n'
            'Stack Trace: %(stack_info)s\n'
            '---'
        )
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with optional structured data."""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message with optional structured data."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with optional structured data."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message with optional structured data."""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with optional structured data."""
        self.logger.critical(message, extra=kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)
    
    def log_request(self, method: str, url: str, status_code: int, 
                   response_time: float, **kwargs) -> None:
        """Log HTTP request details."""
        self.info(
            f"HTTP {method} {url} - {status_code} - {response_time:.3f}s",
            request_method=method,
            request_url=url,
            response_status=status_code,
            response_time=response_time,
            **kwargs
        )
    
    def log_preset_action(self, action: str, preset_name: str, **kwargs) -> None:
        """Log preset management actions."""
        self.info(
            f"Preset {action}: {preset_name}",
            action=action,
            preset_name=preset_name,
            **kwargs
        )
    
    def log_user_action(self, action: str, **kwargs) -> None:
        """Log user interface actions."""
        self.debug(
            f"User action: {action}",
            user_action=action,
            **kwargs
        )
    
    def log_application_event(self, event: str, **kwargs) -> None:
        """Log application lifecycle events."""
        self.info(
            f"Application event: {event}",
            app_event=event,
            **kwargs
        )


# ================= Custom Formatters =================

class ColoredFormatter(logging.Formatter):
    """Console formatter with colors for different log levels."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{level_color}{record.levelname}{self.RESET}"
        
        return super().format(record)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add stack trace if present
        if record.stack_info:
            log_entry['stack_trace'] = record.stack_info
        
        # Add any extra fields from the log record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                          'pathname', 'filename', 'module', 'lineno', 
                          'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process',
                          'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


# ================= Logging Manager =================

class LoggingManager:
    """Centralized logging management for the application."""
    
    def __init__(self) -> None:
        self.loggers: Dict[str, StructuredLogger] = {}
        self._setup_root_logger()
    
    def _setup_root_logger(self) -> None:
        """Setup root logger configuration."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
    
    def get_logger(self, name: str) -> StructuredLogger:
        """Get or create a structured logger."""
        if name not in self.loggers:
            self.loggers[name] = StructuredLogger(name)
        return self.loggers[name]
    
    def set_global_level(self, level: str) -> None:
        """Set global logging level."""
        log_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        
        # Update all existing loggers
        for logger in self.loggers.values():
            logger.logger.setLevel(log_level)
    
    def cleanup(self) -> None:
        """Cleanup logging resources."""
        for logger in self.loggers.values():
            for handler in logger.logger.handlers:
                handler.close()
            logger.logger.handlers.clear()


# Global logging manager
_logging_manager = LoggingManager()


def get_logger(name: str = "api_tester") -> StructuredLogger:
    """Get the global structured logger."""
    return _logging_manager.get_logger(name)


def set_logging_level(level: str) -> None:
    """Set global logging level."""
    _logging_manager.set_global_level(level)


def cleanup_logging() -> None:
    """Cleanup logging resources."""
    _logging_manager.cleanup()
