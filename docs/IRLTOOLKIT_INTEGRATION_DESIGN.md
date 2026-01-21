# IRLToolkit → VVLIVE Integration Analysis & Design Document

**Document Type:** Design Analysis (No Code)
**Status:** Ready for Review
**Date:** 2026-01-21

---

## Executive Summary

This document analyzes the IRLToolkit GitHub organization repositories and designs integration strategies for VVLIVE, a bonded cellular IRL streaming system. After thorough analysis, **four repositories** present strong integration candidates:

| Repository | Integration Value | Priority |
|------------|-------------------|----------|
| **simpleobsws** | Replace current obs-websocket-py with cleaner async interface | Medium |
| **obs-websocket-http** | Add HTTP control layer for external integrations | High |
| **srtla** | Add bonded SRT transport as alternative/complement to MPTCP | High |
| **nginx-rtmp-auth** | Secure RTMP ingest with stream key validation | Medium |

Two repositories are **recommended for exclusion**: `3d` (unrelated hardware models) and `vlc-srt-urlparam-mod` (archived, unmaintained).

The remaining repositories (`neko-community`, `obsws-rproxy-client`, `srt` fork) offer **future potential** but require significant infrastructure investment beyond VVLIVE's current scope.

---

## Section 1: IRLToolkit Repository Summaries

### 1.1 simpleobsws (Python — OBS WebSocket Library)

**Problem Solved**: Provides a simplified, async Python interface for OBS Studio control via obs-websocket protocol.

**Architecture**:
- Pure Python, asynchronous design using `asyncio`
- Direct JSON response handling (no abstraction layers)
- Protocol support: obs-websocket 5.0.0+ (matches VVLIVE's current requirement)

**Inputs/Outputs**:
- **Input**: WebSocket connection parameters (host, port, password)
- **Output**: Raw JSON responses from OBS requests

**Dependencies**:
- Python 3.7+
- `websockets` library (standard async WebSocket client)

**Deployment**: pip-installable library (`pip install simpleobsws`)

**Configuration**: Connection established via constructor parameters or explicit connect calls

**Trigger Points**:
- `connect()` — Establish authenticated WebSocket
- `call(request_type, request_data)` — Send request, await response
- `emit(request_type, request_data)` — Fire-and-forget request

---

### 1.2 obs-websocket-http (Python — HTTP-to-WebSocket Bridge)

**Problem Solved**: Creates RESTful HTTP endpoints that proxy to OBS WebSocket, enabling integration with systems that cannot maintain WebSocket connections.

**Architecture**:
- Python HTTP server (likely Flask/FastAPI-based)
- Maintains persistent WebSocket connection to OBS
- Translates HTTP requests to WebSocket calls

**Inputs/Outputs**:
- **Input**: HTTP requests to `/emit/{requestType}` or `/call/{requestType}`
- **Output**: JSON responses (fire-and-forget acknowledgment or full OBS response)

**Dependencies**:
- Python 3.8+
- Requires `simpleobsws` or similar WebSocket client
- Web framework for HTTP serving

**Deployment**: Standalone service or Docker container

**Configuration** (via `config.ini`):
- `[http]`: address, port, authentication_key, cors_domains
- `[obsws]`: host, port, password

**Trigger Points**:
- HTTP GET/POST to `/emit/{requestType}` — No response wait
- HTTP GET/POST to `/call/{requestType}` — Waits for OBS response

---

### 1.3 nginx-rtmp-auth (Python — RTMP Authentication)

**Problem Solved**: Validates incoming RTMP stream connections against configured stream keys before allowing publish.

**Architecture**:
- Lightweight Python HTTP callback server
- Integrates with nginx-rtmp-module's `on_publish` directive
- Validates credentials against JSON configuration file

**Inputs/Outputs**:
- **Input**: nginx-rtmp callback with stream name/key
- **Output**: HTTP 200 (allow) or 403 (deny)

**Dependencies**:
- Python 3.x
- nginx with rtmp-module
- Flask or similar micro-framework

**Deployment**: Runs as sidecar service alongside nginx

**Configuration**:
- `config.ini` — Server settings (host, port)
- `authentication.json` — Application names and valid stream keys

**Trigger Points**:
- nginx `on_publish` callback triggers validation
- Returns immediately; no persistent state

---

### 1.4 srtla (C — SRT Link Aggregation Proxy)

**Problem Solved**: Bonds multiple network connections (e.g., cellular modems) for SRT transport, providing redundancy and capacity aggregation.

**Architecture**:
- Two binaries: `srtla_send` (encoder side) and `srtla_rec` (server side)
- Tracks packets-in-flight per link with dynamic window sizing
- Two-phase connection registration (SRTLA_REG1/REG2 protocol)
- Distributes traffic based on real-time network conditions

**Inputs/Outputs**:
- **Input (Sender)**: SRT stream + IP address file listing network interfaces
- **Input (Receiver)**: Bonded packets + SRT configuration
- **Output**: Unified SRT stream with improved reliability

**Dependencies**:
- Linux (kernel with multiple network interfaces)
- Patched BELABOX SRT library (receiver side)
- Source routing configuration for multi-interface bonding

**Deployment**: Compiled binaries run on both encoder (sender) and server (receiver) sides

**Configuration**:
- Sender: IP list file, source routing rules
- Receiver: `lossmaxttl` (10-50), `latency` (ms for retransmission)

**Trigger Points**:
- Connection establishment via registration protocol
- Continuous packet distribution and acknowledgment tracking
- Adaptive metrics: `SRTO_SNDDATA`, RTT available for ABR decisions

---

### 1.5 obsws-rproxy-client (C++/Python — Reverse Proxy for OBS WebSocket)

**Problem Solved**: Enables remote OBS control without port forwarding by connecting through a relay server.

**Architecture**:
- Qt-based desktop client (C++)
- Python server component for relay
- Client initiates outbound connection to relay; external clients connect to relay

**Inputs/Outputs**:
- **Input**: Local OBS WebSocket credentials + relay server address
- **Output**: Proxied WebSocket connection accessible remotely

**Dependencies**:
- Qt framework (C++)
- Python server runtime
- CMake for build

**Deployment**: Client app on OBS machine; server on accessible host

**Configuration**: Relay server address, authentication credentials

**Trigger Points**:
- Client startup establishes tunnel
- Remote requests routed through relay to local OBS

---

### 1.6 neko-community (Go/TypeScript — Virtual Browser Environment)

**Problem Solved**: Self-hosted virtual browser accessible via WebRTC, enabling collaborative viewing and remote desktop scenarios.

**Architecture**:
- Go backend with WebRTC streaming
- Vue.js/TypeScript frontend
- Docker-based containerization
- X server integration for Linux desktop

**Inputs/Outputs**:
- **Input**: User connections via web browser
- **Output**: WebRTC video stream of virtual desktop; control events

**Dependencies**:
- Docker/Docker Compose
- Linux host with X11 support
- WebRTC-compatible browsers

**Deployment**: Docker container with exposed ports

**Configuration**: Environment variables for browser type, resolution, features

**Trigger Points**:
- Container startup initializes virtual desktop
- WebRTC negotiation on client connection
- Optional RTMP broadcast output

---

### 1.7 srt (C++ — SRT Protocol Fork)

**Problem Solved**: Fork of Haivision's Secure Reliable Transport protocol.

**Architecture**: Standard SRT library with potential IRL-specific patches

**Status**: Appears to be a deployment fork without significant modifications. May exist for dependency pinning with srtla.

---

### 1.8 3d (Various — 3D Printable Parts) — **EXCLUDE**

**Problem Solved**: Hardware mounting solutions for streaming equipment.

**Relevance to VVLIVE**: None. Software-only integration scope.

---

### 1.9 vlc-srt-urlparam-mod (C — VLC SRT Module) — **EXCLUDE**

**Problem Solved**: Modified VLC streaming module.

**Status**: Archived, unmaintained. No active development.

---

## Section 2: Relevance Evaluation to VVLIVE

### 2.1 Current VVLIVE Architecture Summary

VVLIVE is a **bonded cellular IRL streaming system** with:

| Layer | Current Implementation |
|-------|------------------------|
| **Transport** | MPTCP (Multipath TCP) bonding dual cellular connections |
| **Quality Control** | Locked adaptive state machine (6 states, deterministic transitions) |
| **OBS Integration** | `obs-websocket-py 1.0` for scene switching (opt-in) |
| **Ingest Monitoring** | HTTP polling of nginx-rtmp/SRT/Node-Media-Server stats |
| **API Layer** | FastAPI REST + WebSocket endpoints |
| **Frontend** | React dashboard with Tailwind CSS |

### 2.2 Gap Analysis & Enhancement Opportunities

| VVLIVE Need | Current State | IRLToolkit Solution |
|-------------|---------------|---------------------|
| OBS control library | obs-websocket-py (works but basic) | **simpleobsws** — cleaner async, same protocol |
| External OBS HTTP access | Not available | **obs-websocket-http** — REST endpoints for OBS |
| RTMP ingest security | No authentication | **nginx-rtmp-auth** — stream key validation |
| Alternative transport | MPTCP only | **srtla** — bonded SRT as fallback/alternative |
| Remote OBS access | Requires port forwarding | **obsws-rproxy-client** — future consideration |
| Virtual browser | Not applicable | **neko** — future consideration for overlays |

### 2.3 Tool-by-Tool Relevance Assessment

#### **simpleobsws — MEDIUM PRIORITY**

**Fit**: Direct replacement for `obs-websocket-py` in `obs_controller.py`

**Benefits**:
- Maintained by IRLToolkit (IRL streaming focus)
- Cleaner async interface with raw JSON access
- Same protocol version (5.0.0+)
- Lighter dependency footprint

**Trade-off**: Current implementation works; migration adds risk without major feature gain.

**Recommendation**: Consider for future refactoring, not urgent.

---

#### **obs-websocket-http — HIGH PRIORITY**

**Fit**: New microservice enabling HTTP-based OBS control

**Benefits**:
- Enables external integrations (webhooks, automation scripts, mobile apps)
- Decouples OBS control from VVLIVE backend
- Supports CORS for browser-based control panels
- Provides fire-and-forget (`/emit`) and request-response (`/call`) patterns

**VVLIVE Enhancement**:
- Dashboard could call OBS directly via HTTP
- External services (Discord bots, Stream Deck) can trigger scene changes
- Reduces coupling between VVLIVE backend and OBS

**Recommendation**: **Integrate as optional companion service.**

---

#### **nginx-rtmp-auth — MEDIUM PRIORITY**

**Fit**: Sidecar service for RTMP ingest security

**Benefits**:
- Prevents unauthorized stream hijacking
- Simple stream key management
- Works with existing nginx-rtmp infrastructure

**VVLIVE Enhancement**:
- Secures the ingest path from encoder to server
- Validates stream keys before accepting publish
- Protects against malicious or accidental overwrites

**Recommendation**: **Integrate for production deployments with public ingest.**

---

#### **srtla — HIGH PRIORITY**

**Fit**: Alternative/complementary transport layer to MPTCP

**Benefits**:
- Protocol-level bonding (vs. kernel-level MPTCP)
- Designed specifically for IRL streaming use cases
- Provides SRT metrics (`SRTO_SNDDATA`, RTT) for ABR decisions
- Works with standard encoders supporting SRT output

**VVLIVE Enhancement**:
- Dual transport strategy: MPTCP for TCP streams, SRTLA for SRT streams
- SRTLA metrics can feed into the quality state machine
- Fallback transport if MPTCP unavailable or underperforming

**Considerations**:
- Requires patched SRT library on receiver
- Different deployment topology than MPTCP
- AGPL-3.0 license requires compliance review

**Recommendation**: **Integrate as alternative transport module.**

---

#### **obsws-rproxy-client — LOW PRIORITY (FUTURE)**

**Fit**: Enables remote OBS control without port forwarding

**Benefits**:
- Useful for distributed setups (OBS on home network, server in cloud)
- Eliminates NAT traversal complexity

**Trade-off**: Requires relay server infrastructure; adds latency and complexity.

**Recommendation**: Document as future enhancement; not required for MVP.

---

#### **neko-community — LOW PRIORITY (FUTURE)**

**Fit**: Virtual browser for overlays, alerts, or isolated browsing

**Benefits**:
- Could display web-based overlays without local browser
- Isolated environment for sensitive content
- RTMP output capability

**Trade-off**: Significant infrastructure (Docker, WebRTC); tangential to core streaming.

**Recommendation**: Note for roadmap; not part of initial integration.

---

#### **srt (fork) — NO ACTION**

**Assessment**: Deployment fork without clear modifications.

**Recommendation**: Use if needed for SRTLA dependency; otherwise prefer upstream Haivision.

---

## Section 3: High-Level Integration Strategy

### 3.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           VVLIVE SYSTEM (Enhanced)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐ │
│  │   Encoder    │────▶│   Transport  │────▶│      Ingest Server       │ │
│  │   (URay)     │     │    Layer     │     │    (nginx-rtmp/SRT)      │ │
│  └──────────────┘     └──────────────┘     └──────────────────────────┘ │
│                              │                         │                 │
│            ┌─────────────────┼─────────────────┐       │                 │
│            ▼                 ▼                 ▼       │                 │
│     ┌────────────┐   ┌─────────────┐   ┌───────────┐  │                 │
│     │   MPTCP    │   │   SRTLA     │   │   Direct  │  │                 │
│     │  (current) │   │  [NEW]      │   │   SRT     │  │                 │
│     └────────────┘   └─────────────┘   └───────────┘  │                 │
│                              │                         │                 │
│                              ▼                         ▼                 │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                     VVLIVE Backend (FastAPI)                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐│  │
│  │  │   State     │  │   Metrics   │  │      OBS Integration        ││  │
│  │  │  Machine    │◀─│ Aggregator  │  │  ┌─────────┐  ┌───────────┐ ││  │
│  │  └─────────────┘  └─────────────┘  │  │ Direct  │  │   HTTP    │ ││  │
│  │         │                ▲         │  │ (WS)    │  │   [NEW]   │ ││  │
│  │         │                │         │  └────┬────┘  └─────┬─────┘ ││  │
│  │         │         ┌──────┴──────┐  └───────┼─────────────┼───────┘│  │
│  │         │         │   Ingest    │          │             │        │  │
│  │         │         │  Monitor    │          ▼             ▼        │  │
│  │         │         └──────┬──────┘     ┌─────────────────────┐     │  │
│  │         ▼                ▼            │      OBS Studio      │     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                              │                                           │
│                              ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    nginx-rtmp-auth [NEW]                           │  │
│  │                  (Sidecar Authentication)                          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 3.2 Integration Design: obs-websocket-http

#### **Integration Type**: Companion Microservice

#### **Placement in VVLIVE**:
- Runs as **separate service** alongside VVLIVE backend
- Can be deployed as Docker container or systemd service
- Communicates with same OBS instance as current `obs_controller.py`

#### **Interaction Model**:

```
┌─────────────────┐        ┌──────────────────────┐        ┌────────────┐
│  VVLIVE Backend │───────▶│  obs-websocket-http  │───────▶│    OBS     │
│                 │  HTTP  │    (Port 5001)       │   WS   │  (Port     │
│                 │        │                      │        │   4455)    │
└─────────────────┘        └──────────────────────┘        └────────────┘
         │                           ▲
         │                           │
         ▼                           │
┌─────────────────┐                  │
│    External     │──────────────────┘
│   Integrations  │       HTTP
│ (Stream Deck,   │
│  Discord Bots)  │
└─────────────────┘
```

#### **Inputs/Outputs**:
- **Input**: HTTP requests (scene name, source settings, etc.)
- **Output**: JSON responses with OBS state or acknowledgment

#### **Communication**:
- VVLIVE backend can optionally route OBS commands through HTTP service
- External tools connect directly to HTTP service
- No changes required to existing WebSocket-based `obs_controller.py`

#### **Configuration Flags**:

```
# New feature flags in .env
FEATURE_OBS_HTTP_BRIDGE=false          # Enable HTTP bridge service
OBS_HTTP_BRIDGE_HOST=localhost         # HTTP bridge address
OBS_HTTP_BRIDGE_PORT=5001              # HTTP bridge port
OBS_HTTP_BRIDGE_AUTH_KEY=              # Optional authentication
```

#### **Compatibility Approach**:
- **Existing behavior preserved**: Direct WebSocket control continues to work
- **Additive only**: HTTP bridge is purely optional companion
- **No API changes**: VVLIVE `/api/obs/*` endpoints unchanged
- **Gradual adoption**: External integrations can use HTTP bridge while VVLIVE uses WebSocket

---

### 3.3 Integration Design: srtla

#### **Integration Type**: Alternative Transport Module

#### **Placement in VVLIVE**:
- **Sender component** (`srtla_send`) on Raspberry Pi with encoder
- **Receiver component** (`srtla_rec`) on cloud VPS
- New **metrics adapter** in VVLIVE backend to read SRTLA stats

#### **Interaction Model**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ENCODER SIDE (Raspberry Pi)                     │
│  ┌──────────────┐     ┌─────────────────┐     ┌───────────────────────┐ │
│  │    URay      │────▶│   srtla_send    │────▶│   Cellular Modems     │ │
│  │   Encoder    │ SRT │   (bonding)     │     │   (Verizon + AT&T)    │ │
│  └──────────────┘     └─────────────────┘     └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ (Multiple paths)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          SERVER SIDE (Cloud VPS)                         │
│  ┌───────────────────────┐     ┌──────────────────────────────────────┐ │
│  │      srtla_rec        │────▶│         VVLIVE Backend               │ │
│  │   (unified stream)    │ SRT │  ┌──────────────────────────────┐   │ │
│  │                       │     │  │   srtla_metrics_adapter.py   │   │ │
│  │   Exposes:            │     │  │   [NEW MODULE]               │   │ │
│  │   - Packet stats      │────▶│  │   - Reads SRTLA stats        │   │ │
│  │   - Per-link RTT      │     │  │   - Normalizes to VVLIVE     │   │ │
│  │   - Loss metrics      │     │  │     NetworkMetrics format    │   │ │
│  └───────────────────────┘     │  └──────────────────────────────┘   │ │
│                                │              │                       │ │
│                                │              ▼                       │ │
│                                │    ┌────────────────────┐           │ │
│                                │    │   State Machine    │           │ │
│                                │    │  (quality control) │           │ │
│                                │    └────────────────────┘           │ │
│                                └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

#### **Inputs/Outputs**:
- **Input (sender)**: SRT stream from encoder, IP list of interfaces
- **Input (receiver)**: Bonded packets from sender
- **Output (receiver)**: Unified SRT stream + metrics for VVLIVE
- **Output (VVLIVE)**: NetworkMetrics populated from SRTLA stats

#### **Communication**:
- New `srtla_metrics_adapter.py` module reads SRTLA receiver stats
- Adapter normalizes metrics to existing `NetworkMetrics` format
- State machine consumes metrics identically to MPTCP source
- No changes to state machine logic required

#### **Configuration Flags**:

```
# New feature flags in .env
FEATURE_SRTLA_TRANSPORT=false          # Enable SRTLA transport
SRTLA_METRICS_SOURCE=socket            # socket | file | api
SRTLA_STATS_ENDPOINT=                  # If API-based metrics
SRTLA_RECEIVER_PORT=9000               # SRTLA receiver port

# Transport selection
TRANSPORT_MODE=mptcp                   # mptcp | srtla | hybrid
```

#### **Compatibility Approach**:
- **Parallel operation**: SRTLA can run alongside MPTCP
- **Transport abstraction**: New transport adapter interface
- **Metric normalization**: Both transports produce identical `NetworkMetrics`
- **Gradual migration**: Start with SRTLA as backup, optionally make primary

---

### 3.4 Integration Design: nginx-rtmp-auth

#### **Integration Type**: Sidecar Authentication Service

#### **Placement in VVLIVE**:
- Runs as **separate process** on ingest server
- nginx-rtmp calls auth service on `on_publish` events
- No direct integration with VVLIVE backend required

#### **Interaction Model**:

```
┌──────────────┐         ┌───────────────────┐         ┌──────────────────┐
│   Encoder    │──RTMP──▶│    nginx-rtmp     │──HTTP──▶│ nginx-rtmp-auth  │
│              │         │                   │         │   (Port 8080)    │
│              │         │  on_publish:      │         │                  │
│              │         │  - calls auth     │◀──200───│  Validates key   │
│              │         │  - waits for OK   │  or 403 │  from JSON config│
└──────────────┘         └───────────────────┘         └──────────────────┘
                                  │
                                  │ (if authenticated)
                                  ▼
                         ┌───────────────────┐
                         │   VVLIVE ingest   │
                         │   monitoring      │
                         └───────────────────┘
```

#### **Inputs/Outputs**:
- **Input**: nginx `on_publish` callback with stream name
- **Output**: HTTP 200 (allow) or 403 (deny)

#### **Communication**:
- nginx-rtmp module handles callback automatically
- No direct VVLIVE backend communication needed
- Authentication happens at nginx level, transparent to VVLIVE

#### **Configuration**:

nginx.conf addition:
```nginx
application live {
    live on;
    on_publish http://127.0.0.1:8080/auth;
    # ... existing VVLIVE config
}
```

authentication.json:
```json
{
  "live": {
    "allowed_keys": ["secret-stream-key-1", "backup-key-2"]
  }
}
```

#### **Configuration Flags** (for VVLIVE awareness):

```
# New feature flags in .env
FEATURE_RTMP_AUTH=false                # Document auth is enabled
RTMP_AUTH_SERVICE_URL=                 # Health check endpoint (optional)
```

#### **Compatibility Approach**:
- **Zero VVLIVE changes**: Auth happens at nginx layer
- **Transparent**: Authenticated streams appear identical to unauthenticated
- **Fail-safe**: If auth service down, nginx can be configured to deny all
- **No code changes**: Only nginx configuration updates

---

### 3.5 Integration Design: simpleobsws (Optional Refactor)

#### **Integration Type**: Library Replacement

#### **Placement in VVLIVE**:
- Replaces `obs-websocket-py` in `obs_controller.py`
- Same location, same functionality, different library

#### **Interaction Model**:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        obs_controller.py                              │
│                                                                       │
│  BEFORE:                          │  AFTER:                          │
│  ──────                           │  ─────                           │
│  from obswebsocket import        │  import simpleobsws              │
│      obsws, requests             │                                   │
│                                   │  self.ws = simpleobsws           │
│  self.ws = obsws(host, port,     │      .WebSocketClient(            │
│      password)                    │      url=f"ws://{host}:{port}",  │
│  self.ws.connect()                │      password=password)          │
│                                   │  await self.ws.connect()         │
│  self.ws.call(                    │                                   │
│      requests.SetCurrentScene(    │  await self.ws.call(             │
│          scene_name))             │      "SetCurrentProgramScene",   │
│                                   │      {"sceneName": scene_name})  │
└──────────────────────────────────────────────────────────────────────┘
```

#### **Inputs/Outputs**:
- Identical to current implementation
- Raw JSON responses instead of wrapper objects

#### **Configuration Flags**:

```
# New feature flags in .env
OBS_LIBRARY=obs-websocket-py         # obs-websocket-py | simpleobsws
```

#### **Compatibility Approach**:
- **Behavioral equivalent**: Same OBS operations, different library
- **Feature flag**: Allow runtime selection during transition
- **Gradual rollout**: Test simpleobsws while obs-websocket-py remains default

---

## Section 4: Risks, Conflicts, and Exclusions

### 4.1 Potential Breakages and Conflicts

#### **obs-websocket-http Integration Risks**

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Port conflicts** | Low | Configure non-conflicting port (5001 vs 8000) |
| **Dual control conflicts** | Medium | Document that simultaneous WebSocket + HTTP control may cause race conditions; recommend single source of truth |
| **Authentication mismatch** | Low | Ensure HTTP bridge and direct WebSocket use same OBS credentials |
| **CORS misconfiguration** | Low | Restrict CORS domains in production |

#### **srtla Integration Risks**

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Patched SRT library requirement** | High | Receiver requires BELABOX SRT fork; may conflict with system SRT |
| **AGPL-3.0 license** | High | If distributing VVLIVE binaries, must comply with AGPL copyleft |
| **Metric format differences** | Medium | Adapter must correctly translate SRTLA stats to NetworkMetrics |
| **Latency increase** | Medium | SRTLA adds reordering delay; may affect ultra-low-latency use cases |
| **Multi-interface routing** | Medium | Requires correct source routing; misconfiguration breaks bonding |
| **Encoder SRT support** | Low | URay encoder must support SRT output (verify capability) |

#### **nginx-rtmp-auth Integration Risks**

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Auth service failure** | High | If service crashes, all publishes blocked; add health checks, systemd restart |
| **Latency on publish** | Low | Auth callback adds milliseconds to stream start |
| **Key management** | Medium | Need secure process for updating/rotating stream keys |
| **nginx-rtmp version compatibility** | Low | Verify `on_publish` directive works with deployed nginx version |

#### **simpleobsws Migration Risks**

| Risk | Severity | Mitigation |
|------|----------|------------|
| **API differences** | Medium | Method signatures differ; requires obs_controller.py refactoring |
| **Error handling changes** | Medium | Exception types may differ; update try/catch blocks |
| **Testing coverage** | Medium | Existing tests assume obs-websocket-py responses |

---

### 4.2 API Mismatches

| Component | VVLIVE Expects | IRLToolkit Provides | Resolution |
|-----------|---------------|---------------------|------------|
| OBS scene switch | Method-based API | JSON request/response | Adapter wrapper |
| Network metrics | `NetworkMetrics` dataclass | SRTLA raw stats | Translation layer in adapter |
| Auth response | N/A (nginx handles) | HTTP 200/403 | No change needed |

---

### 4.3 Versioning Considerations

| Component | VVLIVE Version | IRLToolkit Version | Compatibility |
|-----------|----------------|-------------------|---------------|
| obs-websocket protocol | 5.0+ | 5.0+ | Compatible |
| Python | 3.11+ | 3.7+ (simpleobsws), 3.8+ (HTTP) | Compatible |
| SRT library | System default | BELABOX fork | Requires isolation |
| nginx-rtmp | Standard | Standard | Compatible |

---

### 4.4 Performance Considerations

| Integration | Performance Impact | Recommendation |
|-------------|-------------------|----------------|
| obs-websocket-http | +5-20ms latency for HTTP vs WebSocket | Acceptable for non-critical operations |
| srtla | +50-200ms latency from reordering buffer | Configure `lossmaxttl` appropriately |
| nginx-rtmp-auth | +1-5ms on publish initiation | Negligible; cache valid keys |
| simpleobsws | Similar to current library | No significant change |

---

### 4.5 Security Considerations

| Component | Security Concern | Mitigation |
|-----------|------------------|------------|
| obs-websocket-http | HTTP endpoint exposed | Enable authentication_key; restrict CORS |
| srtla | No built-in encryption | SRT passphrase encryption; firewall rules |
| nginx-rtmp-auth | Stream keys in JSON file | File permissions (600); secrets management |
| simpleobsws | Same as current | WebSocket password; OBS authentication |

---

### 4.6 Dependency Introduction

| Component | New Dependencies | OS/Runtime Requirements |
|-----------|------------------|-------------------------|
| obs-websocket-http | Flask/FastAPI (Python) | Python 3.8+ |
| srtla | BELABOX SRT library (C++) | Linux, build tools |
| nginx-rtmp-auth | Python, Flask | Python 3.x |
| simpleobsws | websockets library | Python 3.7+ |

---

### 4.7 Repositories to Exclude

| Repository | Reason for Exclusion |
|------------|---------------------|
| **3d** | Hardware/3D printing; no software relevance |
| **vlc-srt-urlparam-mod** | Archived; unmaintained; no active development |
| **neko / neko-community** | Significant infrastructure overhead; tangential to core streaming (future roadmap item) |
| **obsws-rproxy-client** | Requires relay server infrastructure; adds complexity for limited benefit (future roadmap item) |
| **srt (fork)** | No clear modifications; use only if required for SRTLA dependency |

---

## Section 5: Summary Integration Matrix

| Component | Type | Priority | Breaking Changes | New Dependencies | License |
|-----------|------|----------|------------------|------------------|---------|
| obs-websocket-http | Microservice | High | None | Python, Flask/FastAPI | MIT |
| srtla | Transport Module | High | Requires SRT fork | C, Linux toolchain | AGPL-3.0 |
| nginx-rtmp-auth | Sidecar | Medium | None (nginx config) | Python, Flask | MIT (assumed) |
| simpleobsws | Library Swap | Medium | Refactor obs_controller | websockets | MIT |

---

## Section 6: Conceptual Integration Phases

### Phase 1: HTTP OBS Control (Low Risk)
1. Deploy obs-websocket-http as companion service
2. Document HTTP endpoints for external integrations
3. Add optional routing from VVLIVE to HTTP bridge
4. No changes to existing VVLIVE code required

### Phase 2: RTMP Authentication (Low Risk)
1. Deploy nginx-rtmp-auth alongside existing nginx
2. Update nginx.conf with `on_publish` directive
3. Configure stream keys in authentication.json
4. Test publish flow end-to-end

### Phase 3: SRTLA Transport (Medium Risk)
1. Build and deploy SRTLA sender/receiver
2. Implement `srtla_metrics_adapter.py` in VVLIVE
3. Add transport selection configuration
4. Test parallel MPTCP + SRTLA operation
5. Validate state machine with SRTLA metrics

### Phase 4: OBS Library Migration (Low Risk, Optional)
1. Add simpleobsws to requirements.txt
2. Create abstraction layer in obs_controller.py
3. Feature flag for library selection
4. Gradual migration with testing

---

## Section 7: Final Recommendations

### Approved Integrations (Proceed to Implementation)

| # | Component | Integration Type | Effort Estimate |
|---|-----------|------------------|-----------------|
| 1 | **obs-websocket-http** | Companion microservice | Docker deployment + nginx proxy |
| 2 | **srtla** | Alternative transport module | New adapter + deployment scripts |
| 3 | **nginx-rtmp-auth** | Sidecar authentication | nginx config + service deployment |
| 4 | **simpleobsws** | Library refactor (optional) | Code migration in obs_controller.py |

### Deferred to Future Roadmap

| Component | Reason |
|-----------|--------|
| obsws-rproxy-client | Requires relay infrastructure; NAT traversal not critical for current deployment model |
| neko-community | Interesting for overlay/isolation use cases; significant Docker/WebRTC investment |

### Excluded (No Integration)

| Component | Reason |
|-----------|--------|
| 3d | Not software; hardware models |
| vlc-srt-urlparam-mod | Archived; no maintenance |
| srt (fork) | No clear differentiation; use upstream or only for SRTLA dependency |

---

## Conclusion

This design document provides a comprehensive analysis of the IRLToolkit GitHub organization and its potential integration with VVLIVE. Four components have been identified as strong candidates for integration:

1. **obs-websocket-http** — Enables HTTP-based OBS control for external integrations
2. **srtla** — Provides bonded SRT transport as an alternative to MPTCP
3. **nginx-rtmp-auth** — Adds stream key authentication for ingest security
4. **simpleobsws** — Offers a cleaner async OBS WebSocket library (optional migration)

All proposed integrations follow VVLIVE's established patterns:
- **Opt-in via feature flags**
- **Non-breaking to existing functionality**
- **Modular deployment** (microservices, sidecars, adapters)
- **Configurable and testable independently**

---

**This design is ready for review before any implementation begins.**

No code has been written. No configurations have been modified. All proposals are conceptual and require explicit approval before proceeding to implementation phase.
