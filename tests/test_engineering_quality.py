"""
Unit Tests for SlothMesh Engineering Rigor
Covers:
1. Binary IPC Protocol Parser (pack, unpack, checksum validation, corruption detection)
2. Agent Action Executor & Mocked GPIO Actuation
3. Safety Layer Allowlist Validation & Fallback to Rule Baseline
4. Scaler & Normalization Pipeline Verification
"""

import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "models"))

from ipc_protocol import pack_telemetry, unpack_telemetry, calculate_checksum, PACKET_SIZE
from sloth_agent import SlothMeshAgent, GPIOController, ALLOWED_ACTIONS
from baseline_agent import BaselineRuleAgent

# 1. Binary IPC Protocol Tests
def test_ipc_pack_unpack_roundtrip():
    raw_packet = pack_telemetry(
        cmd=0x11,
        rssi_dbm=-82,
        snr_db=9,
        packet_error_rate=0.28,
        retry_count=4,
        channel_busy_ratio=0.62,
        jitter_ms=38,
        predicted_state=1,  # DEGRADING
        sleep_interval_sec=5
    )
    assert len(raw_packet) == PACKET_SIZE

    decoded = unpack_telemetry(raw_packet)
    assert decoded is not None
    assert decoded["rssi"] == -82.0
    assert decoded["snr"] == 9.0
    assert abs(decoded["per"] - 0.28) < 0.005
    assert decoded["retries"] == 4
    assert decoded["busy"] == 0.62
    assert decoded["jitter"] == 38.0
    assert decoded["m33_class"] == "DEGRADING"
    assert decoded["checksum_valid"] is True

def test_ipc_checksum_corruption_detection():
    raw_packet = bytearray(pack_telemetry(
        cmd=0x10,
        rssi_dbm=-60,
        snr_db=25,
        packet_error_rate=0.01,
        retry_count=0,
        channel_busy_ratio=0.20,
        jitter_ms=6,
        predicted_state=0
    ))

    # Corrupt 1 byte in payload (simulating RF or serial bus noise)
    raw_packet[4] ^= 0xFF

    # Must fail checksum validation and return None
    decoded = unpack_telemetry(bytes(raw_packet))
    assert decoded is None

def test_ipc_invalid_magic_byte():
    raw_packet = bytearray(pack_telemetry(0x10, -60, 25, 0.01, 0, 0.2, 5, 0))
    raw_packet[0] = 0x99  # Corrupt magic byte
    assert unpack_telemetry(bytes(raw_packet)) is None

# 2. GPIO Controller & Action Actuation Tests
def test_mock_gpio_controller_state_tracking():
    gpio = GPIOController(simulate=True)
    assert gpio.pins[4] == 0

    gpio.write_pin(4, 1)
    assert gpio.pins[4] == 1

    gpio.write_pin(4, 0)
    assert gpio.pins[4] == 0

# 3. Agent Safety Layer & Fallback Tests
def test_agent_safety_fallback_on_unrecognized_action():
    agent = SlothMeshAgent(simulate=True, timeout_sec=1.0)

    # Force simulated SLM to return an invalid or hallucinated action
    agent._query_slm = lambda tel: ("HALLUCINATED_INVALID_ACTION", "I suggest rebooting everything", 0.01)

    telemetry = {
        "rssi": -94.0,
        "snr": 1.5,
        "per": 0.78,
        "retries": 9,
        "busy": 0.96,
        "jitter": 130.0,
        "m33_class": "CRITICAL"
    }

    record = agent.evaluate_telemetry(telemetry)

    # The safety layer MUST reject the hallucinated action and fallback to the rule baseline
    assert record["decision"] in ALLOWED_ACTIONS
    assert record["decision"] == "TRIGGER_FAILOVER"
    assert record["decision_source"] == "BASELINE_RULE_FALLBACK"
    assert "SAFETY FALLBACK TRIGGERED" in record["reason"]

def test_agent_healthy_paced_sleep_bypass():
    agent = SlothMeshAgent(simulate=True)
    healthy_tel = {
        "rssi": -55.0,
        "snr": 30.0,
        "per": 0.01,
        "retries": 0,
        "busy": 0.15,
        "jitter": 5.0,
        "m33_class": "HEALTHY"
    }
    record = agent.evaluate_telemetry(healthy_tel)
    assert record["decision"] == "CONTINUE_NORMAL_OPERATION"
    assert record["decision_source"] == "M33_TINYML_PACED"

# 4. Scaler Pipeline Tests
def test_scaler_normalization_parameters():
    mean_path = os.path.join(os.path.dirname(__file__), "..", "models", "scaler_mean.npy")
    scale_path = os.path.join(os.path.dirname(__file__), "..", "models", "scaler_scale.npy")

    assert os.path.exists(mean_path)
    assert os.path.exists(scale_path)

    mean = np.load(mean_path)
    scale = np.load(scale_path)

    assert mean.shape == (6,)
    assert scale.shape == (6,)
    assert np.all(scale > 0)  # Standard deviations must be positive

    # Test sample transformation
    raw_sample = np.array([-70.0, 20.0, 0.05, 1.0, 0.30, 10.0])
    normalized = (raw_sample - mean) / scale
    assert normalized.shape == (6,)
    assert not np.isnan(normalized).any()
