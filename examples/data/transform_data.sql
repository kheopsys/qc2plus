
-- Transform data

-- Customers customer_datamart
CREATE TABLE demo.customer_datamart AS 
    WITH mart AS (
        SELECT
            cus.customer_id
            , cus.country
            , SUM(total_amount) AS lifetime_value
            , COUNT(DISTINCT order_id) AS order_frequency
        FROM demo.customers cus 
        LEFT JOIN demo.orders ord
        ON cus.customer_id=ord.customer_id
        WHERE ord.order_date >= CURRENT_DATE - INTERVAL '90 days' 
        GROUP BY 1, 2
    )

    SELECT
        customer_id
        , country
        , lifetime_value
        , order_frequency
        , CASE 
            WHEN order_frequency = 1 THEN 'Mono-buyer'
            WHEN order_frequency < 20 THEN 'Regular-buyer'
            WHEN order_frequency >= 20 THEN 'VIP-buyer'
            ELSE 'Not-segmented'
        END AS customer_segment
    FROM mart
;
