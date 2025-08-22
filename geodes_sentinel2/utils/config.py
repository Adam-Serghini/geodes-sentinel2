"""
Configuration management for Sentinel-2 processor.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field


class DefaultsConfig(BaseModel):
    """Default processing parameters."""

    model_config = ConfigDict(extra="allow")

    max_cloud_cover: float = Field(default=30.0, description="Maximum cloud cover percentage")
    bands: Optional[list] = Field(default=None, description="Default bands to process")
    indices: Optional[list] = Field(default=None, description="Default indices to calculate")
    keep_downloads: bool = Field(default=True, description="Keep downloaded ZIP files")
    output_structure: Dict[str, str] = Field(
        default_factory=lambda: {"downloads": "downloads", "crops": "crops", "indices": "indices"}
    )


class ProcessingConfig(BaseModel):
    """Processing configuration."""

    model_config = ConfigDict(extra="allow")

    output_format: str = Field(default="GeoTIFF", description="Output format for processed data")
    compression: str = Field(default="lzw", description="Compression method for outputs")
    resampling_method: str = Field(default="bilinear", description="Resampling method")
    num_threads: int = Field(default=4, description="Number of processing threads")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Logging level")
    file: Optional[str] = Field(default=None, description="Log file path")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )


class DownloadConfig(BaseModel):
    """Download configuration."""

    model_config = ConfigDict(extra="allow")

    chunk_size: int = Field(default=8192, description="Download chunk size in bytes")
    max_retries: int = Field(default=3, description="Max retry attempts")
    timeout: int = Field(default=600, description="Download timeout in seconds")
    show_progress: bool = Field(default=True, description="Show progress bar")


class SearchConfig(BaseModel):
    """Search configuration."""

    model_config = ConfigDict(extra="allow")

    limit: int = Field(default=100, description="Default search limit")
    dataset: str = Field(default="PEPS_S2_L1C", description="Default dataset")
    sort_by: str = Field(default="start_datetime", description="Sort field")
    sort_order: str = Field(default="asc", description="Sort order")


class Config(BaseModel):
    """Main configuration."""

    model_config = ConfigDict(extra="allow")

    api_key: Optional[str] = Field(default=None, description="GEODES API key")
    base_url: str = Field(
        default="https://geodes-portal.cnes.fr", description="GEODES portal base URL"
    )
    output_dir: str = Field(default="./output", description="Default output directory")
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    download: DownloadConfig = Field(default_factory=DownloadConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """
        Load configuration from file.

        Args:
            config_path: Path to configuration file (JSON or YAML)

        Returns:
            Config object
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path) as f:
            if config_path.suffix in [".yaml", ".yml"]:
                try:
                    import yaml  # type: ignore[import-untyped]

                    data = yaml.safe_load(f)
                except ImportError as e:
                    raise ImportError("PyYAML required for YAML config files") from e
            else:
                data = json.load(f)

        return cls(**data)

    @classmethod
    def from_env(cls, env_file: Optional[Path] = None) -> "Config":
        """
        Load configuration from environment variables.

        Args:
            env_file: Optional .env file path

        Returns:
            Config object
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        config_dict: Dict[str, Any] = {}

        # API configuration
        if api_key := os.getenv("GEODES_API_KEY"):
            config_dict["api_key"] = api_key

        if base_url := os.getenv("GEODES_BASE_URL"):
            config_dict["base_url"] = base_url

        if output_dir := os.getenv("OUTPUT_DIR"):
            config_dict["output_dir"] = output_dir

        # Processing configuration
        processing: Dict[str, Any] = {}
        if max_cloud := os.getenv("MAX_CLOUD_COVER"):
            processing["max_cloud_cover"] = float(max_cloud)

        if output_format := os.getenv("OUTPUT_FORMAT"):
            processing["output_format"] = output_format

        if compression := os.getenv("COMPRESSION"):
            processing["compression"] = compression

        if processing:
            config_dict["processing"] = processing

        # Logging configuration
        logging_config: Dict[str, Any] = {}
        if log_level := os.getenv("LOG_LEVEL"):
            logging_config["level"] = log_level

        if log_file := os.getenv("LOG_FILE"):
            logging_config["file"] = log_file

        if logging_config:
            config_dict["logging"] = logging_config

        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump(exclude_none=True)

    def save(self, path: Path):
        """
        Save configuration to file.

        Args:
            path: Output file path
        """
        path = Path(path)

        with open(path, "w") as f:
            if path.suffix in [".yaml", ".yml"]:
                try:
                    import yaml  # type: ignore[import-untyped]

                    yaml.safe_dump(self.to_dict(), f, default_flow_style=False)
                except ImportError:
                    # Fallback to JSON
                    json.dump(self.to_dict(), f, indent=2)
            else:
                json.dump(self.to_dict(), f, indent=2)


def load_config(config_file: Optional[Path] = None, use_env: bool = True) -> Config:
    """
    Load configuration from file and/or environment.

    Args:
        config_file: Optional configuration file path
        use_env: Whether to load from environment variables

    Returns:
        Config object
    """
    if config_file and config_file.exists():
        config = Config.from_file(config_file)
    else:
        config = Config()

    if use_env:
        env_config = Config.from_env()
        # Merge environment config (environment takes precedence)
        config = Config(**{**config.to_dict(), **env_config.to_dict()})

    return config
