#!/usr/bin/env python3
"""
Arduino UNO Q Orchestration Service: Edge Telemetry Sentinel & Dual-Model Cognitive Layer
Hardware Target: Arduino UNO Q (Qualcomm Linux AP + STM32U585 Cortex-M33 MCU Bridge)

Features:
- Live MCU Bridge binary frame parsing (0xA5 IPC protocol)
- Node heartbeat & timeout tracking (3.5s expiration)
- Tier 1: SmolLM2 135M (Fast Triage Agent)
- Tier 2: Qwen 3 0.6B (Deep Causal Attribution & Chain-of-Thought)
- Tier 3: Laya System-1 NOULs Deterministic Decision & Arbitration Layer
- Dual OLED & ANSI Terminal Visual Dashboard
- Real-time JSON telemetry sync for Tactical CAD Dashboard
"""

import os
import sys
import time
import glob
import json
import threading
import serial
from typing import Dict, Any, Optional

from laya_safety_engine import LayaSafetyEngine
from dual_model_engine import DualModelEngine
from oled_terminal_display import OLEDDisplay

# Status file path for live dashboard sync
STATUS_FILE = os.path.join(os.path.dirname(__file__), "live_status.json")
HEARTBEAT_TIMEOUT_SEC = 3.5

class UnoQOrchestrator:
    def __init__(self, serial_port=None, baudrate=115200):
        self.serial_port = serial_port or self.detect_serial_port()
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = False
        
        self.laya = LayaSafetyEngine()
        self.dual_engine = DualModelEngine()
        self.display = OLEDDisplay()
        
        self.nodes = {
            1: {
                "last_seen": 0,
                "status": "UNKNOWN",
                "seq": 0,
                "rssi": -62.0,
                "snr": 24.0,
                "decision": "INITIALIZING",
                "consensus": "INITIALIZING",
                "smollm": {},
                "qwen": {},
                "causal": "Awaiting Arduino UNO Q MCU frame stream..."
            }
        }
        self.simulated_override = None

    def detect_serial_port(self):
        """Auto-detect Arduino UNO Q Bridge /dev/ttyACM0 or USB modem ports."""
        candidates = glob.glob("/dev/ttyACM*") + glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/ttyUSB*")
        for port in candidates:
            return port
        return "/dev/ttyACM0"

    def connect_serial(self):
        if not self.serial_port or not os.path.exists(self.serial_port):
            print(f"[UNO Q] Warning: Serial port {self.serial_port} not found. Running in hardware-ready loop.")
            return False
        try:
            self.serial_conn = serial.Serial(self.serial_port, self.baudrate, timeout=1)
            print(f"[UNO Q] Connected to live Arduino UNO Q MCU on {self.serial_port} @ {self.baudrate}")
            return True
        except Exception as e:
            print(f"[UNO Q] Serial connection error: {e}")
            return False

    def process_telemetry(self, node_id: int, raw_status: int, seq: int):
        now = time.time()
        node = self.nodes.get(node_id, {})
        node["last_seen"] = now
        node["seq"] = seq

        # Check if user injected a simulation override for live demo
        if self.simulated_override:
            rssi, snr, per, retries, jitter, tinyml_cls = self.simulated_override
        else:
            # Derived from MCU Bridge live packet (status byte: 0=Normal, 1=Degrading, 2=Critical, 3=Heartbeat)
            if raw_status == 0 or raw_status == 3:
                rssi, snr, per, retries, jitter, tinyml_cls = -62.0, 24.0, 0.01, 0, 8.0, "NORMAL"
            elif raw_status == 1:
                rssi, snr, per, retries, jitter, tinyml_cls = -82.0, 10.0, 0.22, 4, 38.0, "DEGRADING"
            else:
                rssi, snr, per, retries, jitter, tinyml_cls = -94.0, 3.0, 0.68, 8, 110.0, "CRITICAL"

        telemetry = {
            "node_id": node_id,
            "rssi": rssi,
            "snr": snr,
            "per": per,
            "retries": retries,
            "jitter": jitter,
            "tinyml_class": tinyml_cls
        }

        # 1. Run Dual-Model Edge Cognitive Pipeline (SmolLM2-135M + Qwen3-0.6B)
        # On normal link, we can use fast cached triage to save energy (Sloth Pacing); on anomaly we invoke full dual models
        if tinyml_cls != "NORMAL" or self.simulated_override:
            dual_res = self.dual_engine.run_dual_inference(telemetry)
            smollm_out = dual_res["smollm"]
            qwen_out = dual_res["qwen"]
        else:
            smollm_out = {
                "model": "smollm2:135m",
                "latency_sec": 0.015,
                "proposed_state": "NORMAL",
                "proposed_action": "CONTINUE_NORMAL_OPERATION",
                "raw_text": "Link nominal. Paced energy preservation active.",
                "status": "PACED"
            }
            qwen_out = {
                "model": "qwen3:0.6b",
                "latency_sec": 0.020,
                "proposed_state": "NORMAL",
                "proposed_action": "CONTINUE_NORMAL_OPERATION",
                "content": "All RF metrics within optimal NOUL bounds. Zero packet loss.",
                "thinking": "Link parameters nominal. Sloth pacing enabled.",
                "status": "PACED"
            }

        # 2. Tier 3: Laya System-1 NOULs Deterministic Arbitration
        laya_eval = self.laya.evaluate_dual_model(telemetry, smollm_out, qwen_out)
        state = laya_eval["state"]
        decision = laya_eval["action"]

        node["status"] = state
        node["rssi"] = rssi
        node["snr"] = snr
        node["decision"] = decision
        node["consensus"] = laya_eval["consensus_badge"]
        node["smollm"] = smollm_out
        node["qwen"] = qwen_out
        node["causal"] = laya_eval["causal_explanation"]

        # 3. Render Rich Visual OLED Display Box
        box = self.display.render_dual_model(node_id, telemetry, laya_eval)
        print(box)

        # 4. Save Real-Time Status for Tactical CAD Dashboard
        self._sync_live_status(node_id, telemetry, laya_eval)

    def _sync_live_status(self, node_id: int, telemetry: Dict, laya_eval: Dict):
        try:
            status_data = {
                "timestamp": time.time(),
                "node_id": node_id,
                "telemetry": telemetry,
                "laya": laya_eval
            }
            with open(STATUS_FILE, "w") as f:
                json.dump(status_data, f, indent=2)
        except Exception:
            pass

    def check_timeouts(self):
        """Ensures nodes that stop transmitting are marked CRITICAL."""
        now = time.time()
        for nid, data in self.nodes.items():
            if data["last_seen"] > 0 and (now - data["last_seen"]) > HEARTBEAT_TIMEOUT_SEC:
                if data["status"] != "TIMEOUT_CRITICAL":
                    data["status"] = "TIMEOUT_CRITICAL"
                    data["decision"] = "TRIGGER_CHANNEL_FAILOVER"
                    data["causal"] = f"Node missed heartbeat (>{HEARTBEAT_TIMEOUT_SEC}s). Marked unreachable."
                    print(f"\n[ALERT] NODE {nid} TIMEOUT! Exceeded {HEARTBEAT_TIMEOUT_SEC}s threshold.")
                    
                    tel = {"rssi": -105.0, "snr": 0.0, "per": 1.0, "retries": 10, "jitter": 200.0, "tinyml_class": "CRITICAL"}
                    laya_eval = self.laya.evaluate_dual_model(tel, None, None)
                    box = self.display.render_dual_model(nid, tel, laya_eval)
                    print(box)
                    self._sync_live_status(nid, tel, laya_eval)

    def run(self):
        self.running = True
        self.connect_serial()
        print("\n" + "=" * 74)
        print(" 🦥 ARDUINO UNO Q DUAL-MODEL SENTINEL & LAYA DECISION LAYER")
        print(f" Target Serial Port: {self.serial_port}")
        print(" Models: smollm2:135m (Triage) + qwen3:0.6b (Deep Reasoner) via Ollama")
        print(" Decision Layer: Laya System-1 NOULs (Deterministic Hardware Invariant)")
        print("=" * 74)

        while self.running:
            self.check_timeouts()

            # Read Arduino UNO Q Hardware Serial Stream
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    header = self.serial_conn.read(1)
                    if header == b'\xa5':
                        payload = self.serial_conn.read(8)
                        if len(payload) == 8:
                            node_id = payload[0]
                            status = payload[1]
                            seq = int.from_bytes(payload[2:6], 'big')
                            self.process_telemetry(node_id, status, seq)
                except Exception as e:
                    time.sleep(0.5)
            else:
                time.sleep(1.0)

    def stop(self):
        self.running = False
        if self.serial_conn:
            self.serial_conn.close()

if __name__ == "__main__":
    orchestrator = UnoQOrchestrator()
    try:
        orchestrator.run()
    except KeyboardInterrupt:
        orchestrator.stop()
        print("\nStopped.")
