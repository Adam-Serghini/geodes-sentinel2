"""
Search module for querying Sentinel-2 data from GEODES portal.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import requests  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class SearchParameters(BaseModel):
    """Parameters for Sentinel-2 search."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    bbox: Tuple[float, float, float, float] = Field(description="Bounding box")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")
    max_cloud_cover: float = Field(default=50.0, description="Maximum cloud cover percentage")
    dataset: str = Field(default="PEPS_S2_L1C", description="Dataset to search")


class GeodesSearch:
    """Handle searches on the GEODES STAC API."""

    def __init__(self, api_key: str, base_url: str = "https://geodes-portal.cnes.fr"):
        """
        Initialize the search client.

        Args:
            api_key: GEODES API key
            base_url: Base URL for GEODES portal
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create an authenticated session."""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json", "X-API-Key": self.api_key})
        return session

    @staticmethod
    def load_geometry_from_geojson(geojson_path: Path) -> Dict:
        """
        Load geometry from a GeoJSON file.

        Args:
            geojson_path: Path to GeoJSON file

        Returns:
            Dictionary with geometry information including dates if available
        """
        with open(geojson_path) as f:
            data = json.load(f)

        feature = data["features"][0]
        properties = feature["properties"]

        # Extract dates from properties if available
        result = {
            "name": properties.get("Name", "Unknown"),
            "geometry": feature["geometry"],
            "properties": properties,
        }

        # Check for date fields in properties
        if "begin" in properties:
            # Handle ISO format dates
            begin_date = properties["begin"]
            if "T" in begin_date:
                begin_date = begin_date.split("T")[0]
            result["start_date"] = begin_date

        if "end" in properties:
            end_date = properties["end"]
            if "T" in end_date:
                end_date = end_date.split("T")[0]
            result["end_date"] = end_date

        # Also check for alternative date field names
        if "start_date" in properties:
            result["start_date"] = properties["start_date"]
        if "end_date" in properties:
            result["end_date"] = properties["end_date"]

        # Validate dates are present
        if "start_date" not in result or "end_date" not in result:
            raise ValueError(
                f"GeoJSON file must contain date properties. "
                f"Add 'begin' and 'end' fields to properties. "
                f"Found properties: {list(properties.keys())}"
            )

        return result

    @staticmethod
    def geometry_to_bbox(geometry: Dict) -> Tuple[float, float, float, float]:
        """
        Convert geometry to bounding box.

        Args:
            geometry: GeoJSON geometry dict

        Returns:
            Bounding box tuple (west, south, east, north)
        """
        if geometry["type"] == "Polygon":
            # GeoJSON Polygon structure: [[[lon, lat], [lon, lat], ...]]
            # The first array is for the outer ring
            coordinates = geometry["coordinates"][0]
            # Check if we have another level of nesting (triple-nested case)
            if (
                coordinates
                and isinstance(coordinates[0], list)
                and isinstance(coordinates[0][0], list)
            ):
                coordinates = coordinates[0]
        elif geometry["type"] == "MultiPolygon":
            # Flatten all polygons
            coordinates = []
            for polygon in geometry["coordinates"]:
                # Each polygon is like: [[[lon, lat], ...]]
                ring = polygon[0]
                if ring and isinstance(ring[0], list) and isinstance(ring[0][0], list):
                    ring = ring[0]
                coordinates.extend(ring)
        else:
            raise ValueError(f"Unsupported geometry type: {geometry['type']}")

        lons = [point[0] for point in coordinates]
        lats = [point[1] for point in coordinates]

        return (min(lons), min(lats), max(lons), max(lats))

    def search(self, params: SearchParameters) -> List[Dict]:
        """
        Search for Sentinel-2 products.

        Args:
            params: Search parameters

        Returns:
            List of found products
        """
        query = {
            "page": 1,
            "limit": None,
            "bbox": list(params.bbox),
            "query": {
                "dataset": {"in": [params.dataset]},
                "start_datetime": {"gte": f"{params.start_date}T00:00:00.000Z"},
                "end_datetime": {"lte": f"{params.end_date}T23:59:59.999Z"},
                "eo:cloud_cover": {"lte": params.max_cloud_cover},
            },
            "sortBy": [{"direction": "asc", "field": "start_datetime"}],
        }

        logger.info(f"Searching with bbox: {params.bbox}")
        logger.debug(f"Full query: {query}")

        try:
            response = self.session.post(f"{self.base_url}/api/stac/search", json=query)
            response.raise_for_status()
            data = response.json()

            features = data.get("features", [])
            logger.info(f"Found {len(features)} products")

            return list(features)

        except requests.RequestException as e:
            logger.error(f"Search failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {e}")
            raise

    def search_by_geometry(
        self, geometry_path: Path, start_date: str, end_date: str, max_cloud_cover: float = 50.0
    ) -> List[Dict]:
        """
        Search for products using a GeoJSON file.

        Args:
            geometry_path: Path to GeoJSON file
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            max_cloud_cover: Maximum cloud cover percentage

        Returns:
            List of found products
        """
        # Load geometry
        geom_data = self.load_geometry_from_geojson(geometry_path)

        # Convert to bbox
        bbox = self.geometry_to_bbox(geom_data["geometry"])

        # Create search parameters
        params = SearchParameters(
            bbox=bbox, start_date=start_date, end_date=end_date, max_cloud_cover=max_cloud_cover
        )

        # Perform search
        products = self.search(params)

        # Add geometry name to results
        for product in products:
            product["search_zone"] = geom_data["name"]

        return products
