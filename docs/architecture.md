# VVLIVE Architecture

## System Overview

```
Camera → Encoder → Pi (MPTCP Client) → Verizon + AT&T → VPS → OBS → Twitch
                                              ↓
                                       Dashboard (React)
```

## Components

### Raspberry Pi
- MPTCP client
- Encoder control
- Network monitoring

### Cloud VPS
- MPTCP server
- Backend API (FastAPI)
- OBS integration
- Dashboard hosting

### Backend Services
- State machine (quality control)
- Encoder controller
- Health monitoring
- Alert system
- IRLToolkit integrations (v1.2.0)

### Frontend
- React dashboard
- Real-time WebSocket updates
- Quality controls

## Data Flow

1. Camera → Encoder (HDMI/SDI)
2. Encoder → Pi (RTMP/SRT over Ethernet)
3. Pi → VPS (MPTCP over dual cellular)
4. VPS → OBS (local SRT/RTMP)
5. OBS → Streaming platform (RTMP)

## State Machine

Quality states (LOCKED):
- HIGH: 1080p30 @ 4.5 Mbps
- MEDIUM: 720p30 @ 2.5 Mbps
- LOW: 480p24 @ 1.2 Mbps
- VERY_LOW: 360p24 @ 600 Kbps

Transitions based on:
- Bandwidth
- Packet loss
- RTT (latency)

See `state_machine.py` for implementation.

---

## IRLToolkit Integration Architecture (v1.2.0)

### Overview

VVLIVE v1.2.0 integrates optional components from the IRLToolkit GitHub organization. All integrations follow these principles:

- **Opt-in by default** - All features disabled unless explicitly enabled
- **Non-breaking** - Existing functionality unchanged
- **Modular** - Components operate independently
- **Graceful degradation** - Failures don't affect core system

### Enhanced Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           VVLIVE SYSTEM (v1.2.0)                         │
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
│     │  (default) │   │  [IRLTkit]  │   │   SRT     │  │                 │
│     └────────────┘   └─────────────┘   └───────────┘  │                 │
│                              │                         │                 │
│                              ▼                         ▼                 │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                     VVLIVE Backend (FastAPI)                       │  │
│  │                                                                     │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐│  │
│  │  │   State     │  │   Metrics   │  │      OBS Integration        ││  │
│  │  │  Machine    │◀─│ Aggregator  │  │  ┌─────────┐  ┌───────────┐ ││  │
│  │  └─────────────┘  └─────────────┘  │  │ Direct  │  │   HTTP    │ ││  │
│  │         │                ▲         │  │ (WS)    │  │ [IRLTkit] │ ││  │
│  │         │                │         │  └────┬────┘  └─────┬─────┘ ││  │
│  │         │         ┌──────┴──────┐  └───────┼─────────────┼───────┘│  │
│  │         │         │   SRTLA     │          │             │        │  │
│  │         │         │  Adapter    │          ▼             ▼        │  │
│  │         │         │  [IRLTkit]  │     ┌─────────────────────┐     │  │
│  │         │         └─────────────┘     │      OBS Studio      │     │  │
│  │         ▼                             └─────────────────────┘     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                              │                                           │
│                              ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    nginx-rtmp-auth [IRLTkit]                       │  │
│  │                  (Sidecar Authentication)                          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### IRLToolkit Components

#### 1. OBS HTTP Bridge (`obs_http_bridge.py`)

**Purpose:** HTTP-based OBS control for external integrations

**Architecture:**
- HTTP client that talks to standalone obs-websocket-http service
- Decouples OBS control from VVLIVE backend
- Enables external tools (Stream Deck, bots) to control OBS

**Data Flow:**
```
External Tool → HTTP → OBS HTTP Bridge Client → obs-websocket-http service → OBS
                       (VVLIVE)                 (Standalone)
```

**Feature Flag:** `FEATURE_OBS_HTTP_BRIDGE`

#### 2. SRTLA Metrics Adapter (`srtla_adapter.py`)

**Purpose:** Alternative bonded transport metrics via SRT link aggregation

**Architecture:**
- Reads metrics from SRTLA receiver
- Normalizes to VVLIVE's `NetworkMetrics` format
- Feeds into existing state machine without changes

**Data Flow:**
```
SRTLA Receiver → Adapter → NetworkMetrics → State Machine
```

**Metrics Sources:**
- `socket` - Direct socket to srtla_rec (placeholder)
- `file` - Stats file at `/tmp/srtla_stats_{port}.json`
- `api` - HTTP endpoint for stats

**Feature Flag:** `FEATURE_SRTLA_TRANSPORT`

#### 3. RTMP Auth Monitor (`rtmp_auth_monitor.py`)

**Purpose:** Monitor nginx-rtmp-auth service health

**Architecture:**
- Sidecar monitoring only - authentication at nginx level
- Health check endpoint for auth service
- Configuration examples for nginx integration

**Data Flow:**
```
Encoder → nginx-rtmp → nginx-rtmp-auth → Allow/Deny
                              ↓
                      RTMP Auth Monitor (health check only)
```

**Feature Flag:** `FEATURE_RTMP_AUTH`

#### 4. OBS WebSocket Adapter (`obs_websocket_adapter.py`)

**Purpose:** Abstraction layer for OBS WebSocket libraries

**Architecture:**
- Factory function creates appropriate adapter
- Supports native implementation or simpleobsws
- Runtime library selection via configuration

**Libraries:**
- `obs-websocket-py` (default) - Current implementation
- `simpleobsws` - IRLToolkit async library

**Feature Flag:** `OBS_LIBRARY` setting

### Module Dependencies

```
config.py
    ↓
obs_http_bridge.py ← httpx
srtla_adapter.py   ← httpx, models.py
rtmp_auth_monitor.py ← httpx
obs_websocket_adapter.py ← simpleobsws (optional)
    ↓
main.py (FastAPI lifespan initialization)
```

### API Endpoints (IRLToolkit)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/obs-http/status` | GET | OBS HTTP Bridge status |
| `/api/obs-http/health` | GET | Bridge health check |
| `/api/obs-http/scene` | POST | Switch scene via HTTP |
| `/api/obs-http/scene` | GET | Get current scene |
| `/api/obs/library-info` | GET | OBS library configuration |
| `/api/srtla/status` | GET | SRTLA adapter status |
| `/api/srtla/metrics` | GET | Normalized SRTLA metrics |
| `/api/srtla/raw` | GET | Raw SRTLA statistics |
| `/api/rtmp-auth/status` | GET | RTMP auth monitor status |
| `/api/rtmp-auth/health` | GET | Auth service health |
| `/api/rtmp-auth/config-example/nginx` | GET | nginx config example |
| `/api/rtmp-auth/config-example/auth` | GET | auth.json example |

### Configuration

All IRLToolkit features in `config.py`:

```python
# OBS HTTP Bridge
feature_obs_http_bridge: bool = False
obs_http_bridge_host: str = "localhost"
obs_http_bridge_port: int = 5001
obs_http_bridge_auth_key: Optional[str] = None
obs_http_bridge_timeout: int = 5

# SRTLA Transport
feature_srtla_transport: bool = False
srtla_metrics_source: str = "socket"
srtla_stats_endpoint: str = ""
srtla_receiver_port: int = 9000
transport_mode: str = "mptcp"

# RTMP Authentication
feature_rtmp_auth: bool = False
rtmp_auth_service_url: str = ""

# OBS Library Selection
obs_library: str = "obs-websocket-py"
```

### Backward Compatibility

All IRLToolkit integrations maintain backward compatibility:

1. **Feature Flags** - All disabled by default
2. **API Unchanged** - Existing endpoints unmodified
3. **State Machine** - Core logic untouched
4. **Graceful Failures** - Components fail independently
5. **No Required Dependencies** - Works without IRLToolkit services
