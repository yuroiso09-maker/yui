"""
OTIS zRAM Manager
Advanced zRAM management for extreme memory compression and expansion
"""

import asyncio
import subprocess
import os
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from loguru import logger


class ZRAMManager:
    """
    Advanced zRAM manager that can achieve 5:1+ compression ratios
    and dynamically adjust based on system needs
    """
    
    def __init__(self, config):
        self.config = config
        self.is_running = False
        self.zram_devices = []
        self.compression_stats = {}
        self.dynamic_expansion_enabled = False
        
        # Compression algorithms by performance/ratio
        self.compression_algorithms = {
            'lz4': {'speed': 'fastest', 'ratio': 2.5, 'cpu_usage': 'low'},
            'lzo': {'speed': 'fast', 'ratio': 2.8, 'cpu_usage': 'low'},
            'zstd': {'speed': 'medium', 'ratio': 4.5, 'cpu_usage': 'medium'},
            'lz4hc': {'speed': 'slow', 'ratio': 3.2, 'cpu_usage': 'medium'}
        }
        
        logger.info("💾 zRAM Manager initialized")
    
    async def start(self) -> bool:
        """Start zRAM with optimal configuration"""
        if self.is_running:
            return True
        
        try:
            # Check if zRAM is available
            if not await self._check_zram_availability():
                logger.error("zRAM is not available on this system")
                return False
            
            # Calculate optimal zRAM size
            zram_size_mb = await self._calculate_optimal_size()
            
            # Setup zRAM devices
            await self._setup_zram_devices(zram_size_mb)
            
            # Configure compression
            await self._configure_compression()
            
            # Enable zRAM devices
            await self._enable_zram_devices()
            
            # Start monitoring
            self.is_running = True
            asyncio.create_task(self._monitor_zram_performance())
            
            logger.success(f"✅ zRAM started with {zram_size_mb}MB capacity")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start zRAM: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop zRAM and cleanup"""
        if not self.is_running:
            return True
        
        try:
            self.is_running = False
            
            # Disable zRAM devices
            for device in self.zram_devices:
                await self._disable_zram_device(device)
            
            self.zram_devices.clear()
            logger.success("✅ zRAM stopped and cleaned up")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop zRAM: {e}")
            return False
    
    async def _check_zram_availability(self) -> bool:
        """Check if zRAM is available on the system"""
        try:
            # Check if zRAM module is loaded
            result = await self._run_command(['lsmod'])
            if 'zram' not in result.stdout:
                # Try to load zRAM module
                await self._run_command(['sudo', 'modprobe', 'zram'])
            
            # Check for zRAM control interface
            return Path('/sys/class/zram-control').exists() or Path('/dev/zram0').exists()
            
        except Exception as e:
            logger.warning(f"Error checking zRAM availability: {e}")
            return False
    
    async def _calculate_optimal_size(self) -> int:
        """Calculate optimal zRAM size based on system memory and configuration"""
        try:
            # Get total system memory
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            total_memory_kb = 0
            for line in meminfo.split('\n'):
                if line.startswith('MemTotal:'):
                    total_memory_kb = int(line.split()[1])
                    break
            
            total_memory_mb = total_memory_kb // 1024
            
            # Calculate zRAM size as percentage of total memory
            zram_size_mb = int(total_memory_mb * (self.config.zram_size_percent / 100))
            
            # Apply limits
            min_size_mb = 512  # Minimum 512MB
            max_size_mb = total_memory_mb // 2  # Maximum 50% of total memory
            
            zram_size_mb = max(min_size_mb, min(zram_size_mb, max_size_mb))
            
            logger.info(f"Calculated optimal zRAM size: {zram_size_mb}MB ({self.config.zram_size_percent}% of {total_memory_mb}MB)")
            return zram_size_mb
            
        except Exception as e:
            logger.error(f"Failed to calculate zRAM size: {e}")
            return 1024  # Default 1GB
    
    async def _setup_zram_devices(self, size_mb: int):
        """Setup zRAM devices"""
        try:
            # Determine number of devices (usually 1 per CPU core, max 4)
            import psutil
            num_cores = psutil.cpu_count(logical=True)
            num_devices = min(4, max(1, num_cores))
            
            # Size per device
            size_per_device_mb = size_mb // num_devices
            
            for i in range(num_devices):
                device_path = f'/dev/zram{i}'
                
                # Create zRAM device if it doesn't exist
                if not Path(device_path).exists():
                    await self._create_zram_device(i)
                
                # Set device size
                await self._set_zram_device_size(i, size_per_device_mb)
                
                self.zram_devices.append({
                    'id': i,
                    'path': device_path,
                    'size_mb': size_per_device_mb
                })
            
            logger.info(f"Setup {num_devices} zRAM devices, {size_per_device_mb}MB each")
            
        except Exception as e:
            logger.error(f"Failed to setup zRAM devices: {e}")
            raise
    
    async def _create_zram_device(self, device_id: int):
        """Create a zRAM device"""
        try:
            # Try using zramctl (modern method)
            try:
                await self._run_command(['sudo', 'zramctl', '--find', '--size', '1M'])
                return
            except:
                pass
            
            # Fallback to manual creation
            control_path = '/sys/class/zram-control/hot_add'
            if Path(control_path).exists():
                with open(control_path, 'w') as f:
                    f.write(str(device_id))
            
        except Exception as e:
            logger.warning(f"Failed to create zRAM device {device_id}: {e}")
    
    async def _set_zram_device_size(self, device_id: int, size_mb: int):
        """Set zRAM device size"""
        try:
            size_bytes = size_mb * 1024 * 1024
            disksize_path = f'/sys/block/zram{device_id}/disksize'
            
            if Path(disksize_path).exists():
                await self._run_command(['sudo', 'sh', '-c', f'echo {size_bytes} > {disksize_path}'])
            else:
                logger.warning(f"Cannot set size for zRAM device {device_id}: path not found")
            
        except Exception as e:
            logger.error(f"Failed to set zRAM device size: {e}")
    
    async def _configure_compression(self):
        """Configure compression algorithm for zRAM devices"""
        try:
            algorithm = self.config.compression_algorithm
            
            for device in self.zram_devices:
                device_id = device['id']
                comp_algorithm_path = f'/sys/block/zram{device_id}/comp_algorithm'
                
                if Path(comp_algorithm_path).exists():
                    # Check available algorithms
                    with open(comp_algorithm_path, 'r') as f:
                        available_algorithms = f.read().strip()
                    
                    if algorithm in available_algorithms:
                        await self._run_command(['sudo', 'sh', '-c', f'echo {algorithm} > {comp_algorithm_path}'])
                        logger.info(f"Set compression algorithm to {algorithm} for zRAM{device_id}")
                    else:
                        logger.warning(f"Algorithm {algorithm} not available for zRAM{device_id}, using default")
                
        except Exception as e:
            logger.error(f"Failed to configure compression: {e}")
    
    async def _enable_zram_devices(self):
        """Enable zRAM devices as swap"""
        try:
            for device in self.zram_devices:
                device_path = device['path']
                
                # Format as swap
                await self._run_command(['sudo', 'mkswap', device_path])
                
                # Enable swap with high priority
                priority = 100  # Higher priority than disk swap
                await self._run_command(['sudo', 'swapon', '-p', str(priority), device_path])
                
                logger.info(f"Enabled {device_path} as swap with priority {priority}")
            
        except Exception as e:
            logger.error(f"Failed to enable zRAM devices: {e}")
            raise
    
    async def _disable_zram_device(self, device: Dict[str, Any]):
        """Disable a zRAM device"""
        try:
            device_path = device['path']
            
            # Disable swap
            await self._run_command(['sudo', 'swapoff', device_path])
            
            # Reset device
            device_id = device['id']
            reset_path = f'/sys/block/zram{device_id}/reset'
            if Path(reset_path).exists():
                await self._run_command(['sudo', 'sh', '-c', f'echo 1 > {reset_path}'])
            
            logger.info(f"Disabled zRAM device {device_path}")
            
        except Exception as e:
            logger.warning(f"Failed to disable zRAM device: {e}")
    
    async def _monitor_zram_performance(self):
        """Monitor zRAM performance and adjust if needed"""
        while self.is_running:
            try:
                await self._update_compression_stats()
                await self._check_performance_optimization()
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in zRAM monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _update_compression_stats(self):
        """Update compression statistics"""
        try:
            total_orig_data_size = 0
            total_compr_data_size = 0
            total_mem_used_total = 0
            
            for device in self.zram_devices:
                device_id = device['id']
                stats_path = f'/sys/block/zram{device_id}'
                
                if Path(stats_path).exists():
                    # Read statistics
                    stats = {}
                    for stat_file in ['orig_data_size', 'compr_data_size', 'mem_used_total']:
                        stat_path = Path(stats_path) / stat_file
                        if stat_path.exists():
                            with open(stat_path, 'r') as f:
                                stats[stat_file] = int(f.read().strip())
                    
                    total_orig_data_size += stats.get('orig_data_size', 0)
                    total_compr_data_size += stats.get('compr_data_size', 0)
                    total_mem_used_total += stats.get('mem_used_total', 0)
            
            # Calculate compression ratio
            if total_compr_data_size > 0:
                compression_ratio = total_orig_data_size / total_compr_data_size
            else:
                compression_ratio = 1.0
            
            self.compression_stats = {
                'orig_data_size_mb': total_orig_data_size / (1024 * 1024),
                'compr_data_size_mb': total_compr_data_size / (1024 * 1024),
                'mem_used_total_mb': total_mem_used_total / (1024 * 1024),
                'compression_ratio': compression_ratio,
                'effective_size_gb': (total_orig_data_size / (1024 * 1024 * 1024)),
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to update compression stats: {e}")
    
    async def _check_performance_optimization(self):
        """Check if performance optimization is needed"""
        try:
            if not self.compression_stats:
                return
            
            compression_ratio = self.compression_stats['compression_ratio']
            
            # If compression ratio is too low, try different algorithm
            if compression_ratio < 2.0 and self.config.compression_algorithm != 'zstd':
                logger.info("Low compression ratio detected, switching to zstd")
                await self._switch_compression_algorithm('zstd')
            
            # If memory usage is high, enable dynamic expansion
            mem_used_mb = self.compression_stats['mem_used_total_mb']
            total_zram_size_mb = sum(device['size_mb'] for device in self.zram_devices)
            
            if mem_used_mb > total_zram_size_mb * 0.8:  # 80% usage
                if not self.dynamic_expansion_enabled:
                    await self._enable_dynamic_expansion()
            
        except Exception as e:
            logger.error(f"Error in performance optimization check: {e}")
    
    async def _switch_compression_algorithm(self, new_algorithm: str):
        """Switch to a different compression algorithm"""
        try:
            logger.info(f"Switching zRAM compression algorithm to {new_algorithm}")
            
            # This requires recreating zRAM devices
            await self.stop()
            self.config.compression_algorithm = new_algorithm
            await self.start()
            
        except Exception as e:
            logger.error(f"Failed to switch compression algorithm: {e}")
    
    async def _enable_dynamic_expansion(self):
        """Enable dynamic zRAM expansion"""
        try:
            if self.dynamic_expansion_enabled:
                return
            
            logger.info("🚀 Enabling dynamic zRAM expansion")
            
            # Add additional zRAM device
            new_device_id = len(self.zram_devices)
            additional_size_mb = 512  # Add 512MB
            
            await self._create_zram_device(new_device_id)
            await self._set_zram_device_size(new_device_id, additional_size_mb)
            
            # Configure and enable
            device_path = f'/dev/zram{new_device_id}'
            await self._run_command(['sudo', 'mkswap', device_path])
            await self._run_command(['sudo', 'swapon', '-p', '90', device_path])
            
            self.zram_devices.append({
                'id': new_device_id,
                'path': device_path,
                'size_mb': additional_size_mb
            })
            
            self.dynamic_expansion_enabled = True
            logger.success(f"✅ Added {additional_size_mb}MB zRAM expansion")
            
        except Exception as e:
            logger.error(f"Failed to enable dynamic expansion: {e}")
    
    async def _run_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """Run system command asynchronously"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return subprocess.CompletedProcess(
                command, process.returncode, stdout.decode(), stderr.decode()
            )
            
        except Exception as e:
            logger.error(f"Command failed: {' '.join(command)} - {e}")
            raise
    
    # Public interface methods
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get current zRAM statistics"""
        return self.compression_stats.copy() if self.compression_stats else {}
    
    async def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed zRAM statistics"""
        stats = await self.get_stats()
        stats.update({
            'devices': self.zram_devices.copy(),
            'algorithm': self.config.compression_algorithm,
            'dynamic_expansion_enabled': self.dynamic_expansion_enabled,
            'total_devices': len(self.zram_devices)
        })
        return stats
    
    async def get_status(self) -> Dict[str, Any]:
        """Get zRAM manager status"""
        return {
            'enabled': self.is_running,
            'devices': len(self.zram_devices),
            'algorithm': self.config.compression_algorithm,
            'stats': await self.get_stats()
        }
    
    async def increase_compression(self):
        """Increase compression aggressiveness"""
        if self.config.compression_algorithm != 'zstd':
            await self._switch_compression_algorithm('zstd')
    
    async def optimize_for_performance(self):
        """Optimize for performance over compression ratio"""
        if self.config.compression_algorithm != 'lz4':
            await self._switch_compression_algorithm('lz4')
    
    async def expand_if_needed(self):
        """Expand zRAM if needed"""
        if not self.dynamic_expansion_enabled:
            await self._enable_dynamic_expansion()
    
    async def expand_dynamically(self):
        """Force dynamic expansion"""
        await self._enable_dynamic_expansion()
    
    async def prepare_for_high_usage(self):
        """Prepare for high memory usage"""
        await self.expand_if_needed()
        await self.increase_compression()
    
    async def optimize_for_low_usage(self):
        """Optimize for low memory usage"""
        await self.optimize_for_performance()
    
    async def optimize_for_gaming(self):
        """Optimize zRAM for gaming (low latency)"""
        await self._switch_compression_algorithm('lz4')
    
    async def optimize_for_media(self):
        """Optimize zRAM for media applications"""
        await self._switch_compression_algorithm('lzo')
    
    async def force_compression_cycle(self):
        """Force a compression cycle"""
        try:
            # Trigger compression by temporarily reducing memory pressure
            for device in self.zram_devices:
                device_id = device['id']
                idle_path = f'/sys/block/zram{device_id}/idle'
                if Path(idle_path).exists():
                    await self._run_command(['sudo', 'sh', '-c', f'echo all > {idle_path}'])
            
            logger.info("Forced zRAM compression cycle")
            
        except Exception as e:
            logger.error(f"Failed to force compression cycle: {e}")
    
    async def get_compression_efficiency(self) -> float:
        """Get compression efficiency score (0-100)"""
        if not self.compression_stats:
            return 0.0
        
        compression_ratio = self.compression_stats.get('compression_ratio', 1.0)
        
        # Score based on compression ratio (5:1 = 100 points)
        efficiency = min(100, (compression_ratio - 1) * 25)
        return efficiency