-- Search Testing Query Suite Status (litecli compatible)
-- Monitor test query coverage and evaluation progress
-- Usage: uv run litecli data/videos.db < scripts/queries/search_testing-litecli.sql

SELECT '=== TEST QUERY SUITE STATUS ===' as section;

SELECT
    'Total Test Queries' as metric,
    COUNT(*) as value
FROM test_queries
UNION ALL
SELECT
    'Query Types',
    COUNT(DISTINCT query_type)
FROM test_queries
UNION ALL
SELECT
    'Evaluated Queries',
    COUNT(DISTINCT query_text)
FROM evaluation_results
UNION ALL
SELECT
    'Unevaluated Queries',
    (SELECT COUNT(DISTINCT query_text) FROM test_queries)
    - COALESCE((SELECT COUNT(DISTINCT query_text) FROM evaluation_results), 0)
FROM test_queries;

SELECT '=== QUERIES BY TYPE ===' as section

SELECT
    COALESCE(query_type, 'unknown') as query_type,
    COUNT(*) as query_count
FROM test_queries
GROUP BY query_type
ORDER BY query_count DESC;

SELECT '=== EVALUATION COVERAGE BY QUERY TYPE ===' as section

SELECT
    tq.query_type,
    COUNT(DISTINCT tq.id) as total_queries,
    COUNT(DISTINCT er.query_text) as evaluated_queries,
    COUNT(DISTINCT tq.id) - COUNT(DISTINCT er.query_text) as remaining_queries,
    ROUND(COUNT(DISTINCT er.query_text) * 100.0 / NULLIF(COUNT(DISTINCT tq.id), 0), 1) as coverage_pct,
    ROUND(AVG(CAST(er.relevance_score AS FLOAT)), 2) as avg_relevance
FROM test_queries tq
LEFT JOIN evaluation_results er ON tq.query_text = er.query_text
WHERE tq.query_type IS NOT NULL
GROUP BY tq.query_type
ORDER BY coverage_pct DESC;

SELECT '=== ALL TEST QUERIES ===' as section

SELECT
    tq.id,
    tq.query_text,
    tq.query_type,
    tq.expected_channels,
    COUNT(DISTINCT er.id) as evaluation_count,
    ROUND(AVG(CAST(er.relevance_score AS FLOAT)), 2) as avg_relevance,
    CASE WHEN COUNT(DISTINCT er.id) > 0 THEN 'Evaluated' ELSE 'Pending' END as status
FROM test_queries tq
LEFT JOIN evaluation_results er ON tq.query_text = er.query_text
GROUP BY tq.id, tq.query_text, tq.query_type
ORDER BY tq.query_type, tq.query_text;

SELECT '=== QUERIES WITHOUT EVALUATIONS ===' as section

SELECT
    tq.id,
    tq.query_text,
    tq.query_type,
    tq.expected_channels
FROM test_queries tq
LEFT JOIN evaluation_results er ON tq.query_text = er.query_text
WHERE er.id IS NULL
ORDER BY tq.query_type, tq.query_text;

SELECT '=== HIGHEST RATED QUERIES ===' as section

SELECT
    tq.query_text,
    tq.query_type,
    ROUND(AVG(CAST(er.relevance_score AS FLOAT)), 2) as avg_relevance,
    COUNT(DISTINCT er.id) as evaluation_count,
    SUM(CASE WHEN er.best_result_position = 1 THEN 1 ELSE 0 END) as top1_hits
FROM test_queries tq
JOIN evaluation_results er ON tq.query_text = er.query_text
GROUP BY tq.query_text, tq.query_type
ORDER BY avg_relevance DESC, evaluation_count DESC
LIMIT 20;

SELECT '=== LOWEST RATED QUERIES ===' as section

SELECT
    tq.query_text,
    tq.query_type,
    ROUND(AVG(CAST(er.relevance_score AS FLOAT)), 2) as avg_relevance,
    COUNT(DISTINCT er.id) as evaluation_count,
    SUM(CASE WHEN er.best_result_position = 1 THEN 1 ELSE 0 END) as top1_hits
FROM test_queries tq
JOIN evaluation_results er ON tq.query_text = er.query_text
GROUP BY tq.query_text, tq.query_type
ORDER BY avg_relevance ASC, evaluation_count DESC
LIMIT 20;

SELECT '=== EXPECTED CHANNELS ANALYSIS ===' as section

SELECT
    expected_channels,
    COUNT(*) as query_count
FROM test_queries
WHERE expected_channels IS NOT NULL AND TRIM(expected_channels) != ''
GROUP BY expected_channels
ORDER BY query_count DESC;
