-- 03_review_late_vs_on_time.sql
-- Request: "Do late orders hurt our ratings?" (Customer success / Sales)
-- Clarified: average latest review score and 1-star share for delivered
-- orders that have both a delivery date and a review, on-time vs late.

SELECT
    CASE on_time_flag WHEN 1 THEN 'on_time' ELSE 'late' END AS delivery,
    COUNT(*) AS reviewed_orders,
    ROUND(AVG(review_score), 2) AS avg_review_score,
    ROUND(100.0 * SUM(CASE WHEN review_score = 1 THEN 1 ELSE 0 END) / COUNT(*), 1)
        AS one_star_pct
FROM master_orders
WHERE is_delivered = 1
  AND on_time_flag IS NOT NULL
  AND review_score IS NOT NULL
GROUP BY on_time_flag
ORDER BY delivery DESC;
