"""
services/resilience_service.py
Exponential Backoff, Circuit Breaker, and Offline Fallback Engine.
"""

import time
import random
import logging
from typing import Callable, Any, TypeVar

T = TypeVar("T")
logger = logging.getLogger("pocketsmart.resilience")

class CircuitBreakerOpenException(Exception):
    """Raised when consecutive errors exceed threshold."""
    pass

class ResilienceEngine:
    def __init__(self, failure_threshold: int = 3, recovery_timeout_sec: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.circuit_open = False

    def execute_with_retry(
        self, 
        operation_name: str, 
        func: Callable[[], T], 
        max_retries: int = 3, 
        initial_delay: float = 1.0
    ) -> T:
        now = time.time()
        if self.circuit_open:
            if now - self.last_failure_time > self.recovery_timeout_sec:
                logger.warning(f"Circuit Breaker half-open: probing {operation_name}...")
                self.circuit_open = False
                self.failure_count = 0
            else:
                raise CircuitBreakerOpenException(
                    f"Circuit breaker is active for {operation_name}. Cooling down. Try again shortly."
                )

        delay = initial_delay
        for attempt in range(1, max_retries + 1):
            try:
                result = func()
                self.failure_count = 0
                return result
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str
                is_transient = "503" in err_str or "timeout" in err_str or is_rate_limit

                if attempt < max_retries and is_transient:
                    jitter = random.uniform(0.1, 0.5)
                    sleep_time = delay + jitter
                    logger.warning(f"Transient failure in {operation_name} (Attempt {attempt}/{max_retries}): {e}. Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    delay *= 2
                else:
                    self.failure_count += 1
                    self.last_failure_time = time.time()
                    if self.failure_count >= self.failure_threshold:
                        self.circuit_open = True
                        logger.error(f"Circuit breaker tripped open after {self.failure_count} consecutive failures.")
                    raise e
        raise RuntimeError(f"Unexpected termination in retry loop for {operation_name}")

resilience_engine = ResilienceEngine()
