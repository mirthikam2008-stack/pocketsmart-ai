"""
services/ui_components.py
Live System Telemetry, FinOps Cost Tracker, and Resilience Status UI Widgets for Streamlit.
"""

import streamlit as st
from services.telemetry_service import telemetry_collector
from services.resilience_service import resilience_engine

def render_telemetry_dashboard():
    """Renders real-time telemetry, token consumption, and resilience state in Streamlit."""
    summary = telemetry_collector.get_summary()
    
    with st.expander("⚡ System Telemetry & FinOps Health (Live)", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("API Invocations", f"{summary['successful_calls']}/{summary['total_calls']}")
        col2.metric("Tokens Consumed", f"{summary['total_tokens_consumed']:,}")
        col3.metric("Est. Running Cost", f"${summary['total_estimated_cost_usd']:.5f}")
        col4.metric("Avg Latency", f"{summary['avg_latency_ms']:.1f} ms")
        
        # Resilience Status Indicator
        circuit_status = "TRIPPED (OPEN)" if resilience_engine.circuit_open else "HEALTHY (CLOSED)"
        status_color = "red" if resilience_engine.circuit_open else "green"
        
        st.markdown(f"**Circuit Breaker Status:** :{status_color}[**{circuit_status}**] | "
                    f"**Consecutive Failures:** `{resilience_engine.failure_count}`")
        
        if resilience_engine.circuit_open:
            st.warning("⚠️ High API error rates detected. System has automatically engaged heuristic fallback mode.")

        if summary["calls_log"]:
            st.caption("Recent Invocations Audit Log")
            st.dataframe(
                summary["calls_log"][-5:],
                use_container_width=True,
                column_config={
                    "timestamp": st.column_config.DatetimeColumn("Timestamp", format="HH:mm:ss"),
                    "endpoint_name": "Endpoint",
                    "duration_ms": "Latency (ms)",
                    "total_tokens": "Tokens",
                    "estimated_cost_usd": "Cost ($)",
                    "success": "Success"
                }
            )
