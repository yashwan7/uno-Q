#!/usr/bin/env python3
"""
Dual-Model Edge Cognitive Pipeline & Laya Decision Layer
Target Platform: Arduino UNO Q (Linux Application Processor + STM32U5 Cortex-M33)

Architecture:
  ┌─────────────────────────────────────────────────────────────┐
  │ Physical Telemetry Stream (UNO Q MCU Frame/Real RF Metrics) │
  │ RSSI, SNR, PER, Retries, Jitter, TinyML hardware class       │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
  ┌─────────────────────────────┐ ┌─────────────────────────────┐
  │ Tier 1: SmolLM2 135M        │ │ Tier 2: Qwen 3 0.6B         │
  │ Fast Triage Agent           │ │ Deep Causal Reasoner        │
  │ Latency: < 0.8s             │ │ Latency: ~ 1.8s             │
  │ Rapid link classification   │ │ Chain-of-Thought attribution│
  └──────────────┬──────────────┘ └──────────────┬──────────────┘
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ Tier 3: Laya System-1 NOULs Deterministic Decision Layer    │
  │ • Validates models against hard physical laws               │
  │ • Calculates Model Consensus (Agreement vs Divergence)      │
  │ • Overrides model hallucinations / false alarms             │
  │ • Enforces final binding hardware actuation                 │
  └─────────────────────────────────────────────────────────────┘
"""

import os
import time
import json
import requests
from typing import Dict, Any, Optional, Tuple

class DualModelEngine:
    def __init__(self, ollama_url: str = "http://localhost:11434/api/chat"):
        self.ollama_url = os.getenv("OLLAMA_URL", ollama_url)
        self.fast_model = os.getenv("FAST_SLM_MODEL", "smollm2:135m")
        self.deep_model = os.getenv("DEEP_SLM_MODEL", "qwen3:0.6b")
        
        # Test availability
        self.fast_available = self._check_model(self.fast_model)
        self.deep_available = self._check_model(self.deep_model)

    def _check_model(self, model_name: str) -> bool:
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                return any(model_name in m for m in models)
        except Exception:
            return False
        return False

    def query_smollm_triage(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tier 1: Fast triage with SmolLM2-135M.
        Directly classifies link state and suggests immediate edge action.
        """
        t0 = time.time()
        rssi = telemetry.get("rssi", -65.0)
        snr = telemetry.get("snr", 20.0)
        per = telemetry.get("per", 0.02) * 100.0
        retries = telemetry.get("retries", 0)

        prompt = (
            f"You are a wireless link triage monitor. Telemetry: RSSI={rssi:.1f}dBm, "
            f"SNR={snr:.1f}dB, PacketError={per:.1f}%, Retries={retries}. "
            f"Diagnose state (NORMAL, DEGRADING, or CRITICAL) and recommend action in 1 brief sentence."
        )

        try:
            resp = requests.post(
                self.ollama_url,
                json={
                    "model": self.fast_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 60}
                },
                timeout=5
            )
            dur = time.time() - t0
            raw_text = resp.json().get("message", {}).get("content", "").strip()

            # Parse proposed state from SmolLM response
            clean = raw_text.upper()
            if "CRITICAL" in clean or "COLLAPSE" in clean or "FAILOVER" in clean:
                proposed_state = "CRITICAL"
                proposed_action = "TRIGGER_CHANNEL_FAILOVER"
            elif "DEGRAD" in clean or "WEAK" in clean or "ANTENNA" in clean or "HIGH RETRIES" in clean:
                proposed_state = "DEGRADING"
                proposed_action = "SWITCH_DIVERSITY_ANTENNA"
            else:
                proposed_state = "NORMAL"
                proposed_action = "CONTINUE_NORMAL_OPERATION"

            return {
                "model": self.fast_model,
                "latency_sec": round(dur, 3),
                "proposed_state": proposed_state,
                "proposed_action": proposed_action,
                "raw_text": raw_text,
                "status": "SUCCESS"
            }
        except Exception as e:
            return {
                "model": self.fast_model,
                "latency_sec": round(time.time() - t0, 3),
                "proposed_state": "UNKNOWN",
                "proposed_action": "CONTINUE_NORMAL_OPERATION",
                "raw_text": f"SmolLM offline: {e}",
                "status": "FALLBACK"
            }

    def query_qwen_deep(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tier 2: Deep Causal Attribution with Qwen 3 (0.6B).
        Produces Chain-of-Thought reasoning regarding multipath, RF attenuation, and interference.
        """
        t0 = time.time()
        rssi = telemetry.get("rssi", -65.0)
        snr = telemetry.get("snr", 20.0)
        per = telemetry.get("per", 0.02) * 100.0
        retries = telemetry.get("retries", 0)
        jitter = telemetry.get("jitter", 8.0)

        prompt = (
            f"Telemetry: RSSI={rssi:.1f}dBm, SNR={snr:.1f}dB, PacketError={per:.1f}%, Retries={retries}, Jitter={jitter:.1f}ms. "
            f"Explain the physical RF cause (e.g. multipath fading, rain attenuation, co-channel interference, or nominal signal) "
            f"and propose tactical remediation in 1 concise sentence."
        )

        try:
            resp = requests.post(
                self.ollama_url,
                json={
                    "model": self.deep_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0.2}
                },
                timeout=8
            )
            dur = time.time() - t0
            msg = resp.json().get("message", {})
            raw_text = msg.get("content", "").strip()
            thinking = msg.get("thinking", "").strip()

            clean = raw_text.upper()
            if "CRITICAL" in clean or "COLLAPSE" in clean or "FAILOVER" in clean or "HOP" in clean:
                proposed_state = "CRITICAL"
                proposed_action = "TRIGGER_CHANNEL_FAILOVER"
            elif "DEGRAD" in clean or "ANTENNA" in clean or "DIVERSITY" in clean or "ATTENUATION" in clean:
                proposed_state = "DEGRADING"
                proposed_action = "SWITCH_DIVERSITY_ANTENNA"
            else:
                proposed_state = "NORMAL"
                proposed_action = "CONTINUE_NORMAL_OPERATION"

            return {
                "model": self.deep_model,
                "latency_sec": round(dur, 3),
                "proposed_state": proposed_state,
                "proposed_action": proposed_action,
                "content": raw_text,
                "thinking": thinking,
                "status": "SUCCESS"
            }
        except Exception as e:
            return {
                "model": self.deep_model,
                "latency_sec": round(time.time() - t0, 3),
                "proposed_state": "UNKNOWN",
                "proposed_action": "CONTINUE_NORMAL_OPERATION",
                "content": f"Qwen3 offline: {e}",
                "thinking": "",
                "status": "FALLBACK"
            }

    def run_dual_inference(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs both models sequentially/synchronously for edge clarity,
        returning a combined structured cognitive package.
        """
        smollm_out = self.query_smollm_triage(telemetry)
        qwen_out = self.query_qwen_deep(telemetry)

        # Compute consensus between the two models
        models_agree = (smollm_out.get("proposed_state") == qwen_out.get("proposed_state"))
        
        return {
            "smollm": smollm_out,
            "qwen": qwen_out,
            "models_agree": models_agree,
            "combined_latency_sec": round(smollm_out["latency_sec"] + qwen_out["latency_sec"], 3)
        }

if __name__ == "__main__":
    print("Testing Dual-Model Engine on local Ollama...")
    engine = DualModelEngine()
    test_tel = {"rssi": -83.5, "snr": 9.2, "per": 0.25, "retries": 4, "jitter": 38.0}
    res = engine.run_dual_inference(test_tel)
    print(json.dumps(res, indent=2))
