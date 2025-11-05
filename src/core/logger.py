"""
OTIS Logging System
Advanced logging with performance monitoring and beautiful output
"""

import sys
import os
from pathlib import Path
from typing import Optional
from loguru import logger
import time


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_performance_logging: bool = True
) -> logger:
    """
    Setup OTIS logging system with beautiful formatting and performance monitoring
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        enable_performance_logging: Enable performance metrics logging
    
    Returns:
        Configured logger instance
    """
    
    # Remove default logger
    logger.remove()
    
    # Create logs directory if it doesn't exist
    log_dir = Path.home() / ".config" / "otis" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Default log file if not specified
    if log_file is None:
        log_file = log_dir / "otis.log"
    
    # Console logging with beautiful formatting
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    logger.add(
        sys.stdout,
        format=console_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # File logging with detailed formatting
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    logger.add(
        log_file,
        format=file_format,
        level="DEBUG",  # Always log everything to file
        rotation="10 MB",
        retention="7 days",
        compression="gz",
        backtrace=True,
        diagnose=True
    )
    
    # Performance logging if enabled
    if enable_performance_logging:
        perf_log_file = log_dir / "performance.log"
        logger.add(
            perf_log_file,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | PERF | {message}",
            level="INFO",
            rotation="5 MB",
            retention="3 days",
            filter=lambda record: "PERF" in record["message"]
        )
    
    # Add custom log levels for OTIS (only if they don't exist)
    try:
        logger.level("SUCCESS", no=25, color="<green><bold>")
    except ValueError:
        pass  # Level already exists
    
    try:
        logger.level("PERFORMANCE", no=15, color="<blue>")
    except ValueError:
        pass  # Level already exists
    
    # Log startup message
    logger.info("🚀 OTIS Logging System initialized")
    logger.info(f"📝 Log file: {log_file}")
    logger.info(f"📊 Log level: {log_level}")
    
    return logger


class PerformanceLogger:
    """Performance monitoring and logging utility"""
    
    def __init__(self):
        self.start_times = {}
        self.performance_metrics = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = time.time()
        logger.debug(f"⏱️  Started timing: {operation}")
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and log the result"""
        if operation not in self.start_times:
            logger.warning(f"No start time found for operation: {operation}")
            return 0.0
        
        duration = time.time() - self.start_times[operation]
        del self.start_times[operation]
        
        # Store performance metric
        if operation not in self.performance_metrics:
            self.performance_metrics[operation] = []
        self.performance_metrics[operation].append(duration)
        
        # Log performance
        logger.info(f"⚡ PERF | {operation}: {duration:.3f}s")
        
        return duration
    
    def log_memory_usage(self, component: str, memory_mb: float):
        """Log memory usage for a component"""
        logger.info(f"💾 PERF | {component} memory usage: {memory_mb:.1f} MB")
    
    def log_cpu_usage(self, component: str, cpu_percent: float):
        """Log CPU usage for a component"""
        logger.info(f"🔥 PERF | {component} CPU usage: {cpu_percent:.1f}%")
    
    def log_performance_multiplier(self, component: str, multiplier: float):
        """Log performance multiplier for a component"""
        logger.success(f"🚀 PERF | {component} performance multiplier: {multiplier}x")
    
    def get_average_duration(self, operation: str) -> float:
        """Get average duration for an operation"""
        if operation not in self.performance_metrics:
            return 0.0
        
        durations = self.performance_metrics[operation]
        return sum(durations) / len(durations)
    
    def log_system_stats(self, stats: dict):
        """Log comprehensive system statistics"""
        logger.info("📊 PERF | System Statistics:")
        for key, value in stats.items():
            if isinstance(value, float):
                logger.info(f"📊 PERF |   {key}: {value:.2f}")
            else:
                logger.info(f"📊 PERF |   {key}: {value}")


# Global performance logger instance
perf_logger = PerformanceLogger()


def log_function_performance(func):
    """Decorator to automatically log function performance"""
    def wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__name__}"
        perf_logger.start_timer(func_name)
        
        try:
            result = func(*args, **kwargs)
            perf_logger.end_timer(func_name)
            return result
        except Exception as e:
            perf_logger.end_timer(func_name)
            logger.error(f"❌ Error in {func_name}: {e}")
            raise
    
    return wrapper


async def log_async_function_performance(func):
    """Decorator to automatically log async function performance"""
    async def wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__name__}"
        perf_logger.start_timer(func_name)
        
        try:
            result = await func(*args, **kwargs)
            perf_logger.end_timer(func_name)
            return result
        except Exception as e:
            perf_logger.end_timer(func_name)
            logger.error(f"❌ Error in {func_name}: {e}")
            raise
    
    return wrapper


class LogContext:
    """Context manager for logging operations with automatic timing"""
    
    def __init__(self, operation: str, log_start: bool = True, log_end: bool = True):
        self.operation = operation
        self.log_start = log_start
        self.log_end = log_end
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        if self.log_start:
            logger.info(f"🔄 Starting: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            if self.log_end:
                logger.success(f"✅ Completed: {self.operation} ({duration:.3f}s)")
        else:
            logger.error(f"❌ Failed: {self.operation} ({duration:.3f}s) - {exc_val}")
        
        # Log performance metric
        perf_logger.performance_metrics.setdefault(self.operation, []).append(duration)


# Convenience functions for common logging patterns
def log_startup(component: str):
    """Log component startup"""
    logger.info(f"🚀 Starting {component}...")


def log_success(message: str):
    """Log success message"""
    logger.success(f"✅ {message}")


def log_error(message: str, exception: Exception = None):
    """Log error message"""
    if exception:
        logger.error(f"❌ {message}: {exception}")
    else:
        logger.error(f"❌ {message}")


def log_warning(message: str):
    """Log warning message"""
    logger.warning(f"⚠️  {message}")


def log_info(message: str):
    """Log info message"""
    logger.info(f"ℹ️  {message}")


def log_debug(message: str):
    """Log debug message"""
    logger.debug(f"🔍 {message}")


def log_performance_boost(component: str, multiplier: float):
    """Log performance boost"""
    logger.success(f"🚀 {component}: {multiplier}x performance boost!")


def log_memory_optimization(component: str, before_mb: float, after_mb: float):
    """Log memory optimization results"""
    savings = before_mb - after_mb
    percentage = (savings / before_mb) * 100 if before_mb > 0 else 0
    logger.success(f"💾 {component}: {savings:.1f}MB saved ({percentage:.1f}% reduction)")


def log_system_transformation(before_stats: dict, after_stats: dict):
    """Log complete system transformation results"""
    logger.info("🎉 OTIS System Transformation Complete!")
    logger.info("📊 Before vs After:")
    
    for key in before_stats:
        if key in after_stats:
            before = before_stats[key]
            after = after_stats[key]
            
            if isinstance(before, (int, float)) and isinstance(after, (int, float)):
                if before > 0:
                    improvement = (after / before) if after > before else (before / after)
                    logger.success(f"📈 {key}: {before} → {after} ({improvement:.1f}x improvement)")
                else:
                    logger.info(f"📊 {key}: {before} → {after}")
            else:
                logger.info(f"📊 {key}: {before} → {after}")


# Export commonly used functions
__all__ = [
    'setup_logger',
    'PerformanceLogger',
    'perf_logger',
    'log_function_performance',
    'log_async_function_performance',
    'LogContext',
    'log_startup',
    'log_success',
    'log_error',
    'log_warning',
    'log_info',
    'log_debug',
    'log_performance_boost',
    'log_memory_optimization',
    'log_system_transformation'
]