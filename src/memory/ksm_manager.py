"""
OTIS KSM (Kernel Samepage Merging) Manager
Advanced memory deduplication for massive memory savings
"""

import asyncio
import time
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger


class KSMManager:
    """
    Kernel Samepage Merging manager for memory deduplication
    Can save 30-50% of memory by merging identical pages
    """
    
    def __init__(self, config):
        self.config = config
        self.is_running = False
        self.ksm_stats = {}
        self.ksm_path = Path('/sys/kernel/mm/ksm')
        
        logger.info("🔄 KSM Manager initialized")
    
    async def start(self) -> bool:
        """Start KSM with optimal configuration"""
        if not self.ksm_path.exists():
            logger.warning("KSM not available on this system")
            return False
        
        try:
            # Enable KSM
            await self._write_ksm_param('run', '1')
            
            # Configure KSM parameters
            await self._configure_ksm_parameters()
            
            self.is_running = True
            asyncio.create_task(self._monitor_ksm())
            
            logger.success("✅ KSM started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start KSM: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop KSM"""
        try:
            await self._write_ksm_param('run', '0')
            self.is_running = False
            logger.success("✅ KSM stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop KSM: {e}")
            return False
    
    async def _configure_ksm_parameters(self):
        """Configure KSM parameters for optimal performance"""
        try:
            # Set scan parameters based on system memory
            import psutil
            total_memory_gb = psutil.virtual_memory().total / (1024**3)
            
            if total_memory_gb <= 4:
                # Aggressive settings for low memory systems
                await self._write_ksm_param('pages_to_scan', '1000')
                await self._write_ksm_param('sleep_millisecs', '20')
            elif total_memory_gb <= 8:
                # Balanced settings
                await self._write_ksm_param('pages_to_scan', '500')
                await self._write_ksm_param('sleep_millisecs', '50')
            else:
                # Conservative settings for high memory systems
                await self._write_ksm_param('pages_to_scan', '200')
                await self._write_ksm_param('sleep_millisecs', '100')
            
            logger.info("KSM parameters configured")
            
        except Exception as e:
            logger.error(f"Failed to configure KSM parameters: {e}")
    
    async def _write_ksm_param(self, param: str, value: str):
        """Write KSM parameter"""
        param_path = self.ksm_path / param
        if param_path.exists():
            process = await asyncio.create_subprocess_exec(
                'sudo', 'sh', '-c', f'echo {value} > {param_path}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
    
    async def _read_ksm_param(self, param: str) -> Optional[str]:
        """Read KSM parameter"""
        param_path = self.ksm_path / param
        if param_path.exists():
            try:
                with open(param_path, 'r') as f:
                    return f.read().strip()
            except:
                return None
        return None
    
    async def _monitor_ksm(self):
        """Monitor KSM performance"""
        while self.is_running:
            try:
                await self._update_ksm_stats()
                await asyncio.sleep(60)  # Update every minute
            except Exception as e:
                logger.error(f"Error monitoring KSM: {e}")
                await asyncio.sleep(120)
    
    async def _update_ksm_stats(self):
        """Update KSM statistics"""
        try:
            stats = {}
            
            # Read KSM statistics
            for param in ['pages_shared', 'pages_sharing', 'pages_unshared', 'pages_volatile']:
                value = await self._read_ksm_param(param)
                if value:
                    stats[param] = int(value)
            
            # Calculate savings
            pages_shared = stats.get('pages_shared', 0)
            pages_sharing = stats.get('pages_sharing', 0)
            
            if pages_shared > 0:
                # Each shared page saves (pages_sharing - pages_shared) pages
                saved_pages = pages_sharing - pages_shared
                saved_mb = (saved_pages * 4096) / (1024 * 1024)  # Assuming 4KB pages
                savings_gb = saved_mb / 1024
            else:
                savings_gb = 0
            
            self.ksm_stats = {
                **stats,
                'savings_gb': savings_gb,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to update KSM stats: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get KSM statistics"""
        return self.ksm_stats.copy()
    
    async def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed KSM statistics"""
        return await self.get_stats()
    
    async def get_status(self) -> Dict[str, Any]:
        """Get KSM status"""
        return {
            'enabled': self.is_running,
            'available': self.ksm_path.exists(),
            'stats': await self.get_stats()
        }
    
    async def enable_aggressive_mode(self):
        """Enable aggressive KSM scanning"""
        await self._write_ksm_param('pages_to_scan', '2000')
        await self._write_ksm_param('sleep_millisecs', '10')
    
    async def enable_balanced_mode(self):
        """Enable balanced KSM scanning"""
        await self._write_ksm_param('pages_to_scan', '500')
        await self._write_ksm_param('sleep_millisecs', '50')
    
    async def optimize_for_app_type(self, app_type: str):
        """Optimize KSM for specific application type"""
        if app_type == 'gaming':
            # Gaming: reduce KSM activity to avoid latency
            await self._write_ksm_param('pages_to_scan', '100')
            await self._write_ksm_param('sleep_millisecs', '200')
        elif app_type == 'office':
            # Office: aggressive merging for document data
            await self.enable_aggressive_mode()
    
    async def optimize_for_gaming(self):
        """Optimize KSM for gaming"""
        await self.optimize_for_app_type('gaming')
    
    async def optimize_for_office(self):
        """Optimize KSM for office applications"""
        await self.optimize_for_app_type('office')
    
    async def force_merge_cycle(self):
        """Force immediate KSM merge cycle"""
        # Temporarily increase scan rate
        await self._write_ksm_param('pages_to_scan', '5000')
        await asyncio.sleep(5)
        await self._configure_ksm_parameters()  # Restore normal settings