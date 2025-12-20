# Implementation: Scraper Run History Tracking

## Status: ✅ COMPLETE

**Date**: 2025-12-20
**Purpose**: Track historical records of scraper runs in database for auditing and monitoring

## What Was Built

### 1. Database Schema Addition
- **Migration**: `scripts/migrations/versions/002_add_scraper_runs.py`
- **Updated**: `scripts/init_db.py` (schema version bumped to 2)
- **Table**: `scraper_runs` with 11 fields

**Table Schema**:
```sql
CREATE TABLE scraper_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id TEXT NOT NULL,
    run_started_at TIMESTAMP NOT NULL,
    run_completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    new_videos_count INTEGER DEFAULT 0,
    existing_videos_skipped INTEGER DEFAULT 0,
    total_videos_in_csv INTEGER DEFAULT 0,
    csv_path TEXT,
    status TEXT DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 2. Scraper.py Updates
Modified `scraper.py` with three key additions:

**a) Logging Method** (`_log_scraper_run`):
- Inserts run record into database
- Captures: new video count, skipped count, total CSV rows, file path, timestamps
- Handles success and error cases
- Gracefully skips if no database path

**b) CSV Return Value Update**:
- Modified `create_csv()` to return tuple: `(output_path, new_video_count, skipped_count)`
- Enables caller to access metrics

**c) Run Method Enhancement**:
- Captures `start_time` at beginning
- Wraps execution in try-except block
- Logs every scenario: successful run, no new videos, errors
- Calls `_log_scraper_run()` after CSV creation
- Logs error details if exception occurs

### 3. Viewer Helper Script
Created `scripts/view_scraper_history.py`:
- Displays recent scraper runs in human-readable format
- Shows: run ID, playlist, timestamp, new/skipped/total counts, status
- Limits output to last 10 runs (configurable)
- Error handling for missing database

## Example Usage

### Run the scraper (automatic logging)
```bash
$ uv run python scraper.py PL15F8EFEA8777D0C6
...
📊 Run logged to database (ID: 5)
...
```

### View run history
```bash
$ uv run python scripts/view_scraper_history.py

================================================================================
Recent Scraper Runs (last 10)
================================================================================

Run #5 - 2025-12-20T12:47:35.312493
  Playlist: PL15F8EFEA8777D0C6
  New videos: 14
  Existing skipped: 410
  Total in CSV: 424
  Status: success

Run #4 - 2025-12-20T12:47:22.019699
  Playlist: PL15F8EFEA8777D0C6
  New videos: 14
  Existing skipped: 410
  Total in CSV: 424
  Status: success
```

## Migration Management

### Applied Migrations
```bash
# Check status
$ uv run python scripts/migrate.py status
Current version: 2
Latest version: 2
✓ All migrations applied

# View specific run
$ sqlite3 data/videos.db "SELECT * FROM scraper_runs ORDER BY id DESC LIMIT 1"
```

### Rollback Capability
```bash
# Rollback if needed
$ uv run python scripts/migrate.py downgrade

# Re-apply
$ uv run python scripts/migrate.py upgrade
```

## Test Results

### ✅ Migration Creation
- Migration file created: `002_add_scraper_runs.py`
- Follows existing migration patterns
- Includes upgrade and downgrade functions

### ✅ Database Updates
- Migration applied successfully
- `scraper_runs` table created
- Schema version updated to 2
- Table verified with `.tables` command

### ✅ Scraper Logging
- Run #1: 14 new videos, 410 skipped, logged successfully
- Run #2: 14 new videos, 410 skipped, logged successfully
- Console output: `📊 Run logged to database (ID: X)`

### ✅ View History Script
- Displays all recorded runs
- Shows formatted output with all key metrics
- Handles missing database gracefully

### ✅ Migration Rollback
- Downgrade works: Migration removed, version reverted to 1
- Re-upgrade works: Migration reapplied, version back to 2
- No data loss on rollback

## Files Modified

1. **scripts/migrations/versions/002_add_scraper_runs.py** (NEW)
   - Migration for adding scraper_runs table
   - ~30 lines

2. **scripts/init_db.py** (UPDATED)
   - Added scraper_runs table creation
   - Updated schema version to 2
   - ~20 lines added

3. **scraper.py** (UPDATED)
   - Added `_log_scraper_run()` method (~35 lines)
   - Updated `create_csv()` to return tuple with metrics (~3 lines)
   - Updated `run()` to capture time and log runs (~35 lines)
   - Total: ~73 lines added

4. **scripts/view_scraper_history.py** (NEW)
   - Helper to view scraper run history
   - ~50 lines

## Future Enhancements

1. **Query Filtering**: Add parameters to `view_scraper_history.py`
   - Filter by playlist ID
   - Filter by date range
   - Filter by status

2. **Analytics**: Add aggregation queries
   - Videos added per week
   - Average new videos per run
   - API quota analysis

3. **Alert Thresholds**: Add monitoring
   - Alert if skipped count changes unexpectedly
   - Track API quotas over time

4. **Retention Policy**: Add cleanup
   - Archive old runs
   - Auto-delete runs older than N days

## Success Criteria Met

✅ scraper_runs table exists in database
✅ Each scraper run creates a new row with metrics
✅ Historical data is queryable
✅ Migration system tracks version correctly (v0 → v1 → v2)
✅ Fresh databases (init_db.py) include the table
✅ Console output shows "Run logged to database (ID: X)"
✅ View helper displays formatted history
✅ Migration can be rolled back and reapplied

## Integration with Data Pipeline

This fits seamlessly into your data pipeline:

```
STEP 0: SCRAPING (UPDATED with run tracking)
├─ Run scraper.py
├─ Automatically logs to scraper_runs table
├─ Complete archive CSV generated (new + previous)
└─ Database records the metrics

STEP 1: INGESTION
├─ Run ingest_csv.py
├─ New videos added to database

STEP 2: CLEANING
├─ Run apply_semantic_cleaning.py
└─ Cleaned columns populated

STEP 3: EMBEDDINGS
├─ Run main.py index
└─ ChromaDB updated

STEP 4: SEARCH & EVAL
└─ Run main.py search
```

The scraper_runs table complements existing tables:
- `videos`: Contains video data
- `embeddings_log`: Tracks embedding generation
- `evaluation_results`: Tracks search quality
- **`scraper_runs`: Tracks scraping execution** ← NEW
