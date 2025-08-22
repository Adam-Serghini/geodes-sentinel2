"""
Band math module for calculating vegetation indices from Sentinel-2 data.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import rasterio
from rasterio import Affine
from rasterio.warp import Resampling, reproject

logger = logging.getLogger(__name__)


class BandMath:
    """Calculate vegetation indices and band combinations."""

    # Sentinel-2 band central wavelengths (nm) and common names
    BAND_INFO = {
        "B01": {"wavelength": 443, "name": "Coastal aerosol", "resolution": 60},
        "B02": {"wavelength": 490, "name": "Blue", "resolution": 10},
        "B03": {"wavelength": 560, "name": "Green", "resolution": 10},
        "B04": {"wavelength": 665, "name": "Red", "resolution": 10},
        "B05": {"wavelength": 705, "name": "Red Edge 1", "resolution": 20},
        "B06": {"wavelength": 740, "name": "Red Edge 2", "resolution": 20},
        "B07": {"wavelength": 783, "name": "Red Edge 3", "resolution": 20},
        "B08": {"wavelength": 842, "name": "NIR", "resolution": 10},
        "B8A": {"wavelength": 865, "name": "NIR narrow", "resolution": 20},
        "B09": {"wavelength": 945, "name": "Water vapor", "resolution": 60},
        "B10": {"wavelength": 1375, "name": "Cirrus", "resolution": 60},
        "B11": {"wavelength": 1610, "name": "SWIR 1", "resolution": 20},
        "B12": {"wavelength": 2190, "name": "SWIR 2", "resolution": 20},
    }

    def __init__(self, output_dir: Path = Path("./indices")):
        """
        Initialize the band math calculator.

        Args:
            output_dir: Directory for output indices
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def load_band(
        band_path: Path,
        target_shape: Optional[Tuple] = None,
        target_transform: Optional[Affine] = None,
        target_crs: Optional[str] = None,
    ) -> Tuple[np.ndarray, Dict]:
        """
        Load a band and optionally resample to target resolution.

        Args:
            band_path: Path to band file
            target_shape: Target shape for resampling
            target_transform: Target transform for resampling
            target_crs: Target CRS for resampling

        Returns:
            Band array and metadata
        """
        with rasterio.open(band_path) as src:
            if target_shape and target_transform:
                # Resample to target resolution
                data = np.empty(target_shape, dtype=src.dtypes[0])

                reproject(
                    source=rasterio.band(src, 1),
                    destination=data,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=target_transform,
                    dst_crs=target_crs or src.crs,
                    resampling=Resampling.bilinear,
                )
            else:
                data = src.read(1)
                target_transform = src.transform
                target_crs = src.crs

            meta = src.meta.copy()
            meta.update(
                {
                    "transform": target_transform,
                    "crs": target_crs,
                    "height": data.shape[0],
                    "width": data.shape[1],
                }
            )

            return data.astype(np.float32), meta

    @staticmethod
    def normalize_difference(band1: np.ndarray, band2: np.ndarray) -> np.ndarray:
        """
        Calculate normalized difference: (band1 - band2) / (band1 + band2).

        Args:
            band1: First band array
            band2: Second band array

        Returns:
            Normalized difference array
        """
        with np.errstate(divide="ignore", invalid="ignore"):
            nd = (band1 - band2) / (band1 + band2)
            nd[np.isnan(nd)] = 0
            nd[np.isinf(nd)] = 0
            return nd  # type: ignore[no-any-return]

    def calculate_ndvi(
        self, red_path: Path, nir_path: Path, output_path: Optional[Path] = None
    ) -> Path:
        """
        Calculate NDVI (Normalized Difference Vegetation Index).
        NDVI = (NIR - Red) / (NIR + Red)

        Args:
            red_path: Path to red band (B04)
            nir_path: Path to NIR band (B08)
            output_path: Optional output path

        Returns:
            Path to output file
        """
        logger.info("Calculating NDVI")

        # Load bands
        red, red_meta = self.load_band(red_path)
        nir, nir_meta = self.load_band(nir_path, red.shape, red_meta["transform"], red_meta["crs"])

        # Calculate NDVI
        ndvi = self.normalize_difference(nir, red)

        # Prepare output
        if output_path is None:
            output_path = self.output_dir / f"ndvi_{red_path.stem.replace('_B04', '')}.tif"

        # Save
        out_meta = red_meta.copy()
        out_meta.update({"dtype": "float32", "count": 1, "compress": "lzw"})

        with rasterio.open(output_path, "w", **out_meta) as dst:
            dst.write(ndvi, 1)
            dst.set_band_description(1, "NDVI")

        logger.info(f"NDVI saved to {output_path}")
        return output_path

    def calculate_evi(
        self, blue_path: Path, red_path: Path, nir_path: Path, output_path: Optional[Path] = None
    ) -> Path:
        """
        Calculate EVI (Enhanced Vegetation Index).
        EVI = 2.5 * ((NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1))

        Args:
            blue_path: Path to blue band (B02)
            red_path: Path to red band (B04)
            nir_path: Path to NIR band (B08)
            output_path: Optional output path

        Returns:
            Path to output file
        """
        logger.info("Calculating EVI")

        # Load bands (resample to red resolution)
        red, red_meta = self.load_band(red_path)
        nir, _ = self.load_band(nir_path, red.shape, red_meta["transform"], red_meta["crs"])
        blue, _ = self.load_band(blue_path, red.shape, red_meta["transform"], red_meta["crs"])

        # Calculate EVI
        with np.errstate(divide="ignore", invalid="ignore"):
            evi = 2.5 * ((nir - red) / (nir + 6 * red - 7.5 * blue + 1))
            evi[np.isnan(evi)] = 0
            evi[np.isinf(evi)] = 0
            evi = np.clip(evi, -1, 1)

        # Prepare output
        if output_path is None:
            output_path = self.output_dir / f"evi_{red_path.stem.replace('_B04', '')}.tif"

        # Save
        out_meta = red_meta.copy()
        out_meta.update({"dtype": "float32", "count": 1, "compress": "lzw"})

        with rasterio.open(output_path, "w", **out_meta) as dst:
            dst.write(evi, 1)
            dst.set_band_description(1, "EVI")

        logger.info(f"EVI saved to {output_path}")
        return output_path

    def calculate_ndwi(
        self, green_path: Path, nir_path: Path, output_path: Optional[Path] = None
    ) -> Path:
        """
        Calculate NDWI (Normalized Difference Water Index).
        NDWI = (Green - NIR) / (Green + NIR)

        Args:
            green_path: Path to green band (B03)
            nir_path: Path to NIR band (B08)
            output_path: Optional output path

        Returns:
            Path to output file
        """
        logger.info("Calculating NDWI")

        # Load bands
        green, green_meta = self.load_band(green_path)
        nir, _ = self.load_band(nir_path, green.shape, green_meta["transform"], green_meta["crs"])

        # Calculate NDWI
        ndwi = self.normalize_difference(green, nir)

        # Prepare output
        if output_path is None:
            output_path = self.output_dir / f"ndwi_{green_path.stem.replace('_B03', '')}.tif"

        # Save
        out_meta = green_meta.copy()
        out_meta.update({"dtype": "float32", "count": 1, "compress": "lzw"})

        with rasterio.open(output_path, "w", **out_meta) as dst:
            dst.write(ndwi, 1)
            dst.set_band_description(1, "NDWI")

        logger.info(f"NDWI saved to {output_path}")
        return output_path

    def calculate_savi(
        self, red_path: Path, nir_path: Path, L: float = 0.5, output_path: Optional[Path] = None
    ) -> Path:
        """
        Calculate SAVI (Soil Adjusted Vegetation Index).
        SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)

        Args:
            red_path: Path to red band (B04)
            nir_path: Path to NIR band (B08)
            L: Soil brightness correction factor (0.5 for intermediate vegetation)
            output_path: Optional output path

        Returns:
            Path to output file
        """
        logger.info(f"Calculating SAVI with L={L}")

        # Load bands
        red, red_meta = self.load_band(red_path)
        nir, _ = self.load_band(nir_path, red.shape, red_meta["transform"], red_meta["crs"])

        # Calculate SAVI
        with np.errstate(divide="ignore", invalid="ignore"):
            savi = ((nir - red) / (nir + red + L)) * (1 + L)
            savi[np.isnan(savi)] = 0
            savi[np.isinf(savi)] = 0
            savi = np.clip(savi, -1, 1)

        # Prepare output
        if output_path is None:
            output_path = self.output_dir / f"savi_{red_path.stem.replace('_B04', '')}.tif"

        # Save
        out_meta = red_meta.copy()
        out_meta.update({"dtype": "float32", "count": 1, "compress": "lzw"})

        with rasterio.open(output_path, "w", **out_meta) as dst:
            dst.write(savi, 1)
            dst.set_band_description(1, "SAVI")

        logger.info(f"SAVI saved to {output_path}")
        return output_path

    def calculate_gndvi(
        self, green_path: Path, nir_path: Path, output_path: Optional[Path] = None
    ) -> Path:
        """
        Calculate GNDVI (Green Normalized Difference Vegetation Index).
        GNDVI = (NIR - Green) / (NIR + Green)

        Args:
            green_path: Path to green band (B03)
            nir_path: Path to NIR band (B08)
            output_path: Optional output path

        Returns:
            Path to output file
        """
        logger.info("Calculating GNDVI")

        # Load bands
        green, green_meta = self.load_band(green_path)
        nir, _ = self.load_band(nir_path, green.shape, green_meta["transform"], green_meta["crs"])

        # Calculate GNDVI
        gndvi = self.normalize_difference(nir, green)

        # Prepare output
        if output_path is None:
            output_path = self.output_dir / f"gndvi_{green_path.stem.replace('_B03', '')}.tif"

        # Save
        out_meta = green_meta.copy()
        out_meta.update({"dtype": "float32", "count": 1, "compress": "lzw"})

        with rasterio.open(output_path, "w", **out_meta) as dst:
            dst.write(gndvi, 1)
            dst.set_band_description(1, "GNDVI")

        logger.info(f"GNDVI saved to {output_path}")
        return output_path

    def calculate_ndre(
        self, red_edge_path: Path, nir_path: Path, output_path: Optional[Path] = None
    ) -> Path:
        """
        Calculate NDRE (Normalized Difference Red Edge).
        NDRE = (NIR - RedEdge) / (NIR + RedEdge)

        Args:
            red_edge_path: Path to red edge band (B05)
            nir_path: Path to NIR band (B08)
            output_path: Optional output path

        Returns:
            Path to output file
        """
        logger.info("Calculating NDRE")

        # Load bands
        red_edge, re_meta = self.load_band(red_edge_path)
        nir, _ = self.load_band(nir_path, red_edge.shape, re_meta["transform"], re_meta["crs"])

        # Calculate NDRE
        ndre = self.normalize_difference(nir, red_edge)

        # Prepare output
        if output_path is None:
            output_path = self.output_dir / f"ndre_{red_edge_path.stem.replace('_B05', '')}.tif"

        # Save
        out_meta = re_meta.copy()
        out_meta.update({"dtype": "float32", "count": 1, "compress": "lzw"})

        with rasterio.open(output_path, "w", **out_meta) as dst:
            dst.write(ndre, 1)
            dst.set_band_description(1, "NDRE")

        logger.info(f"NDRE saved to {output_path}")
        return output_path

    def calculate_custom(
        self, expression: str, bands: Dict[str, Path], output_path: Optional[Path] = None
    ) -> Path:
        """
        Calculate custom band math expression.

        Args:
            expression: Math expression (e.g., "(B08 - B04) / (B08 + B04)")
            bands: Dictionary mapping band names to file paths
            output_path: Optional output path

        Returns:
            Path to output file
        """
        logger.info(f"Calculating custom expression: {expression}")

        # Load all bands
        band_arrays = {}
        reference_meta = None
        reference_shape = None

        for band_name, band_path in bands.items():
            if reference_meta is None:
                band_array, reference_meta = self.load_band(band_path)
                reference_shape = band_array.shape
            else:
                band_array, _ = self.load_band(
                    band_path, reference_shape, reference_meta["transform"], reference_meta["crs"]
                )
            band_arrays[band_name] = band_array

        # Evaluate expression
        with np.errstate(divide="ignore", invalid="ignore"):
            result = eval(expression, {"__builtins__": {}}, band_arrays)
            result[np.isnan(result)] = 0
            result[np.isinf(result)] = 0

        # Prepare output
        if output_path is None:
            output_path = self.output_dir / "custom_index.tif"

        # Save
        if reference_meta is not None:
            out_meta = reference_meta.copy()
        else:
            raise ValueError("reference_meta is None, cannot create output metadata")
        out_meta.update({"dtype": "float32", "count": 1, "compress": "lzw"})

        with rasterio.open(output_path, "w", **out_meta) as dst:
            dst.write(result, 1)
            dst.set_band_description(1, f"Custom: {expression}")

        logger.info(f"Custom index saved to {output_path}")
        return output_path

    def process_all_indices(
        self, crop_dir: Path, indices: Optional[List[str]] = None
    ) -> Dict[str, List[Path]]:
        """
        Calculate multiple indices for all available dates.

        Args:
            crop_dir: Directory containing cropped bands
            indices: List of indices to calculate (default: NDVI, EVI, NDWI)

        Returns:
            Dictionary mapping index names to output paths
        """
        if indices is None:
            indices = ["NDVI", "EVI", "NDWI"]

        results: Dict[str, List[Path]] = {idx: [] for idx in indices}

        # Find all unique dates/products
        band_files = list(crop_dir.glob("*.tif"))
        products: Dict[str, Dict[str, Path]] = {}

        for band_file in band_files:
            # Extract product identifier (everything before the band)
            parts = band_file.stem.rsplit("_", 1)
            if len(parts) == 2:
                product_id = parts[0]
                band = parts[1]

                if product_id not in products:
                    products[product_id] = {}
                products[product_id][band] = band_file

        # Calculate indices for each product
        for product_id, bands in products.items():
            logger.info(f"Processing indices for {product_id}")

            if "NDVI" in indices and "B04" in bands and "B08" in bands:
                try:
                    path = self.calculate_ndvi(bands["B04"], bands["B08"])
                    results["NDVI"].append(path)
                except Exception as e:
                    logger.error(f"Failed to calculate NDVI for {product_id}: {e}")

            if "EVI" in indices and all(b in bands for b in ["B02", "B04", "B08"]):
                try:
                    path = self.calculate_evi(bands["B02"], bands["B04"], bands["B08"])
                    results["EVI"].append(path)
                except Exception as e:
                    logger.error(f"Failed to calculate EVI for {product_id}: {e}")

            if "NDWI" in indices and "B03" in bands and "B08" in bands:
                try:
                    path = self.calculate_ndwi(bands["B03"], bands["B08"])
                    results["NDWI"].append(path)
                except Exception as e:
                    logger.error(f"Failed to calculate NDWI for {product_id}: {e}")

            if "SAVI" in indices and "B04" in bands and "B08" in bands:
                try:
                    path = self.calculate_savi(bands["B04"], bands["B08"])
                    results["SAVI"].append(path)
                except Exception as e:
                    logger.error(f"Failed to calculate SAVI for {product_id}: {e}")

            if "GNDVI" in indices and "B03" in bands and "B08" in bands:
                try:
                    path = self.calculate_gndvi(bands["B03"], bands["B08"])
                    results["GNDVI"].append(path)
                except Exception as e:
                    logger.error(f"Failed to calculate GNDVI for {product_id}: {e}")

            if "NDRE" in indices and "B05" in bands and "B08" in bands:
                try:
                    path = self.calculate_ndre(bands["B05"], bands["B08"])
                    results["NDRE"].append(path)
                except Exception as e:
                    logger.error(f"Failed to calculate NDRE for {product_id}: {e}")

        # Summary
        for idx, paths in results.items():
            if paths:
                logger.info(f"Calculated {len(paths)} {idx} indices")

        return results
