"""
OTIS Configuration Manager
Handles all configuration loading, validation, and management
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class MemoryConfig:
    """Memory optimization configuration"""
    zram_size_percent: int = 25
    compression_algorithm: str = "zstd"
    enable_ksm: bool = True
    ai_prediction: bool = True
    cloud_extension: bool = False
    max_compression_ratio: float = 5.0
    enable_ballooning: bool = True
    aggressive_mode: bool = False


@dataclass
class GPUConfig:
    """GPU virtualization configuration"""
    enable_llvmpipe: bool = True
    dxvk_async: bool = True
    cloud_rendering: bool = False
    ai_upscaling: bool = True
    software_rendering_threads: int = 0  # 0 = auto-detect
    vulkan_optimization: bool = True
    directx_translation: bool = True
    frame_prediction: bool = True


@dataclass
class StorageConfig:
    """Storage optimization configuration"""
    compression_level: int = 9
    enable_deduplication: bool = True
    cloud_extension: bool = False
    cache_size_gb: int = 2
    predictive_caching: bool = True
    context_aware_compression: bool = True
    virtual_storage_pools: bool = True


@dataclass
class AIConfig:
    """AI optimization configuration"""
    enable_prediction: bool = True
    prediction_window_minutes: int = 5
    learning_rate: float = 0.001
    model_update_interval: int = 300  # seconds
    enable_thermal_management: bool = True
    enable_workload_prediction: bool = True
    enable_resource_allocation: bool = True


@dataclass
class CloudConfig:
    """Cloud hybrid computing configuration"""
    enable_cloud_bursting: bool = False
    enable_edge_computing: bool = True
    cloud_provider: str = "auto"  # auto, aws, azure, gcp
    max_cloud_cost_per_hour: float = 1.0
    latency_threshold_ms: int = 100
    enable_hybrid_processing: bool = True


@dataclass
class WindowsConfig:
    """Windows compatibility configuration"""
    wine_version: str = "staging"
    dxvk_version: str = "latest"
    enable_registry_virtualization: bool = True
    enable_api_emulation: bool = True
    compatibility_mode: str = "aggressive"  # conservative, balanced, aggressive
    enable_directx_translation: bool = True


@dataclass
class SecurityConfig:
    """Security engine configuration"""
    enable_behavioral_analysis: bool = True
    enable_memory_protection: bool = True
    enable_ai_threat_detection: bool = True
    scan_only_when_idle: bool = True
    zero_impact_mode: bool = True
    threat_detection_sensitivity: str = "balanced"  # low, balanced, high


@dataclass
class OTISConfig:
    """Main OTIS configuration"""
    memory: MemoryConfig
    gpu: GPUConfig
    storage: StorageConfig
    ai: AIConfig
    cloud: CloudConfig
    windows: WindowsConfig
    security: SecurityConfig
    
    # Global settings
    log_level: str = "INFO"
    enable_telemetry: bool = False
    auto_update: bool = True
    performance_mode: str = "auto"  # auto, gaming, productivity, extreme
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)


class ConfigManager:
    """Manages OTIS configuration loading, validation, and updates"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = self._determine_config_path(config_path)
        self.config = self._load_config()
        self._validate_config()
        
        logger.info(f"Configuration loaded from: {self.config_path}")
    
    def _determine_config_path(self, config_path: Optional[str]) -> Path:
        """Determine the configuration file path"""
        if config_path:
            return Path(config_path)
        
        # Check for config in order of preference
        possible_paths = [
            Path.home() / ".config" / "otis" / "config.yaml",
            Path.home() / ".otis" / "config.yaml",
            Path("/etc/otis/config.yaml"),
            Path(__file__).parent.parent.parent / "config" / "default.yaml"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # If no config found, create default config
        default_path = Path.home() / ".config" / "otis" / "config.yaml"
        default_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_default_config(default_path)
        return default_path
    
    def _create_default_config(self, path: Path):
        """Create default configuration file"""
        default_config = OTISConfig(
            memory=MemoryConfig(),
            gpu=GPUConfig(),
            storage=StorageConfig(),
            ai=AIConfig(),
            cloud=CloudConfig(),
            windows=WindowsConfig(),
            security=SecurityConfig()
        )
        
        with open(path, 'w') as f:
            yaml.dump(default_config.to_dict(), f, default_flow_style=False, indent=2)
        
        logger.info(f"Created default configuration at: {path}")
    
    def _load_config(self) -> OTISConfig:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                if self.config_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    config_data = yaml.safe_load(f)
            
            # Create configuration objects with defaults
            return OTISConfig(
                memory=MemoryConfig(**config_data.get('memory', {})),
                gpu=GPUConfig(**config_data.get('gpu', {})),
                storage=StorageConfig(**config_data.get('storage', {})),
                ai=AIConfig(**config_data.get('ai', {})),
                cloud=CloudConfig(**config_data.get('cloud', {})),
                windows=WindowsConfig(**config_data.get('windows', {})),
                security=SecurityConfig(**config_data.get('security', {})),
                log_level=config_data.get('log_level', 'INFO'),
                enable_telemetry=config_data.get('enable_telemetry', False),
                auto_update=config_data.get('auto_update', True),
                performance_mode=config_data.get('performance_mode', 'auto')
            )
            
        except Exception as e:
            logger.warning(f"Failed to load config from {self.config_path}: {e}")
            logger.info("Using default configuration")
            return OTISConfig(
                memory=MemoryConfig(),
                gpu=GPUConfig(),
                storage=StorageConfig(),
                ai=AIConfig(),
                cloud=CloudConfig(),
                windows=WindowsConfig(),
                security=SecurityConfig()
            )
    
    def _validate_config(self):
        """Validate configuration values"""
        # Memory validation
        if not 1 <= self.config.memory.zram_size_percent <= 50:
            logger.warning("zram_size_percent should be between 1-50%, using default 25%")
            self.config.memory.zram_size_percent = 25
        
        if self.config.memory.compression_algorithm not in ['lz4', 'lzo', 'zstd', 'lz4hc']:
            logger.warning(f"Invalid compression algorithm, using 'zstd'")
            self.config.memory.compression_algorithm = 'zstd'
        
        # GPU validation
        if self.config.gpu.software_rendering_threads < 0:
            self.config.gpu.software_rendering_threads = 0
        
        # Storage validation
        if not 1 <= self.config.storage.compression_level <= 22:
            logger.warning("compression_level should be between 1-22, using default 9")
            self.config.storage.compression_level = 9
        
        if self.config.storage.cache_size_gb < 0:
            self.config.storage.cache_size_gb = 2
        
        # AI validation
        if not 1 <= self.config.ai.prediction_window_minutes <= 60:
            logger.warning("prediction_window_minutes should be between 1-60, using default 5")
            self.config.ai.prediction_window_minutes = 5
        
        if not 0.0001 <= self.config.ai.learning_rate <= 0.1:
            logger.warning("learning_rate should be between 0.0001-0.1, using default 0.001")
            self.config.ai.learning_rate = 0.001
        
        # Cloud validation
        if self.config.cloud.max_cloud_cost_per_hour < 0:
            self.config.cloud.max_cloud_cost_per_hour = 1.0
        
        if self.config.cloud.latency_threshold_ms < 10:
            self.config.cloud.latency_threshold_ms = 100
        
        logger.info("Configuration validation completed")
    
    def get_section(self, section: str) -> Union[MemoryConfig, GPUConfig, StorageConfig, AIConfig, CloudConfig, WindowsConfig, SecurityConfig]:
        """Get configuration section"""
        return getattr(self.config, section)
    
    def get_config(self) -> OTISConfig:
        """Get full configuration"""
        return self.config
    
    def update_section(self, section: str, updates: Dict[str, Any]):
        """Update configuration section"""
        section_config = getattr(self.config, section)
        for key, value in updates.items():
            if hasattr(section_config, key):
                setattr(section_config, key, value)
            else:
                logger.warning(f"Unknown configuration key: {section}.{key}")
        
        self._validate_config()
        self.save_config()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config.to_dict(), f, default_flow_style=False, indent=2)
            logger.info(f"Configuration saved to: {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def reload_config(self):
        """Reload configuration from file"""
        self.config = self._load_config()
        self._validate_config()
        logger.info("Configuration reloaded")
    
    def get_hardware_optimized_config(self, hardware_info: Dict[str, Any]) -> OTISConfig:
        """Get hardware-optimized configuration"""
        optimized_config = self.config
        
        # Optimize memory settings based on available RAM
        total_ram_gb = hardware_info.get('memory', {}).get('total_gb', 4)
        if total_ram_gb <= 4:
            optimized_config.memory.zram_size_percent = 30
            optimized_config.memory.aggressive_mode = True
        elif total_ram_gb <= 8:
            optimized_config.memory.zram_size_percent = 20
        else:
            optimized_config.memory.zram_size_percent = 15
        
        # Optimize GPU settings based on graphics hardware
        gpu_info = hardware_info.get('gpu', {})
        if gpu_info.get('type') == 'integrated':
            optimized_config.gpu.enable_llvmpipe = True
            optimized_config.gpu.ai_upscaling = True
            optimized_config.gpu.cloud_rendering = True
        
        # Optimize storage settings based on storage type
        storage_info = hardware_info.get('storage', {})
        if storage_info.get('type') == 'ssd':
            optimized_config.storage.compression_level = 6  # Lower compression for SSD
        else:
            optimized_config.storage.compression_level = 9  # Higher compression for HDD
        
        # Optimize CPU settings
        cpu_cores = hardware_info.get('cpu', {}).get('cores', 2)
        optimized_config.gpu.software_rendering_threads = max(1, cpu_cores - 1)
        
        return optimized_config
    
    def get_mode_optimized_config(self, mode: str) -> OTISConfig:
        """Get mode-optimized configuration"""
        optimized_config = self.config
        
        if mode == "gaming":
            # Gaming mode: prioritize GPU and low latency
            optimized_config.gpu.dxvk_async = True
            optimized_config.gpu.ai_upscaling = True
            optimized_config.memory.aggressive_mode = True
            optimized_config.ai.enable_thermal_management = True
            
        elif mode == "productivity":
            # Productivity mode: prioritize memory and storage
            optimized_config.memory.enable_ksm = True
            optimized_config.storage.predictive_caching = True
            optimized_config.ai.enable_workload_prediction = True
            
        elif mode == "extreme":
            # Extreme mode: enable everything for maximum performance
            optimized_config.memory.aggressive_mode = True
            optimized_config.memory.cloud_extension = True
            optimized_config.gpu.cloud_rendering = True
            optimized_config.storage.cloud_extension = True
            optimized_config.cloud.enable_cloud_bursting = True
            
        return optimized_config