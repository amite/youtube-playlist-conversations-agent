-- API Cost Analysis and Projection (litecli compatible)
-- Track embedding costs and estimate expenses for remaining videos
-- OpenAI text-embedding-3-small pricing: $0.00002 per 1K tokens
-- Usage: uv run litecli data/videos.db < scripts/queries/cost_analysis-litecli.sql

SELECT '=== EMBEDDING COST SUMMARY ===' as section;

SELECT
    'Total Embeddings Generated' as metric,
    COUNT(*) as value
FROM embeddings_log
UNION ALL
SELECT
    'Title Embeddings',
    SUM(CASE WHEN embedding_type = 'title' THEN 1 ELSE 0 END)
FROM embeddings_log
UNION ALL
SELECT
    'Description Embeddings',
    SUM(CASE WHEN embedding_type = 'description' THEN 1 ELSE 0 END)
FROM embeddings_log;

SELECT '=== HISTORICAL COST (from embeddings_log) ===' as section

-- Cost breakdown by embedding type
WITH cost_by_type AS (
    SELECT
        embedding_type,
        COUNT(*) as embeddings,
        SUM(token_count) as total_tokens,
        ROUND(SUM(token_count) / 1000.0 * 0.00002, 4) as cost_usd
    FROM embeddings_log
    GROUP BY embedding_type
)
SELECT
    embedding_type,
    embeddings,
    total_tokens,
    cost_usd
FROM cost_by_type
UNION ALL
SELECT
    'TOTAL',
    SUM(embeddings),
    SUM(total_tokens),
    SUM(cost_usd)
FROM cost_by_type;

SELECT '=== COST PER VIDEO ===' as section

-- Average cost to generate both embeddings (title + description) for a video
WITH video_costs AS (
    SELECT
        video_id,
        SUM(token_count) as tokens,
        ROUND(SUM(token_count) / 1000.0 * 0.00002, 4) as cost_per_video
    FROM embeddings_log
    GROUP BY video_id
)
SELECT
    'Average cost per video (title + description)' as metric,
    ROUND(AVG(cost_per_video), 4) as cost_usd,
    ROUND(AVG(tokens), 0) as avg_tokens
FROM video_costs
UNION ALL
SELECT
    'Min cost per video',
    ROUND(MIN(cost_per_video), 4),
    (SELECT ROUND(MIN(tokens), 0) FROM video_costs)
FROM video_costs
UNION ALL
SELECT
    'Max cost per video',
    ROUND(MAX(cost_per_video), 4),
    (SELECT ROUND(MAX(tokens), 0) FROM video_costs)
FROM video_costs;

SELECT '=== PROJECTION FOR REMAINING UNINDEXED VIDEOS ===' as section

WITH estimates AS (
    SELECT
        (SELECT COUNT(*) FROM videos WHERE is_indexed = 0) as unindexed_count,
        (SELECT COUNT(*) FROM embeddings_log) as embeddings_so_far,
        COALESCE((SELECT ROUND(AVG(token_count), 0) FROM embeddings_log), 100) as avg_tokens_per_embedding
    FROM videos LIMIT 1
)
SELECT
    unindexed_count || ' unindexed videos' as metric,
    unindexed_count * 2 as estimated_embeddings_needed,
    unindexed_count * 2 * avg_tokens_per_embedding as estimated_tokens,
    ROUND(unindexed_count * 2 * avg_tokens_per_embedding / 1000.0 * 0.00002, 4) as estimated_cost_usd
FROM estimates;

SELECT '=== PROJECTED TOTAL PROJECT COST ===' as section

WITH costs AS (
    SELECT
        (SELECT ROUND(SUM(token_count) / 1000.0 * 0.00002, 4) FROM embeddings_log) as spent,
        COALESCE((SELECT ROUND(AVG(token_count), 0) FROM embeddings_log), 100) as avg_per_embedding,
        (SELECT COUNT(*) FROM videos) as total_videos,
        (SELECT COUNT(*) FROM videos WHERE is_indexed = 1) as indexed_count
    FROM videos LIMIT 1
)
SELECT
    'Already spent' as cost_category,
    spent as cost_usd
FROM costs
UNION ALL
SELECT
    'Remaining (estimated)',
    ROUND((total_videos - indexed_count) * 2 * avg_per_embedding / 1000.0 * 0.00002, 4)
FROM costs
UNION ALL
SELECT
    'TOTAL (full indexing)',
    ROUND(spent + (total_videos - indexed_count) * 2 * avg_per_embedding / 1000.0 * 0.00002, 4)
FROM costs;

SELECT '=== COST BY CHANNEL ===' as section

SELECT
    v.channel_name,
    COUNT(DISTINCT el.video_id) as videos_embedded,
    SUM(el.token_count) as total_tokens,
    ROUND(SUM(el.token_count) / 1000.0 * 0.00002, 4) as cost_usd
FROM embeddings_log el
JOIN videos v ON el.video_id = v.video_id
GROUP BY v.channel_name
ORDER BY cost_usd DESC
LIMIT 20;

SELECT '=== DAILY COST TRENDS ===' as section

SELECT
    DATE(created_at) as date,
    COUNT(*) as embeddings_created,
    SUM(token_count) as tokens_used,
    ROUND(SUM(token_count) / 1000.0 * 0.00002, 4) as daily_cost_usd
FROM embeddings_log
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 30;

SELECT '=== WEEKLY COST TRENDS ===' as section

SELECT
    strftime('%Y-W%W', created_at) as week,
    COUNT(*) as embeddings_created,
    SUM(token_count) as tokens_used,
    ROUND(SUM(token_count) / 1000.0 * 0.00002, 4) as weekly_cost_usd
FROM embeddings_log
GROUP BY strftime('%Y-W%W', created_at)
ORDER BY week DESC
LIMIT 12;

SELECT '=== TOKEN DISTRIBUTION ===' as section

WITH token_stats AS (
    SELECT
        MIN(token_count) as min_tokens,
        MAX(token_count) as max_tokens,
        ROUND(AVG(token_count), 0) as avg_tokens,
        COUNT(*) as embedding_count
    FROM embeddings_log
)
SELECT
    'Token statistics' as metric,
    min_tokens as min,
    max_tokens as max,
    avg_tokens as average,
    ROUND(avg_tokens * embedding_count / 1000.0 * 0.00002, 4) as cost_per_avg_embedding
FROM token_stats;
