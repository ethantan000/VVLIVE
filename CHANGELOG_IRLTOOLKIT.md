# VVLIVE IRLToolkit Integration Changelog

## Version 1.2.0 - IRLToolkit Integration

**Release Date:** 2026-01-21

### Summary

This release integrates optional components from the IRLToolkit GitHub organization to enhance VVLIVE's streaming capabilities. All features are **opt-in** and **disabled by default**, ensuring complete backward compatibility with existing deployments.

---

### Added

#### OBS HTTP Bridge Integration
- **New Module:** `backend/app/obs_http_bridge.py`
- **Purpose:** HTTP-based OBS control via obs-websocket-http companion service
- **Features:**
  - Scene switching via HTTP endpoints
  - Health checking of HTTP bridge service
  - Fire-and-forget (`emit`) and request-response (`call`) patterns
  - Optional authentication key support
- **Configuration:**
  - `FEATURE_OBS_HTTP_BRIDGE` - Enable/disable (default: false)
  - `OBS_HTTP_BRIDGE_HOST` - Service host (default: localhost)
  - `OBS_HTTP_BRIDGE_PORT` - Service port (default: 5001)
  - `OBS_HTTP_BRIDGE_AUTH_KEY` - Optional auth key
  - `OBS_HTTP_BRIDGE_TIMEOUT` - Request timeout (default: 5s)
- **API Endpoints:**
  - `GET /api/obs-http/status`
  - `GET /api/obs-http/health`
  - `POST /api/obs-http/scene`
  - `GET /api/obs-http/scene`

#### SRTLA Metrics Adapter
- **New Module:** `backend/app/srtla_adapter.py`
- **Purpose:** Alternative bonded transport metrics via SRT link aggregation
- **Features:**
  - Reads metrics from SRTLA receiver
  - Normalizes to VVLIVE NetworkMetrics format
  - Supports multiple metrics sources (socket, file, API)
  - Background polling with configurable interval
- **Configuration:**
  - `FEATURE_SRTLA_TRANSPORT` - Enable/disable (default: false)
  - `SRTLA_METRICS_SOURCE` - socket | file | api (default: socket)
  - `SRTLA_STATS_ENDPOINT` - API endpoint for stats
  - `SRTLA_RECEIVER_PORT` - Receiver port (default: 9000)
  - `TRANSPORT_MODE` - mptcp | srtla | hybrid (default: mptcp)
- **API Endpoints:**
  - `GET /api/srtla/status`
  - `GET /api/srtla/metrics`
  - `GET /api/srtla/raw`

#### RTMP Authentication Monitor
- **New Module:** `backend/app/rtmp_auth_monitor.py`
- **Purpose:** Monitor nginx-rtmp-auth service health
- **Features:**
  - Health check endpoint for auth service
  - Example configuration generation
  - nginx-rtmp configuration examples
- **Configuration:**
  - `FEATURE_RTMP_AUTH` - Enable/disable (default: false)
  - `RTMP_AUTH_SERVICE_URL` - Health check endpoint
- **API Endpoints:**
  - `GET /api/rtmp-auth/status`
  - `GET /api/rtmp-auth/health`
  - `GET /api/rtmp-auth/config-example/nginx`
  - `GET /api/rtmp-auth/config-example/auth`

#### simpleobsws Library Support
- **New Module:** `backend/app/obs_websocket_adapter.py`
- **Purpose:** Abstraction layer for OBS WebSocket libraries
- **Features:**
  - Runtime library selection via configuration
  - Factory pattern for adapter creation
  - Library availability reporting
- **Configuration:**
  - `OBS_LIBRARY` - obs-websocket-py | simpleobsws (default: obs-websocket-py)
- **API Endpoint:**
  - `GET /api/obs/library-info`
- **Dependency:**
  - `simpleobsws==1.3.1` (optional, in requirements.txt)

### Changed

#### Configuration (`config.py`)
- Added 12 new configuration options for IRLToolkit features
- All new options have sensible defaults and are disabled by default
- Backward compatible with existing .env files

#### Main Application (`main.py`)
- Added lifespan initialization for new components
- Added cleanup handlers for graceful shutdown
- Added IRLToolkit feature logging on startup

#### Requirements (`requirements.txt`)
- Added `simpleobsws==1.3.1` as optional dependency

#### Documentation
- Updated `README.md` with IRLToolkit integration section
- Updated `docs/architecture.md` with integration architecture
- Updated `backend/.env.example` with all new configuration options

---

### Non-Breaking Changes

This release maintains **full backward compatibility**:

1. **Existing APIs Unchanged**
   - All existing endpoints remain functional
   - No changes to request/response formats
   - No changes to WebSocket protocol

2. **Existing Behavior Preserved**
   - State machine logic untouched
   - Quality presets unchanged
   - OBS integration unchanged when new features disabled

3. **Feature Flags**
   - All new features disabled by default
   - Explicit opt-in required
   - Independent feature activation

4. **Graceful Degradation**
   - Components fail independently
   - Missing external services handled gracefully
   - No required external dependencies

---

### Known Limitations

1. **SRTLA Socket Mode**
   - Socket-based metrics source is a placeholder
   - Requires custom srtla build with stats socket

2. **simpleobsws Integration**
   - Adapter available but not actively used by obs_controller.py
   - Manual integration required for full library switch

3. **External Dependencies**
   - OBS HTTP Bridge requires standalone obs-websocket-http service
   - SRTLA requires srtla sender/receiver deployment
   - RTMP Auth requires nginx-rtmp-auth configuration

---

### Testing & Validation

#### Normal Conditions
- All endpoints return expected responses when features disabled
- Components initialize and shutdown cleanly
- No errors in logs with default configuration

#### Degraded Conditions
- Missing external services return appropriate error responses
- Timeouts handled gracefully
- Failed health checks don't affect core system

#### Rollback Procedure
To disable all IRLToolkit features:
```env
FEATURE_OBS_HTTP_BRIDGE=false
FEATURE_SRTLA_TRANSPORT=false
FEATURE_RTMP_AUTH=false
OBS_LIBRARY=obs-websocket-py
```

---

### Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `backend/app/config.py` | Modified | Added IRLToolkit configuration options |
| `backend/app/main.py` | Modified | Added component initialization and API endpoints |
| `backend/app/obs_http_bridge.py` | **New** | OBS HTTP Bridge client |
| `backend/app/srtla_adapter.py` | **New** | SRTLA metrics adapter |
| `backend/app/rtmp_auth_monitor.py` | **New** | RTMP auth health monitor |
| `backend/app/obs_websocket_adapter.py` | **New** | OBS library abstraction |
| `backend/requirements.txt` | Modified | Added simpleobsws dependency |
| `backend/.env.example` | Modified | Added IRLToolkit configuration |
| `README.md` | Modified | Added integration documentation |
| `docs/architecture.md` | Modified | Added integration architecture |
| `docs/IRLTOOLKIT_INTEGRATION_DESIGN.md` | Existing | Design document |
| `CHANGELOG_IRLTOOLKIT.md` | **New** | This changelog |

---

### Migration Guide

#### From v1.1.0 (NOALBS features)

No migration required. All existing functionality remains unchanged.

#### Enabling IRLToolkit Features

1. Update configuration:
   ```bash
   cp backend/.env.example backend/.env.new
   diff backend/.env backend/.env.new  # Review new options
   ```

2. Add desired features to `.env`:
   ```env
   FEATURE_OBS_HTTP_BRIDGE=true
   # ... other features as needed
   ```

3. Install updated dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. Restart backend:
   ```bash
   systemctl restart vvlive-backend
   ```

---

### Contributors

- Implementation based on approved design document
- Follows VVLIVE v1.1.0 integration patterns (NOALBS)

### License

Same as VVLIVE project license.
