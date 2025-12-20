# Plan: Add Database-Aware Incremental Scraping to Prevent API Quota Waste

## Problem Statement

**Current Issue**: The YouTube scraper re-fetches ALL playlist videos on every run, regardless of whether they already exist in the database. This wastes YouTube API quota (~18 API calls per scrape for 410 videos).

**Root Cause**: `scraper.py` has zero database awareness - it always fetches the entire playlist from scratch and writes to a new CSV file. The deduplication logic only exists in the ingestion layer (`ingest_csv.py` and `update_data.py`), which prevents database duplicates but AFTER the API quota has already been spent.

**Impact**:
- First scrape: 18 API calls (necessary)
- Every subsequent scrape: 18 API calls (100% wasted if no new videos)
- For incremental updates (5 new videos): Should only need 1-2 API calls, but uses 18

**Evidence**:
- [scraper.py:27-108](scraper.py#L27-L108) - No SQLite imports, no database queries
- [scraper.py:42](scraper.py#L42) - Always fetches full playlist via `playlistItems` endpoint
- [scraper.py:90](scraper.py#L90) - Always fetches stats for ALL videos via `videos` endpoint
- [ingest_csv.py:58-76](scripts/ingest_csv.py#L58-L76) - Deduplication happens during ingestion (too late)

---

## Solution Overview

**Approach**: Add database awareness to `scraper.py` to check existing video IDs before making API calls. Implement incremental scraping that only fetches NEW videos.

**Key Design Decision**: Modify `scraper.py` to accept an optional database path parameter. When provided, it will:
1. Load existing video IDs from the database
2. Filter them out during API response processing
3. Only fetch statistics for truly new videos
4. Skip API calls entirely if no new videos found

**Backward Compatibility**: Keep the existing standalone CSV workflow working for users without a database.

---

## Implementation Plan

### Phase 1: Add Database Awareness (Core Fix)

**File**: [scraper.py](scraper.py)

**Changes**:

1. **Add SQLite import** (line 8, after dotenv import)
   ```python
   import sqlite3
   ```

2. **Update `__init__` method** (lines 13-26)
   - Add optional `db_path` parameter
   - Load existing video_ids from database if `db_path` provided
   ```python
   def __init__(self, playlist_id: str, api_key: str,
                output_filename: str | None = None,
                db_path: str | None = None):
       # ... existing code ...
       self.db_path = db_path
       self.existing_video_ids = self._load_existing_video_ids()
   ```

3. **Add helper method to load existing IDs** (after `__init__`)
   ```python
   def _load_existing_video_ids(self) -> set[str]:
       """Load existing video IDs from database to skip re-fetching."""
       if not self.db_path or not Path(self.db_path).exists():
           return set()

       try:
           conn = sqlite3.connect(self.db_path)
           cursor = conn.cursor()
           cursor.execute("SELECT video_id FROM videos")
           existing_ids = {row[0] for row in cursor.fetchall()}
           conn.close()
           print(f"📂 Loaded {len(existing_ids)} existing video IDs from database")
           return existing_ids
       except Exception as e:
           print(f"⚠️  Could not load existing IDs: {e}")
           return set()
   ```

4. **Filter out existing videos in `fetch_playlist_items`** (lines 57-67)
   - After fetching each page, filter items
   - Track skipped vs new videos
   ```python
   # After line 57: all_items.extend(data.get("items", []))
   items = data.get("items", [])

   # Filter out existing videos if database provided
   if self.existing_video_ids:
       new_items = [
           item for item in items
           if item["contentDetails"]["videoId"] not in self.existing_video_ids
       ]
       skipped = len(items) - len(new_items)
       all_items.extend(new_items)
       print(f"  ✓ Page {page_count}: {len(new_items)} new, {skipped} skipped")
   else:
       all_items.extend(items)
       print(f"  ✓ Page {page_count}: {len(all_items)} items total")
   ```

5. **Update final message** (line 66)
   ```python
   if self.existing_video_ids:
       print(f"✅ Fetched {len(all_items)} NEW playlist items ({len(self.existing_video_ids)} existing skipped)")
   else:
       print(f"✅ Fetched {len(all_items)} playlist items")
   ```

6. **Early exit if no new videos** (after line 67, before return)
   ```python
   if len(all_items) == 0 and self.existing_video_ids:
       print("ℹ️  No new videos found in playlist")
       return []
   ```

7. **Update `main` function** (lines 181-208)
   - Pass database path to scraper
   ```python
   def main(playlist_id: str = typer.Argument(..., help="YouTube playlist ID to scrape")):
       """Main entry point for the YouTube Playlist Scraper CLI."""
       # ... existing code ...

       # Database path for incremental scraping
       db_path = data_dir / "videos.db"

       # Create scraper instance
       scraper = YouTubePlaylistScraper(
           playlist_id=playlist_id,
           api_key=API_KEY,
           output_filename=str(output_filename),
           db_path=str(db_path) if db_path.exists() else None
       )

       # ... existing code ...
   ```

**Testing Strategy**:
1. Test with fresh database (should fetch all videos as before)
2. Test with existing database (should skip existing, fetch only new)
3. Test with no new videos (should exit early, save API quota)
4. Verify CSV output contains only new videos
5. Verify ingestion still works correctly

---

### Phase 2: Enhanced Output & Validation

**File**: [scraper.py](scraper.py)

**Changes**:

1. **Update CSV creation message** (lines 149-151)
   ```python
   if self.existing_video_ids:
       print(f"✅ CSV created: {output_path}")
       print(f"   New videos: {len(rows) - 1}")
       print(f"   Existing videos skipped: {len(self.existing_video_ids)}")
   else:
       print(f"✅ CSV created: {output_path}")
       print(f"   Total rows: {len(rows) - 1} videos")
   ```

2. **Add early exit in `run` method** (after line 163)
   ```python
   playlist_items = await self.fetch_playlist_items()
   if not playlist_items:
       print("\nℹ️  No new videos to process. Database is up to date!")
       return
   ```

**Why This Matters**:
- Clear feedback to user about API savings
- Prevents empty CSV files when no new videos exist
- Validates that incremental scraping is working

---

### Phase 3: Update Documentation

**File**: [CLAUDE.md](CLAUDE.md)

**Changes**:

1. **Update scraper command documentation**
   - Note that scraper now checks database automatically
   - Explain incremental scraping behavior
   - Document when to expect API calls vs skips

2. **Update workflow section** (line 150-157 in DATA-PIPELINE-EXPLAINED.md)
   ```
   # Week 2+: Add new videos (UPDATED)
   python scraper.py                                      # Only fetches NEW videos (smart!)
   uv run python scripts/ingest_csv.py                   # New rows → DB
   uv run python scripts/apply_semantic_cleaning.py --incremental  # Clean only new
   uv run python main.py index --limit N                 # Embed only new
   ```

**File**: [artifacts/wip/plans/DATA-PIPELINE-EXPLAINED.md](artifacts/wip/plans/DATA-PIPELINE-EXPLAINED.md)

**Changes**:

1. **Update STEP 1 section** (lines 12-29)
   - Note database-aware scraping
   - Document API quota savings
   - Explain incremental behavior

---

## Critical Files to Modify

1. **[scraper.py](scraper.py)** - Main implementation (7 changes)
   - Add sqlite3 import
   - Add db_path parameter to `__init__`
   - Add `_load_existing_video_ids()` method
   - Filter existing videos in `fetch_playlist_items()`
   - Early exit if no new videos
   - Enhanced output messages
   - Update `main()` to pass db_path

2. **[CLAUDE.md](CLAUDE.md)** - Documentation update
   - Update scraper usage notes
   - Document incremental behavior

3. **[artifacts/wip/plans/DATA-PIPELINE-EXPLAINED.md](artifacts/wip/plans/DATA-PIPELINE-EXPLAINED.md)** - Pipeline documentation
   - Update STEP 1 with new behavior
   - Note API quota savings

---

## Testing Checklist

**Before Implementation**:
- [ ] Backup current `videos.db` database
- [ ] Note current video count (410 videos)
- [ ] Have test playlist ID ready

**Test Case 1: Fresh Database (Baseline)**
```bash
# Move database temporarily
mv data/videos.db data/videos.db.backup

# Run scraper (should fetch all videos)
python scraper.py PLtest123

# Expected: "Fetched X playlist items" (no existing IDs loaded)
# Expected: CSV contains all videos
```

**Test Case 2: Existing Database (Incremental)**
```bash
# Restore database
mv data/videos.db.backup data/videos.db

# Run scraper on SAME playlist
python scraper.py PLtest123

# Expected: "Loaded 410 existing video IDs from database"
# Expected: "No new videos found in playlist" OR "Fetched N NEW playlist items"
# Expected: If no new videos, no API calls to videos endpoint
```

**Test Case 3: Verify CSV Output**
```bash
# Check CSV only contains new videos
wc -l data/youtube_playlist_*.csv

# Expected: Header + N new videos (not 410 duplicates)
```

**Test Case 4: Ingestion Still Works**
```bash
# Ingest the new CSV
uv run python scripts/ingest_csv.py

# Expected: Only new videos added to database
# Expected: No duplicate key errors
```

**Test Case 5: No New Videos Scenario**
```bash
# Run scraper twice in a row
python scraper.py PLtest123
python scraper.py PLtest123

# Expected on second run:
# - "No new videos found in playlist"
# - No CSV file created (or empty CSV)
# - Minimal API usage (only playlist items check, no video stats)
```

---

## API Quota Savings Calculation

**Before Fix** (current behavior):
- Every scrape: 18 API calls (410 videos ÷ 50 batch size)
- Monthly scrapes (4 runs): 72 API calls
- Wasted quota: 100% after first run

**After Fix** (incremental scraping):
- First scrape: 18 API calls (necessary)
- Subsequent runs with 0 new videos: ~9 calls (playlist check only)
- Subsequent runs with 5 new videos: ~10 calls (playlist + 1 batch)
- Monthly scrapes (1 initial + 3 incremental): 18 + 9 + 9 + 9 = 45 calls
- **Savings: 37.5% API quota** (and scales better with more frequent runs)

**Best Case** (weekly scrapes, 1-2 new videos per week):
- First scrape: 18 calls
- 52 weekly scrapes: 18 + (52 × 9) = 486 calls
- Without fix: 18 × 52 = 936 calls
- **Savings: 48% API quota**

---

## Risks & Mitigation

**Risk 1**: Database corruption prevents ID loading
- **Mitigation**: Graceful fallback to empty set (scrapes everything)
- **Evidence**: Try-except block in `_load_existing_video_ids()`

**Risk 2**: Playlist videos get deleted (rare)
- **Mitigation**: Database keeps historical data (expected behavior)
- **Note**: Scraper only handles additions, not deletions

**Risk 3**: CSV ingestion expects old format
- **Mitigation**: CSV structure unchanged (just fewer rows)
- **Validation**: Test Case 4 verifies ingestion compatibility

**Risk 4**: Breaking existing workflows
- **Mitigation**: Database path is optional, backward compatible
- **Validation**: Test Case 1 verifies standalone CSV mode still works

---

## Next Steps After Implementation

1. **Run scraper on test playlist** to verify incremental behavior
2. **Monitor API quota usage** via YouTube API Console
3. **Update workflow documentation** with new best practices
4. **Consider future enhancement**: Track `last_sync_timestamp` in database for publishedAfter filtering (Phase 2 improvement)

---

## Alternative Approaches Considered

**Alternative 1**: Use `publishedAfter` parameter on playlistItems endpoint
- **Pros**: True incremental sync, minimal API calls
- **Cons**: Requires tracking last sync timestamp, more complex
- **Decision**: Save for Phase 2 if current fix insufficient

**Alternative 2**: Separate incremental script (`scraper_incremental.py`)
- **Pros**: No changes to existing scraper
- **Cons**: Code duplication, maintenance burden
- **Decision**: Rejected in favor of unified scraper with optional db_path

**Alternative 3**: Move database check to ingestion layer
- **Pros**: No changes to scraper
- **Cons**: Doesn't solve API quota waste (API calls already made)
- **Decision**: Rejected - doesn't address root cause

---

## Success Criteria

✅ **Must Have**:
1. Scraper loads existing video IDs from database if provided
2. API calls reduced by 50%+ for re-scrapes with no new videos
3. CSV output contains ONLY new videos (or empty if none)
4. Existing ingestion workflow unaffected
5. Backward compatible (works without database)

✅ **Nice to Have**:
1. Clear console output showing existing vs new video counts
2. Early exit if no new videos (saves time + API quota)
3. Updated documentation reflecting new behavior

---

## Estimated Complexity

**Implementation Time**: 30-45 minutes
- Phase 1 (core fix): 20 minutes
- Phase 2 (output/validation): 10 minutes
- Phase 3 (documentation): 10 minutes
- Testing: 15 minutes

**Lines of Code Changed**: ~40-50 lines
- scraper.py: +35 lines (new method, filtering logic, messages)
- CLAUDE.md: +5 lines (documentation)
- DATA-PIPELINE-EXPLAINED.md: +5 lines (pipeline notes)

**Risk Level**: Low
- Changes isolated to scraper.py
- Backward compatible design
- Existing functionality preserved
- Easy to test and validate
