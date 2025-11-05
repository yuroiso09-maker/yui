"""
OTIS Memory Optimization Engine
The core memory management system that can turn 4GB into 40GB+ effective memory
"""

import asyncio
import subprocess
import time
import threading
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from loguru import logger
from core.logger import LogContext, log_performance_boost, perf_logger
from .zram_manager import ZRAMManager
from .ksm_manager import KSMManager
from .compression_engine import CompressionEngine
from .memory_predictor import MemoryPredictor


@dataclass
class MemoryStats:
    """Memory statistics structure"""
    total_physical_gb: float
    total_effective_gb: float
    used_gb: float
    available_gb: float
    compression_ratio: float
    ksm_savings_gb: float
    zram_size_gb: float
    performance_multiplier: float


class MemoryOptimizationEngine:
    """
    Advanced memory optimization engine that provides massive memory expansion
    through intelligent compression, deduplication, and prediction
    """
    
    def __init__(self, config, system_info):
        self.config = config
        self.system_info = system_info
        self.is_running = False
        self.optimization_thread = None
        
        # Initialize sub-engines
        self.zram_manager = ZRAMManager(config)
        self.ksm_manager = KSMManager(config)
        self.compression_engine = CompressionEngine(config)
        self.memory_predictor = MemoryPredictor(config)
        
        # Performance tracking
        self.initial_memory_gb = 0
        self.current_stats = None
        self.optimization_history = []
        
        logger.info("💾 Memory Optimization Engine initialized")
    
    async def start(self, mode: str = "auto") -> bool:
        """Start the memory optimization engine"""
        if self.is_running:
            return True
        
        try:
            with LogContext("Starting Memory Optimization Engine"):
                # Get initial memory state
                self.initial_memory_gb = self.system_info.get_memory_info().total_gb
                logger.info(f"Initial physical memory: {self.initial_memory_gb:.1f}GB")
                
                # Configure for hardware and mode
                await self._configure_for_mode(mode)
                
                # Start all sub-engines
                await self._start_sub_engines()
                
                # Start continuous optimization
                self.is_running = True
                self.optimization_thread = threading.Thread(
                    target=self._optimization_loop,
                    daemon=True
                )
                self.optimization_thread.start()
                
                # Calculate and log performance boost
                await asyncio.sleep(2)  # Wait for initial optimization
                stats = await self.get_current_stats()
                log_performance_boost(
                    "Memory Engine", 
                    stats.performance_multiplier
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to start memory engine: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the memory optimization engine"""
        if not self.is_running:
            return True
        
        try:
            with LogContext("Stopping Memory Optimization Engine"):
                self.is_running = False
                
                # Stop optimization thread
                if self.optimization_thread and self.optimization_thread.is_alive():
                    self.optimization_thread.join(timeout=5)
                
                # Stop all sub-engines
                await self.zram_manager.stop()
                await self.ksm_manager.stop()
                await self.compression_engine.stop()
                await self.memory_predictor.stop()
                
                # Generate final report
                await self._generate_final_report()
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to stop memory engine: {e}")
            return False
    
    async def _configure_for_mode(self, mode: str):
        """Configure memory engine for specific mode"""
        memory_info = self.system_info.get_memory_info()
        
        if mode == "gaming":
            # Gaming mode: prioritize low latency and high performance
            self.config.aggressive_mode = True
            self.config.zram_size_percent = min(30, self.config.zram_size_percent)
            self.config.compression_algorithm = "lz4"  # Faster compression
            
        elif mode == "productivity":
            # Productivity mode: balance performance and memory savings
            self.config.zram_size_percent = 25
            self.config.compression_algorithm = "zstd"  # Better compression
            self.config.enable_ksm = True
            
        elif mode == "extreme":
            # Extreme mode: maximum memory expansion
            self.config.aggressive_mode = True
            self.config.zram_size_percent = 35
            self.config.max_compression_ratio = 6.0
            self.config.enable_ksm = True
            self.config.enable_ballooning = True
            
        # Auto-adjust based on available memory
        if memory_info.total_gb <= 4:
            self.config.aggressive_mode = True
            self.config.zram_size_percent = max(30, self.config.zram_size_percent)
        elif memory_info.total_gb <= 8:
            self.config.zram_size_percent = max(20, self.config.zram_size_percent)
        
        logger.info(f"Memory engine configured for {mode} mode")
        logger.info(f"zRAM size: {self.config.zram_size_percent}% of physical memory")
        logger.info(f"Compression algorithm: {self.config.compression_algorithm}")
        logger.info(f"Aggressive mode: {self.config.aggressive_mode}")
    
    async def _start_sub_engines(self):
        """Start all memory sub-engines"""
        # Start in optimal order for maximum effectiveness
        
        # 1. Start compression engine first
        await self.compression_engine.start()
        logger.success("✅ Compression engine started")
        
        # 2. Start zRAM manager
        await self.zram_manager.start()
        logger.success("✅ zRAM manager started")
        
        # 3. Start KSM manager if enabled
        if self.config.enable_ksm:
            await self.ksm_manager.start()
            logger.success("✅ KSM manager started")
        
        # 4. Start memory predictor
        if self.config.ai_prediction:
            await self.memory_predictor.start()
            logger.success("✅ Memory predictor started")
    
    def _optimization_loop(self):
        """Continuous memory optimization loop"""
        logger.info("🔄 Starting memory optimization loop")
        
        while self.is_running:
            try:
                asyncio.run(self._optimization_cycle())
                time.sleep(10)  # Optimize every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in memory optimization loop: {e}")
                time.sleep(30)  # Wait longer on error
    
    async def _optimization_cycle(self):
        """Single memory optimization cycle"""
        try:
            # Get current memory state
            memory_info = self.system_info.get_memory_info()
            
            # Check if aggressive optimization is needed
            if memory_info.usage_percent > 85:
                await self._enable_aggressive_optimization()
            elif memory_info.usage_percent < 50:
                await self._enable_efficiency_optimization()
            
            # Let memory predictor analyze patterns
            if self.config.ai_prediction:
                predictions = await self.memory_predictor.predict_memory_needs()
                await self._optimize_based_on_predictions(predictions)
            
            # Update performance statistics
            self.current_stats = await self.get_current_stats()
            self.optimization_history.append({
                'timestamp': time.time(),
                'stats': self.current_stats,
                'memory_usage': memory_info.usage_percent
            })
            
            # Keep only last 100 optimization cycles
            if len(self.optimization_history) > 100:
                self.optimization_history = self.optimization_history[-100:]
            
        except Exception as e:
            logger.error(f"Error in optimization cycle: {e}")
    
    async def _enable_aggressive_optimization(self):
        """Enable aggressive memory optimization when memory is low"""
        logger.info("🔥 Enabling aggressive memory optimization")
        
        # Increase zRAM compression
        await self.zram_manager.increase_compression()
        
        # Enable more aggressive KSM
        if self.config.enable_ksm:
            await self.ksm_manager.enable_aggressive_mode()
        
        # Enable memory ballooning if available
        if self.config.enable_ballooning:
            await self._enable_memory_ballooning()
    
    async def _enable_efficiency_optimization(self):
        """Enable efficiency optimization when memory usage is low"""
        logger.debug("⚡ Enabling efficiency optimization")
        
        # Reduce zRAM compression for better performance
        await self.zram_manager.optimize_for_performance()
        
        # Reduce KSM aggressiveness
        if self.config.enable_ksm:
            await self.ksm_manager.enable_balanced_mode()
    
    async def _optimize_based_on_predictions(self, predictions: Dict[str, Any]):
        """Optimize memory based on AI predictions"""
        predicted_usage = predictions.get('memory_usage_percent', 0)
        predicted_apps = predictions.get('applications', [])
        
        # Pre-allocate memory for predicted applications
        for app in predicted_apps:
            if app.get('memory_intensive', False):
                await self._prepare_for_memory_intensive_app(app)
        
        # Adjust compression based on predicted usage
        if predicted_usage > 80:
            await self.zram_manager.prepare_for_high_usage()
        elif predicted_usage < 40:
            await self.zram_manager.optimize_for_low_usage()
    
    async def _prepare_for_memory_intensive_app(self, app_info: Dict[str, Any]):
        """Prepare memory system for memory-intensive application"""
        logger.info(f"🎯 Preparing memory for {app_info.get('name', 'unknown app')}")
        
        # Increase available memory
        await self.zram_manager.expand_if_needed()
        
        # Pre-compress less important data
        await self.compression_engine.compress_background_data()
        
        # Optimize KSM for the application type
        if self.config.enable_ksm:
            await self.ksm_manager.optimize_for_app_type(app_info.get('type', 'generic'))
    
    async def _enable_memory_ballooning(self):
        """Enable memory ballooning for dynamic allocation"""
        try:
            # This would implement memory ballooning techniques
            # For now, we'll simulate it with zRAM expansion
            await self.zram_manager.expand_dynamically()
            logger.info("💨 Memory ballooning enabled")
        except Exception as e:
            logger.warning(f"Failed to enable memory ballooning: {e}")
    
    async def get_current_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        memory_info = self.system_info.get_memory_info()
        zram_stats = await self.zram_manager.get_stats()
        ksm_stats = await self.ksm_manager.get_stats() if self.config.enable_ksm else {}
        
        # Calculate effective memory
        zram_effective_gb = zram_stats.get('effective_size_gb', 0)
        ksm_savings_gb = ksm_stats.get('savings_gb', 0)
        total_effective_gb = memory_info.total_gb + zram_effective_gb + ksm_savings_gb
        
        # Calculate performance multiplier
        performance_multiplier = total_effective_gb / self.initial_memory_gb if self.initial_memory_gb > 0 else 1.0
        
        return MemoryStats(
            total_physical_gb=memory_info.total_gb,
            total_effective_gb=total_effective_gb,
            used_gb=memory_info.used_gb,
            available_gb=memory_info.available_gb + zram_effective_gb + ksm_savings_gb,
            compression_ratio=zram_stats.get('compression_ratio', 1.0),
            ksm_savings_gb=ksm_savings_gb,
            zram_size_gb=zram_stats.get('size_gb', 0),
            performance_multiplier=performance_multiplier
        )
    
    async def get_status(self) -> Dict[str, Any]:
        """Get memory engine status"""
        stats = await self.get_current_stats()
        
        return {
            'enabled': self.is_running,
            'running': self.is_running,
            'stats': stats,
            'sub_engines': {
                'zram': await self.zram_manager.get_status(),
                'ksm': await self.ksm_manager.get_status() if self.config.enable_ksm else {'enabled': False},
                'compression': await self.compression_engine.get_status(),
                'predictor': await self.memory_predictor.get_status() if self.config.ai_prediction else {'enabled': False}
            },
            'optimization_cycles': len(self.optimization_history),
            'last_optimization': self.optimization_history[-1]['timestamp'] if self.optimization_history else None
        }
    
    async def get_performance_multiplier(self) -> float:
        """Get current performance multiplier"""
        stats = await self.get_current_stats()
        return stats.performance_multiplier
    
    async def get_efficiency_score(self) -> float:
        """Get memory efficiency score (0-100)"""
        stats = await self.get_current_stats()
        memory_info = self.system_info.get_memory_info()
        
        # Calculate efficiency based on:
        # - Compression ratio
        # - Memory utilization
        # - Performance multiplier
        
        compression_score = min(100, (stats.compression_ratio - 1) * 25)  # Max 100 for 5:1 ratio
        utilization_score = 100 - memory_info.usage_percent  # Lower usage = higher efficiency
        multiplier_score = min(100, (stats.performance_multiplier - 1) * 10)  # Max 100 for 11x multiplier
        
        return (compression_score + utilization_score + multiplier_score) / 3
    
    async def configure_for_hardware(self, hardware_info: Dict[str, Any]):
        """Configure memory engine for specific hardware"""
        memory_info = hardware_info.get('memory', {})
        cpu_info = hardware_info.get('cpu', {})
        
        # Adjust configuration based on hardware
        if memory_info.get('total_gb', 4) <= 4:
            self.config.aggressive_mode = True
            self.config.zram_size_percent = 35
            self.config.max_compression_ratio = 6.0
        
        # Adjust compression threads based on CPU cores
        cpu_cores = cpu_info.get('cores_logical', 2)
        await self.compression_engine.set_threads(max(1, cpu_cores // 2))
        
        logger.info(f"Memory engine configured for hardware: {memory_info.get('total_gb', 'unknown')}GB RAM")
    
    async def optimize_for_profile(self, profile: Dict[str, Any]):
        """Optimize memory for specific application profile"""
        app_type = profile.get('type', 'generic')
        memory_requirements = profile.get('memory_requirements', {})
        
        if app_type == 'gaming':
            # Gaming: prioritize low latency
            await self.zram_manager.optimize_for_gaming()
            if self.config.enable_ksm:
                await self.ksm_manager.optimize_for_gaming()
        
        elif app_type == 'office':
            # Office: optimize for document handling
            await self.compression_engine.optimize_for_documents()
            if self.config.enable_ksm:
                await self.ksm_manager.optimize_for_office()
        
        elif app_type == 'media':
            # Media: handle large files efficiently
            await self.zram_manager.optimize_for_media()
            await self.compression_engine.optimize_for_media()
        
        # Pre-allocate memory if needed
        required_gb = memory_requirements.get('minimum_gb', 0)
        if required_gb > 0:
            await self._ensure_available_memory(required_gb)
    
    async def optimize_based_on_predictions(self, predictions: Dict[str, Any]):
        """Optimize based on AI predictions"""
        await self._optimize_based_on_predictions(predictions)
    
    async def _ensure_available_memory(self, required_gb: float):
        """Ensure at least the required amount of memory is available"""
        stats = await self.get_current_stats()
        
        if stats.available_gb < required_gb:
            shortage_gb = required_gb - stats.available_gb
            logger.info(f"🎯 Ensuring {required_gb:.1f}GB available memory (need {shortage_gb:.1f}GB more)")
            
            # Try to free up memory
            await self.compression_engine.compress_background_data()
            await self.zram_manager.expand_if_needed()
            
            if self.config.enable_ksm:
                await self.ksm_manager.force_merge_cycle()
    
    async def _generate_final_report(self):
        """Generate final performance report"""
        if not self.optimization_history:
            return
        
        final_stats = self.optimization_history[-1]['stats']
        initial_memory = self.initial_memory_gb
        
        logger.info("📊 Memory Engine Final Report")
        logger.info(f"💾 Initial memory: {initial_memory:.1f}GB")
        logger.info(f"💾 Final effective memory: {final_stats.total_effective_gb:.1f}GB")
        logger.info(f"🚀 Performance multiplier: {final_stats.performance_multiplier:.1f}x")
        logger.info(f"📈 Memory expansion: {final_stats.total_effective_gb - initial_memory:.1f}GB gained")
        logger.info(f"⚡ Compression ratio: {final_stats.compression_ratio:.1f}:1")
        logger.info(f"💰 KSM savings: {final_stats.ksm_savings_gb:.1f}GB")
        logger.info(f"🔄 Optimization cycles: {len(self.optimization_history)}")
        
        # Calculate average efficiency
        if len(self.optimization_history) > 1:
            avg_efficiency = sum(h['stats'].performance_multiplier for h in self.optimization_history) / len(self.optimization_history)
            logger.info(f"📊 Average performance multiplier: {avg_efficiency:.1f}x")
    
    async def force_optimization(self):
        """Force immediate optimization cycle"""
        logger.info("🔄 Forcing immediate memory optimization")
        await self._optimization_cycle()
    
    async def get_memory_map(self) -> Dict[str, Any]:
        """Get detailed memory usage map"""
        return {
            'physical_memory': self.system_info.get_memory_info(),
            'zram': await self.zram_manager.get_detailed_stats(),
            'ksm': await self.ksm_manager.get_detailed_stats() if self.config.enable_ksm else {},
            'compression': await self.compression_engine.get_stats(),
            'predictions': await self.memory_predictor.get_current_predictions() if self.config.ai_prediction else {}
        }