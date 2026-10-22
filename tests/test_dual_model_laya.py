"""
Unit & Integration Tests for Dual-Model Engine and Laya System-1 Decision Layer
Tests:
1. SmolLM2-135M Triage output format and state mapping
2. Qwen3-0.6B Deep Causal reasoning and thinking extraction
3. Multi-Tier Consensus computation
4. Deterministic Laya NOULs arbitration when models disagree
5. Laya override when SmolLM suggests false continue during critical collapse
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "uno_q_core"))
from laya_safety_engine import LayaSafetyEngine
from dual_model_engine import DualModelEngine

@pytest.fixture
def laya():
    return LayaSafetyEngine()

@pytest.fixture
def dual_engine():
    return DualModelEngine()

def test_laya_dual_model_unanimous_normal(laya):
    telemetry = {
        "rssi": -62.0,
        "snr": 25.0,
        "per": 0.01,
        "retries": 0,
        "jitter": 6.0,
        "tinyml_class": "NORMAL"
    }
    smollm_out = {
        "model": "smollm2:135m",
        "latency_sec": 0.08,
        "proposed_state": "NORMAL",
        "proposed_action": "CONTINUE_NORMAL_OPERATION",
        "raw_text": "Link is completely nominal.",
        "status": "SUCCESS"
    }
    qwen_out = {
        "model": "qwen3:0.6b",
        "latency_sec": 1.75,
        "proposed_state": "NORMAL",
        "proposed_action": "CONTINUE_NORMAL_OPERATION",
        "content": "All RF metrics within optimal NOUL bounds.",
        "thinking": "Signal strength and SNR are optimal.",
        "status": "SUCCESS"
    }
    res = laya.evaluate_dual_model(telemetry, smollm_out, qwen_out)
    assert res["state"] == "NORMAL"
    assert res["action"] == "CONTINUE_NORMAL_OPERATION"
    assert res["consensus_badge"] == "100% UNANIMOUS"
    assert res["smollm_audit"]["validated"] is True
    assert res["qwen_audit"]["validated"] is True

def test_laya_dual_model_degrading_switch_antenna(laya):
    telemetry = {
        "rssi": -82.0,
        "snr": 9.5,
        "per": 0.22,
        "retries": 4,
        "jitter": 38.0,
        "tinyml_class": "DEGRADING"
    }
    smollm_out = {
        "model": "smollm2:135m",
        "latency_sec": 0.12,
        "proposed_state": "DEGRADING",
        "proposed_action": "SWITCH_DIVERSITY_ANTENNA",
        "raw_text": "Diagnosing as DEGRADING, recommend antenna switch.",
        "status": "SUCCESS"
    }
    qwen_out = {
        "model": "qwen3:0.6b",
        "latency_sec": 1.95,
        "proposed_state": "DEGRADING",
        "proposed_action": "SWITCH_DIVERSITY_ANTENNA",
        "content": "Multipath reflections are causing inter-symbol interference.",
        "thinking": "High jitter indicates delay spread.",
        "status": "SUCCESS"
    }
    res = laya.evaluate_dual_model(telemetry, smollm_out, qwen_out)
    assert res["state"] == "DEGRADING"
    assert res["action"] == "SWITCH_DIVERSITY_ANTENNA"
    assert res["consensus_badge"] == "100% UNANIMOUS"

def test_laya_dual_model_critical_override(laya):
    # Physical RF collapse: -95dBm RSSI, 74% packet loss
    telemetry = {
        "rssi": -95.0,
        "snr": 2.0,
        "per": 0.74,
        "retries": 9,
        "jitter": 120.0,
        "tinyml_class": "CRITICAL"
    }
    # Simulate SmolLM hallucinating that everything is normal:
    smollm_hallucinating = {
        "model": "smollm2:135m",
        "latency_sec": 0.10,
        "proposed_state": "NORMAL",
        "proposed_action": "CONTINUE_NORMAL_OPERATION",
        "raw_text": "Link is fine, continue normal operation.",
        "status": "SUCCESS"
    }
    qwen_out = {
        "model": "qwen3:0.6b",
        "latency_sec": 1.82,
        "proposed_state": "CRITICAL",
        "proposed_action": "TRIGGER_CHANNEL_FAILOVER",
        "content": "Severe co-channel RF jamming detected.",
        "thinking": "SNR is 2dB, packet collapse imminent.",
        "status": "SUCCESS"
    }
    res = laya.evaluate_dual_model(telemetry, smollm_hallucinating, qwen_out)
    # Laya MUST enforce FAILOVER regardless of SmolLM's false proposal
    assert res["state"] == "CRITICAL"
    assert res["action"] == "TRIGGER_CHANNEL_FAILOVER"
    assert res["smollm_audit"]["validated"] is False
    assert "SmolLM missed critical collapse" in res["smollm_audit"]["override"]
    assert res["qwen_audit"]["validated"] is True
    assert res["consensus_badge"] == "HYBRID_RESOLVED"

def test_dual_engine_inference_live(dual_engine):
    # Only run if Ollama is accessible
    if not dual_engine.fast_available or not dual_engine.deep_available:
        pytest.skip("Local Ollama models not available")

    test_tel = {"rssi": -80.0, "snr": 11.0, "per": 0.18, "retries": 3, "jitter": 30.0}
    out = dual_engine.run_dual_inference(test_tel)
    assert "smollm" in out
    assert "qwen" in out
    assert out["smollm"]["latency_sec"] > 0
    assert out["qwen"]["latency_sec"] > 0
