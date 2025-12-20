-- Before/After Algorithm Comparison Queries (litecli compatible)
-- Compare search quality metrics across algorithm versions and changes
-- Useful for A/B testing embedding weights, data cleaning, and ranking changes
-- Usage: uv run litecli data/videos.db < scripts/queries/comparison_queries-litecli.sql

SELECT '=== OVERALL EVALUATION METRICS ===' as section;
SELECT '';

SELECT
    'Total Evaluations' as metric,
    COUNT(*) as value,
    ROUND(AVG(CAST(relevance_score AS FLOAT)), 2) as avg_relevance,
    SUM(CASE WHEN best_result_position = 1 THEN 1 ELSE 0 END) as top1_count,
    ROUND(SUM(CASE WHEN best_result_position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as top1_accuracy_pct
FROM evaluation_results;

SELECT '';
SELECT '=== RELEVANCE SCORE DISTRIBUTION ===' as section;
SELECT '';

SELECT
    relevance_score,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM evaluation_results), 1) as pct
FROM evaluation_results
WHERE relevance_score IS NOT NULL
GROUP BY relevance_score
ORDER BY relevance_score DESC;

SELECT '';
SELECT '=== EVALUATION METRICS BY TIME PERIOD ===' as section;
SELECT '';

-- Compare early vs late evaluations (useful for tracking improvement over time)
WITH periods AS (
    SELECT
        CASE
            WHEN ROWID <= (SELECT COUNT(*) / 3 FROM evaluation_results) THEN 'Early (first 33%)'
            WHEN ROWID <= (SELECT COUNT(*) * 2 / 3 FROM evaluation_results) THEN 'Middle (33-66%)'
            ELSE 'Late (last 33%)'
        END as period,
        relevance_score,
        best_result_position
    FROM evaluation_results
)
SELECT
    period,
    COUNT(*) as evaluations,
    ROUND(AVG(CAST(relevance_score AS FLOAT)), 2) as avg_relevance,
    SUM(CASE WHEN best_result_position = 1 THEN 1 ELSE 0 END) as top1_hits,
    ROUND(SUM(CASE WHEN best_result_position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as top1_accuracy_pct
FROM periods
WHERE period IS NOT NULL
GROUP BY period;

SELECT '';
SELECT '=== DAILY EVALUATION TRENDS ===' as section;
SELECT '';

SELECT
    DATE(created_at) as date,
    COUNT(*) as evaluations_done,
    ROUND(AVG(CAST(relevance_score AS FLOAT)), 2) as avg_relevance,
    SUM(CASE WHEN best_result_position = 1 THEN 1 ELSE 0 END) as top1_hits,
    ROUND(SUM(CASE WHEN best_result_position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as top1_accuracy_pct
FROM evaluation_results
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 30;

SELECT '';
SELECT '=== PERFORMANCE BY QUERY TYPE ===' as section;
SELECT '';

SELECT
    tq.query_type,
    COUNT(er.id) as evaluations,
    ROUND(AVG(CAST(er.relevance_score AS FLOAT)), 2) as avg_relevance,
    SUM(CASE WHEN er.best_result_position = 1 THEN 1 ELSE 0 END) as top1_hits,
    ROUND(SUM(CASE WHEN er.best_result_position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(er.id), 1) as top1_accuracy_pct
FROM evaluation_results er
LEFT JOIN test_queries tq ON er.query_text = tq.query_text
WHERE tq.query_type IS NOT NULL
GROUP BY tq.query_type
ORDER BY avg_relevance DESC;

SELECT '';
SELECT '=== QUERIES SHOWING IMPROVEMENT (ascending relevance) ===' as section;
SELECT '';

-- Group evaluations by query and sort by relevance to show improvement trend
WITH query_evals AS (
    SELECT
        query_text,
        created_at,
        relevance_score,
        ROW_NUMBER() OVER (PARTITION BY query_text ORDER BY created_at) as eval_order
    FROM evaluation_results
),
first_last AS (
    SELECT
        query_text,
        MIN(CASE WHEN eval_order = 1 THEN relevance_score END) as first_relevance,
        MAX(CASE WHEN eval_order = (SELECT MAX(eval_order) FROM query_evals qe2 WHERE qe2.query_text = query_evals.query_text) THEN relevance_score END) as latest_relevance
    FROM query_evals
    GROUP BY query_text
)
SELECT
    query_text,
    first_relevance as initial_score,
    latest_relevance as latest_score,
    latest_relevance - first_relevance as improvement,
    COUNT(*) as total_evaluations
FROM first_last
JOIN evaluation_results USING (query_text)
WHERE latest_relevance > first_relevance
GROUP BY query_text
ORDER BY improvement DESC;

SELECT '';
SELECT '=== QUERIES SHOWING REGRESSION (descending relevance) ===' as section;
SELECT '';

-- Queries that got worse
WITH query_evals AS (
    SELECT
        query_text,
        created_at,
        relevance_score,
        ROW_NUMBER() OVER (PARTITION BY query_text ORDER BY created_at) as eval_order
    FROM evaluation_results
),
first_last AS (
    SELECT
        query_text,
        MIN(CASE WHEN eval_order = 1 THEN relevance_score END) as first_relevance,
        MAX(CASE WHEN eval_order = (SELECT MAX(eval_order) FROM query_evals qe2 WHERE qe2.query_text = query_evals.query_text) THEN relevance_score END) as latest_relevance
    FROM query_evals
    GROUP BY query_text
)
SELECT
    query_text,
    first_relevance as initial_score,
    latest_relevance as latest_score,
    latest_relevance - first_relevance as regression,
    COUNT(*) as total_evaluations
FROM first_last
JOIN evaluation_results USING (query_text)
WHERE latest_relevance < first_relevance
GROUP BY query_text
ORDER BY regression ASC;

SELECT '';
SELECT '=== BEST RESULT POSITION DISTRIBUTION ===' as section;
SELECT '';

SELECT
    best_result_position as position,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM evaluation_results WHERE best_result_position IS NOT NULL), 1) as pct
FROM evaluation_results
WHERE best_result_position IS NOT NULL
GROUP BY best_result_position
ORDER BY best_result_position;

SELECT '';
SELECT '=== TEMPLATE: COMPARE TWO TIME PERIODS ===' as section;
SELECT '';

-- This is a template to compare metrics before/after a specific date
-- Edit the date cutoff below to compare different algorithm versions
-- Example: Change '2025-01-01' to your cutoff date

SELECT
    'Before 2025-01-01' as period,
    COUNT(*) as evaluations,
    ROUND(AVG(CAST(relevance_score AS FLOAT)), 2) as avg_relevance,
    SUM(CASE WHEN best_result_position = 1 THEN 1 ELSE 0 END) as top1_hits,
    ROUND(SUM(CASE WHEN best_result_position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as top1_accuracy_pct
FROM evaluation_results
WHERE DATE(created_at) < '2025-01-01'
UNION ALL
SELECT
    'After 2025-01-01' as period,
    COUNT(*) as evaluations,
    ROUND(AVG(CAST(relevance_score AS FLOAT)), 2) as avg_relevance,
    SUM(CASE WHEN best_result_position = 1 THEN 1 ELSE 0 END) as top1_hits,
    ROUND(SUM(CASE WHEN best_result_position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as top1_accuracy_pct
FROM evaluation_results
WHERE DATE(created_at) >= '2025-01-01';
