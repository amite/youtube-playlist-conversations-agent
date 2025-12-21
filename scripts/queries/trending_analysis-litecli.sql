-- Trending and Temporal Analysis (litecli compatible)
-- Publication trends, recent videos, view count trends over time
-- Usage: uv run litecli data/videos.db < scripts/queries/trending_analysis-litecli.sql

SELECT '=== MOST RECENT VIDEOS ===' as section;

SELECT
    title,
    channel_name,
    datetime(published_at, 'unixepoch') as published_at,
    view_count,
    like_count,
    ROUND(duration_seconds / 60, 1) as duration_min
FROM videos
WHERE published_at IS NOT NULL
ORDER BY published_at DESC
LIMIT 30;

SELECT '=== VIDEOS FROM LAST 30 DAYS ===' as section

SELECT
    COUNT(*) as recent_video_count,
    ROUND(AVG(view_count), 0) as avg_views,
    MAX(view_count) as max_views,
    ROUND(AVG(like_count), 0) as avg_likes
FROM videos
WHERE published_at IS NOT NULL
    AND published_at > strftime('%s', 'now', '-30 days');

SELECT '=== VIDEOS FROM LAST 90 DAYS ===' as section

SELECT
    COUNT(*) as recent_video_count,
    ROUND(AVG(view_count), 0) as avg_views,
    MAX(view_count) as max_views
FROM videos
WHERE published_at IS NOT NULL
    AND published_at > strftime('%s', 'now', '-90 days');

SELECT '=== VIDEOS FROM LAST 1 YEAR ===' as section

SELECT
    COUNT(*) as recent_video_count,
    ROUND(AVG(view_count), 0) as avg_views,
    MAX(view_count) as max_views
FROM videos
WHERE published_at IS NOT NULL
    AND published_at > strftime('%s', 'now', '-1 year');

SELECT '=== PUBLICATION TRENDS (by year) ===' as section

SELECT
    strftime('%Y', datetime(published_at, 'unixepoch')) as year,
    COUNT(*) as video_count,
    ROUND(AVG(view_count), 0) as avg_views,
    SUM(view_count) as total_views,
    MIN(datetime(published_at, 'unixepoch')) as earliest,
    MAX(datetime(published_at, 'unixepoch')) as latest
FROM videos
WHERE published_at IS NOT NULL
GROUP BY year
ORDER BY year DESC;

SELECT '=== PUBLICATION TRENDS (by month, last 24 months) ===' as section

SELECT
    strftime('%Y-%m', datetime(published_at, 'unixepoch')) as year_month,
    COUNT(*) as video_count,
    ROUND(AVG(view_count), 0) as avg_views
FROM videos
WHERE published_at IS NOT NULL
    AND published_at > strftime('%s', 'now', '-24 months')
GROUP BY year_month
ORDER BY year_month DESC;

SELECT '=== MOST VIEWED VIDEOS IN LAST YEAR ===' as section

SELECT
    title,
    channel_name,
    datetime(published_at, 'unixepoch') as published_at,
    view_count,
    like_count
FROM videos
WHERE published_at IS NOT NULL
    AND published_at > strftime('%s', 'now', '-1 year')
ORDER BY view_count DESC
LIMIT 20;

SELECT '=== OLDEST VIDEOS IN DATABASE ===' as section

SELECT
    title,
    channel_name,
    datetime(published_at, 'unixepoch') as published_at,
    view_count,
    ROUND((strftime('%s', 'now') - published_at) / 86400 / 365.25, 1) as age_years
FROM videos
WHERE published_at IS NOT NULL
ORDER BY published_at ASC
LIMIT 20;

SELECT '=== VIEW GROWTH PATTERNS ===' as section

WITH decade_views AS (
    SELECT
        CASE
            WHEN strftime('%Y', datetime(published_at, 'unixepoch')) < '2010' THEN 'pre-2010'
            WHEN strftime('%Y', datetime(published_at, 'unixepoch')) < '2015' THEN '2010-2014'
            WHEN strftime('%Y', datetime(published_at, 'unixepoch')) < '2020' THEN '2015-2019'
            ELSE '2020+'
        END as period,
        ROUND(AVG(view_count), 0) as avg_views,
        COUNT(*) as video_count
    FROM videos
    WHERE published_at IS NOT NULL
    GROUP BY period
)
SELECT * FROM decade_views
ORDER BY period DESC;
