-- Q1: Simple Projection
-- Complexity: Low
-- Description: Basic SELECT with LIMIT to test simple data retrieval

SELECT 
    l_orderkey, 
    l_shipdate 
FROM lineitem 
LIMIT 1000;
