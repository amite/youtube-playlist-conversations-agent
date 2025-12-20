#!/usr/bin/env python3
"""
Apply Phase 0.2 semantic cleaning to existing videos in database.
Updates cleaned_title and cleaned_description columns.

Supports both:
- One-time full cleaning: uv run python scripts/apply_semantic_cleaning.py
- Incremental cleaning (new videos only): uv run python scripts/apply_semantic_cleaning.py --incremental
"""

import sqlite3
import sys
import argparse
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.cleaning import clean_title_semantic, clean_description_semantic


def apply_cleaning(db_path: str = "data/videos.db", dry_run: bool = False, incremental: bool = False):
    """Apply semantic cleaning to videos in database.

    Args:
        db_path: Path to SQLite database
        dry_run: If True, preview changes without writing
        incremental: If True, only clean videos where cleaned_title IS NULL
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Determine which videos to clean
    if incremental:
        # Only clean new videos (where cleaned_title is NULL)
        cursor.execute("""
            SELECT video_id, title, description FROM videos
            WHERE cleaned_title IS NULL
        """)
        mode_str = "incremental (new videos only)"
    else:
        # Clean all videos
        cursor.execute("SELECT video_id, title, description FROM videos")
        mode_str = "full (all videos)"

    videos = cursor.fetchall()

    print(f"Processing {len(videos)} videos ({mode_str})...")

    stats = {
        'total': len(videos),
        'title_changes': 0,
        'desc_changes': 0,
        'desc_length_before': 0,
        'desc_length_after': 0,
    }

    updates = []

    for video_id, title, description in videos:
        # Clean title
        cleaned_title = clean_title_semantic(title)
        if cleaned_title != title:
            stats['title_changes'] += 1

        # Clean description
        cleaned_description = clean_description_semantic(description or "[No Description]")
        if cleaned_description != description:
            stats['desc_changes'] += 1

        stats['desc_length_before'] += len(description or "")
        stats['desc_length_after'] += len(cleaned_description)

        updates.append((cleaned_title, cleaned_description, video_id))

    # Report stats
    if stats['desc_length_before'] > 0:
        avg_reduction = 100 * (1 - stats['desc_length_after'] / stats['desc_length_before'])
    else:
        avg_reduction = 0

    print(f"\nCleaning Statistics:")
    print(f"  Titles modified: {stats['title_changes']}/{stats['total']}")
    print(f"  Descriptions modified: {stats['desc_changes']}/{stats['total']}")
    print(f"  Avg description length reduction: {avg_reduction:.1f}%")

    if dry_run:
        print("\n[DRY RUN] No changes written to database.")
        conn.close()
        return

    # Apply updates
    cursor.executemany("""
        UPDATE videos
        SET cleaned_title = ?, cleaned_description = ?
        WHERE video_id = ?
    """, updates)

    conn.commit()
    conn.close()

    print(f"\n✅ Updated {len(updates)} videos in database.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Apply semantic cleaning to videos in database."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to database"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Only clean new videos (WHERE cleaned_title IS NULL)"
    )
    args = parser.parse_args()

    apply_cleaning(dry_run=args.dry_run, incremental=args.incremental)
