#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the logging system.
This script tests all the logging functionality to ensure it's working correctly.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config.logging_config import setup_logging, get_logger, log_function_call, log_performance


def test_basic_logging():
    """Test basic logging functionality."""
    print("Testing basic logging...")
    
    # Setup logging
    logger = setup_logging(log_level=10, console_output=True)  # DEBUG level
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    print("Basic logging test completed.\n")


def test_module_logging():
    """Test module-specific logging."""
    print("Testing module logging...")
    
    # Test different module loggers
    scraper_logger = get_logger("scraper.test")
    downloader_logger = get_logger("downloader.test")
    config_logger = get_logger("config.test")
    
    scraper_logger.info("Scraper module test message")
    downloader_logger.info("Downloader module test message")
    config_logger.info("Config module test message")
    
    print("Module logging test completed.\n")


@log_function_call(get_logger("test"))
@log_performance(get_logger("test"))
def test_decorated_function(x, y):
    """Test function with logging decorators."""
    import time
    time.sleep(0.1)  # Simulate some work
    return x + y


def test_decorators():
    """Test logging decorators."""
    print("Testing logging decorators...")
    
    result = test_decorated_function(5, 3)
    print(f"Decorated function result: {result}")
    
    print("Decorator test completed.\n")


def test_error_logging():
    """Test error logging."""
    print("Testing error logging...")
    
    logger = get_logger("test.errors")
    
    try:
        # Intentionally cause an error
        result = 1 / 0
    except Exception as e:
        logger.error("Caught an exception: %s", str(e), exc_info=True)
    
    print("Error logging test completed.\n")


def main():
    """Run all logging tests."""
    print("=" * 50)
    print("PYANIME LOGGING SYSTEM TEST")
    print("=" * 50)
    
    test_basic_logging()
    test_module_logging()
    test_decorators()
    test_error_logging()
    
    print("=" * 50)
    print("All tests completed!")
    print("Check the log file for detailed output.")
    print("=" * 50)


if __name__ == "__main__":
    main() 