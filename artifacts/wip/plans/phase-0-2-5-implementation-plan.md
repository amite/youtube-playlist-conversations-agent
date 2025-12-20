# Phase 0.2.5: Semantic Loss Analysis - Implementation Plan

## Executive Summary

**Goal**: Validate Phase 0.2 semantic cleaning quality through notebook-based analysis before proceeding to Phase 0.4 (Embedding Generation).

**Current Status**: Phase 0.2 complete (410 videos cleaned, 39.1% avg description reduction)

**Decision**: Implement a **pragmatic, lightweight approach** using existing dependencies rather than the sophisticated NLP-based suggestions.

## Feasibility Analysis of Suggested Approaches

### Suggestions from phase-0-2-5-semantic-cleaning-suggestions.md

I evaluated three categories of semantic loss detection techniques:

#### 1. **Statistical Analysis (Keyword Preservation)** ✅ FEASIBLE & RECOMMENDED
- **Suggested**: Use spaCy/NLTK for keyword extraction
- **Reality Check**: Would require adding new dependencies (spaCy ~500MB download, NLTK setup)
- **Pragmatic Alternative**: Use regex-based keyword matching for technical terms
- **Verdict**: IMPLEMENT with simplified approach (no new NLP dependencies)

#### 2. **Embedding-Based Approaches (Cosine Similarity)** ❌ NOT FEASIBLE YET
- **Suggested**: Generate embeddings for raw vs cleaned descriptions, compare similarity
- **Reality Check**: Requires OpenAI API integration, which doesn't exist yet (Phase 0.4)
- **Cost**: ~$0.01-0.02 for 820 embeddings (410 videos × 2 versions)
- **Complexity**: Would need to implement embedding pipeline just for validation
- **Verdict**: SKIP - this is circular logic (validating cleaning before embeddings by generating embeddings)

#### 3. **Manual Validation (Stratified Sampling)** ✅ ALREADY DONE + EXTEND
- **Suggested**: Review 30-50 videos across reduction ranges
- **Reality Check**: `validate_cleaning.py` already does this with 20 samples
- **Extension**: Add stratified sampling in notebook for deeper analysis
- **Verdict**: IMPLEMENT as core validation method

### Recommendation: Hybrid Pragmatic Approach

**What to implement:**
1. ✅ Statistical keyword preservation (regex-based, no new deps)
2. ✅ High-reduction case review (manual, stratified)
3. ✅ Topic coherence spot checks (manual, qualitative)
4. ✅ Distribution analysis (pandas + matplotlib)
5. ❌ Skip embedding similarity (premature, circular dependency)

**Why this is sufficient:**
- Achieves the goal: validate semantic preservation
- Uses existing tools: pandas, matplotlib, regex
- No new dependencies: keeps project lightweight
- Actionable results: clear go/no-go for Phase 0.4
- Conservative approach: manual review catches edge cases

## Implementation Plan

### Prerequisites Check

**Dependencies needed:**
- ✅ pandas (already installed)
- ✅ numpy (already installed)
- ✅ sqlite3 (standard library)
- ⚠️ matplotlib (NOT installed - need to add to pyproject.toml)

**Action**: Add `matplotlib>=3.8.0` to dependencies before starting

### Notebook Structure

**File**: `notebooks/semantic_cleaning_analysis.ipynb`

**Sections** (6 total):

#### Section 1: Setup & Data Loading (10 min)
```python
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Load data from videos.db
# Select: video_id, title, cleaned_title, description, cleaned_description
# Calculate reduction percentages for each video
```

#### Section 2: Overall Statistics (15 min)
**Analyses:**
1. Histogram of description length reduction (% bins: 0-20%, 20-40%, 40-60%, 60%+)
2. Title vs description reduction comparison (bar chart)
3. Count of videos by reduction bucket
4. Identify outliers (>70% reduction)

**Validation targets:**
- Most videos in 30-50% reduction range ✓
- Few outliers (<10 videos) with >70% reduction
- Titles minimally modified (<5% avg reduction)

#### Section 3: Keyword Preservation Analysis (20 min)
**Approach:**
1. Define top 50 technical keywords manually:
   - AI, API, LLM, Python, Django, React, Docker, Kubernetes, ML, RAG, etc.
2. For each keyword:
   - Count appearances in raw descriptions
   - Count appearances in cleaned descriptions
   - Calculate preservation rate: `cleaned_count / raw_count`
3. Overall preservation metric: Average across all keywords

**Success criteria:**
- 90%+ preservation of technical terms
- Core terms (AI, API, Python) at 100% preservation

**Implementation**:
```python
# Define keyword list
technical_keywords = ['AI', 'API', 'LLM', 'Python', 'Django', 'React', ...]

# Count keyword occurrences
preservation_rates = {}
for keyword in technical_keywords:
    raw_count = df['description'].str.contains(keyword, case=False).sum()
    cleaned_count = df['cleaned_description'].str.contains(keyword, case=False).sum()
    if raw_count > 0:
        preservation_rates[keyword] = cleaned_count / raw_count
```

#### Section 4: High-Reduction Case Review (20 min)
**Queries:**
```sql
SELECT video_id, title,
       LENGTH(description) as raw_len,
       LENGTH(cleaned_description) as cleaned_len,
       ROUND((1 - LENGTH(cleaned_description) * 1.0 / LENGTH(description)) * 100, 1) as reduction_pct
FROM videos
WHERE cleaned_description IS NOT NULL
  AND LENGTH(description) > 100
  AND (1 - LENGTH(cleaned_description) * 1.0 / LENGTH(description)) > 0.60
ORDER BY reduction_pct DESC
LIMIT 15;
```

**Manual review:**
- Display side-by-side: raw description (first 500 chars) vs cleaned (full)
- Flag: cleaned < 100 chars when raw > 500 chars
- Document patterns: over-aggressive boilerplate removal, lost context, etc.

#### Section 5: Topic Coherence Spot Checks (20 min)
**Approach:**
1. Stratified random sample: 20 videos across reduction ranges
   - 5 videos: 0-25% reduction
   - 5 videos: 25-40% reduction
   - 5 videos: 40-60% reduction
   - 5 videos: >60% reduction
2. For each video:
   - Show title + first 2 sentences of raw description
   - Show full cleaned description
   - Manual assessment: "Core topic preserved? Yes/No/Partial"

**Success criteria:**
- 95%+ rated as "Yes" (core topic preserved)
- <10% rated as "Partial" (minor loss acceptable)
- 0% rated as "No" (critical loss)

#### Section 6: Recommendations & Go/No-Go Decision (10 min)
**Decision tree:**
```
IF keyword_preservation >= 90% AND topic_coherence >= 95% AND outliers < 5%:
    ✅ PROCEED to Phase 0.4 (Embedding Generation)
ELSE IF keyword_preservation >= 85% AND topic_coherence >= 90%:
    ⚠️ MINOR ISSUES - document patterns, consider Phase 0.4 with notes
ELSE:
    ❌ MAJOR ISSUES - fix cleaning patterns, re-run Phase 0.2
```

**Document:**
- Summary of findings (bullet points)
- Specific patterns detected (if any)
- Recommendation with rationale
- Next steps

## Files to Create/Modify

### Create (1 file)
- `notebooks/semantic_cleaning_analysis.ipynb`

### Modify (1 file)
- `pyproject.toml` - Add `matplotlib>=3.8.0` to dependencies

### Read-only (reference)
- `data/videos.db` - Source of cleaned data
- `utils/cleaning.py` - Reference for cleaning logic
- `notebooks/yt_stats.ipynb` - Template for notebook structure

## Success Criteria

- ✅ Notebook runs end-to-end without errors
- ✅ Keyword preservation rate >90% (or document why <90% is acceptable)
- ✅ Topic coherence validation >95%
- ✅ High-reduction cases reviewed and patterns documented
- ✅ Clear go/no-go recommendation with rationale

## Why This Approach is Better Than Suggestions

### 1. No Circular Dependency (Embeddings)
**Suggestion**: Generate embeddings for validation
**Problem**: We haven't built the embedding pipeline yet (Phase 0.4)
**Solution**: Use manual + statistical validation instead

### 2. No Heavy Dependencies (NLP Libraries)
**Suggestion**: Use spaCy/NLTK for keyword extraction
**Problem**: Adds 500MB+ to project, requires model downloads
**Solution**: Regex-based keyword matching (good enough for technical terms)

### 3. Pragmatic Manual Review
**Suggestion**: Automated topic coherence via LDA/BERTopic
**Problem**: Overkill for 410 videos, requires new libraries
**Solution**: Manual spot-check 20 videos (1-2 hours, high confidence)

### 4. Actionable Results
**Suggestion**: Deep statistical analysis across multiple metrics
**Problem**: Can lead to analysis paralysis
**Solution**: Focus on 3 key metrics (keyword, coherence, outliers) → clear decision

## Estimated Effort

**Total**: 1.5 hours

- Setup & dependencies: 10 min
- Data loading: 10 min
- Overall statistics: 15 min
- Keyword preservation: 20 min
- High-reduction review: 20 min
- Topic coherence validation: 20 min
- Recommendations: 10 min
- Documentation: 15 min

## Next Steps After Phase 0.2.5

**If validation passes (expected):**
1. Commit notebook + analysis results
2. Update project docs with validation summary
3. Proceed to Phase 0.4: Embedding Generation
4. Use `cleaned_title` and `cleaned_description` for embeddings

**If issues detected:**
1. Document specific over-cleaning patterns
2. Update cleaning functions in `utils/cleaning.py`
3. Re-run `apply_semantic_cleaning.py --full`
4. Re-run Phase 0.2.5 validation
5. Proceed to Phase 0.4 only after validation passes

## Critical Files

**Create:**
- `notebooks/semantic_cleaning_analysis.ipynb` (main deliverable)

**Modify:**
- `pyproject.toml` (add matplotlib)

**Reference:**
- `data/videos.db` (410 videos with cleaned data)
- `utils/cleaning.py` (cleaning functions)
- `scripts/data_stats.py` (validation metrics)
- `notebooks/yt_stats.ipynb` (notebook template)

## Technical Keywords List (50 terms)

Core technical terms to track in keyword preservation analysis:

**AI/ML**: AI, ML, LLM, GPT, RAG, embedding, model, neural, deep learning, machine learning, NLP, computer vision, transformer, attention

**Programming**: Python, JavaScript, TypeScript, React, Django, Flask, Node, Express, API, REST, GraphQL, SQL, PostgreSQL, MongoDB, Redis

**DevOps**: Docker, Kubernetes, AWS, GCP, Azure, CI/CD, deployment, containerization, microservices, serverless

**Tools**: Git, GitHub, VS Code, Jupyter, notebook, CLI, terminal, shell, bash

**Concepts**: tutorial, guide, example, documentation, architecture, pattern, best practice, optimization, performance, security

---

## Implementation Steps (Execution Order)

### Step 1: Add matplotlib dependency
1. Edit `pyproject.toml`
2. Add `"matplotlib>=3.8.0",` to the dependencies list
3. Run `uv sync` to install matplotlib

### Step 2: Create notebook structure
1. Create `notebooks/semantic_cleaning_analysis.ipynb`
2. Add 6 sections as outlined above
3. Start with imports and data loading

### Step 3: Implement analysis sections in order
1. Section 1: Setup & Data Loading (connect to SQLite, load videos)
2. Section 2: Overall Statistics (histograms, reduction distribution)
3. Section 3: Keyword Preservation (regex-based, 50 technical terms)
4. Section 4: High-Reduction Cases (manual review of >60% reduction)
5. Section 5: Topic Coherence (stratified sampling, manual assessment)
6. Section 6: Recommendations (go/no-go decision)

### Step 4: Validation & Documentation
1. Run notebook end-to-end
2. Verify all metrics meet success criteria
3. Document findings in final section
4. Make go/no-go recommendation for Phase 0.4

### Step 5: Commit & Report
1. Commit notebook to git
2. Update session summary with validation results
3. Create Phase 0.2.5 completion report in `artifacts/wip/phase_1/cleaning/`

---

## User Confirmation ✅

**Decision confirmed**: Pragmatic approach (regex + manual review + matplotlib)
- No embedding similarity validation (premature, Phase 0.4 dependency)
- No heavy NLP libraries (overkill for this validation)
- Focus on actionable results with existing tools

**Status**: Ready to implement
**Blocker**: None (matplotlib will be added in Step 1)
**Expected outcome**: Clear validation that Phase 0.2 cleaning is ready for Phase 0.4 embeddings
**Expected duration**: 1.5 hours
