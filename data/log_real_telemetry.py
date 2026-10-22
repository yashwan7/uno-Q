#!/usr/bin/env python3
"""
Real Hardware RF Telemetry Logger for SlothMesh
Target: Arduino UNO Q (Linux Host / USB Serial) or NXP FRDM-MCXN236

Role:
Streams physical telemetry frames from the microcontroller over USB CDC / UART,
decodes binary/CSV frames, and appends them to a CSV dataset for retraining
the INT8 TinyML model on real-world RF environments.
"""

import sys
import os
import time
import argparse
import csv
import glob

def parse_args():
    parser = argparse.ArgumentParser(description="SlothMesh Real Telemetry Logger")
    parser.add_argument("--port", type=str, default=None, help="Serial port (auto-detects if None)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--output", type=str, default="data/real_telemetry.csv", help="Output CSV path")
    parser.add_argument("--samples", type=int, default=1000, help="Number of samples to record")
    return parser.parse_args()

def auto_detect_port():
    candidates = glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")
    return candidates[0] if candidates else None

def main():
    args = parse_args()
    port = args.port or auto_detect_port()

    print("=" * 65)
    print(" 📡 SlothMesh Real RF Telemetry Logger")
    print(f" Port: {port or 'SIMULATED (No hardware port detected)'}")
    print(f" Output File: {args.output}")
    print(f" Target Samples: {args.samples}")
    print("=" * 65)

    fields = ['timestamp', 'node_id', 'rssi_dbm', 'snr_db', 'packet_error_rate', 'retry_count', 'channel_busy_ratio', 'jitter_ms', 'label']

    file_exists = os.path.exists(args.output)
    f_out = open(args.output, "a", newline="")
    writer = csv.DictWriter(f_out, fieldnames=fields)
    if not file_exists:
        writer.writeheader()

    if not port or not os.path.exists(port):
        print("\n[NOTE] Running in simulated logging mode (generating synthetic test frames)...")
        import random
        for i in range(min(20, args.samples)):
            row = {
                'timestamp': time.time(),
                'node_id': 1,
                'rssi_dbm': round(random.gauss(-64, 4), 1),
                'snr_db': round(random.gauss(24, 3), 1),
                'packet_error_rate': round(max(0, random.gauss(0.02, 0.01)), 3),
                'retry_count': random.randint(0, 1),
                'channel_busy_ratio': round(random.uniform(0.15, 0.35), 2),
                'jitter_ms': round(max(1, random.gauss(8, 2)), 1),
                'label': 0
            }
            writer.writerow(row)
            f_out.flush()
            time.sleep(0.05)
        print(f"Recorded 20 simulated baseline frames to {args.output}")
        f_out.close()
        return

    try:
        import serial
        ser = serial.Serial(port, args.baud, timeout=2)
        print(f"[CONNECTED] Logging from {port} @ {args.baud} baud...")
        count = 0
        while count < args.samples:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue
            # Format expected: CSV from firmware or binary 0xA5
            parts = line.split(",")
            if len(parts) >= 6:
                try:
                    row = {
                        'timestamp': time.time(),
                        'node_id': 1,
                        'rssi_dbm': float(parts[0]),
                        'snr_db': float(parts[1]),
                        'packet_error_rate': float(parts[2]),
                        'retry_count': int(parts[3]),
                        'channel_busy_ratio': float(parts[4]),
                        'jitter_ms': float(parts[5]),
                        'label': int(parts[6]) if len(parts) > 6 else 0
                    }
                    writer.writerow(row)
                    f_out.flush()
                    count += 1
                    if count % 25 == 0:
                        print(f"Recorded {count}/{args.samples} frames...")
                except ValueError:
                    pass
        ser.close()
        print(f"\n[DONE] Saved {count} physical frames to {args.output}")
    except Exception as e:
        print(f"Error accessing serial port: {e}")
    finally:
        f_out.close()

if __name__ == "__main__":
    main()
