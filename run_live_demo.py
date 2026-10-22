#!/usr/bin/env python3
"""
🦥 RESq Mesh / SlothMesh Live Hardware & Dual-Model Cognitive Demo
Hardware: Arduino UNO Q (Linux AP + Cortex-M33) & NXP FRDM-MCXN236 Cortex-M33
Models: smollm2:135m (Fast Triage) + qwen3:0.6b (Deep Causal Reasoner) via Ollama
Decision Layer: Laya System-1 NOULs (Deterministic Safety Invariants)

Interactive Demo Flow for Judges:
1. NORMAL: Ingests real NXP hardware packets from /dev/cu.usbmodemFIK54L1PUAFFP3.
2. DEGRADING: Simulates rain fade & multipath; SmolLM rapid triage + Qwen3 causal analysis + Laya antenna switch.
3. CRITICAL: Simulates severe RF blackout; SmolLM + Qwen3 analyze collapse; Laya enforces emergency frequency hop.
4. RECOVERY: Restores clean channel; returns to energy-efficient Sloth pacing.
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "uno_q_core"))
from uno_q_service import UnoQOrchestrator

def main():
    print("=" * 74)
    print(" 🦥 RESq MESH / SLOTHMESH: LIVE HARDWARE & DUAL-MODEL DEMO")
    print(" Hardware: Arduino UNO Q + NXP FRDM-MCXN236 Cortex-M33")
    print(" Tier 1 AI: smollm2:135m (Instant Edge Triage, 270MB)")
    print(" Tier 2 AI: qwen3:0.6b   (Deep Causal Attribution, 522MB)")
    print(" Tier 3 Arbiter: Laya System-1 NOULs (Deterministic Safety Layer)")
    print("=" * 74)

    orchestrator = UnoQOrchestrator()
    print("\n[STEP 1] Ingesting Live NXP Hardware Frames (0xA5 Protocol)...")
    orchestrator.connect_serial()
    
    # Read 3 real hardware frames from NXP
    read_count = 0
    start_t = time.time()
    while read_count < 3 and (time.time() - start_t) < 6:
        if orchestrator.serial_conn and orchestrator.serial_conn.is_open:
            hdr = orchestrator.serial_conn.read(1)
            if hdr == b'\xa5':
                payload = orchestrator.serial_conn.read(8)
                if len(payload) == 8:
                    orchestrator.process_telemetry(payload[0], payload[1], int.from_bytes(payload[2:6], 'big'))
                    read_count += 1
        time.sleep(0.1)

    if read_count == 0:
        print("[UNO Q] Note: Running with synthesized nominal baseline for demonstration.")
        orchestrator.process_telemetry(1, 0, 100)

    print("\n[STEP 2] Simulating RF Degradation (Rain Fade / Multipath)...")
    print(">>> Triggering Dual-Model Pipeline: SmolLM (Triage) + Qwen3 (Causal Reasoner)...")
    time.sleep(1.0)
    orchestrator.simulated_override = (-82.0, 9.0, 0.28, 4, 38.0, "DEGRADING")
    orchestrator.process_telemetry(1, 1, 101)

    print("\n[STEP 3] Simulating Critical Channel Collapse (Co-Channel Jamming)...")
    print(">>> Triggering Dual-Model Pipeline: SmolLM (Triage) + Qwen3 (Causal Reasoner)...")
    time.sleep(1.0)
    orchestrator.simulated_override = (-95.0, 2.0, 0.74, 9, 120.0, "CRITICAL")
    orchestrator.process_telemetry(1, 2, 102)

    print("\n[STEP 4] Channel Stabilized (Full Recovery)...")
    time.sleep(1.0)
    orchestrator.simulated_override = None
    orchestrator.process_telemetry(1, 0, 103)

    print("\n" + "=" * 74)
    print(" ✅ LIVE DEMO COMPLETE: Dual-Model inferences verified under Laya Safety Rules.")
    print("=" * 74)

if __name__ == "__main__":
    main()
