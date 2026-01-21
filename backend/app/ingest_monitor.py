"""
Ingest Server Stats Monitor
Based on NOALBS ingest monitoring patterns

Polls streaming server stats endpoints (nginx-rtmp, SRT, etc.) to verify
actual received bitrate at the ingest point. Complements MPTCP metrics.
"""

import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

import httpx

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class IngestStats:
    """Ingest server statistics"""
    bitrate_kbps: float
    connection_active: bool
    rtt_ms: Optional[float] = None
    packet_loss_percent: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class IngestMonitor:
    """
    Ingest server stats monitor

    Polls streaming server statistics endpoints to get ground truth
    about received bitrate. Supports multiple server types (NOALBS pattern).
    """

    def __init__(self):
        self.enabled = settings.feature_ingest_monitoring
        self.stats_url = settings.ingest_stats_url
        self.stream_key = settings.ingest_stream_key
        self.poll_interval = settings.ingest_stats_poll_interval
        self.server_type = settings.ingest_server_type.lower()

        self.last_stats: Optional[IngestStats] = None
        self.poll_task: Optional[asyncio.Task] = None
        self.http_client: Optional[httpx.AsyncClient] = None

        self.poll_failures = 0
        self.total_polls = 0

        logger.info(f"Ingest Monitor initialized (enabled={self.enabled}, type={self.server_type})")

    async def start(self):
        """Start monitoring ingest stats"""
        if not self.enabled:
            logger.debug("Ingest monitoring disabled")
            return

        if self.poll_task and not self.poll_task.done():
            logger.warning("Ingest monitoring already running")
            return

        logger.info(f"Starting ingest monitoring (interval={self.poll_interval}s)")

        # Create HTTP client
        self.http_client = httpx.AsyncClient(timeout=5.0)

        # Start polling loop
        self.poll_task = asyncio.create_task(self._poll_loop())

    async def stop(self):
        """Stop monitoring"""
        if self.poll_task:
            self.poll_task.cancel()
            try:
                await self.poll_task
            except asyncio.CancelledError:
                pass
            self.poll_task = None

        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None

        logger.info("Ingest monitoring stopped")

    async def _poll_loop(self):
        """Continuous polling loop"""
        try:
            while True:
                await self._poll_stats()
                await asyncio.sleep(self.poll_interval)
        except asyncio.CancelledError:
            logger.debug("Poll loop cancelled")
        except Exception as e:
            logger.error(f"Poll loop error: {e}")

    async def _poll_stats(self):
        """Poll stats endpoint once"""
        self.total_polls += 1

        try:
            if self.server_type == "nginx":
                stats = await self._poll_nginx_rtmp()
            elif self.server_type == "srt":
                stats = await self._poll_srt()
            elif self.server_type == "node-media-server":
                stats = await self._poll_node_media()
            else:
                logger.warning(f"Unsupported server type: {self.server_type}")
                return

            if stats:
                self.last_stats = stats
                self.poll_failures = 0
                logger.debug(
                    f"Ingest stats: {stats.bitrate_kbps:.1f} kbps, "
                    f"active={stats.connection_active}"
                )
            else:
                self.poll_failures += 1
                logger.debug(f"Failed to get ingest stats (failures={self.poll_failures})")

        except Exception as e:
            self.poll_failures += 1
            logger.error(f"Stats polling error: {e}")

    async def _poll_nginx_rtmp(self) -> Optional[IngestStats]:
        """
        Poll nginx-rtmp stats endpoint (NOALBS pattern)

        nginx-rtmp stats format:
        <rtmp>
          <server>
            <application>
              <live>
                <stream>
                  <name>stream_key</name>
                  <bw_in>bytes/s</bw_in>
                  <bw_out>bytes/s</bw_out>
                </stream>
              </live>
            </application>
          </server>
        </rtmp>
        """
        try:
            response = await self.http_client.get(self.stats_url)
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.text)

            # Find our stream
            for stream in root.findall(".//stream"):
                name_elem = stream.find("name")
                if name_elem is not None and name_elem.text == self.stream_key:
                    # Found our stream
                    bw_in_elem = stream.find("bw_in")
                    if bw_in_elem is not None and bw_in_elem.text:
                        # Convert bytes/s to kbps
                        bytes_per_sec = float(bw_in_elem.text)
                        bitrate_kbps = (bytes_per_sec * 8) / 1000

                        return IngestStats(
                            bitrate_kbps=bitrate_kbps,
                            connection_active=True
                        )

            # Stream not found = not active
            return IngestStats(
                bitrate_kbps=0.0,
                connection_active=False
            )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error polling nginx stats: {e}")
            return None
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
            return None

    async def _poll_srt(self) -> Optional[IngestStats]:
        """
        Poll SRT stats endpoint

        SRT stats typically provided as JSON with RTT and bitrate
        """
        try:
            response = await self.http_client.get(self.stats_url)
            response.raise_for_status()

            data = response.json()

            # Extract stats (format varies by SRT implementation)
            # This is a generic implementation - adjust for specific server
            bitrate_kbps = data.get("bitrate", 0) / 1000  # Assuming bps
            rtt_ms = data.get("rtt", 0)
            active = data.get("connected", False)

            return IngestStats(
                bitrate_kbps=bitrate_kbps,
                connection_active=active,
                rtt_ms=rtt_ms
            )

        except Exception as e:
            logger.error(f"SRT stats error: {e}")
            return None

    async def _poll_node_media(self) -> Optional[IngestStats]:
        """
        Poll Node-Media-Server stats endpoint

        Format: JSON with streams array
        """
        try:
            response = await self.http_client.get(f"{self.stats_url}/api/streams")
            response.raise_for_status()

            data = response.json()

            # Find our stream in the streams list
            for stream in data.get("streams", []):
                if stream.get("app") == self.stream_key.split("/")[0]:
                    # Calculate bitrate from video + audio
                    video_kbps = stream.get("video", {}).get("bitrate", 0) / 1000
                    audio_kbps = stream.get("audio", {}).get("bitrate", 0) / 1000
                    total_kbps = video_kbps + audio_kbps

                    return IngestStats(
                        bitrate_kbps=total_kbps,
                        connection_active=True
                    )

            # Stream not found
            return IngestStats(
                bitrate_kbps=0.0,
                connection_active=False
            )

        except Exception as e:
            logger.error(f"Node-Media-Server stats error: {e}")
            return None

    def get_latest_stats(self) -> Optional[IngestStats]:
        """Get most recent stats"""
        return self.last_stats

    def get_bitrate_kbps(self) -> float:
        """Get current bitrate in kbps"""
        if self.last_stats:
            return self.last_stats.bitrate_kbps
        return 0.0

    def is_connection_active(self) -> bool:
        """Check if stream connection is active"""
        if self.last_stats:
            return self.last_stats.connection_active
        return False

    def get_health(self) -> Dict[str, Any]:
        """Get monitor health status"""
        success_rate = 0.0
        if self.total_polls > 0:
            success_rate = ((self.total_polls - self.poll_failures) / self.total_polls) * 100

        return {
            "enabled": self.enabled,
            "server_type": self.server_type,
            "stats_url": self.stats_url,
            "total_polls": self.total_polls,
            "poll_failures": self.poll_failures,
            "success_rate_percent": round(success_rate, 1),
            "last_stats": {
                "bitrate_kbps": self.get_bitrate_kbps(),
                "connection_active": self.is_connection_active(),
                "timestamp": self.last_stats.timestamp.isoformat() if self.last_stats else None
            } if self.last_stats else None
        }
