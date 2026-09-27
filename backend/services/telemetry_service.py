"""
services/telemetry_service.py
Enterprise Telemetry, Latency, and Token Cost Monitoring for PocketSmart AI.
"""

import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field

# Pricing standard for gemini-3.7-pro (USD per 1M tokens)
COST_PER_MILLION_INPUT = 1.25
COST_PER_MILLION_OUTPUT = 5.00

@dataclass
class APICallMetric:
    timestamp: float
    endpoint_name: str
    model: str
    duration_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class SessionTelemetry:
    session_id: str
    start_time: float = field(default_factory=time.time)
    calls: List[APICallMetric] = field(default_factory=list)

    def record_call(self, endpoint_name: str, model: str, duration_ms: float, 
                    prompt_tokens: int, completion_tokens: int, 
                    success: bool = True, error_message: Optional[str] = None) -> APICallMetric:
        total = prompt_tokens + completion_tokens
        cost = (
            (prompt_tokens / 1_000_000 * COST_PER_MILLION_INPUT) +
            (completion_tokens / 1_000_000 * COST_PER_MILLION_OUTPUT)
        )
        metric = APICallMetric(
            timestamp=time.time(),
            endpoint_name=endpoint_name,
            model=model,
            duration_ms=round(duration_ms, 2),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            estimated_cost_usd=round(cost, 6),
            success=success,
            error_message=error_message
        )
        self.calls.append(metric)
        return metric

    def get_summary(self) -> Dict[str, Any]:
        total_calls = len(self.calls)
        successful_calls = sum(1 for c in self.calls if c.success)
        total_tokens = sum(c.total_tokens for c in self.calls)
        total_cost = sum(c.estimated_cost_usd for c in self.calls)
        avg_latency = (sum(c.duration_ms for c in self.calls) / total_calls) if total_calls > 0 else 0.0

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": total_calls - successful_calls,
            "total_tokens_consumed": total_tokens,
            "total_estimated_cost_usd": round(total_cost, 6),
            "avg_latency_ms": round(avg_latency, 2),
            "calls_log": [asdict(c) for c in self.calls]
        }

    def export_json(self) -> str:
        return json.dumps(self.get_summary(), indent=2)

# Global in-memory telemetry instance
telemetry_collector = SessionTelemetry(session_id="pocketsmart_runtime")
