#!/usr/bin/env python3
"""Data quality dashboard for YouTube video database."""

import sqlite3
from pathlib import Path
from datetime import datetime


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def get_db_path() -> Path:
    """Get path to database."""
    return Path(__file__).parent.parent / "data" / "videos.db"


def main():
    """Run data quality checks."""
    db_path = get_db_path()
    if not db_path.exists():
        print("❌ Database not found. Run init_db.py first.")
        return 1

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Overall stats
    print_section("Overall Statistics")
    cursor.execute("SELECT COUNT(*) FROM videos")
    total = cursor.fetchone()[0]
    print(f"  Total videos: {total}")

    cursor.execute("SELECT COUNT(*) FROM videos WHERE is_indexed = 1")
    indexed = cursor.fetchone()[0]
    unindexed = total - indexed
    print(f"  Indexed: {indexed}")
    print(f"  Unindexed: {unindexed}")

    # Data completeness
    print_section("Data Completeness")
    cursor.execute("SELECT COUNT(*) FROM videos WHERE title IS NOT NULL AND title != ''")
    print(f"  Valid titles: {cursor.fetchone()[0]}/{total}")

    cursor.execute("SELECT COUNT(*) FROM videos WHERE description IS NOT NULL AND description != ''")
    print(f"  Valid descriptions: {cursor.fetchone()[0]}/{total}")

    cursor.execute("SELECT COUNT(*) FROM videos WHERE channel_name IS NOT NULL AND channel_name != ''")
    print(f"  Valid channel names: {cursor.fetchone()[0]}/{total}")

    cursor.execute("SELECT COUNT(*) FROM videos WHERE duration_seconds IS NOT NULL")
    print(f"  Valid durations: {cursor.fetchone()[0]}/{total}")

    cursor.execute("SELECT COUNT(*) FROM videos WHERE published_at IS NOT NULL")
    print(f"  Valid publish dates: {cursor.fetchone()[0]}/{total}")

    cursor.execute("SELECT COUNT(*) FROM videos WHERE view_count IS NOT NULL")
    print(f"  Valid view counts: {cursor.fetchone()[0]}/{total}")

    # Content statistics
    print_section("Content Statistics")

    cursor.execute(
        "SELECT AVG(LENGTH(title)), MIN(LENGTH(title)), MAX(LENGTH(title)) FROM videos"
    )
    avg_title_len, min_title_len, max_title_len = cursor.fetchone()
    print(f"  Title length (avg/min/max): {avg_title_len:.0f} / {min_title_len} / {max_title_len}")

    cursor.execute(
        "SELECT AVG(LENGTH(description)), MIN(LENGTH(description)), MAX(LENGTH(description)) FROM videos WHERE description != '[No Description]'"
    )
    result = cursor.fetchone()
    if result[0]:
        avg_desc_len, min_desc_len, max_desc_len = result
        print(f"  Description length (avg/min/max): {avg_desc_len:.0f} / {min_desc_len} / {max_desc_len}")

    cursor.execute("SELECT AVG(duration_seconds) FROM videos WHERE duration_seconds IS NOT NULL")
    avg_duration = cursor.fetchone()[0]
    hours = avg_duration / 3600 if avg_duration else 0
    print(f"  Average video duration: {hours:.1f} hours ({avg_duration:.0f} seconds)")

    cursor.execute("SELECT AVG(view_count) FROM videos WHERE view_count IS NOT NULL")
    avg_views = cursor.fetchone()[0]
    print(f"  Average views: {avg_views:,.0f}")

    cursor.execute("SELECT AVG(like_count) FROM videos WHERE like_count IS NOT NULL")
    avg_likes = cursor.fetchone()[0]
    print(f"  Average likes: {avg_likes:,.0f}")

    # Date range
    print_section("Date Range")
    cursor.execute("SELECT MIN(published_at), MAX(published_at) FROM videos WHERE published_at IS NOT NULL")
    min_date, max_date = cursor.fetchone()
    if min_date and max_date:
        min_dt = datetime.fromtimestamp(min_date)
        max_dt = datetime.fromtimestamp(max_date)
        print(f"  Oldest video: {min_dt.strftime('%Y-%m-%d')}")
        print(f"  Newest video: {max_dt.strftime('%Y-%m-%d')}")

    # Channel stats
    print_section("Channel Statistics")
    cursor.execute("SELECT COUNT(DISTINCT channel_name) FROM videos WHERE channel_name IS NOT NULL")
    print(f"  Unique channels: {cursor.fetchone()[0]}")

    cursor.execute(
        "SELECT channel_name, COUNT(*) as count FROM videos WHERE channel_name IS NOT NULL GROUP BY channel_name ORDER BY count DESC LIMIT 5"
    )
    print(f"  Top 5 channels:")
    for channel, count in cursor.fetchall():
        print(f"    - {channel}: {count} videos")

    # Embedding log
    print_section("Embedding Log")
    cursor.execute("SELECT COUNT(*) FROM embeddings_log")
    print(f"  Total embeddings generated: {cursor.fetchone()[0]}")

    cursor.execute("SELECT embedding_type, COUNT(*) FROM embeddings_log GROUP BY embedding_type")
    for embedding_type, count in cursor.fetchall():
        print(f"    - {embedding_type}: {count}")

    # Evaluation stats
    print_section("Evaluation Results")
    cursor.execute("SELECT COUNT(*) FROM evaluation_results")
    eval_count = cursor.fetchone()[0]
    print(f"  Total evaluations: {eval_count}")

    if eval_count > 0:
        cursor.execute("SELECT AVG(relevance_score) FROM evaluation_results")
        avg_score = cursor.fetchone()[0]
        print(f"  Average relevance score: {avg_score:.2f}/5")

    # Test queries
    print_section("Test Queries")
    cursor.execute("SELECT COUNT(*) FROM test_queries")
    query_count = cursor.fetchone()[0]
    print(f"  Total test queries: {query_count}")

    if query_count > 0:
        cursor.execute("SELECT query_type, COUNT(*) FROM test_queries GROUP BY query_type")
        print(f"  By type:")
        for query_type, count in cursor.fetchall():
            print(f"    - {query_type}: {count}")

    # Semantic cleaning statistics
    print_section("Semantic Cleaning (Phase 0.2)")
    cursor.execute("SELECT COUNT(*) FROM videos WHERE cleaned_title IS NOT NULL")
    cleaned_count = cursor.fetchone()[0]
    uncleaned_count = total - cleaned_count
    print(f"  Videos with cleaned data: {cleaned_count}/{total}")
    print(f"  Videos pending cleaning: {uncleaned_count}/{total}")

    if cleaned_count > 0:
        # Title length statistics
        cursor.execute(
            "SELECT AVG(LENGTH(cleaned_title)), MIN(LENGTH(cleaned_title)), MAX(LENGTH(cleaned_title)) FROM videos WHERE cleaned_title IS NOT NULL"
        )
        avg_clean_title, min_clean_title, max_clean_title = cursor.fetchone()
        cursor.execute(
            "SELECT AVG(LENGTH(title)) FROM videos WHERE cleaned_title IS NOT NULL"
        )
        avg_raw_title = cursor.fetchone()[0]
        title_reduction_pct = 100 * (1 - avg_clean_title / avg_raw_title) if avg_raw_title > 0 else 0

        print(f"\n  Title length:")
        print(f"    - Raw (avg): {avg_raw_title:.0f} chars")
        print(f"    - Cleaned (avg): {avg_clean_title:.0f} chars")
        print(f"    - Reduction: {title_reduction_pct:.1f}%")

        # Description length statistics
        cursor.execute(
            "SELECT AVG(LENGTH(cleaned_description)), MIN(LENGTH(cleaned_description)), MAX(LENGTH(cleaned_description)) FROM videos WHERE cleaned_title IS NOT NULL AND cleaned_description IS NOT NULL AND cleaned_description != '[No Description]'"
        )
        result = cursor.fetchone()
        if result[0]:
            avg_clean_desc, min_clean_desc, max_clean_desc = result
            cursor.execute(
                "SELECT AVG(LENGTH(description)) FROM videos WHERE cleaned_title IS NOT NULL AND description IS NOT NULL AND description != '[No Description]'"
            )
            avg_raw_desc = cursor.fetchone()[0]
            desc_reduction_pct = 100 * (1 - avg_clean_desc / avg_raw_desc) if avg_raw_desc > 0 else 0

            print(f"\n  Description length:")
            print(f"    - Raw (avg): {avg_raw_desc:.0f} chars")
            print(f"    - Cleaned (avg): {avg_clean_desc:.0f} chars")
            print(f"    - Reduction: {desc_reduction_pct:.1f}%")
            print(f"    - Target goal: 30-50% reduction ✓" if 30 <= desc_reduction_pct <= 50 else f"    - Target goal: 30-50% reduction (actual: {desc_reduction_pct:.1f}%)")

    conn.close()
    print_section("✓ Data validation complete")
    return 0


if __name__ == "__main__":
    exit(main())
