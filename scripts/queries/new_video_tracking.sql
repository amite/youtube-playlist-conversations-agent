-- New Video Tracking Queries
-- Identify videos added since specific timestamps
-- Usage: sqlite3 -header -column data/videos.db < scripts/queries/new_video_tracking.sql

.headers on
.mode column

SELECT '=== NEW VIDEO TRACKING QUERIES ===' as section;

-- Find videos added since a specific timestamp
SELECT 'Videos added since 2025-12-20 07:17:09' as query;
SELECT 
    video_id,
    title,
    channel_name,
    created_at,
    published_at
FROM videos 
WHERE created_at > '2025-12-20 07:17:09'
ORDER BY created_at DESC;

-- Count new videos since a timestamp
SELECT 'Count of new videos since 2025-12-20 07:17:09' as query;
SELECT COUNT(*) as new_videos_count
FROM videos 
WHERE created_at > '2025-12-20 07:17:09';

-- Find videos added in the last 24 hours
SELECT 'Videos added in last 24 hours' as query;
SELECT 
    video_id,
    title,
    channel_name,
    created_at
FROM videos 
WHERE created_at > datetime('now', '-24 hours')
ORDER BY created_at DESC;

-- Find videos added since last week
SELECT 'Videos added in last 7 days' as query;
SELECT 
    video_id,
    title,
    channel_name,
    created_at
FROM videos 
WHERE created_at > datetime('now', '-7 days')
ORDER BY created_at DESC;