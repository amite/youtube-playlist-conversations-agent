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

### Quick Start

**Step 1: Setup**
```bash
# Install dependencies
uv sync
```

**Step 2: Configure API Keys**
Create a `.env` file:
```
OPENAI_API_KEY=sk-...  # Get from https://platform.openai.com/api-keys
YOUTUBE_API_KEY=...     # Get from Google Cloud Console (if populating new video data)
```

**Step 3: Index Videos**
```bash
# Index 50 videos into ChromaDB
uv run python main.py index --limit 50
```

**Step 4: Search**
```bash
# Perform a semantic search
uv run python main.py search "machine learning tutorials"

# Rate the results
uv run python main.py rate

# View stats
uv run python main.py stats
```

**Step 5: Evaluate Search Quality**
```bash
# Run all test queries and collect ratings
uv run python main.py evaluate-all
```

---

## Architecture & Design

### System Components

1. **SQLite Database** (`data/videos.db`)
   - `videos`: Video metadata (title, description, channel, stats, is_indexed flag)
   - `embeddings_log`: Track embedding generation (model, tokens, timestamps)
   - `evaluation_results`: Manual ratings and relevance assessments
   - `test_queries`: Test query suite for systematic evaluation

2. **ChromaDB Vector Store**
   - `title_embeddings`: 1536-dim embeddings of video titles
   - `description_embeddings`: 1536-dim embeddings of video descriptions
   - Separate collections for better semantic quality and A/B testing

3. **Search Pipeline**
   - Generate query embedding via OpenAI API
   - Query both ChromaDB collections independently
   - Merge with weighted scoring: `(title_score * 0.6) + (description_score * 0.4)`
   - Fetch full metadata from SQLite
   - Display top 5 ranked results

4. **Evaluation Framework**
   - Manual rating system (1-5 relevance score)
   - Test query suite across 5 types: topical, conceptual, technical, trend, tutorial
   - Metrics: average relevance, top-1 accuracy, coverage, failure patterns
   - Query type analysis to identify what works vs fails

### Why This Design?

**Separate Title/Description Embeddings**
- Titles are concise and focused (~60 chars)
- Descriptions are detailed but noisy (~2000 chars with links, boilerplate)
- Concatenating dilutes the title signal
- Separate collections enable weighted merging and experimentation

**Stateless Architecture**
- Each search is independent (no conversation history)
- Simpler to evaluate and improve systematically
- Multi-turn support can be added in Phase 2 if data shows it's needed

**Manual Evaluation First**
- Identify systematic failure patterns before adding automation
- Gather evidence about what helps (metadata boosting, query expansion, etc.)
- Data-driven approach to Phase 2 priorities

---

## Phase 1 Goals & Success Criteria

### Goals
- ✅ Index 500-1000 videos successfully
- ✅ Execute 30 test queries with manual ratings
- ✅ Calculate metrics: average relevance, coverage, failure patterns
- ✅ Understand if separate embeddings matter
- ✅ Document what improvements are needed

### Success Criteria
- Average relevance score > 3.5/5
- Top-1 accuracy (best result in position 1) > 40%
- Coverage (at least 1 relevant result in top 5) > 80%
- Identify top 3 systematic failure patterns

---

## Test Query Suite

Example queries by type:

**Topical** (specific subject)
- "React hooks tutorial"
- "Python pandas dataframe manipulation"
- "CSS grid layout examples"

**Conceptual** (understanding/comparison)
- "Difference between SQL and NoSQL"
- "What is Docker and why use it"
- "REST vs GraphQL pros and cons"

**Technical** (how-to/implementation)
- "Implement merge sort in Python"
- "Build REST API with Node.js"
- "Set up CI/CD pipeline with GitHub Actions"

**Trend** (recent/current)
- "AI developments 2024"
- "Latest JavaScript features"
- "New React 19 features"

**Tutorial** (learning-focused)
- "Machine learning for beginners"
- "Learn TypeScript from scratch"
- "Web development roadmap 2024"

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Invalid API key" | Check `.env` file, verify OpenAI API key is valid |
| "ChromaDB collection not found" | Run `index --limit N` to populate embeddings first |
| "No results for search" | Verify videos are indexed; try simpler query |
| "High token costs" | Use `index --limit 10` for testing before full indexing |
| "Slow searches" | Ensure ChromaDB is fully loaded; check system RAM |

---

## Use Cases

✅ **Semantic Search**: Find videos by meaning, not just keywords
✅ **Quality Evaluation**: Understand search limitations and improve systematically
✅ **Dataset Exploration**: Browse curated video collections semantically
✅ **Research**: Extract patterns about what queries work well
✅ **Phase 2 Planning**: Data-driven roadmap for improvements