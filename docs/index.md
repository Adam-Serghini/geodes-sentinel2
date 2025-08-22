# Sentinel-2 GEODES Documentation

Welcome to the GEODES Sentinel-2 Processor documentation!

## Overview

The GEODES Sentinel-2 Processor is a Python package for searching, downloading, and processing Sentinel-2 satellite imagery from the GEODES portal (CNES - French space agency).

## Features

- 🔍 **Search** Sentinel-2 imagery by location and date range
- 📥 **Download** satellite data with automatic retry and progress tracking
- ✂️ **Crop** imagery to your area of interest (supports any polygon shape)
- 🌱 **Calculate** vegetation indices (NDVI, EVI, NDWI, SAVI, GNDVI, NDRE)
- 📊 **Export** results to CSV with detailed metadata
- 🗺️ **Batch process** multiple areas efficiently
- 🎯 **Modular design** - use only what you need

## Quick Links

- [Installation](installation.md)
- [Quick Start](quickstart.md)
- [CLI Reference](cli.md)
- [API Reference](api.md)
- [Configuration](configuration.md)
- [Examples](examples.md)
- [Troubleshooting](troubleshooting.md)

## Requirements

- Python 3.9 or higher
- GEODES API key (free registration at [GEODES portal](https://geodes-portal.cnes.fr))
- At least 2GB of disk space for downloads
- Internet connection for data retrieval

## License

This project is licensed under the MIT License.