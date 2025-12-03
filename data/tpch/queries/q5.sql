-- Q5: Join & Aggregation
-- Complexity: High
-- Description: Multi-table JOIN with aggregation

SELECT 
    c_nationkey, 
    SUM(l_extendedprice) AS total_revenue
FROM customer c 
JOIN orders o ON c.c_custkey = o.o_custkey 
JOIN lineitem l ON o.o_orderkey = l.l_orderkey 
GROUP BY c_nationkey;
