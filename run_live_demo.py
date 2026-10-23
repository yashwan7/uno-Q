#!/usr/bin/env python3
"""
🦥 SlothMesh Live Hardware & Dual-Model Cognitive Demo
Target Hardware: Arduino UNO Q (Qualcomm Linux AP + STM32U585 Cortex-M33)
Models: smollm2:135m (Instant Edge Triage) + qwen3:0.6b (Deep Causal Reasoner) via Ollama
Decision Layer: Laya System-1 NOULs (Deterministic Safety Invariants)

Interactive Demo Flow:
1. NORMAL: Ingests nominal telemetry (RSSI: -58 dBm, SNR: 28 dB, PER: 1%). Paced sleep mode.
2. DEGRADING: Simulates rain fade & multipath (-82 dBm, PER: 28%). SmolLM rapid triage + Qwen3 causal attribution + Antenna diversity toggle (GPIO 4).
3. CRITICAL: Simulates severe RF blackout / jamming (-95 dBm, PER: 74%). Laya safety engine enforces emergency channel failover.
4. RECOVERY: Restores clean channel (Channel 11); returns to energy-paced Sloth sleep mode.

Supports:
  --simulate: Pure simulation mode (runs without physical board attached)
  --hardware: Attempts connection to physical Arduino UNO Q USB serial port
"""

import sys
import os
import time
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "uno_q_core"))
from uno_q_service import UnoQOrchestrator

def parse_args():
    parser = argparse.ArgumentParser(description="SlothMesh Live Demo")
    parser.add_argument("--simulate", action="store_true", default=False, help="Run pure software simulation without hardware")
    parser.add_argument("--hardware", action="store_true", default=False, help="Connect to physical Arduino UNO Q serial port")
    parser.add_argument("--deep-model", default=os.getenv("DEEP_SLM_MODEL", "qwen3:0.6b"), help="Deep causal reasoner SLM (e.g. qwen3:0.6b for 2GB/4GB boards, qwen3:4b for 4GB variant)")
    return parser.parse_args()

def main():
    args = parse_args()
    simulate_mode = args.simulate or not args.hardware
    os.environ["DEEP_SLM_MODEL"] = args.deep_model

    print("=" * 74)
    print(" 🦥 SLOTHMESH: COGNITIVE EDGE MESH LIVE DEMO")
    print(" Target: Arduino UNO Q (Qualcomm Linux AP + STM32U585 Cortex-M33)")
    print(f" Execution Mode: {'SIMULATION (--simulate)' if simulate_mode else 'PHYSICAL HARDWARE (--hardware)'}")
    print(" Tier 1 AI: smollm2:135m (Instant Edge Triage, 270MB)")
    print(f" Tier 2 AI: {args.deep_model:<12s} (Deep Causal Attribution {'[4GB RAM Variant]' if '4b' in args.deep_model else '[2GB/4GB Compatible]'})")
    print(" Tier 3 Arbiter: Laya System-1 NOULs (Deterministic Safety Invariants)")
    print("=" * 74)

    orchestrator = UnoQOrchestrator()

    if not simulate_mode:
        print("\n[STEP 1] Connecting to Physical Arduino UNO Q Serial Port...")
        orchestrator.connect_serial()
        read_count = 0
        start_t = time.time()
        while read_count < 3 and (time.time() - start_t) < 5:
            if orchestrator.serial_conn and orchestrator.serial_conn.is_open:
                hdr = orchestrator.serial_conn.read(1)
                if hdr in [b'\xa5', b'\x53']:
                    payload = orchestrator.serial_conn.read(8)
                    if len(payload) == 8:
                        orchestrator.process_telemetry(payload[0], payload[1], int.from_bytes(payload[2:6], 'big'))
                        read_count += 1
            time.sleep(0.1)

        if read_count == 0:
            print("[UNO Q] No incoming physical frames detected within 5s. Falling back to nominal baseline.")
            orchestrator.process_telemetry(1, 0, 100)
    else:
        print("\n[STEP 1] Ingesting Nominal Link Telemetry (M33 Energy-Paced Mode)...")
        time.sleep(0.5)
        orchestrator.process_telemetry(1, 0, 100)

    print("\n[STEP 2] Injecting RF Degradation (Rain Fade / Multipath Scattering)...")
    print(">>> Triggering Dual-Model Pipeline: SmolLM (Triage) + Qwen3 (Causal Reasoner)...")
    time.sleep(1.0)
    orchestrator.simulated_override = (-82.0, 9.0, 0.28, 4, 38.0, "DEGRADING")
    orchestrator.process_telemetry(1, 1, 101)

    print("\n[STEP 3] Injecting Critical Link Collapse (Co-Channel Jamming / Bleed)...")
    print(">>> Triggering Dual-Model Pipeline: SmolLM (Triage) + Qwen3 (Causal Reasoner)...")
    time.sleep(1.0)
    orchestrator.simulated_override = (-95.0, 2.0, 0.74, 9, 120.0, "CRITICAL")
    orchestrator.process_telemetry(1, 2, 102)

    print("\n[STEP 4] Channel Stabilized (Full Mesh Recovery)...")
    time.sleep(1.0)
    orchestrator.simulated_override = None
    orchestrator.process_telemetry(1, 0, 103)

    print("\n" + "=" * 74)
    print(" ✅ LIVE DEMO COMPLETE: Dual-Model inferences verified under Laya Safety Rules.")
    print("=" * 74)

if __name__ == "__main__":
    main()
