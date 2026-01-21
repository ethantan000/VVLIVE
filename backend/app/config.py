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
    
    # Features
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


settings = Settings()

# Validate security on module load (but only in production mode)
if not settings.debug:
    settings.validate_security()