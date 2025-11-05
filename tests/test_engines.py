"""
OTIS Engine Tests
Individual engine testing for all optimization engines
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from memory.memory_engine import MemoryOptimizationEngine
from gpu.gpu_engine import GPUVirtualizationEngine
from storage.storage_engine import StorageOptimizationEngine
from ai.ai_engine import AIOptimizationEngine
from windows.windows_engine import WindowsCompatibilityEngine
from security.security_engine import SecurityEngine
from core.config import ConfigManager
from core.system_info import SystemInfo


@pytest.fixture
def config():
    """Provide configuration for tests"""
    return ConfigManager()


@pytest.fixture
def system_info():
    """Provide system info for tests"""
    return SystemInfo()


class TestMemoryEngine:
    """Test Memory Optimization Engine"""
    
    @pytest.mark.asyncio
    async def test_memory_engine_initialization(self, config, system_info):
        """Test memory engine initialization"""
        engine = MemoryOptimizationEngine(config, system_info)
        
        assert engine is not None
        assert not engine.is_running
        
        # Test components
        assert engine.zram_manager is not None
        assert engine.ksm_manager is not None
        assert engine.compression_engine is not None
        assert engine.memory_predictor is not None
    
    @pytest.mark.asyncio
    async def test_memory_engine_startup(self, config, system_info):
        """Test memory engine startup"""
        engine = MemoryOptimizationEngine(config, system_info)
        
        success = await engine.start()
        assert success is True
        assert engine.is_running is True
        
        # Test status
        status = await engine.get_status()
        assert status['enabled'] is True
        
        # Cleanup
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_memory_performance_multiplier(self, config, system_info):
        """Test memory performance multiplier"""
        engine = MemoryOptimizationEngine(config, system_info)
        
        multiplier = await engine.get_performance_multiplier()
        assert multiplier >= 1.0


class TestGPUEngine:
    """Test GPU Virtualization Engine"""
    
    @pytest.mark.asyncio
    async def test_gpu_engine_initialization(self, config, system_info):
        """Test GPU engine initialization"""
        engine = GPUVirtualizationEngine(config, system_info)
        
        assert engine is not None
        assert not engine.is_running
        
        # Test components
        assert engine.llvmpipe_manager is not None
        assert engine.dxvk_manager is not None
        assert engine.resource_manager is not None
    
    @pytest.mark.asyncio
    async def test_gpu_engine_startup(self, config, system_info):
        """Test GPU engine startup"""
        engine = GPUVirtualizationEngine(config, system_info)
        
        success = await engine.start()
        assert success is True
        assert engine.is_running is True
        
        # Test status
        status = await engine.get_status()
        assert status['enabled'] is True
        
        # Cleanup
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_gpu_capabilities_detection(self, config, system_info):
        """Test GPU capabilities detection"""
        engine = GPUVirtualizationEngine(config, system_info)
        
        capabilities = await engine.detect_gpu_capabilities()
        assert isinstance(capabilities, dict)
        assert 'has_integrated_gpu' in capabilities


class TestStorageEngine:
    """Test Storage Optimization Engine"""
    
    @pytest.mark.asyncio
    async def test_storage_engine_initialization(self, config, system_info):
        """Test storage engine initialization"""
        engine = StorageOptimizationEngine(config, system_info)
        
        assert engine is not None
        assert not engine.is_running
        
        # Test components
        assert engine.compression_manager is not None
        assert engine.deduplication_manager is not None
        assert engine.cloud_extension is not None
    
    @pytest.mark.asyncio
    async def test_storage_engine_startup(self, config, system_info):
        """Test storage engine startup"""
        engine = StorageOptimizationEngine(config, system_info)
        
        success = await engine.start()
        assert success is True
        assert engine.is_running is True
        
        # Test status
        status = await engine.get_status()
        assert status['enabled'] is True
        
        # Cleanup
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_compression_support_detection(self, config, system_info):
        """Test compression support detection"""
        engine = StorageOptimizationEngine(config, system_info)
        
        support = await engine.detect_compression_support()
        assert isinstance(support, dict)
        assert 'zstd' in support
        assert 'gzip' in support


class TestAIEngine:
    """Test AI Optimization Engine"""
    
    @pytest.mark.asyncio
    async def test_ai_engine_initialization(self, config, system_info):
        """Test AI engine initialization"""
        engine = AIOptimizationEngine(config, system_info)
        
        assert engine is not None
        assert not engine.is_running
        
        # Test components
        assert engine.pattern_recognizer is not None
        assert engine.predictive_optimizer is not None
        assert engine.learning_engine is not None
    
    @pytest.mark.asyncio
    async def test_ai_engine_startup(self, config, system_info):
        """Test AI engine startup"""
        engine = AIOptimizationEngine(config, system_info)
        
        success = await engine.start()
        assert success is True
        assert engine.is_running is True
        
        # Test status
        status = await engine.get_status()
        assert status['enabled'] is True
        
        # Cleanup
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_pattern_analysis(self, config, system_info):
        """Test system pattern analysis"""
        engine = AIOptimizationEngine(config, system_info)
        
        patterns = await engine.analyze_system_patterns()
        assert isinstance(patterns, dict)
        assert 'current_metrics' in patterns or len(patterns) == 0  # May be empty if no data


class TestWindowsEngine:
    """Test Windows Compatibility Engine"""
    
    @pytest.mark.asyncio
    async def test_windows_engine_initialization(self, config, system_info):
        """Test Windows engine initialization"""
        engine = WindowsCompatibilityEngine(config, system_info)
        
        assert engine is not None
        assert not engine.is_running
        
        # Test components
        assert engine.wine_manager is not None
        assert engine.api_emulation is not None
        assert engine.performance_optimizer is not None
    
    @pytest.mark.asyncio
    async def test_windows_engine_startup(self, config, system_info):
        """Test Windows engine startup"""
        engine = WindowsCompatibilityEngine(config, system_info)
        
        success = await engine.start()
        assert success is True
        assert engine.is_running is True
        
        # Test status
        status = await engine.get_status()
        assert status['enabled'] is True
        
        # Cleanup
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_wine_detection(self, config, system_info):
        """Test Wine detection"""
        engine = WindowsCompatibilityEngine(config, system_info)
        
        wine_info = await engine.wine_manager.detect_wine_installation()
        assert isinstance(wine_info, dict)
        assert 'wine_available' in wine_info


class TestSecurityEngine:
    """Test Security Engine"""
    
    @pytest.mark.asyncio
    async def test_security_engine_initialization(self, config, system_info):
        """Test security engine initialization"""
        engine = SecurityEngine(config, system_info)
        
        assert engine is not None
        assert not engine.is_running
        
        # Test components
        assert engine.behavioral_analyzer is not None
        assert engine.threat_detector is not None
        assert engine.protection_manager is not None
    
    @pytest.mark.asyncio
    async def test_security_engine_startup(self, config, system_info):
        """Test security engine startup"""
        engine = SecurityEngine(config, system_info)
        
        success = await engine.start()
        assert success is True
        assert engine.is_running is True
        
        # Test status
        status = await engine.get_status()
        assert status['enabled'] is True
        
        # Cleanup
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_threat_detection(self, config, system_info):
        """Test threat detection"""
        engine = SecurityEngine(config, system_info)
        
        await engine.start()
        
        # Perform security scan
        scan_results = await engine.perform_security_scan()
        assert isinstance(scan_results, dict)
        
        await engine.stop()


@pytest.mark.asyncio
async def test_all_engines_performance():
    """Test that all engines provide performance improvements"""
    config = ConfigManager()
    system_info = SystemInfo()
    
    engines = [
        MemoryOptimizationEngine(config, system_info),
        GPUVirtualizationEngine(config, system_info),
        StorageOptimizationEngine(config, system_info),
        AIOptimizationEngine(config, system_info),
        WindowsCompatibilityEngine(config, system_info),
        SecurityEngine(config, system_info)
    ]
    
    for engine in engines:
        try:
            await engine.start()
            
            # Test performance multiplier
            if hasattr(engine, 'get_performance_multiplier'):
                multiplier = await engine.get_performance_multiplier()
                assert multiplier >= 1.0, f"{engine.__class__.__name__} should provide performance improvement"
            
            # Test efficiency score
            if hasattr(engine, 'get_efficiency_score'):
                score = await engine.get_efficiency_score()
                assert 0 <= score <= 100, f"{engine.__class__.__name__} efficiency score should be 0-100"
            
        finally:
            if engine.is_running:
                await engine.stop()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])