# Data Cleaning Plan for YouTube Semantic Search Engine

## Context

The project has 413 videos in CSV format but no data ingestion pipeline. The database (videos.db) is empty with no schema created. Before implementing the semantic search engine, we need to clean the data and establish a robust ingestion pipeline that can handle both the initial migration and future incremental updates.

**Critical Gap:** CSV → SQLite ingestion pipeline with data cleaning

**User Choices:**
- **Cleaning Approach:** Quick rule-based cleaning (regex patterns, no NLP libraries)
- **Data Retention:** Keep both raw and cleaned columns for debugging
- **Dataset Growth:** Design for incremental updates (reusable pipeline)

## Phase 0: Data Cleaning & Ingestion Pipeline

### Phase 0.1: Basic Data Quality & Database Setup

**Goal:** Create database schema and handle fundamental data quality issues

**Tasks:**

1. **Create database schema script** (`scripts/init_db.py`)
   - Create `videos` table with columns:
     - video_id (PK, TEXT)
     - channel_name (TEXT)
     - title (TEXT)
     - title_cleaned (TEXT) -- for semantic search
     - description (TEXT) -- raw, preserved
     - description_cleaned (TEXT) -- for semantic search
     - duration_seconds (INTEGER)
     - upload_date (TEXT, ISO 8601 format)
     - views (INTEGER)
     - likes (INTEGER)
     - comments (INTEGER)
     - is_indexed (INTEGER, default 0) -- tracks ChromaDB indexing status
     - created_at (TEXT, timestamp)
   - Create `embeddings_log` table for tracking embedding generation
   - Create `evaluation_results` table for manual quality ratings
   - Create `test_queries` table for test query suite
   - Add indexes on video_id, is_indexed, upload_date

2. **Build basic cleaning functions** (`utils/cleaning.py`)
   - `remove_duplicates(df)`: Remove duplicate video_ids (keep first occurrence)
   - `remove_missing_descriptions(df)`: Drop rows where description is null/empty
   - `trim_whitespace(df)`: Strip leading/trailing whitespace from all text columns
   - `parse_duration(iso_duration)`: Convert "PT1H46M33S" → integer seconds
   - `parse_datetime(iso_datetime)`: Convert ISO 8601 timestamp to SQLite-compatible format
   - Add logging for each cleaning step (e.g., "Removed 3 duplicates")

3. **Create ingestion script** (`scripts/ingest_csv.py`)
   - Load CSV with pandas
   - Apply Phase 0.1 cleaning functions
   - Validate data types and constraints
   - Insert into SQLite with proper error handling
   - Generate summary report (rows processed, rows skipped, issues found)
   - Add `--dry-run` flag to preview changes without writing to database

**Files to Create:**
- [scripts/init_db.py](scripts/init_db.py) - Database schema initialization
- [utils/cleaning.py](utils/cleaning.py) - Cleaning utility functions
- [scripts/ingest_csv.py](scripts/ingest_csv.py) - CSV → SQLite ingestion with Phase 0.1 cleaning

**Success Criteria:**
- Database schema created successfully
- 413 videos → ~406 videos after removing duplicates and missing descriptions
- All duration values parsed to integer seconds
- All timestamps parsed to datetime format
- Zero data type errors in SQLite

**Estimated Time:** 3-4 hours

---

### Phase 0.2: Semantic Cleaning (High Impact)

**Goal:** Remove boilerplate and noise from descriptions and titles to improve embedding quality

**Tasks:**

1. **Build description cleaning patterns** (`utils/cleaning.py`)
   - `remove_urls(text)`: Strip all URLs (http://, https://, bit.ly, etc.)
   - `remove_timestamps(text)`: Remove timestamp markers (00:00, 05:30, [0:00], etc.)
   - `remove_boilerplate_sections(text)`: Regex patterns for:
     - Social media CTAs: "Follow me on Twitter/LinkedIn/Instagram"
     - Newsletter signups: "Subscribe to my newsletter", "Join my mailing list"
     - Sponsorship mentions: "This video is sponsored by", "Thanks to [brand]"
     - Generic "Resources:" or "Links:" sections followed by URLs
     - "Connect with me", "Where to find me" sections
   - `remove_excessive_newlines(text)`: Collapse multiple newlines to single
   - `extract_core_content(text)`: Keep first 2-3 substantive paragraphs (before boilerplate)

2. **Build title cleaning patterns** (`utils/cleaning.py`)
   - `remove_excessive_punctuation(text)`: Replace "!!!" → "!", "???" → "?"
   - `normalize_capitalization(text)`: Convert ALL CAPS words to Title Case (preserve acronyms)
   - `remove_clickbait_markers(text)`: Strip patterns like:
     - "You WON'T BELIEVE"
     - "SHOCKING"
     - "Top 10 [...]"
     - Excessive emojis in titles
   - Keep topic keywords and descriptive information intact

3. **Create comprehensive pattern library** (`config/cleaning_patterns.json`)
   - Store all regex patterns in a JSON config file for easy iteration
   - Patterns organized by category: urls, timestamps, boilerplate, clickbait
   - Version the patterns (v1.0) to track changes over time
   - Document why each pattern exists with examples

4. **Extend ingestion script** (`scripts/ingest_csv.py`)
   - Add `--clean-semantic` flag to trigger Phase 0.2 cleaning
   - Apply description cleaning → write to `description_cleaned` column
   - Apply title cleaning → write to `title_cleaned` column
   - Keep raw `description` and `title` intact
   - Log cleaning statistics (avg length before/after, % content removed)

5. **Create validation script** (`scripts/validate_cleaning.py`)
   - Sample 20 random videos
   - Display side-by-side comparison: raw vs cleaned (descriptions and titles)
   - Generate HTML report for manual review
   - Calculate metrics: avg description length reduction, % boilerplate removed
   - Flag potential over-cleaning (descriptions < 100 chars after cleaning)

**Files to Modify/Create:**
- [utils/cleaning.py](utils/cleaning.py) - Add semantic cleaning functions
- [config/cleaning_patterns.json](config/cleaning_patterns.json) - Regex pattern library
- [scripts/ingest_csv.py](scripts/ingest_csv.py) - Add semantic cleaning flag
- [scripts/validate_cleaning.py](scripts/validate_cleaning.py) - Quality validation

**Success Criteria:**
- Description length reduced by ~30-50% on average (removing boilerplate)
- Title cleaning preserves topic keywords while removing clickbait
- Manual validation shows 90%+ of cleaned descriptions are coherent
- No critical content accidentally removed (verified via sampling)

**Estimated Time:** 6-8 hours

---

### Phase 0.3: Incremental Update Pipeline

**Goal:** Support adding new videos without re-processing existing data

**Tasks:**

1. **Add upsert logic** (`scripts/ingest_csv.py`)
   - Check if video_id already exists in database before inserting
   - Skip existing videos (log: "Skipped N existing videos")
   - Only process new videos
   - Add `--force-reprocess` flag to re-clean and update existing videos if needed

2. **Create update workflow script** (`scripts/update_data.py`)
   - Convenience wrapper for incremental updates
   - Steps:
     1. Run scraper to fetch new videos → append to CSV
     2. Run ingestion with deduplication
     3. Generate update report (new videos added, total count)
   - Add `--scrape-and-ingest` flag for end-to-end workflow

3. **Add data versioning** (simple approach)
   - Append timestamp to processed CSVs: `youtube_playlist_..._cleaned_20251220.csv`
   - Keep original raw CSV untouched
   - Store cleaning logs in `data/logs/cleaning_YYYYMMDD.log`

**Files to Modify/Create:**
- [scripts/ingest_csv.py](scripts/ingest_csv.py) - Add upsert and force-reprocess logic
- [scripts/update_data.py](scripts/update_data.py) - Incremental update workflow
- [data/logs/](data/logs/) - Directory for cleaning logs

**Success Criteria:**
- Running ingestion twice on same CSV doesn't create duplicates
- New videos added seamlessly without affecting existing data
- Logs show clear before/after counts for each run

**Estimated Time:** 2-3 hours

---

### Phase 0.4: Integration with Main Pipeline

**Goal:** Ensure cleaned data flows correctly into the search engine

**Tasks:**

1. **Update main.py index command** (when building main.py)
   - Use `title_cleaned` and `description_cleaned` for embeddings (NOT raw versions)
   - Verify `is_indexed` flag is set correctly after embedding generation
   - Add validation: ensure video exists in SQLite before indexing

2. **Create data quality dashboard** (`scripts/data_stats.py`)
   - Show database statistics:
     - Total videos in database
     - Videos with cleaned descriptions vs raw only
     - Average description length (raw vs cleaned)
     - Videos indexed in ChromaDB vs not indexed
     - Date range of videos
     - Top channels by video count
   - Add to CLI: `uv run python scripts/data_stats.py`

3. **Document the pipeline** (update README.md)
   - Add "Data Pipeline" section explaining:
     - CSV structure → Database schema mapping
     - Cleaning stages (basic → semantic)
     - How to add new videos
     - How to re-process if cleaning logic changes
   - Include examples of before/after cleaning

**Files to Modify/Create:**
- [main.py](main.py) - Use cleaned columns for embeddings (when building)
- [scripts/data_stats.py](scripts/data_stats.py) - Data quality dashboard
- [README.md](README.md) - Document data pipeline

**Success Criteria:**
- Embeddings are generated from cleaned data, not raw data
- Documentation clearly explains the full data flow
- Data stats script provides visibility into cleaning quality

**Estimated Time:** 2-3 hours

---

## Implementation Order

**Week 1: Core Cleaning Pipeline**
1. Phase 0.1: Basic data quality & database setup (3-4 hours)
2. Phase 0.2: Semantic cleaning (6-8 hours)
3. Validation: Manual review of cleaned data (1-2 hours)

**Week 1-2: Incremental Updates & Integration**
4. Phase 0.3: Incremental update pipeline (2-3 hours)
5. Phase 0.4: Integration with main pipeline (2-3 hours)

**Total Estimated Time:** 14-20 hours

---

## Critical Files to Create/Modify

**New Files:**
- [scripts/init_db.py](scripts/init_db.py) - Initialize database schema
- [scripts/ingest_csv.py](scripts/ingest_csv.py) - CSV → SQLite with cleaning
- [scripts/validate_cleaning.py](scripts/validate_cleaning.py) - Quality validation
- [scripts/update_data.py](scripts/update_data.py) - Incremental update workflow
- [scripts/data_stats.py](scripts/data_stats.py) - Data quality dashboard
- [utils/cleaning.py](utils/cleaning.py) - All cleaning functions
- [config/cleaning_patterns.json](config/cleaning_patterns.json) - Regex patterns

**Modified Files:**
- [README.md](README.md) - Document data pipeline
- [main.py](main.py) - Use cleaned columns for embeddings (when building search engine)

---

## Testing Strategy

**Unit Tests** (create `tests/test_cleaning.py`):
- Test each cleaning function with edge cases
- Verify duration parsing handles all ISO 8601 formats
- Ensure regex patterns don't over-match
- Test that cleaning preserves essential content

**Integration Tests**:
- Run full pipeline on sample CSV (20 videos)
- Verify database contains expected cleaned data
- Check that re-running doesn't create duplicates

**Manual Validation**:
- Review 20 random samples before/after cleaning
- Ensure no critical content lost
- Verify boilerplate actually removed

---

## Risk Mitigation

**Risk:** Over-aggressive cleaning removes valuable content
**Mitigation:**
- Keep raw versions in database
- Manual validation with sampling
- Iterative pattern refinement based on review

**Risk:** Regex patterns miss new boilerplate formats
**Mitigation:**
- Store patterns in config file for easy updates
- Add `--force-reprocess` flag to re-clean with new patterns
- Log cleaning changes for transparency

**Risk:** Incremental updates break existing data
**Mitigation:**
- Use upsert logic with video_id primary key
- Add dry-run mode to preview changes
- Version cleaning logs

---

## Success Metrics

1. **Data Quality:**
   - Zero duplicate video_ids in database
   - Zero missing descriptions in cleaned dataset
   - Description length reduction: 30-50% (boilerplate removed)
   - Manual validation: 90%+ coherent cleaned descriptions

2. **Pipeline Robustness:**
   - Incremental updates work without duplicates
   - Dry-run mode accurately previews changes
   - Clear logging at each pipeline stage

3. **Search Quality Impact:**
   - Embeddings generated from cleaned data
   - Search quality improvement validated in Phase 1 evaluation
   - Target: >3.5 average relevance score (from README success criteria)

---

## Future Enhancements (Post-Phase 1)

If Phase 1 evaluation shows cleaning quality issues:
- Add spacy-based sentence segmentation for better content extraction
- Implement NER to preserve mentions of technologies/tools
- Use BERTopic for semantic deduplication
- Fine-tune cleaning patterns based on failure analysis

For now: **Ship quick rule-based cleaning, validate with real search queries, iterate based on data.**
