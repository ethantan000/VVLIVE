"""
Configuration management for VVLIVE backend
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import sys
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    """Application settings"""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Security
    secret_key: str = "change-this-in-production"
    api_token: str = "change-this-in-production"

    def validate_security(self):
        """Validate security settings and warn about insecure defaults"""
        insecure = []

        if self.secret_key == "change-this-in-production":
            insecure.append("SECRET_KEY")
        if self.api_token == "change-this-in-production":
            insecure.append("API_TOKEN")
        if self.encoder_password == "admin":
            insecure.append("ENCODER_PASSWORD")

        if insecure and not self.debug:
            logger.error("=" * 70)
            logger.error("SECURITY WARNING: Insecure default values detected!")
            logger.error(f"Please change these in .env file: {', '.join(insecure)}")
            logger.error("=" * 70)
            if not self.debug:
                sys.exit(1)
    
    # Encoder
    encoder_ip: str = "192.168.1.100"
    encoder_username: str = "admin"
    encoder_password: str = "admin"
    encoder_type: str = "uray"
    
    # OBS
    obs_host: str = "localhost"
    obs_port: int = 4455
    obs_password: Optional[str] = None
    
    # MPTCP
    mptcp_server_port: int = 8443
    
    # Monitoring
    metrics_poll_interval: int = 1
    log_level: str = "INFO"
    
    # Database
    database_path: str = "./data/streaming.db"
    
    # Features (existing)
    feature_emergency_mode: bool = True
    feature_audio_only_mode: bool = True
    feature_output_freeze_detection: bool = True
    feature_muted_but_live_detection: bool = True
    feature_health_score: bool = True
    feature_uplink_trust_scoring: bool = True
    feature_dead_link_suppression: bool = True
    feature_silent_alerts: bool = True
    feature_post_stream_report: bool = True
    feature_timeline: bool = True

    # NOALBS-Inspired Features (opt-in)
    feature_obs_integration: bool = False
    feature_ingest_monitoring: bool = False
    feature_retry_logic: bool = False
    feature_dual_metrics: bool = False

    # Ingest Server Configuration (NOALBS pattern)
    ingest_stats_url: str = "http://localhost/stats"
    ingest_stream_key: str = "live/stream"
    ingest_stats_poll_interval: int = 2  # seconds
    ingest_server_type: str = "nginx"  # nginx, srt, node-media-server

    # NOALBS-Style Bitrate Thresholds (kbps)
    bitrate_threshold_low_kbps: int = 500
    bitrate_threshold_offline_kbps: int = 450
    bitrate_threshold_rtt_ms: int = 1000  # For SRT monitoring

    # Retry Logic (NOALBS pattern)
    state_change_retry_attempts: int = 5
    state_change_retry_interval: int = 2  # seconds between checks
    instant_recovery_enabled: bool = True  # Skip retries on upgrade

    # OBS Scene Mapping
    obs_scene_high: str = "Main Camera"
    obs_scene_medium: str = "Main Camera"
    obs_scene_low: str = "Simple Overlay"
    obs_scene_very_low: str = "Audio Only"
    obs_scene_error: str = "Stream Offline"
    obs_scene_emergency: str = "Emergency Simple"

    # =========================================================================
    # IRLToolkit Integration Features (v1.2.0) - All opt-in, disabled by default
    # =========================================================================

    # OBS HTTP Bridge (obs-websocket-http integration)
    # Enables HTTP-based OBS control via companion service
    feature_obs_http_bridge: bool = False
    obs_http_bridge_host: str = "localhost"
    obs_http_bridge_port: int = 5001
    obs_http_bridge_auth_key: Optional[str] = None
    obs_http_bridge_timeout: int = 5  # seconds

    # SRTLA Transport (srtla integration)
    # Alternative bonded transport using SRT link aggregation
    feature_srtla_transport: bool = False
    srtla_metrics_source: str = "socket"  # socket | file | api
    srtla_stats_endpoint: str = ""  # API endpoint for stats if using api mode
    srtla_receiver_port: int = 9000
    transport_mode: str = "mptcp"  # mptcp | srtla | hybrid

    # RTMP Authentication (nginx-rtmp-auth integration)
    # Documents that nginx-rtmp-auth is configured for ingest security
    feature_rtmp_auth: bool = False
    rtmp_auth_service_url: str = ""  # Health check endpoint (optional)

    # OBS Library Selection (simpleobsws integration)
    # Choose between obs-websocket-py (current) or simpleobsws
    obs_library: str = "obs-websocket-py"  # obs-websocket-py | simpleobsws


settings = Settings()

# Validate security on module load (but only in production mode)
if not settings.debug:
    settings.validate_security()