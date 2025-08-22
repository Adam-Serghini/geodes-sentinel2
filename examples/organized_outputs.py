"""
Example showing organized output directory structure for different projects.

This demonstrates how to organize outputs for multiple fields or time periods
using custom output directories.
"""

from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from geodes_sentinel2 import Sentinel2Processor
from geodes_sentinel2.utils import setup_package_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_package_logging(level="INFO")


def process_seasonal_monitoring():
    """
    Organize outputs by season for crop monitoring.
    """
    base_dir = Path("seasonal_monitoring_2024")
    
    # Define seasons
    seasons = {
        "spring": ("2024-03-01", "2024-05-31"),
        "summer": ("2024-06-01", "2024-08-31"),
        "autumn": ("2024-09-01", "2024-11-30"),
    }
    
    for season_name, (start_date, end_date) in seasons.items():
        print(f"\n{'='*60}")
        print(f"Processing {season_name.upper()} season")
        print('='*60)
        
        # Create season-specific output directory
        season_dir = base_dir / season_name
        
        processor = Sentinel2Processor(output_dir=season_dir)
        
        results = processor.process(
            area="examples/data/sample_area.geojson",
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=20,
            max_products=3,
            indices=["NDVI", "EVI"],
            keep_downloads=True,
            output_csv=season_dir / f"{season_name}_results.csv"
        )
        
        print(f"✓ {season_name.capitalize()} processing complete")
        print(f"  Output directory: {season_dir}")
        print(f"  Products processed: {len(results)}")


def process_multiple_fields():
    """
    Organize outputs by field for multi-field management.
    """
    base_dir = Path("multi_field_analysis")
    
    # Simulate multiple field files
    fields = {
        "field_north": "examples/data/sample_area.geojson",
        "field_south": "examples/data/sample_area.geojson",  # Use same file for demo
        "field_east": "examples/data/sample_area.geojson",
    }
    
    analysis_date = "2024-05-15"
    
    for field_name, field_file in fields.items():
        print(f"\n{'='*60}")
        print(f"Processing {field_name}")
        print('='*60)
        
        # Create field-specific output directory
        field_dir = base_dir / field_name / analysis_date.replace('-', '_')
        
        processor = Sentinel2Processor(output_dir=field_dir)
        
        results = processor.process(
            area=field_file,
            start_date=analysis_date,
            end_date=analysis_date,
            max_cloud_cover=15,
            max_products=1,
            indices=["NDVI", "EVI", "NDWI"],
            keep_downloads=True,
            output_csv=field_dir / "analysis.csv"
        )
        
        print(f"✓ {field_name} processing complete")
        print(f"  Output directory: {field_dir}")


def process_with_timestamps():
    """
    Organize outputs with timestamp for versioning.
    """
    # Create timestamped directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"processing_runs/run_{timestamp}")
    
    print(f"\n{'='*60}")
    print(f"Processing with timestamp: {timestamp}")
    print('='*60)
    
    processor = Sentinel2Processor(output_dir=output_dir)
    
    results = processor.process(
        area="examples/data/sample_area.geojson",
        start_date="2024-05-01",
        end_date="2024-05-31",
        max_cloud_cover=25,
        max_products=2,
        indices=["NDVI"],
        keep_downloads=True,
        output_csv=output_dir / "results.csv"
    )
    
    # Create a summary file
    summary_file = output_dir / "processing_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Processing Summary\n")
        f.write(f"==================\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Products processed: {len(results)}\n")
        f.write(f"Date range: {results['date'].min()} to {results['date'].max()}\n")
        f.write(f"Output directory: {output_dir}\n")
    
    print(f"✓ Processing complete")
    print(f"  Output directory: {output_dir}")
    print(f"  Summary saved to: {summary_file}")


def process_by_tile():
    """
    Organize outputs by Sentinel-2 tile for large area monitoring.
    """
    base_dir = Path("tile_based_processing")
    
    # First, search to identify available tiles
    processor = Sentinel2Processor()
    
    products = processor.search(
        area="examples/data/sample_area.geojson",
        start_date="2024-05-01",
        end_date="2024-05-31",
        max_cloud_cover=30
    )
    
    # Group products by tile
    tiles = {}
    for product in products:
        tile = product['properties'].get('grid:code', 'unknown')
        if tile not in tiles:
            tiles[tile] = []
        tiles[tile].append(product)
    
    print(f"\n{'='*60}")
    print(f"Found {len(tiles)} tiles to process")
    print('='*60)
    
    # Process each tile separately
    for tile_name, tile_products in tiles.items():
        print(f"\nProcessing tile: {tile_name}")
        
        tile_dir = base_dir / f"tile_{tile_name}"
        processor = Sentinel2Processor(output_dir=tile_dir)
        
        # Download and process products for this tile
        paths = processor.download(
            products=tile_products[:2],  # Limit for demo
            zone_name=tile_name
        )
        
        if paths:
            crop_results = processor.crop(
                zip_paths=paths,
                geometry="examples/data/sample_area.geojson",
                zone_name=tile_name,
                bands=["B04", "B08"]  # Just Red and NIR for NDVI
            )
            
            index_results = processor.calculate_indices(
                crop_dir=tile_dir / "crops",
                indices=["NDVI"]
            )
            
            print(f"  ✓ Tile {tile_name} complete")
            print(f"    Output: {tile_dir}")


if __name__ == "__main__":
    print("ORGANIZED OUTPUT EXAMPLES")
    print("=" * 60)
    
    # Example 1: Seasonal monitoring
    print("\n1. Seasonal Monitoring")
    print("-" * 40)
    print("Organizing outputs by season...")
    # Uncomment to run:
    # process_seasonal_monitoring()
    
    # Example 2: Multiple fields
    print("\n2. Multi-Field Processing")
    print("-" * 40)
    print("Organizing outputs by field...")
    # Uncomment to run:
    # process_multiple_fields()
    
    # Example 3: Timestamped runs
    print("\n3. Timestamped Processing")
    print("-" * 40)
    print("Creating timestamped output directory...")
    # Uncomment to run:
    # process_with_timestamps()
    
    # Example 4: Tile-based processing
    print("\n4. Tile-Based Processing")
    print("-" * 40)
    print("Organizing by Sentinel-2 tile...")
    # Uncomment to run:
    # process_by_tile()
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("\nOutput directory structures created:")
    print("  - seasonal_monitoring_2024/[spring|summer|autumn]/")
    print("  - multi_field_analysis/[field_name]/[date]/")
    print("  - processing_runs/run_[timestamp]/")
    print("  - tile_based_processing/tile_[code]/")
    print("\nUse these patterns to organize your own processing workflows!")