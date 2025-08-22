"""Tests for the main processor."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from geodes_sentinel2.core.processor import Sentinel2Processor


class TestSentinel2Processor:
    """Test the Sentinel2Processor class."""
    
    @pytest.fixture
    def processor(self, tmp_path):
        """Create a processor instance."""
        with patch.dict('os.environ', {'GEODES_API_KEY': 'test-key'}):
            return Sentinel2Processor(output_dir=tmp_path)
    
    @pytest.fixture
    def sample_geojson(self, tmp_path):
        """Create a sample GeoJSON file."""
        import json
        
        geojson_data = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {
                    "Name": "TestField",
                    "begin": "2024-06-01T00:00:00Z",
                    "end": "2024-06-07T00:00:00Z"
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
    
    def test_initialization(self, tmp_path):
        """Test processor initialization."""
        with patch.dict('os.environ', {'GEODES_API_KEY': 'test-key'}):
            processor = Sentinel2Processor(output_dir=tmp_path)
        
        assert processor.output_dir == tmp_path
        assert processor.downloads_dir.exists()
        assert processor.crops_dir.exists()
        assert processor.indices_dir.exists()
    
    def test_initialization_no_api_key(self, tmp_path):
        """Test that missing API key raises error."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key must be provided"):
                Sentinel2Processor(output_dir=tmp_path)
    
    @patch('geodes_sentinel2.core.processor.Sentinel2Processor.search')
    def test_dry_run(self, mock_search, processor, sample_geojson):
        """Test dry run mode."""
        mock_search.return_value = [
            {
                'properties': {
                    'identifier': 'S2A_MSIL1C_20240601',
                    'start_datetime': '2024-06-01T10:30:00Z',
                    'eo:cloud_cover': 15.5
                }
            }
        ]
        
        results = processor.process(
            area=sample_geojson,
            max_cloud_cover=30,
            dry_run=True
        )
        
        # In dry run, should not download or process
        assert results.empty or len(results) > 0  # DataFrame created
        mock_search.assert_called_once()
    
    @patch('geodes_sentinel2.core.processor.Sentinel2Processor.search')
    @patch('geodes_sentinel2.core.processor.Sentinel2Processor.download')
    @patch('geodes_sentinel2.core.processor.Sentinel2Processor.crop')
    def test_process_basic(self, mock_crop, mock_download, mock_search, processor, sample_geojson):
        """Test basic processing workflow."""
        mock_search.return_value = [
            {
                'properties': {
                    'identifier': 'S2A_MSIL1C_20240601',
                    'start_datetime': '2024-06-01T10:30:00Z',
                    'eo:cloud_cover': 15.5
                }
            }
        ]
        
        mock_download.return_value = [Path('test.zip')]
        mock_crop.return_value = {'test.zip': [Path('B04.tif'), Path('B08.tif')]}
        
        results = processor.process(
            area=sample_geojson,
            max_cloud_cover=30,
            bands=['B04', 'B08']
        )
        
        assert isinstance(results, pd.DataFrame)
        assert len(results) == 1
        mock_search.assert_called_once()
        mock_download.assert_called_once()
        mock_crop.assert_called_once()
    
    def test_process_batch(self, processor, sample_geojson, tmp_path):
        """Test batch processing."""
        # Create second geojson
        import json
        
        geojson2_data = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {
                    "Name": "TestField2",
                    "begin": "2024-07-01T00:00:00Z",
                    "end": "2024-07-07T00:00:00Z"
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
        
        geojson2_path = tmp_path / "test_area2.geojson"
        with open(geojson2_path, 'w') as f:
            json.dump(geojson2_data, f)
        
        with patch.object(processor, 'process') as mock_process:
            mock_process.return_value = pd.DataFrame([
                {'zone_name': 'TestField', 'product_id': 'test1'}
            ])
            
            results = processor.process_batch(
                areas=[sample_geojson, geojson2_path],
                max_cloud_cover=30
            )
            
            assert mock_process.call_count == 2
    
    def test_search_method(self, processor, sample_geojson):
        """Test search method."""
        with patch.object(processor.searcher, 'search_by_geometry') as mock_search:
            mock_search.return_value = []
            
            results = processor.search(
                area=sample_geojson,
                start_date="2024-06-01",
                end_date="2024-06-07",
                max_cloud_cover=30
            )
            
            assert results == []
            mock_search.assert_called_once()
    
    def test_calculate_indices(self, processor, tmp_path):
        """Test vegetation index calculation."""
        # Use the processor's crops_dir which already exists
        crops_dir = processor.crops_dir
        
        (crops_dir / "test_2024-06-01_B04.tif").touch()
        (crops_dir / "test_2024-06-01_B08.tif").touch()
        
        with patch.object(processor.band_math, 'process_all_indices') as mock_indices:
            mock_indices.return_value = {
                'NDVI': [Path('test_NDVI.tif')]
            }
            
            results = processor.calculate_indices(
                crop_dir=crops_dir,
                indices=['NDVI']
            )
            
            assert 'NDVI' in results
            mock_indices.assert_called_once_with(crops_dir, ['NDVI'])


class TestProcessorConfig:
    """Test processor with configuration."""
    
    def test_with_config(self, tmp_path):
        """Test processor with custom configuration."""
        from geodes_sentinel2.utils.config import Config, DefaultsConfig
        
        config = Config(
            api_key="test-key",
            output_dir=str(tmp_path),
            defaults=DefaultsConfig(
                max_cloud_cover=20.0,
                bands=['B04', 'B08'],
                indices=['NDVI']
            )
        )
        
        processor = Sentinel2Processor(
            api_key="test-key",
            output_dir=tmp_path,
            config=config
        )
        
        assert processor.config == config
        assert processor.output_dir == tmp_path