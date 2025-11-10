import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for the site analyzer."""
    
    def __init__(self, config_path: Optional[str] = None, preset: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to config YAML file. If None, uses default config.yaml
            preset: Name of preset to apply (e.g., 'quick_scan', 'deep_analysis')
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
        
        # Apply preset if specified
        if preset:
            self.apply_preset(preset)
    
    def apply_preset(self, preset_name: str):
        """Apply a configuration preset."""
        if 'presets' in self._config and preset_name in self._config['presets']:
            preset = self._config['presets'][preset_name]
            
            # Apply preset values to main config
            for key, value in preset.items():
                if key in self._config['crawling']:
                    self._config['crawling'][key] = value
                elif key in self._config['analysis']:
                    self._config['analysis'][key] = value
        else:
            raise ValueError(f"Preset '{preset_name}' not found")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value: Any):
        """Set a configuration value (for CLI overrides)."""
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
    
    def get_crawl_config(self) -> Dict[str, Any]:
        """Get all crawling configuration."""
        return self._config.get('crawling', {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get all output configuration."""
        return self._config.get('output', {})
    
    def get_viz_config(self) -> Dict[str, Any]:
        """Get all visualization configuration."""
        return self._config.get('visualization', {})
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """Get all analysis configuration."""
        return self._config.get('analysis', {})
    
    @property
    def max_concurrency(self) -> int:
        return self.get('crawling', 'max_concurrency', 5)
    
    @property
    def max_pages(self) -> int:
        return self.get('crawling', 'max_pages', 100)
    
    @property
    def timeout(self) -> int:
        return self.get('crawling', 'timeout', 10)
    
    @property
    def max_retries(self) -> int:
        return self.get('crawling', 'max_retries', 3)
    
    @property
    def retry_delay(self) -> float:
        return self.get('crawling', 'retry_delay', 1.0)
    
    @property
    def rate_limit(self) -> float:
        return self.get('crawling', 'rate_limit', 2.0)
    
    @property
    def respect_robots_txt(self) -> bool:
        return self.get('crawling', 'respect_robots_txt', True)
    
    @property
    def user_agent(self) -> str:
        return self.get('crawling', 'user_agent', 'SiteAnalyzer/1.0')
    
    @property
    def output_directory(self) -> str:
        return self.get('output', 'directory', 'output')
    
    @property
    def output_formats(self) -> list:
        return self.get('output', 'formats', ['json', 'html', 'csv'])
    
    @property
    def max_depth(self) -> int:
        return self.get('analysis', 'max_depth', 5)


def load_config(config_path: Optional[str] = None, preset: Optional[str] = None) -> Config:
    """Load configuration from file."""
    return Config(config_path, preset)

