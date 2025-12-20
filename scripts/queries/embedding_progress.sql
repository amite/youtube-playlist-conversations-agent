-- Embedding Progress Tracking
-- Monitor embedding generation progress and API usage
-- Usage: sqlite3 -header -column data/videos.db < scripts/queries/embedding_progress.sql

.headers on
.mode column

SELECT '=== EMBEDDING GENERATION STATUS ===' as section;
SELECT '';

SELECT
    'Total Videos' as metric,
    COUNT(*) as value
FROM videos
UNION ALL
SELECT
    'Indexed (is_indexed=1)',
    SUM(CASE WHEN is_indexed = 1 THEN 1 ELSE 0 END)
FROM videos
UNION ALL
SELECT
    'Unindexed (is_indexed=0)',
    SUM(CASE WHEN is_indexed = 0 THEN 1 ELSE 0 END)
FROM videos
UNION ALL
SELECT
    'Indexing Progress %',
    ROUND(SUM(CASE WHEN is_indexed = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM videos;

SELECT '';
SELECT '=== EMBEDDINGS LOG SUMMARY ===' as section;
SELECT '';

SELECT
    COALESCE(embedding_type, 'NO EMBEDDINGS') as embedding_type,
    COUNT(*) as embeddings_generated,
    SUM(token_count) as total_tokens,
    ROUND(AVG(token_count), 0) as avg_tokens_per_embedding,
    MIN(token_count) as min_tokens,
    MAX(token_count) as max_tokens,
    COALESCE(model, 'N/A') as model
FROM embeddings_log
GROUP BY embedding_type, model
ORDER BY embedding_type;

SELECT '';
SELECT '=== API COST ANALYSIS ===' as section;
SELECT '';

-- Cost calculation: $0.00002 per 1K tokens for text-embedding-3-small
SELECT
    COALESCE(embedding_type, 'TOTAL') as embedding_type,
    SUM(token_count) as total_tokens,
    ROUND(SUM(token_count) / 1000.0 * 0.00002, 4) as cost_usd
FROM embeddings_log
GROUP BY embedding_type
UNION ALL
SELECT
    'TOTAL (from log)',
    SUM(token_count),
    ROUND(SUM(token_count) / 1000.0 * 0.00002, 4)
FROM embeddings_log;

SELECT '';
SELECT '=== EMBEDDING TIMELINE ===' as section;
SELECT '';

SELECT
    strftime('%Y-%m-%d', created_at) as date,
    COUNT(*) as embeddings_created,
    SUM(token_count) as tokens_used,
    ROUND(SUM(token_count) / 1000.0 * 0.00002, 4) as cost_usd
FROM embeddings_log
GROUP BY strftime('%Y-%m-%d', created_at)
ORDER BY date DESC
LIMIT 30;

SELECT '';
SELECT '=== PROJECTION FOR REMAINING VIDEOS ===' as section;
SELECT '';

-- Estimate cost for unindexed videos based on average token count
WITH avg_tokens AS (
    SELECT
        COALESCE(ROUND(AVG(token_count), 0), 100) as avg_per_embedding
    FROM embeddings_log
)
SELECT
    (SELECT COUNT(*) FROM videos WHERE is_indexed = 0) as unindexed_videos,
    (SELECT COUNT(*) FROM videos WHERE is_indexed = 0) * 2 as estimated_embeddings,
    (SELECT COUNT(*) FROM videos WHERE is_indexed = 0) * 2 * avg_per_embedding as estimated_total_tokens,
    ROUND((SELECT COUNT(*) FROM videos WHERE is_indexed = 0) * 2 * avg_per_embedding / 1000.0 * 0.00002, 4) as estimated_cost_usd
FROM avg_tokens;

SELECT '';
SELECT '=== EMBEDDING DETAILS (last 20 entries) ===' as section;
SELECT '';

SELECT
    el.video_id,
    el.embedding_type,
    el.token_count,
    el.model,
    el.created_at,
    v.title
FROM embeddings_log el
LEFT JOIN videos v ON el.video_id = v.video_id
ORDER BY el.created_at DESC
LIMIT 20;
