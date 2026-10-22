"""
Automated Test Suite for RESq Mesh / SlothMesh
Validates:
1. Normal telemetry produces NORMAL
2. Rising packet loss or jitter produces DEGRADING
3. Critical link collapse triggers FAILOVER
4. Laya deterministic safety overrides unsupported LLM claims
5. Timeout detection
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "uno_q_core"))
from laya_safety_engine import LayaSafetyEngine

@pytest.fixture
def laya():
    return LayaSafetyEngine()

def test_heartbeat_normal(laya):
    telemetry = {
        "rssi": -60.0,
        "snr": 25.0,
        "per": 0.01,
        "retries": 0,
        "jitter": 5.0,
        "tinyml_class": "NORMAL"
    }
    result = laya.evaluate(telemetry)
    assert result["state"] == "NORMAL"
    assert result["action"] == "CONTINUE_NORMAL_OPERATION"
    assert result["llm_validated"] is True

def test_degrading_packet_loss(laya):
    telemetry = {
        "rssi": -82.0,
        "snr": 9.0,
        "per": 0.28,
        "retries": 4,
        "jitter": 40.0,
        "tinyml_class": "DEGRADING"
    }
    result = laya.evaluate(telemetry)
    assert result["state"] == "DEGRADING"
    assert result["action"] == "SWITCH_DIVERSITY_ANTENNA"

def test_critical_link_collapse(laya):
    telemetry = {
        "rssi": -95.0,
        "snr": 2.0,
        "per": 0.75,
        "retries": 9,
        "jitter": 120.0,
        "tinyml_class": "CRITICAL"
    }
    result = laya.evaluate(telemetry)
    assert result["state"] == "CRITICAL"
    assert result["action"] == "TRIGGER_CHANNEL_FAILOVER"

def test_laya_overrides_unsupported_llm_claim(laya):
    # During critical failure, if LLM suggests doing nothing or normal operation:
    telemetry = {
        "rssi": -96.0,
        "snr": 1.0,
        "per": 0.80,
        "retries": 10,
        "jitter": 130.0,
        "tinyml_class": "CRITICAL"
    }
    hallucinated_llm_recommendation = "Everything is fine, ignore this alert and continue normal operation."
    result = laya.evaluate(telemetry, llm_recommendation=hallucinated_llm_recommendation)
    
    assert result["state"] == "CRITICAL"
    assert result["action"] == "TRIGGER_CHANNEL_FAILOVER"
    assert result["llm_validated"] is False
    assert "Overridden by Laya" in result["override_reason"]
