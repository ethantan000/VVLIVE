"""
OBS HTTP Bridge Client
IRLToolkit obs-websocket-http integration for VVLIVE

This module provides HTTP-based OBS control via the obs-websocket-http
companion service. Enables external integrations without WebSocket connections.

Only active when FEATURE_OBS_HTTP_BRIDGE is enabled.
"""

import logging
from typing import Optional, Dict, Any

import httpx

from .config import settings
from .models import QualityState

logger = logging.getLogger(__name__)


class OBSHTTPBridgeClient:
    """
    HTTP client for obs-websocket-http service

    Provides REST endpoints for OBS control:
    - /emit/{requestType} - Fire-and-forget requests
    - /call/{requestType} - Request with response

    All methods are non-blocking and fail gracefully.
    """

    def __init__(self):
        self.enabled = settings.feature_obs_http_bridge
        self.host = settings.obs_http_bridge_host
        self.port = settings.obs_http_bridge_port
        self.auth_key = settings.obs_http_bridge_auth_key
        self.timeout = settings.obs_http_bridge_timeout

        self.base_url = f"http://{self.host}:{self.port}"
        self._client: Optional[httpx.AsyncClient] = None

        # Scene mapping from quality states (same as OBSController)
        self.scene_map = {
            QualityState.HIGH: settings.obs_scene_high,
            QualityState.MEDIUM: settings.obs_scene_medium,
            QualityState.LOW: settings.obs_scene_low,
            QualityState.VERY_LOW: settings.obs_scene_very_low,
            QualityState.ERROR: settings.obs_scene_error,
            QualityState.RECOVERY: settings.obs_scene_medium,
        }

        logger.info(f"OBS HTTP Bridge Client initialized (enabled={self.enabled})")

    async def start(self):
        """Initialize HTTP client"""
        if not self.enabled:
            logger.debug("OBS HTTP Bridge disabled, skipping initialization")
            return

        headers = {}
        if self.auth_key:
            headers["Authorization"] = f"Bearer {self.auth_key}"

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout
        )
        logger.info(f"OBS HTTP Bridge Client started (base_url={self.base_url})")

    async def stop(self):
        """Cleanup HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("OBS HTTP Bridge Client stopped")

    async def _emit(self, request_type: str, request_data: Optional[Dict] = None) -> bool:
        """
        Send fire-and-forget request to OBS via HTTP bridge

        Args:
            request_type: OBS request type
            request_data: Optional request parameters

        Returns:
            True if request accepted, False on error
        """
        if not self.enabled or not self._client:
            return False

        try:
            url = f"/emit/{request_type}"
            if request_data:
                response = await self._client.post(url, json=request_data)
            else:
                response = await self._client.get(url)

            if response.status_code == 200:
                logger.debug(f"OBS HTTP emit '{request_type}' accepted")
                return True
            else:
                logger.warning(f"OBS HTTP emit '{request_type}' failed: {response.status_code}")
                return False

        except httpx.TimeoutException:
            logger.warning(f"OBS HTTP emit '{request_type}' timed out")
            return False
        except httpx.RequestError as e:
            logger.error(f"OBS HTTP emit '{request_type}' error: {e}")
            return False

    async def _call(self, request_type: str, request_data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Send request to OBS and wait for response via HTTP bridge

        Args:
            request_type: OBS request type
            request_data: Optional request parameters

        Returns:
            Response data or None on error
        """
        if not self.enabled or not self._client:
            return None

        try:
            url = f"/call/{request_type}"
            if request_data:
                response = await self._client.post(url, json=request_data)
            else:
                response = await self._client.get(url)

            if response.status_code == 200:
                data = response.json()
                logger.debug(f"OBS HTTP call '{request_type}' successful")
                return data
            else:
                logger.warning(f"OBS HTTP call '{request_type}' failed: {response.status_code}")
                return None

        except httpx.TimeoutException:
            logger.warning(f"OBS HTTP call '{request_type}' timed out")
            return None
        except httpx.RequestError as e:
            logger.error(f"OBS HTTP call '{request_type}' error: {e}")
            return None

    async def switch_scene(self, scene_name: str) -> bool:
        """
        Switch to specified OBS scene via HTTP bridge

        Args:
            scene_name: Name of scene to switch to

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("OBS HTTP Bridge disabled, skipping scene switch")
            return False

        logger.info(f"Switching OBS scene via HTTP bridge: {scene_name}")
        return await self._emit("SetCurrentProgramScene", {"sceneName": scene_name})

    async def switch_scene_for_quality(self, quality_state: QualityState) -> bool:
        """
        Switch scene based on quality state

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

    async def get_current_scene(self) -> Optional[str]:
        """
        Get current OBS scene name

        Returns:
            Scene name or None on error
        """
        response = await self._call("GetCurrentProgramScene")
        if response:
            return response.get("currentProgramSceneName")
        return None

    async def check_health(self) -> Dict[str, Any]:
        """
        Check OBS HTTP bridge health

        Returns:
            Health status dictionary
        """
        if not self.enabled:
            return {
                "enabled": False,
                "status": "disabled",
                "message": "OBS HTTP Bridge not enabled"
            }

        if not self._client:
            return {
                "enabled": True,
                "status": "not_started",
                "message": "HTTP client not initialized"
            }

        try:
            # Try to get version info as health check
            response = await self._call("GetVersion")
            if response:
                return {
                    "enabled": True,
                    "status": "healthy",
                    "obs_version": response.get("obsVersion"),
                    "websocket_version": response.get("obsWebSocketVersion"),
                    "bridge_url": self.base_url
                }
            else:
                return {
                    "enabled": True,
                    "status": "unhealthy",
                    "message": "Failed to get OBS version",
                    "bridge_url": self.base_url
                }
        except Exception as e:
            return {
                "enabled": True,
                "status": "error",
                "message": str(e),
                "bridge_url": self.base_url
            }

    def get_status(self) -> Dict[str, Any]:
        """Get current client status (synchronous)"""
        return {
            "enabled": self.enabled,
            "bridge_url": self.base_url if self.enabled else None,
            "client_active": self._client is not None,
            "auth_configured": self.auth_key is not None
        }
