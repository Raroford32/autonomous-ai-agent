"""
Advanced Metrics and Monitoring System
Provides comprehensive metrics collection, analysis, and visualization
"""

import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class PerformanceBaseline:
    """Performance baseline for comparison"""
    metric_name: str
    baseline_value: float
    threshold_warning: float
    threshold_critical: float
    sample_size: int = 100


class MetricsMonitor:
    """
    Advanced metrics monitoring system for tracking agent performance
    """
    
    def __init__(self, agent_ref, retention_hours: int = 24):
        self.agent = agent_ref
        self.retention_hours = retention_hours
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.baselines: Dict[str, PerformanceBaseline] = {}
        self.alerts: List[Dict] = []
        
        logger.info("Metrics Monitor initialized")
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None, unit: str = ""):
        """Record a metric value"""
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            unit=unit
        )
        
        self.metrics[name].append(metric)
        
        # Check against baseline if exists
        if name in self.baselines:
            self._check_baseline(name, value)
    
    def _check_baseline(self, metric_name: str, value: float):
        """Check if metric value exceeds baseline thresholds"""
        baseline = self.baselines[metric_name]
        
        if value >= baseline.threshold_critical:
            self.alerts.append({
                'severity': 'critical',
                'metric': metric_name,
                'value': value,
                'threshold': baseline.threshold_critical,
                'timestamp': datetime.utcnow().isoformat()
            })
            logger.critical(f"CRITICAL: {metric_name} = {value} (threshold: {baseline.threshold_critical})")
        
        elif value >= baseline.threshold_warning:
            self.alerts.append({
                'severity': 'warning',
                'metric': metric_name,
                'value': value,
                'threshold': baseline.threshold_warning,
                'timestamp': datetime.utcnow().isoformat()
            })
            logger.warning(f"WARNING: {metric_name} = {value} (threshold: {baseline.threshold_warning})")
    
    def establish_baseline(self, metric_name: str, percentile: float = 0.95):
        """Establish performance baseline from historical data"""
        if metric_name not in self.metrics or len(self.metrics[metric_name]) < 10:
            logger.warning(f"Insufficient data to establish baseline for {metric_name}")
            return
        
        values = [m.value for m in self.metrics[metric_name]]
        values.sort()
        
        # Calculate percentile-based thresholds
        baseline_idx = int(len(values) * 0.5)
        warning_idx = int(len(values) * 0.75)
        critical_idx = int(len(values) * percentile)
        
        baseline = PerformanceBaseline(
            metric_name=metric_name,
            baseline_value=values[baseline_idx],
            threshold_warning=values[warning_idx],
            threshold_critical=values[critical_idx],
            sample_size=len(values)
        )
        
        self.baselines[metric_name] = baseline
        logger.info(f"Baseline established for {metric_name}: {baseline.baseline_value} "
                   f"(warn: {baseline.threshold_warning}, crit: {baseline.threshold_critical})")
    
    def get_metric_stats(self, metric_name: str, window_minutes: int = 60) -> Dict[str, float]:
        """Get statistical summary of a metric over time window"""
        if metric_name not in self.metrics:
            return {}
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_values = [
            m.value for m in self.metrics[metric_name]
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_values:
            return {}
        
        recent_values.sort()
        
        return {
            'count': len(recent_values),
            'min': recent_values[0],
            'max': recent_values[-1],
            'mean': sum(recent_values) / len(recent_values),
            'median': recent_values[len(recent_values) // 2],
            'p95': recent_values[int(len(recent_values) * 0.95)] if len(recent_values) > 20 else recent_values[-1],
            'p99': recent_values[int(len(recent_values) * 0.99)] if len(recent_values) > 100 else recent_values[-1]
        }
    
    def detect_anomalies(self, metric_name: str, sensitivity: float = 2.0) -> List[Metric]:
        """Detect anomalous metric values using statistical methods"""
        if metric_name not in self.metrics or len(self.metrics[metric_name]) < 20:
            return []
        
        values = [m.value for m in self.metrics[metric_name]]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Find values beyond sensitivity * std_dev
        anomalies = []
        for metric in self.metrics[metric_name]:
            if abs(metric.value - mean) > sensitivity * std_dev:
                anomalies.append(metric)
        
        return anomalies
    
    def get_trend(self, metric_name: str, window_minutes: int = 60) -> str:
        """Determine trend direction for a metric"""
        if metric_name not in self.metrics:
            return 'unknown'
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_metrics = [
            m for m in self.metrics[metric_name]
            if m.timestamp >= cutoff_time
        ]
        
        if len(recent_metrics) < 5:
            return 'insufficient_data'
        
        # Simple trend analysis: compare first half vs second half
        mid = len(recent_metrics) // 2
        first_half_avg = sum(m.value for m in recent_metrics[:mid]) / mid
        second_half_avg = sum(m.value for m in recent_metrics[mid:]) / (len(recent_metrics) - mid)
        
        diff_percent = ((second_half_avg - first_half_avg) / first_half_avg) * 100
        
        if diff_percent > 10:
            return 'increasing'
        elif diff_percent < -10:
            return 'decreasing'
        else:
            return 'stable'
    
    def generate_health_score(self) -> float:
        """Generate overall health score (0.0 - 1.0)"""
        if not self.baselines:
            return 0.5  # Unknown health
        
        scores = []
        
        for metric_name, baseline in self.baselines.items():
            if metric_name not in self.metrics or not self.metrics[metric_name]:
                continue
            
            latest_value = self.metrics[metric_name][-1].value
            
            # Score based on how far from critical threshold
            if latest_value <= baseline.baseline_value:
                score = 1.0
            elif latest_value <= baseline.threshold_warning:
                score = 0.7
            elif latest_value <= baseline.threshold_critical:
                score = 0.3
            else:
                score = 0.0
            
            scores.append(score)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive metrics report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'health_score': self.generate_health_score(),
            'total_metrics_tracked': len(self.metrics),
            'total_data_points': sum(len(v) for v in self.metrics.values()),
            'active_alerts': [a for a in self.alerts if 
                            datetime.fromisoformat(a['timestamp']) > 
                            datetime.utcnow() - timedelta(hours=1)],
            'metrics_summary': {}
        }
        
        for metric_name in self.metrics.keys():
            stats = self.get_metric_stats(metric_name, window_minutes=60)
            if stats:
                report['metrics_summary'][metric_name] = {
                    'stats': stats,
                    'trend': self.get_trend(metric_name),
                    'baseline': (
                        {
                            'value': self.baselines[metric_name].baseline_value,
                            'warning': self.baselines[metric_name].threshold_warning,
                            'critical': self.baselines[metric_name].threshold_critical
                        }
                        if metric_name in self.baselines else None
                    )
                }
        
        return report
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        if format == 'json':
            data = {
                metric_name: [
                    {
                        'value': m.value,
                        'timestamp': m.timestamp.isoformat(),
                        'tags': m.tags,
                        'unit': m.unit
                    }
                    for m in metrics
                ]
                for metric_name, metrics in self.metrics.items()
            }
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        
        for metric_name in self.metrics.keys():
            # Filter out old metrics
            self.metrics[metric_name] = deque(
                (m for m in self.metrics[metric_name] if m.timestamp >= cutoff_time),
                maxlen=10000
            )
        
        logger.info(f"Cleaned up metrics older than {self.retention_hours} hours")
