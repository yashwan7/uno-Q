"""
OLED & Terminal Status Display Driver
Supports:
1. Physical SSD1306 128x64 I2C OLED (via busio/board or smbus if available)
2. High-Fidelity Dual-Model ANSI OLED Emulation for Terminal / Console Demo
"""

import sys
import time
from typing import Dict, Any, Optional

class OLEDDisplay:
    def __init__(self, use_hardware=False):
        self.hardware_available = False
        self.width = 128
        self.height = 64

        if use_hardware:
            try:
                import board
                import busio
                import adafruit_ssd1306
                i2c = busio.I2C(board.SCL, board.SDA)
                self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
                self.oled.fill(0)
                self.oled.show()
                self.hardware_available = True
            except Exception:
                self.hardware_available = False

    def render(self, node_id: int, status: str, rssi: float, snr: float, decision: str, slm_text: str):
        """Legacy render method for single model fallback."""
        color = "\033[92m" if status == "NORMAL" else "\033[93m" if status == "DEGRADING" else "\033[91m"
        reset = "\033[0m"
        bold = "\033[1m"
        cyan = "\033[96m"
        gray = "\033[90m"

        box = f"""
{gray}┌────────────────────────────────────────────────────────┐{reset}
{gray}│{reset}  {bold}📟 ARDUINO UNO Q OLED DASHBOARD{reset}  {gray}[128x64 I2C]{reset}            {gray}│{reset}
{gray}├────────────────────────────────────────────────────────┤{reset}
{gray}│{reset}  Node: {bold}NODE-{node_id:02d}{reset}   │  Link State: {color}{bold}{status:12s}{reset}       {gray}│{reset}
{gray}│{reset}  RSSI: {cyan}{rssi:5.1f} dBm{reset}  │  SNR: {cyan}{snr:4.1f} dB{reset}                     {gray}│{reset}
{gray}├────────────────────────────────────────────────────────┤{reset}
{gray}│{reset}  {bold}Laya Decision:{reset} {color}{decision:35s}{reset}{gray}│{reset}
{gray}│{reset}  {bold}Local SLM:{reset} {slm_text[:40]:40s}{gray}│{reset}
{gray}└────────────────────────────────────────────────────────┘{reset}
"""
        return box

    def render_dual_model(self, node_id: int, telemetry: Dict[str, Any], laya_eval: Dict[str, Any]) -> str:
        """
        Renders rich dual-model diagnostic alongside Laya System-1 arbitration.
        Shows SmolLM 135M, Qwen 3 0.6B, Consensus, and Final Binding Action.
        """
        status = laya_eval.get("state", "NORMAL")
        decision = laya_eval.get("action", "CONTINUE_NORMAL_OPERATION")
        consensus = laya_eval.get("consensus_badge", "UNANIMOUS")
        smollm_info = laya_eval.get("smollm_audit", {})
        qwen_info = laya_eval.get("qwen_audit", {})
        causal_exp = laya_eval.get("causal_explanation", "Nominal link operation.")

        rssi = telemetry.get("rssi", -62.0)
        snr = telemetry.get("snr", 24.0)
        per = telemetry.get("per", 0.01) * 100.0

        # Colors
        color = "\033[92m" if status == "NORMAL" else "\033[93m" if status == "DEGRADING" else "\033[91m"
        reset = "\033[0m"
        bold = "\033[1m"
        cyan = "\033[96m"
        yellow = "\033[93m"
        gray = "\033[90m"
        magenta = "\033[95m"

        # Hardware render if connected
        if self.hardware_available:
            try:
                self.oled.fill(0)
                self.oled.text(f"N{node_id}:{status} {consensus[:6]}", 0, 0, 1)
                self.oled.text(f"R:{rssi:.0f} S:{snr:.0f} P:{per:.0f}%", 0, 16, 1)
                self.oled.text(f"ACT:{decision[:15]}", 0, 32, 1)
                self.oled.text(f"QWEN:{causal_exp[:18]}", 0, 48, 1)
                self.oled.show()
            except Exception:
                pass

        smollm_status = "VALID" if smollm_info.get("validated", True) else "OVERRULED"
        smollm_color = "\033[92m" if smollm_info.get("validated", True) else "\033[91m"
        
        qwen_status = "VALID" if qwen_info.get("validated", True) else "OVERRULED"
        qwen_color = "\033[92m" if qwen_info.get("validated", True) else "\033[91m"

        smollm_line = f"SmolLM 135M [{smollm_info.get('latency_sec', 0.1):.2f}s]: {smollm_info.get('action', 'CONTINUE')[:24]} ({smollm_color}{smollm_status}{reset})"
        qwen_line = f"Qwen3 0.6B  [{qwen_info.get('latency_sec', 1.8):.2f}s]: {causal_exp[:36]}"

        box = f"""
{gray}┌────────────────────────────────────────────────────────────────────────┐{reset}
{gray}│{reset}  {bold}📟 ARDUINO UNO Q COGNITIVE SENTINEL{reset}   {cyan}[Dual-Model + Laya System-1]{reset}     {gray}│{reset}
{gray}├────────────────────────────────────────────────────────────────────────┤{reset}
{gray}│{reset}  Node: {bold}NODE-{node_id:02d}{reset}  │  State: {color}{bold}{status:12s}{reset}  │  RSSI: {cyan}{rssi:5.1f}dBm{reset}  │ SNR: {cyan}{snr:4.1f}dB{reset}   {gray}│{reset}
{gray}├────────────────────────────────────────────────────────────────────────┤{reset}
{gray}│{reset}  ⚡ {bold}Tier 1 (Fast Triage):{reset} {smollm_line:50s} {gray}│{reset}
{gray}│{reset}  🧠 {bold}Tier 2 (Deep Causal):{reset} {qwen_line:50s} {gray}│{reset}
{gray}├────────────────────────────────────────────────────────────────────────┤{reset}
{gray}│{reset}  🛡️ {bold}Laya Decision Layer:{reset}  Consensus: {magenta}{consensus:15s}{reset}               {gray}│{reset}
{gray}│{reset}     {bold}BINDING ACTION:{reset}     {color}{bold}{decision:35s}{reset}            {gray}│{reset}
{gray}│{reset}     {bold}PHYSICAL BASIS:{reset}     {laya_eval.get('physics_reason', '')[:45]:45s}  {gray}│{reset}
{gray}└────────────────────────────────────────────────────────────────────────┘{reset}
"""
        return box
