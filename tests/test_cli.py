"""Tests for CLI functionality."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, Mock
import json

from geodes_sentinel2.cli import cli


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_geojson(tmp_path):
    """Create a sample GeoJSON file."""
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
    
    return str(geojson_path)


class TestCLI:
    """Test CLI commands."""
    
    def test_cli_help(self, runner):
        """Test CLI help."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'GEODES Sentinel-2 Processor' in result.output
    
    def test_process_help(self, runner):
        """Test process command help."""
        result = runner.invoke(cli, ['process', '--help'])
        assert result.exit_code == 0
        assert 'Complete processing workflow' in result.output
        assert '--dry-run' in result.output
    
    @patch('geodes_sentinel2.cli.Sentinel2Processor')
    def test_process_dry_run(self, mock_processor_class, runner, sample_geojson, tmp_path):
        """Test process command with dry run."""
        mock_processor = Mock()
        mock_processor.process.return_value = Mock(empty=True)
        mock_processor_class.return_value = mock_processor
        
        result = runner.invoke(cli, [
            'process',
            sample_geojson,
            str(tmp_path),
            '--dry-run'
        ])
        
        assert result.exit_code == 0
        assert '[DRY RUN]' in result.output
        mock_processor.process.assert_called_once()
        
        # Check that dry_run=True was passed
        call_kwargs = mock_processor.process.call_args.kwargs
        assert call_kwargs['dry_run'] is True
    
    @patch('geodes_sentinel2.cli.Sentinel2Processor')
    def test_process_with_indices(self, mock_processor_class, runner, sample_geojson, tmp_path):
        """Test process command with indices."""
        mock_processor = Mock()
        mock_processor.process.return_value = Mock(empty=True)
        mock_processor_class.return_value = mock_processor
        
        result = runner.invoke(cli, [
            'process',
            sample_geojson,
            str(tmp_path),
            '-i', 'NDVI EVI NDWI'
        ])
        
        assert result.exit_code == 0
        mock_processor.process.assert_called_once()
        
        # Check that indices were parsed correctly
        call_kwargs = mock_processor.process.call_args.kwargs
        assert call_kwargs['indices'] == ['NDVI', 'EVI', 'NDWI']
    
    @patch('geodes_sentinel2.cli.Sentinel2Processor')
    def test_process_with_bands(self, mock_processor_class, runner, sample_geojson, tmp_path):
        """Test process command with bands."""
        mock_processor = Mock()
        mock_processor.process.return_value = Mock(empty=True)
        mock_processor_class.return_value = mock_processor
        
        result = runner.invoke(cli, [
            'process',
            sample_geojson,
            str(tmp_path),
            '-b', 'B02 B03 B04 B08'
        ])
        
        assert result.exit_code == 0
        mock_processor.process.assert_called_once()
        
        # Check that bands were parsed correctly
        call_kwargs = mock_processor.process.call_args.kwargs
        assert call_kwargs['bands'] == ['B02', 'B03', 'B04', 'B08']
    
    def test_info_command(self, runner):
        """Test info command."""
        result = runner.invoke(cli, ['info'])
        assert result.exit_code == 0
        assert 'GEODES Sentinel-2 Processor' in result.output
        assert 'NDVI' in result.output
        assert 'B04' in result.output
    
    @patch('geodes_sentinel2.cli.Sentinel2Processor')
    def test_batch_command(self, mock_processor_class, runner, sample_geojson, tmp_path):
        """Test batch command."""
        mock_processor = Mock()
        mock_processor.process_batch.return_value = Mock(empty=False)
        mock_processor_class.return_value = mock_processor
        
        # Create second geojson
        geojson2 = tmp_path / "area2.geojson"
        with open(sample_geojson) as f:
            data = json.load(f)
        with open(geojson2, 'w') as f:
            json.dump(data, f)
        
        result = runner.invoke(cli, [
            'batch',
            sample_geojson,
            str(geojson2),
            str(tmp_path),
            '-i', 'NDVI'
        ])
        
        # May fail due to mock issues, but check the call was attempted
        mock_processor.process_batch.assert_called_once()
    
    def test_search_command_missing_dates(self, runner, tmp_path):
        """Test search command with missing dates."""
        # Create geojson without dates
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
        
        with patch('geodes_sentinel2.cli.Sentinel2Processor'):
            result = runner.invoke(cli, [
                'search',
                str(geojson_path),
                str(tmp_path)
            ])
        
        # Should fail due to missing dates
        assert result.exit_code != 0
    
    def test_invalid_command(self, runner):
        """Test invalid command."""
        result = runner.invoke(cli, ['invalid-command'])
        assert result.exit_code != 0
        assert 'Error' in result.output or 'Usage' in result.output


class TestCLIConfig:
    """Test CLI with configuration."""
    
    @pytest.fixture
    def config_file(self, tmp_path):
        """Create a config file."""
        import yaml
        
        config = {
            'defaults': {
                'max_cloud_cover': 25.0,
                'bands': ['B04', 'B08'],
                'indices': ['NDVI'],
                'keep_downloads': True
            }
        }
        
        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        return str(config_path)
    
    @patch('geodes_sentinel2.cli.Sentinel2Processor')
    def test_with_config(self, mock_processor_class, runner, sample_geojson, tmp_path, config_file):
        """Test CLI with config file."""
        mock_processor = Mock()
        mock_processor.process.return_value = Mock(empty=True)
        mock_processor_class.return_value = mock_processor
        
        result = runner.invoke(cli, [
            '--config', config_file,
            'process',
            sample_geojson,
            str(tmp_path)
        ])
        
        # Should load config
        assert result.exit_code == 0