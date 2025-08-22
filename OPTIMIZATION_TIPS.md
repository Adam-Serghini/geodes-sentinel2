# Performance Optimization Tips

## Memory Management

### For Large Batch Processing
When processing many areas or long time periods:

1. **Process areas sequentially** rather than loading all data at once
2. **Use smaller date ranges** - split annual processing into seasons
3. **Limit bands** - only process the bands you need
4. **Clean up intermediate files** periodically

### Example: Memory-Efficient Batch Processing

```python
from geodes_sentinel2 import Sentinel2Processor
import gc

processor = Sentinel2Processor(output_dir="./output")

# Process areas one at a time to minimize memory usage
areas = ["field1.geojson", "field2.geojson", "field3.geojson"]

for area in areas:
    # Process single area
    results = processor.process(
        area=area,
        max_cloud_cover=30,
        bands=['B04', 'B08'],  # Only red and NIR for NDVI
        indices=['NDVI'],
        keep_downloads=False  # Don't keep ZIPs to save space
    )
    
    # Save results immediately
    results.to_csv(f"results_{Path(area).stem}.csv", index=False)
    
    # Force garbage collection
    del results
    gc.collect()
```

## Download Optimization

### Parallel Downloads
The package automatically handles downloads efficiently, but you can optimize:

1. **Good internet connection** - Downloads are typically 500MB-1GB per product
2. **SSD storage** - Faster for extracting and processing ZIP files
3. **Keep downloads** - Reuse ZIPs for multiple processing runs

### Example: Reusing Downloads

```python
# First run - download and keep ZIPs
processor.process(
    area="field.geojson",
    keep_downloads=True,
    download_only=True  # Only download, don't process
)

# Later runs - reuse existing ZIPs
processor.process(
    area="field.geojson",
    crop_only=True,  # Skip download, use existing ZIPs
    indices=['NDVI', 'EVI', 'NDWI']  # Calculate different indices
)
```

## Processing Speed

### Tips for Faster Processing

1. **Limit search results** - Use stricter cloud cover thresholds
2. **Process specific tiles** - If you know the Sentinel-2 tile ID
3. **Use UV package manager** - Much faster than pip for dependencies
4. **SSD over HDD** - Significant speed improvement for I/O operations

### Example: Optimized Search Parameters

```python
# More selective search = faster processing
results = processor.process(
    area="field.geojson",
    max_cloud_cover=10,  # Strict cloud filter
    bands=['B02', 'B03', 'B04', 'B08'],  # Only needed bands
    indices=['NDVI'],  # Only required indices
)
```

## Disk Space Management

### Space Requirements

- **Downloads**: ~500MB-1GB per Sentinel-2 product
- **Extracted bands**: ~50-100MB per band
- **Indices**: ~10-20MB per index
- **Total**: Plan for 2-3GB per product processed

### Cleanup Strategy

```python
from pathlib import Path
import shutil

def cleanup_old_data(output_dir, keep_days=7):
    """Remove data older than specified days."""
    import time
    
    output_path = Path(output_dir)
    current_time = time.time()
    
    for subdir in ['downloads', 'crops']:
        dir_path = output_path / subdir
        if dir_path.exists():
            for file in dir_path.iterdir():
                file_age = current_time - file.stat().st_mtime
                if file_age > (keep_days * 86400):  # Convert days to seconds
                    file.unlink()
                    print(f"Removed old file: {file.name}")
```

## Network Optimization

### Handling Connection Issues

The package includes automatic retry logic, but you can optimize:

1. **Stable connection** - Avoid processing during network maintenance
2. **Off-peak hours** - Better download speeds
3. **Local caching** - Keep frequently used products

### Example: Robust Download with Custom Retry

```python
import time

def download_with_retry(processor, products, max_retries=3):
    """Download with custom retry logic."""
    for attempt in range(max_retries):
        try:
            paths = processor.download(
                products=products,
                zone_name="field",
                show_progress=True
            )
            return paths
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(60)  # Wait 1 minute before retry
            else:
                raise
```

## Batch Processing Optimization

### Efficient Multi-Area Processing

```python
# Process areas with similar dates together
summer_fields = ["wheat1.geojson", "wheat2.geojson"]
winter_fields = ["corn1.geojson", "corn2.geojson"]

# Group by season for better caching
for season_fields in [summer_fields, winter_fields]:
    results = processor.process_batch(
        areas=season_fields,
        max_cloud_cover=20,
        indices=['NDVI', 'EVI']
    )
```

## Cloud Cover Optimization

### Smart Cloud Filtering

```python
# Two-pass approach for optimal data
# First pass: Try low cloud cover
results = processor.search(
    area="field.geojson",
    start_date="2024-06-01",
    end_date="2024-08-31",
    max_cloud_cover=10
)

# If insufficient results, increase threshold
if len(results) < 5:
    results = processor.search(
        area="field.geojson",
        start_date="2024-06-01",
        end_date="2024-08-31",
        max_cloud_cover=30
    )
```