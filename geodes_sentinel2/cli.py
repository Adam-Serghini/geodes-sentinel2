"""
Command-line interface for Sentinel-2 GEODES processor.
"""

import json
import sys
from pathlib import Path

import click
import pandas as pd
from dotenv import load_dotenv

from geodes_sentinel2 import Sentinel2Processor
from geodes_sentinel2.utils import load_config, setup_package_logging

# Load environment variables
load_dotenv()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--config", "-c", type=click.Path(exists=True), help="Configuration file")
@click.pass_context
def cli(ctx, verbose, config):
    """GEODES Sentinel-2 Processor - Download and process satellite imagery."""
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_package_logging(level=log_level)

    # Load configuration
    if config:
        ctx.obj = load_config(Path(config))
    else:
        ctx.obj = load_config()


@cli.command()
@click.argument("area", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option("--cloud", "-c", default=50.0, help="Max cloud cover percentage")
@click.option("--output", "-o", default="search_results.json", help="Output file name")
@click.pass_context
def search(ctx, area, output_dir, cloud, output):
    """Search for Sentinel-2 products using dates from GeoJSON."""
    processor = Sentinel2Processor(output_dir=output_dir)

    # Load GeoJSON to get dates
    from geodes_sentinel2.core.search import GeodesSearch

    geom_data = GeodesSearch.load_geometry_from_geojson(Path(area))

    # Get dates from GeoJSON
    if "start_date" not in geom_data or "end_date" not in geom_data:
        click.echo("Error: GeoJSON must contain 'begin' and 'end' date properties", err=True)
        ctx.exit(1)

    start = geom_data["start_date"]
    end = geom_data["end_date"]

    click.echo(f"Searching for products over {area}")
    click.echo(f"Date range from GeoJSON: {start} to {end}")
    click.echo(f"Max cloud cover: {cloud}%")

    products = processor.search(
        area=Path(area),
        start_date=start,
        end_date=end,
        max_cloud_cover=cloud,
    )

    # Save results
    output_path = Path(output_dir) / output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(products, f, indent=2)

    click.echo(f"Found {len(products)} products")
    click.echo(f"Results saved to {output_path}")

    # Display summary
    if products:
        df = pd.DataFrame([p["properties"] for p in products])
        click.echo("\nSummary:")
        click.echo(
            f"  Date range: {df['start_datetime'].min()[:10]} to {df['start_datetime'].max()[:10]}"
        )
        click.echo(f"  Average cloud cover: {df['eo:cloud_cover'].mean():.1f}%")
        click.echo(f"  Platforms: {df['platform'].value_counts().to_dict()}")


@cli.command()
@click.argument("products", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option("--zone", "-z", default="zone", help="Zone name for file prefix")
@click.pass_context
def download(ctx, products, output_dir, zone):
    """Download Sentinel-2 products from search results."""
    processor = Sentinel2Processor(output_dir=output_dir)

    # Load products
    with open(products) as f:
        product_list = json.load(f)

    if not isinstance(product_list, list):
        # If it's a STAC response, extract features
        product_list = product_list.get("features", [])

    click.echo(f"Downloading {len(product_list)} products")

    paths = processor.download(products=product_list, zone_name=zone, show_progress=True)

    click.echo(f"Downloaded {len(paths)} products to {output_dir}")


@cli.command()
@click.argument("zips", type=click.Path(exists=True))
@click.argument("area", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option("--zone", "-z", default="zone", help="Zone name for file prefix")
@click.option(
    "--bands",
    "-b",
    default="",
    help='Specific bands to crop (space-separated, e.g., "B02 B03 B04 B08")',
)
@click.pass_context
def crop(ctx, zips, area, output_dir, zone, bands):
    """Crop bands from downloaded ZIP files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    processor = Sentinel2Processor(output_dir=output_path)

    # Get ZIP files
    zips_path = Path(zips)
    if zips_path.is_dir():
        zip_files = list(zips_path.glob("*.zip"))
    else:
        # Assume it's a text file with paths
        with open(zips_path) as f:
            zip_files = [Path(line.strip()) for line in f]

    click.echo(f"Processing {len(zip_files)} ZIP files")

    # Parse bands
    bands_list = bands.split() if bands else None

    results = processor.crop(
        zip_paths=zip_files, geometry=Path(area), zone_name=zone, bands=bands_list
    )

    total_cropped = sum(len(files) for files in results.values())
    click.echo(f"Cropped {total_cropped} band files to {output_dir}")


@cli.command()
@click.argument("crops", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option(
    "--indices",
    "-i",
    default="NDVI EVI NDWI",
    help='Indices to calculate (space-separated, default: "NDVI EVI NDWI")',
)
@click.pass_context
def indices(ctx, crops, output_dir, indices):
    """Calculate vegetation indices from cropped bands."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    processor = Sentinel2Processor(output_dir=output_path)

    crops_dir = Path(crops)

    # Parse indices
    indices_list = indices.split() if indices else ["NDVI", "EVI", "NDWI"]

    click.echo(f"Calculating indices: {', '.join(indices_list)}")

    results = processor.calculate_indices(crop_dir=crops_dir, indices=indices_list)

    for idx, paths in results.items():
        if paths:
            click.echo(f"  {idx}: {len(paths)} files generated")

    click.echo(f"Indices saved to {output_dir}")


@cli.command()
@click.argument("area", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option("--cloud", "-c", type=float, help="Max cloud cover percentage (default from config)")
@click.option(
    "--bands",
    "-b",
    default="",
    help='Specific bands to process (space-separated, e.g., "B02 B03 B04 B08")',
)
@click.option(
    "--indices",
    "-i",
    "indices_str",
    default="",
    help='Indices to calculate (use quotes for multiple, e.g., -i "NDVI EVI NDWI")',
)
@click.option(
    "--keep-zips/--no-keep-zips",
    default=None,
    help="Keep downloaded ZIP files (default from config)",
)
@click.option("--csv", help="Save results to CSV file")
@click.option("--dry-run", is_flag=True, help="Show what would be done without actually doing it")
@click.pass_context
def process(ctx, area, output_dir, cloud, bands, indices_str, keep_zips, csv, dry_run):
    """Complete processing workflow: search, download, crop, and calculate indices."""
    # Load config if available
    config = ctx.obj if ctx.obj else {}

    # Use config defaults if not specified
    if cloud is None and config and hasattr(config, "defaults"):
        cloud = config.defaults.max_cloud_cover
    elif cloud is None:
        cloud = 30.0  # Default fallback

    if keep_zips is None and config and hasattr(config, "defaults"):
        keep_zips = config.defaults.keep_downloads
    elif keep_zips is None:
        keep_zips = True  # Default fallback

    processor = Sentinel2Processor(output_dir=output_dir, config=config if config else None)

    click.echo("=" * 60)
    click.echo("Sentinel-2 Processing Pipeline" + (" [DRY RUN]" if dry_run else ""))
    click.echo("=" * 60)

    # Parse bands - use config defaults if not specified
    if bands:
        bands_list = bands.split()
    elif config and hasattr(config, "defaults") and config.defaults.bands:
        bands_list = config.defaults.bands
        click.echo(f"Using default bands from config: {', '.join(bands_list)}")
    else:
        bands_list = None

    # Parse indices - use config defaults if not specified
    if indices_str:
        indices_list = indices_str.split()
    elif config and hasattr(config, "defaults") and config.defaults.indices:
        indices_list = config.defaults.indices
        click.echo(f"Using default indices from config: {', '.join(indices_list)}")
    else:
        indices_list = None

    # Run processing (will always use GeoJSON dates)
    results = processor.process(
        area=Path(area),
        max_cloud_cover=cloud,
        bands=bands_list,
        indices=indices_list,
        keep_downloads=keep_zips,
        output_csv=csv,
        dry_run=dry_run,
    )

    if not results.empty:
        click.echo("\n" + "=" * 60)
        click.echo("Processing Complete!")
        click.echo("=" * 60)

        # Display results table
        display_cols = ["date", "platform", "cloud_cover", "bands_cropped"]
        if "indices_calculated" in results.columns:
            display_cols.append("indices_calculated")

        click.echo("\nResults:")
        click.echo(results[display_cols].to_string())

        # Display output locations
        click.echo("\nOutput locations:")
        click.echo(f"  Downloads: {processor.downloads_dir}")
        click.echo(f"  Crops: {processor.crops_dir}")
        if indices:
            click.echo(f"  Indices: {processor.indices_dir}")
        if csv:
            click.echo(f"  CSV: {csv}")

        if keep_zips:
            click.echo(f"\n✓ ZIP files preserved in {processor.downloads_dir}")
    else:
        click.echo("No products found matching criteria")


@cli.command()
@click.argument("areas", nargs=-1, required=True, type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option("--cloud", "-c", default=50.0, help="Max cloud cover percentage")
@click.option(
    "--indices", "-i", default="", help='Indices to calculate (space-separated, e.g., "NDVI EVI")'
)
@click.option("--csv", default="batch_results.csv", help="Results CSV file")
@click.pass_context
def batch(ctx, areas, output_dir, cloud, indices, csv):
    """Process multiple areas in batch mode using dates from each GeoJSON."""
    processor = Sentinel2Processor(output_dir=output_dir)

    areas_list = list(areas)  # Convert tuple to list, keep as is for typing
    click.echo(f"Processing {len(areas_list)} areas in batch mode")
    click.echo("Each area will use its own dates from GeoJSON properties")

    # Parse indices
    indices_list = indices.split() if indices else None

    # Use the process_batch method
    try:
        combined_df = processor.process_batch(
            areas=areas_list,  # type: ignore[arg-type]
            max_cloud_cover=cloud,
            indices=indices_list,
            keep_downloads=True,
            output_csv=None,  # We'll save the combined CSV at the end
        )

        if not combined_df.empty:
            # Save combined results
            csv_path = Path(output_dir) / csv
            combined_df.to_csv(csv_path, index=False)

            click.echo(f"\n{'='*60}")
            click.echo("Batch Processing Complete!")
            click.echo(f"Total products processed: {len(combined_df)}")
            click.echo(f"Results saved to: {csv_path}")

            # Show summary by area
            click.echo("\nSummary by area:")
            for zone in combined_df["zone_name"].unique():
                zone_df = combined_df[combined_df["zone_name"] == zone]
                click.echo(f"  {zone}: {len(zone_df)} products")
        else:
            click.echo("No products found for any area", err=True)

    except Exception as e:
        click.echo(f"Batch processing failed: {e}", err=True)
        ctx.exit(1)


@cli.command()
def info():
    """Display information about the processor."""
    from geodes_sentinel2 import __version__
    from geodes_sentinel2.processing.band_math import BandMath

    click.echo(f"GEODES Sentinel-2 Processor v{__version__}")
    click.echo("\nSupported bands:")
    for band, info in BandMath.BAND_INFO.items():
        click.echo(f"  {band}: {info['name']} ({info['wavelength']}nm, {info['resolution']}m)")

    click.echo("\nSupported indices:")
    indices = [
        ("NDVI", "Normalized Difference Vegetation Index"),
        ("EVI", "Enhanced Vegetation Index"),
        ("NDWI", "Normalized Difference Water Index"),
        ("SAVI", "Soil Adjusted Vegetation Index"),
        ("GNDVI", "Green NDVI"),
        ("NDRE", "Normalized Difference Red Edge"),
    ]
    for idx, desc in indices:
        click.echo(f"  {idx}: {desc}")

    click.echo("\nConfiguration:")
    click.echo("  Set GEODES_API_KEY environment variable or use .env file")
    click.echo("  Optional: Create config.yaml for advanced settings")


def main():
    """Main entry point for CLI."""
    try:
        cli(obj={})
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
