-- Q3: Aggregation
-- Complexity: Medium
-- Description: GROUP BY aggregation with COUNT

SELECT 
    o_custkey, 
    COUNT(*) AS order_count
FROM orders 
GROUP BY o_custkey;
