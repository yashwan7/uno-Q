# 📊 SlothMesh Edge AI Benchmark: Baseline vs. Open-Weight SLMs

**Target Silicon:** Arduino UNO Q (Linux Application Processor + STM32U5 Cortex-M33 Coprocessor)  
**Harness:** `agent/sloth_benchmark_eval.py`  
**Scenario Callset:** `agent/scenarios.json` (40 Diverse Scenarios)  
**Raw Results:** `agent/benchmark_results.json`  

---

## 1. Evaluation Methodology

We benchmarked three distinct edge decision engines across **40 standardized RF telemetry scenarios**, covering:
- Nominal propagation (line-of-sight, indoor, light load)
- Severe multipath fading, rain attenuation, and antenna polarization drift
- High CCA channel contention and airtime exhaustion
- Perimeter/fringe coverage near sensitivity limits
- Bufferbloat queuing delay spikes
- In-band microwave and co-channel RF jamming collapses
- Conflicting signals (e.g. strong carrier with high packet loss)
- Ambiguous threshold-boundary transitions
- Post-mitigation recovery verification

### Criteria
1. **Remediation Correctness:** Did the system select the exact action needed for the ground-truth root cause (`CONTINUE_NORMAL_OPERATION`, `MONITOR_AND_EVALUATE_FAILOVER`, `TRIGGER_FAILOVER`)?
2. **Factual Faithfulness:** Did the engine avoid hallucinating metrics or numbers absent from the ingested telemetry?
3. **Execution Latency:** Measured over repeated iterations.
4. **RAM Footprint:** Silicon memory required during active evaluation.

---

## 2. Empirical Benchmark Results (40 Scenarios)

| Architecture / Model | Remediation Correctness | Factual Consistency | Mean Latency ± StdDev | RAM Footprint | Execution Core |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Rule-Based Baseline** (`baseline_agent.py`) | **40 / 40 (100.0%)** | 9 / 40 (22.5%)* | **< 0.05 ms** (± 0.01 ms) | **1.2 KB** | Cortex-M33 / Linux Host |
| **Qwen 3 (0.6B)** (Unconstrained SLM) | 22 / 40 (55.0%) | 31 / 40 (77.5%) | **2.62 s** (± 1.62 s) | **522 MB** | Arduino UNO Q Host (Ollama) |
| **Qwen 3 (4B)** (Unconstrained SLM) | 29 / 40 (72.5%) | 36 / 40 (90.0%) | **45.05 s** (± 6.80 s) | **2.5 GB** | Arduino UNO Q Host (Ollama) |
| **SlothMesh Cascaded System** (SLM + Laya Safety Layer) | **40 / 40 (100.0%)** | **38 / 40 (95.0%)** | **2.62 s** (SLM) / **1.18 ms** (M33) | **522 MB** | Dual-Core Asymmetric Pipeline |

*\*Note: The rule-based baseline outputs formatted diagnostic strings that include threshold bounds not present in raw input registers, triggering the numeric filter.*

---

## 3. Honest Tradeoff Analysis: SLM vs. Rule-Based Baseline

### A. Where the Rule-Based Baseline Wins
1. **Deterministic Guarantees:** Threshold logic will never hallucinate or ambiguously hedge. It enforces mathematically provable Network Operational Utility Limits (NOULs).
2. **Zero Compute Overhead:** The baseline evaluates in **under 50 microseconds** and consumes **1.2 KB of RAM**. It can run inside an interrupt service routine on the Cortex-M33 without waking the power-hungry Linux application processor.
3. **Safety Critical Actuation:** In critical blackout events (RSSI < -95 dBm, PER > 70%), waiting 2.6 seconds for an LLM to generate an explanation before hopping channels could result in total connection loss. The baseline triggers emergency failover immediately.

### B. Where the Small Language Model (Qwen 0.6B) Wins
1. **Causal Metric Attribution:** A threshold rule can tell you *that* the link degraded; it cannot explain *why*. Qwen 0.6B correctly distinguishes between:
   - **Multipath Reflections vs. Thermal Noise:** Recognizes that elevated jitter with moderate RSSI indicates delay spread solvable by antenna diversity.
   - **Co-Channel Jamming vs. Physical Obstruction:** Notes that high Clear Channel Assessment (CCA) occupancy indicates external network congestion rather than path loss.
2. **Nuanced Human Diagnostics:** Produces clear, plain-language incident reports for network operators without requiring raw register dumps.
3. **Handling Complex N-Dimensional Tradeoffs:** Eliminates the need for combinatorial, hard-to-maintain multi-variable nested `if/else` ladders when scaling to dozens of transceiver parameters.

### C. When the Baseline is the Better Choice
- On battery-powered remote nodes where every milliampere-second counts.
- For the primary hardware actuation trigger (this is why SlothMesh uses Laya System-1 as the final authority over the SLM).
- When operating in high-frequency control loops (< 100 ms).
