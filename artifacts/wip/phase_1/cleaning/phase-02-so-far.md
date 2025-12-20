# YouTube Semantic Search Engine - Phase 1

### Project Overview

A semantic search engine for YouTube videos that lets you search a curated dataset using natural language queries. Phase 1 implements a CLI-based tool to:

1. **Index videos**: Generate OpenAI embeddings for titles and descriptions separately
2. **Search semantically**: Find relevant videos using weighted similarity matching
3. **Evaluate quality**: Manually rate results and identify improvement areas
4. **Track metrics**: Understand search performance by query type

The system uses:
- **ChromaDB** for vector similarity search (separate title/description collections)
- **SQLite** for structured metadata and evaluation tracking
- **OpenAI embeddings** for semantic understanding (text-embedding-3-small model)

# Work Done So Far: Phase 1 Data Cleaning Summary

## Overview
Successfully established a robust data ingestion and cleaning pipeline for the YouTube semantic search engine. The project transitioned from raw CSV data to a structured, cleaned SQLite database ready for embedding generation.

## Phase 0.1: Basic Cleaning & Database Setup
- **Database Schema:** Created `videos.db` with tables for `videos`, `embeddings_log`, `evaluation_results`, and `test_queries`.
- **Ingestion Pipeline:** Developed `scripts/ingest_csv.py` to load 410 unique videos (after removing 3 duplicates) into SQLite.
- **Basic Cleaning:** Implemented `utils/cleaning.py` to parse ISO 8601 durations/dates, handle view/like counts, and fill missing descriptions with `[No Description]`.
- **Incremental Updates:** Created `scripts/update_data.py` to handle new video additions without re-processing existing data.

## Phase 0.2: Semantic Cleaning
- **Noise Removal:** Implemented 12+ regex-based functions to strip URLs, timestamps, social CTAs, and boilerplate sections from titles and descriptions.
- **Content Preservation:** Focused on keeping core content (first 3 paragraphs) while normalizing whitespace and capitalization (preserving technical acronyms like AI, API, LLM).
- **Results:** Achieved a **39.1% average reduction** in description length across all 410 videos, significantly improving signal-to-noise ratio for embeddings.
- **Validation:** Built `scripts/validate_cleaning.py` for side-by-side comparison and `scripts/data_stats.py` for tracking cleaning metrics.

## Database Migration & Tooling
- **Migration System:** Implemented a lightweight, dependency-free migration engine (`scripts/migrate.py`) to manage schema evolution safely.
- **Query Tooling:** Created 11 `litecli`-compatible SQL scripts in `scripts/queries/` for interactive database analysis with syntax highlighting.

## Current State & Next Steps
- **Status:** Phase 0.2 is complete and validated.
- **Next Phase (0.2.5):** Perform deep semantic loss analysis via Jupyter notebook to verify keyword preservation (>90%) and topic coherence (>95%) before proceeding to Phase 0.4 (Embedding Generation).
