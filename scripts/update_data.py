#!/usr/bin/env python3
"""Incremental update pipeline for new scraped videos.

After running scraper.py to append new videos to the CSV, this script
detects new rows and adds them to the SQLite database with cleaning.

Workflow:
    1. python scraper.py  # Appends new videos to CSV
    2. uv run python scripts/update_data.py  # Cleans + adds to SQLite
    3. uv run python main.py index --limit 50  # Index new videos
"""

import csv
import sqlite3
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.cleaning import (
    clean_description,
    clean_title,
    parse_integer,
    parse_iso_datetime,
    parse_iso_duration,
)


def find_csv_file(data_dir: Path) -> Optional[Path]:
    """Find the YouTube playlist CSV file in the data directory."""
    csv_files = list(data_dir.glob("youtube_playlist_*.csv"))
    if not csv_files:
        return None
    return sorted(csv_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def get_existing_video_ids(db_path: Path) -> set:
    """Get set of video_ids already in database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT video_id FROM videos")
    existing_ids = {row[0] for row in cursor.fetchall()}
    conn.close()
    return existing_ids


def add_video(
    cursor,
    video_id: str,
    title: str,
    description: str,
    channel_name: str,
    channel_id: str,
    published_at: Optional[int],
    duration_seconds: Optional[int],
    view_count: Optional[int],
    like_count: Optional[int],
    comment_count: Optional[int],
) -> bool:
    """Add a single video to database."""
    try:
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
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def update_database(csv_path: Path, db_path: Path) -> dict:
    """Update database with new videos from CSV.

    Returns:
        Dictionary with update statistics
    """
    stats = {
        "total_in_csv": 0,
        "already_indexed": 0,
        "new_added": 0,
        "errors": 0,
    }

    existing_ids = get_existing_video_ids(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            stats["total_in_csv"] += 1
            video_id = row.get("video_id", "").strip()

            if not video_id:
                stats["errors"] += 1
                continue

            if video_id in existing_ids:
                stats["already_indexed"] += 1
                continue

            # Parse and clean data
            title = clean_title(row.get("title"))
            description = clean_description(row.get("video_description"))
            channel_name = row.get("channel_name", "").strip()
            channel_id = row.get("channel_id", "").strip()

            duration_seconds = parse_iso_duration(row.get("video_length"))
            published_at = parse_iso_datetime(row.get("video_published_datetime"))
            view_count = parse_integer(row.get("video_views"))
            like_count = parse_integer(row.get("video_likes"))
            comment_count = parse_integer(row.get("number_comments"))

            if add_video(
                cursor,
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
            ):
                stats["new_added"] += 1
                existing_ids.add(video_id)
            else:
                stats["errors"] += 1

    conn.commit()
    conn.close()

    return stats


def main():
    """Main entry point for incremental updates."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    db_path = data_dir / "videos.db"

    if not db_path.exists():
        print("❌ Database not found. Run init_db.py and ingest_csv.py first.")
        return 1

    csv_path = find_csv_file(data_dir)
    if not csv_path:
        print("❌ No YouTube playlist CSV file found in data/")
        return 1

    print(f"📂 Found CSV: {csv_path.name}")
    print(f"💾 Database: {db_path}")

    # Update database
    print("\n🔄 Checking for new videos...")
    stats = update_database(csv_path, db_path)

    # Print summary
    print("\n📊 Update Summary:")
    print(f"  Total rows in CSV: {stats['total_in_csv']}")
    print(f"  Already indexed: {stats['already_indexed']}")
    print(f"  New videos added: {stats['new_added']}")
    print(f"  Errors: {stats['errors']}")

    if stats["new_added"] > 0:
        print(f"\n✅ Next step: uv run python main.py index --limit {stats['new_added']}")
    else:
        print("\n✅ Database is up to date")

    return 0


if __name__ == "__main__":
    exit(main())
