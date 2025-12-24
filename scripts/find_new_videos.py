#!/usr/bin/env python3
"""Find newly added videos by comparing with previous state."""

import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

def find_new_videos(db_path: Path, since_timestamp: str | None = None, output_file: Path | None = None) -> list:
    """Find videos added since a specific timestamp or create a baseline.
    
    Args:
        db_path: Path to SQLite database
        since_timestamp: Timestamp in format YYYY-MM-DD HH:MM:SS
        output_file: Optional file to save new video IDs
        
    Returns:
        List of new video IDs
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if since_timestamp:
        # Find videos added since the timestamp
        cursor.execute(
            """
            SELECT video_id, created_at 
            FROM videos 
            WHERE created_at > ?
            ORDER BY created_at DESC
            """,
            (since_timestamp,)
        )
        new_videos = cursor.fetchall()
        
        if new_videos:
            print(f"✅ Found {len(new_videos)} videos added since {since_timestamp}:")
            for video_id, created_at in new_videos[:10]:  # Show first 10
                print(f"  {video_id} (added: {created_at})")
            if len(new_videos) > 10:
                print(f"  ... and {len(new_videos) - 10} more")
        else:
            print(f"ℹ️  No new videos found since {since_timestamp}")
            
        if output_file:
            with open(output_file, "w") as f:
                f.write(f"# New videos added since {since_timestamp}\n")
                f.write("# Format: video_id,created_at\n")
                for video_id, created_at in new_videos:
                    f.write(f"{video_id},{created_at}\n")
            print(f"📝 Saved to: {output_file}")
            
        return [video_id for video_id, _ in new_videos]
    else:
        # Create baseline - get current max created_at
        cursor.execute("SELECT MAX(created_at) FROM videos")
        max_created = cursor.fetchone()[0]
        
        if max_created:
            print(f"📊 Current database state:")
            print(f"  Latest created_at: {max_created}")
            
            cursor.execute("SELECT COUNT(*) FROM videos")
            total_count = cursor.fetchone()[0]
            print(f"  Total videos: {total_count}")
            
            # Save baseline timestamp
            baseline_file = db_path.parent / "last_checkpoint.txt"
            with open(baseline_file, "w") as f:
                f.write(f"# Database checkpoint: {datetime.now()}\n")
                f.write(f"last_created_at:{max_created}\n")
                f.write(f"total_videos:{total_count}\n")
            
            print(f"📝 Baseline saved to: {baseline_file}")
            print(f"\n💡 To find new videos later, run:")
            print(f"   python scripts/find_new_videos.py --since \"{max_created}\"")
        else:
            print("ℹ️  Database is empty")
    
    conn.close()
    return []

def main():
    parser = argparse.ArgumentParser(
        description="Find newly added videos in the database"
    )
    parser.add_argument(
        "--since",
        help="Find videos added since this timestamp (YYYY-MM-DD HH:MM:SS)"
    )
    parser.add_argument(
        "--output",
        help="Output file to save new video IDs"
    )
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "videos.db"
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return 1
    
    output_file = None
    if args.output:
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
    
    find_new_videos(db_path, args.since, output_file)
    return 0

if __name__ == "__main__":
    exit(main())