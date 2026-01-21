# NOALBS Integration Guide

This guide explains the NOALBS-inspired features integrated into VVLIVE and how to enable and configure them.

## Overview

VVLIVE has integrated proven patterns from **[NOALBS](https://github.com/NOALBS/nginx-obs-automatic-low-bitrate-switching)** (nginx-obs-automatic-low-bitrate-switching) to enhance stream reliability and automation. These features are **completely optional** and disabled by default.

### What is NOALBS?

NOALBS is a battle-tested tool for automatically switching OBS scenes based on bitrate monitoring. It's widely used in the IRL streaming community for handling unstable network conditions.

### Why Integrate NOALBS Patterns?

1. **Proven Reliability**: NOALBS has been tested in real-world IRL streaming scenarios
2. **Anti-Flapping Logic**: Retry mechanisms prevent quality oscillation
3. **Dual Verification**: Combines network metrics with actual ingest stats
4. **OBS Automation**: Automatic scene switching for viewer experience

### VVLIVE's Unique Approach

VVLIVE combines NOALBS patterns with its unique MPTCP bonding:

- **MPTCP metrics**: Proactive network monitoring (unique to VVLIVE)
- **Ingest stats**: Reactive verification (NOALBS pattern)
- **Encoder control**: Primary quality management (VVLIVE-first)
- **Scene switching**: Secondary visual feedback (NOALBS pattern)

## Integrated Features

### 1. OBS WebSocket Integration

**What it does**: Automatically switches OBS scenes based on quality state changes.

**Enable in `.env`**:
```env
FEATURE_OBS_INTEGRATION=true
```

**Configuration**:
```env
# OBS WebSocket settings (already configured)
OBS_HOST=localhost
OBS_PORT=4455
OBS_PASSWORD=your-obs-password

# Scene mapping
OBS_SCENE_HIGH=Main Camera
OBS_SCENE_MEDIUM=Main Camera
OBS_SCENE_LOW=Simple Overlay
OBS_SCENE_VERY_LOW=Audio Only
OBS_SCENE_ERROR=Stream Offline
OBS_SCENE_EMERGENCY=Emergency Simple
```

**How it works**:
1. Connects to OBS via WebSocket v5 protocol
2. Monitors quality state changes from state machine
3. Automatically switches to mapped scene
4. Reconnects automatically if OBS restarts

**API Endpoints**:
- `GET /api/obs/status` - Check OBS connection status
- `POST /api/obs/scene?scene_name=X` - Manually switch scene

### 2. Ingest Server Monitoring

**What it does**: Polls streaming server stats (nginx-rtmp, SRT, etc.) to verify actual received bitrate.

**Enable in `.env`**:
```env
FEATURE_INGEST_MONITORING=true
```

**Configuration**:
```env
# Stats endpoint (nginx-rtmp example)
INGEST_STATS_URL=http://localhost/stats
INGEST_STREAM_KEY=live/stream
INGEST_STATS_POLL_INTERVAL=2

# Server type
INGEST_SERVER_TYPE=nginx
# Supported: nginx, srt, node-media-server, srt-live-server
```

**Supported Servers**:
- **nginx-rtmp**: XML stats endpoint
- **SRT**: JSON stats with RTT
- **Node-Media-Server**: JSON API
- **SRT-Live-Server**: SRT protocol stats

**How it works**:
1. Polls stats endpoint every N seconds
2. Extracts bitrate, connection status, RTT
3. Provides ground truth for quality decisions
4. Falls back gracefully if stats unavailable

**API Endpoints**:
- `GET /api/ingest/stats` - Current ingest server stats

### 3. Retry Logic (Anti-Flapping)

**What it does**: Requires N consecutive failing checks before downgrading quality (prevents oscillation).

**Enable in `.env`**:
```env
FEATURE_RETRY_LOGIC=true
```

**Configuration**:
```env
# Retry attempts before state change
STATE_CHANGE_RETRY_ATTEMPTS=5

# Seconds between retry checks
STATE_CHANGE_RETRY_INTERVAL=2

# Skip retries when upgrading (faster recovery)
INSTANT_RECOVERY_ENABLED=true
```

**How it works**:
- **Downgrades**: Requires 5 consecutive failing checks (default)
- **Upgrades**: Instant if `INSTANT_RECOVERY_ENABLED=true`, otherwise requires retries
- **Reset**: Counters reset when conditions change

**Example**:
```
Network drops to 400 kbps
  ↓ Check 1: Recommend LOW state (1/5)
  ↓ Check 2: Recommend LOW state (2/5)
  ↓ Check 3: Recommend LOW state (3/5)
  ↓ Check 4: Recommend LOW state (4/5)
  ↓ Check 5: Recommend LOW state (5/5) → TRANSITION!
```

If network recovers during retry period, counters reset.

**API Endpoints**:
- `GET /api/state-machine/retry-status` - View retry counters
- `POST /api/state-machine/reset-retry` - Manual reset (testing)

### 4. Dual Metrics Aggregation

**What it does**: Combines MPTCP network metrics with ingest server stats for comprehensive health assessment.

**Enable in `.env`**:
```env
FEATURE_DUAL_METRICS=true
FEATURE_INGEST_MONITORING=true  # Required
```

**How it works**:
1. **Primary Source**: MPTCP metrics (proactive)
2. **Secondary Source**: Ingest stats (reactive verification)
3. **Divergence Detection**: Warns if sources disagree (indicates encoder/local issues)
4. **Health Scoring**: 0-100 score based on all metrics

**Health Scoring Algorithm**:
- Bitrate adequacy: 40 points
- Packet loss: 30 points
- RTT: 20 points
- Connection redundancy: 10 points

**API Endpoints**:
- `GET /api/metrics/aggregated` - Combined health assessment

## NOALBS-Style Bitrate Thresholds

These thresholds determine when quality changes occur:

```env
# Bitrate below this triggers LOW quality state (kbps)
BITRATE_THRESHOLD_LOW_KBPS=500

# Bitrate below this triggers OFFLINE state (kbps)
BITRATE_THRESHOLD_OFFLINE_KBPS=450

# RTT threshold for SRT protocol (milliseconds)
BITRATE_THRESHOLD_RTT_MS=1000
```

**Note**: These complement VVLIVE's existing state machine thresholds. The state machine uses its own bandwidth/packet loss/RTT thresholds for MPTCP metrics. NOALBS thresholds apply to ingest stats verification.

## Setup Guide

### Prerequisites

- OBS Studio 28+ with WebSocket server enabled (for OBS integration)
- nginx-rtmp or compatible streaming server (for ingest monitoring)
- VVLIVE already installed and running

### Basic Setup (OBS Integration Only)

1. **Enable OBS WebSocket** in OBS Studio:
   - Tools → WebSocket Server Settings
   - Enable server
   - Set port to 4455
   - Set password

2. **Configure VVLIVE**:
   ```bash
   cd backend
   nano .env
   ```

   ```env
   # Enable OBS integration
   FEATURE_OBS_INTEGRATION=true

   # OBS settings
   OBS_HOST=localhost
   OBS_PORT=4455
   OBS_PASSWORD=your-obs-password

   # Configure scenes
   OBS_SCENE_HIGH=Main Camera
   OBS_SCENE_LOW=Simple Overlay
   OBS_SCENE_VERY_LOW=Audio Only
   OBS_SCENE_ERROR=Stream Offline
   ```

3. **Restart VVLIVE**:
   ```bash
   python -m app.main
   ```

4. **Verify**:
   ```bash
   curl http://localhost:8000/api/obs/status
   ```

### Full Setup (All Features)

1. **Setup nginx-rtmp** stats endpoint:
   ```nginx
   rtmp {
       server {
           listen 1935;

           application live {
               live on;
               record off;
           }
       }
   }

   http {
       server {
           listen 8080;

           location /stats {
               rtmp_stat all;
               rtmp_stat_stylesheet stat.xsl;
           }
       }
   }
   ```

2. **Enable all NOALBS features**:
   ```env
   # Enable all features
   FEATURE_OBS_INTEGRATION=true
   FEATURE_INGEST_MONITORING=true
   FEATURE_RETRY_LOGIC=true
   FEATURE_DUAL_METRICS=true

   # Ingest monitoring
   INGEST_STATS_URL=http://localhost:8080/stats
   INGEST_STREAM_KEY=live/stream
   INGEST_STATS_POLL_INTERVAL=2
   INGEST_SERVER_TYPE=nginx

   # Retry logic
   STATE_CHANGE_RETRY_ATTEMPTS=5
   INSTANT_RECOVERY_ENABLED=true

   # Thresholds
   BITRATE_THRESHOLD_LOW_KBPS=500
   BITRATE_THRESHOLD_OFFLINE_KBPS=450
   ```

3. **Restart and verify**:
   ```bash
   # Check all features enabled
   curl http://localhost:8000/api/obs/status
   curl http://localhost:8000/api/ingest/stats
   curl http://localhost:8000/api/metrics/aggregated
   curl http://localhost:8000/api/state-machine/retry-status
   ```

## Troubleshooting

### OBS Won't Connect

**Symptom**: `GET /api/obs/status` shows `"state": "error"`

**Solutions**:
1. Verify OBS WebSocket is enabled (Tools → WebSocket Server Settings)
2. Check port 4455 is correct
3. Verify password matches
4. Check OBS is running
5. Review logs: `journalctl -u vvlive-backend -f`

### Ingest Stats Not Updating

**Symptom**: `GET /api/ingest/stats` shows high failure rate

**Solutions**:
1. Verify stats URL is accessible: `curl http://localhost:8080/stats`
2. Check stream key matches
3. Verify server type is correct (nginx, srt, etc.)
4. Check streaming server is receiving stream
5. Review logs for parsing errors

### Retry Logic Too Aggressive

**Symptom**: Quality changes happen too slowly

**Solutions**:
1. Reduce `STATE_CHANGE_RETRY_ATTEMPTS` (try 3 instead of 5)
2. Reduce `STATE_CHANGE_RETRY_INTERVAL` (try 1s instead of 2s)
3. Enable `INSTANT_RECOVERY_ENABLED=true` for faster upgrades

### Retry Logic Too Sensitive

**Symptom**: Quality flaps between states

**Solutions**:
1. Increase `STATE_CHANGE_RETRY_ATTEMPTS` (try 7 or 10)
2. Increase `STATE_CHANGE_RETRY_INTERVAL` (try 3s)
3. Disable instant recovery: `INSTANT_RECOVERY_ENABLED=false`

## Feature Combinations

### Recommended Setups

**Minimal (Scene Switching Only)**:
```env
FEATURE_OBS_INTEGRATION=true
```
- Automatic scene changes
- No additional monitoring
- Use VVLIVE's existing MPTCP metrics

**Standard (Verification + Scenes)**:
```env
FEATURE_OBS_INTEGRATION=true
FEATURE_INGEST_MONITORING=true
FEATURE_DUAL_METRICS=true
```
- Dual-source monitoring
- Automatic scene changes
- Enhanced reliability

**Maximum Stability (All Features)**:
```env
FEATURE_OBS_INTEGRATION=true
FEATURE_INGEST_MONITORING=true
FEATURE_RETRY_LOGIC=true
FEATURE_DUAL_METRICS=true
```
- Anti-flapping protection
- Dual-source monitoring
- Automatic scene changes
- Best for unstable networks

## Performance Impact

### Resource Usage

- **OBS Integration**: <1% CPU, WebSocket connection overhead
- **Ingest Monitoring**: <1% CPU, HTTP poll every 2s (~500 bytes/poll)
- **Retry Logic**: Negligible (in-memory counters only)
- **Dual Metrics**: Negligible (data aggregation only)

**Total overhead**: <2% CPU, <1 KB/s network

### Latency Impact

- **Detection to Action** (with retry logic enabled):
  - Worst case: ~14 seconds (5 retries @ 2s interval + network/state delays)
  - Best case: <500ms (instant recovery on upgrade)

- **Without retry logic**:
  - Same as core VVLIVE (5-60s depending on condition)

## Migration from NOALBS

If you're currently using NOALBS and want to switch to VVLIVE:

### Feature Comparison

| NOALBS Feature | VVLIVE Equivalent | Status |
|----------------|-------------------|--------|
| OBS WebSocket v5 | OBS Controller | ✅ Implemented |
| nginx-rtmp stats | Ingest Monitor | ✅ Implemented |
| SRT stats | Ingest Monitor | ✅ Implemented |
| Retry attempts | Retry Logic | ✅ Implemented |
| Instant recovery | Instant Recovery | ✅ Implemented |
| Scene override per source | N/A | ❌ Not needed (VVLIVE is single-source) |
| Chat commands | N/A | ❌ Not applicable (dashboard-controlled) |
| Twitch integration | N/A | ❌ Not applicable (IRL streaming focus) |

### Migration Steps

1. **Keep NOALBS running** initially
2. **Install VVLIVE** alongside
3. **Enable features one by one**:
   - Start with `FEATURE_OBS_INTEGRATION=false`
   - Enable monitoring first: `FEATURE_INGEST_MONITORING=true`
   - Test for 24 hours
   - Enable OBS: `FEATURE_OBS_INTEGRATION=true`
   - Test for 24 hours
   - Enable retry: `FEATURE_RETRY_LOGIC=true`
4. **Compare behavior** between NOALBS and VVLIVE
5. **Disable NOALBS** once confident

## Advanced Configuration

### Custom Scene Logic

You can configure different scenes for each quality state:

```env
# Same scene for HIGH/MEDIUM (no visual change for minor dips)
OBS_SCENE_HIGH=Main Camera
OBS_SCENE_MEDIUM=Main Camera

# Warning overlay for LOW
OBS_SCENE_LOW=Main Camera - Low Quality Warning

# Audio-only for VERY_LOW
OBS_SCENE_VERY_LOW=Audio Only - Network Issues

# Offline scene for ERROR
OBS_SCENE_ERROR=Stream Offline - Technical Difficulties

# Emergency scene (triggered manually via /api/obs/emergency)
OBS_SCENE_EMERGENCY=Emergency - Be Right Back
```

### Per-Environment Thresholds

**Development** (lenient, faster testing):
```env
STATE_CHANGE_RETRY_ATTEMPTS=2
STATE_CHANGE_RETRY_INTERVAL=1
BITRATE_THRESHOLD_LOW_KBPS=300
```

**Production** (stable, conservative):
```env
STATE_CHANGE_RETRY_ATTEMPTS=7
STATE_CHANGE_RETRY_INTERVAL=3
BITRATE_THRESHOLD_LOW_KBPS=600
```

**High-Latency Connections** (satellite, international):
```env
BITRATE_THRESHOLD_RTT_MS=2000
STATE_CHANGE_RETRY_ATTEMPTS=10
```

## API Reference

### OBS Endpoints

**GET /api/obs/status**
```json
{
  "enabled": true,
  "state": "authenticated",
  "connected": true,
  "current_scene": "Main Camera",
  "host": "localhost:4455"
}
```

**POST /api/obs/scene?scene_name=Audio Only**
```json
{
  "success": true,
  "scene_name": "Audio Only",
  "current_scene": "Audio Only"
}
```

### Ingest Endpoints

**GET /api/ingest/stats**
```json
{
  "enabled": true,
  "server_type": "nginx",
  "total_polls": 1234,
  "poll_failures": 5,
  "success_rate_percent": 99.6,
  "last_stats": {
    "bitrate_kbps": 2450.5,
    "connection_active": true,
    "timestamp": "2026-01-21T12:00:00Z"
  }
}
```

### Aggregated Metrics

**GET /api/metrics/aggregated**
```json
{
  "enabled": true,
  "health_status": "healthy",
  "health_score": 87,
  "primary_source": "both",
  "divergence_detected": false,
  "mptcp": {
    "bandwidth_mbps": 5.2,
    "packet_loss_percent": 0.8,
    "rtt_ms": 45,
    "active_subflows": 2
  },
  "ingest": {
    "bitrate_kbps": 2450.5,
    "connection_active": true
  }
}
```

### Retry Status

**GET /api/state-machine/retry-status**
```json
{
  "enabled": true,
  "retry_attempts": 5,
  "instant_recovery": true,
  "downgrade_counters": {
    "LOW": 3
  },
  "upgrade_counters": {}
}
```

## Backwards Compatibility

All NOALBS features are **100% backward compatible**:

- ✅ Disabled by default
- ✅ Core VVLIVE functionality unchanged
- ✅ Existing API endpoints unmodified
- ✅ No database schema changes required
- ✅ Graceful degradation if components fail

You can enable/disable any feature without affecting others.

## Support

- **Issues**: https://github.com/ethantan000/VVLIVE/issues
- **NOALBS Source**: https://github.com/NOALBS/nginx-obs-automatic-low-bitrate-switching
- **Documentation**: See `docs/` directory

---

**Built with inspiration from the NOALBS project and the IRL streaming community.**
