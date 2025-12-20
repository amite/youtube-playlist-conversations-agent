# Data Pipeline Architecture: Phase 0.2 Context

This document clarifies where `scripts/apply_semantic_cleaning.py` fits in the data processing pipeline.

## The Complete Data Journey

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA PIPELINE                                   │
└─────────────────────────────────────────────────────────────────────────┘

STEP 1: SCRAPING (YouTube Data Collection)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Command:    python scraper.py
Script:     scraper.py
Input:      YouTube playlist URL
Output:     CSV file (data/youtube_playlist_<PLAYLIST_ID>_<TIMESTAMP>.csv)
Data:       Raw video metadata
            - video_id, title, channel_name, description
            - published_at, duration, views, likes, comments
Status:     UPDATED (now with database-aware incremental scraping)

KEY IMPROVEMENT: Scraper now checks videos.db before fetching from YouTube API
            - If database exists: loads existing video_ids, skips them (saves API quota!)
            - If no database: fetches all videos (backward compatible)
            - Result: Only NEW videos are fetched and added to CSV
            - API Savings: 50%+ reduction for incremental updates (18 calls → 1-2 calls)

CSV Structure (raw from YouTube API):
├─ video_id: "dQw4w9WgXcQ"
├─ title: "Rick Astley - Never Gonna Give You Up"          [RAW]
├─ description: "Check out http://... Subscribe here..."   [RAW with URLs, CTAs]
├─ channel_name: "Rick Astley"
└─ video_views: "1234567"


STEP 2A: INGESTION (CSV to Database)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Command:    uv run python scripts/ingest_csv.py
Script:     scripts/ingest_csv.py
Input:      CSV file from Step 1
Output:     SQLite database (data/videos.db)
Processing: Phase 0.1 Cleaning
            - Parse ISO durations (PT1H23M → 5000 seconds)
            - Parse ISO dates (2025-12-20T... → Unix timestamp)
            - Parse integers (view counts, likes)
            - Fill missing descriptions with "[No Description]"
Status:     EXISTING (fully functional, 410 videos already ingested)

Database after Step 2A:
┌────────────────────────────────────────────────┐
│ videos table                                   │
├────────────────────────────────────────────────┤
│ video_id  (PK)                                │
│ title              [RAW from CSV]             │
│ description        [RAW from CSV]             │
│ cleaned_title      [NULL - empty!]            │ ◄─ NEEDS CLEANING
│ cleaned_description [NULL - empty!]           │ ◄─ NEEDS CLEANING
│ channel_name                                  │
│ published_at       (Unix timestamp)           │
│ duration_seconds   (parsed integer)           │
│ view_count, like_count, comment_count         │
│ is_indexed         (0/1 flag for embeddings) │
└────────────────────────────────────────────────┘

Example row state after Step 2A:
    title: "Claude Just Solved Their Biggest Problem!!!"
    description: "Check this out: https://example.com ... Subscribe now! ..."
    cleaned_title: NULL
    cleaned_description: NULL


STEP 2B: SEMANTIC CLEANING (NEW - Phase 0.2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Command:    uv run python scripts/apply_semantic_cleaning.py
Script:     scripts/apply_semantic_cleaning.py (NEW in Phase 0.2)
Input:      SQLite database (videos table)
Output:     Same SQLite database (updated columns)
Processing: Phase 0.2 Semantic Cleaning
            - Remove URLs (https://example.com → removed)
            - Remove timestamps (00:00:00 Intro → removed)
            - Remove CTAs (Subscribe now! → removed)
            - Clean capitalization (BIGGEST → Biggest, preserve AI)
            - Remove emojis (🚀 → removed)
Status:     NEW - This is what Phase 0.2 builds

Key Difference: Semantic cleaning is SEPARATE from ingestion
    WHY?
    1. Can validate & iterate on patterns without re-scraping
    2. Can fix cleaning logic without re-running ingest
    3. Enables incremental cleaning of only new rows
    4. Preserves raw data for A/B testing
    5. Keeps concerns separated (CSV→DB vs semantic improvements)

Two operating modes:
┌─ MODE 1: FULL CLEANING (first-time, 410 videos)
│  Command:  uv run python scripts/apply_semantic_cleaning.py
│  Process:  Reads ALL videos (WHERE 1=1)
│  Updates:  cleaned_title, cleaned_description for all
│
└─ MODE 2: INCREMENTAL CLEANING (new videos after updates)
   Command:  uv run python scripts/apply_semantic_cleaning.py --incremental
   Process:  Reads only new videos (WHERE cleaned_title IS NULL)
   Updates:  cleaned_title, cleaned_description for only new videos

Database after Step 2B:
┌────────────────────────────────────────────────┐
│ videos table                                   │
├────────────────────────────────────────────────┤
│ video_id  (PK)                                │
│ title              "Claude Just Solved..."    │ ◄─ UNCHANGED (kept raw)
│ description        "Check this out: ..."      │ ◄─ UNCHANGED (kept raw)
│ cleaned_title      "Claude Just Solved"       │ ◄─ POPULATED! (cleaned)
│ cleaned_description "Claude just solved..."   │ ◄─ POPULATED! (cleaned)
│ channel_name                                  │
│ published_at                                  │
│ duration_seconds                              │
│ view_count, like_count, comment_count         │
│ is_indexed         0 (not yet embedded)       │
└────────────────────────────────────────────────┘


STEP 3: EMBEDDING GENERATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Command:    uv run python main.py index --limit 410
Script:     main.py (will be updated in Phase 0.4)
Input:      SQLite database (reads cleaned_title and cleaned_description)
Output:     ChromaDB collections
Processing: For each video with is_indexed=0:
            1. Call OpenAI API with cleaned_title
               → 1536-dim vector → store in title_embeddings collection
            2. Call OpenAI API with cleaned_description
               → 1536-dim vector → store in description_embeddings collection
            3. Update is_indexed = 1
            4. Log embedding to embeddings_log table
Status:     EXISTING (but needs update in Phase 0.4 to use cleaned columns)

Why Phase 0.4 is needed: Currently main.py uses raw title/description
                         Must update to use cleaned_title/cleaned_description


STEP 4: SEARCH & EVALUATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Command:    uv run python main.py search "query"
Script:     main.py
Input:      Query text + ChromaDB collections (from Step 3)
Output:     Top 5 results with relevance scores
Status:     EXISTING (works with embeddings from Step 3)
```

## Workflow for Fresh Data (UPDATED - Now with Smart Incremental Scraping)

When you want to add new videos to the system:

```
1. Scrape new videos (SMART - only fetches NEW videos!)
   $ python scraper.py
   └─ Checks videos.db for existing video_ids
   └─ Only fetches NEW videos from YouTube API (saves 50%+ API quota!)
   └─ Creates CSV with only NEW videos (not duplicates)

2. Ingest new videos (Phase 0.1 cleaning only)
   $ uv run python scripts/ingest_csv.py
   └─ Detects new video_ids, inserts to SQLite
   └─ cleaned_title = NULL, cleaned_description = NULL for new rows

3. CLEAN new videos semantically (Phase 0.2)
   $ uv run python scripts/apply_semantic_cleaning.py --incremental
   └─ Finds videos WHERE cleaned_title IS NULL
   └─ Applies all cleaning functions
   └─ Updates cleaned_title and cleaned_description

4. Generate embeddings (Phase 0.4)
   $ uv run python main.py index --limit <N>
   └─ Reads cleaned_title and cleaned_description
   └─ Creates embeddings via OpenAI
   └─ Stores in ChromaDB

5. Search!
   $ uv run python main.py search "your query"
   └─ Returns top 5 semantically relevant results
```

## Why This Architecture?

### Separate Ingestion from Cleaning?

```
WRONG WAY (monolithic):
  scraper → ingest_csv (does ingestion + semantic cleaning + embedding)
    ❌ Can't fix cleaning without re-scraping
    ❌ Can't validate cleaning separately
    ❌ Heavy, complex script
    ❌ Hard to debug

CORRECT WAY (separated concerns):
  scraper → ingest_csv → apply_semantic_cleaning → main.py index
    ✓ Can update cleaning patterns anytime
    ✓ Can validate & iterate without re-scraping
    ✓ Each step is focused and testable
    ✓ Incremental cleaning for new videos only
    ✓ Preserves raw data for A/B testing
```

### Why Keep Raw Columns?

```
Without raw columns:
  - Can't debug what original text was
  - Can't compare cleaning quality
  - Can't revert if cleaning is too aggressive
  - Can't A/B test raw vs cleaned embeddings

With raw columns (our approach):
  ✓ Side-by-side validation
  ✓ Full reversibility
  ✓ A/B testing capability (future)
  ✓ Data audit trail
```

## Scripts & Their Responsibilities

| Script | Role | Phase | Input | Output | Idempotent |
|--------|------|-------|-------|--------|-----------|
| scraper.py | Fetch from YouTube (now with incremental skip!) | Pre-Phase | URL + videos.db | CSV (only new) | NO (appends, but smart) |
| ingest_csv.py | CSV → SQLite + Phase 0.1 cleaning | Phase 0.1 | CSV | DB | NO (inserts new) |
| apply_semantic_cleaning.py | Phase 0.2 semantic cleaning | Phase 0.2 | DB | DB | YES (can re-run) |
| main.py index | Embedding generation | Phase 0.4 | DB | ChromaDB | NO (creates embeddings) |
| main.py search | Query the embeddings | Phase 4+ | Query | Results | YES (read-only) |

## Answer to Your Question

> "Will apply_semantic_cleaning.py be part of a data processing pipeline that connects scraper.py → ingest → semantic cleaning?"

**YES**, but with important nuances:

1. **Is it connected?** ✅ YES
   - scraper.py → CSV → ingest_csv.py → SQLite
   - ingest_csv.py → SQLite ← apply_semantic_cleaning.py
   - apply_semantic_cleaning.py → SQLite → main.py index → ChromaDB

2. **Is it a direct pipeline?** ⚠️ NOT directly connected
   - Each script is independent (runs manually)
   - Not a single unified pipeline function
   - You call them in order: `scraper → ingest → clean → embed → search`

3. **Is cleaning separate from ingestion?** ✅ YES (by design)
   - Ingestion = Phase 0.1 (parsing, basic cleaning)
   - Semantic cleaning = Phase 0.2 (regex-based noise removal)
   - Two separate concerns = two separate scripts

4. **The order for fresh data:**
   ```bash
   # Week 1: Initial setup
   python scraper.py                                      # CSV
   uv run python scripts/ingest_csv.py                   # CSV → DB
   uv run python scripts/apply_semantic_cleaning.py      # DB cleaned columns
   uv run python main.py index --limit 410               # DB → ChromaDB

   # Week 2+: Add new videos
   python scraper.py                                      # Append to CSV
   uv run python scripts/ingest_csv.py                   # New rows → DB
   uv run python scripts/apply_semantic_cleaning.py --incremental  # Clean only new
   uv run python main.py index --limit N                 # Embed only new
   ```

This is a **modular pipeline** not a **monolithic one** - each step can be run independently.
