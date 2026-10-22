---
title: "SlothMesh: Energy-Paced Autonomous Edge AI for the Arduino UNO Q"
published: true
tags: devchallenge, hf26challenge, arduino, tinyml
canonical_url: https://github.com/yashwan7/uno-Q
cover_image: https://raw.githubusercontent.com/yashwan7/uno-Q/main/dashboard/preview.png
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

---

## 🌟 What I Built

SlothMesh channels the calm wisdom of the sloth: **move at your own pace, conserve maximum energy, and let the world come to you.**

In IoT sensor networks, smart-home setups, and field edge systems, developers spend hours:
- Staring at cryptic wireless signal analyzers and packet loss graphs.
- Climbing ladders to point directional antennas.
- Power-cycling unresponsive nodes.
- Swapping batteries that were drained by power-hungry, continuous network polling.

**SlothMesh is a zero-effort, physical edge AI sentinel engineered specifically for the dual-core Arduino UNO Q.** It couples an ultra-low-power microcontroller with an on-board Linux application processor to self-heal RF networks without requiring human intervention:

1. **The Sleepy Sentry (ARM Cortex-M33 Coprocessor):** Stays in low-power standby. Every 5 seconds ("slow and steady"), it wakes up for **1.18 milliseconds** to evaluate 6 physical radio features using a **4.5 KB INT8 TinyML Neural Network**. If the link is Healthy, it returns immediately to sleep—conserving power compared to continuous polling.
2. **The Cognitive Remediator (Qualcomm Linux Host):** When persistent packet loss or RF jamming strikes, the M33 coprocessor fires a hardware interrupt line. The Linux host awakens a local **open-weight Small Language Model (Qwen 0.6B via Ollama)** to diagnose the physical root cause (multipath reflections vs. noise floor elevation vs. co-channel saturation) and autonomously actuate GPIO switches (diversity antenna swap or emergency channel hop).
3. **The Deterministic Safety Gate (Laya System-1):** All model outputs are checked against hard mathematical boundaries (NOULs). If the language model hesitates or returns an invalid action during critical failure, the system falls back to a deterministic rule baseline (`agent/baseline_agent.py`) within microseconds.

---

## 📹 Demo & Visualizations

- **Interactive Tactical CAD Dashboard:** Live web interface featuring Leaflet radar map (centered on Sir MVIT Campus), real-time telemetry registers, scenario injectors, and dual-model reasoning feeds: `http://localhost:8085/`.
- **Hardware-Free Simulation:** Run `python3 agent/sloth_agent.py --simulate` to observe real-time decision auditing without hardware.
- **Physical Demo Runner:** Run `python3 run_live_demo.py` to stream live NXP/Arduino frames, inject multipath interference, and watch the system self-heal.
- **Video Storyboard:** Full 60–90 second demo video script documented in [`docs/DEMO.md`](https://github.com/yashwan7/uno-Q/blob/main/docs/DEMO.md).

---

## 💻 Code Repository

The complete open-source codebase—including Arduino UNO Q Zephyr C++ firmware, INT8 TFLite Micro neural network headers, Python agent daemon, baseline benchmark harness, and interactive dashboard—is available on GitHub under the **MIT License**:

{% embed https://github.com/yashwan7/uno-Q %}

---

## 🏗️ How I Built It: Dual-Core Hardware Co-Design

SlothMesh is engineered around the asymmetric hardware architecture of the **Arduino UNO Q**:

```
                       [ Physical Wireless Radio Signals ]
                                        │
                         (6 RF Telemetry Registers)
                                        │
                                        ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │ 🦥 TIER 1: ARM Cortex-M33 Real-Time Coprocessor                        │
    │  • Low-Power Standby Mode (35 µA datasheet typical)                    │
    │  • Wakes every 5 seconds ("Slow and Steady")                           │
    │  • Runs 4.52 KB INT8 Quantized Neural Network in 1.18 ms               │
    │  • Result: HEALTHY ───► Continues Standby (Linux Host stays asleep)    │
    │            DEGRADING/CRITICAL ───► Pulses Hardware Interrupt (GPIO)    │
    └───────────────────────────────────┬────────────────────────────────────┘
                                        │ (14-Byte Binary IPC Packet)
                                        ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │ 🧠 TIER 2: Arduino UNO Q Linux Host SoC (Open-Weight Model)            │
    │  • Runs local open-weight Qwen 3 (0.6B) via Ollama (100% Offline)      │
    │  • Disentangles multipath fading from co-channel jamming               │
    │  • Governed by Laya System-1 Safety Gate & Rule Baseline Fallback      │
    │  • Actuation: Toggles Antenna GPIO 4 or Mesh Channel Hop (Ch 6 -> 11)  │
    └────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
                   [ Mesh Self-Heals | User Stays on Couch ]
```

### 1. The TinyML Classifier (ARM Cortex-M33)
- **Model Architecture:** Fully quantized Multi-Layer Perceptron (6 inputs $\rightarrow$ 32 ReLU $\rightarrow$ 16 ReLU $\rightarrow$ 3 Softmax).
- **Quantization:** Fully integer quantized (`TFLITE_BUILTINS_INT8`).
- **Memory Footprint:** **4,632 bytes (4.52 KB)**, leaving **98% of the Cortex-M33 microcontroller's RAM free** for user peripherals.
- **Inference Latency:** **1.18 ms** per inference @ 160 MHz.
- **Accuracy on Unseen Test Split:** **93.47% INT8 test accuracy** (with negligible 0.22% quantization drop from float32 baseline).
- **Noise Robustness:** Evaluated with Gaussian noise injections ($\sigma=0.10$ maintains 90.95% accuracy).

### 2. The Local Open-Weight SLM Agent (Linux Host)
- **Local Brain:** Runs **Qwen 3 (0.6B)** (522 MB) locally via Ollama with zero internet connection.
- **Safety Allowlist:** Enforces actions strictly from `ALLOWED_ACTIONS` (`CONTINUE_NORMAL_OPERATION`, `MONITOR_AND_EVALUATE_FAILOVER`, `TRIGGER_FAILOVER`).
- **Deterministic Fallback:** 5.0-second execution timeout; if the model fails or hallucinates, `BaselineRuleAgent` takes over immediately.
- **Audit Logging:** Logs every decision, latency timestamp, and reasoning trace to `agent/decisions_audit.jsonl`.

---

## 📊 Benchmark Comparison: Baseline vs. Open-Weight SLMs

We evaluated our rule-based remediation baseline (`agent/baseline_agent.py`) against **Qwen 3 (0.6B)** across **40 diverse scenarios** (`agent/scenarios.json`), covering multipath fade, fringe boundary, airtime exhaustion, queue bufferbloat, and co-channel jamming:

| Architecture / Model | Remediation Correctness | Factual Consistency | Mean Latency | RAM Footprint | Execution Target |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Rule-Based Baseline** | **40 / 40 (100.0%)** | 9 / 40 (22.5%)* | **< 0.05 ms** | **1.2 KB** | Cortex-M33 / Linux Host |
| **Qwen 3 (0.6B)** (Unconstrained) | 22 / 40 (55.0%) | 31 / 40 (77.5%) | **2.62 s** | **522 MB** | Arduino UNO Q Host |
| **SlothMesh Cascaded System** | **40 / 40 (100.0%)** | **38 / 40 (95.0%)** | **2.62 s** (SLM) / **1.18 ms** (M33) | **522 MB** | Dual-Core Asymmetric Pipeline |

*\*Note: The rule-based baseline outputs formatted diagnostic strings that include threshold bounds not present in raw input registers, triggering the numeric filter.*

### Honest Tradeoff Analysis:
- **Where the Baseline Wins:** Microsecond execution (<0.05 ms), 1.2 KB memory, and 100% deterministic safety bounds.
- **Where the SLM Wins:** Nuanced causal attribution (explaining *why* multipath reflections differ from thermal noise or bufferbloat), generating plain-language incident reports for network operators, and synthesizing compound multi-variable interactions.
- **The SlothMesh Solution:** Pair them together. The SLM provides the intelligence and explanation; the rule baseline provides the safety invariant.

---

## ⚡ Energy & Power Profile

- **Duty-Cycled Linux Polling (1.2s active @ 450 mA every 10s):** Average current $\approx \mathbf{150.8\text{ mA}}$.
- **SlothMesh Event-Driven Architecture:** The Cortex-M33 runs the 1.18 ms TinyML check every 5s ($\approx 38.5\,\mu\text{A}$ MCU average). The Linux host remains in deep suspend, waking only during actual RF anomalies (e.g., ~4 incidents/day).
- **Measurement Status:** Physical current traces on the Arduino UNO Q rails are documented in [`docs/POWER_MEASUREMENT.md`](https://github.com/yashwan7/uno-Q/blob/main/docs/POWER_MEASUREMENT.md) with step-by-step instructions for Nordic PPK2 / INA219 instruments. Values pending empirical measurement are marked `[TO BE MEASURED]`.

---

## 🧠 Why Does Open Innovation Matter?

1. **Runs Completely Offline with Zero Cloud Reliance:** Disasters, remote agricultural fields, and marine stations do not have dependable internet connections. SlothMesh runs 100% on the Arduino UNO Q silicon.
2. **Absolute Data Privacy:** Edge RF telemetry, device positions, and network topology never leave the local hardware.
3. **Custom Hardware Quantization:** Open weights allow precision quantization down to a 4.52 KB INT8 C-array header that executes within microcontroller SRAM.
4. **Zero Recurring API Costs:** You buy the hardware once, flash it, and it runs for free forever.

---

## ⚠️ Limitations & Future Work

- **Synthetic Training Telemetry:** The initial 100,000-sample dataset was synthetically generated from mathematical IEEE propagation formulas. We have provided `data/log_real_telemetry.py` to capture live transceiver frames for retraining.
- **Power Profiler Verification:** While the 1.18 ms execution time is verified via DWT cycle counters, whole-board current traces are scheduled for measurement with a Nordic PPK2 as outlined in `docs/POWER_MEASUREMENT.md`.
- **What's Next:** Direct on-device GGUF inference via `llama-cpp-python` (removing the Ollama daemon) and NPU hardware acceleration via Qualcomm AI Hub.

---

## 🏆 Prize Categories

- **Featured Category:** **Best Use of Arduino ($200 USD)**  
  *Engineered specifically for the **Arduino UNO Q**, taking full advantage of its dual-core architecture: 4.52 KB INT8 TinyML running on the real-time ARM Cortex-M33 coprocessor, coupled with an open-weight Small Language Model running on the Qualcomm Linux host SoC.*
- **Main Challenge:** **Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady ($250 USD)**  
  *An energy-paced, sloth-inspired edge AI system that eliminates human troubleshooting and conserves power through asymmetric edge computing.*

---

## 📜 License & Acknowledgments
Licensed under the **MIT License**. Built with Arduino UNO Q, TensorFlow Lite Micro, Ollama, and Qwen 3.
Dedicated to International Sloth Day 🦥—may our code work smart so we can rest easy!
