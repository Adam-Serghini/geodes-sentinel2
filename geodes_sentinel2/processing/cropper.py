"""
Raster cropping module for Sentinel-2 bands.
"""

import logging
import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import box, shape

logger = logging.getLogger(__name__)


class RasterCropper:
    """Handle raster cropping operations."""

    SENTINEL2_BANDS = [
        "B01",
        "B02",
        "B03",
        "B04",
        "B05",
        "B06",
        "B07",
        "B08",
        "B8A",
        "B09",
        "B10",
        "B11",
        "B12",
    ]

    def __init__(self, output_dir: Path = Path("./crops")):
        """
        Initialize the cropper.

        Args:
            output_dir: Directory for cropped outputs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def extract_band_name(filepath: Union[str, Path]) -> str:
        """
        Extract band name from Sentinel-2 file.

        Args:
            filepath: Path to the band file

        Returns:
            Band name (e.g., 'B02', 'B8A')
        """
        filename = os.path.basename(str(filepath))

        # Standard bands B01-B12
        match = re.search(r"_B(\d{2})\.", filename)
        if match:
            return f"B{match.group(1)}"

        # Special band B8A
        if "_B8A." in filename:
            return "B8A"

        # True Color Image
        if "_TCI." in filename:
            return "TCI"

        return "unknown"

    @staticmethod
    def find_bands_in_zip(zip_path: Path) -> List[Tuple[str, str]]:
        """
        Find all band files in a Sentinel-2 ZIP.

        Args:
            zip_path: Path to ZIP file

        Returns:
            List of (band_name, file_path) tuples
        """
        bands = []

        with zipfile.ZipFile(zip_path, "r") as zf:
            for file_info in zf.filelist:
                filename = file_info.filename

                # Look for files in IMG_DATA folders
                if "IMG_DATA" in filename and filename.endswith(".jp2"):
                    # Skip masks and TCI
                    if not filename.startswith("MSK_") and not filename.endswith("_TCI.jp2"):
                        # Check if it's a band file
                        if "_B" in filename:
                            band_name = RasterCropper.extract_band_name(filename)
                            if band_name != "unknown":
                                bands.append((band_name, filename))
                                logger.debug(f"Found band {band_name}: {filename}")

        return sorted(bands)

    def crop_raster(
        self,
        raster_path: Union[str, Path],
        geometry: Union[Dict, gpd.GeoDataFrame],
        output_path: Path,
        compress: str = "lzw",
    ) -> bool:
        """
        Crop a raster to a geometry.

        Args:
            raster_path: Path to input raster
            geometry: Geometry to crop to (GeoJSON dict or GeoDataFrame)
            output_path: Path for output file
            compress: Compression method

        Returns:
            True if successful, False otherwise
        """
        try:
            with rasterio.open(raster_path) as src:
                raster_crs = src.crs

                # Create GeoDataFrame from geometry
                if isinstance(geometry, dict):
                    # GeoJSON geometry
                    geom_shape = shape(geometry)
                    geom_gdf = gpd.GeoDataFrame([1], geometry=[geom_shape], crs="EPSG:4326")
                elif isinstance(geometry, gpd.GeoDataFrame):
                    geom_gdf = geometry
                else:
                    # Assume it's a shapely geometry
                    geom_gdf = gpd.GeoDataFrame([1], geometry=[geometry], crs="EPSG:4326")

                # Reproject geometry to raster CRS if needed
                if geom_gdf.crs != raster_crs:
                    logger.debug(f"Reprojecting geometry from {geom_gdf.crs} to {raster_crs}")
                    geom_gdf = geom_gdf.to_crs(raster_crs)

                # Get reprojected geometry
                reprojected_geom = geom_gdf.geometry.iloc[0]

                # Check intersection
                raster_bounds = src.bounds
                raster_box = box(*raster_bounds)

                if not raster_box.intersects(reprojected_geom):
                    logger.warning("Geometry does not intersect raster")
                    return False

                # Perform crop
                out_image, out_transform = mask(src, [reprojected_geom], crop=True)

                # Check if crop produced data
                if out_image.shape[1] == 0 or out_image.shape[2] == 0:
                    logger.warning("Crop produced empty image")
                    return False

                # Update metadata
                out_meta = src.meta.copy()
                out_meta.update(
                    {
                        "driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform,
                        "compress": compress,
                    }
                )

                # Save output
                with rasterio.open(output_path, "w", **out_meta) as dest:
                    dest.write(out_image)

                size_str = f"{out_image.shape[1]}x{out_image.shape[2]}"
                logger.info(f"Cropped to {size_str} pixels: {output_path.name}")
                return True

        except Exception as e:
            logger.error(f"Failed to crop {raster_path}: {e}")
            return False

    def process_zip(
        self,
        zip_path: Path,
        geometry: Union[Dict, gpd.GeoDataFrame],
        zone_name: str,
        date: str,
        bands_to_process: Optional[List[str]] = None,
    ) -> List[Path]:
        """
        Extract and crop bands from a Sentinel-2 ZIP.

        Args:
            zip_path: Path to ZIP file
            geometry: Geometry to crop to
            zone_name: Name for output files
            date: Date string for output files
            bands_to_process: Specific bands to process (None = all)

        Returns:
            List of cropped file paths
        """
        cropped_files: List[Path] = []

        # Find bands in ZIP
        bands = self.find_bands_in_zip(zip_path)

        if not bands:
            logger.warning(f"No bands found in {zip_path}")
            return cropped_files

        logger.info(f"Found {len(bands)} bands in ZIP")

        # Filter bands if specified
        if bands_to_process:
            bands = [(b, p) for b, p in bands if b in bands_to_process]
            logger.info(f"Processing {len(bands)} selected bands")

        # Extract and process each band
        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(zip_path, "r") as zf:
                for band_name, band_path in bands:
                    try:
                        # Extract band file
                        logger.debug(f"Extracting {band_name}")
                        zf.extract(band_path, tmp_dir)
                        extracted_path = Path(tmp_dir) / band_path

                        # Create output filename
                        output_filename = f"{zone_name}_{date}_{band_name}.tif"
                        output_path = self.output_dir / output_filename

                        # Crop the band
                        if self.crop_raster(extracted_path, geometry, output_path):
                            cropped_files.append(output_path)
                            logger.info(f"Saved: {output_filename}")
                        else:
                            logger.warning(f"Failed to crop {band_name}")

                    except Exception as e:
                        logger.error(f"Error processing {band_name}: {e}")

        logger.info(f"Successfully cropped {len(cropped_files)}/{len(bands)} bands")
        return cropped_files

    def process_multiple_zips(
        self,
        zip_paths: List[Path],
        geometry: Union[Dict, gpd.GeoDataFrame],
        zone_name: str = "zone",
        bands_to_process: Optional[List[str]] = None,
    ) -> Dict[str, List[Path]]:
        """
        Process multiple ZIP files.

        Args:
            zip_paths: List of ZIP file paths
            geometry: Geometry to crop to
            zone_name: Name for output files
            bands_to_process: Specific bands to process

        Returns:
            Dictionary mapping ZIP names to cropped file lists
        """
        results = {}

        for zip_path in zip_paths:
            logger.info(f"Processing: {zip_path.name}")

            # Extract date from filename
            date_match = re.search(r"_(\d{4}-\d{2}-\d{2})_", zip_path.name)
            date = date_match.group(1) if date_match else "unknown"

            cropped = self.process_zip(zip_path, geometry, zone_name, date, bands_to_process)

            results[zip_path.name] = cropped

        return results
