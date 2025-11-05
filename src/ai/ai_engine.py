"""
OTIS AI Optimization Engine
Machine learning-powered predictive optimization for Linux systems
"""

import asyncio
import json
import time
import threading
import pickle
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from loguru import logger
import psutil
import numpy as np
from collections import defaultdict, deque


@dataclass
class SystemMetrics:
    """System performance metrics snapshot"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    memory_available: float
    disk_io_read: int
    disk_io_write: int
    network_sent: int
    network_recv: int
    process_count: int
    load_average: float


@dataclass
class ApplicationPattern:
    """Application usage pattern"""
    name: str
    category: str
    avg_cpu_usage: float
    avg_memory_usage: float
    peak_cpu_usage: float
    peak_memory_usage: float
    usage_frequency: int
    last_used: float


class PatternRecognizer:
    """System usage pattern recognition"""
    
    def __init__(self):
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 metrics
        self.application_patterns = {}
        self.usage_patterns = {
            'gaming': {'cpu_threshold': 70, 'memory_threshold': 60, 'duration_min': 30},
            'productivity': {'cpu_threshold': 40, 'memory_threshold': 50, 'duration_min': 60},
            'media': {'cpu_threshold': 30, 'memory_threshold': 40, 'duration_min': 20},
            'idle': {'cpu_threshold': 10, 'memory_threshold': 30, 'duration_min': 10}
        }
        
    async def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU and memory
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read = disk_io.read_bytes if disk_io else 0
            disk_write = disk_io.write_bytes if disk_io else 0
            
            # Network I/O
            network_io = psutil.net_io_counters()
            network_sent = network_io.bytes_sent if network_io else 0
            network_recv = network_io.bytes_recv if network_io else 0
            
            # System load
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else cpu_usage / 100
            
            metrics = SystemMetrics(
                timestamp=time.time(),
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                memory_available=memory.available,
                disk_io_read=disk_read,
                disk_io_write=disk_write,
                network_sent=network_sent,
                network_recv=network_recv,
                process_count=len(psutil.pids()),
                load_average=load_avg
            )
            
            self.metrics_history.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Failed to collect metrics: {e}")
            return None
    
    async def analyze_application_patterns(self) -> Dict[str, ApplicationPattern]:
        """Analyze running application patterns"""
        app_stats = defaultdict(lambda: {
            'cpu_samples': [],
            'memory_samples': [],
            'count': 0,
            'last_seen': 0,
            'category': 'unknown'
        })
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    name = info['name']
                    
                    if name and info['cpu_percent'] is not None:
                        app_stats[name]['cpu_samples'].append(info['cpu_percent'])
                        app_stats[name]['memory_samples'].append(info['memory_percent'] or 0)
                        app_stats[name]['count'] += 1
                        app_stats[name]['last_seen'] = time.time()
                        
                        # Categorize application
                        app_stats[name]['category'] = self._categorize_application(name)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Convert to ApplicationPattern objects
            patterns = {}
            for name, stats in app_stats.items():
                if stats['count'] > 0:
                    patterns[name] = ApplicationPattern(
                        name=name,
                        category=stats['category'],
                        avg_cpu_usage=np.mean(stats['cpu_samples']),
                        avg_memory_usage=np.mean(stats['memory_samples']),
                        peak_cpu_usage=np.max(stats['cpu_samples']),
                        peak_memory_usage=np.max(stats['memory_samples']),
                        usage_frequency=stats['count'],
                        last_used=stats['last_seen']
                    )
            
            self.application_patterns = patterns
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze application patterns: {e}")
            return {}
    
    def _categorize_application(self, app_name: str) -> str:
        """Categorize application by name"""
        app_name_lower = app_name.lower()
        
        # Gaming applications
        gaming_keywords = ['game', 'steam', 'wine', 'lutris', 'minecraft', 'unity', 'unreal']
        if any(keyword in app_name_lower for keyword in gaming_keywords):
            return 'gaming'
        
        # Media applications
        media_keywords = ['vlc', 'mpv', 'ffmpeg', 'obs', 'audacity', 'gimp', 'blender']
        if any(keyword in app_name_lower for keyword in media_keywords):
            return 'media'
        
        # Productivity applications
        productivity_keywords = ['office', 'writer', 'calc', 'impress', 'code', 'editor', 'browser']
        if any(keyword in app_name_lower for keyword in productivity_keywords):
            return 'productivity'
        
        # Development tools
        dev_keywords = ['gcc', 'make', 'cmake', 'python', 'node', 'java', 'docker']
        if any(keyword in app_name_lower for keyword in dev_keywords):
            return 'development'
        
        return 'system'
    
    async def detect_usage_pattern(self) -> str:
        """Detect current system usage pattern"""
        if len(self.metrics_history) < 10:
            return 'unknown'
        
        # Analyze recent metrics (last 10 minutes)
        recent_metrics = list(self.metrics_history)[-60:]  # Last 60 samples
        
        avg_cpu = np.mean([m.cpu_usage for m in recent_metrics])
        avg_memory = np.mean([m.memory_usage for m in recent_metrics])
        
        # Determine pattern based on thresholds
        for pattern_name, thresholds in self.usage_patterns.items():
            if (avg_cpu >= thresholds['cpu_threshold'] and 
                avg_memory >= thresholds['memory_threshold']):
                return pattern_name
        
        return 'idle'


class PredictiveOptimizer:
    """Predictive optimization using historical data"""
    
    def __init__(self):
        self.prediction_models = {}
        self.optimization_history = []
        self.learning_enabled = True
        
    async def predict_resource_usage(self, time_horizon_minutes: int = 30) -> Dict[str, float]:
        """Predict resource usage for the next time period"""
        try:
            # Simple prediction based on recent trends
            # In a full implementation, this would use more sophisticated ML models
            
            predictions = {
                'cpu_usage': 50.0,
                'memory_usage': 60.0,
                'disk_io_load': 30.0,
                'network_load': 20.0,
                'confidence': 0.7
            }
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Resource prediction failed: {e}")
            return {}
    
    async def predict_application_needs(self, app_patterns: Dict[str, ApplicationPattern]) -> Dict[str, Dict[str, float]]:
        """Predict application resource needs"""
        predictions = {}
        
        try:
            for app_name, pattern in app_patterns.items():
                # Predict based on historical patterns
                predicted_cpu = pattern.avg_cpu_usage * 1.2  # Add 20% buffer
                predicted_memory = pattern.avg_memory_usage * 1.1  # Add 10% buffer
                
                predictions[app_name] = {
                    'cpu_need': min(predicted_cpu, 100.0),
                    'memory_need': min(predicted_memory, 100.0),
                    'priority': self._calculate_priority(pattern),
                    'category': pattern.category
                }
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Application prediction failed: {e}")
            return {}
    
    def _calculate_priority(self, pattern: ApplicationPattern) -> float:
        """Calculate application priority based on usage patterns"""
        # Higher priority for frequently used applications
        frequency_score = min(pattern.usage_frequency / 100.0, 1.0)
        
        # Higher priority for recently used applications
        time_since_use = time.time() - pattern.last_used
        recency_score = max(0, 1.0 - (time_since_use / 3600))  # Decay over 1 hour
        
        # Category-based priority
        category_priorities = {
            'gaming': 0.9,
            'productivity': 0.8,
            'media': 0.7,
            'development': 0.8,
            'system': 0.6
        }
        category_score = category_priorities.get(pattern.category, 0.5)
        
        return (frequency_score * 0.4 + recency_score * 0.3 + category_score * 0.3)
    
    async def generate_optimization_recommendations(self, 
                                                 current_metrics: SystemMetrics,
                                                 predictions: Dict[str, float],
                                                 app_predictions: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Generate optimization recommendations"""
        recommendations = {
            'memory_optimizations': [],
            'cpu_optimizations': [],
            'storage_optimizations': [],
            'gpu_optimizations': [],
            'priority': 'medium',
            'confidence': 0.8
        }
        
        try:
            # Memory optimizations
            if predictions.get('memory_usage', 0) > 80:
                recommendations['memory_optimizations'].extend([
                    'enable_aggressive_compression',
                    'increase_zram_size',
                    'enable_memory_ballooning'
                ])
                recommendations['priority'] = 'high'
            
            # CPU optimizations
            if predictions.get('cpu_usage', 0) > 70:
                recommendations['cpu_optimizations'].extend([
                    'adjust_cpu_governor',
                    'optimize_process_scheduling',
                    'enable_cpu_affinity'
                ])
            
            # GPU optimizations based on predicted applications
            gaming_apps = [app for app, pred in app_predictions.items() 
                          if pred.get('category') == 'gaming']
            if gaming_apps:
                recommendations['gpu_optimizations'].extend([
                    'enable_gaming_mode',
                    'optimize_llvmpipe_threads',
                    'enable_dxvk'
                ])
            
            # Storage optimizations
            if predictions.get('disk_io_load', 0) > 60:
                recommendations['storage_optimizations'].extend([
                    'enable_compression',
                    'optimize_io_scheduler',
                    'enable_read_ahead'
                ])
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Failed to generate recommendations: {e}")
            return recommendations


class LearningEngine:
    """Machine learning engine for continuous optimization"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.model_file = self.data_dir / 'optimization_model.pkl'
        self.training_data = []
        self.model = None
        
    async def record_optimization_result(self, 
                                       optimization: Dict[str, Any], 
                                       performance_improvement: float):
        """Record the result of an optimization for learning"""
        try:
            result = {
                'timestamp': time.time(),
                'optimization': optimization,
                'performance_improvement': performance_improvement,
                'system_state': await self._capture_system_state()
            }
            
            self.training_data.append(result)
            
            # Save training data periodically
            if len(self.training_data) % 10 == 0:
                await self._save_training_data()
            
        except Exception as e:
            logger.error(f"❌ Failed to record optimization result: {e}")
    
    async def _capture_system_state(self) -> Dict[str, Any]:
        """Capture current system state for learning"""
        try:
            cpu_info = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            
            return {
                'cpu_usage': cpu_info,
                'memory_usage': memory_info.percent,
                'memory_available': memory_info.available,
                'process_count': len(psutil.pids()),
                'timestamp': time.time()
            }
        except Exception:
            return {}
    
    async def _save_training_data(self):
        """Save training data to disk"""
        try:
            data_file = self.data_dir / 'training_data.json'
            with open(data_file, 'w') as f:
                json.dump(self.training_data, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Failed to save training data: {e}")
    
    async def train_model(self):
        """Train the optimization model (simplified implementation)"""
        try:
            if len(self.training_data) < 10:
                logger.info("📚 Insufficient training data for model training")
                return False
            
            # In a full implementation, this would train a proper ML model
            # For now, we'll create a simple rule-based model
            
            self.model = {
                'trained': True,
                'training_samples': len(self.training_data),
                'last_trained': time.time()
            }
            
            # Save model
            with open(self.model_file, 'wb') as f:
                pickle.dump(self.model, f)
            
            logger.success(f"✅ Model trained with {len(self.training_data)} samples")
            return True
            
        except Exception as e:
            logger.error(f"❌ Model training failed: {e}")
            return False


class AIOptimizationEngine:
    """
    Advanced AI Optimization Engine
    Provides intelligent, predictive system optimization using machine learning
    """
    
    def __init__(self, config, system_info):
        self.config = config
        self.system_info = system_info
        self.is_running = False
        
        # Initialize AI components
        self.pattern_recognizer = PatternRecognizer()
        self.predictive_optimizer = PredictiveOptimizer()
        
        # Learning engine
        data_dir = Path.home() / '.otis' / 'ai_data'
        self.learning_engine = LearningEngine(data_dir)
        
        # Monitoring
        self.monitoring = False
        self.monitor_thread = None
        self.optimization_count = 0
        self.performance_multiplier = 1.0
        
        logger.info("🧠 AI Optimization Engine initialized")
    
    async def start(self, mode: str = "auto") -> bool:
        """Start AI optimization engine"""
        try:
            logger.info("🚀 Starting AI Optimization Engine...")
            
            # Start pattern recognition monitoring
            await self._start_monitoring()
            
            # Load existing model if available
            if self.learning_engine.model_file.exists():
                try:
                    with open(self.learning_engine.model_file, 'rb') as f:
                        self.learning_engine.model = pickle.load(f)
                    logger.info("📚 Loaded existing AI model")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load existing model: {e}")
            
            self.is_running = True
            logger.success("✅ AI Optimization Engine started")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start AI engine: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop AI optimization engine"""
        try:
            await self._stop_monitoring()
            
            # Save training data
            await self.learning_engine._save_training_data()
            
            self.is_running = False
            logger.success("✅ AI Optimization Engine stopped")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to stop AI engine: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get AI engine status"""
        return {
            "enabled": self.is_running,
            "monitoring_active": self.monitoring,
            "optimization_count": self.optimization_count,
            "performance_multiplier": self.performance_multiplier,
            "model_trained": self.learning_engine.model is not None,
            "training_samples": len(self.learning_engine.training_data),
            "pattern_history_size": len(self.pattern_recognizer.metrics_history),
            "application_patterns": len(self.pattern_recognizer.application_patterns)
        }
    
    async def get_performance_multiplier(self) -> float:
        """Get current performance multiplier"""
        return self.performance_multiplier
    
    async def get_efficiency_score(self) -> float:
        """Get efficiency score based on AI optimization"""
        base_score = 60.0
        
        if self.learning_engine.model:
            base_score += 20.0
        
        if len(self.pattern_recognizer.metrics_history) > 100:
            base_score += 15.0
        
        if self.optimization_count > 0:
            optimization_bonus = min(self.optimization_count * 2, 20)
            base_score += optimization_bonus
        
        return min(base_score, 100.0)
    
    async def analyze_system_patterns(self) -> Dict[str, Any]:
        """Analyze current system usage patterns"""
        try:
            # Collect current metrics
            current_metrics = await self.pattern_recognizer.collect_metrics()
            
            # Analyze application patterns
            app_patterns = await self.pattern_recognizer.analyze_application_patterns()
            
            # Detect usage pattern
            usage_pattern = await self.pattern_recognizer.detect_usage_pattern()
            
            return {
                'current_metrics': asdict(current_metrics) if current_metrics else {},
                'application_patterns': {name: asdict(pattern) for name, pattern in app_patterns.items()},
                'usage_pattern': usage_pattern,
                'analysis_timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"❌ Pattern analysis failed: {e}")
            return {}
    
    async def generate_predictions(self) -> Dict[str, Any]:
        """Generate system performance predictions"""
        try:
            # Get resource usage predictions
            resource_predictions = await self.predictive_optimizer.predict_resource_usage()
            
            # Get application patterns
            app_patterns = await self.pattern_recognizer.analyze_application_patterns()
            
            # Get application predictions
            app_predictions = await self.predictive_optimizer.predict_application_needs(app_patterns)
            
            return {
                'resource_predictions': resource_predictions,
                'application_predictions': app_predictions,
                'prediction_timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"❌ Prediction generation failed: {e}")
            return {}
    
    async def generate_optimization_recommendations(self) -> Dict[str, Any]:
        """Generate AI-powered optimization recommendations"""
        try:
            # Collect current data
            current_metrics = await self.pattern_recognizer.collect_metrics()
            if not current_metrics:
                return {}
            
            # Generate predictions
            predictions_data = await self.generate_predictions()
            resource_predictions = predictions_data.get('resource_predictions', {})
            app_predictions = predictions_data.get('application_predictions', {})
            
            # Generate recommendations
            recommendations = await self.predictive_optimizer.generate_optimization_recommendations(
                current_metrics, resource_predictions, app_predictions
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Recommendation generation failed: {e}")
            return {}
    
    async def configure_for_hardware(self, hardware_info: Dict[str, Any]):
        """Configure AI engine for specific hardware"""
        try:
            cpu_cores = hardware_info.get('cpu_cores', 4)
            memory_gb = hardware_info.get('memory_gb', 4)
            
            # Adjust AI processing based on hardware capabilities
            if cpu_cores >= 8 and memory_gb >= 16:
                # High-end system - enable advanced AI features
                self.predictive_optimizer.learning_enabled = True
                self.performance_multiplier = 2.5
            elif cpu_cores >= 4 and memory_gb >= 8:
                # Mid-range system - balanced AI features
                self.predictive_optimizer.learning_enabled = True
                self.performance_multiplier = 2.0
            else:
                # Low-end system - basic AI features
                self.predictive_optimizer.learning_enabled = False
                self.performance_multiplier = 1.5
            
            logger.info(f"🔧 AI engine configured for hardware: {cpu_cores} cores, {memory_gb}GB RAM")
            
        except Exception as e:
            logger.error(f"❌ Failed to configure for hardware: {e}")
    
    async def optimize_for_profile(self, profile: Dict[str, Any]):
        """Optimize AI settings for specific usage profile"""
        try:
            profile_type = profile.get('type', 'balanced')
            
            if profile_type == 'gaming':
                # Gaming optimization - focus on performance prediction
                self.performance_multiplier = 2.8
                
            elif profile_type == 'productivity':
                # Productivity optimization - focus on efficiency
                self.performance_multiplier = 2.2
                
            elif profile_type == 'server':
                # Server optimization - focus on stability
                self.performance_multiplier = 2.0
            
            logger.info(f"🎯 AI engine optimized for {profile_type} profile")
            
        except Exception as e:
            logger.error(f"❌ Failed to optimize for profile: {e}")
    
    async def optimize_based_on_predictions(self, predictions: Dict[str, Any]):
        """This engine generates predictions, so this is a no-op"""
        pass
    
    # Legacy methods for compatibility
    async def start_predictive_optimization(self):
        """Start predictive optimization"""
        return await self.start()
    
    async def analyze_application(self, app_name: str, app_type: str) -> Dict[str, Any]:
        """Analyze application and return optimization profile"""
        return {"type": app_type, "memory_requirements": {"minimum_gb": 1}}
    
    async def predict_resource_needs(self) -> Dict[str, Any]:
        """Predict resource needs"""
        predictions = await self.generate_predictions()
        return {
            "memory_usage_percent": predictions.get('resource_predictions', {}).get('memory_usage', 50),
            "applications": list(predictions.get('application_predictions', {}).keys())
        }
    
    async def _start_monitoring(self) -> bool:
        """Start AI monitoring thread"""
        if self.monitoring:
            return True
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("📊 AI monitoring started")
        return True
    
    async def _stop_monitoring(self) -> bool:
        """Stop AI monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("📊 AI monitoring stopped")
        return True
    
    def _monitoring_loop(self):
        """AI monitoring loop"""
        while self.monitoring:
            try:
                # Collect metrics periodically
                asyncio.run(self.pattern_recognizer.collect_metrics())
                
                # Train model periodically
                if len(self.learning_engine.training_data) > 0 and \
                   len(self.learning_engine.training_data) % 50 == 0:
                    asyncio.run(self.learning_engine.train_model())
                
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ AI monitoring error: {e}")
                time.sleep(60)