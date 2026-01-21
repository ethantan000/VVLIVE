"""
VVLIVE Backend - Main Application
FastAPI server with WebSocket support
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import init_database
from .models import QualityState, QUALITY_PRESETS
from .state_machine import AdaptiveStateMachine

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("VVLIVE Backend starting...")
    logger.info(f"Features enabled: Emergency={settings.feature_emergency_mode}")

    # Initialize database
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Initialize state machine
    app.state.quality_machine = AdaptiveStateMachine(initial_state=QualityState.MEDIUM)
    logger.info(f"State machine initialized at {QualityState.MEDIUM.value}")

    yield

    # Shutdown
    logger.info("VVLIVE Backend shutting down...")


# Create FastAPI app
app = FastAPI(
    title="VVLIVE Backend",
    description="IRL Bonded Streaming Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
# In production, set ALLOWED_ORIGINS environment variable to specific domains
allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if settings.debug:
    # Allow all origins in debug mode for development
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False if "*" in allowed_origins else True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "VVLIVE Backend",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "features": {
            "emergency_mode": settings.feature_emergency_mode,
            "audio_only": settings.feature_audio_only_mode
        }
    }


@app.get("/api/status")
async def get_status():
    """Get current system status"""
    machine = app.state.quality_machine
    current_state = machine.get_current_state()
    current_preset = machine.get_current_preset()

    return {
        "quality_state": current_state.value,
        "preset": {
            "resolution": current_preset.resolution,
            "framerate": current_preset.framerate,
            "bitrate_kbps": current_preset.bitrate_kbps,
        },
        "time_in_state": machine.context.time_in_state(),
        "features": {
            "emergency_mode": settings.feature_emergency_mode,
            "audio_only": settings.feature_audio_only_mode,
            "health_score": settings.feature_health_score,
        }
    }


@app.get("/api/metrics")
async def get_metrics():
    """Get current network metrics (mock data for now)"""
    # TODO: Implement actual MPTCP metrics collection
    return {
        "bandwidth_mbps": 5.2,
        "packet_loss_percent": 0.8,
        "rtt_ms": 45,
        "active_subflows": 2,
        "uplinks": [
            {"name": "Verizon", "status": "active", "bandwidth_mbps": 3.1},
            {"name": "AT&T", "status": "active", "bandwidth_mbps": 2.1}
        ]
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket.accept()
    logger.info("Dashboard WebSocket connected")

    try:
        # Send initial state
        machine = app.state.quality_machine
        await websocket.send_json({
            "type": "status",
            "quality_state": machine.get_current_state().value,
        })

        while True:
            # Wait for client messages (ping/pong for keepalive)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            # TODO: Send real-time metric updates here
    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("Dashboard WebSocket closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )