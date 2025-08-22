"""Tests for search functionality."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from geodes_sentinel2.core.search import GeodesSearch, SearchParameters


class TestGeodesSearch:
    """Test the GeodesSearch class."""
    
    @pytest.fixture
    def mock_api_key(self):
        """Provide a mock API key."""
        return "test-api-key-123"
    
    @pytest.fixture
    def searcher(self, mock_api_key):
        """Create a GeodesSearch instance."""
        return GeodesSearch(mock_api_key)
    
    @pytest.fixture
    def sample_geojson(self, tmp_path):
        """Create a sample GeoJSON file."""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {
                    "Name": "TestField",
                    "begin": "2024-06-01T00:00:00Z",
                    "end": "2024-06-30T00:00:00Z"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[
                        [1.0, 47.0],
                        [1.1, 47.0],
                        [1.1, 47.1],
                        [1.0, 47.1],
                        [1.0, 47.0]
                    ]]]
                }
            }]
        }
        
        geojson_path = tmp_path / "test_area.geojson"
        with open(geojson_path, 'w') as f:
            json.dump(geojson_data, f)
        
        return geojson_path
    
    def test_load_geometry_from_geojson(self, sample_geojson):
        """Test loading geometry and dates from GeoJSON."""
        result = GeodesSearch.load_geometry_from_geojson(sample_geojson)
        
        assert result['name'] == 'TestField'
        assert result['start_date'] == '2024-06-01'
        assert result['end_date'] == '2024-06-30'
        assert result['geometry']['type'] == 'Polygon'
    
    def test_load_geometry_missing_dates(self, tmp_path):
        """Test that missing dates raise an error."""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {"Name": "TestField"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[
                        [1.0, 47.0],
                        [1.1, 47.0],
                        [1.1, 47.1],
                        [1.0, 47.1],
                        [1.0, 47.0]
                    ]]]
                }
            }]
        }
        
        geojson_path = tmp_path / "no_dates.geojson"
        with open(geojson_path, 'w') as f:
            json.dump(geojson_data, f)
        
        with pytest.raises(ValueError, match="must contain date properties"):
            GeodesSearch.load_geometry_from_geojson(geojson_path)
    
    def test_geometry_to_bbox(self):
        """Test converting geometry to bounding box."""
        geometry = {
            "type": "Polygon",
            "coordinates": [[[
                [1.0, 47.0],
                [1.1, 47.0],
                [1.1, 47.1],
                [1.0, 47.1],
                [1.0, 47.0]
            ]]]
        }
        
        bbox = GeodesSearch.geometry_to_bbox(geometry)
        
        assert bbox == (1.0, 47.0, 1.1, 47.1)
    
    def test_search_parameters(self):
        """Test SearchParameters model."""
        params = SearchParameters(
            bbox=(1.0, 47.0, 1.1, 47.1),
            start_date="2024-06-01",
            end_date="2024-06-30",
            max_cloud_cover=30.0
        )
        
        assert params.dataset == "PEPS_S2_L1C"
        assert params.max_cloud_cover == 30.0
    
    @patch('requests.Session.post')
    def test_search_success(self, mock_post, searcher):
        """Test successful search."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "identifier": "S2A_MSIL1C_20240601",
                        "start_datetime": "2024-06-01T10:30:00Z",
                        "eo:cloud_cover": 15.5
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        params = SearchParameters(
            bbox=(1.0, 47.0, 1.1, 47.1),
            start_date="2024-06-01",
            end_date="2024-06-30",
            max_cloud_cover=30.0
        )
        
        results = searcher.search(params)
        
        assert len(results) == 1
        assert results[0]['properties']['identifier'] == "S2A_MSIL1C_20240601"
    
    @patch('requests.Session.post')
    def test_search_by_geometry(self, mock_post, searcher, sample_geojson):
        """Test search by geometry file."""
        mock_response = Mock()
        mock_response.json.return_value = {"features": []}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        results = searcher.search_by_geometry(
            sample_geojson,
            "2024-06-01",
            "2024-06-30",
            max_cloud_cover=30.0
        )
        
        assert isinstance(results, list)
        mock_post.assert_called_once()


class TestSearchIntegration:
    """Integration tests for search functionality."""
    
    @pytest.fixture
    def sample_geojson(self, tmp_path):
        """Create a sample GeoJSON file for integration tests."""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {
                    "Name": "TestField",
                    "begin": "2024-06-01T00:00:00Z",
                    "end": "2024-06-30T00:00:00Z"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[
                        [1.0, 47.0],
                        [1.1, 47.0],
                        [1.1, 47.1],
                        [1.0, 47.1],
                        [1.0, 47.0]
                    ]]]
                }
            }]
        }
        
        geojson_path = tmp_path / "test_area.geojson"
        with open(geojson_path, 'w') as f:
            json.dump(geojson_data, f)
        
        return geojson_path
    
    @pytest.mark.skipif(not Path(".env").exists(), reason="No .env file with API key")
    def test_real_search(self, sample_geojson):
        """Test real search (requires API key)."""
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv("GEODES_API_KEY")
        
        if not api_key:
            pytest.skip("No API key available")
        
        searcher = GeodesSearch(api_key)
        results = searcher.search_by_geometry(
            sample_geojson,
            "2024-06-01",
            "2024-06-07",  # One week
            max_cloud_cover=50.0
        )
        
        # Should find some products in a week
        assert isinstance(results, list)
        if results:
            assert 'properties' in results[0]
            assert 'identifier' in results[0]['properties']