"""
VVLIVE Backend - Main Application
FastAPI server with WebSocket support

NOALBS Integration:
- OBS WebSocket controller (opt-in)
- Ingest stats monitoring (opt-in)
- Retry logic wrapper (opt-in)
- Dual metrics aggregation (opt-in)
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import init_database
from .models import QualityState, QUALITY_PRESETS
from .state_machine import AdaptiveStateMachine, RetryLogicWrapper
from .obs_controller import OBSController
from .ingest_monitor import IngestMonitor
from .metrics_aggregator import MetricsAggregator

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
    logger.info(f"Core features: Emergency={settings.feature_emergency_mode}")
    logger.info(
        f"NOALBS features: OBS={settings.feature_obs_integration}, "
        f"Ingest={settings.feature_ingest_monitoring}, "
        f"Retry={settings.feature_retry_logic}, "
        f"Dual={settings.feature_dual_metrics}"
    )

    # Initialize database
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Initialize core state machine
    core_machine = AdaptiveStateMachine(initial_state=QualityState.MEDIUM)
    logger.info(f"Core state machine initialized at {QualityState.MEDIUM.value}")

    # Wrap with retry logic if enabled (NOALBS feature)
    if settings.feature_retry_logic:
        app.state.quality_machine = RetryLogicWrapper(core_machine)
        logger.info("State machine wrapped with retry logic")
    else:
        app.state.quality_machine = core_machine
        logger.info("Using core state machine without retry logic")

    # Initialize NOALBS-inspired components (opt-in)
    app.state.obs_controller: Optional[OBSController] = None
    app.state.ingest_monitor: Optional[IngestMonitor] = None
    app.state.metrics_aggregator: Optional[MetricsAggregator] = None

    # OBS Controller
    if settings.feature_obs_integration:
        try:
            app.state.obs_controller = OBSController()
            # Connect to OBS (async, will retry on failure)
            asyncio.create_task(app.state.obs_controller.connect())
            logger.info("OBS Controller initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OBS Controller: {e}")

    # Ingest Monitor
    if settings.feature_ingest_monitoring:
        try:
            app.state.ingest_monitor = IngestMonitor()
            await app.state.ingest_monitor.start()
            logger.info("Ingest Monitor started")
        except Exception as e:
            logger.error(f"Failed to start Ingest Monitor: {e}")

    # Metrics Aggregator (requires ingest monitor)
    if settings.feature_dual_metrics:
        try:
            app.state.metrics_aggregator = MetricsAggregator(app.state.ingest_monitor)
            logger.info("Metrics Aggregator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Metrics Aggregator: {e}")

    yield

    # Shutdown
    logger.info("VVLIVE Backend shutting down...")

    # Cleanup OBS Controller
    if app.state.obs_controller:
        try:
            await app.state.obs_controller.disconnect()
            logger.info("OBS Controller disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting OBS: {e}")

    # Cleanup Ingest Monitor
    if app.state.ingest_monitor:
        try:
            await app.state.ingest_monitor.stop()
            logger.info("Ingest Monitor stopped")
        except Exception as e:
            logger.error(f"Error stopping Ingest Monitor: {e}")


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


# ============================================================================
# NOALBS-INSPIRED ENDPOINTS (Opt-In Features)
# ============================================================================

@app.get("/api/obs/status")
async def get_obs_status():
    """Get OBS controller status"""
    if not app.state.obs_controller:
        return {
            "enabled": False,
            "message": "OBS integration not enabled"
        }

    return app.state.obs_controller.get_status()


@app.post("/api/obs/scene")
async def switch_obs_scene(scene_name: str):
    """Manually switch OBS scene"""
    if not app.state.obs_controller:
        return {
            "success": False,
            "message": "OBS integration not enabled"
        }

    success = await app.state.obs_controller.switch_scene(scene_name)
    return {
        "success": success,
        "scene_name": scene_name,
        "current_scene": app.state.obs_controller.current_scene
    }


@app.get("/api/ingest/stats")
async def get_ingest_stats():
    """Get ingest server stats"""
    if not app.state.ingest_monitor:
        return {
            "enabled": False,
            "message": "Ingest monitoring not enabled"
        }

    return app.state.ingest_monitor.get_health()


@app.get("/api/metrics/aggregated")
async def get_aggregated_metrics():
    """Get combined MPTCP + ingest metrics"""
    if not app.state.metrics_aggregator:
        return {
            "enabled": False,
            "message": "Dual metrics not enabled"
        }

    return app.state.metrics_aggregator.get_summary()


@app.get("/api/state-machine/retry-status")
async def get_retry_status():
    """Get retry logic status and counters"""
    machine = app.state.quality_machine

    # Check if retry wrapper is active
    if isinstance(machine, RetryLogicWrapper):
        return machine.get_retry_status()
    else:
        return {
            "enabled": False,
            "message": "Retry logic not enabled"
        }


@app.post("/api/state-machine/reset-retry")
async def reset_retry_counters():
    """Reset retry counters (for testing/manual override)"""
    machine = app.state.quality_machine

    if isinstance(machine, RetryLogicWrapper):
        machine.reset_counters()
        return {
            "success": True,
            "message": "Retry counters reset"
        }
    else:
        return {
            "success": False,
            "message": "Retry logic not enabled"
        }


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

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