"""
Vegetation monitoring example using Sentinel-2 data and vegetation indices.

This example shows how to:
1. Download time series data for a field
2. Calculate multiple vegetation indices
3. Track vegetation changes over time
"""

import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from dotenv import load_dotenv

from geodes_sentinel2 import Sentinel2Processor
from geodes_sentinel2.processing import BandMath
from geodes_sentinel2.utils import setup_package_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_package_logging(level="INFO")


def monitor_vegetation_growth(
    area_file: Path,
    start_date: str,
    end_date: str,
    output_dir: str = "./vegetation_monitoring"
):
    """
    Monitor vegetation growth over a time period.
    
    Args:
        area_file: Path to field boundary GeoJSON
        start_date: Start of monitoring period
        end_date: End of monitoring period
        output_dir: Output directory
    """
    print("="*60)
    print("VEGETATION MONITORING SYSTEM")
    print("="*60)
    
    # Initialize processor
    processor = Sentinel2Processor(output_dir=output_dir)
    
    # Process time series with all vegetation indices
    print(f"\nMonitoring period: {start_date} to {end_date}")
    print(f"Field: {area_file.name}")
    
    results = processor.process(
        area=area_file,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=20,  # Lower cloud cover for better quality
        bands=None,  # Get all bands for comprehensive analysis
        indices=["NDVI", "EVI", "NDWI", "SAVI", "GNDVI"],  # Multiple indices
        keep_downloads=True,  # Keep for potential reprocessing
        output_csv=f"{output_dir}/monitoring_results.csv"
    )
    
    if results.empty:
        print("No suitable imagery found for monitoring period")
        return None
    
    # Analyze vegetation trends
    print("\n" + "="*60)
    print("VEGETATION ANALYSIS")
    print("="*60)
    
    # Sort by date
    results = results.sort_values('date')
    
    # Display time series
    print(f"\nTime series data ({len(results)} observations):")
    for _, row in results.iterrows():
        print(f"  {row['date']}: Platform={row['platform']}, "
              f"Cloud={row['cloud_cover']:.1f}%, "
              f"Indices={row['indices_calculated']}")
    
    # Calculate statistics for each index
    print("\nVegetation Index Statistics:")
    print("-" * 40)
    
    # Get actual NDVI values (this is simplified - in reality you'd read the rasters)
    # For demonstration, we'll show the structure
    indices_dir = Path(output_dir) / "indices"
    
    for index_type in ["NDVI", "EVI", "NDWI"]:
        index_files = list(indices_dir.glob(f"{index_type.lower()}_*.tif"))
        if index_files:
            print(f"\n{index_type}:")
            print(f"  Files generated: {len(index_files)}")
            print(f"  Time points: {', '.join([f.stem.split('_')[-1] for f in index_files])}")
    
    return results


def analyze_crop_health(
    area_file: Path,
    date: str,
    output_dir: str = "./crop_health"
):
    """
    Detailed crop health analysis for a specific date.
    
    Args:
        area_file: Path to field boundary GeoJSON
        date: Specific date for analysis
        output_dir: Output directory
    """
    print("="*60)
    print("CROP HEALTH ANALYSIS")
    print("="*60)
    
    processor = Sentinel2Processor(output_dir=output_dir)
    
    # Search for imagery around the date
    products = processor.search(
        area=area_file,
        start_date=date,
        end_date=date,
        max_cloud_cover=10  # Very low cloud for accurate analysis
    )
    
    if not products:
        print(f"No imagery found for {date}")
        # Try expanding date range
        from datetime import datetime, timedelta
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        start = (date_obj - timedelta(days=3)).strftime("%Y-%m-%d")
        end = (date_obj + timedelta(days=3)).strftime("%Y-%m-%d")
        
        print(f"Expanding search to {start} - {end}")
        products = processor.search(
            area=area_file,
            start_date=start,
            end_date=end,
            max_cloud_cover=15
        )
    
    if products:
        print(f"Found {len(products)} suitable images")
        
        # Process the best image
        best_product = min(products, key=lambda p: p['properties'].get('eo:cloud_cover', 100))
        print(f"Using image from {best_product['properties']['start_datetime'][:10]} "
              f"with {best_product['properties'].get('eo:cloud_cover', 0):.1f}% cloud cover")
        
        # Download and process
        results = processor.process(
            area=area_file,
            start_date=best_product['properties']['start_datetime'][:10],
            end_date=best_product['properties']['start_datetime'][:10],
            max_products=1,
            indices=["NDVI", "EVI", "NDWI", "SAVI", "GNDVI", "NDRE"],
            keep_downloads=True,
            output_csv=f"{output_dir}/health_analysis.csv"
        )
        
        # Health interpretation
        print("\n" + "="*60)
        print("HEALTH INDICATORS")
        print("="*60)
        
        print("\nIndex Interpretation Guide:")
        print("-" * 40)
        print("NDVI (Vegetation Density):")
        print("  < 0.1: Bare soil or dead plants")
        print("  0.2-0.4: Sparse or stressed vegetation")
        print("  0.4-0.6: Moderate healthy vegetation")
        print("  > 0.6: Dense healthy vegetation")
        
        print("\nEVI (Enhanced Vegetation):")
        print("  More sensitive in high biomass regions")
        print("  Better for dense canopy monitoring")
        
        print("\nNDWI (Water Content):")
        print("  < 0: Low water content/drought stress")
        print("  > 0: Adequate water content")
        
        print("\nSAVI (Soil Adjusted):")
        print("  Minimizes soil brightness influence")
        print("  Better for sparse vegetation")
        
        return results
    else:
        print("No suitable imagery found")
        return None


def compare_fields(
    field_files: list,
    date: str,
    output_dir: str = "./field_comparison"
):
    """
    Compare vegetation indices across multiple fields.
    
    Args:
        field_files: List of GeoJSON files for different fields
        date: Date for comparison
        output_dir: Output directory
    """
    print("="*60)
    print("MULTI-FIELD COMPARISON")
    print("="*60)
    
    processor = Sentinel2Processor(output_dir=output_dir)
    
    comparison_results = []
    
    for field_file in field_files:
        field_path = Path(field_file)
        print(f"\nProcessing field: {field_path.stem}")
        
        results = processor.process(
            area=field_path,
            start_date=date,
            end_date=date,
            max_cloud_cover=20,
            max_products=1,
            bands=["B02", "B03", "B04", "B08"],  # Minimum for indices
            indices=["NDVI", "EVI"],
            keep_downloads=True
        )
        
        if not results.empty:
            results['field'] = field_path.stem
            comparison_results.append(results)
    
    if comparison_results:
        # Combine results
        comparison_df = pd.concat(comparison_results, ignore_index=True)
        comparison_df.to_csv(f"{output_dir}/field_comparison.csv", index=False)
        
        print("\n" + "="*60)
        print("COMPARISON RESULTS")
        print("="*60)
        
        print("\nField Summary:")
        for _, row in comparison_df.iterrows():
            print(f"  {row['field']}: Date={row['date']}, "
                  f"Cloud={row['cloud_cover']:.1f}%, "
                  f"Indices={row['indices_calculated']}")
        
        return comparison_df
    else:
        print("No data available for comparison")
        return None


if __name__ == "__main__":
    # Example 1: Monitor vegetation growth over a season
    print("Example 1: Seasonal Vegetation Monitoring")
    print("-" * 40)
    
    monitoring_results = monitor_vegetation_growth(
        area_file=Path("examples/data/sample_area.geojson"),
        start_date="2024-03-01",
        end_date="2024-06-30",
        output_dir="./monitoring_output"
    )
    
    # Example 2: Detailed crop health analysis
    print("\n\nExample 2: Crop Health Analysis")
    print("-" * 40)
    
    health_results = analyze_crop_health(
        area_file=Path("examples/data/sample_area.geojson"),
        date="2024-05-15",
        output_dir="./health_output"
    )
    
    # Example 3: Compare multiple fields (if you have multiple GeoJSON files)
    # print("\n\nExample 3: Multi-Field Comparison")
    # print("-" * 40)
    # 
    # comparison = compare_fields(
    #     field_files=[
    #         "field1.geojson",
    #         "field2.geojson",
    #         "field3.geojson"
    #     ],
    #     date="2024-05-15",
    #     output_dir="./comparison_output"
    # )