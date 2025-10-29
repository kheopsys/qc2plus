# Changelog

All notable changes to QC2Plus will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]



## [1.0.3] - 2025-01-29

### Added
- Complete Docker Compose setup with demo databases
- PostgreSQL demo database with sample data
- Results database for quality metrics storage
- Multi-channel alerting support (Email, Slack, Teams)
- Power BI integration with auto-created tables
- Enhanced documentation with Docker guides

### Changed
- Improved error handling in Level 2 analyzers
- Optimized statistical threshold calculations
- Updated README with comprehensive examples

### Fixed
- NULL value handling in statistical threshold tests
- Connection timeout issues with large datasets
- Memory leak in correlation analyzer

## [1.0.2] - 2025-10-26

### Added
- Level 2 ML-based anomaly detection
  - Correlation analysis
  - Temporal pattern detection
  - Distribution monitoring
- Enhanced alerting system with severity levels
- Statistical threshold test for Level 1

### Changed
- Refactored core runner for better performance
- Improved logging system
- Updated dependencies

### Fixed
- Foreign key validation with NULL values
- Email format validation regex
- Date validation for edge cases

## [1.0.1] - 2025-10-24

### Fixed
- Package installation issues
- Missing dependencies in requirements.txt
- CLI entry point configuration

## [1.0.0] - 2025-10-23

### Added
- Initial release
- Level 1 SQL-based quality tests
  - unique, not_null, foreign_key
  - range_check, accepted_values
  - email_format, future_date
- Basic alerting via email
- PostgreSQL, Snowflake, BigQuery support
- CLI interface (`qc2plus` command)
- Project initialization (`qc2plus init`)
- YAML-based configuration
- Result persistence to database

---

## Version History

- **1.0.3** - Docker support + Enhanced documentation
- **1.0.2** - Level 2 ML analyzers
- **1.0.1** - Bug fixes
- **1.0.0** - Initial release

---

## Types of Changes

- **Added** - New features
- **Changed** - Changes to existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Vulnerability fixes

---

[Unreleased]: https://github.com/YOUR_USERNAME/qc2plus/compare/v1.0.3...HEAD
[1.0.3]: https://github.com/YOUR_USERNAME/qc2plus/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/YOUR_USERNAME/qc2plus/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/YOUR_USERNAME/qc2plus/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/YOUR_USERNAME/qc2plus/releases/tag/v1.0.0