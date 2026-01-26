"""
Configuration management for SermonPod.
Handles saving and loading user preferences.
"""

import json
from pathlib import Path
from typing import Any, Dict


class ConfigManager:
    """Manages application configuration and user preferences."""

    def __init__(self, config_name: str = "sermonpod_config.json"):
        """
        Initialize the configuration manager.

        Args:
            config_name: Name of the configuration file
        """
        self.config_dir = Path.home() / ".config" / "sermonpod"
        self.config_file = self.config_dir / config_name
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    self._config = json.load(f)
            else:
                # Initialize with defaults
                self._config = self._get_default_config()
        except Exception:
            # If loading fails, use defaults
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.

        Returns:
            Dictionary with default settings
        """
        from .file_utils import get_default_output_dir

        return {
            "output_directory": get_default_output_dir(),
            "audio_quality": "320",  # Default: 320kbps
            "last_used_filename": "",
        }

    def save_config(self):
        """Save current configuration to file."""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Write configuration to file
            with open(self.config_file, "w") as f:
                json.dump(self._config, f, indent=2)
        except Exception:
            # Silently fail - configuration is not critical
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """
        Set a configuration value and save.

        Args:
            key: Configuration key
            value: Value to set
        """
        self._config[key] = value
        self.save_config()

    def get_output_directory(self) -> str:
        """
        Get the saved output directory preference.

        Returns:
            Output directory path
        """
        return self.get(
            "output_directory", self._get_default_config()["output_directory"]
        )

    def set_output_directory(self, directory: str):
        """
        Save the output directory preference.

        Args:
            directory: Directory path to save
        """
        self.set("output_directory", directory)

    def get_audio_quality(self) -> str:
        """
        Get the saved audio quality preference.

        Returns:
            Audio quality setting (e.g., "320", "192", "128")
        """
        return self.get("audio_quality", "320")

    def set_audio_quality(self, quality: str):
        """
        Save the audio quality preference.

        Args:
            quality: Audio quality setting
        """
        self.set("audio_quality", quality)

    def get_last_filename(self) -> str:
        """
        Get the last used filename.

        Returns:
            Last filename used
        """
        return self.get("last_used_filename", "")

    def set_last_filename(self, filename: str):
        """
        Save the last used filename.

        Args:
            filename: Filename to save
        """
        self.set("last_used_filename", filename)
