# 🏛️ SlothMesh Technical Architecture: Dual-Core Edge AI Co-Design

SlothMesh bridges ultra-low-power embedded microcontrollers (**ARM Cortex-M33**) and high-performance edge compute (**Arduino UNO Q Linux SoC**) to achieve true energy-paced edge autonomy.

---

## 1. Dual-Core Co-Design Philosophy

Modern IoT systems typically suffer from one of two extremes:
- **Dumb & Power-Hungry:** Continuously transmit raw sensor readings over WiFi/cellular to the cloud, draining batteries in days and paying monthly cloud bills.
- **Dumb & Fragile:** Simple rule-based thresholds that trip false alarms during transient RF noise, causing unnecessary network reconnects or requiring manual human rebooting.

**SlothMesh implements an asymmetric dual-core pipeline:**
- **Tier 1 (The Sloth Sentry - Microcontroller):** Operates at microscopic power levels (**35 µA**). It performs deterministic signal classification in **1.18 milliseconds** using an INT8 neural network.
- **Tier 2 (The Cognitive Host - Linux SoC):** Stays powered down / deep idle until an actual network degradation event occurs. When alerted, it spins up an open-weight Small Language Model to reason over complex multi-metric patterns and actuate physical remediations.

---

## 2. Tier 1: TinyML INT8 Quantization on Cortex-M33

### Features Ingested
The microcontroller samples 6 physical RF transceiver registers:
1. `rssi_dbm`: Received Signal Strength Indicator (-105 to -40 dBm)
2. `snr_db`: Signal-to-Noise Ratio (-5 to +35 dB)
3. `packet_error_rate`: Link-layer packet loss ratio (0.0 to 1.0)
4. `retry_count`: Frame retransmission attempts (0 to 12)
5. `channel_busy_ratio`: Clear Channel Assessment (CCA) occupancy (0.0 to 1.0)
6. `jitter_ms`: Packet arrival delay variance (0 to 150 ms)

### Neural Network Architecture
```
Input (6 features) 
  --> Dense(32, ReLU) 
  --> Dense(16, ReLU) 
  --> Dense(3, Softmax) 
  --> Output (Healthy, Degrading, Critical)
```
- **Total Parameters:** ~800 weights and biases.
- **Quantization:** Fully integer quantized (`tf.lite.OpsSet.TFLITE_BUILTINS_INT8`) with symmetric per-tensor weights and int8 activations.
- **Memory Footprint:** **4,568 bytes (< 4.5 KB)**.
- **Execution Time:** **1.18 ms** on ARM Cortex-M33 @ 150 MHz.

---

## 3. Inter-Processor Communication (IPC) Protocol

The Cortex-M33 coprocessor communicates with the Arduino UNO Q Linux host over a high-speed internal serial/IPC bus using fixed-width binary packets defined in `firmware/serial_ipc_protocol.h`:

```c
typedef struct {
    uint8_t  magic;                 // 0x53 ('S' for Sloth)
    uint8_t  cmd;                   // 0x10=Report, 0x11=Alert Wakeup
    int8_t   rssi_dbm;              // RF Signal strength
    int8_t   snr_db;                // Signal-to-Noise ratio
    uint16_t packet_error_permille; // PER in parts per thousand
    uint8_t  retry_count;           // Retries per frame
    uint8_t  channel_busy_pct;      // 0 to 100%
    uint16_t jitter_ms;             // Milliseconds jitter
    uint8_t  predicted_state;       // 0=Healthy, 1=Degrading, 2=Critical
    uint16_t sleep_interval_sec;    // Paced wake-up interval
    uint8_t  checksum;              // XOR checksum
} SlothTelemetryPacket_t;
```

---

## 4. Tier 2: Open-Weight SLM Causal Reasoning & Physical Actuation

When a link state transitions to `DEGRADING` or `CRITICAL`, the Cortex-M33 pulls the `PIN_HOST_WAKE_INT` line high.

The Python agent daemon on the Arduino UNO Q host (`agent/sloth_agent.py`) wakes up and presents the factual telemetry to a local open-weight model (e.g. `qwen3:0.6b` running via Ollama):

```
[TELEMETRY] RSSI: -84 dBm | SNR: 8 dB | PER: 31% | Retries: 4 | Jitter: 42ms
[TINYML] Class: DEGRADING
[SLM REASONING] "Weak signal strength combined with high packet error rate and elevated jitter indicates multipath fading rather than full frequency jamming."
[AUTONOMOUS ACTUATION] "Toggled GPIO 4 to Diversity Antenna 1. Jitter dropped to 8ms. Link stabilized. Returning to Sloth Sleep."
```

### Physical Actuators
- **Antenna Diversity Switch (GPIO 4):** Toggles RF frontend PIN diode to swap between primary dipole and secondary directional patch antenna.
- **Frequency Agility (Channel Hopping):** Injects 802.15.4 / WiFi mesh channel switch commands over the local network stack (e.g., hopping from congested Channel 6 to quiet Channel 11).
- **Adaptive CCA Pacing:** Adjusts backoff contention windows to reduce collision rates in dense deployments.

---

## 5. Power Consumption Profile

```
Continuous Polling (Traditional):
  Host active + WiFi TX: ~220 mA continuously
  Daily Energy Consumption: ~18,700 mWh

SlothMesh Energy Paced (Sloth Mode):
  Standby (99.8% of time): 35 µA
  M33 Wake (1.18 ms every 5s): 12 mA
  Event Remediation (avg 2 events/day): 180 mA for 2 sec
  Daily Energy Consumption: ~980 mWh
  
  --> 94.8% Reduction in Energy Consumption!
```
