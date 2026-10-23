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

**SlothMesh is an open-source, physical edge AI sentinel engineered specifically for the dual-core Arduino UNO Q.** It couples an ultra-low-power microcontroller with an on-board Linux application processor to self-heal RF networks without requiring human intervention:

1. **The Sleepy Sentry (STM32U585 ARM Cortex-M33 Coprocessor):** Stays in low-power standby. Every 5 seconds ("slow and steady"), it wakes up for **1.18 milliseconds [MEASURED]** to evaluate 6 physical radio features using an **803-parameter, 4.52 KB INT8 TinyML Neural Network**. If the link is Healthy, it returns immediately to sleep—conserving power compared to continuous polling.
2. **The Cognitive Remediator (Qualcomm Linux Host):** When persistent packet loss or RF jamming strikes, the M33 coprocessor fires a hardware interrupt line. The Linux host awakens a local **open-weight Small Language Model (Qwen 0.6B via Ollama)** to diagnose the physical root cause (multipath reflections vs. noise floor elevation vs. co-channel saturation) and autonomously actuate GPIO switches (diversity antenna swap or emergency channel hop).
3. **The Deterministic Safety Gate (Laya System-1):** All model outputs are checked against hard mathematical boundaries (NOULs). If the language model hesitates or returns an invalid action during critical failure, the system falls back to a deterministic rule baseline (`agent/baseline_agent.py`) within microseconds.

---

## 📹 Demo & Visualizations

- **Interactive Tactical CAD Dashboard:** Live web interface featuring Leaflet radar map (centered on Sir MVIT Campus), real-time telemetry registers, scenario injectors, and dual-model reasoning feeds: `http://localhost:8085/`.
- **Hardware-Free Simulation:** Run `python3 run_live_demo.py --simulate` to observe real-time decision auditing without hardware.
- **Physical Demo Runner:** Run `python3 run_live_demo.py --hardware` to stream live Arduino UNO Q frames, inject multipath interference, and watch the system self-heal.
- **Video Storyboard:** Full 60–90 second demo video script documented in [`docs/DEMO.md`](https://github.com/yashwan7/uno-Q/blob/main/docs/DEMO.md).

---

## 💻 Code Repository

The complete open-source codebase—including Arduino UNO Q firmware, INT8 TFLite Micro neural network headers, Python agent daemon, baseline benchmark harness, and interactive dashboard—is available on GitHub under the **MIT License**:

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
    │  • Runs 4.52 KB INT8 Quantized Neural Network in 1.18 ms [MEASURED]    │
    │  • Result: HEALTHY ───► Continues Standby (Linux Host stays asleep)    │
    │            DEGRADING/CRITICAL ───► Pulses Hardware Interrupt (GPIO)    │
    └───────────────────────────────────┬────────────────────────────────────┘
                                        │ (13-Byte Binary IPC Packet)
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
- **Memory Footprint:** **4,632 bytes (4.52 KB Flash)** and **2,048 bytes (2.0 KB SRAM)** tensor arena, leaving **98% of the Cortex-M33 microcontroller's RAM free** for user peripherals.
- **Inference Latency:** **1.18 ms** per inference @ 160 MHz (188,776 cycles measured via DWT cycle counter in `results/m33_dwt_benchmark.log`).
- **Accuracy on Unseen Test Split:** **97.48% INT8 test accuracy** on session-based contiguous partitions (zero row leakage).
- **Noise Robustness:** Evaluated with Gaussian noise injections ($\sigma=0.10$ maintains 97.20% accuracy).

### 2. The Local Open-Weight SLM Agent (Linux Host)
- **Local Brain:** Runs **Qwen 3 (0.6B)** (522 MB) locally via Ollama with zero internet connection.
- **Safety Allowlist:** Enforces actions strictly from `ALLOWED_ACTIONS` (`CONTINUE_NORMAL_OPERATION`, `MONITOR_AND_EVALUATE_FAILOVER`, `TRIGGER_FAILOVER`).
- **Deterministic Fallback:** 5.0-second execution timeout; if the model fails or hallucinates, `BaselineRuleAgent` takes over immediately.
- **Audit Logging:** Logs every decision, latency timestamp, and reasoning trace to `agent/decisions_audit.jsonl`.

---

## 📊 Benchmark Comparison: Baseline vs. Open-Weight SLMs

We evaluated 5 architectures across **52 standardized edge RF scenarios** (5 runs per scenario, 260 total evaluations per model). Full analysis in [`BENCHMARK.md`](https://github.com/yashwan7/uno-Q/blob/main/BENCHMARK.md):

| Architecture / Configuration | Remediation Correctness | Factual Clean Rate | Mean Latency ± StdDev | RAM Footprint | Execution Target |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Deterministic Rules Baseline** | 50 / 52 (**96.15%**) | 10 / 52 (19.2%) | **< 0.05 ms** (± 0.01 ms) | **1.2 KB SRAM** | Cortex-M33 / Host |
| **TinyML INT8 Sentinel** | 52 / 52 (**100.0%**) | 52 / 52 (**100.0%**) | **1.18 ms** (± 0.001 ms) | **2.0 KB SRAM** | STM32U585 M33 (160 MHz) |
| **Qwen 3 (0.6B)** (Unconstrained) | 39 / 52 (**75.0%**) | 39 / 52 (**75.0%**) | **1.82 s** (± 0.35 s) | **522 MB RAM** | Qualcomm Linux Host |
| **Qwen 3 (4B)** (4GB RAM UNO Q only)* | 46 / 52 (**88.46%**) | 46 / 52 (**88.46%**) | **42.10 s** (± 5.40 s) | **2.5 GB RAM** | Qualcomm Linux Host |
| **Cascaded SlothMesh (SLM + Laya)** | **52 / 52 (100.0%)** | **48 / 52 (92.3%)** | **1.18 ms** (M33) / **1.82 s** (SLM) | **524 MB RAM** | Dual-Core Asymmetric Pipeline |

*\*Note on Board RAM: Qwen 4B requires 2.5 GB RAM and is only compatible with the **4 GB RAM variant** of the Arduino UNO Q. On 2 GB boards, it causes an OOM panic. Qwen 0.6B (522 MB) and SmolLM2 (270 MB) run comfortably across both 2 GB and 4 GB hardware.*

### Honest Tradeoff Analysis:
- **Where the Baseline Wins:** Microsecond execution (<0.05 ms), 1.2 KB memory, and 100% deterministic safety bounds.
- **Where the SLM Wins:** Nuanced causal attribution (explaining *why* multipath reflections differ from thermal noise or bufferbloat), generating plain-language incident reports for network operators, and synthesizing compound multi-variable interactions.
- **The SlothMesh Solution:** Pair them together. The SLM provides the intelligence and explanation; the rule baseline provides the safety invariant.

---

## ⚡ Energy & Power Profile

SlothMesh replaces continuous-polling strawmen with an honest, two-domain mathematical power profile:

- **Domain A: Microcontroller (3.3V Rail):**
  $$\bar{I}_{\text{MCU}} = \frac{I_{\text{sleep}} \cdot t_{\text{sleep}} + I_{\text{active}} \cdot t_{\text{active}}}{T_{\text{period}}} = \frac{35\,\mu\text{A} \times 4.9988\text{ s} + 15\,\text{mA} \times 0.00118\text{ s}}{5.0\text{ s}} \approx \mathbf{38.53\,\mu\text{A}}\text{ [ESTIMATED]}$$
- **Domain B: Whole Board (5.0V USB-C Ingress):**
  - Fair duty-cycled polling baseline (10s wake): **150.8 mA average [ESTIMATED]**.
  - SlothMesh event-driven mode (host in deep suspend, waking only on anomaly): **110.1 mA average [ESTIMATED]**.
  - Relative energy reduction: **27.0% [ESTIMATED]**.
- **Measurement Status:** Physical current traces on the Arduino UNO Q rails are documented in [`docs/POWER_MEASUREMENT.md`](https://github.com/yashwan7/uno-Q/blob/main/docs/POWER_MEASUREMENT.md) with step-by-step instructions for Nordic PPK2 / INA219 instruments. Values pending empirical measurement are marked `[TO BE MEASURED]`.

---

## 🔍 Complete Claim Traceability Matrix

Every technical claim in this article is backed by code or raw results in the repository:

| Claim Description | Value Reported | Status Tag | Backing File / Verification Artifact |
| :--- | :---: | :---: | :--- |
| TinyML Quantized Binary Size | 4,632 bytes (4.52 KB) | `[MEASURED]` | [`models/slothmesh_int8.tflite`](https://github.com/yashwan7/uno-Q/blob/main/models/slothmesh_int8.tflite), [`firmware/sloth_m33_model.h`](https://github.com/yashwan7/uno-Q/blob/main/firmware/sloth_m33_model.h) |
| TinyML SRAM Tensor Arena | 2,048 bytes (2.0 KB) | `[MEASURED]` | [`models/metrics.json`](https://github.com/yashwan7/uno-Q/blob/main/models/metrics.json) |
| Cortex-M33 Inference Latency | 1.18 ms (188,776 cycles) | `[MEASURED]` | [`results/m33_dwt_benchmark.log`](https://github.com/yashwan7/uno-Q/blob/main/results/m33_dwt_benchmark.log) |
| Float32 Test Accuracy | 97.84% | `[BENCHMARKED]` | [`models/metrics.json`](https://github.com/yashwan7/uno-Q/blob/main/models/metrics.json) (Session-based split) |
| INT8 Quantized Test Accuracy | 97.48% | `[BENCHMARKED]` | [`models/metrics.json`](https://github.com/yashwan7/uno-Q/blob/main/models/metrics.json) (Session-based split) |
| Noise Robustness ($\sigma=0.10$) | 97.20% | `[BENCHMARKED]` | [`models/metrics.json`](https://github.com/yashwan7/uno-Q/blob/main/models/metrics.json) |
| Rules Baseline Correctness | 50 / 52 (96.15%) | `[BENCHMARKED]` | [`results/benchmark_results.json`](https://github.com/yashwan7/uno-Q/blob/main/results/benchmark_results.json) |
| Unconstrained Qwen 0.6B Correctness | 39 / 52 (75.0%) | `[BENCHMARKED]` | [`results/benchmark_results.json`](https://github.com/yashwan7/uno-Q/blob/main/results/benchmark_results.json) |
| Cascaded SlothMesh Correctness | 52 / 52 (100.0%) | `[BENCHMARKED]` | [`results/benchmark_results.json`](https://github.com/yashwan7/uno-Q/blob/main/results/benchmark_results.json) |
| Qwen 0.6B Host Latency | 1.82 s (± 0.35 s) | `[BENCHMARKED]` | [`results/benchmark_results.json`](https://github.com/yashwan7/uno-Q/blob/main/results/benchmark_results.json) |
| Qwen 0.6B TTFT | 0.22 s | `[BENCHMARKED]` | [`results/benchmark_results.json`](https://github.com/yashwan7/uno-Q/blob/main/results/benchmark_results.json) |
| Cortex-M33 Average Current | 38.53 µA | `[ESTIMATED]` | [`power/measure_power.py`](https://github.com/yashwan7/uno-Q/blob/main/power/measure_power.py), [`results/power_profile.json`](https://github.com/yashwan7/uno-Q/blob/main/results/power_profile.json) |
| Whole-Board Energy Reduction | 27.0% (vs 10s baseline) | `[ESTIMATED]` | [`power/measure_power.py`](https://github.com/yashwan7/uno-Q/blob/main/power/measure_power.py), [`results/power_profile.json`](https://github.com/yashwan7/uno-Q/blob/main/results/power_profile.json) |
| Board Physical Current Traces | Empirical profile pending | `[TO BE MEASURED]` | Measurement procedure in [`docs/POWER_MEASUREMENT.md`](https://github.com/yashwan7/uno-Q/blob/main/docs/POWER_MEASUREMENT.md) |

---

## 🧠 Why Does Open Innovation Matter?

1. **Runs Completely Offline with Zero Cloud Reliance:** Disasters, remote agricultural fields, and marine stations do not have dependable internet connections. SlothMesh runs 100% on the Arduino UNO Q silicon.
2. **Absolute Data Privacy:** Edge RF telemetry, device positions, and network topology never leave the local hardware.
3. **Custom Hardware Quantization:** Open weights allow precision quantization down to a 4.52 KB INT8 C-array header that executes within microcontroller SRAM.
4. **Zero Recurring API Costs:** You buy the hardware once, flash it, and it runs for free forever.

---

## ⚠️ Limitations & Future Work

- **Synthetic Training Telemetry:** The initial 600,000-sample dataset was synthetically generated from mathematical IEEE propagation formulas. We have provided `data/capture_real_rf.py` to capture live transceiver frames for retraining.
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
