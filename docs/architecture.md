\# VVLIVE Architecture



\## System Overview

```

Camera → Encoder → Pi (MPTCP Client) → Verizon + AT\&T → VPS → OBS → Twitch

```



\## Components



\### Raspberry Pi

\- MPTCP client

\- Encoder control

\- Network monitoring



\### Cloud VPS

\- MPTCP server

\- Backend API (FastAPI)

\- OBS integration

\- Dashboard hosting



\### Backend Services

\- State machine (quality control)

\- Encoder controller

\- Health monitoring

\- Alert system



\### Frontend

\- React dashboard

\- Real-time WebSocket updates

\- Quality controls



\## Data Flow



1\. Camera → Encoder (HDMI/SDI)

2\. Encoder → Pi (RTMP/SRT over Ethernet)

3\. Pi → VPS (MPTCP over dual cellular)

4\. VPS → OBS (local SRT/RTMP)

5\. OBS → Streaming platform (RTMP)



\## State Machine



Quality states (LOCKED):

\- HIGH: 1080p30 @ 4.5 Mbps

\- MEDIUM: 720p30 @ 2.5 Mbps

\- LOW: 480p24 @ 1.2 Mbps

\- VERY\_LOW: 360p24 @ 600 Kbps



Transitions based on:

\- Bandwidth

\- Packet loss

\- RTT (latency)



See `state\_machine.py` for implementation.

