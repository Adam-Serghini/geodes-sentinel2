#!/bin/bash

# Batch Processing Example using CLI
# This example shows how to process multiple agricultural fields in batch mode

echo "========================================"
echo "Batch Processing with CLI"
echo "========================================"

# 1. Create multiple GeoJSON files with different dates
echo "Creating sample GeoJSON files..."

# Field 1: Summer wheat monitoring
cat > field1_wheat.geojson << 'EOF'
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "properties": {
      "Name": "WheatField_North",
      "begin": "2024-06-01T00:00:00Z",
      "end": "2024-08-31T00:00:00Z",
      "crop": "wheat"
    },
    "geometry": {
      "type": "Polygon",
      "coordinates": [[
        [22.7724, 5.9666],
        [22.7751, 5.9675],
        [22.7777, 5.9643],
        [22.7750, 5.9633],
        [22.7724, 5.9666]
      ]]
    }
  }]
}
EOF

# Field 2: Spring corn monitoring
cat > field2_corn.geojson << 'EOF'
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "properties": {
      "Name": "CornField_South",
      "begin": "2024-03-01T00:00:00Z",
      "end": "2024-05-31T00:00:00Z",
      "crop": "corn"
    },
    "geometry": {
      "type": "Polygon",
      "coordinates": [[
        [23.7800, 4.9600],
        [23.7850, 4.9610],
        [23.7860, 4.9580],
        [23.7810, 4.9570],
        [23.7800, 4.9600]
      ]]
    }
  }]
}
EOF

# Field 3: Vineyard annual monitoring
cat > field3_vineyard.geojson << 'EOF'
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "properties": {
      "Name": "VineyardWest",
      "begin": "2024-01-01T00:00:00Z",
      "end": "2024-12-31T00:00:00Z",
      "crop": "vineyard"
    },
    "geometry": {
      "type": "Polygon",
      "coordinates": [[
        [24.7900, 3.9550],
        [24.7920, 3.9560],
        [24.7940, 3.9540],
        [24.7920, 3.9530],
        [24.7900, 3.9550]
      ]]
    }
  }]
}
EOF

echo "Created 3 GeoJSON files with different date ranges"

# 2. Run batch processing
echo ""
echo "Running batch processing for all fields..."
echo "Each field will use its own dates from GeoJSON properties"
echo ""

geodes-sentinel2 batch \
    field1_wheat.geojson \
    field2_corn.geojson \
    field3_vineyard.geojson \
    ./batch_output \
    --cloud 30 \
    --indices NDVI EVI NDWI \
    --csv batch_results.csv

echo ""
echo "========================================"
echo "Batch processing complete!"
echo "========================================"
echo ""
echo "Output structure:"
echo "batch_output/"
echo "├── downloads/        # ZIP files for all areas"
echo "├── crops/           # Cropped bands for all areas"
echo "├── indices/         # NDVI, EVI, NDWI for all areas"
echo "└── batch_results.csv # Combined results for all fields"
echo ""
echo "Each field was processed with its own date range:"
echo "- WheatField_North: June-August 2024 (summer growing season)"
echo "- CornField_South: March-May 2024 (spring planting season)"
echo "- VineyardWest: Full year 2024 (annual monitoring)"