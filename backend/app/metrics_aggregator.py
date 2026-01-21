"""
Metrics Aggregator
Combines MPTCP metrics with ingest server stats (NOALBS pattern)

This module implements dual-source monitoring to provide comprehensive
health assessment. MPTCP metrics are proactive (network layer), ingest
stats are reactive (application layer verification).
"""

import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .config import settings
from .ingest_monitor import IngestMonitor, IngestStats

logger = logging.getLogger(__name__)


class MetricSource(Enum):
    """Which metric source triggered a decision"""
    MPTCP = "mptcp"
    INGEST = "ingest"
    BOTH = "both"
    NEITHER = "neither"


class HealthStatus(Enum):
    """Overall health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class AggregatedMetrics:
    """Combined metrics from both sources"""
    # MPTCP metrics (from kernel)
    mptcp_bandwidth_mbps: Optional[float] = None
    mptcp_packet_loss: Optional[float] = None
    mptcp_rtt_ms: Optional[float] = None
    mptcp_active_subflows: Optional[int] = None

    # Ingest metrics (from streaming server)
    ingest_bitrate_kbps: Optional[float] = None
    ingest_connection_active: Optional[bool] = None
    ingest_rtt_ms: Optional[float] = None

    # Derived metrics
    health_status: HealthStatus = HealthStatus.UNKNOWN
    health_score: int = 0  # 0-100
    divergence_detected: bool = False
    primary_source: MetricSource = MetricSource.NEITHER

    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class MetricsAggregator:
    """
    Dual-source metrics aggregator

    Combines MPTCP network metrics with ingest server stats to provide
    comprehensive health assessment. Implements NOALBS-style verification
    while maintaining VVLIVE's MPTCP-first approach.
    """

    def __init__(self, ingest_monitor: IngestMonitor):
        self.enabled = settings.feature_dual_metrics
        self.ingest_monitor = ingest_monitor

        # Thresholds from NOALBS pattern
        self.low_threshold_kbps = settings.bitrate_threshold_low_kbps
        self.offline_threshold_kbps = settings.bitrate_threshold_offline_kbps
        self.rtt_threshold_ms = settings.bitrate_threshold_rtt_ms

        self.last_aggregated: Optional[AggregatedMetrics] = None

        logger.info(f"Metrics Aggregator initialized (enabled={self.enabled})")

    def aggregate(
        self,
        mptcp_bandwidth_mbps: Optional[float] = None,
        mptcp_packet_loss: Optional[float] = None,
        mptcp_rtt_ms: Optional[float] = None,
        mptcp_subflows: Optional[int] = None
    ) -> AggregatedMetrics:
        """
        Aggregate metrics from both sources

        Args:
            mptcp_bandwidth_mbps: MPTCP bandwidth in Mbps
            mptcp_packet_loss: Packet loss percentage
            mptcp_rtt_ms: Round-trip time in ms
            mptcp_subflows: Number of active MPTCP subflows

        Returns:
            Aggregated metrics with health assessment
        """
        # Get ingest stats
        ingest_stats: Optional[IngestStats] = None
        if self.ingest_monitor and self.ingest_monitor.enabled:
            ingest_stats = self.ingest_monitor.get_latest_stats()

        # Create aggregated metrics
        metrics = AggregatedMetrics(
            mptcp_bandwidth_mbps=mptcp_bandwidth_mbps,
            mptcp_packet_loss=mptcp_packet_loss,
            mptcp_rtt_ms=mptcp_rtt_ms,
            mptcp_active_subflows=mptcp_subflows
        )

        if ingest_stats:
            metrics.ingest_bitrate_kbps = ingest_stats.bitrate_kbps
            metrics.ingest_connection_active = ingest_stats.connection_active
            metrics.ingest_rtt_ms = ingest_stats.rtt_ms

        # Determine primary source and health
        metrics.primary_source = self._determine_primary_source(metrics)
        metrics.health_status = self._assess_health(metrics)
        metrics.health_score = self._calculate_health_score(metrics)
        metrics.divergence_detected = self._detect_divergence(metrics)

        self.last_aggregated = metrics

        if metrics.divergence_detected:
            logger.warning(
                f"Metric divergence detected: MPTCP={mptcp_bandwidth_mbps}Mbps, "
                f"Ingest={metrics.ingest_bitrate_kbps}kbps"
            )

        return metrics

    def _determine_primary_source(self, metrics: AggregatedMetrics) -> MetricSource:
        """
        Determine which source should be trusted

        Priority:
        1. Both available → BOTH (most reliable)
        2. MPTCP only → MPTCP (proactive)
        3. Ingest only → INGEST (reactive)
        4. Neither → NEITHER (unknown state)
        """
        has_mptcp = metrics.mptcp_bandwidth_mbps is not None
        has_ingest = metrics.ingest_bitrate_kbps is not None

        if has_mptcp and has_ingest:
            return MetricSource.BOTH
        elif has_mptcp:
            return MetricSource.MPTCP
        elif has_ingest:
            return MetricSource.INGEST
        else:
            return MetricSource.NEITHER

    def _assess_health(self, metrics: AggregatedMetrics) -> HealthStatus:
        """
        Assess overall health using NOALBS thresholds

        Logic:
        - OFFLINE: Ingest not connected OR bitrate < offline threshold
        - CRITICAL: Bitrate < low threshold
        - DEGRADED: Bitrate < ideal OR high packet loss/RTT
        - HEALTHY: All metrics good
        """
        # Check ingest connection first (ground truth)
        if metrics.ingest_connection_active is False:
            return HealthStatus.OFFLINE

        # Get effective bitrate (prefer ingest as ground truth)
        bitrate_kbps = metrics.ingest_bitrate_kbps
        if bitrate_kbps is None and metrics.mptcp_bandwidth_mbps is not None:
            # Convert MPTCP bandwidth to approximate bitrate
            bitrate_kbps = metrics.mptcp_bandwidth_mbps * 1000 * 0.8  # Assume 80% efficiency

        if bitrate_kbps is None:
            return HealthStatus.UNKNOWN

        # NOALBS-style threshold checks
        if bitrate_kbps < self.offline_threshold_kbps:
            return HealthStatus.OFFLINE
        elif bitrate_kbps < self.low_threshold_kbps:
            return HealthStatus.CRITICAL
        elif self._has_degraded_metrics(metrics):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    def _has_degraded_metrics(self, metrics: AggregatedMetrics) -> bool:
        """Check if any metrics indicate degradation"""
        # High packet loss
        if metrics.mptcp_packet_loss and metrics.mptcp_packet_loss > 2.0:
            return True

        # High RTT
        rtt = metrics.mptcp_rtt_ms or metrics.ingest_rtt_ms
        if rtt and rtt > self.rtt_threshold_ms:
            return True

        # Single subflow (redundancy lost)
        if metrics.mptcp_active_subflows == 1:
            return True

        return False

    def _calculate_health_score(self, metrics: AggregatedMetrics) -> int:
        """
        Calculate health score 0-100

        Based on:
        - Bitrate adequacy (40 points)
        - Packet loss (30 points)
        - RTT (20 points)
        - Connection redundancy (10 points)
        """
        score = 0

        # Bitrate score (40 points)
        bitrate_kbps = metrics.ingest_bitrate_kbps
        if bitrate_kbps is None and metrics.mptcp_bandwidth_mbps:
            bitrate_kbps = metrics.mptcp_bandwidth_mbps * 1000 * 0.8

        if bitrate_kbps:
            if bitrate_kbps >= 2500:  # HIGH quality threshold
                score += 40
            elif bitrate_kbps >= self.low_threshold_kbps:
                score += int(40 * (bitrate_kbps - self.low_threshold_kbps) / 2000)
            else:
                score += int(40 * (bitrate_kbps / self.low_threshold_kbps))

        # Packet loss score (30 points)
        if metrics.mptcp_packet_loss is not None:
            if metrics.mptcp_packet_loss == 0:
                score += 30
            elif metrics.mptcp_packet_loss < 1.0:
                score += 25
            elif metrics.mptcp_packet_loss < 2.0:
                score += 20
            elif metrics.mptcp_packet_loss < 5.0:
                score += 10
            # >5% = 0 points

        # RTT score (20 points)
        rtt = metrics.mptcp_rtt_ms or metrics.ingest_rtt_ms
        if rtt is not None:
            if rtt < 50:
                score += 20
            elif rtt < 100:
                score += 15
            elif rtt < 200:
                score += 10
            elif rtt < self.rtt_threshold_ms:
                score += 5
            # >threshold = 0 points

        # Redundancy score (10 points)
        if metrics.mptcp_active_subflows:
            if metrics.mptcp_active_subflows >= 2:
                score += 10
            elif metrics.mptcp_active_subflows == 1:
                score += 5
            # 0 subflows = 0 points

        return min(100, max(0, score))

    def _detect_divergence(self, metrics: AggregatedMetrics) -> bool:
        """
        Detect divergence between MPTCP and ingest metrics

        Divergence occurs when network metrics look good but ingest
        bitrate is low, indicating encoder or local network issues.
        """
        if metrics.primary_source != MetricSource.BOTH:
            return False

        # Convert to same units
        mptcp_kbps = metrics.mptcp_bandwidth_mbps * 1000 if metrics.mptcp_bandwidth_mbps else 0
        ingest_kbps = metrics.ingest_bitrate_kbps or 0

        # Allow 30% variance
        if mptcp_kbps > 0 and ingest_kbps > 0:
            ratio = min(mptcp_kbps, ingest_kbps) / max(mptcp_kbps, ingest_kbps)
            return ratio < 0.7  # More than 30% difference

        return False

    def get_latest(self) -> Optional[AggregatedMetrics]:
        """Get most recent aggregated metrics"""
        return self.last_aggregated

    def should_downgrade(self) -> Tuple[bool, MetricSource]:
        """
        Determine if quality should be downgraded (NOALBS pattern)

        Returns:
            (should_downgrade, triggering_source)
        """
        if not self.last_aggregated:
            return False, MetricSource.NEITHER

        metrics = self.last_aggregated

        # Check ingest stats first (ground truth)
        if metrics.ingest_bitrate_kbps is not None:
            if metrics.ingest_bitrate_kbps < self.low_threshold_kbps:
                return True, MetricSource.INGEST

        # Check MPTCP metrics
        if metrics.mptcp_bandwidth_mbps is not None:
            if metrics.mptcp_bandwidth_mbps < 0.5:  # Less than 500 kbps
                return True, MetricSource.MPTCP

        # Check degraded state
        if metrics.health_status in [HealthStatus.CRITICAL, HealthStatus.OFFLINE]:
            return True, metrics.primary_source

        return False, MetricSource.NEITHER

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary for API/dashboard"""
        if not self.last_aggregated:
            return {
                "enabled": self.enabled,
                "status": "no_data",
                "health_score": 0
            }

        m = self.last_aggregated

        return {
            "enabled": self.enabled,
            "health_status": m.health_status.value,
            "health_score": m.health_score,
            "primary_source": m.primary_source.value,
            "divergence_detected": m.divergence_detected,
            "mptcp": {
                "bandwidth_mbps": m.mptcp_bandwidth_mbps,
                "packet_loss_percent": m.mptcp_packet_loss,
                "rtt_ms": m.mptcp_rtt_ms,
                "active_subflows": m.mptcp_active_subflows
            } if m.mptcp_bandwidth_mbps is not None else None,
            "ingest": {
                "bitrate_kbps": m.ingest_bitrate_kbps,
                "connection_active": m.ingest_connection_active,
                "rtt_ms": m.ingest_rtt_ms
            } if m.ingest_bitrate_kbps is not None else None,
            "timestamp": m.timestamp.isoformat()
        }
