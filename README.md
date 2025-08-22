# 🛰️ GEODES Sentinel-2 Processor

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/Adam-serghini/geodes-sentinel2/branch/main/graph/badge.svg)](https://codecov.io/gh/Adam-serghini/geodes-sentinel2)

A Python package for searching, downloading, and processing Sentinel-2 satellite imagery from the GEODES portal (CNES - French space agency).

## 🚀 Features

- 🔍 **Search** Sentinel-2 imagery by location and date range
- 📥 **Download** satellite data with automatic retry and progress tracking
- 💾 **Preserve** downloaded ZIP files for future reprocessing
- ✂️ **Crop** imagery to your area of interest (supports any polygon shape)
- 🌱 **Calculate** vegetation indices (NDVI, EVI, NDWI, SAVI, GNDVI, NDRE)
- 📊 **Export** results to CSV with detailed metadata
- 🗺️ **Batch process** multiple areas efficiently
- 🎯 **Modular design** - use only what you need

## 📋 Requirements

- Python 3.9 or higher
- GEODES API key (free registration at [GEODES portal](https://geodes-portal.cnes.fr))
- At least 2GB of disk space for downloads
- Internet connection for data retrieval

## 📦 Installation

### From PyPI

```bash
pip install geodes-sentinel2
```

### From Source

```bash
# Clone the repository
git clone https://github.com/Adam-serghini/geodes-sentinel2.git
cd geodes-sentinel2

# Install with pip
pip install -e .

# Or using UV (recommended for development)
uv venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On Linux/Mac
uv pip install -e .
```

## 🎯 Quick Start

### 1. Set up your GEODES API key

Create a `.env` file from the template:
```bash
cp .env.example .env
```

Edit `.env` and add your GEODES API key:
```
GEODES_API_KEY=your_api_key_here
```

### 2. Basic Usage

```python
from geodes_sentinel2 import Sentinel2Processor

# Initialize processor with output directory
processor = Sentinel2Processor(output_dir="./output")

# Process imagery (dates are read from GeoJSON properties)
results = processor.process(
    area="path/to/area.geojson",
    max_cloud_cover=30,
    indices=["NDVI", "EVI"]
)
```

**Note**: Your GeoJSON file must contain `begin` and `end` date properties:
```json
{
  "type": "Feature",
  "properties": {
    "Name": "MyField",
    "begin": "2024-01-01T00:00:00Z",
    "end": "2024-03-31T00:00:00Z"
  },
  "geometry": { ... }
}
```

### 3. Command Line Interface

All commands now use dates from GeoJSON file properties:

```bash
# Complete processing pipeline
geodes-sentinel2 process field.geojson ./output \
    -c 30 \
    -i NDVI EVI NDWI \
    --keep-zips

# Search only
geodes-sentinel2 search field.geojson ./search_output \
    -c 30

# Download from search results
geodes-sentinel2 download search_results.json ./downloads \
    -z field_name

# Crop specific bands
geodes-sentinel2 crop ./downloads field.geojson ./crops \
    -b B02 B03 B04 B08

# Calculate vegetation indices
geodes-sentinel2 indices ./crops ./indices \
    -i NDVI EVI NDWI SAVI

# Batch processing for multiple fields (each with its own dates)
geodes-sentinel2 batch field1.geojson field2.geojson ./batch_output \
    -c 30 \
    -i NDVI EVI \
    --csv batch_results.csv

# Get information about bands and indices
geodes-sentinel2 info
```

## 🌱 Vegetation Indices

The package supports multiple vegetation indices:

- **NDVI** (Normalized Difference Vegetation Index): Vegetation health monitoring
- **EVI** (Enhanced Vegetation Index): Improved sensitivity in high biomass regions
- **NDWI** (Normalized Difference Water Index): Water content in vegetation
- **SAVI** (Soil Adjusted Vegetation Index): Minimizes soil brightness influences
- **GNDVI** (Green NDVI): Chlorophyll content assessment
- **NDRE** (Normalized Difference Red Edge): Crop health and nitrogen status

## 📊 Examples

Check the `examples/` directory for complete working examples:

### Basic Usage (`examples/basic_usage.py`)
```python
# Simple workflow with vegetation indices
# Dates are read from GeoJSON properties
processor = Sentinel2Processor(output_dir="./output")
results = processor.process(
    area="field.geojson",
    indices=["NDVI", "EVI"],
    keep_downloads=True  # Preserve ZIP files
)
```

### Vegetation Monitoring (`examples/vegetation_monitoring.py`)
- Track vegetation changes over time
- Calculate multiple indices for crop health
- Compare fields side by side
- Generate time series analysis

### Organized Outputs (`examples/organized_outputs.py`)
- Seasonal monitoring with structured directories
- Multi-field processing with field-specific outputs
- Timestamped runs for versioning
- Tile-based processing for large areas

### CLI Usage (`examples/cli_usage.sh` / `cli_usage.bat`)
- Step-by-step command-line workflow
- Custom output directories for each step
- Complete project organization example

### Advanced Features
- **Modular processing**: Search, download, and process separately
- **Batch mode**: Process multiple areas with individual date ranges
- **Automatic date extraction**: Dates read from GeoJSON properties
- **ZIP preservation**: Keep downloads for future reprocessing without re-downloading
- **Progress tracking**: Real-time progress for batch operations
- **Error resilience**: Batch processing continues even if individual areas fail

## 🛠️ Development

### Setup Development Environment

```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black geodes_sentinel2/
ruff check geodes_sentinel2/

# Type checking
mypy geodes_sentinel2/
```

### Running Tests

```bash
pytest tests/ -v --cov=geodes_sentinel2
```

## 📚 Documentation

Full documentation is available at [https://geodes-sentinel2.readthedocs.io](https://geodes-sentinel2.readthedocs.io)

## 🔧 Troubleshooting

### Common Issues

1. **"No dates found in GeoJSON file"**
   - Ensure your GeoJSON has `begin` and `end` properties
   - Dates should be in ISO format: `"2024-01-01T00:00:00Z"`

2. **"Geometry does not intersect raster"**
   - Check that your area is within the Sentinel-2 tile coverage
   - Verify coordinates are in WGS84 (EPSG:4326)

3. **"API key not found"**
   - Set the `GEODES_API_KEY` environment variable
   - Or create a `.env` file with your key

4. **Large downloads failing**
   - The package automatically retries failed downloads
   - For very large areas, process in smaller batches

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- CNES for providing the GEODES portal
- ESA for Sentinel-2 mission
- The open-source geospatial Python community

## 📧 Contact

Adam Serghini - [@Adam-serghini](https://github.com/Adam-serghini)

Project Link: [https://github.com/Adam-serghini/geodes-sentinel2](https://github.com/Adam-serghini/geodes-sentinel2)