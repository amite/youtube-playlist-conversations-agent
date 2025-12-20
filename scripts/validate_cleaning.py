#!/usr/bin/env python3
"""
Validate Phase 0.2 semantic cleaning results.
Shows side-by-side comparison of raw vs cleaned data.

Usage:
    uv run python scripts/validate_cleaning.py
    uv run python scripts/validate_cleaning.py --samples 20
"""

import sqlite3
import argparse
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_cleaning(db_path: str = "data/videos.db", sample_size: int = 20):
    """Sample random videos and display raw vs cleaned comparison.

    Args:
        db_path: Path to SQLite database
        sample_size: Number of random samples to display
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if cleaned data exists
    cursor.execute("""
        SELECT COUNT(*) FROM videos WHERE cleaned_title IS NOT NULL
    """)
    cleaned_count = cursor.fetchone()[0]

    if cleaned_count == 0:
        print("❌ No cleaned data found. Run apply_semantic_cleaning.py first.")
        conn.close()
        return

    # Get random sample
    cursor.execute("""
        SELECT video_id, title, cleaned_title, description, cleaned_description
        FROM videos
        WHERE cleaned_title IS NOT NULL
        ORDER BY RANDOM()
        LIMIT ?
    """, (sample_size,))

    samples = cursor.fetchall()

    print(f"Validating {len(samples)}/{cleaned_count} cleaned videos\n")

    issues_found = 0

    for idx, (video_id, title, cleaned_title, description, cleaned_description) in enumerate(samples, 1):
        print(f"\n{'='*80}")
        print(f"Sample {idx}/{len(samples)} - Video ID: {video_id}")
        print(f"{'='*80}")

        # Title comparison
        title_reduction = len(title) - len(cleaned_title)
        print(f"\nTITLE ({len(title)} → {len(cleaned_title)} chars, {title_reduction} chars removed):")
        print(f"  RAW:     {title}")
        print(f"  CLEANED: {cleaned_title}")

        # Description comparison (first 300 chars)
        desc = description or ""
        cleaned_desc = cleaned_description or ""
        desc_preview = desc[:300]
        cleaned_preview = cleaned_desc[:300]
        desc_reduction = len(desc) - len(cleaned_desc)
        reduction_pct = (100 * desc_reduction / len(desc)) if len(desc) > 0 else 0

        print(f"\nDESCRIPTION ({len(desc)} → {len(cleaned_desc)} chars, {desc_reduction} removed, {reduction_pct:.1f}%):")
        print(f"  RAW:     {desc_preview}..." if len(desc) > 300 else f"  RAW:     {desc_preview}")
        print(f"  CLEANED: {cleaned_preview}..." if len(cleaned_desc) > 300 else f"  CLEANED: {cleaned_preview}")

        # Flag potential issues
        if len(cleaned_desc) < 50 and len(desc) > 200:
            print("  ⚠️  WARNING: Cleaned description is very short (possible over-cleaning)")
            issues_found += 1

    conn.close()

    print(f"\n\n{'='*80}")
    print(f"✅ Validation complete.")
    print(f"   Reviewed: {len(samples)} samples")
    print(f"   Cleaned: {cleaned_count} total videos")
    if issues_found > 0:
        print(f"   ⚠️  Potential issues: {issues_found} over-cleaned descriptions")
    else:
        print(f"   ✅ No issues detected")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate Phase 0.2 semantic cleaning results."
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=20,
        help="Number of random samples to review (default: 20)"
    )
    args = parser.parse_args()

    validate_cleaning(sample_size=args.samples)
