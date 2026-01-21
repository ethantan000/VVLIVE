"""
RTMP Authentication Monitor
IRLToolkit nginx-rtmp-auth integration for VVLIVE

This module provides health monitoring for the nginx-rtmp-auth service.
The actual authentication happens at the nginx level - this module only
monitors the auth service status for dashboard visibility.

Only active when FEATURE_RTMP_AUTH is enabled.
"""

import logging
from typing import Dict, Any, Optional

import httpx

from .config import settings

logger = logging.getLogger(__name__)


class RTMPAuthMonitor:
    """
    Monitor for nginx-rtmp-auth service health

    Provides visibility into RTMP ingest authentication status.
    Does not perform authentication - that's handled by nginx.
    """

    def __init__(self):
        self.enabled = settings.feature_rtmp_auth
        self.service_url = settings.rtmp_auth_service_url
        self._http_client: Optional[httpx.AsyncClient] = None
        self._last_health_check: Optional[Dict[str, Any]] = None

        logger.info(f"RTMP Auth Monitor initialized (enabled={self.enabled})")

    async def start(self):
        """Initialize HTTP client for health checks"""
        if not self.enabled:
            logger.debug("RTMP Auth disabled, skipping start")
            return

        if self.service_url:
            self._http_client = httpx.AsyncClient(timeout=5.0)
            logger.info(f"RTMP Auth Monitor started (service_url={self.service_url})")
        else:
            logger.info("RTMP Auth Monitor started (no service_url configured - nginx-level only)")

    async def stop(self):
        """Cleanup HTTP client"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
            logger.info("RTMP Auth Monitor stopped")

    async def check_health(self) -> Dict[str, Any]:
        """
        Check health of nginx-rtmp-auth service

        Returns:
            Health status dictionary
        """
        if not self.enabled:
            return {
                "enabled": False,
                "status": "disabled",
                "message": "RTMP authentication not enabled"
            }

        if not self.service_url:
            return {
                "enabled": True,
                "status": "nginx_only",
                "message": "RTMP auth configured at nginx level (no health endpoint)"
            }

        if not self._http_client:
            return {
                "enabled": True,
                "status": "not_started",
                "message": "Monitor not initialized"
            }

        try:
            # Try to reach the auth service health endpoint
            response = await self._http_client.get(self.service_url)

            if response.status_code == 200:
                self._last_health_check = {
                    "enabled": True,
                    "status": "healthy",
                    "service_url": self.service_url,
                    "response_code": response.status_code
                }
            else:
                self._last_health_check = {
                    "enabled": True,
                    "status": "unhealthy",
                    "service_url": self.service_url,
                    "response_code": response.status_code,
                    "message": f"Unexpected response code: {response.status_code}"
                }

        except httpx.TimeoutException:
            self._last_health_check = {
                "enabled": True,
                "status": "timeout",
                "service_url": self.service_url,
                "message": "Health check timed out"
            }
        except httpx.RequestError as e:
            self._last_health_check = {
                "enabled": True,
                "status": "error",
                "service_url": self.service_url,
                "message": str(e)
            }

        return self._last_health_check

    def get_status(self) -> Dict[str, Any]:
        """Get current monitor status (synchronous)"""
        return {
            "enabled": self.enabled,
            "service_url": self.service_url or "not_configured",
            "last_check": self._last_health_check,
            "note": "Authentication performed by nginx-rtmp-auth at nginx level"
        }

    @staticmethod
    def get_nginx_config_example() -> str:
        """
        Get example nginx-rtmp configuration for auth integration

        Returns:
            Example nginx config snippet
        """
        return """
# nginx-rtmp configuration example for VVLIVE with nginx-rtmp-auth
# Add this to your nginx.conf rtmp block

rtmp {
    server {
        listen 1935;
        chunk_size 4096;

        application live {
            live on;
            record off;

            # nginx-rtmp-auth integration
            on_publish http://127.0.0.1:8080/auth;

            # Optional: notify on publish done
            # on_publish_done http://127.0.0.1:8080/auth/done;

            # Push to local HLS/DASH or relay
            # push rtmp://localhost/hls;
        }
    }
}
"""

    @staticmethod
    def get_auth_config_example() -> str:
        """
        Get example authentication.json configuration

        Returns:
            Example auth config
        """
        return """{
    "live": {
        "allowed_keys": [
            "your-secret-stream-key-1",
            "backup-stream-key-2"
        ]
    }
}"""
