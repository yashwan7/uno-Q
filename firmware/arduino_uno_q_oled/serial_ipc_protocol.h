#ifndef SERIAL_IPC_PROTOCOL_H
#define SERIAL_IPC_PROTOCOL_H

#include <stdint.h>

/**
 * SlothMesh Inter-Processor Communication (IPC) Protocol
 * Platform: Arduino UNO Q (ARM Cortex-M33 <---> Linux Host SoC)
 * Design Goal: Extreme energy conservation, zero unnecessary wakeups.
 */

#define SLOTH_MAGIC_BYTE 0x53 // 'S' for Sloth

typedef enum {
    LINK_STATE_HEALTHY   = 0, // Optimal RF link, keep sleeping (conserve power)
    LINK_STATE_DEGRADING = 1, // Channel jitter / packet loss, alert host for evaluation
    LINK_STATE_CRITICAL  = 2  // Link collapsed / RF jam, trigger immediate autonomous failover
} SlothLinkState_t;

typedef enum {
    CMD_TELEMETRY_REPORT  = 0x10,
    CMD_WAKEUP_HOST_ALERT = 0x11,
    CMD_HOST_FAILOVER_ACK = 0x20,
    CMD_SET_SLEEP_PACING  = 0x30
} SlothCommand_t;

#pragma pack(push, 1)
typedef struct {
    uint8_t  magic;               // Must be SLOTH_MAGIC_BYTE
    uint8_t  cmd;                 // SlothCommand_t
    int8_t   rssi_dbm;            // e.g., -75 dBm
    int8_t   snr_db;              // e.g., +15 dB
    uint16_t packet_error_permille; // 0 to 1000 (0.00% to 100.0%)
    uint8_t  retry_count;         // Retransmissions per frame
    uint8_t  channel_busy_pct;    // 0 to 100%
    uint16_t jitter_ms;           // Milliseconds of RF packet jitter
    uint8_t  predicted_state;     // SlothLinkState_t from TinyML INT8 model
    uint16_t sleep_interval_sec;  // Paced wake-up interval (Sloth energy pacing)
    uint8_t  checksum;            // XOR checksum
} SlothTelemetryPacket_t;
#pragma pack(pop)

static inline uint8_t calculate_checksum(const uint8_t *data, size_t len) {
    uint8_t c = 0;
    for (size_t i = 0; i < len; i++) {
        c ^= data[i];
    }
    return c;
}

#endif // SERIAL_IPC_PROTOCOL_H
