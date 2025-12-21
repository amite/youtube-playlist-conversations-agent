-- Database Overview
-- Quick snapshot of videos.db status and key metrics
-- Usage: sqlite3 -header -column data/videos.db < scripts/queries/overview.sql

.headers on
.mode column

SELECT '=== DATABASE OVERVIEW ===' as section;

-- Total counts and progress
SELECT
    'Total Videos' as metric,
    COUNT(*) as value
FROM videos
UNION ALL
SELECT
    'Unique Channels',
    COUNT(DISTINCT channel_name)
FROM videos
UNION ALL
SELECT
    'Indexed Videos (is_indexed=1)',
    SUM(CASE WHEN is_indexed = 1 THEN 1 ELSE 0 END)
FROM videos
UNION ALL
SELECT
    'Unindexed Videos (is_indexed=0)',
    SUM(CASE WHEN is_indexed = 0 THEN 1 ELSE 0 END)
FROM videos
UNION ALL
SELECT
    'Cleaned Titles (NOT NULL)',
    SUM(CASE WHEN cleaned_title IS NOT NULL THEN 1 ELSE 0 END)
FROM videos
UNION ALL
SELECT
    'Cleaned Descriptions (NOT NULL)',
    SUM(CASE WHEN cleaned_description IS NOT NULL THEN 1 ELSE 0 END)
FROM videos;

SELECT '=== CONTENT METRICS ===' as section

SELECT
    ROUND(AVG(duration_seconds), 0) as avg_duration_sec,
    MIN(duration_seconds) as min_duration_sec,
    MAX(duration_seconds) as max_duration_sec,
    ROUND(AVG(view_count), 0) as avg_views,
    ROUND(AVG(like_count), 0) as avg_likes,
    ROUND(AVG(comment_count), 0) as avg_comments
FROM videos;

SELECT '=== ENGAGEMENT RATES ===' as section

SELECT
    ROUND(AVG(CAST(like_count AS FLOAT) / NULLIF(view_count, 0) * 100), 2) as avg_like_rate_pct,
    ROUND(AVG(CAST(comment_count AS FLOAT) / NULLIF(view_count, 0) * 100), 2) as avg_comment_rate_pct
FROM videos
WHERE view_count > 0;

SELECT '=== DATABASE TABLES ===' as section

SELECT
    'videos' as table_name,
    COUNT(*) as record_count
FROM videos
UNION ALL
SELECT
    'embeddings_log',
    COUNT(*)
FROM embeddings_log
UNION ALL
SELECT
    'evaluation_results',
    COUNT(*)
FROM evaluation_results
UNION ALL
SELECT
    'test_queries',
    COUNT(*)
FROM test_queries;
