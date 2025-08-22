# Quick Start Guide

## Your First Processing

### 1. Prepare Your Area File

Create a GeoJSON file with your area of interest. **Important**: The file must include date properties.

```json
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "properties": {
      "Name": "MyField",
      "begin": "2024-06-01T00:00:00Z",
      "end": "2024-06-30T00:00:00Z"
    },
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[
        [22.7724, 5.9666],
        [22.7751, 5.9675],
        [22.7777, 5.9643],
        [22.7750, 5.9633],
        [22.7724, 5.9666]
      ]]]
    }
  }]
}
```

### 2. Test with Dry Run

Before downloading data, test what will be processed:

```bash
geodes-sentinel2 process area.geojson ./output --dry-run
```

This shows:
- How many products will be downloaded
- Estimated download size
- What bands and indices will be calculated

### 3. Run Processing

Process your area with vegetation indices:

```bash
geodes-sentinel2 process area.geojson ./output \
    -c 30 \
    -i "NDVI EVI" \
    --keep-zips
```

Options:
- `-c 30`: Maximum 30% cloud cover
- `-i "NDVI EVI"`: Calculate NDVI and EVI indices
- `--keep-zips`: Keep downloaded files for future use

### 4. Check Results

Your output directory will contain:
```
output/
├── downloads/      # Original ZIP files (if --keep-zips)
├── crops/         # Cropped bands for your area
├── indices/       # Calculated vegetation indices
└── results.csv    # Summary of all products
```

## Using Python API

```python
from geodes_sentinel2 import Sentinel2Processor

# Initialize processor
processor = Sentinel2Processor(output_dir="./output")

# Process area (dates from GeoJSON)
results = processor.process(
    area="field.geojson",
    max_cloud_cover=30,
    indices=['NDVI', 'EVI'],
    keep_downloads=True
)

# Results is a pandas DataFrame
print(f"Processed {len(results)} products")
print(results[['date', 'cloud_cover', 'bands_cropped']].head())
```

## Common Workflows

### Search Only

Find available products without downloading:

```bash
geodes-sentinel2 search area.geojson ./output -c 20
```

### Download Specific Products

Download from previous search results:

```bash
geodes-sentinel2 download search_results.json ./downloads
```

### Calculate Indices from Existing Data

If you already have cropped bands:

```bash
geodes-sentinel2 indices ./crops ./indices -i "NDVI EVI NDWI SAVI"
```

### Batch Processing

Process multiple fields at once:

```bash
geodes-sentinel2 batch field1.geojson field2.geojson field3.geojson ./output \
    -i "NDVI" \
    --csv batch_results.csv
```

## Using Configuration File

Create `config.yaml` to set defaults:

```yaml
defaults:
  max_cloud_cover: 20.0
  bands:
    - B04  # Red
    - B08  # NIR
  indices:
    - NDVI
    - EVI
  keep_downloads: true
```

Then run without specifying options:

```bash
geodes-sentinel2 process area.geojson ./output --config config.yaml
```

## Tips

1. **Start with dry-run**: Always test with `--dry-run` first
2. **Use appropriate date ranges**: Shorter ranges = faster processing
3. **Keep ZIP files**: Use `--keep-zips` to avoid re-downloading
4. **Monitor disk space**: Each product needs ~1-2GB total
5. **Check cloud cover**: Lower values = fewer but cleaner images

## Next Steps

- [CLI Reference](cli.md) - All command options
- [Configuration](configuration.md) - Customize defaults
- [Examples](examples.md) - More use cases
- [API Reference](api.md) - Python programming interface