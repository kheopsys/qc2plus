"""
2QC+ Anomaly Filter
Contextual analysis to eliminate false positives by checking:
1. Seasonal patterns
2. Correlated indicator variations
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

from qc2plus.core.connection import ConnectionManager


class AnomalyFilter:
    """Filters false anomaly alerts using contextual analysis"""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    def filter_anomalies(
        self, results: Dict[str, Any], model_name: str
    ) -> Dict[str, Any]:
        """Filter anomalies using seasonal and correlation context"""

        try:
            filtered_results = results.copy()

            # Process each model's results
            for model_name, model_results in results.get("models", {}).items():

                # Filter Level 1 anomalies (statistical thresholds)
                if "level1" in model_results:
                    filtered_results["models"][model_name]["level1"] = (
                        self._filter_level1_anomalies(
                            model_results["level1"], model_name
                        )
                    )

                # Filter Level 2 anomalies (ML detections)
                if "level2" in model_results:
                    filtered_results["models"][model_name]["level2"] = (
                        self._filter_level2_anomalies(
                            model_results["level2"], model_name
                        )
                    )

            # Recalculate summary statistics
            filtered_results = self._recalculate_summary(filtered_results)

            return filtered_results

        except Exception as e:
            logging.error(f"Anomaly filtering failed: {str(e)}")
            return results  # Return original results if filtering fails

    def _filter_level1_anomalies(
        self, level1_results: Dict[str, Any], model_name: str
    ) -> Dict[str, Any]:
        """Filter Level 1 statistical threshold anomalies"""

        filtered_results = {}

        for test_name, test_result in level1_results.items():
            if not test_result.get("passed", True):

                # Check if this is a statistical_threshold test
                if "statistical_threshold" in test_name:

                    # 1. Check seasonal context
                    is_seasonal = self._is_seasonal_period()

                    # 2. Check correlated indicators
                    has_correlated_variations = self._check_correlated_variations(
                        model_name, test_name
                    )

                    # Filter logic
                    if is_seasonal and has_correlated_variations:
                        # Convert to contextual variation (not an anomaly)
                        filtered_results[test_name] = {
                            "passed": True,  # Override to passed
                            "original_status": "failed",
                            "filter_reason": "seasonal_correlated_variation",
                            "message": "Normal variation due to seasonal pattern and correlated indicators",
                            "severity": "info",
                            "contextual_analysis": {
                                "seasonal_period": is_seasonal,
                                "correlated_variations": has_correlated_variations,
                            },
                        }
                    else:
                        # Keep as anomaly
                        filtered_results[test_name] = test_result
                else:
                    # Non-statistical tests pass through unchanged
                    filtered_results[test_name] = test_result
            else:
                # Passed tests remain unchanged
                filtered_results[test_name] = test_result

        return filtered_results

    def _filter_level2_anomalies(
        self, level2_results: Dict[str, Any], model_name: str
    ) -> Dict[str, Any]:
        """Filter Level 2 ML anomalies (distribution, temporal)"""

        filtered_results = {}

        for analyzer_name, analyzer_result in level2_results.items():
            if not analyzer_result.get("passed", True):

                if analyzer_name in ["distribution", "temporal"]:

                    # Check contextual factors
                    context = self._analyze_anomaly_context(analyzer_result, model_name)

                    if context["should_filter"]:
                        # Convert to contextual variation
                        filtered_results[analyzer_name] = {
                            "passed": True,  # Override to passed
                            "original_status": "failed",
                            "anomalies_count": 0,
                            "filter_reason": context["reason"],
                            "message": f"Normal variation: {context['explanation']}",
                            "contextual_analysis": context["details"],
                        }
                    else:
                        # Keep as anomaly
                        filtered_results[analyzer_name] = analyzer_result
                else:
                    # Other analyzers pass through unchanged
                    filtered_results[analyzer_name] = analyzer_result
            else:
                # Passed tests remain unchanged
                filtered_results[analyzer_name] = analyzer_result

        return filtered_results

    def _is_seasonal_period(self) -> Dict[str, Any]:
        """Check if current period shows strong seasonal patterns"""

        try:
            current_date = datetime.now()

            # Define high-seasonality periods
            seasonal_periods = [
                # Holiday seasons
                {
                    "start": (11, 20),
                    "end": (12, 31),
                    "name": "Black Friday / Holiday season",
                },
                {
                    "start": (1, 1),
                    "end": (1, 15),
                    "name": "New Year period",
                },
                # Back to school
                {
                    "start": (8, 15),
                    "end": (9, 15),
                    "name": "Back to school",
                },
                # Summer vacation
                {
                    "start": (7, 1),
                    "end": (8, 15),
                    "name": "Summer vacation",
                },
                # Spring season
                {
                    "start": (3, 15),
                    "end": (5, 15),
                    "name": "Spring season",
                },
            ]

            current_month = current_date.month
            current_day = current_date.day

            for period in seasonal_periods:
                start_month, start_day = period["start"]
                end_month, end_day = period["end"]

                # Handle year-end wrap around
                if start_month > end_month:  # Nov-Dec to Jan
                    if (
                        (current_month == start_month and current_day >= start_day)
                        or (current_month == end_month and current_day <= end_day)
                        or (current_month == 12)
                    ):
                        return {
                            "is_seasonal": True,
                            "period_name": period["name"],
                            "intensity": "high",
                        }
                else:  # Normal periods
                    if start_month <= current_month <= end_month:
                        if (
                            (current_month == start_month and current_day >= start_day)
                            or (current_month == end_month and current_day <= end_day)
                            or (start_month < current_month < end_month)
                        ):
                            return {
                                "is_seasonal": True,
                                "period_name": period["name"],
                                "intensity": "high",
                            }

            # Check for weekend effects (Fridays/Saturdays often have spikes)
            if current_date.weekday() in [
                4,
                5,
            ]:  # Friday = 4, Saturday = 5
                return {
                    "is_seasonal": True,
                    "period_name": "Weekend effect",
                    "intensity": "medium",
                }

            return {"is_seasonal": False}

        except Exception as e:
            logging.warning(f"Seasonal check failed: {str(e)}")
            return {"is_seasonal": False}

    def _check_correlated_variations(
        self, model_name: str, test_name: str
    ) -> Dict[str, Any]:
        """Check if multiple correlated indicators show similar variations"""

        try:
            schema = self.connection_manager.config.get("schema", "public")

            # Define correlated indicator groups
            correlation_groups = {
                "ecommerce_funnel": [
                    "daily_sessions",
                    "daily_page_views",
                    "daily_cart_adds",
                    "daily_orders",
                    "daily_revenue",
                ],
                "user_engagement": [
                    "daily_users",
                    "daily_sessions",
                    "session_duration",
                    "page_views",
                ],
                "sales_metrics": [
                    "daily_orders",
                    "daily_revenue",
                    "daily_customers",
                    "avg_order_value",
                ],
            }

            # Get recent variations for each group
            for group_name, indicators in correlation_groups.items():
                variations = self._get_indicator_variations(model_name, indicators)

                if len(variations) >= 3:  # Need at least 3 indicators
                    # Check if variations are consistent (all moving in same
                    # direction)
                    positive_changes = sum(
                        1 for v in variations.values() if v > 0.15
                    )  # >15% increase
                    negative_changes = sum(
                        1 for v in variations.values() if v < -0.15
                    )  # >15% decrease

                    # If most indicators move together significantly
                    if (
                        positive_changes >= len(variations) * 0.7
                        or negative_changes >= len(variations) * 0.7
                    ):
                        return {
                            "has_correlated_variations": True,
                            "group": group_name,
                            "variations": variations,
                            "pattern": (
                                "increase"
                                if positive_changes > negative_changes
                                else "decrease"
                            ),
                            "consistency_score": max(positive_changes, negative_changes)
                            / len(variations),
                        }

            return {"has_correlated_variations": False}

        except Exception as e:
            logging.warning(f"Correlation check failed: {str(e)}")
            return {"has_correlated_variations": False}

    def _get_indicator_variations(
        self, model_name: str, indicators: List[str]
    ) -> Dict[str, float]:
        """Get recent variations for a list of indicators"""

        variations = {}

        try:
            schema = self.connection_manager.config.get("schema", "public")

            # Check if we have a metrics table (like daily_metrics in advanced
            # demo)
            for indicator in indicators:

                # Try to get data from different possible tables
                queries_to_try = [
                    # From daily_metrics table (advanced schema)
                    f"""
                    SELECT
                        AVG(CASE WHEN metric_date >= CURRENT_DATE - INTERVAL '7 days' THEN {indicator} END) as recent_avg,
                        AVG(CASE WHEN metric_date BETWEEN CURRENT_DATE - INTERVAL '30 days' AND CURRENT_DATE - INTERVAL '8 days' THEN {indicator} END) as baseline_avg
                    FROM {schema}.daily_metrics
                    WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
                    """,
                    # From aggregated orders (basic schema)
                    f"""
                    SELECT
                        AVG(CASE WHEN order_date >= CURRENT_DATE - INTERVAL '7 days' THEN daily_count END) as recent_avg,
                        AVG(CASE WHEN order_date BETWEEN CURRENT_DATE - INTERVAL '30 days' AND CURRENT_DATE - INTERVAL '8 days' THEN daily_count END) as baseline_avg
                    FROM (
                        SELECT order_date, COUNT(*) as daily_count
                        FROM {schema}.orders
                        WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
                        GROUP BY order_date
                    ) daily_data
                    """,
                ]

                for query in queries_to_try:
                    try:
                        # Adapt query for different databases
                        if self.connection_manager.db_type == "bigquery":
                            query = query.replace("CURRENT_DATE", "CURRENT_DATE()")
                            query = query.replace("INTERVAL '", "INTERVAL ")
                            query = query.replace(" days'", " DAY")

                        result = self.connection_manager.execute_query(query)

                        if (
                            not result.empty
                            and result.iloc[0]["recent_avg"] is not None
                        ):
                            recent_avg = float(result.iloc[0]["recent_avg"])
                            baseline_avg = float(result.iloc[0]["baseline_avg"])

                            if baseline_avg > 0:
                                variation = (recent_avg - baseline_avg) / baseline_avg
                                variations[indicator] = variation
                                break  # Successfully got data, move to next indicator

                    except Exception:
                        continue  # Try next query

        except Exception as e:
            logging.warning(f"Failed to get indicator variations: {str(e)}")

        return variations

    def _analyze_anomaly_context(
        self, analyzer_result: Dict[str, Any], model_name: str
    ) -> Dict[str, Any]:
        """Analyze context for Level 2 anomalies"""

        context = {
            "should_filter": False,
            "reason": "",
            "explanation": "",
            "details": {},
        }

        try:
            # Check seasonal context
            seasonal_info = self._is_seasonal_period()

            # Check correlated variations
            correlation_info = self._check_correlated_variations(model_name, "general")

            # Decision logic
            if seasonal_info.get("is_seasonal", False) and correlation_info.get(
                "has_correlated_variations", False
            ):
                context.update(
                    {
                        "should_filter": True,
                        "reason": "seasonal_and_correlated",
                        "explanation": f"Variation during {
                            seasonal_info['period_name']} with {
                            correlation_info['consistency_score']:.0%} indicator consistency",
                        "details": {
                            "seasonal": seasonal_info,
                            "correlations": correlation_info,
                        },
                    }
                )
            elif (
                seasonal_info.get("is_seasonal", False)
                and seasonal_info.get("intensity") == "high"
            ):
                context.update(
                    {
                        "should_filter": True,
                        "reason": "high_seasonality",
                        "explanation": f"Expected variation during {
                            seasonal_info['period_name']}",
                        "details": {"seasonal": seasonal_info},
                    }
                )
            elif (
                correlation_info.get("has_correlated_variations", False)
                and correlation_info.get("consistency_score", 0) > 0.8
            ):
                context.update(
                    {
                        "should_filter": True,
                        "reason": "high_correlation",
                        "explanation": f"Systematic {
                            correlation_info['pattern']} across {
                            correlation_info['group']} indicators",
                        "details": {"correlations": correlation_info},
                    }
                )

        except Exception as e:
            logging.warning(f"Context analysis failed: {str(e)}")

        return context

    def _recalculate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Recalculate summary statistics after filtering"""

        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        critical_failures = 0

        for model_name, model_results in results.get("models", {}).items():

            # Count Level 1 tests
            for test_name, test_result in model_results.get("level1", {}).items():
                total_tests += 1
                if test_result.get("passed", False):
                    passed_tests += 1
                else:
                    failed_tests += 1
                    if test_result.get("severity") == "critical":
                        critical_failures += 1

            # Count Level 2 tests
            for analyzer_name, analyzer_result in model_results.get(
                "level2", {}
            ).items():
                total_tests += 1
                if analyzer_result.get("passed", False):
                    passed_tests += 1
                else:
                    failed_tests += 1

        # Update summary
        results.update(
            {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "critical_failures": critical_failures,
                "status": (
                    "success"
                    if failed_tests == 0
                    else ("critical_failure" if critical_failures > 0 else "failure")
                ),
            }
        )

        return results
