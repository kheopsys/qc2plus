"""
2QC+ Data Quality Automation Framework
Setup configuration
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="qc2plus",
    version="1.0.0",
    author="QC2Plus Team",
    author_email="contact@qc2plus.org",
    description="Data Quality Automation Framework with ML-powered anomaly detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/qc2plus/qc2plus",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
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
    keywords="data-quality, sql, ml, anomaly-detection, dbt",
    project_urls={
        "Bug Reports": "https://github.com/qc2plus/qc2plus/issues",
        "Source": "https://github.com/qc2plus/qc2plus/",
        "Documentation": "https://qc2plus.readthedocs.io/",
    },
)
