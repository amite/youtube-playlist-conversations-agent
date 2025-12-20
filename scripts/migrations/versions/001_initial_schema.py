"""
Migration 001: Initial database schema

This is the baseline migration that recreates the initial schema
from init_db.py. Marks the database as version 1.

Created: 2025-12-20
"""


def upgrade(conn):
    """Create initial database schema."""
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


def downgrade(conn):
    """Drop all tables (reverting to pre-schema state)."""
    cursor = conn.cursor()

    # Drop tables in reverse order (respecting foreign key constraints)
    cursor.execute("DROP TABLE IF EXISTS test_queries")
    cursor.execute("DROP TABLE IF EXISTS evaluation_results")
    cursor.execute("DROP TABLE IF EXISTS embeddings_log")
    cursor.execute("DROP TABLE IF EXISTS videos")

    conn.commit()
