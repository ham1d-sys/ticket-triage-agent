# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

## [v0.1.1] - 2026-09-03

### Added

- Added success logging to the `write_outputs()` method in `TriageProcessor`.

### Changed

- Refactored I/O logic by moving main-level reading and writing functions from `triage.py` to `ticket_io.py`.
- Updated the **How It Works** section of the README for better technical accuracy.

## [v0.1.0] - 2026-09-03

### Added

- Load tickets from a CSV file.
- Validate tickets against the configured validation rules.
- Triage valid tickets by category, urgency, and reason.
- Export triaged, invalid, and needs-review tickets to separate CSV files.