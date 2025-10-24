"""
SLA Uptime Monitoring System
============================

Comprehensive uptime and performance monitoring system for Harmonic IoT Protocol
with SLA tracking, alerting, and reporting capabilities.

Copyright (c) 2025 Guilherme Gonçalves Machado
Licensed under CC BY-NC-SA 4.0
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import requests
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class MonitorStatus(Enum):
    """Monitor status enumeration."""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"

@dataclass
class SLAThreshold:
    """SLA threshold configuration."""
    name: str
    target_value: float
    measurement_unit: str
    measurement_period: str  # 'monthly', 'daily', 'hourly'
    violation_threshold: float
    compensation_rate: float  # Percentage of service credits

@dataclass
class MonitorResult:
    """Monitor check result."""
    timestamp: datetime
    status: MonitorStatus
    response_time: Optional[float]
    status_code: Optional[int]
    error_message: Optional[str]
    additional_metrics: Dict[str, float]

class UptimeMonitor:
    """
    Comprehensive uptime and SLA monitoring system.

    Monitors multiple endpoints, tracks SLA compliance, sends alerts,
    and generates compliance reports for enterprise customers.
    """

    def __init__(self, config: Dict):
        """
        Initialize uptime monitor.

        Args:
            config: Monitor configuration including endpoints, thresholds, and alerting
        """
        self.config = config
        self.monitors: Dict[str, Dict] = config.get('monitors', {})
        self.sla_thresholds: Dict[str, SLAThreshold] = self._load_sla_thresholds()
        self.alert_channels: List[Dict] = config.get('alert_channels', [])

        # Monitoring state
        self.monitor_results: Dict[str, List[MonitorResult]] = {}
        self.current_incidents: Dict[str, Dict] = {}
        self.sla_violations: List[Dict] = []

        # Performance tracking
        self.uptime_stats: Dict[str, Dict] = {}
        self.performance_stats: Dict[str, Dict] = {}

        logger.info("Uptime monitor initialized")

    def _load_sla_thresholds(self) -> Dict[str, SLAThreshold]:
        """Load SLA thresholds from configuration."""
        thresholds = {}

        sla_config = self.config.get('sla_thresholds', {})

        # Default SLA thresholds for Harmonic IoT Protocol
        default_thresholds = {
            'uptime': SLAThreshold(
                name='Service Uptime',
                target_value=99.9,  # 99.9% uptime
                measurement_unit='percentage',
                measurement_period='monthly',
                violation_threshold=99.8,
                compensation_rate=10.0  # 10% service credit
            ),
            'api_response_time': SLAThreshold(
                name='API Response Time',
                target_value=200.0,  # 200ms
                measurement_unit='milliseconds',
                measurement_period='daily',
                violation_threshold=500.0,
                compensation_rate=5.0  # 5% service credit
            ),
            'harmonic_processing_time': SLAThreshold(
                name='Harmonic Processing Time',
                target_value=100.0,  # 100ms
                measurement_unit='milliseconds',
                measurement_period='hourly',
                violation_threshold=250.0,
                compensation_rate=2.0  # 2% service credit
            )
        }

        # Merge with custom configuration
        for name, config_data in sla_config.items():
            if name in default_thresholds:
                # Update default with custom values
                threshold = default_thresholds[name]
                for key, value in config_data.items():
                    setattr(threshold, key, value)
                thresholds[name] = threshold
            else:
                # Create new threshold from config
                thresholds[name] = SLAThreshold(**config_data)

        # Add any missing defaults
        for name, threshold in default_thresholds.items():
            if name not in thresholds:
                thresholds[name] = threshold

        return thresholds

    async def start_monitoring(self, check_interval: int = 60) -> None:
        """
        Start continuous monitoring of all configured endpoints.

        Args:
            check_interval: Interval between checks in seconds
        """
        logger.info(f"Starting uptime monitoring with {check_interval}s interval")

        while True:
            try:
                # Run all monitor checks concurrently
                tasks = []
                for monitor_name, monitor_config in self.monitors.items():
                    task = asyncio.create_task(
                        self._check_monitor(monitor_name, monitor_config)
                    )
                    tasks.append(task)

                # Wait for all checks to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results and check for SLA violations
                for i, result in enumerate(results):
                    monitor_name = list(self.monitors.keys())[i]

                    if isinstance(result, Exception):
                        logger.error(f"Monitor {monitor_name} failed: {result}")
                        continue

                    # Store result
                    if monitor_name not in self.monitor_results:
                        self.monitor_results[monitor_name] = []

                    self.monitor_results[monitor_name].append(result)

                    # Check for incidents and SLA violations
                    await self._process_monitor_result(monitor_name, result)

                # Clean up old results (keep last 24 hours)
                self._cleanup_old_results()

                # Wait for next check interval
                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(check_interval)

    async def _check_monitor(self, monitor_name: str, config: Dict) -> MonitorResult:
        """
        Perform a single monitor check.

        Args:
            monitor_name: Name of the monitor
            config: Monitor configuration

        Returns:
            MonitorResult: Result of the monitor check
        """
        start_time = time.time()

        try:
            url = config['url']
            method = config.get('method', 'GET').upper()
            timeout = config.get('timeout', 10)
            expected_status = config.get('expected_status', 200)
            expected_response_time = config.get('expected_response_time', 5000)  # ms

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                if method == 'GET':
                    async with session.get(url) as response:
                        response_time = (time.time() - start_time) * 1000  # Convert to ms

                        # Determine status
                        if response.status == expected_status and response_time <= expected_response_time:
                            status = MonitorStatus.UP
                        elif response.status == expected_status:
                            status = MonitorStatus.DEGRADED
                        else:
                            status = MonitorStatus.DOWN

                        # Additional metrics for harmonic protocol
                        additional_metrics = {}
                        if 'harmonic' in url.lower():
                            additional_metrics = await self._collect_harmonic_metrics(session, config)

                        return MonitorResult(
                            timestamp=datetime.utcnow(),
                            status=status,
                            response_time=response_time,
                            status_code=response.status,
                            error_message=None,
                            additional_metrics=additional_metrics
                        )

                elif method == 'POST':
                    payload = config.get('payload', {})
                    async with session.post(url, json=payload) as response:
                        response_time = (time.time() - start_time) * 1000

                        status = MonitorStatus.UP if response.status == expected_status else MonitorStatus.DOWN

                        return MonitorResult(
                            timestamp=datetime.utcnow(),
                            status=status,
                            response_time=response_time,
                            status_code=response.status,
                            error_message=None,
                            additional_metrics={}
                        )

        except asyncio.TimeoutError:
            return MonitorResult(
                timestamp=datetime.utcnow(),
                status=MonitorStatus.DOWN,
                response_time=None,
                status_code=None,
                error_message="Request timeout",
                additional_metrics={}
            )

        except Exception as e:
            return MonitorResult(
                timestamp=datetime.utcnow(),
                status=MonitorStatus.DOWN,
                response_time=None,
                status_code=None,
                error_message=str(e),
                additional_metrics={}
            )

    async def _collect_harmonic_metrics(self, session: aiohttp.ClientSession, config: Dict) -> Dict[str, float]:
        """Collect harmonic protocol specific metrics."""
        metrics = {}

        try:
            # Check harmonic processing endpoint
            harmonic_url = config.get('harmonic_endpoint', '/api/harmonic/metrics')
            base_url = config['url'].split('/api')[0] if '/api' in config['url'] else config['url']

            async with session.get(f"{base_url}{harmonic_url}") as response:
                if response.status == 200:
                    data = await response.json()

                    metrics['fft_processing_time'] = data.get('fft_processing_time', 0)
                    metrics['active_channels'] = data.get('active_channels', 0)
                    metrics['device_count'] = data.get('device_count', 0)
                    metrics['frequency_accuracy'] = data.get('frequency_accuracy', 0)

        except Exception as e:
            logger.warning(f"Failed to collect harmonic metrics: {e}")

        return metrics

    async def _process_monitor_result(self, monitor_name: str, result: MonitorResult) -> None:
        """Process monitor result and check for incidents/SLA violations."""

        # Check for new incidents
        if result.status in [MonitorStatus.DOWN, MonitorStatus.DEGRADED]:
            await self._handle_incident(monitor_name, result)
        else:
            # Check if incident should be resolved
            if monitor_name in self.current_incidents:
                await self._resolve_incident(monitor_name, result)

        # Check SLA violations
        await self._check_sla_violations(monitor_name, result)

        # Update statistics
        self._update_statistics(monitor_name, result)

    async def _handle_incident(self, monitor_name: str, result: MonitorResult) -> None:
        """Handle new or ongoing incidents."""

        if monitor_name not in self.current_incidents:
            # New incident
            incident = {
                'incident_id': f"INC_{int(time.time())}_{monitor_name}",
                'monitor_name': monitor_name,
                'start_time': result.timestamp,
                'status': result.status.value,
                'error_message': result.error_message,
                'alert_sent': False
            }

            self.current_incidents[monitor_name] = incident

            # Send alert
            await self._send_alert(
                severity=AlertSeverity.CRITICAL if result.status == MonitorStatus.DOWN else AlertSeverity.WARNING,
                title=f"Service {result.status.value.upper()}: {monitor_name}",
                message=f"Monitor {monitor_name} is {result.status.value}. Error: {result.error_message}",
                incident_id=incident['incident_id']
            )

            incident['alert_sent'] = True

            logger.warning(f"New incident: {incident['incident_id']}")

    async def _resolve_incident(self, monitor_name: str, result: MonitorResult) -> None:
        """Resolve existing incident."""

        if monitor_name in self.current_incidents:
            incident = self.current_incidents[monitor_name]

            # Calculate downtime
            downtime = result.timestamp - incident['start_time']

            # Send resolution alert
            await self._send_alert(
                severity=AlertSeverity.INFO,
                title=f"Service RECOVERED: {monitor_name}",
                message=f"Monitor {monitor_name} has recovered. Downtime: {downtime}",
                incident_id=incident['incident_id']
            )

            # Archive incident
            incident['end_time'] = result.timestamp
            incident['downtime'] = downtime.total_seconds()
            incident['resolved'] = True

            # Remove from current incidents
            del self.current_incidents[monitor_name]

            logger.info(f"Incident resolved: {incident['incident_id']}")

    async def _check_sla_violations(self, monitor_name: str, result: MonitorResult) -> None:
        """Check for SLA violations based on current result."""

        # Check uptime SLA
        if result.status == MonitorStatus.DOWN:
            uptime_percentage = self._calculate_uptime_percentage(monitor_name, 'monthly')
            uptime_threshold = self.sla_thresholds['uptime']

            if uptime_percentage < uptime_threshold.violation_threshold:
                violation = {
                    'violation_id': f"SLA_{int(time.time())}_{monitor_name}_uptime",
                    'monitor_name': monitor_name,
                    'sla_type': 'uptime',
                    'threshold': uptime_threshold.target_value,
                    'actual_value': uptime_percentage,
                    'timestamp': result.timestamp,
                    'compensation_rate': uptime_threshold.compensation_rate
                }

                self.sla_violations.append(violation)

                await self._send_alert(
                    severity=AlertSeverity.EMERGENCY,
                    title=f"SLA VIOLATION: Uptime below {uptime_threshold.target_value}%",
                    message=f"Uptime for {monitor_name}: {uptime_percentage:.2f}%",
                    incident_id=violation['violation_id']
                )

        # Check response time SLA
        if result.response_time:
            response_threshold = self.sla_thresholds['api_response_time']

            if result.response_time > response_threshold.violation_threshold:
                violation = {
                    'violation_id': f"SLA_{int(time.time())}_{monitor_name}_response_time",
                    'monitor_name': monitor_name,
                    'sla_type': 'response_time',
                    'threshold': response_threshold.target_value,
                    'actual_value': result.response_time,
                    'timestamp': result.timestamp,
                    'compensation_rate': response_threshold.compensation_rate
                }

                self.sla_violations.append(violation)

                await self._send_alert(
                    severity=AlertSeverity.WARNING,
                    title=f"SLA VIOLATION: Response time above {response_threshold.target_value}ms",
                    message=f"Response time for {monitor_name}: {result.response_time:.2f}ms",
                    incident_id=violation['violation_id']
                )

    async def _send_alert(self, severity: AlertSeverity, title: str, message: str, incident_id: str) -> None:
        """Send alert through configured channels."""

        alert_data = {
            'severity': severity.value,
            'title': title,
            'message': message,
            'incident_id': incident_id,
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'Harmonic IoT Protocol'
        }

        for channel in self.alert_channels:
            try:
                if channel['type'] == 'email':
                    await self._send_email_alert(channel, alert_data)
                elif channel['type'] == 'slack':
                    await self._send_slack_alert(channel, alert_data)
                elif channel['type'] == 'webhook':
                    await self._send_webhook_alert(channel, alert_data)
                elif channel['type'] == 'pagerduty':
                    await self._send_pagerduty_alert(channel, alert_data)

            except Exception as e:
                logger.error(f"Failed to send alert via {channel['type']}: {e}")

    async def _send_slack_alert(self, channel: Dict, alert_data: Dict) -> None:
        """Send alert to Slack."""
        webhook_url = channel['webhook_url']

        color_map = {
            'info': 'good',
            'warning': 'warning',
            'critical': 'danger',
            'emergency': 'danger'
        }

        payload = {
            'attachments': [{
                'color': color_map.get(alert_data['severity'], 'warning'),
                'title': alert_data['title'],
                'text': alert_data['message'],
                'fields': [
                    {'title': 'Incident ID', 'value': alert_data['incident_id'], 'short': True},
                    {'title': 'Severity', 'value': alert_data['severity'].upper(), 'short': True},
                    {'title': 'Service', 'value': alert_data['service'], 'short': True},
                    {'title': 'Timestamp', 'value': alert_data['timestamp'], 'short': True}
                ]
            }]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Slack webhook returned {response.status}")

    def _calculate_uptime_percentage(self, monitor_name: str, period: str) -> float:
        """Calculate uptime percentage for specified period."""
        if monitor_name not in self.monitor_results:
            return 100.0

        now = datetime.utcnow()

        if period == 'hourly':
            start_time = now - timedelta(hours=1)
        elif period == 'daily':
            start_time = now - timedelta(days=1)
        elif period == 'monthly':
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(hours=1)

        results = [
            r for r in self.monitor_results[monitor_name]
            if r.timestamp >= start_time
        ]

        if not results:
            return 100.0

        up_count = sum(1 for r in results if r.status == MonitorStatus.UP)
        total_count = len(results)

        return (up_count / total_count) * 100.0

    def _update_statistics(self, monitor_name: str, result: MonitorResult) -> None:
        """Update monitoring statistics."""

        # Initialize stats if needed
        if monitor_name not in self.uptime_stats:
            self.uptime_stats[monitor_name] = {
                'total_checks': 0,
                'successful_checks': 0,
                'failed_checks': 0,
                'last_check': None
            }

        if monitor_name not in self.performance_stats:
            self.performance_stats[monitor_name] = {
                'response_times': [],
                'avg_response_time': 0,
                'min_response_time': float('inf'),
                'max_response_time': 0
            }

        # Update uptime stats
        uptime_stat = self.uptime_stats[monitor_name]
        uptime_stat['total_checks'] += 1
        uptime_stat['last_check'] = result.timestamp

        if result.status == MonitorStatus.UP:
            uptime_stat['successful_checks'] += 1
        else:
            uptime_stat['failed_checks'] += 1

        # Update performance stats
        if result.response_time:
            perf_stat = self.performance_stats[monitor_name]
            perf_stat['response_times'].append(result.response_time)

            # Keep only last 1000 response times
            if len(perf_stat['response_times']) > 1000:
                perf_stat['response_times'] = perf_stat['response_times'][-1000:]

            perf_stat['avg_response_time'] = sum(perf_stat['response_times']) / len(perf_stat['response_times'])
            perf_stat['min_response_time'] = min(perf_stat['min_response_time'], result.response_time)
            perf_stat['max_response_time'] = max(perf_stat['max_response_time'], result.response_time)

    def _cleanup_old_results(self) -> None:
        """Clean up old monitoring results to prevent memory issues."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        for monitor_name in self.monitor_results:
            self.monitor_results[monitor_name] = [
                r for r in self.monitor_results[monitor_name]
                if r.timestamp >= cutoff_time
            ]

    def generate_sla_report(self, period: str = 'monthly') -> Dict[str, Any]:
        """
        Generate SLA compliance report.

        Args:
            period: Report period ('hourly', 'daily', 'monthly')

        Returns:
            Dict: SLA compliance report
        """
        report = {
            'report_period': period,
            'generated_at': datetime.utcnow().isoformat(),
            'monitors': {},
            'sla_violations': [],
            'overall_compliance': {}
        }

        for monitor_name in self.monitors:
            uptime_percentage = self._calculate_uptime_percentage(monitor_name, period)

            monitor_report = {
                'uptime_percentage': uptime_percentage,
                'sla_target': self.sla_thresholds['uptime'].target_value,
                'sla_compliant': uptime_percentage >= self.sla_thresholds['uptime'].target_value,
                'total_checks': self.uptime_stats.get(monitor_name, {}).get('total_checks', 0),
                'failed_checks': self.uptime_stats.get(monitor_name, {}).get('failed_checks', 0)
            }

            if monitor_name in self.performance_stats:
                perf_stats = self.performance_stats[monitor_name]
                monitor_report['avg_response_time'] = perf_stats['avg_response_time']
                monitor_report['response_time_sla_target'] = self.sla_thresholds['api_response_time'].target_value
                monitor_report['response_time_compliant'] = perf_stats['avg_response_time'] <= self.sla_thresholds['api_response_time'].target_value

            report['monitors'][monitor_name] = monitor_report

        # Add SLA violations for the period
        period_start = datetime.utcnow() - timedelta(days=30 if period == 'monthly' else 1)
        report['sla_violations'] = [
            v for v in self.sla_violations
            if v['timestamp'] >= period_start
        ]

        # Calculate overall compliance
        all_monitors_compliant = all(
            m['sla_compliant'] for m in report['monitors'].values()
        )

        report['overall_compliance'] = {
            'compliant': all_monitors_compliant,
            'violation_count': len(report['sla_violations']),
            'compensation_owed': sum(v['compensation_rate'] for v in report['sla_violations'])
        }

        return report
