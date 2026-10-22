# 🤝 Contributing to SlothMesh

Thank you for your interest in contributing to **SlothMesh**! SlothMesh is an open-source, reproducible edge AI architecture developed for the **Arduino UNO Q** (dual-core Linux + ARM Cortex-M33).

We welcome contributions of all levels—whether fixing typos, improving documentation, expanding test scenarios, or optimizing embedded C++ inference.

---

## 🚀 Quick Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yashwan7/uno-Q.git
   cd uno-Q
   ```

2. **Install dependencies:**
   ```bash
   make setup
   ```

3. **Verify the test suite:**
   ```bash
   make test
   ```

4. **Run the agent in simulation mode:**
   ```bash
   make simulate
   ```

---

## 🎯 Good First Issues (Beginner-Friendly Ideas)

Here are 5 concrete, high-impact tasks ready for contributors:

### Issue #1: Add a Real ESP32 / LoRa SX1262 Telemetry Provider
- **Area:** Firmware / Drivers
- **Goal:** In `firmware/`, add an adapter sketch that interfaces with an SX1262 LoRa or ESP32-NOW transceiver, populating the 14-byte `SlothTelemetryPacket_t` with physical RSSI and SNR readings.
- **Skills:** Arduino C++, SPI/I2C basics.

### Issue #2: Expand Scenarios to 60 with Satellite Doppler Shift Cases
- **Area:** Data & Benchmarks (`agent/scenarios.json`)
- **Goal:** Add 10-20 additional scenarios representing LEO satellite passes or high-speed vehicle Doppler shift (rapidly changing SNR and frequency offset).
- **Skills:** JSON, RF intuition.

### Issue #3: Implement a llama.cpp / GGUF Direct Host Runner
- **Area:** Agent (`agent/sloth_agent.py`)
- **Goal:** Provide an alternative local inference backend using `llama-cpp-python` with 4-bit GGUF models directly on the Linux host SoC, avoiding the need for a separate Ollama background daemon.
- **Skills:** Python, llama.cpp.

### Issue #4: Physical Current Profiling Log Upload
- **Area:** Hardware / Power (`docs/POWER_MEASUREMENT.md`)
- **Goal:** If you have access to a Nordic PPK2, Monsoon, or INA219 breakout, follow the procedure in `docs/POWER_MEASUREMENT.md`, record raw CSV traces, and submit a PR replacing a `[TO BE MEASURED]` placeholder with real empirical oscillograms.
- **Skills:** Hardware instrumentation, multimeter / power profiler.

### Issue #5: Web Dashboard Tactical CAD Dark/Light Contrast Enhancements
- **Area:** Dashboard (`dashboard/`)
- **Goal:** Add a high-contrast tactical map mode and keyboard shortcuts (e.g., keys `1`, `2`, `3`, `4` to instantly toggle scenarios) to `dashboard/app.js`.
- **Skills:** Vanilla JavaScript, CSS, Leaflet.js.

---

## 📝 Pull Request Guidelines

1. Ensure all 15 pytest unit tests pass before submitting (`make test`).
2. Run `make benchmark` to verify that your changes do not break the evaluation pipeline.
3. Keep commit messages clear and descriptive (e.g., `feat:`, `fix:`, `docs:`, `test:`).
4. SlothMesh is licensed under the permissive **MIT License**. All contributions must be compatible with MIT terms.
