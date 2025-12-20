# Phase 0.2: Semantic Cleaning Implementation Plan

## Overview

Implement regex-based semantic cleaning to remove noise from video titles and descriptions. The database schema is already prepared with `cleaned_title` and `cleaned_description` columns (currently empty). This phase will populate those columns for all 410 existing videos and ensure future ingestion uses cleaned data.

## Data Flow Pipeline

Here's the complete workflow for fresh data coming in through the system:

```
1. SCRAPING (existing)
   python scraper.py
   └─> Outputs: data/youtube_playlist_<PLAYLIST_ID>_<TIMESTAMP>.csv
       (Raw video metadata from YouTube API: title, description, etc.)

2a. INITIAL INGESTION (Phase 0.1 - existing)
   uv run python scripts/ingest_csv.py
   └─> Phase 0.1 cleaning: parse durations, dates, integers
   └─> Inserts into SQLite: videos table (title, description in raw columns)
   └─> Populates: cleaned_title = NULL, cleaned_description = NULL

2b. SEMANTIC CLEANING (Phase 0.2 - NEW in this phase)
   Two paths depending on data freshness:

   PATH A: First-time historical data (410 existing videos)
   ─────────────────────────────────
   uv run python scripts/apply_semantic_cleaning.py
   └─> Reads all 410 videos from database (raw title/description)
   └─> Applies semantic cleaning functions
   └─> Updates: cleaned_title, cleaned_description columns
   └─> One-time operation, then done

   PATH B: New incremental data (future scrapes)
   ────────────────────────────────
   1. python scraper.py  (appends new videos to CSV)
   2. uv run python scripts/update_data.py  (detects & adds new rows to DB)
   3. uv run python scripts/apply_semantic_cleaning.py --incremental
      └─> Reads videos WHERE cleaned_title IS NULL
      └─> Applies semantic cleaning only to new rows
      └─> Updates cleaned columns
   4. uv run python main.py index --limit N  (generates embeddings)

3. EMBEDDING GENERATION (Phase 0.4 - existing, will be updated)
   uv run python main.py index --limit N
   └─> Reads cleaned_title and cleaned_description from database
   └─> Generates embeddings via OpenAI API
   └─> Stores in ChromaDB with title/description separation
   └─> Marks is_indexed = 1

4. SEARCH & EVALUATION (existing)
   uv run python main.py search "query"
   └─> Uses cleaned embeddings for semantic search
   └─> Returns top 5 results
```

**Key Design Decision:** Semantic cleaning is a **separate step from ingestion** because:
- Allows validation and iterating on cleaning patterns without re-scraping
- Enables incremental cleaning of only new videos (identify via `cleaned_title IS NULL`)
- Preserves both raw and cleaned data for A/B testing
- Cleaning patterns can be updated and re-applied without touching ingestion code
- Keeps concerns separated: ingestion handles CSV→DB, cleaning handles semantic improvements

## Current State

**Database:**
- 410 videos with basic Phase 0.1 cleaning (placeholders, parsing)
- `cleaned_title` and `cleaned_description` columns exist but are NOT populated
- Schema version 1 (no migration needed)

**Data Quality Issues:**
- **89.8%** of descriptions contain URLs (368/410 videos)
- **58.8%** contain timestamps (241/410 videos)
- **30.2%** contain social CTAs (124/410 videos)
- Titles have excessive caps, emojis, clickbait patterns
- Average description: 1,584 chars (expected 30-50% reduction after cleaning)

**Existing Code:**
- `utils/cleaning.py` has basic Phase 0.1 functions (parse_iso_duration, clean_description with placeholders only)
- Comments explicitly note "Phase 0.2 for semantic cleaning"
- `scripts/ingest_csv.py` ingests data but does NOT populate cleaned columns
- `scripts/update_data.py` already exists for incremental updates (uses Phase 0.1 cleaning)

## Implementation Steps

### Step 1: Implement Description Cleaning Functions

**File:** `utils/cleaning.py`

Add the following functions:

1. **`remove_urls(text: str) -> str`**
   - Remove all URL patterns: `https?://`, `www.`, short links (`bit.ly`, etc.)
   - Regex: `r'https?://\S+|www\.\S+|bit\.ly/\S+'`
   - Preserve surrounding text structure

2. **`remove_timestamps(text: str) -> str`**
   - Remove timestamp patterns: `00:00:00`, `0:00`, `[0:00]`, `00:00 - Topic`
   - Regex patterns:
     - `r'\d{1,2}:\d{2}:\d{2}'` (HH:MM:SS or MM:SS:SS)
     - `r'\d{1,2}:\d{2}'` (MM:SS or H:MM)
     - `r'\[\d{1,2}:\d{2}(?::\d{2})?\]'` (bracket format)
   - Remove entire timestamp lines/sections

3. **`remove_social_ctas(text: str) -> str`**
   - Remove sentences/sections with: "subscribe", "follow me", "newsletter", "check out", "click here"
   - Use case-insensitive matching
   - Remove entire sentences containing CTAs (not just the word)

4. **`remove_boilerplate_sections(text: str) -> str`**
   - Remove sections starting with: "Resources:", "Links:", "Chapters:", "Timestamps:", "Affiliate disclosure:"
   - Also remove sponsorship blocks (detect via patterns like "sponsored by", "this video is brought to you")

5. **`extract_core_content(text: str, max_paragraphs: int = 3) -> str`**
   - Keep first 2-3 substantive paragraphs (actual content description)
   - Stop before boilerplate sections start
   - Fallback: If entire text is short (<200 chars), keep all

6. **`normalize_whitespace(text: str) -> str`**
   - Collapse multiple newlines → single newline
   - Collapse multiple spaces → single space
   - Strip leading/trailing whitespace

7. **`clean_description_semantic(text: str) -> str`** (orchestrator)
   - Apply all cleaning functions in order:
     1. remove_urls
     2. remove_timestamps
     3. remove_boilerplate_sections
     4. remove_social_ctas
     5. extract_core_content (first 3 paragraphs)
     6. normalize_whitespace
   - Return cleaned text
   - If result is too short (<50 chars), return original with just URL removal

### Step 2: Implement Title Cleaning Functions

**File:** `utils/cleaning.py`

Add the following functions:

1. **`remove_emojis(title: str) -> str`**
   - Strip emoji characters (🚀, 💡, 🔥, etc.)
   - Use regex with Unicode emoji ranges or `emoji` library

2. **`remove_excessive_punctuation(title: str) -> str`**
   - Replace `!!!` → `!`, `???` → `?`, `...` → (nothing or single period)
   - Keep single punctuation marks

3. **`normalize_caps(title: str) -> str`**
   - Detect words in ALL CAPS (>3 chars)
   - Convert to Title Case UNLESS it's a known acronym (AI, API, LLM, GPU, AWS, GCP, etc.)
   - Example: "NEW AI Tool" → "New AI Tool" (preserve "AI", fix "NEW")
   - Use word-by-word analysis with acronym list

4. **`remove_clickbait_patterns(title: str) -> str`**
   - Remove phrases like: "SHOCKING", "You WON'T BELIEVE", "Just Changed EVERYTHING"
   - Case-insensitive matching
   - Preserve rest of title structure

5. **`clean_title_semantic(title: str) -> str`** (orchestrator)
   - Apply in order:
     1. remove_emojis
     2. remove_excessive_punctuation
     3. normalize_caps
     4. remove_clickbait_patterns
     5. Strip whitespace
   - Return cleaned title

### Step 3: Create Script to Apply Cleaning to Existing Data

**File:** `scripts/apply_semantic_cleaning.py` (NEW)

```python
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--incremental", action="store_true", help="Only clean new videos (WHERE cleaned_title IS NULL)")
    args = parser.parse_args()

    apply_cleaning(dry_run=args.dry_run, incremental=args.incremental)
```

**Usage:**
```bash
# First time: Clean all 410 existing videos (Phase 0.2)
uv run python scripts/apply_semantic_cleaning.py --dry-run  # Preview
uv run python scripts/apply_semantic_cleaning.py            # Apply

# After updates: Clean only new videos (incremental)
uv run python scripts/apply_semantic_cleaning.py --incremental --dry-run
uv run python scripts/apply_semantic_cleaning.py --incremental
```

### Step 4: Create Validation Script

**File:** `scripts/validate_cleaning.py` (NEW)

```python
#!/usr/bin/env python3
"""
Validate Phase 0.2 semantic cleaning results.
Shows side-by-side comparison of raw vs cleaned data.
"""

import sqlite3
import random

def validate_cleaning(db_path: str = "data/videos.db", sample_size: int = 20):
    """Sample random videos and display raw vs cleaned comparison."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get random sample
    cursor.execute("""
        SELECT video_id, title, cleaned_title, description, cleaned_description
        FROM videos
        WHERE cleaned_title IS NOT NULL
        ORDER BY RANDOM()
        LIMIT ?
    """, (sample_size,))

    samples = cursor.fetchall()

    for idx, (video_id, title, cleaned_title, description, cleaned_description) in enumerate(samples, 1):
        print(f"\n{'='*80}")
        print(f"Sample {idx}/{sample_size} - Video ID: {video_id}")
        print(f"{'='*80}")

        # Title comparison
        print(f"\nTITLE (Original {len(title)} → Cleaned {len(cleaned_title)} chars):")
        print(f"  RAW:     {title}")
        print(f"  CLEANED: {cleaned_title}")

        # Description comparison (first 300 chars)
        desc_preview = (description or "")[:300]
        cleaned_preview = (cleaned_description or "")[:300]

        print(f"\nDESCRIPTION (Original {len(description or '')} → Cleaned {len(cleaned_description or '')} chars):")
        print(f"  RAW:     {desc_preview}...")
        print(f"  CLEANED: {cleaned_preview}...")

        # Flag potential issues
        if len(cleaned_description or "") < 50 and len(description or "") > 200:
            print("  ⚠️  WARNING: Cleaned description is very short (possible over-cleaning)")

    conn.close()

    print(f"\n\n✅ Validation complete. Review {sample_size} samples above.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=20, help="Number of random samples")
    args = parser.parse_args()

    validate_cleaning(sample_size=args.samples)
```

**Usage:**
```bash
uv run python scripts/validate_cleaning.py --samples 20
```

### Step 5: Update Ingestion Script (Optional Enhancement)

**File:** `scripts/ingest_csv.py`

This is **optional for Phase 0.2**. You can:

**Option A: Keep as-is (recommended for Phase 0.2)**
- Ingestion stays simple (Phase 0.1 only)
- Cleaning is a separate step (can be iterated independently)
- Existing `ingest_csv.py` continues to work

**Option B: Integrate cleaning into ingestion (Phase 0.3 optimization)**
- Import semantic cleaning functions
- Populate `cleaned_title` and `cleaned_description` during ingestion
- Requires testing with both paths (initial + incremental)

**Current Recommendation:** Keep Step 5 for Phase 0.3 after semantic cleaning is stable.

### Step 6: Update Data Statistics Script

**File:** `scripts/data_stats.py`

**Add new metrics:**
- Average cleaned title length vs raw title length
- Average cleaned description length vs raw description length
- % reduction in description length
- Count of videos with cleaned data populated
- Count of videos still needing cleaning (cleaned_title IS NULL)

### Step 7: Create Completion Report

**File:** `artifacts/wip/phase_1/cleaning/phase-0-2-completion-report.md` (NEW)

Document:
- What was built (12+ cleaning functions)
- Validation results (side-by-side comparison, metrics)
- Cleaning statistics (% reduction, pattern removal counts)
- Data pipeline overview
- Next steps (Phase 0.3 - integration, Phase 0.4 - embedding)

## Critical Files

**Modify:**
- `utils/cleaning.py` - Add 12+ semantic cleaning functions

**Create:**
- `scripts/apply_semantic_cleaning.py` - Apply cleaning to all or new videos
- `scripts/validate_cleaning.py` - Quality validation with side-by-side comparison
- `artifacts/wip/phase_1/cleaning/phase-0-2-completion-report.md` - Phase completion report

**Future modifications (Phase 0.3+):**
- `scripts/ingest_csv.py` - Integrate cleaning into ingestion
- `scripts/data_stats.py` - Add cleaning metrics

## Testing & Validation Strategy

1. **Unit-level:** Test each cleaning function with sample data (URLs, timestamps, CTAs)
2. **Integration:** Run `apply_semantic_cleaning.py --dry-run` to preview changes (0 writes)
3. **Validation:** Use `validate_cleaning.py` to manually review 20 random samples
4. **Metrics:** Check that description length reduces by 30-50% on average
5. **Quality:** Ensure no critical content is lost (verify via sampling)
6. **Iteration:** Adjust regex patterns if over-cleaning or under-cleaning detected

## Success Criteria

- ✅ All 410 existing videos have `cleaned_title` and `cleaned_description` populated
- ✅ Description length reduced by 30-50% on average
- ✅ 90%+ of sampled cleaned descriptions are coherent and preserve key information
- ✅ No critical content accidentally removed (verified via validation script)
- ✅ Title cleaning preserves acronyms (AI, API, LLM) while fixing clickbait
- ✅ `apply_semantic_cleaning.py --incremental` works for future new videos
- ✅ Zero database errors during cleaning application
- ✅ Data pipeline documented with clear step order

## Known Challenges & Solutions

**Challenge 1: Over-cleaning risk**
- **Solution:** Keep raw columns for debugging, extensive validation sampling, fallback logic in `clean_description_semantic`

**Challenge 2: Acronym preservation in titles**
- **Solution:** Maintain allowlist of common acronyms (AI, API, LLM, GPU, AWS, GCP, SQL, etc.)

**Challenge 3: Diverse timestamp formats**
- **Solution:** Multiple regex patterns covering all observed formats

**Challenge 4: URLs with complex query params**
- **Solution:** Comprehensive URL regex pattern: `r'https?://\S+|www\.\S+|bit\.ly/\S+'`

**Challenge 5: Boilerplate detection**
- **Solution:** Pattern-based section removal + "extract first N paragraphs" heuristic

**Challenge 6: Identifying new vs existing videos for incremental cleaning**
- **Solution:** Check `cleaned_title IS NULL` to identify videos not yet cleaned

## Estimated Effort

- **Step 1-2:** Implement cleaning functions (2-3 hours)
- **Step 3-4:** Build cleaning/validation scripts (1-2 hours)
- **Step 6-7:** Update stats and create completion report (1 hour)
- **Testing:** Manual validation and iteration (1-2 hours)

**Total: 6-8 hours** (matches original estimate)

## Next Phase Preview

**Phase 0.3:** Integration (1-2 hours)
- Optionally integrate cleaning into `scripts/ingest_csv.py`
- Ensure `scripts/update_data.py` uses semantic cleaning for new videos
- Keep incremental mode working

**Phase 0.4:** Search Integration (2-3 hours)
- Update `main.py index` command to use `cleaned_title` and `cleaned_description` for embeddings
- Compare search quality before/after cleaning via evaluation metrics
- Document improvements in completion report
