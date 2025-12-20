# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference for Plan Mode

**Last Verified**: 2025-12-20 | **Status**: Current ✓

**Project**: YouTube semantic search engine (Phase 1: CLI-based evaluation)

**System Pipeline**: Query → OpenAI Embed (text-embedding-3-small, 1536 dims) → ChromaDB search (title_embeddings + description_embeddings) → Weighted merge (60% title + 40% description) → SQLite fetch → Display + Manual rating

**Main Entry Point**: [main.py](main.py) - Typer CLI with commands: index, search, rate, evaluate-all, stats

**Data Storage**:
- **SQLite** (`data/videos.db`): Videos metadata, embeddings log, evaluation results, test queries
  - `videos`: video_id, title, description, channel_name, published_at, duration, views, likes, is_indexed
  - `embeddings_log`: Tracks embedding generation (model, tokens, timestamps, cost)
  - `evaluation_results`: Manual ratings (query, rating 1-5, best_position, notes)
  - `test_queries`: Test suite (~30 queries) with query_text, query_type
- **ChromaDB**: Two collections with 1536-dim embeddings (title_embeddings, description_embeddings)

**Critical Design Patterns**:
- Separate title/description embeddings → enables weighted merging and A/B testing
- `is_indexed` flag → prevents re-embedding videos
- Incremental indexing → reduces API costs
- Manual evaluation strategy → Phase 1 focuses on quality assessment before automation

**Common Changes in Plan Mode**:
1. Adjust embedding weights (search ranking, default 60% title / 40% description)
2. Add evaluation metrics (new stats output, query the evaluation_results table)
3. Extend test query suite (add rows to test_queries, run evaluate-all)
4. Optimize indexing (check is_indexed flag, update embeddings_log)

**Important Constraints**:
- Never read entire CSV files from `data/` folder (use SQL queries instead)
- Preserve backward compatibility with ChromaDB collections
- Always verify embedding model is text-embedding-3-small before changes
- Test with `evaluate-all` after search pipeline changes

---

## Project Overview

A semantic search engine for YouTube videos. Phase 1 builds a stateless CLI-based semantic search tool that allows users to query a curated set of YouTube videos and get relevant results ranked by semantic similarity. The system uses OpenAI embeddings with ChromaDB for vector search and SQLite for structured metadata storage.

**Phase 1 Focus**: Prove semantic search works, evaluate search quality with manual ratings, and identify improvements needed for future phases.

## Commands

### Development Setup
```bash
# Install dependencies using uv (required)
uv sync
```

### CLI Commands

**index --limit N**
- Index N unindexed videos from SQLite into ChromaDB
- Generates separate embeddings for titles and descriptions
- Shows progress bar and API cost estimate

**search "query text"**
- Perform semantic search across indexed videos
- Returns top 5 results ranked by weighted similarity score
- Displays metadata: channel, date, duration, views, likes, similarity scores

**rate**
- Evaluate the last search results (1-5 relevance score)
- Note which position had the best result
- Store evaluation in database for analysis

**evaluate-all**
- Run all test queries from test_queries table
- Collect manual ratings for each
- Generate summary report with metrics

**stats**
- Show evaluation statistics and patterns
- Average relevance by query type
- Identify common failure reasons

### Getting Help
```bash
uv run python main.py --help
uv run python main.py <command> --help
```

## Architecture

### System Design

```
Query → Embed (OpenAI API) → Search ChromaDB → Rank/Merge →
Fetch from SQLite → Display Results → Manual Rating
```

### Main Components

**[main.py](main.py) - CLI Entry Point**
- Typer CLI interface for all commands (index, search, rate, evaluate-all, stats)
- Handles user input and output formatting

**Database Layer**
- **SQLite** (`data/videos.db`): Stores structured metadata for all videos
  - `videos` table: video_id, title, description, channel info, stats, is_indexed flag
  - `embeddings_log` table: Track embedding generation (model, tokens, timestamps)
  - `evaluation_results` table: Manual ratings for search quality assessment
  - `test_queries` table: Test query suite for systematic evaluation

- **ChromaDB**: Vector database with two collections
  - `title_embeddings`: 1536-dim embeddings of video titles
  - `description_embeddings`: 1536-dim embeddings of video descriptions
  - Separate collections allow weighted merging and A/B testing

**Search Pipeline**
1. Generate query embedding via OpenAI API (text-embedding-3-small)
2. Query title_embeddings collection → top 10 results with scores
3. Query description_embeddings collection → top 10 results with scores
4. Merge with weighted scoring: `(title_similarity * 0.6) + (description_similarity * 0.4)`
5. Fetch full video details from SQLite for top 5 results
6. Display with formatted output

**Evaluation System**
- Manual rating interface: Rate relevance (1-5), note best result position, add notes
- Test query suite: 30+ curated queries across types (topical, conceptual, technical, trend, tutorial)
- Metrics tracking: Average relevance, top-1 accuracy, coverage, failure patterns

### Configuration

**Environment Variables** (.env)
- `OPENAI_API_KEY` - OpenAI API key for embeddings (required)
- `YOUTUBE_API_KEY` - YouTube Data API key (for data collection, if still scraping)

**Embedding Model**
- Model: `text-embedding-3-small` (1536 dimensions)
- Cost: $0.00002 per 1K tokens (~$0.01 for 1000 videos)

## Key Design Notes

**Why Separate Title/Description Embeddings**
- Titles are concise and topic-focused (~60 chars avg)
- Descriptions are detailed but noisy (~2000 chars, links, boilerplate)
- Concatenating dilutes the title signal for semantic search
- Separate embeddings enable weighted merging (60% title, 40% description) and A/B testing

**Stateless Architecture**
- Each search query is independent (no conversation history)
- Simpler to build, debug, and evaluate
- Multi-turn support can be added in Phase 2 if needed

**Incremental Indexing**
- Videos marked with `is_indexed` flag to track embedding status
- Index new videos without re-processing existing ones
- Reduces API costs and enables incremental dataset growth

**Manual Evaluation Strategy**
- Phase 1 focuses on manual quality assessment with a test query suite
- Identifies systematic failure patterns before adding automated improvements
- Gathers data on what query types work vs fail
- Informs Phase 2 priorities (metadata boosting, query understanding, etc.)

## Documentation Structure

**Plan Mode Plans**
- IMPORTANT: When finishing a plan in plan mode, always write the plan to disk
- Save plans to `artifacts/wip/plans/` folder
- Naming convention: descriptive name (e.g., `semantic-cleaning-plan.md`, `api-refactor-plan.md`)
- Include: objectives, implementation steps, affected files, testing strategy, any architectural decisions

**Phase Completion Reports**
- IMPORTANT: All phase completion reports must be saved in `artifacts/wip/phase_1/cleaning/` folder
- Format: `phase-0-X-completion-report.md` where X is the phase number
- These reports document what was built, validation results, and next steps
- Do NOT save completion reports in `.claude/` folder

**Session Summaries**
- Session summaries should be saved in `.claude/session-summaries/` (created automatically by session-refiner skill)
- Use timestamp format: `YYYYMMDD-topic.md`

## Database Migrations

The project uses a lightweight, custom migration system to manage SQLite schema evolution safely. No external dependencies (no Alembic).

### Migration System Overview

**How It Works**
- Migrations live in `scripts/migrations/versions/` as Python files
- Each migration file has `upgrade(conn)` and `downgrade(conn)` functions
- Schema version is tracked in a `schema_version` table in the database
- Migrations are applied in order and can be rolled back

**CLI Commands** (all from project root)
```bash
# Check current migration status
uv run python scripts/migrate.py status

# Apply pending migrations
uv run python scripts/migrate.py upgrade

# Apply migrations up to specific version
uv run python scripts/migrate.py upgrade --to 3

# Rollback last migration
uv run python scripts/migrate.py downgrade

# Rollback multiple migrations
uv run python scripts/migrate.py downgrade --steps 2

# Create a new migration file
uv run python scripts/migrate.py create "add video tags table"
```

### Creating a New Migration

1. **Create migration file**
   ```bash
   uv run python scripts/migrate.py create "my feature name"
   ```
   This generates `scripts/migrations/versions/00X_my_feature_name.py`

2. **Edit the migration file**
   ```python
   def upgrade(conn):
       """Apply migration."""
       cursor = conn.cursor()
       cursor.execute("""
           ALTER TABLE videos ADD COLUMN new_field TEXT
       """)
       conn.commit()

   def downgrade(conn):
       """Rollback migration."""
       cursor = conn.cursor()
       cursor.execute("ALTER TABLE videos DROP COLUMN new_field")
       conn.commit()
   ```

3. **Test the migration**
   ```bash
   uv run python scripts/migrate.py upgrade
   # Test that the change works
   uv run python scripts/migrate.py downgrade
   # Verify rollback works
   uv run python scripts/migrate.py upgrade
   ```

### Migration Best Practices

**Safe Migrations** (low risk, use migrations):
- Adding nullable columns: `ALTER TABLE videos ADD COLUMN new_field TEXT`
- Adding new tables: `CREATE TABLE new_table (...)`
- Adding indexes: `CREATE INDEX idx_name ON table(column)`
- Renaming columns with data copy (CREATE new, copy data, DROP old)

**Breaking Changes** (high complexity, consider re-creating database):
- Changing primary key structure
- Major schema refactoring (3+ tables affected)
- SQLite type changes (not supported by ALTER TABLE)
- When migration complexity > value of preserving data

**When to Drop and Re-ingest** (if data is not critical):
- Early prototyping phase
- Schema experiments
- Breaking changes where migration cost exceeds re-ingestion cost

**Critical Data to Preserve** (always migrate if possible):
- `evaluation_results` table (manual ratings are valuable)
- `embeddings_log` table (API cost tracking and embedding history)

---

## Working with Data Files

**Large CSV Files in @data Folder**
- IMPORTANT: Never read entire CSV files from the `data/` directory
- Always sample only 20-30 records when examining CSV files using the offset and limit parameters
- Use `head` command via bash for quick inspection, or read with line limits via Read tool
- This prevents unnecessary context usage and keeps Claude Code responsive
- For analysis across the entire dataset, use pandas or SQL queries within scripts, not by reading the file directly

## Common Development Tasks

**Add a new evaluation metric**
1. Query the `evaluation_results` table with specific criteria
2. Calculate aggregate (avg, count, etc.) using SQL or pandas
3. Add to `stats` command output

**Extend the test query suite**
1. Add new rows to `test_queries` table with query_text and query_type
2. Run `evaluate-all` to execute and collect ratings
3. Analyze patterns by query_type in stats

**Experiment with embedding weights**
1. Modify the weight constants in the search merging logic
2. Re-run evaluation suite with new weights
3. Compare metrics before/after in stats output

**Debug embedding issues**
1. Check OpenAI API key is valid in .env
2. Verify ChromaDB collections are created and populated
3. Check `embeddings_log` table for failed indexing attempts
4. Monitor API token usage in logs
