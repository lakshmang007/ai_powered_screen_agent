"""
Utility functions and helpers for the AI-Powered Screen Agent.
"""

import os
import json
import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import configparser

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        
    Returns:
        Configured logger
    """
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            # Ensure UTF-8 for file handler to avoid encoding errors with non-ASCII
            logging.FileHandler(log_file, encoding='utf-8') if log_file else logging.NullHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def load_config(config_path: str = "config/config.ini") -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    config = configparser.ConfigParser()
    
    # Default configuration
    default_config = {
        'screen_agent': {
            'screenshot_interval': '0.5',
            'confidence_threshold': '0.8',
            'max_retries': '3'
        },
        'voice': {
            'timeout': '5',
            'phrase_timeout': '1.0',
            'energy_threshold': '300'
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/screen_agent.log'
        }
    }
    
    # Load from file if exists
    if os.path.exists(config_path):
        config.read(config_path)
    else:
        # Create default config file
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        for section, options in default_config.items():
            config.add_section(section)
            for key, value in options.items():
                config.set(section, key, value)
        
        with open(config_path, 'w') as f:
            config.write(f)
    
    # Convert to dictionary
    result = {}
    for section in config.sections():
        result[section] = dict(config.items(section))
    
    return result

def save_config(config_data: Dict[str, Any], config_path: str = "config/config.ini"):
    """
    Save configuration to file.
    
    Args:
        config_data: Configuration dictionary
        config_path: Path to configuration file
    """
    config = configparser.ConfigParser()
    
    for section, options in config_data.items():
        config.add_section(section)
        for key, value in options.items():
            config.set(section, key, str(value))
    
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        config.write(f)

def load_json(file_path: str) -> Dict[str, Any]:
    """
    Load JSON data from file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        JSON data as dictionary
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON file {file_path}: {e}")
        return {}

def save_json(data: Dict[str, Any], file_path: str):
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        file_path: Path to JSON file
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def ensure_directory(directory_path: str):
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        directory_path: Path to directory
    """
    os.makedirs(directory_path, exist_ok=True)

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to project root
    """
    return Path(__file__).parent.parent.parent

def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def get_timestamp() -> str:
    """
    Get current timestamp as string.
    
    Returns:
        Timestamp string
    """
    return time.strftime('%Y%m%d_%H%M%S')

def parse_email(text: str) -> Optional[str]:
    """
    Extract email address from text.
    
    Args:
        text: Text to search for email
        
    Returns:
        Email address if found, None otherwise
    """
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None

def parse_url(text: str) -> Optional[str]:
    """
    Extract URL from text.
    
    Args:
        text: Text to search for URL
        
    Returns:
        URL if found, None otherwise
    """
    import re
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, text)
    return match.group(0) if match else None

def is_valid_file_path(path: str) -> bool:
    """
    Check if a path is a valid file path.
    
    Args:
        path: File path to check
        
    Returns:
        True if valid, False otherwise
    """
    try:
        Path(path)
        return True
    except (OSError, ValueError):
        return False

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.
    
    Args:
        filename: Filename
        
    Returns:
        File extension (without dot)
    """
    return Path(filename).suffix.lstrip('.')

def create_backup(file_path: str) -> str:
    """
    Create a backup of a file.
    
    Args:
        file_path: Path to file to backup
        
    Returns:
        Path to backup file
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    backup_path = f"{file_path}.backup_{get_timestamp()}"
    
    import shutil
    shutil.copy2(file_path, backup_path)
    
    return backup_path

def retry_on_exception(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    Decorator to retry function on exception.
    
    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logging.error(f"All {max_retries + 1} attempts failed")
            
            raise last_exception
        
        return wrapper
    return decorator

class PerformanceTimer:
    """Context manager for measuring execution time."""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logging.info(f"{self.name} completed in {format_duration(duration)}")
    
    @property
    def duration(self) -> float:
        """Get the measured duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
