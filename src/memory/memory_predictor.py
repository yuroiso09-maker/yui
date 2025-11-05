"""
OTIS Memory Predictor
AI-powered memory usage prediction and optimization
"""

import asyncio
import time
import numpy as np
from typing import Dict, Any, List, Optional
from collections import deque
from loguru import logger


class MemoryPredictor:
    """
    AI-powered memory predictor that learns usage patterns
    and predicts future memory needs
    """
    
    def __init__(self, config):
        self.config = config
        self.is_running = False
        self.memory_history = deque(maxlen=1000)  # Keep last 1000 measurements
        self.predictions = {}
        self.learning_enabled = config.ai_prediction
        
        logger.info("🧠 Memory Predictor initialized")
    
    async def start(self) -> bool:
        """Start memory predictor"""
        if not self.learning_enabled:
            return True
        
        self.is_running = True
        asyncio.create_task(self._prediction_loop())
        logger.success("✅ Memory predictor started")
        return True
    
    async def stop(self) -> bool:
        """Stop memory predictor"""
        self.is_running = False
        logger.success("✅ Memory predictor stopped")
        return True
    
    async def _prediction_loop(self):
        """Main prediction loop"""
        while self.is_running:
            try:
                await self._collect_memory_data()
                await self._generate_predictions()
                await asyncio.sleep(30)  # Predict every 30 seconds
            except Exception as e:
                logger.error(f"Error in prediction loop: {e}")
                await asyncio.sleep(60)
    
    async def _collect_memory_data(self):
        """Collect memory usage data"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            data_point = {
                'timestamp': time.time(),
                'usage_percent': memory.percent,
                'available_gb': memory.available / (1024**3),
                'used_gb': memory.used / (1024**3)
            }
            
            self.memory_history.append(data_point)
            
        except Exception as e:
            logger.error(f"Failed to collect memory data: {e}")
    
    async def _generate_predictions(self):
        """Generate memory usage predictions"""
        if len(self.memory_history) < 10:
            return
        
        try:
            # Simple trend analysis for now
            recent_usage = [point['usage_percent'] for point in list(self.memory_history)[-10:]]
            
            # Calculate trend
            if len(recent_usage) >= 2:
                trend = (recent_usage[-1] - recent_usage[0]) / len(recent_usage)
                
                # Predict next 5 minutes
                current_usage = recent_usage[-1]
                predicted_usage = max(0, min(100, current_usage + (trend * 10)))  # 10 = 5 minutes / 30 seconds
                
                self.predictions = {
                    'memory_usage_percent': predicted_usage,
                    'trend': trend,
                    'confidence': min(100, len(self.memory_history) / 10),
                    'timestamp': time.time(),
                    'applications': []  # Would be populated by app analysis
                }
            
        except Exception as e:
            logger.error(f"Failed to generate predictions: {e}")
    
    async def predict_memory_needs(self) -> Dict[str, Any]:
        """Get current memory predictions"""
        return self.predictions.copy()
    
    async def get_current_predictions(self) -> Dict[str, Any]:
        """Get current predictions"""
        return await self.predict_memory_needs()
    
    async def get_status(self) -> Dict[str, Any]:
        """Get predictor status"""
        return {
            'enabled': self.learning_enabled,
            'running': self.is_running,
            'data_points': len(self.memory_history),
            'predictions': self.predictions
        }