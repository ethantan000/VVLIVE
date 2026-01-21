"""
OBS WebSocket Library Abstraction
IRLToolkit simpleobsws integration for VVLIVE

This module provides an abstraction layer for OBS WebSocket communication,
allowing runtime selection between the native implementation (using websockets
library directly) and simpleobsws (IRLToolkit's async OBS WebSocket library).

Configurable via OBS_LIBRARY setting in .env:
- "obs-websocket-py" (default): Uses native websockets implementation
- "simpleobsws": Uses IRLToolkit's simpleobsws library
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from .config import settings

logger = logging.getLogger(__name__)


class OBSWebSocketAdapter(ABC):
    """
    Abstract base class for OBS WebSocket adapters

    Defines the interface for OBS WebSocket communication that both
    native and simpleobsws implementations must follow.
    """

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to OBS WebSocket server"""
        pass

    @abstractmethod
    async def disconnect(self):
        """Disconnect from OBS WebSocket server"""
        pass

    @abstractmethod
    async def call(self, request_type: str, request_data: Optional[Dict] = None) -> Optional[Dict]:
        """Send request and wait for response"""
        pass

    @abstractmethod
    async def emit(self, request_type: str, request_data: Optional[Dict] = None) -> bool:
        """Send fire-and-forget request"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected and authenticated"""
        pass


class SimpleOBSWSAdapter(OBSWebSocketAdapter):
    """
    Adapter using IRLToolkit's simpleobsws library

    Provides cleaner async interface with built-in protocol handling.
    """

    def __init__(self, host: str, port: int, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.password = password
        self._ws = None
        self._connected = False

        logger.info(f"SimpleOBSWS Adapter initialized (host={host}:{port})")

    async def connect(self) -> bool:
        """Connect to OBS using simpleobsws"""
        try:
            import simpleobsws

            # Build connection URL
            url = f"ws://{self.host}:{self.port}"

            # Create WebSocket client
            self._ws = simpleobsws.WebSocketClient(
                url=url,
                password=self.password
            )

            # Connect and authenticate
            await self._ws.connect()
            await self._ws.wait_until_identified()

            self._connected = True
            logger.info("SimpleOBSWS connected and authenticated")
            return True

        except ImportError:
            logger.error("simpleobsws library not installed. Install with: pip install simpleobsws")
            return False
        except Exception as e:
            logger.error(f"SimpleOBSWS connection failed: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """Disconnect from OBS"""
        if self._ws:
            try:
                await self._ws.disconnect()
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self._ws = None
                self._connected = False
                logger.info("SimpleOBSWS disconnected")

    async def call(self, request_type: str, request_data: Optional[Dict] = None) -> Optional[Dict]:
        """Send request and wait for response"""
        if not self._connected or not self._ws:
            logger.warning(f"Cannot call '{request_type}': Not connected")
            return None

        try:
            import simpleobsws

            request = simpleobsws.Request(request_type, request_data)
            response = await self._ws.call(request)

            if response.ok():
                return response.responseData
            else:
                logger.warning(f"OBS request '{request_type}' failed: {response.requestStatus}")
                return None

        except Exception as e:
            logger.error(f"SimpleOBSWS call '{request_type}' error: {e}")
            return None

    async def emit(self, request_type: str, request_data: Optional[Dict] = None) -> bool:
        """Send fire-and-forget request"""
        if not self._connected or not self._ws:
            logger.warning(f"Cannot emit '{request_type}': Not connected")
            return False

        try:
            import simpleobsws

            request = simpleobsws.Request(request_type, request_data)
            await self._ws.emit(request)
            return True

        except Exception as e:
            logger.error(f"SimpleOBSWS emit '{request_type}' error: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if connected"""
        return self._connected and self._ws is not None


def create_obs_adapter(
    host: str = None,
    port: int = None,
    password: str = None
) -> Optional[OBSWebSocketAdapter]:
    """
    Factory function to create appropriate OBS WebSocket adapter

    Uses OBS_LIBRARY setting to determine which implementation to use:
    - "simpleobsws": Uses IRLToolkit's simpleobsws library
    - Default: Returns None (use native implementation in obs_controller.py)

    Args:
        host: OBS WebSocket host
        port: OBS WebSocket port
        password: OBS WebSocket password

    Returns:
        OBSWebSocketAdapter instance or None for native implementation
    """
    host = host or settings.obs_host
    port = port or settings.obs_port
    password = password or settings.obs_password
    library = settings.obs_library.lower()

    if library == "simpleobsws":
        try:
            import simpleobsws
            logger.info(f"Using simpleobsws adapter (version {simpleobsws.__version__})")
            return SimpleOBSWSAdapter(host, port, password)
        except ImportError:
            logger.warning("simpleobsws not installed, falling back to native implementation")
            return None
    else:
        # Return None to indicate native implementation should be used
        logger.info(f"Using native OBS WebSocket implementation (obs_library={library})")
        return None


def get_library_info() -> Dict[str, Any]:
    """
    Get information about available OBS WebSocket libraries

    Returns:
        Dictionary with library availability and configuration
    """
    info = {
        "configured_library": settings.obs_library,
        "native_available": True,  # Always available (uses websockets)
        "simpleobsws_available": False,
        "simpleobsws_version": None
    }

    try:
        import simpleobsws
        info["simpleobsws_available"] = True
        info["simpleobsws_version"] = simpleobsws.__version__
    except ImportError:
        pass

    return info
