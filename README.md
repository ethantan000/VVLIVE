# VVLIVE - IRL Bonded Cellular Streaming Solution

**VVLIVE** (Variable Video LIVE) is a complete system for reliable mobile live streaming using bonded cellular connections. It combines multiple cellular uplinks (Verizon + AT&T) via MPTCP (Multipath TCP) to create a single high-bandwidth, fault-tolerant connection for IRL streaming.

## 🎯 What Does It Do?

VVLIVE automatically adapts video quality based on real-time network conditions to prevent stream drops during mobile broadcasts. When bandwidth drops, it seamlessly downgrades quality. When conditions improve, it upgrades back.

**Key Flow:**
```
Camera → Encoder → Raspberry Pi (MPTCP Client) → Dual Cellular → Cloud VPS → OBS → Twitch/YouTube
                                                 ↓
                                          Dashboard (React)
```

## ✨ Features

### Adaptive Quality Control
- **Automatic quality switching** based on bandwidth, packet loss, and latency
- **Quality levels:** HIGH (1080p30), MEDIUM (720p30), LOW (480p24), VERY_LOW (360p24)
- **Smart hysteresis** to prevent quality flapping
- **Recovery mode** for gradual upgrades

### Resilience
- **Dual uplink bonding** via MPTCP
- **Emergency mode** - switches to simple scene on critical issues
- **Audio-only fallback** when video bandwidth unavailable
- **Automatic encoder control** to match network conditions

### Monitoring
- **Real-time dashboard** showing network status and quality state
- **Health scoring** for overall stream quality
- **Event timeline** of quality changes and alerts
- **Post-stream reports** with statistics

### IRLToolkit Integration (v1.2.0)
- **OBS HTTP Bridge** - HTTP-based OBS control for external integrations
- **SRTLA Transport** - Alternative bonded transport using SRT link aggregation
- **RTMP Authentication** - Stream key validation via nginx-rtmp-auth
- **simpleobsws** - Optional async OBS WebSocket library

## 📋 Prerequisites

### Hardware
- **Raspberry Pi 4/5** (4GB+ RAM) - MPTCP client
- **URay H.265 encoder** (or compatible) - video encoding
- **2x Cellular hotspots** - Verizon + AT&T recommended
- **Cloud VPS** (2+ vCPU, 4GB+ RAM, Ubuntu 22.04+) - MPTCP server
- **Camera** with HDMI/SDI output

### Software
- **Raspberry Pi:** Pi OS with kernel 5.6+ (MPTCP support)
- **VPS:** Ubuntu 22.04+ with kernel 5.6+
- **Local Machine:** Python 3.11+, Node.js 18+, OBS Studio 28+

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/ethantan000/VVLIVE.git
cd VVLIVE
```

### 2. Setup Raspberry Pi (MPTCP Client)

```bash
# On Raspberry Pi
cd mptcp
sudo bash setup_mptcp_pi.sh

# Verify MPTCP is enabled
sysctl net.mptcp.enabled  # Should show: net.mptcp.enabled = 1
```

### 3. Setup Cloud VPS (MPTCP Server)

```bash
# On VPS
cd mptcp
sudo bash setup_mptcp_server.sh

# Verify MPTCP is enabled
sysctl net.mptcp.enabled  # Should show: net.mptcp.enabled = 1
```

### 4. Install Backend

```bash
# On VPS
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Edit configuration (see Configuration section)

# Run backend
python -m app.main
# Backend will start on http://localhost:8000
```

### 5. Install Frontend

```bash
# On VPS
cd frontend
npm install

# Development
npm run dev  # Runs on http://localhost:3000

# Production
npm run build
sudo cp -r dist/* /var/www/vvlive/  # Deploy to nginx
```

### 6. Configure OBS

1. Open OBS Studio
2. Go to **Tools → WebSocket Server Settings**
3. Enable server, set port to `4455`
4. Set a password (update in backend `.env`)
5. Create scenes:
   - **Main Camera** - normal streaming layout
   - **Emergency - Simple** - minimal overlay for bad conditions
   - **Audio Only** - static image with audio

### 7. Setup Nginx (Production)

```bash
# Install nginx
sudo apt install nginx

# Copy configuration
sudo cp config/nginx/vvlive.conf /etc/nginx/sites-available/vvlive
sudo ln -s /etc/nginx/sites-available/vvlive /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

### 8. Access Dashboard

- **Development:** http://localhost:3000
- **Production:** http://YOUR_VPS_IP

## ⚙️ Configuration

### Backend Environment Variables

Create `backend/.env` from the template:

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

**Critical settings to change:**

```env
# SECURITY - Generate secure keys for production
SECRET_KEY=your-random-secure-key-here
API_TOKEN=your-random-secure-token-here

# ENCODER - Your URay encoder settings
ENCODER_IP=192.168.1.100
ENCODER_USERNAME=admin
ENCODER_PASSWORD=your-encoder-password

# OBS - WebSocket connection
OBS_HOST=localhost
OBS_PORT=4455
OBS_PASSWORD=your-obs-password

# MPTCP - Server port
MPTCP_SERVER_PORT=8443
```

**Generate secure keys:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Network Configuration

On **Raspberry Pi**, configure routing for dual uplink:

```bash
# Example: Verizon on eth0, AT&T on eth1
sudo ip rule add from 192.168.1.0/24 table verizon
sudo ip rule add from 192.168.2.0/24 table att
sudo ip route add default via 192.168.1.1 dev eth0 table verizon
sudo ip route add default via 192.168.2.1 dev eth1 table att
```

## 🧪 Testing

### Run Backend Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Get current status
curl http://localhost:8000/api/status

# Get network metrics
curl http://localhost:8000/api/metrics
```

### Test Frontend Build

```bash
cd frontend
npm run build
# Build output in dist/
```

## 📖 Architecture

### System Components

1. **Raspberry Pi (MPTCP Client)**
   - Connects to encoder via Ethernet
   - Bonds cellular connections via MPTCP
   - Forwards video stream to VPS

2. **Cloud VPS (MPTCP Server)**
   - Receives bonded MPTCP stream
   - Runs backend API (FastAPI)
   - Monitors network metrics
   - Controls encoder quality
   - Integrates with OBS

3. **Backend (Python/FastAPI)**
   - Adaptive state machine for quality control
   - Real-time network monitoring
   - Encoder control via HTTP API
   - OBS scene switching via WebSocket
   - Dashboard WebSocket updates

4. **Frontend (React/Vite)**
   - Real-time dashboard
   - Quality state visualization
   - Network health indicators
   - Manual controls

### Quality State Machine

The system uses a **locked state machine** for quality adaptation:

```
HIGH (1080p30 @ 4.5 Mbps)
  ↓ packet loss >2% for 5s OR bandwidth <5 Mbps for 10s
MEDIUM (720p30 @ 2.5 Mbps)
  ↓ packet loss >3% for 5s OR bandwidth <3 Mbps for 10s
LOW (480p24 @ 1.2 Mbps)
  ↓ packet loss >5% for 5s OR bandwidth <1.5 Mbps for 10s
VERY_LOW (360p24 @ 600 Kbps)
  ↓ bandwidth <500 Kbps for 20s
ERROR (Audio only)
```

**Upgrades** require:
- Stable conditions for 60 seconds
- Go through RECOVERY state first
- Gradual step-up (no jumps)

**Downgrades** are:
- Fast (5-10 second observation)
- Direct to target state
- Aggressive to prevent drops

See `backend/app/state_machine.py` for full implementation.

### Data Flow

1. **Camera** outputs HDMI/SDI to encoder
2. **Encoder** streams RTMP/SRT to Pi over Ethernet
3. **Pi** forwards stream over bonded MPTCP connection to VPS
4. **VPS** receives stream, monitors MPTCP statistics
5. **Backend** analyzes metrics, adjusts encoder settings
6. **OBS** receives local stream from backend, outputs to Twitch/YouTube
7. **Dashboard** displays real-time status via WebSocket

## 🔧 Development

### Project Structure

```
VVLIVE/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app + routes
│   │   ├── config.py         # Configuration management
│   │   ├── models.py         # Data models + quality presets
│   │   ├── state_machine.py  # Adaptive quality state machine
│   │   └── database.py       # SQLite database setup
│   ├── tests/                # Backend tests
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Configuration template
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main dashboard component
│   │   ├── main.jsx          # React entry point
│   │   └── index.css         # Tailwind styles
│   ├── package.json          # Node dependencies
│   └── vite.config.js        # Vite configuration
├── mptcp/
│   ├── setup_mptcp_pi.sh     # Pi MPTCP setup
│   └── setup_mptcp_server.sh # VPS MPTCP setup
├── config/
│   └── nginx/
│       └── vvlive.conf       # Nginx reverse proxy config
├── docs/
│   ├── architecture.md       # System architecture
│   └── tutorial.md           # Setup tutorial
└── scripts/
    ├── install.sh            # Quick install script
    └── start.sh              # Start dev services
```

### Adding New Features

1. **Backend endpoint:** Add to `backend/app/main.py`
2. **Configuration:** Add to `backend/app/config.py` and `.env.example`
3. **Data model:** Add to `backend/app/models.py`
4. **Frontend UI:** Update `frontend/src/App.jsx`
5. **Tests:** Add to `backend/tests/`

### Running in Development

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python -m app.main
# Runs on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:3000
# Proxies API requests to backend
```

## 🐛 Troubleshooting

### Backend won't start

**Error:** `SECURITY WARNING: Insecure default values detected!`

**Solution:** Edit `backend/.env` and set secure values for `SECRET_KEY`, `API_TOKEN`, and `ENCODER_PASSWORD`. Or set `DEBUG=true` for development.

---

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:** Install dependencies:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend build fails

**Error:** `npm ERR! code ELIFECYCLE`

**Solution:** Clear cache and reinstall:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### MPTCP not working

**Error:** `sysctl: cannot stat /proc/sys/net/mptcp/enabled`

**Solution:** Your kernel doesn't support MPTCP. Upgrade to kernel 5.6+:
```bash
# On Raspberry Pi
sudo rpi-update

# On Ubuntu VPS
sudo apt update && sudo apt upgrade
```

---

**Check:** Are both cellular connections active?
```bash
ip addr show  # Should show both interfaces with IPs
ping -I eth0 8.8.8.8  # Test Verizon
ping -I eth1 8.8.8.8  # Test AT&T
```

### Database errors

**Error:** `aiosqlite.Error: unable to open database file`

**Solution:** Create data directory:
```bash
mkdir -p backend/data
chmod 755 backend/data
```

### OBS won't connect

**Check:**
1. OBS WebSocket server is enabled (Tools → WebSocket Server Settings)
2. Port 4455 is correct in backend `.env`
3. Password matches
4. Firewall allows connection

**Test connection:**
```bash
# Install websocat for testing
cargo install websocat

# Test WebSocket
websocat ws://localhost:4455
```

## 📊 Monitoring

### View Backend Logs

```bash
# If running as systemd service
journalctl -u vvlive-backend -f

# If running directly
# Logs output to stdout
```

### Monitor MPTCP Connections

```bash
# Show MPTCP connections
ss -M

# Show detailed MPTCP info
ss -Mnt

# Watch MPTCP statistics
watch -n 1 'ss -M'
```

### Check Database

```bash
cd backend/data
sqlite3 streaming.db

sqlite> .tables
sqlite> SELECT * FROM stream_sessions;
sqlite> .quit
```

## 🚢 Deployment

### Production Checklist

- [ ] Set secure `SECRET_KEY` and `API_TOKEN`
- [ ] Change all default passwords
- [ ] Set `DEBUG=false` in backend `.env`
- [ ] Build frontend for production (`npm run build`)
- [ ] Configure nginx as reverse proxy
- [ ] Enable HTTPS (Let's Encrypt)
- [ ] Set up systemd services for auto-start
- [ ] Configure firewall (allow 80, 443, 8443)
- [ ] Test failover (disconnect one cellular connection)
- [ ] Monitor logs for first 24 hours

### Systemd Service (Optional)

Create `/etc/systemd/system/vvlive-backend.service`:

```ini
[Unit]
Description=VVLIVE Backend
After=network.target

[Service]
Type=simple
User=vvlive
WorkingDirectory=/home/vvlive/VVLIVE/backend
Environment="PATH=/home/vvlive/VVLIVE/backend/venv/bin"
ExecStart=/home/vvlive/VVLIVE/backend/venv/bin/python -m app.main
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable vvlive-backend
sudo systemctl start vvlive-backend
```

## ⚠️ Current Limitations

This codebase is **architecturally complete** but has some **intentionally incomplete integrations**:

### Not Yet Implemented
- ❌ **MPTCP metrics collection** - Currently returns mock data
- ❌ **Encoder control integration** - API client not connected
- ❌ **OBS integration** - WebSocket client not active
- ❌ **Real-time dashboard updates** - WebSocket sends test data only

### Ready for Development
- ✅ Backend API structure
- ✅ State machine logic
- ✅ Database schema
- ✅ Frontend UI
- ✅ All integration points defined

**See `INTEGRATION_STATUS.md` for detailed implementation status.**

To complete for production use, implement:
1. MPTCP statistics reader (`/proc/net/mptcp`)
2. URay encoder HTTP client
3. OBS WebSocket integration
4. Background monitoring loop

## 🔌 IRLToolkit Integration (v1.2.0)

VVLIVE integrates with tools from the IRLToolkit organization for enhanced streaming capabilities. All features are **opt-in** and disabled by default.

### OBS HTTP Bridge

Enables HTTP-based OBS control for external integrations (Stream Deck, Discord bots, automation scripts).

```env
# Enable OBS HTTP Bridge
FEATURE_OBS_HTTP_BRIDGE=true
OBS_HTTP_BRIDGE_HOST=localhost
OBS_HTTP_BRIDGE_PORT=5001
OBS_HTTP_BRIDGE_AUTH_KEY=your-secret-key  # Optional
```

**API Endpoints:**
- `GET /api/obs-http/status` - Bridge status
- `POST /api/obs-http/scene?scene_name=MyScene` - Switch scene
- `GET /api/obs-http/health` - Health check

**Requires:** Separate [obs-websocket-http](https://github.com/IRLToolkit/obs-websocket-http) service running.

### SRTLA Transport

Alternative bonded transport using SRT link aggregation as complement/alternative to MPTCP.

```env
# Enable SRTLA Transport
FEATURE_SRTLA_TRANSPORT=true
SRTLA_METRICS_SOURCE=api  # socket | file | api
SRTLA_STATS_ENDPOINT=http://localhost:9001/stats
SRTLA_RECEIVER_PORT=9000
TRANSPORT_MODE=srtla  # mptcp | srtla | hybrid
```

**API Endpoints:**
- `GET /api/srtla/status` - Adapter status
- `GET /api/srtla/metrics` - Normalized metrics (VVLIVE format)
- `GET /api/srtla/raw` - Raw SRTLA statistics

**Requires:** [srtla](https://github.com/IRLToolkit/srtla) sender and receiver deployed.

### RTMP Authentication

Documents and monitors nginx-rtmp-auth for ingest security. Authentication happens at nginx level.

```env
# Enable RTMP Auth Monitoring
FEATURE_RTMP_AUTH=true
RTMP_AUTH_SERVICE_URL=http://localhost:8080/health  # Optional health endpoint
```

**API Endpoints:**
- `GET /api/rtmp-auth/status` - Monitor status
- `GET /api/rtmp-auth/health` - Auth service health check
- `GET /api/rtmp-auth/config-example/nginx` - Example nginx config
- `GET /api/rtmp-auth/config-example/auth` - Example auth.json

**Requires:** [nginx-rtmp-auth](https://github.com/IRLToolkit/nginx-rtmp-auth) configured in nginx.

### simpleobsws Library

Optional alternative OBS WebSocket library from IRLToolkit with cleaner async interface.

```env
# Use simpleobsws instead of native implementation
OBS_LIBRARY=simpleobsws  # obs-websocket-py | simpleobsws
```

**API Endpoint:**
- `GET /api/obs/library-info` - Show configured library and availability

### Disabling IRLToolkit Features

All features are disabled by default. To explicitly disable:

```env
FEATURE_OBS_HTTP_BRIDGE=false
FEATURE_SRTLA_TRANSPORT=false
FEATURE_RTMP_AUTH=false
OBS_LIBRARY=obs-websocket-py
```

## 📚 Additional Documentation

- **Architecture:** See `docs/architecture.md`
- **Tutorial:** See `docs/tutorial.md`
- **Integration Status:** See `INTEGRATION_STATUS.md`
- **IRLToolkit Design:** See `docs/IRLTOOLKIT_INTEGRATION_DESIGN.md`
- **API Documentation:** Run backend and visit http://localhost:8000/docs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run tests: `pytest backend/tests/ -v`
6. Submit a pull request

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

- Built for IRL streamers who need reliable mobile connectivity
- Inspired by the need for bulletproof streaming in challenging network conditions
- Thanks to the MPTCP development team for kernel support

## 📞 Support

For issues and questions:
- **GitHub Issues:** https://github.com/ethantan000/VVLIVE/issues
- **Documentation:** See `docs/` directory

---

**Built with ❤️ for IRL streamers everywhere.**
