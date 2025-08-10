# Pyanime Terminal Decoration & Separator System

## Overview
Enhanced the pyanime project with a comprehensive terminal decoration system that provides beautiful visual separators, colored output, and better user experience while maintaining full logging integration.

## ✅ Enhanced Features

### 1. Improved Separator Function
- **Location**: `pyanime/bin/pyanime.py` (enhanced existing function)
- **Features**:
  - **Message Support**: Can display centered messages within separators
  - **Logging Integration**: Different log levels for different separator types
  - **Color Support**: Optional color coding for separators
  - **Dynamic Width**: Automatically adjusts to terminal width
  - **Multiple Characters**: Supports any character for separators

### 2. New Terminal Utilities Module
- **Location**: `pyanime/utils/terminal_utils.py` (new file)
- **Features**:
  - **Section Headers**: Complete section headers with separators and titles
  - **Status Messages**: Colored success, error, warning, and info messages
  - **Progress Bars**: Animated progress bars with color support
  - **Table Formatting**: Enhanced table display with color support
  - **Text Utilities**: Color conversion, text wrapping, and centering

### 3. Visual Enhancements

#### Separator Examples
```python
# Basic separator
separator('=')

# Separator with message
separator('=', "Welcome to pyanime (v1.0.0)", "info")

# Colored separator
separator('=', "Download Complete", "info", "#00ff00")

# Warning separator
separator('=', "Error Occurred", "error")
```

#### Status Messages
```python
print_success("Download completed successfully")
print_error("Failed to connect to server")
print_warning("Using fallback server")
print_info("Processing episode 1 of 12")
```

#### Progress Bars
```python
progress = create_progress_bar(current=50, total=100, width=30, color="#00ff00")
print(f"Download: {progress}")
```

## 🎨 Visual Improvements

### 1. Enhanced User Interface
- **Welcome Screen**: Centered title with decorative separators
- **Section Headers**: Clear visual separation between different parts of the application
- **Status Indicators**: Color-coded messages for different types of information
- **Progress Tracking**: Visual progress bars for long operations

### 2. Color Scheme
- **Success**: Green (`#00ff00`) - ✓
- **Error**: Red (`#ff0000`) - ✗
- **Warning**: Yellow (`#ffaa00`) - ⚠
- **Info**: Blue (`#00b3ff`) - ℹ
- **Anime Titles**: Light Blue (`#00b3ff`)
- **Episode Numbers**: Yellow (`#ffea00`)
- **Download Status**: Orange (`#fc861e`)

### 3. Separator Types
- **Section Separators**: `=` for major sections
- **Subsection Separators**: `-` for subsections
- **Warning Separators**: `!` for warnings
- **Error Separators**: `X` for errors
- **Custom Separators**: Any character supported

## 📊 Logging Integration

### 1. Separator Logging
- **Info Level**: Standard section separators
- **Warning Level**: Warning and error separators
- **Debug Level**: Detailed separator creation logging
- **Error Level**: Error-related separators

### 2. Visual-Log Correlation
- **Console**: Beautiful colored output with separators
- **Log File**: Clean, detailed log entries without color codes
- **Correlation**: Easy to match console output with log entries

## 🔧 Technical Implementation

### 1. Enhanced Separator Function
```python
def separator(char="=", message=None, log_level="info", color=None):
    """
    Create a visual separator line for terminal output.
    
    Args:
        char (str): Character to use for separator (default: "=")
        message (str): Optional message to display in center of separator
        log_level (str): Log level for the separator (debug, info, warning, error)
        color (str): Optional hex color code for the separator
    """
```

### 2. Terminal Utilities
- **get_terminal_size()**: Safe terminal size detection
- **hex_to_rgb()**: Color conversion with error handling
- **center_text()**: Text centering with optional colors
- **print_section_header()**: Complete section headers
- **create_progress_bar()**: Animated progress bars

### 3. Error Handling
- **Graceful Fallbacks**: Fallback values for terminal size detection
- **Color Error Handling**: Graceful handling of invalid color codes
- **Import Error Handling**: Fallback table formatting without tabulate

## 📁 Files Modified/Created

### New Files
1. `pyanime/utils/terminal_utils.py` - Comprehensive terminal utilities

### Modified Files
1. `pyanime/bin/pyanime.py` - Enhanced separator function and visual improvements

## 🎯 Benefits Achieved

### 1. User Experience
- **Visual Clarity**: Clear separation between different sections
- **Status Awareness**: Immediate visual feedback for operations
- **Progress Tracking**: Visual progress indicators for long operations
- **Professional Appearance**: Polished, modern terminal interface

### 2. Developer Experience
- **Easy Integration**: Simple function calls for visual elements
- **Consistent Styling**: Standardized color scheme and formatting
- **Logging Integration**: Full logging support for all visual elements
- **Maintainable Code**: Centralized terminal utilities

### 3. Debugging & Monitoring
- **Visual-Log Correlation**: Easy to match console output with logs
- **Status Tracking**: Clear visual indicators for different states
- **Error Visibility**: Prominent error messages and separators
- **Progress Monitoring**: Visual progress tracking for operations

## 🚀 Usage Examples

### Basic Usage
```python
from utils.terminal_utils import separator, print_success, print_error

# Simple separator
separator('=')

# Separator with message
separator('=', "Download Complete", "info")

# Status messages
print_success("File downloaded successfully")
print_error("Connection failed")
```

### Advanced Usage
```python
from utils.terminal_utils import print_section_header, create_progress_bar

# Section header
print_section_header("Episode Download", "=", "#00b3ff")

# Progress bar
for i in range(0, 101, 10):
    progress = create_progress_bar(i, 100, 30, "#00ff00")
    print(f"\rProgress: {progress}", end="", flush=True)
```

## 📈 Performance Impact
- **Minimal Overhead**: Efficient terminal size detection
- **Lazy Evaluation**: Colors only applied when needed
- **Memory Efficient**: No unnecessary string operations
- **Fast Rendering**: Optimized for real-time display

## 🔮 Future Enhancements
- **Animated Separators**: Moving separator effects
- **Custom Themes**: User-configurable color schemes
- **Interactive Elements**: Clickable terminal elements
- **Export Options**: Save terminal output to files
- **Accessibility**: High contrast and screen reader support

The terminal decoration system provides a professional, user-friendly interface while maintaining full logging integration and performance. The enhanced separators and visual elements make the pyanime application more intuitive and enjoyable to use. 