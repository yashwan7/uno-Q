# 🎬 SlothMesh Live Demo Video Script (60–90 Seconds)

**Target Audience:** Hacktoberfest Week 3 Judges, Edge AI Engineers, Embedded Systems Enthusiasts  
**Video Length:** 75 Seconds (Target: 60–90 seconds)  
**Setting:** Split-screen or picture-in-picture showing:
- **Left:** Tactical CAD Web Dashboard (`http://localhost:8085/`) with live Leaflet map and telemetry gauges.
- **Right / Bottom:** Physical Arduino UNO Q hardware on the desk with OLED display and serial console terminal.

---

## ⏱️ Scene-by-Scene Storyboard

### [00:00 – 00:15] Hook: The Problem & The Sloth Solution
- **Visual:** Focus on the human relaxing on a couch, then pan to the Arduino UNO Q on the desk.
- **Voiceover:**
  > *"Every IoT developer knows the pain of mysterious WiFi drops, climbing ladders to adjust antennas, and battery-draining continuous polling. Meet **SlothMesh**—an autonomous edge AI system engineered for the new dual-core **Arduino UNO Q** that channels the energy-saving wisdom of the sloth."*
- **On-Screen Display:** Title card: **SlothMesh: Asymmetric Dual-Core Edge AI for Arduino UNO Q**.

### [00:15 – 00:30] Tier 1: Real-Time Sentry on Cortex-M33
- **Visual:** Tactical Dashboard showing Node 01 in `QUIET SUNSHINE (NORMAL)` mode at 35 µA. Terminal showing periodic M33 checks.
- **Voiceover:**
  > *"Instead of keeping the power-hungry Linux application processor awake, the onboard **ARM Cortex-M33 coprocessor** acts as our sleepy sentry. It wakes every 5 seconds for just **1.18 milliseconds** to evaluate 6 physical RF features using a 4.5 KB INT8 TinyML neural network. If the link is nominal, the host stays asleep."*

### [00:30 – 00:50] Anomaly Injection & Hardware Wake Interrupt
- **Visual:** Click button `02 // RAIN FADE / MULTIPATH (DEGRADING)`. Notice RSSI drops to -82 dBm, Jitter jumps to 38ms. The M33 pulls GPIO Pin 3 high.
- **Voiceover:**
  > *"Now, let's inject severe multipath interference. Within milliseconds, the TinyML model detects link degradation and fires a hardware interrupt to the Linux host."*
- **Visual:** Host awakens. Ollama queries **Qwen 3 (0.6B)**.
- **Voiceover:**
  > *"The host spins up a local, 100% offline open-weight model—Qwen 0.6B. The model diagnoses the physical cause: multipath signal reflections. It autonomously actuates GPIO Pin 4, swapping to a diversity patch antenna. The link stabilizes instantly."*

### [00:50 – 01:10] Critical Jamming & Deterministic Laya Decision Layer
- **Visual:** Click button `03 // RF BLACKOUT / COLLISION (CRITICAL)`. 74% packet loss, RSSI -95 dBm.
- **Voiceover:**
  > *"What if interference is catastrophic? In this severe co-channel blackout, our dual-model pipeline compares fast triage against causal reasoning, verified by our **Laya System-1 Safety Layer**. Even if an LLM hesitates, Laya enforces a hard deterministic rule and triggers an emergency channel hop from Channel 6 to 11. Zero packets lost. Zero human intervention."*

### [01:10 – 01:25] Conclusion & Open Source Pitch
- **Visual:** Full view of the self-healing mesh on the Tactical CAD map at Sir MVIT Campus. Terminal showing audit log.
- **Voiceover:**
  > *"SlothMesh runs 100% offline with zero cloud bills, open weights, and reproducible benchmarks. Check out our open-source repo on GitHub. Thanks for watching!"*

---

## 📹 Video Assets & Links (Placeholders)

- **Live Video Demonstration (YouTube / Vimeo):** `[INSERT YOUTUBE DEMO LINK HERE]`
- **Animated Walkthrough (GIF):** `[INSERT DEMO GIF LINK HERE]`
- **Interactive Web Demo:** `http://localhost:8085/`
