# 📡 SlothMesh RF Telemetry Dataset & Telemetry Ingestion Guide

> **IMPORTANT DISCLOSURE:**
> The primary dataset (`slothmesh_telemetry_dataset.csv`, 100,000 samples) is **SYNTHETIC**.
> It was generated algorithmically using mathematical propagation and channel collision models derived from **IEEE 802.11 b/g/n (2.4 GHz)** and **IEEE 802.15.4 (Zigbee / Thread)** wireless standards.

---

## 1. Why Synthetic Data for the Prototype?

Edge RF telemetry datasets with ground-truth root cause labels (e.g., distinguishing between multipath fading, rain attenuation, co-channel contention, and antenna misalignment) cannot be easily labeled in physical field tests without laboratory spectrum analyzers and controlled anechoic chambers.

To train the initial INT8 TinyML model (~4.5 KB) on the ARM Cortex-M33 coprocessor:
1. We synthesized 100,000 telemetry snapshots covering three operational states: `HEALTHY (0)`, `DEGRADING (1)`, and `CRITICAL (2)`.
2. We introduced realistic channel noise: 5% stochastic label-boundary noise and Gaussian jitter distributions to mimic imperfect hardware transceivers.
3. Feature ranges and thresholds reflect standard transceiver registers.

---

## 2. Feature Definitions & Hardware Origins

The model ingests 6 physical features from the RF transceiver MAC/PHY layer:

| Feature | Unit | Hardware Source / API Call | Typical Healthy | Typical Degraded | Critical |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `rssi_dbm` | dBm | Radio AGC / RSSI register (`WiFi.RSSI()`, AT86RF215) | -70 to -45 | -85 to -78 | < -88 |
| `snr_db` | dB | Calculated: $\text{RSSI} - \text{NoiseFloor}$ | 20 to 35 | 8 to 15 | < 6 |
| `packet_error_rate` | 0.0–1.0 | Link-layer MAC counter: $\frac{\text{Failed ACKs}}{\text{Total Transmitted}}$ (100-pkt window) | < 0.05 | 0.15 to 0.35 | > 0.40 |
| `retry_count` | count | MAC transmission attempt counter before success or drop | 0 to 1 | 3 to 6 | $\ge 7$ |
| `channel_busy_ratio` | 0.0–1.0 | Clear Channel Assessment (CCA) energy-detect duty cycle | < 0.30 | 0.55 to 0.80 | > 0.85 |
| `jitter_ms` | ms | Packet inter-arrival delay variance: $J = J + \frac{\|D(i-1, i)\| - J}{16}$ | < 15 ms | 35 to 70 ms | > 90 ms |

---

## 3. Data Generation Model

The synthetic dataset was synthesized using the following Gaussian mixture distributions:

- **HEALTHY Class (0):**
  - $\text{RSSI} \sim \mathcal{N}(-60, 6.5)\text{ dBm}$
  - $\text{SNR} \sim \mathcal{N}(26, 4.0)\text{ dB}$
  - $\text{PER} \sim \text{Beta}(1, 50)$ (mean ~0.02)
  - $\text{Retries} \sim \text{Poisson}(0.6)$
  - $\text{CCA Busy} \sim \mathcal{N}(0.22, 0.08)$
  - $\text{Jitter} \sim \mathcal{N}(8.0, 3.5)\text{ ms}$

- **DEGRADING Class (1) — Multipath / Fringe / Congestion:**
  - $\text{RSSI} \sim \mathcal{N}(-82, 4.0)\text{ dBm}$
  - $\text{SNR} \sim \mathcal{N}(11, 2.5)\text{ dB}$
  - $\text{PER} \sim \mathcal{N}(0.25, 0.08)$
  - $\text{Retries} \sim \text{Poisson}(4.2)$
  - $\text{CCA Busy} \sim \mathcal{N}(0.68, 0.12)$
  - $\text{Jitter} \sim \mathcal{N}(42.0, 12.0)\text{ ms}$

- **CRITICAL Class (2) — Jamming / Blackout / Feedline Break:**
  - $\text{RSSI} \sim \mathcal{N}(-95, 3.5)\text{ dBm}$
  - $\text{SNR} \sim \mathcal{N}(2.5, 1.8)\text{ dB}$
  - $\text{PER} \sim \mathcal{N}(0.75, 0.12)$
  - $\text{Retries} \sim \text{Poisson}(9.0)$
  - $\text{CCA Busy} \sim \mathcal{N}(0.92, 0.05)$
  - $\text{Jitter} \sim \mathcal{N}(125.0, 22.0)\text{ ms}$

---

## 4. Logging Real Hardware Telemetry for Retraining

To transition from synthetic to measured real-world telemetry, use the included logging script:

```bash
# Log live telemetry from connected Arduino UNO Q / NXP board over serial
python3 data/log_real_telemetry.py --port /dev/cu.usbmodem* --baud 115200 --output data/real_telemetry.csv
```

Once at least 500 real frames are captured across different environmental conditions, retrain the model:
```bash
python3 models/train_slothmesh_tinyml.py
```
