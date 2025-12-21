-- Search Evaluation Summary (litecli compatible)
-- Track search quality metrics and evaluation results
-- Usage: uv run litecli data/videos.db < scripts/queries/evaluation_summary-litecli.sql

SELECT '=== EVALUATION SUMMARY ===' as section;

SELECT
    'Total Evaluations' as metric,
    COUNT(*) as value
FROM evaluation_results
UNION ALL
SELECT
    'Unique Queries Evaluated',
    COUNT(DISTINCT query_text)
FROM evaluation_results
UNION ALL
SELECT
    'Average Relevance Score (1-5)',
    ROUND(AVG(CAST(relevance_score AS FLOAT)), 2)
FROM evaluation_results
UNION ALL
SELECT
    'Top-1 Accuracy (best result in position 1)',
    ROUND(SUM(CASE WHEN best_result_position = 1 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1)
FROM evaluation_results;

SELECT '=== RELEVANCE SCORE DISTRIBUTION ===' as section

SELECT
    'Score ' || relevance_score as score,
    COUNT(*) as evaluation_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM evaluation_results WHERE evaluation_results.relevance_score IS NOT NULL), 1) as pct_of_evaluations
FROM evaluation_results
WHERE relevance_score IS NOT NULL
GROUP BY relevance_score
ORDER BY relevance_score DESC;

SELECT '=== BEST RESULT POSITION DISTRIBUTION ===' as section

SELECT
    'Position ' || best_result_position as position,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM evaluation_results WHERE best_result_position IS NOT NULL), 1) as pct
FROM evaluation_results
WHERE best_result_position IS NOT NULL
GROUP BY best_result_position
ORDER BY best_result_position;

SELECT '=== EVALUATION BY QUERY TYPE ===' as section

SELECT
    tq.query_type,
    COUNT(er.id) as evaluations,
    ROUND(AVG(CAST(er.relevance_score AS FLOAT)), 2) as avg_relevance,
    SUM(CASE WHEN er.best_result_position = 1 THEN 1 ELSE 0 END) as top1_hits,
    ROUND(SUM(CASE WHEN er.best_result_position = 1 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(er.id), 0), 1) as top1_accuracy_pct
FROM evaluation_results er
LEFT JOIN test_queries tq ON er.query_text = tq.query_text
GROUP BY tq.query_type
ORDER BY evaluations DESC;

SELECT '=== RECENT EVALUATIONS (last 20) ===' as section

SELECT
    datetime(er.created_at) as evaluated_at,
    er.query_text,
    er.relevance_score,
    er.best_result_position,
    er.notes
FROM evaluation_results er
ORDER BY er.created_at DESC
LIMIT 20;

SELECT '=== EVALUATION TIMELINE ===' as section

SELECT
    DATE(er.created_at) as evaluation_date,
    COUNT(*) as evaluations_done,
    ROUND(AVG(CAST(er.relevance_score AS FLOAT)), 2) as avg_relevance,
    SUM(CASE WHEN er.best_result_position = 1 THEN 1 ELSE 0 END) as top1_hits
FROM evaluation_results er
GROUP BY DATE(er.created_at)
ORDER BY evaluation_date DESC
LIMIT 30;

SELECT '=== QUERIES WITHOUT EVALUATIONS ===' as section

SELECT
    tq.id,
    tq.query_text,
    tq.query_type,
    COUNT(er.id) as evaluation_count
FROM test_queries tq
LEFT JOIN evaluation_results er ON tq.query_text = er.query_text
GROUP BY tq.query_text, tq.query_type
HAVING COUNT(er.id) = 0
ORDER BY tq.query_type, tq.query_text;

SELECT '=== NOTES FROM EVALUATIONS ===' as section

SELECT
    er.query_text,
    er.relevance_score,
    er.best_result_position,
    er.notes
FROM evaluation_results er
WHERE er.notes IS NOT NULL AND TRIM(er.notes) != ''
ORDER BY er.created_at DESC
LIMIT 20;
