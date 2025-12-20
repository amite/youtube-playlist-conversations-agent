# Plan: Add Scraper Run History Tracking to Database

## Problem Statement

The user wants to track historical records of scraper runs with metrics like:
- How many new videos were fetched
- How many existing videos were skipped
- Total videos in CSV
- When the run occurred
- Which CSV was generated

Currently, this information is only shown in console output and lost after each run.

## Recommendation: Use Both Migration + init_db.py

**Why this approach?**

1. **For existing databases** (yours): Migration provides a clean upgrade path
   - Run `uv run python scripts/migrate.py upgrade` to add the new table
   - Proper version tracking
   - Can rollback if needed

2. **For fresh databases** (future): init_db.py ensures the table exists from the start
   - Anyone running `scripts/init_db.py` gets the complete schema
   - No need to run migrations on a brand new database
   - Keeps baseline schema in sync with migrations

3. **Best practice**: Your project already follows this pattern
   - init_db.py creates the baseline (currently at version 1)
   - Migrations handle incremental changes (you have migration 001 pending)
   - This keeps both paths working correctly

## Implementation Plan

### Phase 1: Create Migration (for existing databases)

**File**: `scripts/migrations/versions/002_add_scraper_runs.py` (NEW)

Create a new migration following the pattern from `001_initial_schema.py`:

```python
"""Add scraper_runs table to track scraper execution history."""

def upgrade(conn):
    """Create scraper_runs table."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scraper_runs (
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
    """
    )
    conn.commit()

def downgrade(conn):
    """Drop scraper_runs table."""
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS scraper_runs")
    conn.commit()
```

### Phase 2: Update Baseline Schema (for fresh databases)

**File**: `scripts/init_db.py`

Add the scraper_runs table creation after the test_queries table (around line 80):

```python
# Scraper runs table
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS scraper_runs (
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
"""
)
```

Update the version mark to version 2 (line 85):
```python
mark_version(conn, 2)  # Changed from 1 to 2
```

### Phase 3: Update Scraper to Log Runs

**File**: `scraper.py`

Add methods to track scraper runs:

1. **Import datetime at top** (add to existing imports)

2. **Add helper method** to log run to database (after `_append_previous_csv_rows` method):
```python
def _log_scraper_run(
    self,
    new_count: int,
    skipped_count: int,
    total_csv_rows: int,
    csv_path: str,
    start_time: datetime,
    status: str = 'success',
    error: str = None
):
    """Log scraper run to database for historical tracking."""
    if not self.db_path:
        return  # No database, skip logging

    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO scraper_runs (
                playlist_id, run_started_at, run_completed_at,
                new_videos_count, existing_videos_skipped, total_videos_in_csv,
                csv_path, status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.playlist_id,
                start_time.isoformat(),
                datetime.now().isoformat(),
                new_count,
                skipped_count,
                total_csv_rows,
                str(csv_path),
                status,
                error
            )
        )
        conn.commit()
        conn.close()
        print(f"📊 Run logged to database (ID: {cursor.lastrowid})")
    except Exception as e:
        print(f"⚠️  Could not log scraper run: {e}")
```

3. **Update `run()` method** to track and log:
   - Add `start_time = datetime.now()` at beginning (after line 206)
   - Track new_count, skipped_count from fetch_playlist_items results
   - Call `_log_scraper_run()` after CSV creation (after line 223)
   - Pass: new_videos_count, existing_videos_skipped, total_csv_rows, csv_path, start_time

### Phase 4: Add Query Helper (Optional)

**File**: `scripts/view_scraper_history.py` (NEW)

Create a simple script to view scraper run history:

```python
#!/usr/bin/env python3
"""View scraper run history from database."""

import sqlite3
from pathlib import Path

def view_history(db_path: Path, limit: int = 10):
    """Display recent scraper runs."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

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
        (limit,)
    )

    print(f"\n{'='*80}")
    print(f"Recent Scraper Runs (last {limit})")
    print(f"{'='*80}\n")

    for row in cursor.fetchall():
        run_id, playlist, timestamp, new, skipped, total, status = row
        print(f"Run #{run_id} - {timestamp}")
        print(f"  Playlist: {playlist}")
        print(f"  New videos: {new}")
        print(f"  Existing skipped: {skipped}")
        print(f"  Total in CSV: {total}")
        print(f"  Status: {status}")
        print()

    conn.close()

if __name__ == "__main__":
    db_path = Path(__file__).parent.parent / "data" / "videos.db"
    view_history(db_path)
```

## Table Schema Details

```sql
CREATE TABLE scraper_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Auto-incrementing run ID
    playlist_id TEXT NOT NULL,              -- Which playlist was scraped
    run_started_at TIMESTAMP NOT NULL,      -- When scraping began
    run_completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- When it finished
    new_videos_count INTEGER DEFAULT 0,     -- New videos fetched from API
    existing_videos_skipped INTEGER DEFAULT 0,  -- Videos already in DB
    total_videos_in_csv INTEGER DEFAULT 0,  -- Total rows in output CSV
    csv_path TEXT,                          -- Path to generated CSV file
    status TEXT DEFAULT 'success',          -- 'success', 'partial', 'failed'
    error_message TEXT,                     -- Error details if failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Record creation time
)
```

## Migration Workflow

For your existing database:

```bash
# 1. Apply the migration
uv run python scripts/migrate.py upgrade

# 2. Verify
uv run python scripts/migrate.py status
```

## Files to Modify

1. **scripts/migrations/versions/002_add_scraper_runs.py** (NEW) - Migration for existing databases
2. **scripts/init_db.py** - Add table creation, update version to 2
3. **scraper.py** - Add logging method, update run() to track metrics
4. **scripts/view_scraper_history.py** (NEW, optional) - Helper to view history

## Testing Plan

1. Apply migration to existing database: `uv run python scripts/migrate.py upgrade`
2. Run scraper: `uv run python scraper.py PL15F8EFEA8777D0C6`
3. Query scraper_runs table to verify data was logged:
   ```bash
   sqlite3 data/videos.db "SELECT * FROM scraper_runs ORDER BY id DESC LIMIT 1"
   ```
4. Run view_scraper_history.py to see formatted output
5. Verify migration rollback works: `uv run python scripts/migrate.py downgrade`

## Success Criteria

- ✅ scraper_runs table exists in database
- ✅ Each scraper run creates a new row with metrics
- ✅ Historical data is queryable
- ✅ Migration system tracks version correctly
- ✅ Fresh databases (init_db.py) include the table
- ✅ Console output shows "Run logged to database (ID: X)"

## Example Output After Implementation

When running the scraper:
```
...
✅ CSV created: data/youtube_playlist_PL15F8EFEA8777D0C6_20251220_140000.csv
   New videos: 14
   Previous videos: 413
   Total rows: 427 videos
📊 Run logged to database (ID: 5)
...
```

When viewing history:
```
$ uv run python scripts/view_scraper_history.py

================================================================================
Recent Scraper Runs (last 10)
================================================================================

Run #5 - 2025-12-20 14:00:15
  Playlist: PL15F8EFEA8777D0C6
  New videos: 14
  Existing skipped: 410
  Total in CSV: 427
  Status: success

Run #4 - 2025-12-19 16:38:48
  Playlist: PL15F8EFEA8777D0C6
  New videos: 410
  Existing skipped: 0
  Total in CSV: 410
  Status: success
```
