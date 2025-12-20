-- Export and Reporting Queries (litecli compatible)
-- Generate CSV, markdown, and formatted output for reports and dashboards
-- Note: Mode switching (.mode) is not supported in litecli
-- Usage: uv run litecli data/videos.db < scripts/queries/export_reports-litecli.sql

SELECT '=== CHANNEL LEADERBOARD ===' as section;
SELECT '';

SELECT
    channel_name,
    COUNT(*) as video_count,
    ROUND(AVG(view_count), 0) as avg_views,
    ROUND(AVG(like_count), 0) as avg_likes,
    ROUND(AVG(comment_count), 0) as avg_comments,
    ROUND(AVG(duration_seconds), 0) as avg_duration_sec,
    MAX(view_count) as top_video_views,
    SUM(view_count) as total_channel_views
FROM videos
GROUP BY channel_name
ORDER BY video_count DESC, total_channel_views DESC;

SELECT '';
SELECT '=== CONTENT DISTRIBUTION REPORT ===' as section;
SELECT '';

SELECT
    '<5 min' as category,
    COUNT(*) as count,
    ROUND(AVG(view_count), 0) as avg_views,
    ROUND(AVG(duration_seconds), 0) as avg_duration_sec
FROM videos WHERE duration_seconds < 300
UNION ALL
SELECT
    '5-15 min',
    COUNT(*),
    ROUND(AVG(view_count), 0),
    ROUND(AVG(duration_seconds), 0)
FROM videos WHERE duration_seconds >= 300 AND duration_seconds < 900
UNION ALL
SELECT
    '15-30 min',
    COUNT(*),
    ROUND(AVG(view_count), 0),
    ROUND(AVG(duration_seconds), 0)
FROM videos WHERE duration_seconds >= 900 AND duration_seconds < 1800
UNION ALL
SELECT
    '30-60 min',
    COUNT(*),
    ROUND(AVG(view_count), 0),
    ROUND(AVG(duration_seconds), 0)
FROM videos WHERE duration_seconds >= 1800 AND duration_seconds < 3600
UNION ALL
SELECT
    '60+ min',
    COUNT(*),
    ROUND(AVG(view_count), 0),
    ROUND(AVG(duration_seconds), 0)
FROM videos WHERE duration_seconds >= 3600;

SELECT '';
SELECT '=== SEARCH QUALITY SCORECARD ===' as section;
SELECT '';

SELECT
    'Total Evaluations' as metric,
    COUNT(*) as value
FROM evaluation_results
UNION ALL
SELECT
    'Average Relevance',
    ROUND(AVG(CAST(relevance_score AS FLOAT)), 2)
FROM evaluation_results
UNION ALL
SELECT
    'Top-1 Accuracy %',
    ROUND(SUM(CASE WHEN best_result_position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM evaluation_results
UNION ALL
SELECT
    'Queries Evaluated',
    COUNT(DISTINCT query_text)
FROM evaluation_results;

SELECT '';
SELECT '=== TOP 20 VIDEOS BY VIEWS ===' as section;
SELECT '';

SELECT
    title,
    channel_name,
    view_count,
    like_count,
    ROUND(duration_seconds / 60, 0) as duration_min
FROM videos
ORDER BY view_count DESC
LIMIT 20;

SELECT '';
SELECT '=== DATA QUALITY SUMMARY ===' as section;
SELECT '';

SELECT
    'Videos with Title' as aspect,
    SUM(CASE WHEN title IS NOT NULL THEN 1 ELSE 0 END) as count,
    ROUND(SUM(CASE WHEN title IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as percentage
FROM videos
UNION ALL
SELECT
    'Videos with Description',
    SUM(CASE WHEN description IS NOT NULL THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN description IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM videos
UNION ALL
SELECT
    'Videos with Channel',
    SUM(CASE WHEN channel_name IS NOT NULL THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN channel_name IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM videos
UNION ALL
SELECT
    'Videos with Duration',
    SUM(CASE WHEN duration_seconds IS NOT NULL THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN duration_seconds IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM videos
UNION ALL
SELECT
    'Indexed Videos',
    SUM(CASE WHEN is_indexed = 1 THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN is_indexed = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM videos
UNION ALL
SELECT
    'Cleaned Titles',
    SUM(CASE WHEN cleaned_title IS NOT NULL THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN cleaned_title IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM videos;

SELECT '';
SELECT '=== COMPLETE VIDEO CATALOG ===' as section;
SELECT '';

SELECT
    video_id,
    title,
    channel_name,
    channel_id,
    datetime(published_at, 'unixepoch') as published_at,
    ROUND(duration_seconds / 60.0, 1) as duration_min,
    view_count,
    like_count,
    comment_count,
    is_indexed,
    CASE WHEN cleaned_title IS NOT NULL THEN 'Yes' ELSE 'No' END as cleaned,
    created_at
FROM videos
ORDER BY view_count DESC;

SELECT '';
SELECT '=== EMBEDDING COST REPORT ===' as section;
SELECT '';

SELECT
    strftime('%Y-%m-%d', created_at) as date,
    COUNT(*) as embeddings,
    SUM(token_count) as tokens,
    ROUND(SUM(token_count) / 1000.0 * 0.00002, 4) as cost_usd,
    model,
    GROUP_CONCAT(embedding_type) as types
FROM embeddings_log
GROUP BY DATE(created_at)
ORDER BY date DESC;

SELECT '';
SELECT '=== TEST QUERY RESULTS MATRIX ===' as section;
SELECT '';

SELECT
    tq.query_text,
    COALESCE(tq.query_type, 'unknown') as type,
    COUNT(er.id) as evaluations,
    COALESCE(ROUND(AVG(CAST(er.relevance_score AS FLOAT)), 2), 0) as avg_relevance,
    COALESCE(ROUND(SUM(CASE WHEN er.best_result_position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(er.id), 0), 0) as top1_accuracy_pct
FROM test_queries tq
LEFT JOIN evaluation_results er ON tq.query_text = er.query_text
GROUP BY tq.id, tq.query_text, tq.query_type
ORDER BY tq.query_type, tq.query_text;
