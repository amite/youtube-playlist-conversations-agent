# Session Refiner Summary: Data Cleaning Planning

**Date:** 2025-12-20
**Project:** YouTube Semantic Search Engine - Phase 1 Data Cleaning
**Session Type:** Planning & Analysis

---

## Session Overview

This was a planning session to design a data cleaning strategy for the YouTube semantic search project. The user requested a data cleaning plan based on the project README, existing documentation, and CSV data analysis. No implementation occurred - this was purely planning and documentation.

---

## Current Project State

### Data Assets
- **CSV File:** `data/videos_playlist_data.csv` - 413 videos scraped from YouTube
- **Database:** `data/videos.db` - EXISTS but is EMPTY (0 bytes, no schema)
- **Codebase:** Only scraper exists (`scraper.py`), no cleaning or ingestion code

### Data Quality Issues Identified
```
Total videos: 413
Duplicates: 3 video_ids
Missing descriptions: 4 videos
Description noise: 40-60% (URLs, timestamps, social CTAs, boilerplate)
Format issues:
  - Video durations in ISO 8601 ("PT1H46M33S") need parsing
  - Dates in ISO 8601 need parsing
  - View/like counts stored as strings
```

### Critical Gap Discovered
**The project has NO data ingestion pipeline.** The CSV exists but there's no code to:
- Create the SQLite schema (4 tables needed)
- Load CSV data into the database
- Clean data during ingestion
- Validate data quality

This must be built before the search engine can function.

---

## Design Decisions Made

### 1. Cleaning Approach
**Decision:** Quick rule-based cleaning (regex patterns, no NLP)
**Rationale:** Phase 1 focuses on proving semantic search works, not perfect data. Complex NLP cleaning can wait.

### 2. Data Retention Strategy
**Decision:** Keep both raw and cleaned data in separate columns
**Rationale:** Enables A/B testing cleaned vs raw data impact on search quality

### 3. Pipeline Design
**Decision:** Build reusable incremental update pipeline
**Rationale:** User will continue scraping, so one-time cleaning isn't sufficient

---

## 4-Phase Data Cleaning Plan Created

**Document Location:** `/home/amite/code/python/youtube_playlist_scraper/artifacts/wip/phase_1/cleaning/phase-1-data-cleaning.md`

### Phase 0.1: Basic Cleaning + Database Schema (3-4 hours)
**Goal:** Get data into SQLite with minimal cleaning

**Tasks:**
1. Create database schema with 4 tables:
   - `videos` - Core metadata + raw/cleaned columns
   - `embeddings_log` - Track embedding generation
   - `evaluation_results` - Manual search quality ratings
   - `test_queries` - Test query suite
2. Build CSV → SQLite ingestion script
3. Implement basic cleaning:
   - Remove duplicate video_ids
   - Parse ISO 8601 durations to seconds
   - Parse ISO dates to timestamps
   - Convert view/like counts to integers
   - Fill missing descriptions with "[No Description]"

**Files to Create:**
- `scripts/init_db.py` - Initialize schema
- `scripts/ingest_csv.py` - Load CSV with cleaning
- `utils/cleaning.py` - Cleaning functions

**Validation Metrics:**
- 413 videos → ~410 after dedup
- 0 NULL descriptions
- All durations in seconds
- All dates as timestamps

---

### Phase 0.2: Semantic Cleaning (6-8 hours)
**Goal:** Remove noise from titles/descriptions to improve embedding quality

**Description Cleaning Patterns:**
```python
# Remove:
- URLs (https://..., www....)
- Social CTAs ("Subscribe!", "Follow me on...")
- Sponsor boilerplate ("This video is sponsored by...")
- Timestamps (00:00, 1:23:45)
- Emoji spam (>3 consecutive emojis)
- Generic outros ("Thanks for watching...")

# Preserve:
- Core content (what the video is about)
- Key terms and concepts
- Technical details
```

**Title Cleaning:**
- Remove excessive capitalization (ALL CAPS → Title Case)
- Remove emoji spam
- Remove clickbait patterns ("YOU WON'T BELIEVE...")

**Expected Impact:**
- 30-50% description length reduction
- 20-40% improvement in search quality
- Better embedding focus on actual content

**Files to Create:**
- `config/cleaning_patterns.json` - Regex patterns
- `scripts/validate_cleaning.py` - Quality checks

---

### Phase 0.3: Incremental Update Pipeline (2-3 hours)
**Goal:** Support ongoing scraping with automated cleaning

**Script:** `scripts/update_data.py`

**Features:**
- Detect new rows in CSV (not in SQLite)
- Apply same cleaning pipeline
- Update `is_indexed=0` flag for new videos
- Log changes

**Workflow:**
```bash
# After scraping new videos
python scraper.py  # Appends to CSV
uv run python scripts/update_data.py  # Cleans + adds to SQLite
uv run python main.py index --limit 50  # Index new videos
```

---

### Phase 0.4: Integration with Search Engine (2-3 hours)
**Goal:** Connect cleaned data to main.py CLI

**Tasks:**
1. Update main.py to read from SQLite (not CSV)
2. Use `cleaned_description` and `cleaned_title` for embeddings
3. Add data quality dashboard (`scripts/data_stats.py`)

**Stats to Track:**
- Total videos in database
- Indexed vs unindexed count
- Average description length (raw vs cleaned)
- Videos with missing data

---

## Database Schema Design

```sql
CREATE TABLE videos (
    video_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    cleaned_title TEXT,  -- Phase 0.2
    description TEXT,
    cleaned_description TEXT,  -- Phase 0.2
    channel_name TEXT,
    channel_id TEXT,
    published_at TIMESTAMP,
    duration_seconds INTEGER,  -- Parsed from ISO 8601
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    is_indexed BOOLEAN DEFAULT 0,  -- For incremental indexing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE embeddings_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT,
    embedding_type TEXT,  -- 'title' or 'description'
    model TEXT,  -- 'text-embedding-3-small'
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

CREATE TABLE evaluation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT,
    relevance_score INTEGER,  -- 1-5
    best_result_position INTEGER,  -- 1-5
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE test_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    query_type TEXT,  -- topical, conceptual, technical, trend, tutorial
    expected_channels TEXT,  -- Optional: channels expected in results
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Files to Create (Summary)

```
scripts/
  ├── init_db.py              # Create SQLite schema
  ├── ingest_csv.py           # CSV → SQLite with Phase 0.1 cleaning
  ├── validate_cleaning.py    # Quality validation
  ├── update_data.py          # Incremental updates
  └── data_stats.py           # Data quality dashboard

utils/
  └── cleaning.py             # All cleaning functions

config/
  └── cleaning_patterns.json  # Regex patterns for Phase 0.2
```

---

## Time Estimates

| Phase | Tasks | Time |
|-------|-------|------|
| 0.1 | Basic cleaning + schema | 3-4 hours |
| 0.2 | Semantic cleaning | 6-8 hours |
| 0.3 | Incremental pipeline | 2-3 hours |
| 0.4 | Integration + stats | 2-3 hours |
| **Total** | | **14-20 hours** |

---

## Next Steps

1. **User reviews plan** in `artifacts/wip/phase_1/cleaning/phase-1-data-cleaning.md`
2. **User approves or requests changes**
3. **Begin Phase 0.1 implementation:**
   - Create `scripts/init_db.py`
   - Create `utils/cleaning.py`
   - Create `scripts/ingest_csv.py`
   - Run ingestion and validate

---

## Key Technical Notes

### Why Separate raw/cleaned Columns?
- A/B test search quality with raw vs cleaned embeddings
- Debugging: inspect what was removed
- Reversibility: can regenerate cleaned data

### Why Incremental Pipeline?
- User will continue scraping YouTube playlists
- Avoid re-processing existing 413 videos
- Reuse cleaning logic for new data

### Impact of NOT Cleaning
- **20-40% search quality degradation** expected
- Description noise dilutes embeddings (URLs, timestamps don't help search)
- Duplicate videos waste embedding API costs

---

## Context for Next Session

- **Plan document:** `/home/amite/code/python/youtube_playlist_scraper/artifacts/wip/phase_1/cleaning/phase-1-data-cleaning.md`
- **Current data:** `data/videos_playlist_data.csv` (413 videos)
- **Empty database:** `data/videos.db` (needs schema)
- **No implementation started yet** - awaiting user approval

**To start implementation, user should say:**
- "Let's begin Phase 0.1"
- OR "I approve, start with init_db.py"
- OR request changes to the plan first
