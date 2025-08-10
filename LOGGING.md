# Pyanime Logging System

This document describes the comprehensive logging system implemented in the pyanime project.

## Overview

The logging system provides detailed tracking of all operations in the pyanime application, including:
- User interactions
- Network requests and responses
- File operations
- Error handling
- Performance metrics
- Function calls and return values

## Features

### 1. Centralized Configuration
- **File**: `config/logging_config.py`
- **Features**:
  - Colored console output
  - Rotating file logs (10MB max, 5 backups)
  - Detailed file logging with timestamps
  - Module-specific loggers
  - Performance tracking decorators

### 2. Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about program execution
- **WARNING**: Warning messages for potentially problematic situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical errors that may prevent the program from running

### 3. Log Output
- **Console**: Colored output for immediate feedback
- **File**: Detailed logs saved to `pyanime.log` in the project root
- **Rotation**: Automatic log rotation to prevent large files

## Usage

### Basic Logging
```python
from config.logging_config import get_logger

# Get a logger for your module
logger = get_logger("your.module.name")

# Log messages
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error")
```

### Function Decorators
```python
from config.logging_config import log_function_call, log_performance

@log_function_call(logger)
@log_performance(logger)
def your_function(param1, param2):
    # Function code here
    return result
```

### Module-Specific Loggers
```python
# Different loggers for different modules
scraper_logger = get_logger("scraper.searchAnimedetails")
downloader_logger = get_logger("downloader.hd2")
config_logger = get_logger("config.hianime")
```

## Log File Structure

The log file (`pyanime.log`) contains detailed information in the following format:

```
2024-01-15 10:30:45 - pyanime.main - INFO - Starting pyanime application
2024-01-15 10:30:46 - pyanime.scraper.searchAnimedetails - INFO - Searching for anime: Naruto
2024-01-15 10:30:47 - pyanime.scraper.searchAnimedetails - DEBUG - Making request to: https://hianime.bz/search?keyword=Naruto
2024-01-15 10:30:48 - pyanime.scraper.searchAnimedetails - INFO - Found 5 anime blocks in search results
```

## Configuration

### Log Level
Set the log level in `config/logging_config.py`:
```python
# For development (detailed logging)
logger = setup_logging(log_level=logging.DEBUG)

# For production (less verbose)
logger = setup_logging(log_level=logging.INFO)
```

### File Rotation
Configure log file rotation:
```python
logger = setup_logging(
    max_file_size=10*1024*1024,  # 10MB
    backup_count=5,               # Keep 5 backup files
    log_file="custom_log.log"     # Custom log file name
)
```

## Modules with Logging

### 1. Main Application (`bin/pyanime.py`)
- User interactions
- Search operations
- Episode selection
- Download progress

### 2. Scraper Modules
- **`searchAnimedetails.py`**: Anime search and details extraction
- **`searchEpisodedetails.py`**: Episode list extraction
- **`getEpisodestreams.py`**: Stream extraction and processing
- **`tokenextractor.py`**: Token extraction for authentication

### 3. Downloader Module (`Downloader/hd2.py`)
- M3U8 parsing
- Media downloading
- File operations
- Error handling

### 4. Configuration (`config/hianime.py`)
- Configuration loading
- Settings validation

## Testing

Run the logging test script to verify the system:
```bash
cd pyanime
python test_logging.py
```

This will test:
- Basic logging functionality
- Module-specific loggers
- Decorator functionality
- Error logging
- Performance tracking

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in the Python path
2. **Permission Errors**: Check write permissions for the log directory
3. **Large Log Files**: Adjust rotation settings in the configuration

### Debug Mode

Enable debug logging for detailed troubleshooting:
```python
logger = setup_logging(log_level=logging.DEBUG)
```

### Log Analysis

The logs can be analyzed to:
- Track user behavior patterns
- Identify performance bottlenecks
- Debug network issues
- Monitor error rates
- Optimize download processes

## Best Practices

1. **Use Appropriate Log Levels**:
   - DEBUG for detailed troubleshooting
   - INFO for general flow
   - WARNING for potential issues
   - ERROR for actual problems

2. **Include Context**:
   ```python
   logger.info("Processing episode %d/%d: %s", episode_num, total_episodes, episode_title)
   ```

3. **Handle Exceptions**:
   ```python
   try:
       # Your code
   except Exception as e:
       logger.error("Operation failed: %s", str(e), exc_info=True)
   ```

4. **Use Decorators for Performance**:
   ```python
   @log_performance(logger)
   def expensive_operation():
       # Your code
   ```

## Log File Location

- **Default**: `pyanime.log` in the project root
- **Backup Files**: `pyanime.log.1`, `pyanime.log.2`, etc.
- **Custom Location**: Can be specified in the configuration

## Performance Impact

The logging system is designed to be lightweight:
- Asynchronous file writing
- Efficient string formatting
- Minimal overhead in production mode
- Optional debug logging

## Future Enhancements

Potential improvements:
- Remote logging to external services
- Structured logging (JSON format)
- Log aggregation and analysis tools
- Real-time log monitoring
- Custom log formatters for different outputs 