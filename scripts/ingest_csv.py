#!/usr/bin/env python3
"""Ingest YouTube playlist CSV data into SQLite with Phase 0.1 cleaning."""

import csv
import sqlite3
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.cleaning import (
    clean_description,
    clean_title,
    parse_integer,
    parse_iso_datetime,
    parse_iso_duration,
)


def find_csv_file(data_dir: Path) -> Optional[Path]:
    """Find the YouTube playlist CSV file in the data directory.

    Args:
        data_dir: Path to data directory

    Returns:
        Path to CSV file or None if not found
    """
    csv_files = list(data_dir.glob("youtube_playlist_*.csv"))
    if not csv_files:
        return None
    # Return the most recent file (by modification time)
    return sorted(csv_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def ingest_csv(csv_path: Path, db_path: Path) -> dict:
    """Ingest CSV data into SQLite with cleaning.

    Args:
        csv_path: Path to CSV file
        db_path: Path to SQLite database

    Returns:
        Dictionary with ingestion statistics
    """
    stats = {
        "total_rows": 0,
        "inserted": 0,
        "duplicates_skipped": 0,
        "errors": 0,
    }

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check existing video_ids to detect duplicates
    cursor.execute("SELECT video_id FROM videos")
    existing_ids = {row[0] for row in cursor.fetchall()}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            stats["total_rows"] += 1

            video_id = row.get("video_id", "").strip()
            if not video_id:
                stats["errors"] += 1
                continue

            # Skip duplicates
            if video_id in existing_ids:
                stats["duplicates_skipped"] += 1
                continue

            try:
                # Parse and clean data
                title = clean_title(row.get("title"))
                description = clean_description(row.get("video_description"))
                channel_name = row.get("channel_name", "").strip()
                channel_id = row.get("channel_id", "").strip()

                # Parse numeric fields
                duration_str = row.get("video_length")
                duration_seconds = parse_iso_duration(duration_str)

                datetime_str = row.get("video_published_datetime")
                published_at = parse_iso_datetime(datetime_str)

                view_count = parse_integer(row.get("video_views"))
                like_count = parse_integer(row.get("video_likes"))
                comment_count = parse_integer(row.get("number_comments"))

                # Insert into database
                cursor.execute(
                    """
                    INSERT INTO videos (
                        video_id, title, description, channel_name, channel_id,
                        published_at, duration_seconds, view_count, like_count,
                        comment_count, is_indexed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        video_id,
                        title,
                        description,
                        channel_name,
                        channel_id,
                        published_at,
                        duration_seconds,
                        view_count,
                        like_count,
                        comment_count,
                        0,  # is_indexed = False
                    ),
                )
                stats["inserted"] += 1
                existing_ids.add(video_id)

            except Exception as e:
                print(f"Error processing {video_id}: {e}")
                stats["errors"] += 1

    conn.commit()
    conn.close()

    return stats


def main():
    """Main entry point for CSV ingestion."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    db_path = data_dir / "videos.db"

    # Find CSV file
    csv_path = find_csv_file(data_dir)
    if not csv_path:
        print("❌ No YouTube playlist CSV file found in data/")
        return 1

    print(f"📂 Found CSV: {csv_path.name}")
    print(f"💾 Database: {db_path}")

    # Ingest data
    print("\n🔄 Ingesting data...")
    stats = ingest_csv(csv_path, db_path)

    # Print summary
    print("\n📊 Ingestion Summary:")
    print(f"  Total rows in CSV: {stats['total_rows']}")
    print(f"  Inserted: {stats['inserted']}")
    print(f"  Duplicates skipped: {stats['duplicates_skipped']}")
    print(f"  Errors: {stats['errors']}")

    return 0


if __name__ == "__main__":
    exit(main())
