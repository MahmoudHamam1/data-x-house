-- Q4: Aggregation & Sorting
-- Complexity: Medium-High
-- Description: GROUP BY with COUNT and ORDER BY

SELECT 
    o_orderpriority, 
    COUNT(*) AS cnt 
FROM orders 
GROUP BY o_orderpriority 
ORDER BY cnt DESC;
