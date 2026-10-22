# 📊 SlothMesh Open-Weight Model Edge Telemetry Benchmark

This document presents empirical benchmark results evaluating local open-weight models and TinyML architectures running edge RF telemetry verification on the **Arduino UNO Q** hardware platform.

---

## 1. Test Methodology

The benchmark harness (`agent/sloth_benchmark_eval.py`) tests models across 8 standardized edge RF scenarios:
- `S01_healthy_quiescent`: Normal operating conditions
- `S02_degrading_mixed_attenuation`: Multipath fade and high packet loss
- `S03_critical_channel_collapse`: Extreme RF jamming and link collapse
- `S04_only_busy_channel_congestion`: High channel occupancy with strong signal
- `S05_only_weak_signal_fringe`: Fringe coverage area
- `S06_only_jitter_spike`: Transit queue delay variance
- `S07_borderline_link`: Marginal link state
- `S08_recovering_link`: Interference subsiding

### Factual Verification Criteria
1. **Zero Hallucination:** The model must not invent numeric metrics not present in the ingested telemetry.
2. **Metric Completeness:** All abnormal metrics (flagged as non-optimal by the MCU) must be addressed.
3. **Decision Fidelity:** The model must never contradict or alter the deterministic TinyML failover state.

---

## 2. Empirical Results

| Metric | TinyML INT8 MLP | Qwen 3 (0.6B) | Qwen 3 (4B) |
| :--- | :---: | :---: | :---: |
| **Model Size / Weights** | 4,568 bytes (~4.5 KB) | 522 MB | 2.5 GB |
| **RAM Footprint** | < 5 KB | ~650 MB | ~3.1 GB |
| **Target Execution Core** | ARM Cortex-M33 Core | Arduino UNO Q Host SoC | Arduino UNO Q Host SoC |
| **Average Latency** | **1.18 ms** | **1.82 s** | **45.05 s** |
| **Clean Factual Scenarios** | **8 / 8 (100%)** | **7 / 8 (87.5%)** | **8 / 8 (100%)** |
| **Energy Conserved** | 99.9% | 94.8% | 82.1% |

---

## 3. Scenario-by-Scenario Evaluation (Qwen 0.6B)

```json
{
  "S01_healthy_quiescent": {
    "latency": "1.50s",
    "status": "CLEAN",
    "reasoning": "The edge RF event indicates a stable and efficient network environment with all metrics within acceptable thresholds. The RSSI and SNR are within normal ranges, packet errors are low, retries are minimized, and the channel is not busy."
  },
  "S02_degrading_mixed_attenuation": {
    "latency": "2.06s",
    "status": "Remediated",
    "reasoning": "The edge RF event indicates a weak signal (RSSI -84 dBm), low SNR, high packet error rate, and increased retries. The channel is busy, and jitter is elevated, all suggesting potential network instability."
  },
  "S03_critical_channel_collapse": {
    "latency": "1.89s",
    "status": "Remediated",
    "reasoning": "The edge RF event indicates a high level of signal interference, packet errors, and jitter, which are all critical factors contributing to a failure. The TinyML Classifier Output indicates a critical decision to trigger a failure."
  },
  "S08_recovering_link": {
    "latency": "1.50s",
    "status": "CLEAN",
    "reasoning": "The edge RF event shows a stable and efficient network with low RSSI, good SNR, low packet error rate, and minimal retries. The channel is not busy, and jitter is acceptable."
  }
}
```

---

## 4. Key Architectural Takeaways

1. **Sub-1B Models are King for Low-Power Edge SBCs:**
   While larger 4B parameter models provide rich vocabulary, their inference time on edge CPUs without discrete GPU accelerators exceeds 40 seconds. On the other hand, **Qwen 0.6B** finishes in **1.82 seconds**, consuming minimal battery energy and allowing the Arduino UNO Q host to quickly return to low-power standby.
2. **TinyML + SLM Cascading is the Ultimate Pattern:**
   Relying purely on a language model for continuous monitoring would kill the battery within a single afternoon. Using the **4.5 KB INT8 TinyML model on the Cortex-M33 coprocessor** as a micro-power trigger ensures the language model only wakes up when human-level causal reasoning is truly required.
