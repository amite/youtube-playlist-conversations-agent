-- Data Quality Checks (litecli compatible)
-- Identify missing data, duplicates, outliers, and data completeness
-- Usage: uv run litecli data/videos.db < scripts/queries/data_quality-litecli.sql

SELECT '=== DATA COMPLETENESS ===' as section;
SELECT '';

SELECT
    'Total Videos' as metric,
    COUNT(*) as value,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM videos), 1) as pct
FROM videos
UNION ALL
SELECT
    'Videos with title',
    SUM(CASE WHEN title IS NOT NULL AND TRIM(title) != '' THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN title IS NOT NULL AND TRIM(title) != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM videos
UNION ALL
SELECT
    'Videos with description',
    SUM(CASE WHEN description IS NOT NULL AND TRIM(description) != '' THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN description IS NOT NULL AND TRIM(description) != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM videos
UNION ALL
SELECT
    'Videos with channel_name',
    SUM(CASE WHEN channel_name IS NOT NULL THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN channel_name IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM videos
UNION ALL
SELECT
    'Videos with duration',
    SUM(CASE WHEN duration_seconds IS NOT NULL THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN duration_seconds IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM videos
UNION ALL
SELECT
    'Videos with view_count',
    SUM(CASE WHEN view_count IS NOT NULL THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN view_count IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM videos
UNION ALL
SELECT
    'Videos with published_at',
    SUM(CASE WHEN published_at IS NOT NULL THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN published_at IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM videos;

SELECT '';
SELECT '=== NULL FIELDS SUMMARY ===' as section;
SELECT '';

SELECT
    'cleaned_title (null count)',
    SUM(CASE WHEN cleaned_title IS NULL THEN 1 ELSE 0 END) as null_count
FROM videos
UNION ALL
SELECT
    'cleaned_description (null count)',
    SUM(CASE WHEN cleaned_description IS NULL THEN 1 ELSE 0 END)
FROM videos;

SELECT '';
SELECT '=== POTENTIAL DUPLICATES (by title) ===' as section;
SELECT '';

WITH title_dupes AS (
    SELECT
        title,
        COUNT(*) as count,
        COUNT(DISTINCT video_id) as unique_video_ids
    FROM videos
    WHERE title IS NOT NULL
    GROUP BY title
    HAVING COUNT(*) > 1
)
SELECT
    title,
    count as duplicate_count,
    unique_video_ids
FROM title_dupes
ORDER BY count DESC
LIMIT 20;

SELECT '';
SELECT '=== OUTLIERS: UNUSUALLY LONG VIDEOS ===' as section;
SELECT '';

SELECT
    title,
    channel_name,
    ROUND(duration_seconds / 3600.0, 2) as duration_hours,
    view_count,
    published_at
FROM videos
WHERE duration_seconds > 7200
ORDER BY duration_seconds DESC
LIMIT 20;

SELECT '';
SELECT '=== OUTLIERS: EXTREME VIEW COUNTS ===' as section;
SELECT '';

WITH stats AS (
    SELECT
        AVG(view_count) as avg_views,
        SQRT(AVG(view_count * view_count) - AVG(view_count) * AVG(view_count)) as stddev
    FROM videos
)
SELECT
    v.title,
    v.channel_name,
    v.view_count,
    ROUND((v.view_count - s.avg_views) / NULLIF(s.stddev, 0), 2) as stddev_from_mean
FROM videos v, stats s
WHERE v.view_count > (s.avg_views + 2 * s.stddev)
ORDER BY v.view_count DESC
LIMIT 20;

SELECT '';
SELECT '=== OUTLIERS: UNUSUALLY SHORT VIDEOS ===' as section;
SELECT '';

SELECT
    title,
    channel_name,
    duration_seconds,
    view_count
FROM videos
WHERE duration_seconds < 60
ORDER BY duration_seconds ASC
LIMIT 20;

SELECT '';
SELECT '=== DATA ENTRY ISSUES ===' as section;
SELECT '';

SELECT
    'Videos with zero views' as issue,
    COUNT(*) as count
FROM videos
WHERE view_count = 0
UNION ALL
SELECT
    'Videos with NULL duration',
    COUNT(*)
FROM videos
WHERE duration_seconds IS NULL
UNION ALL
SELECT
    'Videos with NULL channel_name',
    COUNT(*)
FROM videos
WHERE channel_name IS NULL
UNION ALL
SELECT
    'Videos with empty title',
    COUNT(*)
FROM videos
WHERE title IS NULL OR TRIM(title) = '';
