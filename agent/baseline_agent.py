#!/usr/bin/env python3
"""
Rule-Based Remediation Baseline for SlothMesh
Runs on: Arduino UNO Q (Linux Host) / Edge Embedded Controllers

Role:
Deterministic baseline for evaluating open-weight Small Language Models (Qwen 0.6B, Qwen 4B).
Uses an explicit decision table and threshold logic over 6 RF telemetry features:
  - rssi (dBm)
  - snr (dB)
  - per (Packet Error Rate, 0.0 - 1.0)
  - retries (count)
  - busy (Channel Busy Ratio, 0.0 - 1.0)
  - jitter (ms)

Remediation Actions:
  - CONTINUE_NORMAL_OPERATION
  - MONITOR_AND_EVALUATE_FAILOVER (Antenna switch / paced re-check)
  - TRIGGER_FAILOVER (Emergency channel hop)
"""

import time
from typing import Dict, Any, Tuple

# Strict Threshold Rules (Aligned with IEEE 802.11 / 802.15.4 link tolerances)
RSSI_CRITICAL = -88.0    # dBm: Imminent link disconnect
RSSI_DEGRADING = -78.0   # dBm: Perimeter / multipath attenuation
SNR_CRITICAL = 6.0       # dB: Low signal-to-noise ratio
SNR_DEGRADING = 12.0     # dB: Borderline SNR floor
PER_CRITICAL = 0.40      # 40% packet error rate
PER_DEGRADING = 0.15     # 15% packet error rate
RETRIES_CRITICAL = 7     # Excessive frame retries
RETRIES_DEGRADING = 3    # Elevated retries
BUSY_CRITICAL = 0.88     # 88% CCA channel occupancy
BUSY_DEGRADING = 0.55    # 55% channel congestion
JITTER_CRITICAL = 90.0   # ms: Extreme packet latency variance
JITTER_DEGRADING = 35.0  # ms: Noticeable packet delay jitter

class BaselineRuleAgent:
    def __init__(self):
        self.channel = 6
        self.antenna = 0

    def evaluate(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes deterministic decision table logic over the 6 RF features.
        Returns: {
            'decision': action string,
            'root_cause': diagnostic text,
            'rules_triggered': list of strings,
            'latency_sec': float,
            'memory_bytes': int (fixed constant ~1KB)
        }
        """
        t0 = time.perf_counter()

        rssi = float(telemetry.get("rssi", -60.0))
        snr = float(telemetry.get("snr", 25.0))
        per = float(telemetry.get("per", 0.02))
        retries = int(telemetry.get("retries", 0))
        busy = float(telemetry.get("busy", 0.20))
        jitter = float(telemetry.get("jitter", 10.0))

        critical_reasons = []
        degrading_reasons = []

        # Check Critical Thresholds
        if rssi <= RSSI_CRITICAL:
            critical_reasons.append(f"RSSI {rssi:.1f} dBm <= {RSSI_CRITICAL} dBm (fringe coverage drop)")
        if snr <= SNR_CRITICAL:
            critical_reasons.append(f"SNR {snr:.1f} dB <= {SNR_CRITICAL} dB (noise floor dominance)")
        if per >= PER_CRITICAL:
            critical_reasons.append(f"PER {per*100:.1f}% >= {PER_CRITICAL*100:.0f}% (link packet collapse)")
        if retries >= RETRIES_CRITICAL:
            critical_reasons.append(f"Retries {retries} >= {RETRIES_CRITICAL} (transceiver ACK exhaustion)")
        if busy >= BUSY_CRITICAL:
            critical_reasons.append(f"Channel busy {busy*100:.0f}% >= {BUSY_CRITICAL*100:.0f}% (severe co-channel jam)")
        if jitter >= JITTER_CRITICAL:
            critical_reasons.append(f"Jitter {jitter:.1f} ms >= {JITTER_CRITICAL:.0f} ms (transit queue collapse)")

        # Check Degrading Thresholds
        if rssi <= RSSI_DEGRADING and rssi > RSSI_CRITICAL:
            degrading_reasons.append(f"RSSI {rssi:.1f} dBm <= {RSSI_DEGRADING} dBm (signal attenuation)")
        if snr <= SNR_DEGRADING and snr > SNR_CRITICAL:
            degrading_reasons.append(f"SNR {snr:.1f} dB <= {SNR_DEGRADING} dB (elevated noise)")
        if per >= PER_DEGRADING and per < PER_CRITICAL:
            degrading_reasons.append(f"PER {per*100:.1f}% >= {PER_DEGRADING*100:.0f}% (packet error rise)")
        if retries >= RETRIES_DEGRADING and retries < RETRIES_CRITICAL:
            degrading_reasons.append(f"Retries {retries} >= {RETRIES_DEGRADING} (moderate retransmissions)")
        if busy >= BUSY_DEGRADING and busy < BUSY_CRITICAL:
            degrading_reasons.append(f"Channel busy {busy*100:.0f}% >= {BUSY_DEGRADING*100:.0f}% (congestion)")
        if jitter >= JITTER_DEGRADING and jitter < JITTER_CRITICAL:
            degrading_reasons.append(f"Jitter {jitter:.1f} ms >= {JITTER_DEGRADING:.0f} ms (multipath delay spread)")

        # Decision Arbitration
        if critical_reasons:
            decision = "TRIGGER_FAILOVER"
            self.channel = 11 if self.channel == 6 else 6
            root_cause = "Critical link collapse detected: " + "; ".join(critical_reasons)
            triggered = critical_reasons
        elif degrading_reasons:
            decision = "MONITOR_AND_EVALUATE_FAILOVER"
            self.antenna = 1 - self.antenna
            root_cause = "Link degradation in progress: " + "; ".join(degrading_reasons)
            triggered = degrading_reasons
        else:
            decision = "CONTINUE_NORMAL_OPERATION"
            root_cause = "All RF metrics strictly within nominal IEEE bounds. Zero action required."
            triggered = []

        dur = time.perf_counter() - t0

        return {
            "decision": decision,
            "root_cause": root_cause,
            "rules_triggered": triggered,
            "latency_sec": dur,
            "memory_kb": 1.2  # Negligible RAM footprint for threshold logic
        }

if __name__ == "__main__":
    agent = BaselineRuleAgent()
    sample = {"rssi": -83.0, "snr": 9.0, "per": 0.22, "retries": 4, "busy": 0.60, "jitter": 40.0}
    res = agent.evaluate(sample)
    print("Baseline Evaluation:")
    for k, v in res.items():
        print(f"  {k}: {v}")
