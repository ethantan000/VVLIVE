"""
Data models for VVLIVE backend
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict


class QualityState(Enum):
    """Video quality states"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"
    RECOVERY = "RECOVERY"
    ERROR = "ERROR"


@dataclass
class QualityPreset:
    """Quality preset configuration"""
    resolution: str
    framerate: int
    bitrate_kbps: int
    encoder_preset: str

    def __str__(self) -> str:
        return f"{self.resolution}@{self.framerate}fps {self.bitrate_kbps}kbps"


# Quality presets mapping - LOCKED specification
QUALITY_PRESETS: Dict[QualityState, QualityPreset] = {
    QualityState.HIGH: QualityPreset(
        resolution="1920x1080",
        framerate=30,
        bitrate_kbps=4500,
        encoder_preset="veryfast"
    ),
    QualityState.MEDIUM: QualityPreset(
        resolution="1280x720",
        framerate=30,
        bitrate_kbps=2500,
        encoder_preset="veryfast"
    ),
    QualityState.LOW: QualityPreset(
        resolution="854x480",
        framerate=24,
        bitrate_kbps=1200,
        encoder_preset="fast"
    ),
    QualityState.VERY_LOW: QualityPreset(
        resolution="640x360",
        framerate=24,
        bitrate_kbps=600,
        encoder_preset="fast"
    ),
    QualityState.RECOVERY: QualityPreset(
        resolution="1280x720",
        framerate=30,
        bitrate_kbps=2500,
        encoder_preset="veryfast"
    ),
    QualityState.ERROR: QualityPreset(
        resolution="640x360",
        framerate=15,
        bitrate_kbps=300,
        encoder_preset="ultrafast"
    )
}


@dataclass
class NetworkMetrics:
    """Network performance metrics"""
    total_bandwidth_bps: float
    packet_loss_percent: float
    min_rtt_ms: float
    max_rtt_ms: float
    active_subflows: int

    @property
    def total_bandwidth_mbps(self) -> float:
        """Bandwidth in Mbps"""
        return self.total_bandwidth_bps / 1_000_000


@dataclass
class StreamHealth:
    """Stream health status"""
    score: int  # 0-100
    status: str  # "HEALTHY", "DEGRADED", "CRITICAL"
    issues: list[str]
    network_metrics: NetworkMetrics
    current_quality: QualityState
