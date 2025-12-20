# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
