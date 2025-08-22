"""
Basic usage example for Sentinel-2 GEODES processor.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from geodes_sentinel2 import Sentinel2Processor
from geodes_sentinel2.utils import setup_package_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_package_logging(level="INFO")


def main():
    """Run basic processing workflow."""
    
    # Initialize processor (API key from environment)
    processor = Sentinel2Processor(
        output_dir="./output_example"
    )
    
    # Define parameters
    area_file = Path("examples/data/sample_area.geojson")
    start_date = "2024-03-01"
    end_date = "2024-03-31"
    
    # Run complete workflow with vegetation indices
    print("Starting Sentinel-2 processing with vegetation indices...")
    
    results = processor.process(
        area=area_file,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=30,
        max_products=2,  # Limit to 2 for demo
        bands=["B02", "B03", "B04", "B08"],  # RGB + NIR for indices
        indices=["NDVI", "EVI", "NDWI"],  # Calculate vegetation indices
        keep_downloads=True,  # Keep ZIP files for future use
        output_csv="results.csv"
    )
    
    # Display results
    if not results.empty:
        print("\nProcessing complete!")
        print(f"Processed {len(results)} products")
        print("\nResults summary:")
        display_cols = ['date', 'platform', 'cloud_cover', 'bands_cropped', 'indices_calculated']
        print(results[display_cols])
        
        # Show file locations
        print("\nOutput files:")
        print(f"  - Downloads: {processor.downloads_dir}")
        print(f"  - Cropped bands: {processor.crops_dir}")
        print(f"  - Vegetation indices: {processor.indices_dir}")
        print(f"  - Results CSV: results.csv")
        
        if results['zip_preserved'].any():
            print(f"\n✓ ZIP files preserved for future processing")
    else:
        print("No products found for the specified criteria")


def advanced_example():
    """Show advanced usage with separate steps."""
    
    processor = Sentinel2Processor()
    
    # Step 1: Search only
    print("Step 1: Searching for products...")
    products = processor.search(
        area="examples/data/sample_area.geojson",
        start_date="2024-03-01",
        end_date="2024-03-31",
        max_cloud_cover=30
    )
    print(f"Found {len(products)} products")
    
    # Step 2: Download specific products
    if products:
        print("\nStep 2: Downloading products...")
        zip_paths = processor.download(
            products[:2],  # Download first 2
            zone_name="sample",
            show_progress=True
        )
        print(f"Downloaded {len(zip_paths)} products")
        
        # Step 3: Crop specific bands
        print("\nStep 3: Cropping bands...")
        crop_results = processor.crop(
            zip_paths,
            geometry="examples/data/sample_area.geojson",
            bands=["B02", "B03", "B04", "B08"]  # Only bands needed for indices
        )
        
        # Step 4: Calculate indices
        print("\nStep 4: Calculating vegetation indices...")
        index_results = processor.calculate_indices(
            indices=["NDVI", "EVI", "NDWI", "SAVI"]
        )
        
        for idx, paths in index_results.items():
            print(f"  {idx}: {len(paths)} files created")


if __name__ == "__main__":
    # Run basic example
    main()
    
    # Uncomment to run advanced example
    # print("\n" + "="*60)
    # print("ADVANCED EXAMPLE")
    # print("="*60)
    # advanced_example()