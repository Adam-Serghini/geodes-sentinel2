"""
Main processor for Sentinel-2 data workflow.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

from geodes_sentinel2.core.downloader import GeodesDownloader
from geodes_sentinel2.core.search import GeodesSearch
from geodes_sentinel2.processing.band_math import BandMath
from geodes_sentinel2.processing.cropper import RasterCropper

logger = logging.getLogger(__name__)


class Sentinel2Processor:
    """Main processor for complete Sentinel-2 workflow."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        output_dir: Optional[Union[str, Path]] = None,
        config: Optional[Dict] = None,
    ):
        """
        Initialize the processor.

        Args:
            api_key: GEODES API key (can be set via environment variable)
            output_dir: Base output directory (required for most operations)
            config: Optional configuration dictionary
        """
        # Get API key from environment if not provided
        if api_key is None:
            import os

            api_key = os.getenv("GEODES_API_KEY")
            if not api_key:
                raise ValueError(
                    "API key must be provided or set in GEODES_API_KEY environment variable"
                )

        self.api_key = api_key

        # Handle output directory
        if output_dir is None:
            # Default to current directory for backward compatibility
            self.output_dir = Path("./output")
            logger.warning("No output directory specified, using default: ./output")
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.downloads_dir = self.output_dir / "downloads"
        self.crops_dir = self.output_dir / "crops"
        self.indices_dir = self.output_dir / "indices"
        self.downloads_dir.mkdir(exist_ok=True)
        self.crops_dir.mkdir(exist_ok=True)
        self.indices_dir.mkdir(exist_ok=True)

        # Initialize components
        self.searcher = GeodesSearch(api_key)
        self.downloader = GeodesDownloader(api_key, self.downloads_dir)
        self.cropper = RasterCropper(self.crops_dir)
        self.band_math = BandMath(self.indices_dir)

        # Store configuration
        self.config = config or {}

        logger.info(f"Initialized processor with output directory: {self.output_dir}")

    def search(
        self,
        area: Union[str, Path, Dict],
        start_date: str,
        end_date: str,
        max_cloud_cover: float = 50.0,
    ) -> List[Dict]:
        """
        Search for Sentinel-2 products.

        Args:
            area: GeoJSON file path or geometry dict
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            max_cloud_cover: Maximum cloud cover percentage

        Returns:
            List of found products
        """
        if isinstance(area, (str, Path)):
            # Load from file
            products = self.searcher.search_by_geometry(
                Path(area), start_date, end_date, max_cloud_cover
            )
        else:
            # Use provided geometry
            bbox = self.searcher.geometry_to_bbox(area)
            from geodes_sentinel2.core.search import SearchParameters

            params = SearchParameters(
                bbox=bbox, start_date=start_date, end_date=end_date, max_cloud_cover=max_cloud_cover
            )
            products = self.searcher.search(params)

        logger.info(f"Found {len(products)} products")
        return products

    def download(
        self, products: List[Dict], zone_name: str = "zone", show_progress: bool = True
    ) -> List[Path]:
        """
        Download Sentinel-2 products.

        Args:
            products: List of products to download
            zone_name: Name prefix for files
            max_downloads: Maximum number of downloads
            show_progress: Show progress bar

        Returns:
            List of downloaded file paths
        """
        paths = self.downloader.download_multiple(products, zone_name, show_progress)

        logger.info(f"Downloaded {len(paths)} products to {self.downloads_dir}")
        return paths

    def crop(
        self,
        zip_paths: List[Path],
        geometry: Union[str, Path, Dict],
        zone_name: str = "zone",
        bands: Optional[List[str]] = None,
    ) -> Dict[str, List[Path]]:
        """
        Crop bands from downloaded ZIPs.

        Args:
            zip_paths: List of ZIP file paths
            geometry: GeoJSON file path or geometry dict
            zone_name: Name prefix for output files
            bands: Specific bands to process (None = all)

        Returns:
            Dictionary mapping ZIP names to cropped files
        """
        # Load geometry if it's a file path
        if isinstance(geometry, (str, Path)):
            geom_data = self.searcher.load_geometry_from_geojson(Path(geometry))
            geometry = geom_data["geometry"]
            if not zone_name or zone_name == "zone":
                zone_name = geom_data["name"]

        results = self.cropper.process_multiple_zips(zip_paths, geometry, zone_name, bands)

        total_cropped = sum(len(files) for files in results.values())
        logger.info(f"Cropped {total_cropped} band files to {self.crops_dir}")

        return results

    def calculate_indices(
        self, crop_dir: Optional[Path] = None, indices: Optional[List[str]] = None
    ) -> Dict[str, List[Path]]:
        """
        Calculate vegetation indices from cropped bands.

        Args:
            crop_dir: Directory containing cropped bands (default: self.crops_dir)
            indices: List of indices to calculate (default: NDVI, EVI, NDWI)

        Returns:
            Dictionary mapping index names to output paths
        """
        if crop_dir is None:
            crop_dir = self.crops_dir

        if indices is None:
            indices = ["NDVI", "EVI", "NDWI"]

        results = self.band_math.process_all_indices(crop_dir, indices)

        total_indices = sum(len(paths) for paths in results.values())
        logger.info(f"Calculated {total_indices} indices in {self.indices_dir}")

        return results

    def process(
        self,
        area: Union[str, Path, Dict],
        max_cloud_cover: float = 50.0,
        bands: Optional[List[str]] = None,
        indices: Optional[List[str]] = None,
        keep_downloads: bool = True,
        download_only: bool = False,
        crop_only: bool = False,
        existing_zips: Optional[List[Path]] = None,
        output_csv: Optional[str] = None,
        dry_run: bool = False,
    ) -> pd.DataFrame:
        """
        Complete processing workflow.

        Args:
            area: GeoJSON file path or geometry dict
            max_cloud_cover: Maximum cloud cover percentage
            bands: Specific bands to process (None = all)
            indices: Vegetation indices to calculate (e.g., ['NDVI', 'EVI'])
            keep_downloads: Keep downloaded ZIP files (default: True)
            download_only: Only download, don't crop
            crop_only: Only crop existing ZIPs
            existing_zips: List of existing ZIP paths (for crop_only)
            output_csv: Path to save results CSV
            dry_run: If True, only show what would be done without actually doing it

        Returns:
            DataFrame with processing results
        """
        results = []

        # Get zone name and dates from GeoJSON
        zone_name = "zone"
        start_date = None
        end_date = None

        if isinstance(area, (str, Path)):
            try:
                geom_data = self.searcher.load_geometry_from_geojson(Path(area))
                zone_name = geom_data.get("name", "zone")

                if "start_date" in geom_data and "end_date" in geom_data:
                    start_date = geom_data["start_date"]
                    end_date = geom_data["end_date"]
                    logger.info(f"Processing {zone_name}: {start_date} to {end_date}")
                else:
                    raise ValueError(
                        f"No dates found in GeoJSON file: {area}\n"
                        f"Please add 'begin' and 'end' properties to your GeoJSON"
                    )
            except Exception as e:
                logger.error(f"Failed to load GeoJSON: {e}")
                raise
        else:
            raise ValueError("Area must be a GeoJSON file path")

        # Step 1: Search (unless crop_only)
        if not crop_only:
            logger.info("Step 1: Searching for products...")
            products = self.search(area, start_date, end_date, max_cloud_cover)

            if dry_run:
                logger.info("[DRY RUN] Would search for products:")
                logger.info(f"  Area: {zone_name}")
                logger.info(f"  Dates: {start_date} to {end_date}")
                logger.info(f"  Max cloud: {max_cloud_cover}%")
                logger.info(f"  Found: {len(products)} products")
                if products:
                    # Show first few products
                    for i, prod in enumerate(products[:3]):
                        props = prod.get("properties", {})
                        product_id = props.get("identifier", "N/A")
                        date = props.get("start_datetime", "")[:10]
                        cloud = props.get("eo:cloud_cover", 0)
                        logger.info(f"    {i+1}. {product_id} - {date} - Cloud: {cloud:.1f}%")
                    if len(products) > 3:
                        logger.info(f"    ... and {len(products) - 3} more")
        else:
            products = []

        # Step 2: Download (unless crop_only or download_only)
        zip_paths = []
        if not crop_only and not dry_run:
            logger.info("Step 2: Downloading products...")
            zip_paths = self.download(products, zone_name, show_progress=True)
        elif not crop_only and dry_run:
            logger.info("[DRY RUN] Step 2: Would download products:")
            total_size_mb = 0
            for prod in products:
                props = prod.get("properties", {})
                # Estimate ~600MB per product
                size_mb = 600
                total_size_mb += size_mb
                logger.info(f"  - {props.get('identifier', 'N/A')} (~{size_mb} MB)")
            logger.info(f"  Total estimated download: ~{total_size_mb/1024:.1f} GB")
        elif existing_zips:
            zip_paths = existing_zips

        # Step 3: Crop (unless download_only)
        crop_results = {}
        if not download_only and zip_paths and not dry_run:
            logger.info("Step 3: Cropping bands...")
            crop_results = self.crop(zip_paths, area, zone_name, bands)

            # Log zip preservation status
            if keep_downloads:
                logger.info(f"ZIP files preserved in: {self.downloads_dir}")
        elif not download_only and dry_run:
            logger.info("[DRY RUN] Step 3: Would crop bands:")
            logger.info(f"  Bands to crop: {bands if bands else 'All available bands'}")
            logger.info(f"  Output directory: {self.crops_dir}")
            if products:
                num_bands = len(bands) if bands else 13
                expected_files = len(products) * num_bands
                logger.info(f"  Expected output: ~{expected_files} band files")

        # Step 4: Calculate indices (if requested and crops available)
        index_results = {}
        if indices and crop_results and not download_only and not dry_run:
            logger.info(f"Step 4: Calculating indices: {indices}")
            index_results = self.calculate_indices(self.crops_dir, indices)
        elif indices and dry_run:
            logger.info("[DRY RUN] Step 4: Would calculate indices:")
            logger.info(f"  Indices: {', '.join(indices)}")
            logger.info(f"  Output directory: {self.indices_dir}")
            if products:
                logger.info(f"  Expected output: {len(products) * len(indices)} index files")

        # Create results DataFrame
        for _, product in enumerate(products):
            props = product.get("properties", {})
            product_id = props.get("identifier", "unknown")

            # Find corresponding ZIP and crops
            zip_path = None
            cropped_files = []

            for zp in zip_paths:
                if product_id in str(zp):
                    zip_path = zp
                    cropped_files = crop_results.get(zp.name, [])
                    break

            result = {
                "zone_name": zone_name,
                "product_id": product_id,
                "date": props.get("start_datetime", "")[:10],
                "datetime": props.get("start_datetime", ""),
                "platform": props.get("platform", "N/A"),
                "cloud_cover": props.get("eo:cloud_cover", 0),
                "processing_level": props.get("processing:level", "L1C"),
                "tile": props.get("grid:code", "N/A"),
                "zip_path": str(zip_path) if zip_path else None,
                "zip_preserved": keep_downloads and zip_path is not None,
                "zip_size_mb": (
                    zip_path.stat().st_size / (1024 * 1024)
                    if zip_path and zip_path.exists()
                    else None
                ),
                "bands_cropped": len(cropped_files),
                "crop_dir": str(self.crops_dir) if cropped_files else None,
                "indices_calculated": ", ".join(indices) if indices and index_results else None,
                "indices_dir": str(self.indices_dir) if index_results else None,
            }

            results.append(result)

        df = pd.DataFrame(results)

        # Save CSV if requested
        if output_csv:
            df.to_csv(output_csv, index=False)
            logger.info(f"Saved results to {output_csv}")

        # Print summary
        logger.info(f"\n{'='*50}")
        logger.info("Processing Summary:")
        logger.info(f"  Products found: {len(products)}")
        logger.info(f"  Products downloaded: {len(zip_paths)}")
        logger.info(f"  Products cropped: {len(crop_results)}")

        if index_results:
            total_indices = sum(len(paths) for paths in index_results.values())
            logger.info(f"  Indices calculated: {total_indices}")

        if not df.empty:
            logger.info(f"  Date range: {df['date'].min()} to {df['date'].max()}")
            logger.info(f"  Average cloud cover: {df['cloud_cover'].mean():.1f}%")
            logger.info(f"  Total download size: {df['zip_size_mb'].sum():.1f} MB")
            if keep_downloads:
                logger.info(f"  ZIP files preserved: Yes ({self.downloads_dir})")
            else:
                logger.info("  ZIP files preserved: No (temporary only)")

        return df

    def process_batch(self, areas: List[Union[str, Path, Dict]], **kwargs) -> pd.DataFrame:
        """
        Process multiple areas using dates from their GeoJSON properties.

        Args:
            areas: List of GeoJSON files or geometry dicts
            **kwargs: Additional arguments for process()

        Returns:
            Combined DataFrame with all results
        """
        all_results = []
        failed_areas = []

        total_areas = len(areas)
        for i, area in enumerate(areas, 1):
            area_name = Path(area).name if isinstance(area, (str, Path)) else f"area_{i}"
            logger.info(f"\n{'='*50}")
            logger.info(f"Processing area {i}/{total_areas}: {area_name}")
            logger.info("=" * 50)

            try:
                df = self.process(area, **kwargs)
                if not df.empty:
                    all_results.append(df)
                    logger.info(f"✓ Successfully processed {area_name}: {len(df)} products")
                else:
                    logger.warning(f"⚠ No products found for {area_name}")
            except Exception as e:
                logger.error(f"✗ Failed to process {area_name}: {e}")
                failed_areas.append((area_name, str(e)))

        # Summary
        logger.info(f"\n{'='*50}")
        logger.info("Batch Processing Summary")
        logger.info("=" * 50)
        logger.info(f"Areas processed: {total_areas - len(failed_areas)}/{total_areas}")

        if failed_areas:
            logger.warning(f"Failed areas ({len(failed_areas)}):")
            for name, error in failed_areas:
                logger.warning(f"  - {name}: {error}")

        if all_results:
            return pd.concat(all_results, ignore_index=True)
        else:
            logger.warning("No results to combine")
            return pd.DataFrame()
