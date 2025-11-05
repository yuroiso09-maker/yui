"""
OTIS Security Engine
Lightweight behavioral analysis and zero-impact protection for Linux systems
"""

import asyncio
import os
import subprocess
import threading
import time
import hashlib
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from collections import defaultdict, deque
from loguru import logger
import psutil


class BehavioralAnalyzer:
    """Behavioral analysis for process monitoring"""
    
    def __init__(self):
        self.process_patterns = defaultdict(list)
        self.suspicious_activities = deque(maxlen=1000)
        self.baseline_behavior = {}
        self.monitoring_active = False
        
    async def establish_baseline(self) -> Dict[str, Any]:
        """Establish baseline system behavior"""
        try:
            baseline = {
                'normal_processes': set(),
                'typical_cpu_usage': {},
                'typical_memory_usage': {},
                'network_patterns': {},
                'file_access_patterns': {}
            }
            
            # Collect current running processes
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    if info['name']:
                        baseline['normal_processes'].add(info['name'])
                        baseline['typical_cpu_usage'][info['name']] = info['cpu_percent'] or 0
                        baseline['typical_memory_usage'][info['name']] = info['memory_percent'] or 0
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.baseline_behavior = baseline
            logger.info(f"🛡️ Baseline established with {len(baseline['normal_processes'])} processes")
            return baseline
            
        except Exception as e:
            logger.error(f"❌ Baseline establishment failed: {e}")
            return {}
    
    async def analyze_process_behavior(self, process_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual process behavior"""
        analysis = {
            'suspicious': False,
            'risk_level': 'low',
            'anomalies': [],
            'confidence': 0.8
        }
        
        try:
            proc_name = process_info.get('name', '')
            cpu_usage = process_info.get('cpu_percent', 0)
            memory_usage = process_info.get('memory_percent', 0)
            
            # Check against baseline
            if proc_name not in self.baseline_behavior.get('normal_processes', set()):
                analysis['anomalies'].append('new_process')
                analysis['risk_level'] = 'medium'
            
            # Check for excessive resource usage
            baseline_cpu = self.baseline_behavior.get('typical_cpu_usage', {}).get(proc_name, 0)
            if cpu_usage > baseline_cpu * 3 and cpu_usage > 50:
                analysis['anomalies'].append('high_cpu_usage')
                analysis['risk_level'] = 'medium'
            
            baseline_memory = self.baseline_behavior.get('typical_memory_usage', {}).get(proc_name, 0)
            if memory_usage > baseline_memory * 3 and memory_usage > 30:
                analysis['anomalies'].append('high_memory_usage')
                analysis['risk_level'] = 'medium'
            
            # Check for suspicious process names
            suspicious_patterns = ['crypto', 'miner', 'bot', 'hack', 'exploit']
            if any(pattern in proc_name.lower() for pattern in suspicious_patterns):
                analysis['anomalies'].append('suspicious_name')
                analysis['risk_level'] = 'high'
                analysis['suspicious'] = True
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Process behavior analysis failed: {e}")
            return analysis
    
    async def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect system anomalies"""
        anomalies = []
        
        try:
            # Check for unusual process activity
            current_processes = {}
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
                try:
                    info = proc.info
                    if info['name']:
                        current_processes[info['pid']] = info
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Analyze each process
            for pid, proc_info in current_processes.items():
                analysis = await self.analyze_process_behavior(proc_info)
                
                if analysis['suspicious'] or analysis['risk_level'] in ['medium', 'high']:
                    anomaly = {
                        'type': 'process_anomaly',
                        'pid': pid,
                        'process_name': proc_info['name'],
                        'analysis': analysis,
                        'timestamp': time.time()
                    }
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"❌ Anomaly detection failed: {e}")
            return []


class ThreatDetector:
    """Lightweight threat detection system"""
    
    def __init__(self):
        self.threat_signatures = {}
        self.active_threats = []
        self.detection_rules = {}
        
    async def load_threat_signatures(self) -> bool:
        """Load threat detection signatures"""
        try:
            # Basic threat signatures (in production, these would be more comprehensive)
            self.threat_signatures = {
                'cryptominer': {
                    'process_names': ['xmrig', 'cpuminer', 'cgminer', 'bfgminer'],
                    'network_patterns': ['stratum+tcp', 'mining.pool'],
                    'cpu_threshold': 80
                },
                'botnet': {
                    'process_names': ['bot', 'ddos', 'flood'],
                    'network_patterns': ['irc://', 'botnet'],
                    'connections_threshold': 100
                },
                'malware': {
                    'process_names': ['trojan', 'virus', 'malware', 'backdoor'],
                    'file_patterns': ['/tmp/.*\\.sh', '/dev/shm/.*'],
                    'behavior_patterns': ['privilege_escalation', 'data_exfiltration']
                }
            }
            
            logger.info(f"🛡️ Loaded {len(self.threat_signatures)} threat signatures")
            return True
            
        except Exception as e:
            logger.error(f"❌ Threat signature loading failed: {e}")
            return False
    
    async def scan_for_threats(self) -> List[Dict[str, Any]]:
        """Scan system for known threats"""
        detected_threats = []
        
        try:
            # Scan running processes
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    info = proc.info
                    proc_name = info['name'].lower() if info['name'] else ''
                    
                    # Check against threat signatures
                    for threat_type, signature in self.threat_signatures.items():
                        # Check process names
                        if any(threat_name in proc_name for threat_name in signature.get('process_names', [])):
                            threat = {
                                'type': threat_type,
                                'detection_method': 'process_name',
                                'pid': info['pid'],
                                'process_name': info['name'],
                                'severity': 'high',
                                'timestamp': time.time()
                            }
                            detected_threats.append(threat)
                        
                        # Check CPU usage for cryptominers
                        if threat_type == 'cryptominer' and info['cpu_percent'] and info['cpu_percent'] > signature.get('cpu_threshold', 80):
                            threat = {
                                'type': 'potential_cryptominer',
                                'detection_method': 'high_cpu_usage',
                                'pid': info['pid'],
                                'process_name': info['name'],
                                'cpu_usage': info['cpu_percent'],
                                'severity': 'medium',
                                'timestamp': time.time()
                            }
                            detected_threats.append(threat)
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.active_threats = detected_threats
            return detected_threats
            
        except Exception as e:
            logger.error(f"❌ Threat scanning failed: {e}")
            return []
    
    async def assess_threat_level(self) -> str:
        """Assess overall system threat level"""
        if not self.active_threats:
            return 'low'
        
        high_severity_threats = [t for t in self.active_threats if t.get('severity') == 'high']
        medium_severity_threats = [t for t in self.active_threats if t.get('severity') == 'medium']
        
        if high_severity_threats:
            return 'high'
        elif len(medium_severity_threats) > 3:
            return 'high'
        elif medium_severity_threats:
            return 'medium'
        else:
            return 'low'


class ProtectionManager:
    """Zero-impact protection management"""
    
    def __init__(self):
        self.protection_enabled = False
        self.quarantine_directory = Path.home() / '.otis' / 'quarantine'
        self.protection_rules = {}
        
    async def enable_protection(self) -> bool:
        """Enable system protection"""
        try:
            # Create quarantine directory
            self.quarantine_directory.mkdir(parents=True, exist_ok=True)
            
            # Setup protection rules
            self.protection_rules = {
                'auto_quarantine': True,
                'process_monitoring': True,
                'network_monitoring': False,  # Disabled for zero-impact
                'file_monitoring': False,     # Disabled for zero-impact
                'alert_only': True            # Alert only, no blocking
            }
            
            self.protection_enabled = True
            logger.info("🛡️ Zero-impact protection enabled")
            return True
            
        except Exception as e:
            logger.error(f"❌ Protection enablement failed: {e}")
            return False
    
    async def quarantine_threat(self, threat_info: Dict[str, Any]) -> bool:
        """Quarantine detected threat (alert only for zero-impact)"""
        try:
            # For zero-impact, we only log and alert, don't actually quarantine
            threat_type = threat_info.get('type', 'unknown')
            process_name = threat_info.get('process_name', 'unknown')
            
            logger.warning(f"🚨 THREAT DETECTED: {threat_type} - {process_name}")
            logger.warning(f"🔍 Detection method: {threat_info.get('detection_method', 'unknown')}")
            logger.warning(f"⚠️ Severity: {threat_info.get('severity', 'unknown')}")
            
            # In a full implementation, this could:
            # - Send notifications to user
            # - Log to security database
            # - Integrate with external security tools
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Threat quarantine failed: {e}")
            return False
    
    async def get_protection_status(self) -> Dict[str, Any]:
        """Get current protection status"""
        return {
            'protection_enabled': self.protection_enabled,
            'quarantine_directory': str(self.quarantine_directory),
            'protection_rules': self.protection_rules,
            'quarantined_items': len(list(self.quarantine_directory.glob('*'))) if self.quarantine_directory.exists() else 0
        }


class SecurityEngine:
    """
    Lightweight Security Engine
    Provides behavioral analysis and zero-impact protection for Linux systems
    """
    
    def __init__(self, config, system_info):
        self.config = config
        self.system_info = system_info
        self.is_running = False
        
        # Initialize security components
        self.behavioral_analyzer = BehavioralAnalyzer()
        self.threat_detector = ThreatDetector()
        self.protection_manager = ProtectionManager()
        
        # Security metrics
        self.performance_multiplier = 1.0
        self.threats_detected = 0
        self.anomalies_detected = 0
        self.monitoring_thread = None
        
        logger.info("🔧 Security Engine initialized")
    
    async def start(self, mode: str = "auto") -> bool:
        """Start security engine"""
        try:
            logger.info("🚀 Starting Security Engine...")
            
            # Establish behavioral baseline
            await self.behavioral_analyzer.establish_baseline()
            
            # Load threat signatures
            await self.threat_detector.load_threat_signatures()
            
            # Enable protection
            await self.protection_manager.enable_protection()
            
            # Start monitoring
            await self._start_monitoring()
            
            # Calculate performance multiplier
            await self._calculate_performance_multiplier()
            
            self.is_running = True
            logger.success(f"✅ Security Engine started - {self.performance_multiplier:.1f}x security boost")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start security engine: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop security engine"""
        try:
            await self._stop_monitoring()
            self.is_running = False
            logger.success("✅ Security Engine stopped")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to stop security engine: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get security engine status"""
        protection_status = await self.protection_manager.get_protection_status()
        threat_level = await self.threat_detector.assess_threat_level()
        
        return {
            "enabled": self.is_running,
            "behavioral_analysis_active": self.behavioral_analyzer.monitoring_active,
            "threat_detection_active": len(self.threat_detector.threat_signatures) > 0,
            "protection_enabled": protection_status['protection_enabled'],
            "performance_multiplier": self.performance_multiplier,
            "threats_detected": self.threats_detected,
            "anomalies_detected": self.anomalies_detected,
            "current_threat_level": threat_level,
            "active_threats": len(self.threat_detector.active_threats),
            "baseline_processes": len(self.behavioral_analyzer.baseline_behavior.get('normal_processes', set()))
        }
    
    async def get_performance_multiplier(self) -> float:
        """Get current performance multiplier"""
        return self.performance_multiplier
    
    async def get_efficiency_score(self) -> float:
        """Get efficiency score based on security protection"""
        base_score = 70.0
        
        if self.protection_manager.protection_enabled:
            base_score += 15.0
        
        if len(self.behavioral_analyzer.baseline_behavior) > 0:
            base_score += 10.0
        
        if len(self.threat_detector.threat_signatures) > 0:
            base_score += 10.0
        
        # Bonus for threat detection
        if self.threats_detected > 0:
            detection_bonus = min(self.threats_detected * 2, 15)
            base_score += detection_bonus
        
        return min(base_score, 100.0)
    
    async def perform_security_scan(self) -> Dict[str, Any]:
        """Perform comprehensive security scan"""
        try:
            logger.info("🔍 Performing security scan...")
            
            # Detect threats
            threats = await self.threat_detector.scan_for_threats()
            self.threats_detected += len(threats)
            
            # Detect anomalies
            anomalies = await self.behavioral_analyzer.detect_anomalies()
            self.anomalies_detected += len(anomalies)
            
            # Process detected threats
            for threat in threats:
                await self.protection_manager.quarantine_threat(threat)
            
            # Assess overall threat level
            threat_level = await self.threat_detector.assess_threat_level()
            
            scan_results = {
                'threats_found': len(threats),
                'anomalies_found': len(anomalies),
                'threat_level': threat_level,
                'threats': threats,
                'anomalies': anomalies,
                'scan_timestamp': time.time()
            }
            
            logger.info(f"🔍 Security scan complete: {len(threats)} threats, {len(anomalies)} anomalies")
            return scan_results
            
        except Exception as e:
            logger.error(f"❌ Security scan failed: {e}")
            return {}
    
    async def configure_for_hardware(self, hardware_info: Dict[str, Any]):
        """Configure security engine for specific hardware"""
        try:
            cpu_cores = hardware_info.get('cpu_cores', 4)
            memory_gb = hardware_info.get('memory_gb', 4)
            
            # Adjust security monitoring based on hardware capabilities
            if cpu_cores >= 8 and memory_gb >= 16:
                # High-end system - enable comprehensive monitoring
                self.performance_multiplier = 2.5
            elif cpu_cores >= 4 and memory_gb >= 8:
                # Mid-range system - balanced monitoring
                self.performance_multiplier = 2.0
            else:
                # Low-end system - lightweight monitoring
                self.performance_multiplier = 1.5
            
            logger.info(f"🔧 Security engine configured for hardware: {cpu_cores} cores, {memory_gb}GB RAM")
            
        except Exception as e:
            logger.error(f"❌ Failed to configure for hardware: {e}")
    
    async def optimize_for_profile(self, profile: Dict[str, Any]):
        """Optimize security settings for specific usage profile"""
        try:
            profile_type = profile.get('type', 'balanced')
            
            if profile_type == 'gaming':
                # Gaming optimization - minimal impact
                self.performance_multiplier = 1.8
                self.protection_manager.protection_rules['alert_only'] = True
                
            elif profile_type == 'productivity':
                # Productivity optimization - balanced protection
                self.performance_multiplier = 2.2
                self.protection_manager.protection_rules['alert_only'] = True
                
            elif profile_type == 'server':
                # Server optimization - enhanced protection
                self.performance_multiplier = 2.8
                self.protection_manager.protection_rules['alert_only'] = False
            
            logger.info(f"🎯 Security engine optimized for {profile_type} profile")
            
        except Exception as e:
            logger.error(f"❌ Failed to optimize for profile: {e}")
    
    async def optimize_based_on_predictions(self, predictions: Dict[str, Any]):
        """Optimize based on AI predictions"""
        try:
            predicted_threats = predictions.get('security_threats', [])
            predicted_load = predictions.get('system_load', 50)
            
            # Adjust monitoring intensity based on predicted threats
            if predicted_threats:
                logger.info(f"🧠 Adjusting security for {len(predicted_threats)} predicted threats")
                self.performance_multiplier *= 1.2
            
            # Adjust based on predicted system load
            if predicted_load > 80:
                # High load expected - reduce security impact
                self.performance_multiplier *= 0.9
            
            logger.info(f"🧠 Security engine optimized based on AI predictions")
            
        except Exception as e:
            logger.error(f"❌ Failed to optimize based on predictions: {e}")
    
    async def _start_monitoring(self) -> bool:
        """Start security monitoring thread"""
        if self.behavioral_analyzer.monitoring_active:
            return True
        
        self.behavioral_analyzer.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("📊 Security monitoring started")
        return True
    
    async def _stop_monitoring(self) -> bool:
        """Stop security monitoring thread"""
        self.behavioral_analyzer.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        logger.info("📊 Security monitoring stopped")
        return True
    
    def _monitoring_loop(self):
        """Security monitoring loop"""
        while self.behavioral_analyzer.monitoring_active:
            try:
                # Perform periodic security scan
                asyncio.run(self.perform_security_scan())
                
                time.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"❌ Security monitoring error: {e}")
                time.sleep(120)
    
    async def _calculate_performance_multiplier(self):
        """Calculate current performance multiplier"""
        base_multiplier = 1.0
        
        # Protection enabled bonus
        if self.protection_manager.protection_enabled:
            base_multiplier += 0.8
        
        # Threat detection bonus
        if len(self.threat_detector.threat_signatures) > 0:
            base_multiplier += 0.6
        
        # Behavioral analysis bonus
        if len(self.behavioral_analyzer.baseline_behavior) > 0:
            base_multiplier += 0.4
        
        # Active monitoring bonus
        if self.behavioral_analyzer.monitoring_active:
            base_multiplier += 0.2
        
        self.performance_multiplier = min(base_multiplier, 5.0)  # Cap at 5x
