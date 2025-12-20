#!/usr/bin/env python3
"""Initialize SQLite database schema for YouTube playlist data."""

import sqlite3
import sys
from pathlib import Path

# Import migration runner for version tracking
sys.path.insert(0, str(Path(__file__).parent))
from migrations.migration_runner import mark_version


def create_schema(db_path: Path) -> None:
    """Create the database schema with all required tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Main videos table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            cleaned_title TEXT,
            description TEXT,
            cleaned_description TEXT,
            channel_name TEXT,
            channel_id TEXT,
            published_at TIMESTAMP,
            duration_seconds INTEGER,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            is_indexed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Embeddings log table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            embedding_type TEXT,
            model TEXT,
            token_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos(video_id)
        )
    """
    )

    # Evaluation results table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT,
            relevance_score INTEGER,
            best_result_position INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Test queries table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS test_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT NOT NULL,
            query_type TEXT,
            expected_channels TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()

    # Mark the database as version 1 (baseline schema)
    mark_version(conn, 1)

    conn.close()
    print(f"✓ Database schema created at {db_path}")
    print(f"✓ Schema version: 1")


if __name__ == "__main__":
    db_path = Path(__file__).parent.parent / "data" / "videos.db"
    create_schema(db_path)
