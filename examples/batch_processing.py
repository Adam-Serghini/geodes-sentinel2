"""
Example: Batch Processing Multiple Areas

This example shows how to process multiple agricultural fields or areas
in a single batch operation. Each area can have its own date range
specified in its GeoJSON properties.
"""

import json
from pathlib import Path
from geodes_sentinel2 import Sentinel2Processor

# Create example GeoJSON files with different areas and dates
def create_sample_geojsons():
    """Create sample GeoJSON files for demonstration."""
    
    # Field 1: Summer monitoring
    field1 = {
        "type": "FeatureCollection",
        "name": "Field1_Summer",
        "features": [{
            "type": "Feature",
            "properties": {
                "Name": "WheatField_North",
                "begin": "2024-06-01T00:00:00Z",
                "end": "2024-08-31T00:00:00Z",
                "crop": "wheat",
                "area_ha": 25.5
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
    
    # Field 2: Spring monitoring
    field2 = {
        "type": "FeatureCollection",
        "name": "Field2_Spring",
        "features": [{
            "type": "Feature",
            "properties": {
                "Name": "CornField_South",
                "begin": "2024-03-01T00:00:00Z",
                "end": "2024-05-31T00:00:00Z",
                "crop": "corn",
                "area_ha": 18.3
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
    
    # Field 3: Full year monitoring
    field3 = {
        "type": "FeatureCollection",
        "name": "Field3_Annual",
        "features": [{
            "type": "Feature",
            "properties": {
                "Name": "VineyardWest",
                "begin": "2024-01-01T00:00:00Z",
                "end": "2024-12-31T00:00:00Z",
                "crop": "vineyard",
                "area_ha": 12.7
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
    
    # Save GeoJSON files
    fields = [
        ("field1_wheat.geojson", field1),
        ("field2_corn.geojson", field2),
        ("field3_vineyard.geojson", field3)
    ]
    
    paths = []
    for filename, data in fields:
        path = Path(f"./data/{filename}")
        path.parent.mkdir(exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        paths.append(path)
        print(f"Created: {path}")
    
    return paths


def main():
    """Run batch processing example."""
    
    print("="*60)
    print("Batch Processing Example")
    print("="*60)
    
    # Create sample GeoJSON files
    print("\n1. Creating sample GeoJSON files...")
    geojson_paths = create_sample_geojsons()
    
    # Initialize processor
    print("\n2. Initializing processor...")
    processor = Sentinel2Processor(output_dir="./batch_output")
    
    # Process all areas in batch
    print("\n3. Processing multiple areas in batch mode...")
    print("   Each area will use its own date range from GeoJSON properties")
    
    try:
        results_df = processor.process_batch(
            areas=geojson_paths,
            max_cloud_cover=30,
            indices=['NDVI', 'EVI'],
            keep_downloads=True
        )
        
        # Save results
        output_csv = "./batch_output/batch_results.csv"
        results_df.to_csv(output_csv, index=False)
        
        print(f"\n4. Results saved to: {output_csv}")
        
        # Display summary
        print("\n5. Processing Summary:")
        print("-" * 40)
        
        for zone in results_df['zone_name'].unique():
            zone_df = results_df[results_df['zone_name'] == zone]
            if not zone_df.empty:
                print(f"\n{zone}:")
                print(f"  - Products found: {len(zone_df)}")
                print(f"  - Date range: {zone_df['date'].min()} to {zone_df['date'].max()}")
                print(f"  - Avg cloud cover: {zone_df['cloud_cover'].mean():.1f}%")
                
                # Get crop type from first product (stored during search)
                first_product = zone_df.iloc[0]
                if 'search_zone' in first_product:
                    print(f"  - Field name: {first_product['search_zone']}")
        
        print("\n" + "="*60)
        print("Batch processing complete!")
        print(f"Total products processed: {len(results_df)}")
        
        # Show file organization
        print("\nOutput structure:")
        print("batch_output/")
        print("├── downloads/        # ZIP files for all areas")
        print("├── crops/           # Cropped bands for all areas")
        print("├── indices/         # NDVI, EVI for all areas")
        print("└── batch_results.csv # Combined results")
        
    except Exception as e:
        print(f"\nError during batch processing: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())