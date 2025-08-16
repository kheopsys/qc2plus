models:
  - name: customers
    description: "Advanced Level 1 + Level 2 ML tests"
    qc2plus_tests:
      level1:
        - unique:
            column_name: customer_id
            severity: critical
        - not_null:
            column_name: email
            severity: critical
        - email_format:
            column_name: email
            severity: medium
        - range_check:
            column_name: age
            min_value: 0
            max_value: 120
            severity: medium
      
      level2:
        correlation_analysis:
          variables: [lifetime_value, order_frequency]
          expected_correlation: 0.7
          threshold: 0.3
        
        temporal_analysis:
          date_column: created_at
          metrics: [count]
          seasonality_check: true
          window_days: 60
        
        multivariate_analysis:
          features: [lifetime_value, order_frequency, avg_order_value]
          contamination: 0.1
          algorithms: [isolation_forest, lof]
