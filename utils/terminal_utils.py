#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Terminal utilities for pyanime project.
Provides visual decoration and terminal formatting functions.
"""

import sys
import os
import shutil
import textwrap
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.logging_config import get_logger

# Setup logging for this module
logger = get_logger("utils.terminal")


def get_terminal_size():
    """Get terminal size with fallback values."""
    try:
        return shutil.get_terminal_size(fallback=(80, 24))
    except Exception as e:
        logger.warning("Failed to get terminal size: %s, using fallback", str(e))
        return (80, 24)


def separator(char="=", message=None, log_level="info", color=None):
    """
    Create a visual separator line for terminal output.
    
    Args:
        char (str): Character to use for separator (default: "=")
        message (str): Optional message to display in center of separator
        log_level (str): Log level for the separator (debug, info, warning, error)
        color (str): Optional hex color code for the separator
    """
    terminal_size = get_terminal_size()
    separator_line = char * terminal_size.columns
    
    if message:
        # Calculate padding to center the message
        padding = (terminal_size.columns - len(message) - 2) // 2
        if padding > 0:
            separator_line = char * padding + " " + message + " " + char * (terminal_size.columns - padding - len(message) - 2)
        else:
            separator_line = char * 2 + " " + message + " " + char * 2
    
    # Apply color if specified
    if color:
        separator_line = hex_to_rgb(color, separator_line)
    
    # Log the separator creation
    if log_level == "debug":
        logger.debug("Creating separator line with char: %s, length: %d", char, len(separator_line))
    elif log_level == "warning":
        logger.warning("Creating separator line with char: %s, length: %d", char, len(separator_line))
    elif log_level == "error":
        logger.error("Creating separator line with char: %s, length: %d", char, len(separator_line))
    else:
        logger.info("Creating separator line with char: %s, length: %d", char, len(separator_line))
    
    print(separator_line)


def hex_to_rgb(hex_code, text):
    """
    Convert hex color to RGB and apply to text.
    
    Args:
        hex_code (str): Hex color code (e.g., "#ff0000")
        text (str): Text to colorize
    
    Returns:
        str: Colored text with ANSI escape codes
    """
    try:
        hex_code = hex_code.lstrip("#")
        r, g, b = tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
        colored_text = f"\033[38;2;{r};{g};{b}m{text}\033[0m"
        logger.debug("Applied color RGB(%d,%d,%d) to text: %s", r, g, b, text[:50] + "..." if len(text) > 50 else text)
        return colored_text
    except Exception as e:
        logger.warning("Failed to apply color %s to text: %s", hex_code, str(e))
        return text


def wrap_text_with_color(text, hex_color, width):
    """
    Wrap text to specified width and apply color.
    
    Args:
        text (str): Text to wrap and colorize
        hex_color (str): Hex color code
        width (int): Maximum width for wrapping
    
    Returns:
        str: Wrapped and colored text
    """
    if not isinstance(text, str):
        logger.debug("Converting non-string text to string: %s", type(text))
        text = str(text)
    
    wrapped_lines = textwrap.wrap(text, width=width)
    colored_lines = [hex_to_rgb(hex_color, line) for line in wrapped_lines]
    result = "\n".join(colored_lines)
    logger.debug("Wrapped and colored text: %d lines, color: %s", len(wrapped_lines), hex_color)
    return result


def center_text(text, color=None):
    """
    Center text in terminal with optional color.
    
    Args:
        text (str): Text to center
        color (str): Optional hex color code
    
    Returns:
        str: Centered text
    """
    terminal_size = get_terminal_size()
    centered = text.center(terminal_size.columns)
    
    if color:
        centered = hex_to_rgb(color, centered)
    
    logger.debug("Centered text: %s", text[:50] + "..." if len(text) > 50 else text)
    return centered


def print_section_header(title, char="=", color="#00b3ff"):
    """
    Print a section header with separator and title.
    
    Args:
        title (str): Section title
        char (str): Separator character
        color (str): Color for the title
    """
    separator(char, log_level="info")
    print(center_text(title, color))
    separator(char, log_level="info")
    logger.info("Printed section header: %s", title)


def print_success(message, color="#00ff00"):
    """
    Print a success message with green color.
    
    Args:
        message (str): Success message
        color (str): Color for the message (default: green)
    """
    colored_message = hex_to_rgb(color, f"✓ {message}")
    print(colored_message)
    logger.info("Success: %s", message)


def print_error(message, color="#ff0000"):
    """
    Print an error message with red color.
    
    Args:
        message (str): Error message
        color (str): Color for the message (default: red)
    """
    colored_message = hex_to_rgb(color, f"✗ {message}")
    print(colored_message)
    logger.error("Error: %s", message)


def print_warning(message, color="#ffaa00"):
    """
    Print a warning message with yellow color.
    
    Args:
        message (str): Warning message
        color (str): Color for the message (default: yellow)
    """
    colored_message = hex_to_rgb(color, f"⚠ {message}")
    print(colored_message)
    logger.warning("Warning: %s", message)


def print_info(message, color="#00b3ff"):
    """
    Print an info message with blue color.
    
    Args:
        message (str): Info message
        color (str): Color for the message (default: blue)
    """
    colored_message = hex_to_rgb(color, f"ℹ {message}")
    print(colored_message)
    logger.info("Info: %s", message)


def create_progress_bar(current, total, width=50, color="#00ff00"):
    """
    Create a progress bar.
    
    Args:
        current (int): Current progress value
        total (int): Total value
        width (int): Width of progress bar
        color (str): Color for the progress bar
    
    Returns:
        str: Progress bar string
    """
    if total == 0:
        return ""
    
    progress = int((current / total) * width)
    bar = "█" * progress + "░" * (width - progress)
    percentage = int((current / total) * 100)
    
    progress_text = f"[{bar}] {percentage}%"
    colored_progress = hex_to_rgb(color, progress_text)
    
    logger.debug("Created progress bar: %d/%d (%d%%)", current, total, percentage)
    return colored_progress


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')
    logger.debug("Cleared terminal screen")


def print_table_with_colors(data, headers, colors=None, tablefmt="grid"):
    """
    Print a table with colored headers and data.
    
    Args:
        data (list): Table data
        headers (list): Table headers
        colors (dict): Color mapping for columns
        tablefmt (str): Table format
    """
    try:
        from tabulate import tabulate
        
        # Apply colors if specified
        if colors:
            colored_data = []
            for row in data:
                colored_row = []
                for i, cell in enumerate(row):
                    if i < len(headers) and headers[i] in colors:
                        colored_row.append(hex_to_rgb(colors[headers[i]], str(cell)))
                    else:
                        colored_row.append(str(cell))
                colored_data.append(colored_row)
        else:
            colored_data = [[str(cell) for cell in row] for row in data]
        
        table = tabulate(colored_data, headers=headers, tablefmt=tablefmt)
        print(table)
        logger.debug("Printed table with %d rows and %d columns", len(data), len(headers))
        
    except ImportError:
        logger.error("tabulate module not available for table formatting")
        # Fallback to simple table
        for header in headers:
            print(f"{header:<20}", end="")
        print()
        print("-" * (20 * len(headers)))
        for row in data:
            for cell in row:
                print(f"{str(cell):<20}", end="")
            print()


if __name__ == "__main__":
    # Test the terminal utilities
    logger.info("Testing terminal utilities")
    
    print_section_header("Terminal Utilities Test", "=", "#00b3ff")
    
    print_info("This is an info message")
    print_success("This is a success message")
    print_warning("This is a warning message")
    print_error("This is an error message")
    
    separator("-", "Progress Test", "info")
    for i in range(0, 101, 10):
        progress = create_progress_bar(i, 100, 30, "#00ff00")
        print(f"\rProgress: {progress}", end="", flush=True)
        import time
        time.sleep(0.1)
    print()
    
    separator("=", "Test Complete", "info") 