"""
2QC+ Data Quality Automation Framework

A comprehensive framework for automated data quality control with two levels:
- Level 1: Business rule validation (constraints, formats, statistical thresholds)
- Level 2: ML-powered anomaly detection (correlations, temporal patterns, distributions)
"""

__version__ = "1.0.4"
__author__ = "QC2Plus Team"
__email__ = "contact-qc2plus@kheopsys.com"


__all__ = [
    "QC2PlusProject",
    "ConnectionManager",
    "QC2PlusRunner",
    "__version__",
]


def __getattr__(name):
    """Lazy imports to avoid circular dependencies"""
    if name == "QC2PlusProject":
        from qc2plus.core.project import QC2PlusProject

        return QC2PlusProject

    elif name == "ConnectionManager":
        from qc2plus.core.connection import ConnectionManager

        return ConnectionManager

    elif name == "QC2PlusRunner":
        from qc2plus.core.runner import QC2PlusRunner

        return QC2PlusRunner

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
