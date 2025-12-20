#!/usr/bin/env python3
"""Export cleaned data from SQLite database to timestamped CSV file."""

import argparse
import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


def export_cleaned_data(db_path: Path, output_dir: Path, limit: Optional[int] = None) -> dict:
    """Export video data from database to CSV.

    Args:
        db_path: Path to SQLite database
        output_dir: Path to output directory for CSV file
        limit: Number of random rows to export (None exports all rows)

    Returns:
        Dictionary with export statistics
    """
    stats = {
        "total_exported": 0,
        "errors": 0,
        "output_path": None,
    }

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"sample_{timestamp}.csv"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch video data (all rows or random sample)
    if limit is None:
        cursor.execute(
            """
            SELECT
                video_id,
                title,
                cleaned_title,
                description,
                cleaned_description,
                channel_name,
                channel_id,
                published_at,
                duration_seconds,
                view_count,
                like_count,
                comment_count,
                is_indexed,
                created_at
            FROM videos
            ORDER BY created_at DESC
            """
        )
    else:
        cursor.execute(
            """
            SELECT
                video_id,
                title,
                cleaned_title,
                description,
                cleaned_description,
                channel_name,
                channel_id,
                published_at,
                duration_seconds,
                view_count,
                like_count,
                comment_count,
                is_indexed,
                created_at
            FROM videos
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (limit,),
        )

    rows = cursor.fetchall()
    cols = [description[0] for description in cursor.description]

    conn.close()

    # Write to CSV
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            writer.writerows(rows)
            stats["total_exported"] = len(rows)
            stats["output_path"] = str(output_path)
    except Exception as e:
        print(f"Error writing CSV: {e}")
        stats["errors"] += 1

    return stats


def main():
    """Main entry point for data export."""
    parser = argparse.ArgumentParser(
        description="Export video data from SQLite database to CSV"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Number of random rows to export (default: all rows)",
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "videos.db"
    output_dir = project_root / "data" / "samples"

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return 1

    print(f"💾 Database: {db_path}")
    print(f"📂 Output directory: {output_dir}")

    # Export data
    if args.limit:
        print(f"\n�� Exporting {args.limit} random rows...")
    else:
        print("\n🔄 Exporting all rows...")

    stats = export_cleaned_data(db_path, output_dir, limit=args.limit)

    # Print summary
    print("\n📊 Export Summary:")
    print(f"  Total records exported: {stats['total_exported']}")
    if stats["errors"]:
        print(f"  Errors: {stats['errors']}")
    if stats["output_path"]:
        print(f"  Output file: {stats['output_path']}")

    return 0


if __name__ == "__main__":
    exit(main())
