"""
VVLIVE Backend - Main Application
FastAPI server with WebSocket support
"""

import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .config import settings

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="VVLIVE Backend",
    description="IRL Bonded Streaming Backend API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("VVLIVE Backend starting...")
    logger.info(f"Features enabled: Emergency={settings.feature_emergency_mode}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("VVLIVE Backend shutting down...")


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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for dashboard"""
    await websocket.accept()
    logger.info("Dashboard WebSocket connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("Dashboard WebSocket disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )