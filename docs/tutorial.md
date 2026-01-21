\# VVLIVE Setup Tutorial



\## Prerequisites



\### Hardware

\- Raspberry Pi 4/5 (4GB+ RAM)

\- URay UHE265-1WB encoder

\- 2x cellular hotspots (Verizon + AT\&T)

\- Cloud VPS (Ubuntu 22.04+)



\### Software

\- Raspberry Pi OS (kernel ≥5.6)

\- Python 3.11+

\- Node.js 18+

\- OBS Studio 28+



\## Installation Steps



\### 1. Setup Raspberry Pi

```bash

\# Clone repository

git clone https://github.com/ethantan000/VVLIVE.git

cd VVLIVE



\# Run MPTCP setup

cd mptcp

sudo bash setup\_mptcp\_pi.sh



\# Verify MPTCP

sysctl net.mptcp.enabled  # Should show = 1

```



\### 2. Setup Cloud VPS

```bash

\# Clone repository

git clone https://github.com/ethantan000/VVLIVE.git

cd VVLIVE



\# Setup MPTCP

cd mptcp

sudo bash setup\_mptcp\_server.sh



\# Install backend

cd ../backend

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt



\# Configure

cp .env.example .env

nano .env  # Edit configuration



\# Run backend

python -m app.main

```



\### 3. Install Frontend

```bash

cd ../frontend

npm install

npm run build



\# Deploy (optional)

sudo cp -r dist/\* /var/www/vvlive/

```



\### 4. Configure OBS



1\. Open OBS

2\. Tools → WebSocket Server Settings

3\. Enable server, port 4455

4\. Create scenes: "Main Camera", "Emergency - Simple", "Audio Only"



\### 5. Access Dashboard



Open browser: `http://localhost:3000` (dev) or `https://YOUR\_VPS\_IP` (production)



\## Troubleshooting



\### Backend won't start

```bash

\# Check logs

journalctl -u vvlive-backend -f



\# Verify Python version

python3 --version  # Should be 3.11+

```



\### MPTCP not working

```bash

\# Verify kernel support

uname -r  # Should be ≥5.6

sysctl net.mptcp.enabled  # Should be 1

```



\### Frontend build fails

```bash

\# Clear node\_modules

rm -rf node\_modules package-lock.json

npm install

```



\## Next Steps



\- Configure encoder IP in backend `.env`

\- Set OBS WebSocket password

\- Test with real cellular connections

\- Review quality presets



See main README for full documentation.

