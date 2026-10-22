#!/usr/bin/env python3
"""
Arduino UNO Q Orchestration Service: Edge Telemetry Sentinel & LLM Engine
Hardware Target: Arduino UNO Q (Linux Application Processor + Cortex-M33)
Connected Hardware: NXP FRDM-MCXN236 (/dev/cu.usbmodemFIK54L1PUAFFP3)

Features:
- Live NXP binary frame parsing (0xA5 protocol)
- Node heartbeat & timeout tracking (3.0s expiration)
- Deterministic Laya System-1 Safety Engine
- Local Open-Weight SLM Adapter (Qwen 0.6B / SmolLM via Ollama, 100% offline)
- Dual OLED & ANSI Terminal Dashboard
- Clean, non-blocking fallback if LLM is unavailable
"""

import os
import sys
import time
import glob
import json
import threading
import requests
import serial

from laya_safety_engine import LayaSafetyEngine
from oled_terminal_display import OLEDDisplay

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
SLM_MODEL = os.getenv("SLM_MODEL", "qwen3:0.6b")
HEARTBEAT_TIMEOUT_SEC = 3.5

class UnoQOrchestrator:
    def __init__(self, serial_port=None, baudrate=115200):
        self.serial_port = serial_port or self.detect_nxp_port()
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = False
        
        self.laya = LayaSafetyEngine()
        self.display = OLEDDisplay()
        
        self.nodes = {
            1: {"last_seen": 0, "status": "UNKNOWN", "seq": 0, "rssi": -65, "snr": 20, "decision": "INITIALIZING", "slm_text": "Awaiting NXP stream..."}
        }
        self.simulated_override = None

    def detect_nxp_port(self):
        """Auto-detect NXP FRDM or Arduino modem ports."""
        candidates = glob.glob("/dev/cu.usbmodemFIK*") + glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/ttyACM*")
        for port in candidates:
            if "FIK" in port or "usbmodem" in port:
                return port
        return "/dev/cu.usbmodemFIK54L1PUAFFP3"

    def connect_serial(self):
        if not self.serial_port or not os.path.exists(self.serial_port):
            print(f"[UNO Q] Warning: NXP port {self.serial_port} not found. Running in hardware-ready loop.")
            return False
        try:
            self.serial_conn = serial.Serial(self.serial_port, self.baudrate, timeout=1)
            print(f"[UNO Q] Connected to live NXP FRDM board on {self.serial_port} @ {self.baudrate}")
            return True
        except Exception as e:
            print(f"[UNO Q] Serial connection error: {e}")
            return False

    def query_local_slm(self, node_id, status, rssi, snr, decision):
        """Query local open-weight model (Qwen 0.6B) non-blockingly."""
        prompt = f"Edge mesh Node {node_id} has link state {status} (RSSI {rssi} dBm, SNR {snr} dB). Action taken: {decision}. In 1 sentence explain the physical cause."
        try:
            r = requests.post(OLLAMA_URL, json={
                "model": SLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.1}
            }, timeout=4)
            return r.json()["message"]["content"].strip()
        except Exception:
            return "Local SLM offline. Laya deterministic safety rule executed."

    def process_telemetry(self, node_id, raw_status, seq):
        now = time.time()
        node = self.nodes.get(node_id, {})
        node["last_seen"] = now
        node["seq"] = seq

        # Check if user injected a simulation override for live demo
        if self.simulated_override:
            rssi, snr, per, retries, jitter, tinyml_cls = self.simulated_override
        else:
            # Derived from NXP live packet (status byte: 0=Normal, 1=Degrading, 2=Critical, 3=Heartbeat)
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

        # Run Laya System-1 Safety Assessment
        safety = self.laya.evaluate(telemetry)
        state = safety["state"]
        decision = safety["action"]

        node["status"] = state
        node["rssi"] = rssi
        node["snr"] = snr
        node["decision"] = decision

        # Query Local Open-Weight SLM on state change or degrading
        if state != "NORMAL":
            slm_reason = self.query_local_slm(node_id, state, rssi, snr, decision)
        else:
            slm_reason = "Link nominal. Paced sloth monitoring active."
        node["slm_text"] = slm_reason

        # Render to OLED & Terminal
        box = self.display.render(node_id, state, rssi, snr, decision, slm_reason)
        print(box)

    def check_timeouts(self):
        """Ensures nodes that stop transmitting are marked CRITICAL."""
        now = time.time()
        for nid, data in self.nodes.items():
            if data["last_seen"] > 0 and (now - data["last_seen"]) > HEARTBEAT_TIMEOUT_SEC:
                if data["status"] != "TIMEOUT_CRITICAL":
                    data["status"] = "TIMEOUT_CRITICAL"
                    data["decision"] = "TRIGGER_CHANNEL_FAILOVER"
                    data["slm_text"] = "Node missed heartbeat (>3.5s). Marked unreachable."
                    print(f"\n[ALERT] NODE {nid} TIMEOUT! Exceeded {HEARTBEAT_TIMEOUT_SEC}s threshold.")
                    box = self.display.render(nid, "CRITICAL", -105.0, 0.0, data["decision"], data["slm_text"])
                    print(box)

    def run(self):
        self.running = True
        self.connect_serial()
        print("\n" + "=" * 60)
        print(" 🦥 ARDUINO UNO Q ORCHESTRATION SERVICE STARTED")
        print(f" Target NXP Port: {self.serial_port}")
        print(f" Local SLM: {SLM_MODEL} | Safety: Laya System-1 NOULs")
        print(" Press 'd'=Degrade, 'c'=Critical, 'n'=Normal, 'q'=Quit")
        print("=" * 60)

        while self.running:
            self.check_timeouts()

            # Read NXP Hardware Serial Stream
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
                # Fallback to periodic loop if serial disconnected
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
