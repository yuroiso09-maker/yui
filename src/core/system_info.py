"""
OTIS System Information Module
Comprehensive hardware detection and system monitoring
"""

import os
import platform
import subprocess
import psutil
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from loguru import logger

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

try:
    import cpuinfo
    CPUINFO_AVAILABLE = True
except ImportError:
    CPUINFO_AVAILABLE = False


@dataclass
class CPUInfo:
    """CPU information structure"""
    brand: str
    architecture: str
    cores_physical: int
    cores_logical: int
    frequency_max: float
    frequency_current: float
    cache_l1: Optional[str] = None
    cache_l2: Optional[str] = None
    cache_l3: Optional[str] = None
    features: List[str] = None


@dataclass
class MemoryInfo:
    """Memory information structure"""
    total_gb: float
    available_gb: float
    used_gb: float
    usage_percent: float
    swap_total_gb: float
    swap_used_gb: float
    swap_percent: float


@dataclass
class GPUInfo:
    """GPU information structure"""
    name: str
    type: str  # 'integrated', 'discrete', 'unknown'
    memory_total_mb: Optional[int] = None
    memory_used_mb: Optional[int] = None
    driver_version: Optional[str] = None
    cuda_support: bool = False
    vulkan_support: bool = False
    opengl_version: Optional[str] = None


@dataclass
class StorageInfo:
    """Storage information structure"""
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float
    type: str  # 'ssd', 'hdd', 'unknown'
    filesystem: str
    mount_point: str


@dataclass
class NetworkInfo:
    """Network information structure"""
    interface: str
    speed_mbps: Optional[int]
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    is_up: bool


class SystemInfo:
    """Comprehensive system information and monitoring"""
    
    def __init__(self):
        self.logger = logger
        self._cache = {}
        self._cache_timeout = 30  # Cache for 30 seconds
        self._last_network_stats = None
        self._last_network_time = None
        
        self.logger.info("🔍 Initializing system information collector")
        self._detect_system_capabilities()
    
    def _detect_system_capabilities(self):
        """Detect system capabilities and available tools"""
        self.capabilities = {
            'gpu_monitoring': GPU_AVAILABLE,
            'detailed_cpu_info': CPUINFO_AVAILABLE,
            'zram_support': self._check_zram_support(),
            'ksm_support': self._check_ksm_support(),
            'wine_available': self._check_wine_availability(),
            'dxvk_available': self._check_dxvk_availability(),
            'vulkan_support': self._check_vulkan_support(),
            'docker_available': self._check_docker_availability()
        }
        
        self.logger.info(f"System capabilities detected: {sum(self.capabilities.values())}/{len(self.capabilities)} available")
    
    def _check_zram_support(self) -> bool:
        """Check if zRAM is supported"""
        try:
            return Path("/sys/class/zram-control").exists() or Path("/dev/zram0").exists()
        except:
            return False
    
    def _check_ksm_support(self) -> bool:
        """Check if KSM is supported"""
        try:
            return Path("/sys/kernel/mm/ksm").exists()
        except:
            return False
    
    def _check_wine_availability(self) -> bool:
        """Check if Wine is available"""
        try:
            subprocess.run(['wine', '--version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def _check_dxvk_availability(self) -> bool:
        """Check if DXVK is available"""
        try:
            # Check for DXVK installation
            wine_prefix = os.environ.get('WINEPREFIX', Path.home() / '.wine')
            dxvk_path = Path(wine_prefix) / 'drive_c' / 'windows' / 'system32' / 'd3d11.dll'
            return dxvk_path.exists()
        except:
            return False
    
    def _check_vulkan_support(self) -> bool:
        """Check if Vulkan is supported"""
        try:
            result = subprocess.run(['vulkaninfo'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _check_docker_availability(self) -> bool:
        """Check if Docker is available"""
        try:
            subprocess.run(['docker', '--version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def _get_cached_or_compute(self, key: str, compute_func, timeout: int = None) -> Any:
        """Get cached value or compute new one"""
        timeout = timeout or self._cache_timeout
        current_time = time.time()
        
        if key in self._cache:
            cached_time, cached_value = self._cache[key]
            if current_time - cached_time < timeout:
                return cached_value
        
        # Compute new value
        new_value = compute_func()
        self._cache[key] = (current_time, new_value)
        return new_value
    
    def get_cpu_info(self) -> CPUInfo:
        """Get detailed CPU information"""
        def _compute_cpu_info():
            try:
                # Get basic CPU info
                cpu_freq = psutil.cpu_freq()
                cpu_count_physical = psutil.cpu_count(logical=False)
                cpu_count_logical = psutil.cpu_count(logical=True)
                
                cpu_info = CPUInfo(
                    brand=platform.processor() or "Unknown",
                    architecture=platform.machine(),
                    cores_physical=cpu_count_physical or 1,
                    cores_logical=cpu_count_logical or 1,
                    frequency_max=cpu_freq.max if cpu_freq else 0.0,
                    frequency_current=cpu_freq.current if cpu_freq else 0.0,
                    features=[]
                )
                
                # Get detailed CPU info if available
                if CPUINFO_AVAILABLE:
                    detailed_info = cpuinfo.get_cpu_info()
                    cpu_info.brand = detailed_info.get('brand_raw', cpu_info.brand)
                    cpu_info.features = detailed_info.get('flags', [])
                    
                    # Try to get cache info
                    for key in ['l1_data_cache_size', 'l1_instruction_cache_size']:
                        if key in detailed_info:
                            cpu_info.cache_l1 = detailed_info[key]
                            break
                    
                    cpu_info.cache_l2 = detailed_info.get('l2_cache_size')
                    cpu_info.cache_l3 = detailed_info.get('l3_cache_size')
                
                return cpu_info
                
            except Exception as e:
                self.logger.warning(f"Failed to get CPU info: {e}")
                return CPUInfo(
                    brand="Unknown",
                    architecture=platform.machine(),
                    cores_physical=1,
                    cores_logical=1,
                    frequency_max=0.0,
                    frequency_current=0.0
                )
        
        return self._get_cached_or_compute('cpu_info', _compute_cpu_info, 300)  # Cache for 5 minutes
    
    def get_memory_info(self) -> MemoryInfo:
        """Get detailed memory information"""
        def _compute_memory_info():
            try:
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                
                return MemoryInfo(
                    total_gb=memory.total / (1024**3),
                    available_gb=memory.available / (1024**3),
                    used_gb=memory.used / (1024**3),
                    usage_percent=memory.percent,
                    swap_total_gb=swap.total / (1024**3),
                    swap_used_gb=swap.used / (1024**3),
                    swap_percent=swap.percent
                )
                
            except Exception as e:
                self.logger.warning(f"Failed to get memory info: {e}")
                return MemoryInfo(0, 0, 0, 0, 0, 0, 0)
        
        return self._get_cached_or_compute('memory_info', _compute_memory_info, 5)  # Cache for 5 seconds
    
    def get_gpu_info(self) -> List[GPUInfo]:
        """Get detailed GPU information"""
        def _compute_gpu_info():
            gpus = []
            
            try:
                if GPU_AVAILABLE:
                    # Get NVIDIA GPUs
                    nvidia_gpus = GPUtil.getGPUs()
                    for gpu in nvidia_gpus:
                        gpus.append(GPUInfo(
                            name=gpu.name,
                            type='discrete',
                            memory_total_mb=gpu.memoryTotal,
                            memory_used_mb=gpu.memoryUsed,
                            driver_version=gpu.driver,
                            cuda_support=True,
                            vulkan_support=self.capabilities['vulkan_support']
                        ))
                
                # Try to detect integrated graphics
                try:
                    # Check for Intel integrated graphics
                    lspci_output = subprocess.run(['lspci'], capture_output=True, text=True)
                    if lspci_output.returncode == 0:
                        for line in lspci_output.stdout.split('\n'):
                            if 'VGA' in line or 'Display' in line:
                                if 'Intel' in line:
                                    gpus.append(GPUInfo(
                                        name=line.split(':')[-1].strip(),
                                        type='integrated',
                                        cuda_support=False,
                                        vulkan_support=self.capabilities['vulkan_support']
                                    ))
                                elif 'AMD' in line and not any(gpu.name in line for gpu in gpus):
                                    gpus.append(GPUInfo(
                                        name=line.split(':')[-1].strip(),
                                        type='discrete' if 'Radeon' in line else 'integrated',
                                        cuda_support=False,
                                        vulkan_support=self.capabilities['vulkan_support']
                                    ))
                except:
                    pass
                
                # If no GPUs detected, assume integrated graphics
                if not gpus:
                    gpus.append(GPUInfo(
                        name="Unknown Integrated Graphics",
                        type='integrated',
                        cuda_support=False,
                        vulkan_support=self.capabilities['vulkan_support']
                    ))
                
                return gpus
                
            except Exception as e:
                self.logger.warning(f"Failed to get GPU info: {e}")
                return [GPUInfo(name="Unknown", type='unknown')]
        
        return self._get_cached_or_compute('gpu_info', _compute_gpu_info, 60)  # Cache for 1 minute
    
    def get_storage_info(self) -> List[StorageInfo]:
        """Get detailed storage information"""
        def _compute_storage_info():
            storage_devices = []
            
            try:
                # Get disk usage for all mount points
                disk_partitions = psutil.disk_partitions()
                
                for partition in disk_partitions:
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        
                        # Determine storage type
                        storage_type = self._detect_storage_type(partition.device)
                        
                        storage_devices.append(StorageInfo(
                            total_gb=usage.total / (1024**3),
                            used_gb=usage.used / (1024**3),
                            free_gb=usage.free / (1024**3),
                            usage_percent=(usage.used / usage.total) * 100,
                            type=storage_type,
                            filesystem=partition.fstype,
                            mount_point=partition.mountpoint
                        ))
                        
                    except PermissionError:
                        # Skip inaccessible mount points
                        continue
                
                return storage_devices
                
            except Exception as e:
                self.logger.warning(f"Failed to get storage info: {e}")
                return []
        
        return self._get_cached_or_compute('storage_info', _compute_storage_info, 30)  # Cache for 30 seconds
    
    def _detect_storage_type(self, device: str) -> str:
        """Detect if storage device is SSD or HDD"""
        try:
            # Extract device name (e.g., sda from /dev/sda1)
            device_name = device.split('/')[-1].rstrip('0123456789')
            
            # Check rotational status
            rotational_path = f"/sys/block/{device_name}/queue/rotational"
            if Path(rotational_path).exists():
                with open(rotational_path, 'r') as f:
                    rotational = f.read().strip()
                    return 'hdd' if rotational == '1' else 'ssd'
            
            # Fallback: check if it's an NVMe device
            if 'nvme' in device_name:
                return 'ssd'
            
            return 'unknown'
            
        except:
            return 'unknown'
    
    def get_network_info(self) -> List[NetworkInfo]:
        """Get network interface information"""
        def _compute_network_info():
            interfaces = []
            
            try:
                # Get network interface statistics
                net_io = psutil.net_io_counters(pernic=True)
                net_if_addrs = psutil.net_if_addrs()
                net_if_stats = psutil.net_if_stats()
                
                for interface_name, io_stats in net_io.items():
                    if interface_name in net_if_stats:
                        stats = net_if_stats[interface_name]
                        
                        interfaces.append(NetworkInfo(
                            interface=interface_name,
                            speed_mbps=stats.speed if stats.speed != 0 else None,
                            bytes_sent=io_stats.bytes_sent,
                            bytes_recv=io_stats.bytes_recv,
                            packets_sent=io_stats.packets_sent,
                            packets_recv=io_stats.packets_recv,
                            is_up=stats.isup
                        ))
                
                return interfaces
                
            except Exception as e:
                self.logger.warning(f"Failed to get network info: {e}")
                return []
        
        return self._get_cached_or_compute('network_info', _compute_network_info, 10)  # Cache for 10 seconds
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': self.get_memory_info(),
            'disk_io': psutil.disk_io_counters(),
            'network_io': psutil.net_io_counters(),
            'boot_time': psutil.boot_time(),
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
    
    def get_detailed_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            'system': {
                'platform': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor()
            },
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'gpu': self.get_gpu_info(),
            'storage': self.get_storage_info(),
            'network': self.get_network_info(),
            'capabilities': self.capabilities
        }
    
    def get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        return psutil.virtual_memory().percent
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        return psutil.cpu_percent(interval=1)
    
    def get_gpu_usage(self) -> float:
        """Get current GPU usage percentage"""
        try:
            if GPU_AVAILABLE:
                gpus = GPUtil.getGPUs()
                if gpus:
                    return gpus[0].load * 100
            return 0.0
        except:
            return 0.0
    
    def get_storage_usage(self) -> float:
        """Get current storage usage percentage"""
        try:
            usage = psutil.disk_usage('/')
            return (usage.used / usage.total) * 100
        except:
            return 0.0
    
    def get_network_usage(self) -> Tuple[float, float]:
        """Get current network usage (upload, download) in MB/s"""
        try:
            current_stats = psutil.net_io_counters()
            current_time = time.time()
            
            if self._last_network_stats and self._last_network_time:
                time_delta = current_time - self._last_network_time
                bytes_sent_delta = current_stats.bytes_sent - self._last_network_stats.bytes_sent
                bytes_recv_delta = current_stats.bytes_recv - self._last_network_stats.bytes_recv
                
                upload_mbps = (bytes_sent_delta / time_delta) / (1024 * 1024)
                download_mbps = (bytes_recv_delta / time_delta) / (1024 * 1024)
            else:
                upload_mbps = download_mbps = 0.0
            
            self._last_network_stats = current_stats
            self._last_network_time = current_time
            
            return upload_mbps, download_mbps
            
        except:
            return 0.0, 0.0
    
    def is_low_end_system(self) -> bool:
        """Determine if this is a low-end system that needs aggressive optimization"""
        memory_info = self.get_memory_info()
        cpu_info = self.get_cpu_info()
        gpu_info = self.get_gpu_info()
        
        # Consider low-end if:
        # - Less than 6GB RAM
        # - Less than 4 CPU cores
        # - Only integrated graphics
        return (
            memory_info.total_gb < 6 or
            cpu_info.cores_logical < 4 or
            all(gpu.type == 'integrated' for gpu in gpu_info)
        )
    
    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get optimization recommendations based on system specs"""
        memory_info = self.get_memory_info()
        cpu_info = self.get_cpu_info()
        gpu_info = self.get_gpu_info()
        storage_info = self.get_storage_info()
        
        recommendations = {
            'memory': {
                'enable_zram': memory_info.total_gb < 8,
                'zram_size_percent': 30 if memory_info.total_gb < 4 else 20,
                'enable_ksm': True,
                'aggressive_mode': memory_info.total_gb < 6
            },
            'gpu': {
                'enable_llvmpipe': all(gpu.type == 'integrated' for gpu in gpu_info),
                'software_rendering_threads': max(1, cpu_info.cores_logical - 1),
                'enable_dxvk': True,
                'ai_upscaling': all(gpu.type == 'integrated' for gpu in gpu_info)
            },
            'storage': {
                'compression_level': 6 if any(s.type == 'ssd' for s in storage_info) else 9,
                'enable_deduplication': True,
                'cache_size_gb': min(2, memory_info.total_gb * 0.1)
            },
            'performance_mode': 'extreme' if self.is_low_end_system() else 'balanced'
        }
        
        return recommendations
    
    def monitor_system_health(self) -> Dict[str, str]:
        """Monitor system health and return status"""
        memory_info = self.get_memory_info()
        cpu_usage = self.get_cpu_usage()
        storage_info = self.get_storage_info()
        
        health_status = {
            'memory': 'good',
            'cpu': 'good',
            'storage': 'good',
            'overall': 'good'
        }
        
        # Check memory health
        if memory_info.usage_percent > 90:
            health_status['memory'] = 'critical'
        elif memory_info.usage_percent > 80:
            health_status['memory'] = 'warning'
        
        # Check CPU health
        if cpu_usage > 95:
            health_status['cpu'] = 'critical'
        elif cpu_usage > 85:
            health_status['cpu'] = 'warning'
        
        # Check storage health
        for storage in storage_info:
            if storage.usage_percent > 95:
                health_status['storage'] = 'critical'
                break
            elif storage.usage_percent > 85:
                health_status['storage'] = 'warning'
        
        # Overall health
        if any(status == 'critical' for status in health_status.values()):
            health_status['overall'] = 'critical'
        elif any(status == 'warning' for status in health_status.values()):
            health_status['overall'] = 'warning'
        
        return health_status