# 📊 SlothMesh Rigorous Edge AI Benchmark & Ablation Study

**Target Hardware:** Arduino UNO Q (Qualcomm Linux AP + STM32U585 Cortex-M33 Coprocessor)  
**Harness:** [`agent/sloth_benchmark_eval.py`](agent/sloth_benchmark_eval.py) (`make bench`)  
**Scenario Callset:** [`agent/scenarios.json`](agent/scenarios.json) (52 Diverse & Adversarial Scenarios, 5 Runs/Each)  
**Raw Benchmark Data:** [`results/benchmark_results.json`](results/benchmark_results.json)  

---

## 1. Evaluation Methodology

We benchmarked 5 distinct edge decision architectures across **52 standardized RF telemetry scenarios** (totaling 260 evaluations per model with 5 runs each to measure stochastic variance).

### Scenarios Covered
- **Nominal Propagation:** Line-of-sight, indoor office, light traffic, low-power whisper links (S01–S08).
- **Physical & Environmental Fading:** Multipath delay spread, rain fade, wet canopy, carrier frequency offset (S09–S16, S46).
- **Network Contention & Congestion:** Heavy CCA occupancy, adjacent-channel bleed, hidden terminal collisions (S17–S24, S41, S50).
- **Interference & RF Jamming:** In-band continuous-wave carrier jammers, 2.45 GHz microwave magnetron leakage, co-channel bleed (S25–S32, S43, S49).
- **Ambiguous & Adversarial Edge Cases:** High RSSI with high PER, beamformed perimeter fringe, bufferbloat jitter spikes, boundary transitions (S33–S40, S42, S44, S47, S48, S51, S52).

---

## 2. Multi-Model Ablation & Benchmark Results (52 Scenarios × 5 Iterations)

| Architecture / Configuration | Remediation Correctness | Factual Clean Rate | Mean Latency ± StdDev | TTFT / Speed | Peak RAM Footprint | Execution Core | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **Deterministic Rules Baseline** (`baseline_agent.py`) | 50 / 52 (**96.15%**) | 10 / 52 (19.2%)* | **< 0.05 ms** (± 0.01 ms) | < 0.05 ms | **1.2 KB SRAM** | Cortex-M33 / Host | `[MEASURED]` |
| **TinyML INT8 Sentinel** (`sloth_m33_model.h`) | 52 / 52 (**100.0%**) | 52 / 52 (**100.0%**) | **1.18 ms** (± 0.001 ms) | 1.18 ms | **2.0 KB SRAM** (4.52 KB Flash) | STM32U585 M33 (160 MHz) | `[MEASURED]` |
| **Qwen 3 (0.6B)** (Unconstrained SLM via Ollama) | 39 / 52 (**75.0%**) | 39 / 52 (**75.0%**) | **1.82 s** (± 0.35 s) | 0.22 s (48 tok/s) | **522 MB RAM** | Qualcomm Linux Host | `[MEASURED]` |
| **Qwen 3 (4B)** (Unconstrained SLM, 4GB RAM only)** | 46 / 52 (**88.46%**) | 46 / 52 (**88.46%**) | **42.10 s** (± 5.40 s) | 1.85 s (4.2 tok/s) | **2.5 GB RAM** | Qualcomm Linux Host | `[MEASURED]` |
| **SlothMesh Cascaded System** (TinyML + Qwen 0.6B + Laya) | **52 / 52 (100.0%)** | **48 / 52 (92.3%)** | **1.18 ms** (M33) / **1.82 s** (SLM) | 0.22 s | **524 MB RAM** (2.0 KB MCU + 522 MB Host) | Dual-Core Asymmetric Pipeline | `[MEASURED]` |

*\*Note 1: The deterministic rule baseline outputs formatted diagnostic strings referencing numeric thresholds (e.g. "-88.0 dBm") not present in input register frames, tripping the strict numeric filter.*  
*\*\*Note 2: **RAM Constraint on Arduino UNO Q Variants:** Qwen 3 (4B) requires 2.5 GB of free RAM. It runs exclusively on the **4 GB RAM variant** of the Arduino UNO Q and will suffer an out-of-memory kernel panic (OOM) on the 2 GB variant. Sub-1B models like **Qwen 0.6B (522 MB)** and **SmolLM2 (270 MB)** run comfortably on both 2 GB and 4 GB hardware.*

---

## 3. Ablation Study: Why Both Tiers are Mandatory

### A. Why TinyML Alone is Not Enough
1. **No Causal Attribution:** An 803-parameter INT8 neural network classifies link status into `HEALTHY`, `DEGRADING`, or `CRITICAL` with 97.48% test accuracy, but it cannot explain *why* the link failed.
2. **Cannot Arbitrate Ambiguous Compound Faults:** When an ambiguous event occurs (such as S41: Hidden Node Collision where signal strength is strong but packet retries climb), the TinyML model outputs a scalar class, unable to suggest protocol-level adjustments (such as enabling RTS/CTS thresholds or traffic shaping).
3. **No Operator Interface:** It cannot synthesize natural-language incident summaries for human network administrators.

### B. Why the SLM Alone is Not Enough
1. **Severe Power Penalty:** Running an open-weight language model continuously requires the Linux application processor to remain awake at ~450 mA – 1,100 mA, draining a battery pack in hours.
2. **Sub-Optimal Latency for Real-Time Loops:** An average inference time of 1.82 seconds is too slow for fast RF control loops that require microsecond-scale reactions to prevent TCP disconnection cliffs.
3. **Stochastic Divergence & Hedging:** Under severe stress, unconstrained SLMs occasionally hedge by selecting `MONITOR_AND_EVALUATE_FAILOVER` instead of commanding an immediate emergency channel switch.

### C. The SlothMesh Cascaded Solution
SlothMesh combines both paradigms into a complementary pipeline:
- **ARM Cortex-M33 Coprocessor:** Executes the **1.18 ms TinyML classifier** at **38.5 µA average current**, keeping the Linux host in deep suspend 99.8% of the time.
- **Qualcomm Linux Host:** Wakes up **only** upon true physical anomalies to run **Qwen 0.6B**, providing deep causal reasoning and generating operator reports.
- **Laya System-1 Safety Layer:** Enforces deterministic Network Operational Utility Limits (NOULs), preventing hallucinations and ensuring **100% remediation correctness**.

---

## 4. Hardware Execution Metadata

```json
{
  "benchmark_host": "Reference Laptop / Arduino UNO Q Linux AP",
  "mcu_coprocessor": "STM32U585 ARM Cortex-M33 @ 160 MHz",
  "dwt_cycles_per_eval": 188776,
  "inference_latency_mcu_ms": 1.18,
  "slm_quantization": "Q4_K_M (Ollama / GGUF)",
  "temperature": 0.1,
  "reproducibility_command": "make bench"
}
```
