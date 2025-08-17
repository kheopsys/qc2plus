"""
2QC+ Data Quality Automation Framework

A comprehensive framework for automated data quality control with two levels:
- Level 1: Business rule validation (constraints, formats, statistical thresholds)
- Level 2: ML-powered anomaly detection (correlations, temporal patterns, distributions)
"""

__version__ = "1.0.0"
__author__ = "QC2Plus Team"
__email__ = "contact-qc2plus@kheopsys.com"

from qc2plus.core.project import QC2PlusProject
from qc2plus.core.runner import QC2PlusRunner
from qc2plus.level1.engine import Level1Engine
from qc2plus.level2.correlation import CorrelationAnalyzer
from qc2plus.level2.temporal import TemporalAnalyzer
from qc2plus.level2.distribution import DistributionAnalyzer

__all__ = [
    "QC2PlusProject",
    "QC2PlusRunner", 
    "Level1Engine",
    "CorrelationAnalyzer",
    "TemporalAnalyzer",
    "DistributionAnalyzer",
]
