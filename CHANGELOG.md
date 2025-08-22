# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.1.0] - 2025-12-22

### Added
- Initial release of GEODES Sentinel-2 Processor
- Search functionality for Sentinel-2 imagery via GEODES API
- Download management with progress tracking and retry logic
- Automatic cropping to area of interest (AOI)
- Vegetation indices calculation (NDVI, EVI, NDWI, SAVI, GNDVI, NDRE)
- Batch processing support for multiple areas
- Command-line interface (CLI) with multiple commands
- Configuration system (environment variables, YAML config files)
- Dry-run mode for previewing operations
- Comprehensive documentation and examples
- Unit tests with ~50% coverage
- Support for reading dates from GeoJSON properties
- Modular architecture for flexible usage

### Features
- **Core functionality**:
  - GEODES STAC API integration
  - Multi-band raster processing
  - Automatic coordinate system transformations
  - ZIP archive handling and extraction

- **CLI commands**:
  - `process` - Complete processing pipeline
  - `search` - Search for products only
  - `download` - Download products
  - `crop` - Crop bands to AOI
  - `indices` - Calculate vegetation indices
  - `batch` - Batch process multiple areas
  - `info` - Display bands and indices information

- **Configuration options**:
  - API key management
  - Cloud cover filtering
  - Band selection
  - Output format options
  - Download preservation

### Documentation
- README with quick start guide
- API documentation
- CLI reference
- Example scripts for common workflows
- Publishing guide for PyPI

### Development
- Black code formatting
- Ruff linting
- MyPy type checking
- Pytest test suite
- GitHub Actions CI/CD workflows
- Makefile for common tasks

## [Unreleased]

### To Do
- Publish to PyPI
- Add more vegetation indices
- Support for Sentinel-2 Level 2A products
- Parallel download support
- Web UI interface
- Docker container support