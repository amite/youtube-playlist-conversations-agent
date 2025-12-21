-- Channel Analysis (litecli compatible)
-- Video count, performance metrics, and engagement by channel
-- Usage: uv run litecli data/videos.db < scripts/queries/channels-litecli.sql

SELECT '=== TOP CHANNELS BY VIDEO COUNT ===' as section;

SELECT
    channel_name,
    COUNT(*) as video_count,
    COUNT(DISTINCT channel_id) as unique_ids,
    ROUND(AVG(view_count), 0) as avg_views,
    ROUND(AVG(like_count), 0) as avg_likes,
    ROUND(AVG(comment_count), 0) as avg_comments,
    ROUND(AVG(duration_seconds) / 60, 1) as avg_duration_min,
    MAX(view_count) as top_video_views
FROM videos
GROUP BY channel_name
ORDER BY video_count DESC, avg_views DESC
LIMIT 30;

SELECT '=== CHANNEL DISTRIBUTION ===' as section;

WITH channel_stats AS (
    SELECT
        channel_name,
        COUNT(*) as video_count
    FROM videos
    GROUP BY channel_name
)
SELECT
    CASE
        WHEN video_count = 1 THEN '1 video'
        WHEN video_count BETWEEN 2 AND 5 THEN '2-5 videos'
        WHEN video_count BETWEEN 6 AND 10 THEN '6-10 videos'
        ELSE '10+ videos'
    END as size_tier,
    COUNT(*) as channel_count,
    SUM(video_count) as total_videos
FROM channel_stats
GROUP BY size_tier
ORDER BY channel_count DESC;

SELECT '=== MOST ACTIVE CHANNELS (by upload date) ===' as section;

SELECT
    channel_name,
    COUNT(*) as video_count,
    MIN(published_at) as oldest_video_timestamp,
    MAX(published_at) as newest_video_timestamp,
    ROUND(AVG(view_count), 0) as avg_views
FROM videos
GROUP BY channel_name
ORDER BY MAX(published_at) DESC
LIMIT 20;

SELECT '=== HIGHEST ENGAGEMENT CHANNELS ===' as section;

SELECT
    channel_name,
    COUNT(*) as video_count,
    ROUND(AVG(CAST(like_count AS FLOAT) / NULLIF(view_count, 0) * 100), 2) as avg_like_rate_pct,
    ROUND(AVG(CAST(comment_count AS FLOAT) / NULLIF(view_count, 0) * 100), 2) as avg_comment_rate_pct,
    ROUND(AVG(view_count), 0) as avg_views
FROM videos
WHERE view_count > 0
GROUP BY channel_name
HAVING COUNT(*) >= 2
ORDER BY avg_like_rate_pct DESC
LIMIT 20;
