-- Content Statistics (litecli compatible)
-- Video length distribution, popularity tiers, engagement metrics
-- Usage: uv run litecli data/videos.db < scripts/queries/content_stats-litecli.sql

SELECT '=== VIDEO LENGTH DISTRIBUTION ===' as section;

WITH length_tiers AS (
    SELECT
        CASE
            WHEN duration_seconds < 300 THEN '<5 min'
            WHEN duration_seconds < 900 THEN '5-15 min'
            WHEN duration_seconds < 1800 THEN '15-30 min'
            WHEN duration_seconds < 3600 THEN '30-60 min'
            ELSE '60+ min'
        END as duration_tier,
        COUNT(*) as video_count,
        ROUND(AVG(view_count), 0) as avg_views,
        ROUND(AVG(like_count), 0) as avg_likes,
        ROUND(AVG(comment_count), 0) as avg_comments
    FROM videos
    GROUP BY duration_tier
)
SELECT * FROM length_tiers
ORDER BY
    CASE duration_tier
        WHEN '<5 min' THEN 1
        WHEN '5-15 min' THEN 2
        WHEN '15-30 min' THEN 3
        WHEN '30-60 min' THEN 4
        ELSE 5
    END;

SELECT '=== POPULARITY TIERS (by view count) ===' as section

WITH popularity_tiers AS (
    SELECT
        CASE
            WHEN view_count < 1000 THEN 'Low (<1K views)'
            WHEN view_count < 10000 THEN 'Medium (1K-10K)'
            WHEN view_count < 100000 THEN 'High (10K-100K)'
            ELSE 'Viral (>100K)'
        END as popularity_tier,
        COUNT(*) as video_count,
        COUNT(DISTINCT channel_name) as unique_channels,
        ROUND(AVG(view_count), 0) as avg_views,
        MAX(view_count) as max_views,
        ROUND(AVG(like_count), 0) as avg_likes
    FROM videos
    GROUP BY popularity_tier
)
SELECT * FROM popularity_tiers
ORDER BY
    CASE popularity_tier
        WHEN 'Low (<1K views)' THEN 1
        WHEN 'Medium (1K-10K)' THEN 2
        WHEN 'High (10K-100K)' THEN 3
        ELSE 4
    END;

SELECT '=== ENGAGEMENT METRICS ===' as section

SELECT
    'Overall Stats' as metric,
    ROUND(AVG(CAST(like_count AS FLOAT) / NULLIF(view_count, 0) * 100), 3) as like_rate_pct,
    ROUND(AVG(CAST(comment_count AS FLOAT) / NULLIF(view_count, 0) * 100), 3) as comment_rate_pct,
    COUNT(*) as video_count
FROM videos
WHERE view_count > 0;

SELECT '=== MOST VIEWED VIDEOS ===' as section

SELECT
    title,
    channel_name,
    view_count,
    like_count,
    comment_count,
    ROUND(CAST(like_count AS FLOAT) / NULLIF(view_count, 0) * 100, 2) as like_rate_pct,
    ROUND(duration_seconds / 60, 1) as duration_min
FROM videos
ORDER BY view_count DESC
LIMIT 20;

SELECT '=== LEAST VIEWED VIDEOS ===' as section

SELECT
    title,
    channel_name,
    view_count,
    like_count,
    comment_count,
    ROUND(duration_seconds / 60, 1) as duration_min
FROM videos
WHERE view_count > 0
ORDER BY view_count ASC
LIMIT 20;

SELECT '=== PUBLICATION DATE DISTRIBUTION ===' as section

WITH date_dist AS (
    SELECT
        strftime('%Y', datetime(published_at, 'unixepoch')) as year,
        strftime('%m', datetime(published_at, 'unixepoch')) as month,
        COUNT(*) as video_count,
        ROUND(AVG(view_count), 0) as avg_views
    FROM videos
    WHERE published_at IS NOT NULL
    GROUP BY year, month
)
SELECT
    year || '-' || month as year_month,
    video_count,
    avg_views
FROM date_dist
ORDER BY year DESC, month DESC
LIMIT 24;
