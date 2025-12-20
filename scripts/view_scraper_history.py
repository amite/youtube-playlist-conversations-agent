#!/usr/bin/env python3
"""View scraper run history from database."""

import sqlite3
from pathlib import Path


def view_history(db_path: Path, limit: int = 10):
    """Display recent scraper runs."""
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id, playlist_id, run_completed_at,
                new_videos_count, existing_videos_skipped, total_videos_in_csv,
                status
            FROM scraper_runs
            ORDER BY run_completed_at DESC
            LIMIT ?
            """,
            (limit,),
        )

        rows = cursor.fetchall()
        if not rows:
            print(f"\n❌ No scraper runs found in database\n")
            conn.close()
            return

        print(f"\n{'='*80}")
        print(f"Recent Scraper Runs (last {limit})")
        print(f"{'='*80}\n")

        for row in rows:
            run_id, playlist, timestamp, new, skipped, total, status = row
            print(f"Run #{run_id} - {timestamp}")
            print(f"  Playlist: {playlist}")
            print(f"  New videos: {new}")
            print(f"  Existing skipped: {skipped}")
            print(f"  Total in CSV: {total}")
            print(f"  Status: {status}")
            print()

    except Exception as e:
        print(f"❌ Error querying database: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    db_path = Path(__file__).parent.parent / "data" / "videos.db"
    view_history(db_path)
