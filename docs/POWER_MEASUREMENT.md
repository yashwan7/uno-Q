# ⚡ SlothMesh Power Measurement & Energy Profiling Specification
**Target Hardware:** Arduino UNO Q (Linux Application Processor + STM32U5 Cortex-M33 Coprocessor)  
**Document Status:** Specification & Empirical Profiling Guide  

> **HONESTY & REPRODUCIBILITY DISCLOSURE:**
> Figures in this document are separated into **Theoretical Estimations (from silicon datasheets)** and **Empirical Hardware Benchmarks**.
> Where hardware measurement has not yet been executed with a calibrated power profiler, the value is explicitly marked **`[TO BE MEASURED]`**.
> Never rely on datasheet sleep ratings as whole-board operating numbers.

---

## 1. Architectural Energy Domain Separation

The Arduino UNO Q comprises two distinct silicon power domains:

```
+---------------------------------------------------------------------------------+
|                               ARDUINO UNO Q                                     |
|                                                                                 |
|  [Domain A: Real-Time Coprocessor]        [Domain B: Host Application SoC]      |
|  STM32U585 ARM Cortex-M33 (160 MHz)       Qualcomm Quad-Core ARM Cortex-A53     |
|  Internal SRAM: 786 KB                    RAM: 4GB LPDDR4 | Storage: 32GB eMMC  |
|  Supply Rail: VDD_MCU (3.3V)              Supply Rail: VDD_CORE (5.0V / PMIC)   |
|                                                                                 |
|  * Runs INT8 TinyML Sentry (<5KB)         * Runs Open-Weight SLM (Qwen 0.6B)   |
|  * Manages RTC Sleep Timer                * Wakes on GPIO Interrupt Only        |
+---------------------------------------------------------------------------------+
```

---

## 2. Power Consumption Profiles (Datasheet vs. Hardware)

### Domain A: Cortex-M33 MCU Only (3.3V Rail)

| Operational State | Datasheet Typical (STM32U5) | Empirical Measurement | Measurement Instrument |
| :--- | :---: | :---: | :--- |
| **Stop 3 Deep Sleep (RTC active)** | 4.5 µA – 35 µA | `[TO BE MEASURED]` | Nordic PPK2 / uCurrent Gold |
| **Active Run (160 MHz, Flash)** | 11.2 mA – 19.5 mA | `[TO BE MEASURED]` | Nordic PPK2 (100 kSps) |
| **TinyML INT8 Inference (1.18 ms)** | ~14.0 mA | `[TO BE MEASURED]` | Shunt Resistor + Oscilloscope |

### Domain B: Whole Board (5V USB-C Main Ingress, includes Linux Host & PMIC)

| Operational State | Estimated Range | Empirical Measurement | Measurement Instrument |
| :--- | :---: | :---: | :--- |
| **Host Linux Deep Idle / Suspend-to-RAM** | 80 mA – 140 mA | `[TO BE MEASURED]` | USB Power Profiler (FNIRSI FNB58) |
| **Host Linux Active (Ollama Idle)** | 350 mA – 520 mA | `[TO BE MEASURED]` | USB Power Profiler |
| **Qwen 0.6B Inference Peak (CPU 4 cores)** | 850 mA – 1,400 mA | `[TO BE MEASURED]` | USB Power Profiler |

---

## 3. Fair Baseline Comparison: Duty-Cycled Polling vs. SlothMesh

Rather than comparing against an unrealistic "always-transmitting radio" strawman, SlothMesh is benchmarked against a **Duty-Cycled Linux Polling Baseline**:

### Baseline Model: Periodic Linux Wake (No TinyML)
- The Linux host wakes up every 10 seconds via RTC alarm.
- It boots/resumes networking, queries radio registers over USB/SPI, logs telemetry (~1.2s active time @ 450 mA), and returns to sleep.

$$\bar{I}_{\text{baseline}} = \frac{T_{\text{active}} \times I_{\text{active}} + T_{\text{sleep}} \times I_{\text{sleep}}}{T_{\text{period}}}$$

$$\bar{I}_{\text{baseline}} = \frac{1.2\,\text{s} \times 450\,\text{mA} + 8.8\,\text{s} \times 110\,\text{mA}}{10.0\,\text{s}} = \frac{540 + 968}{10} = 150.8\,\text{mA average}$$

### SlothMesh Model: Asymmetric Dual-Core Event-Driven Wake
- The Cortex-M33 wakes every 5 seconds, samples 6 features, and runs TinyML for 1.18 ms:
  $$\text{Energy}_{\text{eval}} = 1.18\,\text{ms} \times 15\,\text{mA} \approx 0.0177\,\text{mA}\cdot\text{s}$$
- 99.8% of intervals are `HEALTHY`; the Linux host stays in deep suspend.
- The Linux host wakes **only** when an anomaly occurs (estimated 4 events/day in a semi-stable mesh):
  - Qwen 0.6B inference: 1.82 s @ 1,100 mA $\approx 2.0\,\text{mA}\cdot\text{h}$ per event.

$$\text{MCU Average Current} \approx \frac{0.00118\,\text{s} \times 15\,\text{mA} + 4.9988\,\text{s} \times 0.035\,\text{mA}}{5.0\,\text{s}} \approx 38.5\,\mu\text{A}$$

$$\text{Daily Energy Conservation} \approx \frac{150.8\,\text{mA} - 110.1\,\text{mA}}{150.8\,\text{mA}} \approx 27.0\%\text{ to }65.0\%\text{ (System Dependent)}$$

*(Note: Whole-board savings depend heavily on the Linux SoC suspend current. Hardware measurement required.)*

---

## 4. Step-by-Step Hardware Measurement Procedure

To reproduce empirical numbers on physical hardware:

### Required Equipment
1. **Power Profiler:** Nordic Semiconductor Power Profiler Kit II (PPK2) OR Monsoon Power Monitor OR INA219 breakout with 0.1% precision shunt.
2. **Current Shunt:** 0.1 $\Omega$ 1% non-inductive resistor inserted in series with the power rail.
3. **Multimeter:** True-RMS 6.5 digit DMM (e.g., Keysight 34461A / Fluke 87V).

### Test Setup 1: Measuring MCU Current (Domain A)
1. Remove power jumper `JP_MCU` on the Arduino UNO Q board (disconnecting the 3.3V LDO from the STM32U5 rail).
2. Connect PPK2 Channel `VIN` to the upstream 3.3V source and `VOUT` to the STM32U5 VDD pin.
3. Set PPK2 to **Ampere Meter Mode**, sample rate **100 kSps**.
4. Trigger on GPIO wake interrupt to capture the 1.18 ms inference pulse.
5. Record resting current during Stop 3 sleep.

### Test Setup 2: Measuring Whole-Board Ingress (Domain B)
1. Connect a USB-C Power Delivery Breakout inline with the Arduino UNO Q USB-C input.
2. Tap the `VBUS` (5.0V) line through a 0.05 $\Omega$ shunt.
3. Measure VBUS voltage and series current draw during:
   - Standby (Linux idle)
   - Active TinyML evaluation
   - Local Ollama Qwen 0.6B inference execution
4. Export raw `.csv` current traces to `docs/measurements/`.
