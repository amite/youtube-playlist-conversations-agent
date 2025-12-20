"""Add scraper_runs table to track scraper execution history."""


def upgrade(conn):
    """Create scraper_runs table."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scraper_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id TEXT NOT NULL,
            run_started_at TIMESTAMP NOT NULL,
            run_completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            new_videos_count INTEGER DEFAULT 0,
            existing_videos_skipped INTEGER DEFAULT 0,
            total_videos_in_csv INTEGER DEFAULT 0,
            csv_path TEXT,
            status TEXT DEFAULT 'success',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()


def downgrade(conn):
    """Drop scraper_runs table."""
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS scraper_runs")
    conn.commit()
