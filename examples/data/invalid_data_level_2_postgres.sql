--FOR CORRELATION ISSUES IN LEVEL 2 TESTS
-- 5. TABLE CUSTOMER_DATAMART - DONNÉES INVALIDES (CORRELATION)
-- ============================================
INSERT INTO demo.customer_datamart (customer_id, country, lifetime_value, order_frequency, customer_segment)
VALUES
(1, 'USA', 5000, 25, 'VIP-buyer'),
(2, 'USA', 100, 25, 'Mono-buyer'),
(3, 'USA', 2500, 25, 'Regular-buyer'),
(4, 'USA', 8000, 25, 'VIP-buyer'),
(5, 'USA', 150, 25, 'Mono-buyer');