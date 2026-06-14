# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2026-06-14

### Fixed
- Import `ScannerEntity` from its canonical path to avoid the deprecated
  `device_tracker.config_entry` alias removed in HA Core 2027.6
