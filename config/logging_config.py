#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging configuration for pyanime project.
Provides centralized logging setup with different log levels and handlers.
"""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Create a copy of the record to avoid modifying the original
        record_copy = logging.LogRecord(
            name=record.name,
            level=record.levelno,
            pathname=record.pathname,
            lineno=record.lineno,
            msg=record.msg,
            args=record.args,
            exc_info=record.exc_info,
            func=record.funcName
        )
        
        # Add color to the level name in the copy
        if record_copy.levelname in self.COLORS:
            record_copy.levelname = f"{self.COLORS[record_copy.levelname]}{record_copy.levelname}{self.COLORS['RESET']}"
        
        return super().format(record_copy)


def setup_logging(
    log_level=logging.INFO,
    log_file=None,
    max_file_size=10*1024*1024,  # 10MB
    backup_count=5,
    console_output=False
):
    """
    Setup logging configuration for the pyanime project.
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Path to log file (default: pyanime.log in project root)
        max_file_size: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
        console_output: Whether to output to console (default: False)
    
    Returns:
        logger: Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger('pyanime')
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    colored_formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler with colored output
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(colored_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation (no colors in log file)
    if log_file is None:
        # Get project root directory
        project_root = Path(__file__).parent.parent
        log_file = project_root / 'pyanime.log'
    
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create rotating file handler with clean formatting (no color codes)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)  # Use detailed formatter without colors
    logger.addHandler(file_handler)
    
    # Log the setup
    logger.info("Logging system initialized")
    logger.info("Log level: %s", logging.getLevelName(log_level))
    logger.info("Log file: %s", log_file)
    logger.info("Max file size: %d bytes", max_file_size)
    logger.info("Backup count: %d", backup_count)
    
    return logger


def get_logger(name=None):
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Module name (optional, will use 'pyanime' if not provided)
    
    Returns:
        logger: Logger instance
    """
    if name is None:
        return logging.getLogger('pyanime')
    return logging.getLogger(f'pyanime.{name}')


def log_function_call(logger):
    """
    Decorator to log function calls with parameters and return values.
    
    Args:
        logger: Logger instance to use
    
    Returns:
        decorator: Function decorator
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Log function entry
            logger.debug("Entering function: %s", func.__name__)
            logger.debug("Arguments: args=%s, kwargs=%s", args, kwargs)
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Log successful completion
                logger.debug("Function %s completed successfully", func.__name__)
                logger.debug("Return value: %s", result)
                
                return result
                
            except Exception as e:
                # Log exception
                logger.error("Function %s failed with exception: %s", func.__name__, str(e), exc_info=True)
                raise
        
        return wrapper
    return decorator


def log_performance(logger):
    """
    Decorator to log function performance (execution time).
    
    Args:
        logger: Logger instance to use
    
    Returns:
        decorator: Function decorator
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug("Function %s executed in %.4f seconds", func.__name__, execution_time)
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error("Function %s failed after %.4f seconds: %s", func.__name__, execution_time, str(e), exc_info=True)
                raise
        
        return wrapper
    return decorator


# Initialize default logger
default_logger = setup_logging()


if __name__ == "__main__":
    # Test the logging system
    logger = get_logger("test")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test decorators
    @log_function_call(logger)
    @log_performance(logger)
    def test_function(x, y):
        import time
        time.sleep(0.1)  # Simulate some work
        return x + y
    
    result = test_function(5, 3)
    print(f"Test function result: {result}") 