"""
Download module for Sentinel-2 data from GEODES portal.
"""

import logging
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

import requests  # type: ignore[import-untyped]
from tqdm import tqdm

logger = logging.getLogger(__name__)


class GeodesDownloader:
    """Handle downloads from the GEODES portal."""

    def __init__(self, api_key: str, output_dir: Path = Path("./downloads")):
        """
        Initialize the downloader.

        Args:
            api_key: GEODES API key
            output_dir: Directory for downloads
        """
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create an authenticated session."""
        session = requests.Session()
        session.headers.update({"X-API-Key": self.api_key})
        return session

    @staticmethod
    def extract_download_url(product: Dict) -> Optional[str]:
        """
        Extract the download URL from a product.

        Args:
            product: Product dictionary from STAC search

        Returns:
            Download URL or None if not found
        """
        if "assets" not in product:
            logger.warning("No assets found in product")
            return None

        assets = product["assets"]

        # Look for ZIP assets
        for key, asset in assets.items():
            if isinstance(asset, dict) and "href" in asset:
                if key.endswith(".zip"):
                    logger.debug(f"Found ZIP asset: {key}")
                    return str(asset["href"])

        # Fallback: look for application/zip type
        for key, asset in assets.items():
            if isinstance(asset, dict) and "href" in asset:
                if asset.get("type") == "application/zip":
                    logger.debug(f"Found ZIP by MIME type: {key}")
                    return str(asset["href"])

        logger.warning("No ZIP download URL found")
        return None

    def download(
        self, url: str, filename: str, chunk_size: int = 8192, show_progress: bool = True
    ) -> Path:
        """
        Download a file with progress bar.

        Args:
            url: Download URL
            filename: Target filename
            chunk_size: Download chunk size in bytes
            show_progress: Show progress bar

        Returns:
            Path to downloaded file
        """
        output_path = self.output_dir / filename

        # Check if already exists
        if output_path.exists():
            logger.info(f"File already exists: {filename}")
            return output_path

        logger.info(f"Downloading: {filename}")

        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()

            # Get total size if available
            total_size = int(response.headers.get("content-length", 0))

            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp_file:
                temp_path = Path(tmp_file.name)

                # Download with progress bar
                if show_progress and total_size > 0:
                    with tqdm(total=total_size, unit="iB", unit_scale=True, desc=filename) as pbar:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if chunk:
                                tmp_file.write(chunk)
                                pbar.update(len(chunk))
                else:
                    # Download without progress bar
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            tmp_file.write(chunk)

            # Verify it's a valid ZIP
            if not zipfile.is_zipfile(temp_path):
                temp_path.unlink()
                raise ValueError("Downloaded file is not a valid ZIP")

            # Move to final location
            shutil.move(str(temp_path), str(output_path))
            logger.info(f"Download complete: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Download failed: {e}")
            # Clean up temp file if it exists
            if "temp_path" in locals() and temp_path.exists():
                temp_path.unlink()
            raise

    def download_product(
        self, product: Dict, zone_name: str = "zone", show_progress: bool = True
    ) -> Optional[Path]:
        """
        Download a Sentinel-2 product.

        Args:
            product: Product dictionary from STAC search
            zone_name: Name prefix for the file
            show_progress: Show progress bar

        Returns:
            Path to downloaded file or None if failed
        """
        # Extract metadata
        props = product.get("properties", {})
        product_id = props.get("identifier", "unknown")
        date = props.get("start_datetime", "")[:10]

        # Get download URL
        url = self.extract_download_url(product)
        if not url:
            logger.error(f"No download URL for product {product_id}")
            return None

        # Create filename
        filename = f"{zone_name}_{date}_{product_id}.zip"

        try:
            return self.download(url, filename, show_progress=show_progress)
        except Exception as e:
            logger.error(f"Failed to download {product_id}: {e}")
            return None

    def download_multiple(
        self, products: List[Dict], zone_name: str = "zone", show_progress: bool = True
    ) -> List[Path]:
        """
        Download multiple products.

        Args:
            products: List of products to download
            zone_name: Name prefix for files
            show_progress: Show progress bar

        Returns:
            List of downloaded file paths
        """
        downloaded = []

        for i, product in enumerate(products, 1):
            logger.info(f"Processing product {i}/{len(products)}")

            path = self.download_product(product, zone_name, show_progress)
            if path:
                downloaded.append(path)

        logger.info(f"Downloaded {len(downloaded)}/{len(products)} products")
        return downloaded
