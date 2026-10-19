# Realtime WebSocket API

## Overview

The Realtime WebSocket API is the primary communication channel between the Voragon desktop application and the Realtime Backend. It handles session management, audio streaming, and transcript delivery.

**Status:** Partially implemented — Phase 1–2 cover connect, audio, transcripts, heartbeat, session lifecycle, and errors. Production JWT auth is implemented in [P6-005](../roadmap/dev-step-p6-005-api-gateway-auth.md) (optional locally via `JWT_AUTH_REQUIRED`).

## Endpoint

| Environment | URL |
|-------------|-----|
| Local development | `ws://localhost:8000/v1/realtime` |
| Staging (ALB DNS only) | `wss://<alb-host>/v1/realtime` — [k8s/eks/alb](../../k8s/eks/alb/README.md) |
| Staging / production (custom host) | `wss://api.voragon.example/v1/realtime` — [P6-007](../roadmap/dev-step-p6-007-dns-tls.md), [infra/dns](../../infra/dns/README.md) |

The `/v1/` prefix enables future protocol versions (`/v2/realtime`) without breaking existing clients.

## Protocol Summary

| Message Type | Direction | Format | Description |
|-------------|-----------|--------|-------------|
| `audio.start` | Client → Server | JSON | Begin audio streaming |
| `audio.chunk` | Client → Server | Binary | Audio frame data |
| `audio.stop` | Client → Server | JSON | Stop audio streaming |
| `session.resume` | Client → Server | JSON | Resume a previous session |
| `ping` | Client → Server | JSON | Heartbeat |
| `session.started` | Server → Client | JSON | Session established |
| `transcript.partial` | Server → Client | JSON | Interim transcription |
| `transcript.final` | Server → Client | JSON | Final transcription for a segment |
| `error` | Server → Client | JSON | Error notification |
| `session.ended` | Server → Client | JSON | Session closed |
| `pong` | Server → Client | JSON | Heartbeat response |
| `buffer.overflow` | Server → Client | JSON | Audio buffer overflow warning |

## Connection Lifecycle

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server

    C->>S: WebSocket connect /v1/realtime
    S->>C: session.started
    C->>S: audio.start
    loop Audio streaming
        C->>S: audio.chunk (binary)
        S->>C: transcript.partial
        S->>C: transcript.final
    end
    C->>S: audio.stop
    S->>C: session.ended
    C->>S: WebSocket close
```

## Message Format

### Envelope (JSON Control Messages)

All JSON messages share a common envelope:

```json
{
  "type": "message.type",
  "id": "msg-uuid",
  "session_id": "session-uuid",
  "timestamp": "2026-09-19T03:25:00.000Z",
  "payload": { }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Message type identifier |
| `id` | string (UUID) | Yes | Unique message ID |
| `session_id` | string (UUID) | Yes | Session identifier |
| `timestamp` | string (ISO 8601) | Yes | Message creation time (UTC) |
| `payload` | object | Yes | Type-specific payload |

### Binary Audio Frames

Audio frames are sent as **binary WebSocket messages** (not JSON). Each binary frame has a fixed header followed by raw PCM data:

```
┌──────────────────────────────────────────┐
│ Header (17 bytes)                        │
├──────────┬──────────┬──────────┬─────────┤
│ version  │ seq_num  │ timestamp│ payload │
│ (1 byte) │ (4 bytes)│ (8 bytes)│ length  │
│          │          │          │(4 bytes)│
├──────────┴──────────┴──────────┴─────────┤
│ PCM Data (variable)                      │
│ 16-bit signed LE, 16 kHz, mono          │
└──────────────────────────────────────────┘
```

| Header Field | Size | Type | Description |
|-------------|------|------|-------------|
| `version` | 1 byte | uint8 | Protocol version (currently `1`) |
| `seq_num` | 4 bytes | uint32 | Monotonically increasing sequence number |
| `timestamp` | 8 bytes | uint64 | Capture timestamp (microseconds since epoch) |
| `payload_length` | 4 bytes | uint32 | Length of PCM data in bytes |
| PCM data | variable | bytes | Raw s16le PCM audio (typically 640 bytes = 20 ms) |

Binary frames do not use the JSON envelope. The `session_id` is established by the session and implied by the WebSocket connection.

## Client Messages

### `audio.start`

Begin audio streaming for the session.

```json
{
  "type": "audio.start",
  "id": "msg-001",
  "session_id": "session-uuid",
  "timestamp": "2026-09-19T03:25:00.000Z",
  "payload": {
    "language": "en",
    "model": "asr.default",
    "sample_rate": 16000,
    "channels": 1,
    "sample_format": "s16le",
    "frame_duration_ms": 20
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `language` | string | `"en"` | BCP-47 language code |
| `model` | string | `"asr.default"` | Capability alias for ASR model |
| `sample_rate` | int | `16000` | Audio sample rate in Hz |
| `channels` | int | `1` | Number of audio channels |
| `sample_format` | string | `"s16le"` | Sample format |
| `frame_duration_ms` | int | `20` | Frame duration in milliseconds |

### `audio.chunk`

Binary WebSocket message. See [Binary Audio Frames](#binary-audio-frames) above.

Sent continuously after `audio.start` at the configured frame rate (typically every 20 ms).

### `audio.stop`

Stop audio streaming. The session remains open.

```json
{
  "type": "audio.stop",
  "id": "msg-002",
  "session_id": "session-uuid",
  "timestamp": "2026-09-19T03:30:00.000Z",
  "payload": {}
}
```

### `session.resume`

Attempt to resume a previous session after reconnection.

```json
{
  "type": "session.resume",
  "id": "msg-003",
  "session_id": "previous-session-uuid",
  "timestamp": "2026-09-19T03:30:05.000Z",
  "payload": {}
}
```

| Rule | Requirement |
|------|-------------|
| When to send | After a new WebSocket connect and the interim `session.started`, before `audio.start` on the interim session |
| `session_id` | The **previous** (pre-disconnect) session UUID — not the interim id from the latest `session.started` |
| Success | Server sends a second `session.started` with the **restored** `session_id`; subsequent `ping` / `audio.*` use the restored id |
| Failure | `error` with `SESSION_NOT_FOUND` or `SESSION_EXPIRED` (`recoverable: false`); client may continue on the interim session with `audio.start` |

### `ping`

Heartbeat message. Clients **SHOULD** send `ping` when the connection is open but no audio is being streamed (see [Heartbeat](#heartbeat)).

```json
{
  "type": "ping",
  "id": "msg-004",
  "session_id": "session-uuid",
  "timestamp": "2026-09-19T03:30:15.000Z",
  "payload": {}
}
```

| Rule | Requirement |
|------|-------------|
| Envelope | Same required fields as other client JSON messages (`type`, `id`, `session_id`, `timestamp`, `payload`) |
| `payload` | Object (may be empty `{}`) |
| `session_id` | Must match the active session for this WebSocket |
| Server response | `pong` immediately (see below) |
| Errors | Malformed envelope or `session_id` mismatch → recoverable `error` with code `INVALID_MESSAGE` |

## Server Messages

### `session.started`

Sent immediately after WebSocket connection is established.

```json
{
  "type": "session.started",
  "id": "msg-100",
  "session_id": "session-uuid",
  "timestamp": "2026-09-19T03:25:00.000Z",
  "payload": {
    "protocol_version": 1,
    "reconnect_window_s": 30
  }
}
```

### `transcript.partial`

Interim transcription result. May be revised by subsequent partials.

```json
{
  "type": "transcript.partial",
  "id": "msg-101",
  "session_id": "session-uuid",
  "timestamp": "2026-09-19T03:25:01.500Z",
  "payload": {
    "segment_id": "seg-uuid",
    "sequence": 3,
    "text": "Hello world how",
    "language": "en",
    "confidence": 0.92
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `segment_id` | string (UUID) | VAD speech segment identifier |
| `sequence` | int | Monotonically increasing within segment |
| `text` | string | Transcription text (replaces previous partial for this segment) |
| `language` | string | Detected or configured language |
| `confidence` | float | Confidence score (0.0–1.0) |

### `transcript.final`

Final transcription for a completed speech segment.

```json
{
  "type": "transcript.final",
  "id": "msg-102",
  "session_id": "session-uuid",
  "timestamp": "2026-09-19T03:25:02.000Z",
  "payload": {
    "segment_id": "seg-uuid",
    "sequence": 4,
    "text": "Hello world how are you",
    "language": "en",
    "confidence": 0.95,
    "start_ms": 0,
    "end_ms": 2400
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `start_ms` | int | Segment start offset in session (milliseconds) |
| `end_ms` | int | Segment end offset in session (milliseconds) |

### `error`

Error notification. See [Error Handling](error-handling.md) for error codes.

```json
{
  "type": "error",
  "id": "msg-103",
  "session_id": "session-uuid",
  "timestamp": "2026-09-19T03:25:03.000Z",
  "payload": {
    "code": "ASR_INFERENCE_FAILED",
    "message": "ASR inference failed for segment seg-uuid",
    "recoverable": true,
    "details": {}
  }
}
```

### `session.ended`

Session is closed.

```json
{
  "type": "session.ended",
  "id": "msg-104",
  "session_id": "session-uuid",
  "timestamp": "2026-09-19T03:30:00.000Z",
  "payload": {
    "reason": "client_stop"
  }
}
```

| Reason | Description |
|--------|-------------|
| `client_stop` | Client sent `audio.stop` or disconnected |
| `timeout` | Session idle timeout exceeded |
| `error` | Unrecoverable error |
| `server_shutdown` | Server is shutting down |

### `pong`

Heartbeat response. Sent **once per valid `ping`**; not used for server-initiated keepalive in Phase 2.

```json
{
  "type": "pong",
  "id": "msg-105",
  "session_id": "session-uuid",
  "timestamp": "2026-09-19T03:30:15.000Z",
  "payload": {}
}
```

| Rule | Requirement |
|------|-------------|
| `session_id` | Same session as the connection and the triggering `ping` |
| `id` | New UUID generated by the server (does not copy the client `ping` `id`) |
| `payload` | Empty object `{}` |
| Timing | Sent before processing subsequent client messages from the same connection |

### `buffer.overflow`

Audio buffer overflow warning.

```json
{
  "type": "buffer.overflow",
  "id": "msg-106",
  "session_id": "session-uuid",
  "timestamp": "2026-09-19T03:25:05.000Z",
  "payload": {
    "dropped_frames": 15
  }
}
```

## Heartbeat

Application-level liveness on the WebSocket connection. Transport-level WebSocket ping frames are not used in Phase 2.

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Client `ping` interval | 15 s | **SHOULD** send `ping` when connected and not streaming audio |
| Server idle timeout | 45 s | Close connection if no liveness activity (see below) |
| `pong` latency | Immediate | Server responds to each valid `ping` before handling later messages |

Server configuration: `HEARTBEAT_IDLE_TIMEOUT_S` (default `45`). Tests may use a lower value.

### Liveness activity

The server resets an **idle timer** on each inbound WebSocket message that is successfully received:

| Message | Resets idle timer |
|---------|-------------------|
| Valid JSON control message (`audio.start`, `audio.stop`, `ping`, …) | Yes |
| Valid binary audio frame (`audio.chunk`) | Yes |
| Invalid JSON | Yes (message was received; server may reply with `INVALID_MESSAGE`) |
| Invalid binary frame | Yes |

While the client is streaming audio, frequent `audio.chunk` frames keep the session alive without `ping`. When the client is connected but **not** streaming, it **MUST** send `ping` at least every 15 seconds to stay within the 45 second idle budget (three missed intervals).

### Server behavior (P2-001)

1. After `session.started`, start the idle timer (45 s unless configured otherwise).
2. On each inbound message, reset the idle timer.
3. On valid `ping`, send `pong` then continue processing.
4. If the idle timer expires: emit `session.ended` with `reason: "timeout"`, then close the WebSocket (normal closure). Clients may reconnect per [Error Handling](error-handling.md).

### Client behavior (reference)

| State | Behavior |
|-------|----------|
| Connected, not streaming | Send `ping` every 15 s |
| Streaming audio | `audio.chunk` satisfies liveness; `ping` is optional |
| After `audio.stop` | Resume 15 s `ping` until disconnect or new `audio.start` |

Desktop and CLI clients implement periodic `ping` in later phases; the server must not require `ping` during active audio streaming.

## Reconnection

See [Error Handling](error-handling.md) for full reconnection protocol.

| Parameter | Value |
|-----------|-------|
| Max reconnect attempts | 5 |
| Initial backoff | 1 second |
| Max backoff | 8 seconds |
| Reconnect window | 30 seconds (server retains session) |

On reconnect:
1. Client opens new WebSocket to `/v1/realtime`
2. Server sends `session.started` with new session ID
3. Client sends `session.resume` with previous session ID
4. If within reconnect window, server restores session; otherwise, new session

## Ordering Guarantees

| Data | Guarantee |
|------|-----------|
| Audio frames | Processed in `seq_num` order; out-of-order frames buffered for 100 ms then dropped |
| Partial transcripts | Ordered by `sequence` within a `segment_id` |
| Final transcripts | Ordered by segment creation time |
| Control messages | Processed in receive order |

## Authentication (Production)

When `JWT_AUTH_REQUIRED=true` on the realtime backend (staging EKS after [P6-005](../roadmap/dev-step-p6-005-api-gateway-auth.md)):

1. Client obtains a JWT from the API Gateway HTTP endpoint `POST /v1/auth/token` with header `x-api-key` (see [infra/apigateway/README.md](../../infra/apigateway/README.md)).
2. Client connects to `wss://<host>/v1/realtime` with either:
   - `Authorization: Bearer <access_token>` (tools and clients that support WebSocket headers), or
   - Query parameter `access_token=<access_token>` (Voragon desktop / browser WebSocket API).
3. Server validates HS256 JWT (`aud`: `voragon-realtime`, required `exp` and `sub`) **before** `session.started`. Invalid or missing tokens close the socket with code **4401**.

Local development and default EKS manifests do **not** require authentication (`JWT_AUTH_REQUIRED` defaults to false).

## Versioning

| Version | Status | Changes |
|---------|--------|---------|
| v1 | Current (documented) | Initial protocol |

Clients should connect to `/v1/realtime`. When v2 is introduced, v1 remains available for a deprecation period.

## Related Documents

- [Transcription API](transcription.md)
- [Error Handling](error-handling.md)
- [Realtime Audio Pipeline](../architecture/realtime-audio.md)
- [Backend Architecture](../architecture/backend.md)
