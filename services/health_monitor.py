"""
services/health_monitor.py
Automated SRE Daemon for Monitoring Circuit Breakers, Latency, and Quota Exhaustion.
"""

import json
import urllib.request
import logging
from typing import Dict, Any
from services.telemetry_service import telemetry_collector
from services.resilience_service import resilience_engine

logger = logging.getLogger("pocketsmart.sre")

class SystemHealthMonitor:
    def __init__(self, slack_webhook_url: str = None, latency_threshold_ms: float = 3000.0):
        self.slack_webhook_url = slack_webhook_url
        self.latency_threshold_ms = latency_threshold_ms

    def inspect_system_vitals(self) -> Dict[str, Any]:
        """Audits current operational vitals and triggers automated alerts if breached."""
        summary = telemetry_collector.get_summary()
        circuit_open = resilience_engine.circuit_open
        consecutive_failures = resilience_engine.failure_count
        avg_latency = summary["avg_latency_ms"]

        status = "HEALTHY"
        alerts = []

        if circuit_open:
            status = "CRITICAL_CIRCUIT_OPEN"
            alerts.append("Resilience circuit breaker is TRIPPED. Traffic routed to heuristic engine.")
        elif consecutive_failures > 0:
            status = "DEGRADED"
            alerts.append(f"Transient API errors detected: {consecutive_failures} consecutive failures.")

        if avg_latency > self.latency_threshold_ms:
            status = "LATENCY_WARNING"
            alerts.append(f"Average latency ({avg_latency}ms) exceeds SLA of {self.latency_threshold_ms}ms.")

        report = {
            "system_status": status,
            "circuit_breaker_open": circuit_open,
            "consecutive_failures": consecutive_failures,
            "total_calls_tracked": summary["total_calls"],
            "total_cost_usd": summary["total_estimated_cost_usd"],
            "avg_latency_ms": avg_latency,
            "active_alerts": alerts
        }

        if alerts and self.slack_webhook_url:
            self._dispatch_webhook_alert(report)

        return report

    def _dispatch_webhook_alert(self, report: Dict[str, Any]):
        """Dispatches structured notification to on-call Slack/Discord webhooks."""
        payload = {
            "text": f"🚨 *PocketSmart AI SRE Alert*: System status is `{report['system_status']}`",
            "attachments": [
                {
                    "color": "danger" if report["circuit_breaker_open"] else "warning",
                    "fields": [
                        {"title": "Circuit Breaker", "value": str(report["circuit_breaker_open"]), "short": True},
                        {"title": "Avg Latency", "value": f"{report['avg_latency_ms']} ms", "short": True},
                        {"title": "Alerts", "value": "\n".join(report["active_alerts"]), "short": False}
                    ]
                }
            ]
        }
        try:
            req = urllib.request.Request(
                self.slack_webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            logger.error(f"Failed to transmit SRE webhook alert: {e}")

health_monitor = SystemHealthMonitor()
