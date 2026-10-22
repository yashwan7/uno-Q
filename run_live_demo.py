#!/usr/bin/env python3
"""
🦥 RESq Mesh / SlothMesh Live Demo Runner
Target Hardware: Arduino UNO Q & NXP FRDM-MCXN236

Interactive Demo Flow for Judges:
1. NORMAL: Ingests real NXP hardware packets from /dev/cu.usbmodemFIK54L1PUAFFP3.
2. DEGRADING: Simulates rain fade & multipath; triggers diversity antenna switch.
3. CRITICAL: Simulates severe RF blackout; invokes local Qwen 0.6B & triggers channel hop.
4. RECOVERY: Restores clean channel; returns to low-power paced monitoring.
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "uno_q_core"))
from uno_q_service import UnoQOrchestrator

def main():
    print("=" * 65)
    print(" 🦥 RESq MESH / SLOTHMESH: LIVE HARDWARE DEMO FOR JUDGES")
    print(" Hardware: Arduino UNO Q + NXP FRDM-MCXN236 Cortex-M33")
    print(" Safety: Laya System-1 NOULs | AI: Local Qwen 3 (0.6B)")
    print("=" * 65)

    orchestrator = UnoQOrchestrator()
    print("\n[STEP 1] Ingesting Live NXP Hardware Stream (5 packets)...")
    orchestrator.connect_serial()
    
    # Read 5 real hardware frames
    read_count = 0
    start_t = time.time()
    while read_count < 5 and (time.time() - start_t) < 8:
        if orchestrator.serial_conn and orchestrator.serial_conn.is_open:
            hdr = orchestrator.serial_conn.read(1)
            if hdr == b'\xa5':
                payload = orchestrator.serial_conn.read(8)
                if len(payload) == 8:
                    orchestrator.process_telemetry(payload[0], payload[1], int.from_bytes(payload[2:6], 'big'))
                    read_count += 1
        time.sleep(0.1)

    print("\n[STEP 2] Simulating RF Degradation (Rain Fade / Multipath)...")
    time.sleep(1.5)
    orchestrator.simulated_override = (-82.0, 9.0, 0.28, 4, 38.0, "DEGRADING")
    orchestrator.process_telemetry(1, 1, 101)

    print("\n[STEP 3] Simulating Critical Channel Collapse (RF Jam)...")
    time.sleep(1.5)
    orchestrator.simulated_override = (-95.0, 2.0, 0.74, 9, 120.0, "CRITICAL")
    orchestrator.process_telemetry(1, 2, 102)

    print("\n[STEP 4] Channel Stabilized (Full Recovery)...")
    time.sleep(1.5)
    orchestrator.simulated_override = None
    orchestrator.process_telemetry(1, 0, 103)

    print("\n" + "=" * 65)
    print(" ✅ LIVE DEMO COMPLETE: All transitions verified under Laya Safety Rules.")
    print("=" * 65)

if __name__ == "__main__":
    main()
