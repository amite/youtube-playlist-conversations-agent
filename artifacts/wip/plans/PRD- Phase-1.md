PROJECT SUMMARY: YouTube Semantic Search Agent (Stateless, Single-Query)
=========================================================================

VISION:
A semantic search engine that helps users find the right YouTube videos to learn from—not by matching keywords, but by understanding what they're actually trying to do.

CONTEXT:
- Building a CLI-based semantic search tool for YouTube videos
- Each query is INDEPENDENT (no conversation history/multi-turn)
- Manual evaluation system to assess quality and iterate
- Phase 1 focus: Prove semantic search works, identify improvements needed

WHY THIS MATTERS:
YouTube has millions of videos, but keyword search is frustrating:
- Too many results that match words but not intent
- Hard to find videos at the right depth level (beginner vs advanced)
- Can't express nuanced needs ("recent videos from a specific creator" or "tutorials under 5 minutes")
- Quality videos get buried behind clickbait matches

Our semantic search engine solves this by understanding meaning, not just keywords.

CORE ARCHITECTURE:
Query → Embed → Search ChromaDB → Rank/Merge → Fetch from SQLite → Display → Manual Rating

ARCHITECTURAL DECISIONS:
✓ Stateless queries (each search is independent)
✓ SQLite for structured metadata, ChromaDB for vectors
✓ OpenAI embeddings API (text-embedding-3-small)
✓ Separate title and description embeddings (better quality than combined)
✓ Weighted score merging: title_similarity * 0.6 + description_similarity * 0.4
✓ Incremental indexing with is_indexed flag
✓ Manual CLI evaluation (no automation yet)

DATA SCHEMA (SQLite):
videos:
  - video_id (PK)
  - title
  - description
  - channel_id, channel_name
  - upload_date
  - views, likes, comments
  - duration_seconds
  - is_indexed (boolean, default 0)
  - metadata_json (text, nullable - future use)
  - created_at

embeddings_log:
  - log_id (PK)
  - video_id (FK)
  - embedding_type (enum: 'title', 'description')
  - model_version (e.g., 'text-embedding-3-small')
  - tokens_used
  - created_at

evaluation_results:
  - eval_id (PK)
  - query_text
  - result_video_ids (JSON array)
  - top_result_video_id
  - relevance_score (1-5)
  - best_result_position (1-5 or null)
  - notes (text)
  - failure_reason (text, if relevance < 3)
  - created_at

test_queries:
  - query_id (PK)
  - query_text
  - query_type (enum: 'topical', 'conceptual', 'technical', 'trend', 'tutorial')
  - expected_characteristics (text - what good results should have)
  - created_at

CHROMADB COLLECTIONS:
Collection 1: title_embeddings
  - id: video_id
  - embedding: [1536-dim vector]
  - metadata: {upload_date, views, duration}

Collection 2: description_embeddings
  - id: video_id
  - embedding: [1536-dim vector]
  - metadata: {upload_date, views, duration}

WHY SEPARATE EMBEDDINGS:
- Titles are concise, topic-focused (60 chars avg)
- Descriptions are detailed but noisy (2000 chars, social links, boilerplate)
- Concatenating dilutes title signal
- Separate embeddings allow weighted merging and A/B testing

INDEXING PROCESS:
1. Query SQLite for videos where is_indexed = 0
2. For each video:
   - Generate title embedding via OpenAI API
   - Generate description embedding via OpenAI API
   - Store both in respective ChromaDB collections with metadata
   - Log to embeddings_log table
   - Set is_indexed = 1
3. Batch processing for efficiency (handle rate limits)

SEARCH PROCESS:
1. User enters query via CLI
2. Generate query embedding via OpenAI API
3. Query title_embeddings collection → get top 10 results with similarity scores
4. Query description_embeddings collection → get top 10 results with similarity scores
5. Merge results with weighted scoring:
   final_score = (title_similarity * 0.6) + (description_similarity * 0.4)
6. Sort by final_score, take top 5
7. Fetch full video details from SQLite using video_ids
8. Display results with metadata visible

CLI COMMANDS:
index --limit N
  - Index N unindexed videos
  - Show progress bar and API cost estimate
  
search "query text"
  - Perform semantic search
  - Display top 5 results with scores and metadata
  
rate
  - Evaluate last search results
  - Prompts: relevance (1-5), best position (1-5), notes
  - Stores in evaluation_results table
  
evaluate-all
  - Run all test queries from test_queries table
  - Display results, prompt for ratings
  - Generate summary report
  
stats
  - Show evaluation statistics
  - Average relevance by query type
  - Common failure patterns

RESULT DISPLAY FORMAT:
Search: "machine learning tutorials"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Result #1: Complete Machine Learning Course
  Channel: freeCodeCamp | Date: 2024-03-15 | Duration: 4h 18m
  Views: 2.1M | Likes: 89K
  Title Match: 0.91 | Description Match: 0.85 | Final Score: 0.89

Result #2: ML Crash Course for Beginners
  Channel: TechWithTim | Date: 2024-01-20 | Duration: 45m
  Views: 450K | Likes: 18K
  Title Match: 0.88 | Description Match: 0.79 | Final Score: 0.85

[Results 3-5...]

Rate this search (1-5): _

SAMPLE QUERIES: Real Use Cases Our Engine Should Handle
========================================================

These queries represent actual user intents we're optimizing for:

**Learning & Tutorials**
- "Fetch me videos under 5 minutes that explain embeddings"
- "Show me videos that explain local ollama setup"
- "I need a video that helps me build my own AI engineer portfolio"
- "Show me top freecodecamp videos about building APIs with next js from 2025 only"
- "How to build my own mcp tutorial 2025 with at least 5k likes"
- "Stanford lecture on agents and rag"

**Current Knowledge & Recent Trends**
- "Show me 5 latest videos on vector search"
- "Show me last weeks updates from openai claude and Gemini"
- "Show me what's new from Anthropic"
- "There's a new langchain academy course"
- "2025 ibm videos on AI agents"

**Advanced Technical Topics**
- "Show me videos that show how to deploy an ai model to production"
- "Is there a video about the future of ui design in the age of AI?"
- "Advanced Rag techniques from 2025 only with more than 10k views"
- "Deep dive on agent architectures"
- "Document Rag techniques"
- "Advanced self healing rag"
- "Chunk optimisation in rag"
- "Context engineering video from nate b jones"

**Creator-Specific & Filtered Queries**
- "Which nate b jones videos are talking about prompting techniques?"
- "Adam Lucek videos"
- "Is there anything here that can help with few shot prompting?"
- "Claude agent harness"
- "Show me n8n 2.0 videos with at least 4 comments"

EVALUATION METHODOLOGY:
For each query:
- Run search
- Display results
- Rate relevance (1-5)
- Note which position has best result
- Write why it's good/bad
- Identify missing results

Metrics to Track:
- Average relevance score overall
- Average relevance by query type
- Top-1 accuracy (% where best result is position 1)
- Coverage (% of queries with at least 1 relevant result in top 5)
- Failure patterns (common reasons for relevance < 3)
- Query complexity vs success (simple vs complex filters)

PHASE 1 DEVELOPMENT PLAN (3 weeks at 28 hours/week):

Week 1: Core Infrastructure
Days 1-2 (8h): Setup + Schema
  - Project structure, dependencies [done]
  - SQLite schema creation
  - ChromaDB connection test
  - CLI skeleton with typer

Days 3-4 (8h): Indexing Pipeline
  - Get video dataset (500-1000 videos) [done]
  - Implement index command
  - Generate separate embeddings
  - Store in ChromaDB
  - Test with 50 videos

Days 5-7 (12h): Search Implementation
  - Query both collections
  - Score merging logic
  - SQLite hydration
  - Result display formatting
  - Test with 10 manual queries

Week 2: Evaluation System
Days 8-10 (12h): Manual Evaluation
  - Implement rate command
  - Store evaluations in database
  - Build stats/summary command
  - Create test query suite (30 queries)

Days 11-14 (16h): Test Query Execution
  - Implement evaluate-all command
  - Run all 30 test queries
  - Collect ratings manually
  - Document results
  - Identify failure patterns

Week 3: Analysis & Iteration
Days 15-17 (12h): Data Analysis
  - Query evaluation database
  - Calculate all metrics
  - Identify systematic failures
  - Analyze by query type
  - Create summary report

Days 18-21 (16h): Tuning & Documentation
  - Experiment with title/description weights
  - Test metadata boosting (views, date, duration)
  - Re-run evaluations
  - Compare before/after
  - Write README and documentation
  - Plan Phase 2 priorities

SUCCESS CRITERIA (Outcome-Focused):

**Core Search Quality**
- Index 500-1000 videos successfully
- Execute all sample queries (30+) with ratings
- Average relevance score > 3.5/5
- Achieve 60%+ top-1 accuracy (best result in position 1)
- Achieve 85%+ coverage (at least 1 relevant result in top 5)

**Query Type Performance**
- Learning queries: Capable of finding beginner-friendly, concise content
- Creator-specific: Successfully identify videos from named creators
- Advanced topics: Return specialized, deep technical content
- Time-filtered: Surface recent content appropriately (understand "2025", "last week")
- Filtered results: Handle queries with engagement/quality metrics (likes, views, comments)

**System Insights**
- Identify top 3 systematic failure patterns
- Understand which query types work well vs poorly
- Understand if separate embeddings matter for quality
- Document gaps in capabilities (missing features or limitations)
- Recommend Phase 2 priorities based on failure patterns

**Phase 1 Success = Proof That Semantic Search Adds Value**
Demonstrate that our semantic understanding outperforms simple keyword matching—i.e., that users would actually prefer this over YouTube's built-in search.

PHASE 1 SCOPE:
✓ Semantic search with vector similarity
✓ Manual quality evaluation
✓ Test query regression suite
✓ Incremental indexing
✓ CLI interface only

NON-GOALS (Phase 1):
✗ Multi-turn conversations
✗ Query intent classification
✗ Automated re-ranking
✗ Web UI
✗ Playlist management
✗ Real-time indexing
✗ Metadata enrichment (difficulty tagging, topic extraction)
✗ Query expansion or synonym handling

WHY STATELESS FOR PHASE 1:
- Simpler to build and debug
- Focuses on core semantic search quality
- Easier to evaluate (independent queries)
- Can add multi-turn later if evaluation shows need
- Lower cognitive overhead for first iteration

METADATA STRATEGY:
Phase 1: Store basic metadata (date, views, duration) but DON'T use for ranking
- Just display it alongside results
- Manually observe patterns (e.g., "recent" queries need date boosting)
- Document observations for Phase 2

Phase 2 (Future): Add metadata boosting based on Phase 1 findings
- Recency boosting for "recent developments" queries
- View count as quality signal
- Duration filtering for "deep dive" vs "quick tutorial"

EMBEDDING COST ESTIMATE:
Model: text-embedding-3-small
Cost: $0.00002 per 1K tokens
Average video: ~500 tokens (title + description)
1000 videos = ~500K tokens = ~$0.01

Very cheap. Main cost is query embeddings during development/testing.

KEY UNKNOWNS (To Answer in Phase 1):
1. Are separate title/description embeddings better than combined?
   → A/B test by trying both, compare eval scores

2. What query types work well vs poorly?
   → Track relevance by query_type in evaluation

3. Does metadata (views, date) improve ranking?
   → First see pure semantic results, then experiment with boosting

4. Is top-5 the right number of results?
   → Track how often best result is in positions 1-3 vs 4-5

5. What are systematic failure patterns?
   → Tag failures with reasons, find common themes

EXAMPLE TEST QUERIES BY TYPE (From Real Use Cases):

**Learning & Depth-Aware Queries** (understanding at specific level):
- "Fetch me videos under 5 minutes that explain embeddings"
- "Show me videos that explain local ollama setup"
- "I need a video that helps me build my own AI engineer portfolio"
- "Stanford lecture on agents and rag"

**Creator-Specific Searches** (finding content from a known creator):
- "Which nate b jones videos are talking about prompting techniques?"
- "Adam Lucek videos"
- "Context engineering video from nate b jones"

**Advanced Technical Topics** (specialized, deep knowledge):
- "Advanced Rag techniques from 2025 only with more than 10k views"
- "Deep dive on agent architectures"
- "Chunk optimisation in rag"
- "Advanced self healing rag"
- "Document Rag techniques"

**Filtered & Time-Specific** (with constraints):
- "Show me top freecodecamp videos about building APIs with next js from 2025 only"
- "How to build my own mcp tutorial 2025 with at least 5k likes"
- "Show me 5 latest videos on vector search"
- "Show me last weeks updates from openai claude and Gemini"
- "2025 ibm videos on AI agents"

**Current Knowledge & Trends** (recent/emerging):
- "Show me what's new from Anthropic"
- "There's a new langchain academy course"
- "Is there a video about the future of ui design in the age of AI?"

**Conceptual & Intent-Based** (finding understanding/answers):
- "Is there a video about the future of ui design in the age of AI?"
- "Is there anything here that can help with few shot prompting?"
- "Show me videos that show how to deploy an ai model to production"
- "Claude agent harness"
- "Show me n8n 2.0 videos with at least 4 comments"

CRITICAL ARCHITECTURAL NOTE:
NO localStorage or sessionStorage in artifacts (not supported in claude.ai)
For any future web UI, use React state (useState) only.

NEXT STEPS:
1. Create SQLite schema script
2. Set up ChromaDB connection
3. Build index command with progress tracking
4. Implement search with dual-collection querying
5. Add manual evaluation prompts
6. Create 30-query test suite
7. Run full evaluation cycle
8. Analyze and document findings