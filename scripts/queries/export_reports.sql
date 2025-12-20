-- Export and Reporting Queries
-- Generate CSV, markdown, and formatted output for reports and dashboards
-- Usage examples:
--   sqlite3 -header -column data/videos.db < scripts/queries/export_reports.sql
--   sqlite3 data/videos.db < scripts/queries/export_reports.sql | head -50
--   To export as CSV: sqlite3 -header data/videos.db < scripts/queries/export_reports.sql > report.csv

.headers on
.mode column

SELECT '=== CHANNEL LEADERBOARD (CSV format for spreadsheets) ===' as section;
SELECT '';

.mode csv

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

-- Return to column mode
.mode column

SELECT '';
SELECT '=== CONTENT DISTRIBUTION REPORT ===' as section;
SELECT '';

SELECT
    '=== VIDEO LENGTH DISTRIBUTION ===' as metric;

.mode csv
SELECT
    'Duration Range' as category,
    'Video Count' as count,
    'Avg Views' as avg_views,
    'Avg Duration' as avg_duration_sec
UNION ALL
SELECT
    '<5 min',
    COUNT(*),
    ROUND(AVG(view_count), 0),
    ROUND(AVG(duration_seconds), 0)
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

.mode column

SELECT '';
SELECT '=== SEARCH QUALITY SCORECARD ===' as section;
SELECT '';

.mode markdown

SELECT
    '| Metric | Value |' as metric_row
UNION ALL
SELECT
    '|--------|-------|'
UNION ALL
SELECT
    '| Total Evaluations | ' || COUNT(*) || ' |'
FROM evaluation_results
UNION ALL
SELECT
    '| Average Relevance | ' || ROUND(AVG(CAST(relevance_score AS FLOAT)), 2) || ' / 5 |'
FROM evaluation_results
UNION ALL
SELECT
    '| Top-1 Accuracy | ' || ROUND(SUM(CASE WHEN best_result_position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) || '% |'
FROM evaluation_results
UNION ALL
SELECT
    '| Queries Evaluated | ' || COUNT(DISTINCT query_text) || ' |'
FROM evaluation_results;

.mode column

SELECT '';
SELECT '=== TOP 20 VIDEOS BY VIEWS (Markdown Table) ===' as section;
SELECT '';

.mode markdown

SELECT
    '| Title | Channel | Views | Likes | Duration |' as header
UNION ALL
SELECT
    '|-------|---------|-------|-------|----------|'
UNION ALL
SELECT
    '| ' || title || ' | ' || channel_name || ' | ' || view_count || ' | ' || like_count || ' | ' || ROUND(duration_seconds / 60, 0) || ' min |'
FROM videos
ORDER BY view_count DESC
LIMIT 20;

.mode column

SELECT '';
SELECT '=== DATA QUALITY SUMMARY ===' as section;
SELECT '';

.mode markdown

SELECT
    '| Aspect | Count | Percentage |' as header
UNION ALL
SELECT
    '|--------|-------|------------|'
UNION ALL
SELECT
    '| Videos with Title | ' || SUM(CASE WHEN title IS NOT NULL THEN 1 ELSE 0 END) || ' | ' || ROUND(SUM(CASE WHEN title IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) || '% |'
FROM videos
UNION ALL
SELECT
    '| Videos with Description | ' || SUM(CASE WHEN description IS NOT NULL THEN 1 ELSE 0 END) || ' | ' || ROUND(SUM(CASE WHEN description IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) || '% |'
FROM videos
UNION ALL
SELECT
    '| Videos with Channel | ' || SUM(CASE WHEN channel_name IS NOT NULL THEN 1 ELSE 0 END) || ' | ' || ROUND(SUM(CASE WHEN channel_name IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) || '% |'
FROM videos
UNION ALL
SELECT
    '| Videos with Duration | ' || SUM(CASE WHEN duration_seconds IS NOT NULL THEN 1 ELSE 0 END) || ' | ' || ROUND(SUM(CASE WHEN duration_seconds IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) || '% |'
FROM videos
UNION ALL
SELECT
    '| Indexed Videos | ' || SUM(CASE WHEN is_indexed = 1 THEN 1 ELSE 0 END) || ' | ' || ROUND(SUM(CASE WHEN is_indexed = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) || '% |'
FROM videos
UNION ALL
SELECT
    '| Cleaned Titles | ' || SUM(CASE WHEN cleaned_title IS NOT NULL THEN 1 ELSE 0 END) || ' | ' || ROUND(SUM(CASE WHEN cleaned_title IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) || '% |'
FROM videos;

.mode column

SELECT '';
SELECT '=== COMPLETE VIDEO CATALOG EXPORT (CSV) ===' as section;
SELECT '';

.mode csv

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

.mode column

SELECT '';
SELECT '=== EMBEDDING COST REPORT (CSV) ===' as section;
SELECT '';

.mode csv

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

.mode column

SELECT '';
SELECT '=== TEST QUERY RESULTS MATRIX ===' as section;
SELECT '';

.mode markdown

SELECT
    '| Query Text | Type | Evaluations | Avg Relevance | Top-1 Accuracy |' as header
UNION ALL
SELECT
    '|------------|------|-------------|----------------|----------------|'
UNION ALL
SELECT
    '| ' || tq.query_text || ' | ' || COALESCE(tq.query_type, 'unknown') || ' | ' || COUNT(er.id) || ' | ' || COALESCE(ROUND(AVG(CAST(er.relevance_score AS FLOAT)), 2), 'N/A') || ' | ' || COALESCE(ROUND(SUM(CASE WHEN er.best_result_position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(er.id), 0), 'N/A') || '% |'
FROM test_queries tq
LEFT JOIN evaluation_results er ON tq.query_text = er.query_text
GROUP BY tq.id, tq.query_text, tq.query_type
ORDER BY tq.query_type, tq.query_text;
