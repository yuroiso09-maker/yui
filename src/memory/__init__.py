"""
OTIS Memory Optimization Engine
Advanced memory management and virtualization for 10x memory expansion
"""

from .memory_engine import MemoryOptimizationEngine
from .zram_manager import ZRAMManager
from .ksm_manager import KSMManager
from .compression_engine import CompressionEngine
from .memory_predictor import MemoryPredictor

__all__ = [
    "MemoryOptimizationEngine",
    "ZRAMManager", 
    "KSMManager",
    "CompressionEngine",
    "MemoryPredictor"
]