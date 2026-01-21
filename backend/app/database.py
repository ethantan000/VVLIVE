"""
Database setup and management
"""

import aiosqlite
import logging
from pathlib import Path
from .config import settings

logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database and create tables"""
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        # Stream sessions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stream_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                total_duration_seconds INTEGER,
                avg_bandwidth_mbps REAL,
                quality_changes INTEGER,
                alerts_count INTEGER,
                notes TEXT
            )
        """)

        # Quality transition events
        await db.execute("""
            CREATE TABLE IF NOT EXISTS quality_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                from_state TEXT,
                to_state TEXT,
                reason TEXT,
                bandwidth_mbps REAL,
                packet_loss_percent REAL,
                rtt_ms REAL,
                FOREIGN KEY (session_id) REFERENCES stream_sessions(id)
            )
        """)

        # Network metrics history
        await db.execute("""
            CREATE TABLE IF NOT EXISTS network_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                bandwidth_bps REAL,
                packet_loss_percent REAL,
                rtt_ms REAL,
                active_subflows INTEGER,
                FOREIGN KEY (session_id) REFERENCES stream_sessions(id)
            )
        """)

        # Alerts log
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT,
                message TEXT,
                acknowledged BOOLEAN DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES stream_sessions(id)
            )
        """)

        await db.commit()
        logger.info(f"Database initialized at {db_path}")


async def get_db():
    """Get database connection"""
    db = await aiosqlite.connect(settings.database_path)
    try:
        yield db
    finally:
        await db.close()
