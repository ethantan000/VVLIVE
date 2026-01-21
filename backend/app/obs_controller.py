"""
OBS WebSocket Controller
Based on NOALBS OBS integration patterns, adapted for VVLIVE

This module provides OBS Studio control via WebSocket v5 protocol.
Only active when FEATURE_OBS_INTEGRATION is enabled.
"""

import asyncio
import json
import logging
import hashlib
import base64
from typing import Optional, Dict, Any
from enum import Enum

import websockets
from websockets.client import WebSocketClientProtocol

from .config import settings
from .models import QualityState

logger = logging.getLogger(__name__)


class OBSConnectionState(Enum):
    """OBS connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    ERROR = "error"


class OBSController:
    """
    OBS WebSocket v5 controller

    Manages WebSocket connection to OBS Studio and provides scene switching.
    Implements NOALBS-style reconnection logic and error handling.
    """

    def __init__(self):
        self.ws: Optional[WebSocketClientProtocol] = None
        self.state: OBSConnectionState = OBSConnectionState.DISCONNECTED
        self.current_scene: Optional[str] = None
        self.message_id: int = 1
        self.reconnect_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None

        # Configuration
        self.host = settings.obs_host
        self.port = settings.obs_port
        self.password = settings.obs_password
        self.enabled = settings.feature_obs_integration

        # Scene mapping from quality states
        self.scene_map = {
            QualityState.HIGH: settings.obs_scene_high,
            QualityState.MEDIUM: settings.obs_scene_medium,
            QualityState.LOW: settings.obs_scene_low,
            QualityState.VERY_LOW: settings.obs_scene_very_low,
            QualityState.ERROR: settings.obs_scene_error,
            QualityState.RECOVERY: settings.obs_scene_medium,  # Use MEDIUM during recovery
        }

        logger.info(f"OBS Controller initialized (enabled={self.enabled})")

    async def connect(self) -> bool:
        """
        Connect to OBS WebSocket server

        Returns:
            True if connection successful, False otherwise
        """
        if not self.enabled:
            logger.debug("OBS integration disabled, skipping connection")
            return False

        if self.state in [OBSConnectionState.CONNECTED, OBSConnectionState.AUTHENTICATED]:
            logger.debug("Already connected to OBS")
            return True

        try:
            self.state = OBSConnectionState.CONNECTING
            ws_url = f"ws://{self.host}:{self.port}"

            logger.info(f"Connecting to OBS at {ws_url}...")
            self.ws = await websockets.connect(ws_url)
            self.state = OBSConnectionState.CONNECTED

            # Handle OBS WebSocket v5 Hello message
            hello_msg = await self.ws.recv()
            hello_data = json.loads(hello_msg)

            if hello_data.get("op") != 0:  # OpCode 0 = Hello
                raise Exception(f"Expected Hello message, got opcode {hello_data.get('op')}")

            # Authenticate if password is set
            if self.password:
                auth_success = await self._authenticate(hello_data)
                if not auth_success:
                    raise Exception("Authentication failed")

            self.state = OBSConnectionState.AUTHENTICATED

            # Get current scene
            await self._update_current_scene()

            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            logger.info("Successfully connected to OBS")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to OBS: {e}")
            self.state = OBSConnectionState.ERROR
            await self.disconnect()

            # Schedule reconnection
            if not self.reconnect_task or self.reconnect_task.done():
                self.reconnect_task = asyncio.create_task(self._reconnect_loop())

            return False

    async def _authenticate(self, hello_data: Dict) -> bool:
        """
        Authenticate with OBS using WebSocket v5 challenge-response

        Args:
            hello_data: Hello message from OBS

        Returns:
            True if authentication successful
        """
        try:
            auth_data = hello_data["d"]["authentication"]
            challenge = auth_data["challenge"]
            salt = auth_data["salt"]

            # OBS WebSocket v5 authentication:
            # secret = SHA256(password + salt)
            # auth = SHA256(secret + challenge)
            secret = hashlib.sha256((self.password + salt).encode()).digest()
            auth = base64.b64encode(
                hashlib.sha256(secret + challenge.encode()).digest()
            ).decode()

            # Send Identify message (OpCode 1)
            identify_msg = {
                "op": 1,
                "d": {
                    "rpcVersion": 1,
                    "authentication": auth
                }
            }

            await self.ws.send(json.dumps(identify_msg))

            # Wait for Identified message (OpCode 2)
            response = await self.ws.recv()
            response_data = json.loads(response)

            if response_data.get("op") == 2:
                logger.info("OBS authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {response_data}")
                return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    async def disconnect(self):
        """Disconnect from OBS WebSocket"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None

        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None

        self.state = OBSConnectionState.DISCONNECTED
        logger.info("Disconnected from OBS")

    async def _reconnect_loop(self):
        """Auto-reconnection loop (NOALBS pattern)"""
        reconnect_delay = 5  # seconds
        max_delay = 60

        while self.enabled and self.state != OBSConnectionState.AUTHENTICATED:
            logger.info(f"Attempting to reconnect to OBS in {reconnect_delay}s...")
            await asyncio.sleep(reconnect_delay)

            success = await self.connect()
            if success:
                logger.info("Reconnection successful")
                return

            # Exponential backoff
            reconnect_delay = min(reconnect_delay * 2, max_delay)

    async def _heartbeat_loop(self):
        """Send periodic heartbeat to keep connection alive"""
        try:
            while self.state == OBSConnectionState.AUTHENTICATED:
                await asyncio.sleep(10)  # Heartbeat every 10 seconds

                # Request current scene as heartbeat
                try:
                    await self._update_current_scene()
                except Exception as e:
                    logger.warning(f"Heartbeat failed: {e}")
                    # Trigger reconnection
                    await self.disconnect()
                    if not self.reconnect_task or self.reconnect_task.done():
                        self.reconnect_task = asyncio.create_task(self._reconnect_loop())
                    break
        except asyncio.CancelledError:
            logger.debug("Heartbeat cancelled")

    async def _send_request(self, request_type: str, request_data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Send request to OBS and wait for response

        Args:
            request_type: OBS request type
            request_data: Optional request parameters

        Returns:
            Response data or None if failed
        """
        if self.state != OBSConnectionState.AUTHENTICATED:
            logger.warning(f"Cannot send request '{request_type}': Not authenticated")
            return None

        try:
            msg_id = str(self.message_id)
            self.message_id += 1

            # OpCode 6 = Request
            request_msg = {
                "op": 6,
                "d": {
                    "requestType": request_type,
                    "requestId": msg_id
                }
            }

            if request_data:
                request_msg["d"]["requestData"] = request_data

            await self.ws.send(json.dumps(request_msg))

            # Wait for response (OpCode 7 = RequestResponse)
            response = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
            response_data = json.loads(response)

            if response_data.get("op") == 7 and response_data["d"]["requestId"] == msg_id:
                if response_data["d"]["requestStatus"]["result"]:
                    return response_data["d"].get("responseData")
                else:
                    logger.error(f"Request failed: {response_data['d']['requestStatus']}")
                    return None

            return None

        except asyncio.TimeoutError:
            logger.error(f"Request '{request_type}' timed out")
            return None
        except Exception as e:
            logger.error(f"Request '{request_type}' failed: {e}")
            return None

    async def _update_current_scene(self):
        """Update cached current scene name"""
        response = await self._send_request("GetCurrentProgramScene")
        if response:
            self.current_scene = response.get("currentProgramSceneName")
            logger.debug(f"Current OBS scene: {self.current_scene}")

    async def switch_scene(self, scene_name: str) -> bool:
        """
        Switch to specified OBS scene

        Args:
            scene_name: Name of scene to switch to

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("OBS integration disabled, skipping scene switch")
            return False

        if self.state != OBSConnectionState.AUTHENTICATED:
            logger.warning(f"Cannot switch scene: Not connected to OBS")
            return False

        if self.current_scene == scene_name:
            logger.debug(f"Already on scene '{scene_name}', skipping switch")
            return True

        try:
            logger.info(f"Switching OBS scene: {self.current_scene} → {scene_name}")

            response = await self._send_request("SetCurrentProgramScene", {
                "sceneName": scene_name
            })

            if response is not None:
                self.current_scene = scene_name
                logger.info(f"Scene switched successfully to '{scene_name}'")
                return True
            else:
                logger.error(f"Failed to switch to scene '{scene_name}'")
                return False

        except Exception as e:
            logger.error(f"Scene switch error: {e}")
            return False

    async def switch_scene_for_quality(self, quality_state: QualityState) -> bool:
        """
        Switch scene based on quality state (NOALBS pattern)

        Args:
            quality_state: Quality state to map to scene

        Returns:
            True if successful
        """
        scene_name = self.scene_map.get(quality_state)

        if not scene_name:
            logger.warning(f"No scene mapped for quality state {quality_state.value}")
            return False

        return await self.switch_scene(scene_name)

    async def emergency_mode(self) -> bool:
        """
        Activate emergency mode scene

        Returns:
            True if successful
        """
        return await self.switch_scene(settings.obs_scene_emergency)

    def is_connected(self) -> bool:
        """Check if connected and authenticated"""
        return self.state == OBSConnectionState.AUTHENTICATED

    def get_status(self) -> Dict[str, Any]:
        """Get current OBS controller status"""
        return {
            "enabled": self.enabled,
            "state": self.state.value,
            "connected": self.is_connected(),
            "current_scene": self.current_scene,
            "host": f"{self.host}:{self.port}"
        }
