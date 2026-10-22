"""
OLED & Terminal Status Display Driver
Supports:
1. Physical SSD1306 128x64 I2C OLED (via busio/board or smbus if available)
2. High-Fidelity ANSI OLED Emulation for Terminal / Console Demo
"""

import sys
import time

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
        """
        Renders live node health, Laya decision, and local SLM text
        both to hardware OLED (if present) and to clean ANSI Terminal OLED.
        """
        # Status Color codes
        color = "\033[92m" if status == "NORMAL" else "\033[93m" if status == "DEGRADING" else "\033[91m"
        reset = "\033[0m"
        bold = "\033[1m"
        cyan = "\033[96m"
        gray = "\033[90m"

        # Hardware render
        if self.hardware_available:
            try:
                self.oled.fill(0)
                self.oled.text(f"NODE {node_id}: {status}", 0, 0, 1)
                self.oled.text(f"RSSI: {rssi:.0f} SNR:{snr:.0f}", 0, 16, 1)
                self.oled.text(f"ACT: {decision[:16]}", 0, 32, 1)
                self.oled.text(f"SLM: {slm_text[:20]}", 0, 48, 1)
                self.oled.show()
            except Exception:
                pass

        # Terminal Visual OLED Box
        box = f"""
{gray}┌────────────────────────────────────────────────────────┐{reset}
{gray}│{reset}  {bold}📟 ARDUINO UNO Q / NXP OLED DASHBOARD{reset}  {gray}[128x64 I2C]{reset}        {gray}│{reset}
{gray}├────────────────────────────────────────────────────────┤{reset}
{gray}│{reset}  Node: {bold}NODE-{node_id:02d}{reset}   │  Link State: {color}{bold}{status:12s}{reset}       {gray}│{reset}
{gray}│{reset}  RSSI: {cyan}{rssi:5.1f} dBm{reset}  │  SNR: {cyan}{snr:4.1f} dB{reset}                     {gray}│{reset}
{gray}├────────────────────────────────────────────────────────┤{reset}
{gray}│{reset}  {bold}Laya Decision:{reset} {color}{decision:35s}{reset}{gray}│{reset}
{gray}│{reset}  {bold}Local SLM:{reset} {slm_text[:40]:40s}{gray}│{reset}
{gray}└────────────────────────────────────────────────────────┘{reset}
"""
        return box
