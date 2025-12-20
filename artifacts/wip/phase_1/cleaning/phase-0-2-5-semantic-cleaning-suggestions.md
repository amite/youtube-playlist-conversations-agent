Based on your project context, here are effective techniques for detecting semantic loss after cleaning:

## Statistical Analysis Techniques

**Keyword Preservation Analysis**
- Extract important keywords (nouns, verbs, technical terms) from original descriptions using NLP
- Check what percentage appear in cleaned versions
- Target: >90% of domain-specific terms (AI, API, tutorial, etc.) should remain
- Tools: spaCy for entity recognition, NLTK for keyword extraction

**Length-Based Heuristics**
- You've already tracked 39.1% reduction - now correlate this with content type
- Videos with >60% reduction deserve manual spot-checks
- Flag descriptions that became suspiciously short (<100 chars after cleaning)

## Embedding-Based Approaches

**Cosine Similarity Comparison**
Generate embeddings for both original and cleaned descriptions, measure similarity:
```python
# For each video:
original_embedding = get_embedding(original_desc)
cleaned_embedding = get_embedding(cleaned_desc)
similarity = cosine_similarity(original_embedding, cleaned_embedding)

# Flag if similarity < 0.85 (indicates significant semantic drift)
```
This is your most powerful tool - embeddings capture semantic meaning better than keyword matching.

**Cluster Coherence Test**
- Embed all original descriptions, perform k-means clustering
- Embed all cleaned descriptions, check if same videos stay in same clusters
- High cluster migration suggests semantic loss

## Manual Validation Strategies

**Stratified Sampling**
Review 30-50 videos across:
- High reduction rate (>50% length decrease)
- Low reduction rate (<20% length decrease)  
- Different video categories (tutorial, conceptual, technical)
- Short vs long original descriptions

**Topic Extraction Comparison**
- Use LDA or BERTopic to extract main topics from original descriptions
- Extract topics from cleaned descriptions
- Compare topic distributions - should be nearly identical

## Practical Implementation for Your Project

Given your Phase 0.2.5 goal, I'd recommend this workflow:

1. **Quick Statistical Pass** (1-2 hours)
   - Run keyword extraction on 50 random videos
   - Calculate preservation rate for technical terms
   - Flag outliers for manual review

2. **Embedding Similarity Analysis** (2-3 hours)
   - Generate embeddings for all 410 videos (both versions)
   - Calculate pairwise similarities
   - Create histogram of similarity scores
   - Manually inspect the bottom 10% (videos with lowest similarity)

3. **Manual Spot Checks** (2-3 hours)
   - Review 30 videos stratified by reduction rate
   - For each, ask: "Would I still find this video with the cleaned description?"
   - Document any semantic loss patterns

4. **Topic Coherence Test** (2-3 hours)
   - Cluster both datasets
   - Measure cluster stability
   - Verify videos on similar topics stay grouped

The **embedding similarity approach** is particularly well-suited for your project since you're already using OpenAI embeddings for search. If cleaned descriptions maintain >0.85 average cosine similarity with originals, you can confidently proceed to Phase 0.4.

Would you like me to create a Jupyter notebook artifact that implements the embedding similarity analysis? It would be the most efficient starting point for your validation.