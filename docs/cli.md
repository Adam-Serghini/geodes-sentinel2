# CLI Reference

## Global Options

All commands support these global options:

- `--verbose, -v`: Enable debug logging
- `--config, -c PATH`: Path to configuration file
- `--help`: Show help message

## Commands

### process

Complete processing workflow: search, download, crop, and calculate indices.

```bash
geodes-sentinel2 process AREA OUTPUT_DIR [OPTIONS]
```

**Arguments:**
- `AREA`: Path to GeoJSON file with area of interest
- `OUTPUT_DIR`: Directory for output files

**Options:**
- `--cloud, -c FLOAT`: Maximum cloud cover percentage (default: from config or 30)
- `--bands, -b TEXT`: Space-separated list of bands to process
- `--indices, -i TEXT`: Space-separated list of indices to calculate
- `--keep-zips/--no-keep-zips`: Keep downloaded ZIP files (default: from config)
- `--csv PATH`: Save results summary to CSV file
- `--dry-run`: Show what would be done without actually doing it

**Examples:**

```bash
# Basic processing
geodes-sentinel2 process field.geojson ./output

# With specific bands and indices
geodes-sentinel2 process field.geojson ./output \
    -b "B02 B03 B04 B08" \
    -i "NDVI EVI NDWI"

# Dry run to preview
geodes-sentinel2 process field.geojson ./output --dry-run

# Save results to CSV
geodes-sentinel2 process field.geojson ./output --csv results.csv
```

### search

Search for Sentinel-2 products without downloading.

```bash
geodes-sentinel2 search AREA OUTPUT_DIR [OPTIONS]
```

**Arguments:**
- `AREA`: Path to GeoJSON file
- `OUTPUT_DIR`: Directory for search results

**Options:**
- `--cloud, -c FLOAT`: Maximum cloud cover percentage
- `--output, -o TEXT`: Output filename (default: search_results.json)

**Example:**

```bash
geodes-sentinel2 search field.geojson ./output -c 20
```

### download

Download Sentinel-2 products from search results.

```bash
geodes-sentinel2 download PRODUCTS OUTPUT_DIR [OPTIONS]
```

**Arguments:**
- `PRODUCTS`: Path to JSON file with search results
- `OUTPUT_DIR`: Directory for downloads

**Options:**
- `--zone, -z TEXT`: Zone name prefix for files (default: zone)

**Example:**

```bash
geodes-sentinel2 download search_results.json ./downloads -z myfield
```

### crop

Crop bands from downloaded ZIP files.

```bash
geodes-sentinel2 crop ZIPS AREA OUTPUT_DIR [OPTIONS]
```

**Arguments:**
- `ZIPS`: Path to directory with ZIP files or text file with paths
- `AREA`: Path to GeoJSON file
- `OUTPUT_DIR`: Directory for cropped bands

**Options:**
- `--zone, -z TEXT`: Zone name prefix for output files
- `--bands, -b TEXT`: Space-separated list of bands to crop

**Example:**

```bash
geodes-sentinel2 crop ./downloads field.geojson ./crops \
    -b "B04 B08" \
    -z field1
```

### indices

Calculate vegetation indices from cropped bands.

```bash
geodes-sentinel2 indices CROPS OUTPUT_DIR [OPTIONS]
```

**Arguments:**
- `CROPS`: Path to directory with cropped bands
- `OUTPUT_DIR`: Directory for calculated indices

**Options:**
- `--indices, -i TEXT`: Space-separated list of indices (default: "NDVI EVI NDWI")

**Available Indices:**
- `NDVI`: Normalized Difference Vegetation Index
- `EVI`: Enhanced Vegetation Index
- `NDWI`: Normalized Difference Water Index
- `SAVI`: Soil Adjusted Vegetation Index
- `GNDVI`: Green NDVI
- `NDRE`: Normalized Difference Red Edge

**Example:**

```bash
geodes-sentinel2 indices ./crops ./indices -i "NDVI EVI SAVI GNDVI"
```

### batch

Process multiple areas in batch mode.

```bash
geodes-sentinel2 batch AREAS... OUTPUT_DIR [OPTIONS]
```

**Arguments:**
- `AREAS`: One or more GeoJSON files
- `OUTPUT_DIR`: Directory for all outputs

**Options:**
- `--cloud, -c FLOAT`: Maximum cloud cover percentage
- `--indices, -i TEXT`: Space-separated list of indices
- `--csv TEXT`: Output CSV filename (default: batch_results.csv)

**Example:**

```bash
geodes-sentinel2 batch field1.geojson field2.geojson field3.geojson ./output \
    -c 25 \
    -i "NDVI EVI" \
    --csv all_fields.csv
```

### info

Display information about available bands and indices.

```bash
geodes-sentinel2 info
```

**Output:**
- Supported Sentinel-2 bands with wavelengths and resolutions
- Available vegetation indices with descriptions
- Configuration instructions

## Output Structure

All commands create organized output directories:

```
output_dir/
├── downloads/       # Original ZIP files
│   ├── zone_2024-06-01_S2A_MSIL1C_....zip
│   └── zone_2024-06-06_S2B_MSIL1C_....zip
├── crops/          # Cropped bands
│   ├── zone_2024-06-01_B02.tif
│   ├── zone_2024-06-01_B03.tif
│   ├── zone_2024-06-01_B04.tif
│   └── ...
├── indices/        # Calculated indices
│   ├── zone_2024-06-01_NDVI.tif
│   ├── zone_2024-06-01_EVI.tif
│   └── ...
└── results.csv     # Processing summary
```

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Invalid arguments
- `3`: API error
- `4`: File not found
- `5`: Network error

## Environment Variables

- `GEODES_API_KEY`: Your GEODES API key
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `OUTPUT_DIR`: Default output directory

## Tips

1. **Use quotes for multiple values**: `-i "NDVI EVI NDWI"`
2. **Dry run first**: Always test with `--dry-run`
3. **Check disk space**: Use `--dry-run` to see estimated sizes
4. **Reuse downloads**: Keep ZIPs with `--keep-zips`
5. **Config file**: Set defaults in `config.yaml`