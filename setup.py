"""
2QC+ Data Quality Automation Framework
Setup configuration
"""

import os
from setuptools import setup, find_packages

readme_path = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "2QC+ Data Quality Automation Framework"

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="qc2plus",
    version="1.0.3",
    author="QC2Plus Team",
    author_email="qc2plus@kheopsys.com",
    description="Data Quality Automation Framework with ML-powered anomaly detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kheopsys/qc2plus-internal",
    packages=find_packages(exclude=[
    "examples",
    "examples.*",
    "tests",
    "tests.*",

]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Analytics engineers",
        "Topic :: Database",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "qc2plus=qc2plus.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "qc2plus": [
            "level1/templates/*.sql",
            "templates/*.yml",
        ],
    },
    keywords="data-quality, sql, ml, anomaly-detection, dbt-like",
    project_urls={
        "Bug Reports": "https://github.com/kheopsys/qc2plus-internal/issues",
        "Source": "https://github.com/kheopsys/qc2plus-internal",
        "Documentation": "https://github.com/kheopsys/qc2plus-internal/README.md",
    },
)
