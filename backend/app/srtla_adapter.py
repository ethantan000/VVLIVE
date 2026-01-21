"""
SRTLA Metrics Adapter
IRLToolkit srtla integration for VVLIVE

This module reads metrics from SRTLA receiver and normalizes them
to VVLIVE's NetworkMetrics format for consumption by the state machine.

Supports multiple metrics sources:
- socket: Direct socket connection to srtla_rec
- file: Reading from stats file
- api: HTTP API endpoint for stats

Only active when FEATURE_SRTLA_TRANSPORT is enabled.
"""

import asyncio
import json
import logging
import struct
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from pathlib import Path

import httpx

from .config import settings
from .models import NetworkMetrics

logger = logging.getLogger(__name__)


@dataclass
class SRTLALinkStats:
    """Statistics for a single SRTLA link"""
    link_id: int
    source_ip: str
    packets_sent: int
    packets_acked: int
    packets_lost: int
    rtt_ms: float
    bandwidth_bps: float
    window_size: int
    active: bool


@dataclass
class SRTLAReceiverStats:
    """Aggregated SRTLA receiver statistics"""
    total_packets_received: int
    total_packets_reordered: int
    total_bandwidth_bps: float
    avg_rtt_ms: float
    min_rtt_ms: float
    max_rtt_ms: float
    packet_loss_percent: float
    active_links: int
    links: List[SRTLALinkStats]


class SRTLAMetricsAdapter:
    """
    Adapter for reading SRTLA receiver metrics

    Normalizes SRTLA-specific stats to VVLIVE's NetworkMetrics format,
    allowing the state machine to consume transport metrics from either
    MPTCP or SRTLA without modification.
    """

    def __init__(self):
        self.enabled = settings.feature_srtla_transport
        self.metrics_source = settings.srtla_metrics_source
        self.stats_endpoint = settings.srtla_stats_endpoint
        self.receiver_port = settings.srtla_receiver_port
        self.transport_mode = settings.transport_mode

        self._http_client: Optional[httpx.AsyncClient] = None
        self._polling_task: Optional[asyncio.Task] = None
        self._latest_stats: Optional[SRTLAReceiverStats] = None
        self._last_update: float = 0

        logger.info(
            f"SRTLA Metrics Adapter initialized "
            f"(enabled={self.enabled}, source={self.metrics_source}, mode={self.transport_mode})"
        )

    async def start(self):
        """Start metrics collection"""
        if not self.enabled:
            logger.debug("SRTLA transport disabled, skipping start")
            return

        if self.metrics_source == "api" and self.stats_endpoint:
            self._http_client = httpx.AsyncClient(timeout=5.0)

        # Start background polling
        self._polling_task = asyncio.create_task(self._poll_loop())
        logger.info("SRTLA Metrics Adapter started")

    async def stop(self):
        """Stop metrics collection"""
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
            self._polling_task = None

        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        logger.info("SRTLA Metrics Adapter stopped")

    async def _poll_loop(self):
        """Background loop for polling metrics"""
        poll_interval = settings.ingest_stats_poll_interval  # Reuse existing setting

        while True:
            try:
                await self._fetch_metrics()
                await asyncio.sleep(poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"SRTLA metrics poll error: {e}")
                await asyncio.sleep(poll_interval)

    async def _fetch_metrics(self):
        """Fetch metrics from configured source"""
        try:
            if self.metrics_source == "api":
                stats = await self._fetch_from_api()
            elif self.metrics_source == "file":
                stats = await self._fetch_from_file()
            elif self.metrics_source == "socket":
                stats = await self._fetch_from_socket()
            else:
                logger.warning(f"Unknown metrics source: {self.metrics_source}")
                return

            if stats:
                self._latest_stats = stats
                self._last_update = asyncio.get_event_loop().time()
                logger.debug(f"SRTLA metrics updated: {stats.active_links} links, {stats.total_bandwidth_bps/1e6:.2f} Mbps")

        except Exception as e:
            logger.error(f"Failed to fetch SRTLA metrics: {e}")

    async def _fetch_from_api(self) -> Optional[SRTLAReceiverStats]:
        """Fetch metrics from HTTP API endpoint"""
        if not self._http_client or not self.stats_endpoint:
            return None

        try:
            response = await self._http_client.get(self.stats_endpoint)
            if response.status_code == 200:
                data = response.json()
                return self._parse_api_response(data)
        except Exception as e:
            logger.error(f"SRTLA API fetch error: {e}")
        return None

    async def _fetch_from_file(self) -> Optional[SRTLAReceiverStats]:
        """Fetch metrics from stats file"""
        stats_file = Path(f"/tmp/srtla_stats_{self.receiver_port}.json")

        if not stats_file.exists():
            logger.debug(f"SRTLA stats file not found: {stats_file}")
            return None

        try:
            content = stats_file.read_text()
            data = json.loads(content)
            return self._parse_api_response(data)
        except Exception as e:
            logger.error(f"SRTLA file read error: {e}")
        return None

    async def _fetch_from_socket(self) -> Optional[SRTLAReceiverStats]:
        """Fetch metrics from SRTLA receiver socket (if available)"""
        # SRTLA doesn't have a built-in stats socket, but some forks do
        # This is a placeholder for future integration with custom srtla builds
        logger.debug("Socket-based SRTLA metrics not yet implemented")
        return None

    def _parse_api_response(self, data: Dict[str, Any]) -> SRTLAReceiverStats:
        """Parse API/file response into SRTLAReceiverStats"""
        links = []
        for link_data in data.get("links", []):
            link = SRTLALinkStats(
                link_id=link_data.get("id", 0),
                source_ip=link_data.get("source_ip", ""),
                packets_sent=link_data.get("packets_sent", 0),
                packets_acked=link_data.get("packets_acked", 0),
                packets_lost=link_data.get("packets_lost", 0),
                rtt_ms=link_data.get("rtt_ms", 0),
                bandwidth_bps=link_data.get("bandwidth_bps", 0),
                window_size=link_data.get("window_size", 0),
                active=link_data.get("active", True)
            )
            links.append(link)

        active_links = len([l for l in links if l.active])
        total_bandwidth = sum(l.bandwidth_bps for l in links if l.active)
        rtts = [l.rtt_ms for l in links if l.active and l.rtt_ms > 0]

        total_sent = sum(l.packets_sent for l in links)
        total_lost = sum(l.packets_lost for l in links)
        loss_percent = (total_lost / total_sent * 100) if total_sent > 0 else 0

        return SRTLAReceiverStats(
            total_packets_received=data.get("total_packets", 0),
            total_packets_reordered=data.get("packets_reordered", 0),
            total_bandwidth_bps=total_bandwidth,
            avg_rtt_ms=sum(rtts) / len(rtts) if rtts else 0,
            min_rtt_ms=min(rtts) if rtts else 0,
            max_rtt_ms=max(rtts) if rtts else 0,
            packet_loss_percent=loss_percent,
            active_links=active_links,
            links=links
        )

    def get_network_metrics(self) -> Optional[NetworkMetrics]:
        """
        Get SRTLA metrics normalized to VVLIVE NetworkMetrics format

        This allows the state machine to consume SRTLA metrics
        identically to MPTCP metrics.

        Returns:
            NetworkMetrics instance or None if no data available
        """
        if not self.enabled or not self._latest_stats:
            return None

        stats = self._latest_stats
        return NetworkMetrics(
            total_bandwidth_bps=stats.total_bandwidth_bps,
            packet_loss_percent=stats.packet_loss_percent,
            min_rtt_ms=stats.min_rtt_ms,
            max_rtt_ms=stats.max_rtt_ms,
            active_subflows=stats.active_links  # Map links to subflows
        )

    def get_raw_stats(self) -> Optional[Dict[str, Any]]:
        """Get raw SRTLA statistics for detailed monitoring"""
        if not self._latest_stats:
            return None

        stats = self._latest_stats
        return {
            "total_packets_received": stats.total_packets_received,
            "total_packets_reordered": stats.total_packets_reordered,
            "total_bandwidth_mbps": stats.total_bandwidth_bps / 1_000_000,
            "avg_rtt_ms": stats.avg_rtt_ms,
            "min_rtt_ms": stats.min_rtt_ms,
            "max_rtt_ms": stats.max_rtt_ms,
            "packet_loss_percent": stats.packet_loss_percent,
            "active_links": stats.active_links,
            "links": [
                {
                    "id": link.link_id,
                    "source_ip": link.source_ip,
                    "bandwidth_mbps": link.bandwidth_bps / 1_000_000,
                    "rtt_ms": link.rtt_ms,
                    "packets_lost": link.packets_lost,
                    "active": link.active
                }
                for link in stats.links
            ]
        }

    def get_status(self) -> Dict[str, Any]:
        """Get adapter status"""
        return {
            "enabled": self.enabled,
            "transport_mode": self.transport_mode,
            "metrics_source": self.metrics_source,
            "receiver_port": self.receiver_port,
            "has_data": self._latest_stats is not None,
            "last_update": self._last_update,
            "polling_active": self._polling_task is not None and not self._polling_task.done()
        }
