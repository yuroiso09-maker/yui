"""
OTIS Core System Tests
Comprehensive testing for the complete OTIS system
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.main import OTISCore
from core.config import ConfigManager
from core.system_info import SystemInfo


class TestOTISCore:
    """Test OTIS Core System functionality"""
    
    @pytest.fixture
    async def otis_core(self):
        """Create OTIS core instance for testing"""
        core = OTISCore()
        yield core
        # Cleanup
        if core.is_running:
            await core.stop_all_engines()
    
    def test_core_initialization(self):
        """Test OTIS core system initialization"""
        core = OTISCore()
        
        assert core.config is not None
        assert core.system_info is not None
        assert len(core.engines) == 7  # All 7 engines should be initialized
        assert not core.is_running  # Should not be running initially
        
        # Check all engines are present
        expected_engines = [
            'memory', 'gpu', 'storage', 'ai', 
            'cloud', 'windows', 'security'
        ]
        
        for engine_name in expected_engines:
            assert engine_name in core.engines
    
    @pytest.mark.asyncio
    async def test_engine_startup(self, otis_core):
        """Test starting all engines"""
        success = await otis_core.start_all_engines()
        
        assert success is True
        assert otis_core.is_running is True
        assert otis_core.start_time is not None
        
        # Check engine status
        status = await otis_core.get_comprehensive_status()
        assert status['system_running'] is True
        assert status['total_performance_multiplier'] > 1.0
    
    @pytest.mark.asyncio
    async def test_engine_shutdown(self, otis_core):
        """Test stopping all engines"""
        # Start engines first
        await otis_core.start_all_engines()
        assert otis_core.is_running is True
        
        # Stop engines
        success = await otis_core.stop_all_engines()
        
        assert success is True
        assert otis_core.is_running is False
    
    @pytest.mark.asyncio
    async def test_performance_calculation(self, otis_core):
        """Test performance multiplier calculation"""
        await otis_core.start_all_engines()
        
        multiplier = await otis_core._calculate_performance_multiplier()
        assert multiplier >= 1.0
        assert multiplier < 1000.0  # Reasonable upper bound
    
    @pytest.mark.asyncio
    async def test_comprehensive_status(self, otis_core):
        """Test comprehensive status reporting"""
        await otis_core.start_all_engines()
        
        status = await otis_core.get_comprehensive_status()
        
        # Check required fields
        assert 'system_running' in status
        assert 'total_performance_multiplier' in status
        assert 'overall_efficiency_score' in status
        assert 'engines' in status
        assert 'system_info' in status
        assert 'capabilities' in status
        
        # Check engine statuses
        assert len(status['engines']) == 7
        
        # Check system info
        sys_info = status['system_info']
        assert 'memory_total_gb' in sys_info
        assert 'cpu_cores' in sys_info
        
        # Check capabilities
        capabilities = status['capabilities']
        assert 'memory_expansion' in capabilities
        assert 'gpu_boost' in capabilities


class TestSystemInfo:
    """Test system information collection"""
    
    def test_system_info_initialization(self):
        """Test system info initialization"""
        sys_info = SystemInfo()
        
        assert sys_info is not None
        
        # Test memory info
        memory_info = sys_info.get_memory_info()
        assert memory_info.total_gb > 0
        assert memory_info.available_gb >= 0
        assert 0 <= memory_info.usage_percent <= 100
        
        # Test CPU info
        cpu_info = sys_info.get_cpu_info()
        assert cpu_info.cores_logical > 0
        assert cpu_info.brand is not None
    
    def test_hardware_detection(self):
        """Test hardware detection capabilities"""
        sys_info = SystemInfo()
        
        # Test various hardware detection methods
        memory_usage = sys_info.get_memory_usage()
        assert 0 <= memory_usage <= 100
        
        cpu_usage = sys_info.get_cpu_usage()
        assert 0 <= cpu_usage <= 100


class TestConfigManager:
    """Test configuration management"""
    
    def test_config_loading(self):
        """Test configuration loading"""
        config = ConfigManager()
        
        assert config is not None
        assert config.config is not None
        
        # Test getting configuration values
        optimization_config = config.get('optimization', {})
        assert isinstance(optimization_config, dict)
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = ConfigManager()
        
        # Should not raise exceptions
        config._validate_config()


@pytest.mark.asyncio
async def test_full_system_integration():
    """Test complete system integration"""
    # This test runs the full system startup and shutdown cycle
    core = OTISCore()
    
    try:
        # Start all engines
        success = await core.start_all_engines()
        assert success is True
        
        # Get status
        status = await core.get_comprehensive_status()
        assert status['system_running'] is True
        
        # Verify performance improvement
        assert status['total_performance_multiplier'] > 10.0  # Should be significant
        
        # Test individual engine functionality
        for engine_name, engine in core.engines.items():
            engine_status = await engine.get_status()
            assert 'enabled' in engine_status
            
            if hasattr(engine, 'get_performance_multiplier'):
                multiplier = await engine.get_performance_multiplier()
                assert multiplier >= 1.0
        
    finally:
        # Always cleanup
        if core.is_running:
            await core.stop_all_engines()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])