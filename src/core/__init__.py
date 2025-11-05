"""
OTIS Core Module
The heart of the Optimization and Transformation Intelligence System
"""

__version__ = "1.0.0"
__author__ = "OTIS Development Team"
__email__ = "dev@otis-optimizer.com"

from .main import OTISCore
from .config import ConfigManager
from .logger import setup_logger
from .system_info import SystemInfo

__all__ = [
    "OTISCore",
    "ConfigManager", 
    "setup_logger",
    "SystemInfo"
]