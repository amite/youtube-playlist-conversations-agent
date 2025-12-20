# Phase 0.2.5: Semantic Loss Analysis via Jupyter Notebook

## Overview

Create a comprehensive Jupyter notebook to validate semantic cleaning quality beyond the basic validation script. This phase provides deeper confidence that the cleaning preserved core technical content before proceeding to embedding generation (Phase 0.4).

## Rationale

While `validate_cleaning.py` provides side-by-side comparison of 20 samples, a notebook-based analysis enables:
1. **Keyword preservation analysis** - Verify technical terms survive cleaning
2. **Topic coherence validation** - Check that cleaned descriptions still convey core topics
3. **High-reduction case review** - Manual inspection of videos with >60% reduction
4. **Statistical distribution analysis** - Understand cleaning behavior across dataset
5. **Iterative exploration** - Easy to adjust analysis as needed

**Why this matters:** With 39.1% average reduction, we want to ensure embeddings generated in Phase 0.4 will be based on semantically complete data.

## Implementation Plan

### Step 1: Create Notebook Structure

**File:** `notebooks/semantic_cleaning_analysis.ipynb`

**Sections:**
1. Setup & Data Loading
2. Overall Statistics
3. Keyword Preservation Analysis
4. High-Reduction Case Review
5. Topic Coherence Spot Checks
6. Recommendations

### Step 2: Overall Statistics Analysis

**Queries to run:**
```python
# Distribution of description length reduction
# Histogram showing % reduction across all 410 videos
# Identify outliers (>70% reduction)

# Count of videos by reduction bucket
# 0-20%, 20-40%, 40-60%, 60-80%, 80%+

# Title vs description reduction comparison
# Validate that titles are minimally modified
```

**Expected insights:**
- Most videos in 30-50% reduction range
- Few outliers with extreme reduction
- Titles mostly unchanged (0-5% reduction)

### Step 3: Keyword Preservation Analysis

**Approach:**
1. Extract top 50 technical keywords from raw descriptions using frequency analysis
   - AI, API, LLM, Python, Django, React, Docker, etc.
2. Check if these keywords appear in cleaned descriptions
3. Calculate preservation rate (% of keywords that survived)

**Success criteria:**
- 90%+ preservation of top technical terms
- Core domain keywords (AI, API, Python) should be 100% preserved

### Step 4: High-Reduction Case Review

**Queries:**
```python
# Get all videos with >60% description reduction
# Show side-by-side comparison for manual review
# Flag if cleaned description is <100 chars
```

**Analysis:**
- Manual review of 10-15 high-reduction cases
- Verify that core content summary is preserved
- Document any over-cleaning patterns detected

### Step 5: Topic Coherence Validation

**Approach:**
1. Sample 20 random videos across all reduction ranges
2. For each, extract:
   - Raw description main topics (first 2 sentences)
   - Cleaned description main topics
   - Compare semantic similarity subjectively
3. Rate coherence: "Core topic preserved? Yes/No"

**Success criteria:**
- 95%+ of samples preserve core topic
- If <90%, identify patterns for improvement

### Step 6: Generate Recommendations

Based on analysis, document:
- ✅ Cleaning is ready for Phase 0.4 (embedding generation)
- ⚠️ Minor adjustments needed (list specific patterns)
- ❌ Major issues found (re-run cleaning with updated patterns)

## Files to Create/Modify

### Create (1 new file)
- `notebooks/semantic_cleaning_analysis.ipynb` (new notebook)

### Read-only dependencies
- `data/videos.db` (read cleaned data)
- `utils/cleaning.py` (reference cleaning functions)

## Success Criteria

- ✅ Notebook runs end-to-end without errors
- ✅ Keyword preservation rate >90%
- ✅ Topic coherence validation >95%
- ✅ High-reduction cases manually reviewed and documented
- ✅ Clear recommendation provided (proceed to Phase 0.4 or iterate)

## Estimated Effort

**Total:** 1-1.5 hours

- Notebook setup: 15 min
- Statistics analysis: 15 min
- Keyword preservation: 20 min
- High-reduction review: 20 min
- Topic coherence validation: 20 min
- Documentation: 10 min

## Next Steps After Phase 0.2.5

**If validation passes (expected):**
- Proceed directly to Phase 0.4: Embedding Generation
- Use `cleaned_title` and `cleaned_description` for embeddings
- Compare search quality with Phase 0.1 baseline

**If issues detected:**
- Update cleaning patterns in `utils/cleaning.py`
- Re-run `apply_semantic_cleaning.py` on all 410 videos
- Re-run Phase 0.2.5 analysis to confirm fixes

## Critical Files

**Create:**
- `notebooks/semantic_cleaning_analysis.ipynb`

**Read:**
- `data/videos.db`
- `utils/cleaning.py`
- `scripts/data_stats.py` (for reference)
- `notebooks/yt_stats.ipynb` (existing notebook structure as template)

## Technical Notes

**Notebook dependencies:**
- pandas (already in project)
- sqlite3 (standard library)
- matplotlib/seaborn for visualizations (optional, add if needed)

**Analysis approach:**
- Focus on qualitative validation (manual review)
- Quantitative metrics (keyword preservation %) as supporting evidence
- Prioritize actionability: clear go/no-go decision for Phase 0.4
