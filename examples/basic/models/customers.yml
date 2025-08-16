models:
  - name: customers
    description: "Basic Level 1 tests only"
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
