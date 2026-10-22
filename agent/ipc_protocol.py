"""
SlothMesh Binary Inter-Processor Communication (IPC) Protocol Parser
Maps exactly to firmware/serial_ipc_protocol.h

Packet Layout (14 Bytes packed):
  uint8_t  magic;                 // 0x53 ('S' for Sloth)
  uint8_t  cmd;                   // 0x10=Report, 0x11=Wakeup Alert
  int8_t   rssi_dbm;              // -128 to 127 dBm
  int8_t   snr_db;                // -128 to 127 dB
  uint16_t packet_error_permille; // 0 to 1000 (0.0% to 100.0%)
  uint8_t  retry_count;           // 0 to 255
  uint8_t  channel_busy_pct;      // 0 to 100%
  uint16_t jitter_ms;             // 0 to 65535 ms
  uint8_t  predicted_state;       // 0=Healthy, 1=Degrading, 2=Critical
  uint16_t sleep_interval_sec;    // Pacing interval in seconds
  uint8_t  checksum;              // XOR of preceding 13 bytes
"""

import struct
from typing import Dict, Any, Optional

SLOTH_MAGIC_BYTE = 0x53
PACKET_FORMAT = "<BBbbHBBHBHB"
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)  # 14 bytes

STATE_NAMES = {
    0: "HEALTHY",
    1: "DEGRADING",
    2: "CRITICAL"
}

def calculate_checksum(data: bytes) -> int:
    c = 0
    for b in data:
        c ^= b
    return c

def pack_telemetry(
    cmd: int,
    rssi_dbm: int,
    snr_db: int,
    packet_error_rate: float,
    retry_count: int,
    channel_busy_ratio: float,
    jitter_ms: int,
    predicted_state: int,
    sleep_interval_sec: int = 5
) -> bytes:
    """Encodes telemetry into a 14-byte SlothTelemetryPacket."""
    per_permille = int(min(1.0, max(0.0, packet_error_rate)) * 1000)
    busy_pct = int(min(1.0, max(0.0, channel_busy_ratio)) * 100)

    raw_header = struct.pack(
        "<BBbbHBBHBH",
        SLOTH_MAGIC_BYTE,
        cmd,
        int(rssi_dbm),
        int(snr_db),
        per_permille,
        int(retry_count),
        busy_pct,
        int(jitter_ms),
        int(predicted_state),
        int(sleep_interval_sec)
    )
    checksum = calculate_checksum(raw_header)
    return raw_header + struct.pack("<B", checksum)

def unpack_telemetry(raw_bytes: bytes) -> Optional[Dict[str, Any]]:
    """Decodes a 14-byte SlothTelemetryPacket. Validates magic byte and XOR checksum."""
    if len(raw_bytes) != PACKET_SIZE:
        return None

    if raw_bytes[0] != SLOTH_MAGIC_BYTE:
        return None

    expected_checksum = calculate_checksum(raw_bytes[:13])
    actual_checksum = raw_bytes[13]
    if expected_checksum != actual_checksum:
        return None

    magic, cmd, rssi, snr, per_permille, retries, busy_pct, jitter, pred_state, sleep_sec, _ = struct.unpack(
        PACKET_FORMAT, raw_bytes
    )

    return {
        "magic": hex(magic),
        "cmd": hex(cmd),
        "rssi": float(rssi),
        "snr": float(snr),
        "per": round(per_permille / 1000.0, 3),
        "retries": int(retries),
        "busy": round(busy_pct / 100.0, 2),
        "jitter": float(jitter),
        "m33_class": STATE_NAMES.get(pred_state, "UNKNOWN"),
        "predicted_state_raw": pred_state,
        "sleep_interval_sec": int(sleep_sec),
        "checksum_valid": True
    }
