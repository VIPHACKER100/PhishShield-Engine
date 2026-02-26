"""
Config Loader — Centralised configuration management.
"""

import os
import yaml
from typing import Any

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.yaml")

class Config:
    _instance = None
    _values = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                self._values = yaml.safe_load(f)
        else:
            # Fallback defaults if file missing
            self._values = {
                "security": {"thresholds": {"high_risk": 75, "suspicious": 30}},
                "api": {"port": 8000}
            }

    def get(self, key_path: str, default: Any = None) -> Any:
        try:
            val = self._values
            for part in key_path.split('.'):
                val = val[part]
            return val
        except (KeyError, TypeError):
            return default

# Global settings instance
settings = Config()
